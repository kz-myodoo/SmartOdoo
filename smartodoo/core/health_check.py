"""
HealthChecker — post-startup validation suite.
Powstało jako odpowiedź na incydent 2026-03-11 (3 kaskadowe problemy Docker/Odoo).
"""
import socket
from dataclasses import dataclass, field
from typing import List

from smartodoo.core.docker_ops import DockerOps


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


@dataclass
class HealthReport:
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def summary(self) -> str:
        passed = sum(1 for c in self.checks if c.passed)
        total = len(self.checks)
        return f"{passed}/{total} checks passed"


def check_port_available(port: int) -> bool:
    """Sprawdza czy port na localhost jest wolny (nie nasłuchuje)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        result = s.connect_ex(("127.0.0.1", port))
        return result != 0  # 0 = ktoś nasłuchuje = zajęty


class HealthChecker:
    """
    Post-startup validation suite.
    
    Uruchamia 4 checki:
    1. check_port_conflicts   — czy porty hosta nie kolidują z innymi kontenerami
    2. check_network_connectivity — czy odoo widzi db po DNS
    3. check_odoo_registry    — czy Odoo ładuje moduły bez błędów
    4. check_filestore_exists — czy filestore nie jest pusty
    """

    def __init__(self, docker_ops: DockerOps, odoo_container: str, db_container: str):
        self.docker_ops = docker_ops
        self.odoo_container = odoo_container
        self.db_container = db_container

    def check_port_conflicts(self, ports: List[int]) -> CheckResult:
        """Sprawdza, czy porty na hoście nie są zajęte przez inne procesy/kontenery."""
        occupied = [p for p in ports if not check_port_available(p)]
        if occupied:
            return CheckResult(
                name="Port Conflicts",
                passed=False,
                detail=f"Porty zajęte na hoście: {', '.join(str(p) for p in occupied)}. "
                       f"Zmień DB_HOST_PORT w .env lub zatrzymaj kolidujący kontener."
            )
        return CheckResult(
            name="Port Conflicts",
            passed=True,
            detail=f"Wszystkie porty wolne: {', '.join(str(p) for p in ports)}"
        )

    def check_network_connectivity(self) -> CheckResult:
        """Weryfikuje czy kontener Odoo widzi kontener DB po DNS (ping db)."""
        try:
            output = self.docker_ops.exec_run(
                self.odoo_container,
                ["ping", "-c", "1", "-W", "2", "db"]
            )
            if "1 received" in output or "1 packets" in output:
                return CheckResult(
                    name="Network Connectivity",
                    passed=True,
                    detail="Odoo → DB: połączenie OK"
                )
            return CheckResult(
                name="Network Connectivity",
                passed=False,
                detail=f"Ping do 'db' nie powiódł się: {output[:100]}"
            )
        except Exception as e:
            return CheckResult(
                name="Network Connectivity",
                passed=False,
                detail=f"Brak łączności Odoo → DB: {str(e)[:100]}"
            )

    def check_odoo_registry(self, db_name: str) -> CheckResult:
        """Uruchamia Odoo z --stop-after-init i sprawdza czy registry się załadował."""
        try:
            output = self.docker_ops.exec_run(
                self.odoo_container,
                [
                    "odoo", "--stop-after-init", "--no-http",
                    "--db_host=db", "--db_user=odoo", "--db_password=odoo",
                    f"-d", db_name
                ]
            )
            if "Modules loaded" in output:
                return CheckResult(
                    name="Odoo Registry",
                    passed=True,
                    detail=f"Moduły załadowane poprawnie dla bazy {db_name}"
                )
            return CheckResult(
                name="Odoo Registry",
                passed=False,
                detail=f"Odoo registry nie zwrócił 'Modules loaded': {output[:150]}"
            )
        except Exception as e:
            return CheckResult(
                name="Odoo Registry",
                passed=False,
                detail=f"Błąd ładowania registry Odoo: {str(e)[:150]}"
            )

    def check_filestore_exists(self, db_name: str) -> CheckResult:
        """Sprawdza czy filestore dla bazy istnieje i nie jest pusty."""
        try:
            output = self.docker_ops.exec_run(
                self.odoo_container,
                ["ls", f"/var/lib/odoo/filestore/{db_name}"]
            )
            dirs = [d for d in output.strip().split("\n") if d.strip()]
            if dirs:
                return CheckResult(
                    name="Filestore",
                    passed=True,
                    detail=f"Filestore ma {len(dirs)} podkatalogów dla {db_name}"
                )
            return CheckResult(
                name="Filestore",
                passed=False,
                detail=f"Filestore pusty dla {db_name}! Restore BEZ filestore = 500 error."
            )
        except Exception:
            return CheckResult(
                name="Filestore",
                passed=False,
                detail=f"Filestore nie istnieje: /var/lib/odoo/filestore/{db_name}"
            )

    def run_all(self, db_name: str, ports: List[int] = None) -> HealthReport:
        """Uruchamia wszystkie 4 checki i zwraca HealthReport."""
        if ports is None:
            ports = [5432, 8069]

        report = HealthReport()
        report.checks.append(self.check_port_conflicts(ports))
        report.checks.append(self.check_network_connectivity())
        report.checks.append(self.check_odoo_registry(db_name))
        report.checks.append(self.check_filestore_exists(db_name))
        return report

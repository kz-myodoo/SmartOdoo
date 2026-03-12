"""
TDD RED — Testy dla modułu HealthChecker.
Pokrywają 4 scenariusze incydentowe z postmortem 2026-03-11.
"""
import pytest
from unittest.mock import MagicMock, patch
from smartodoo.core.health_check import HealthChecker, HealthReport, CheckResult


@pytest.fixture
def mock_docker_ops():
    ops = MagicMock()
    return ops


@pytest.fixture
def checker(mock_docker_ops):
    return HealthChecker(
        docker_ops=mock_docker_ops,
        odoo_container="odoo_16_test",
        db_container="db_16_test"
    )


class TestPortConflicts:
    """Problem #1: Port 5432 zajęty → DB odcięta od sieci."""

    def test_detects_occupied_port(self, checker):
        """Jeśli port 5432 jest zajęty, checker musi go wykryć."""
        with patch("smartodoo.core.health_check.check_port_available") as mock_port:
            mock_port.return_value = False
            result = checker.check_port_conflicts([5432])
            assert result.passed is False
            assert "5432" in result.detail

    def test_passes_when_ports_free(self, checker):
        """Jeśli port wolny, check przechodzi."""
        with patch("smartodoo.core.health_check.check_port_available") as mock_port:
            mock_port.return_value = True
            result = checker.check_port_conflicts([5432, 8069])
            assert result.passed is True


class TestNetworkConnectivity:
    """Problem #1b: Kontenery nie widzą się po DNS."""

    def test_fails_when_ping_fails(self, checker, mock_docker_ops):
        """Ping db z kontenera odoo nie przechodzi → check fail."""
        mock_docker_ops.exec_run.side_effect = Exception("Name or service not known")
        result = checker.check_network_connectivity()
        assert result.passed is False

    def test_passes_on_successful_ping(self, checker, mock_docker_ops):
        """Ping db przechodzi → check ok."""
        mock_docker_ops.exec_run.return_value = "PING db: 1 packets transmitted, 1 received"
        result = checker.check_network_connectivity()
        assert result.passed is True


class TestOdooRegistry:
    """Problem #2: kpi.provider brakuje w registry → crash."""

    def test_fails_on_nonzero_exit(self, checker, mock_docker_ops):
        """Odoo --stop-after-init zwraca exit ≠ 0 → fail."""
        mock_docker_ops.exec_run.side_effect = Exception("kpi.provider does not exist")
        result = checker.check_odoo_registry("myodoo_test")
        assert result.passed is False
        assert "registry" in result.detail.lower()

    def test_passes_on_clean_load(self, checker, mock_docker_ops):
        """Odoo ładuje moduły bez błędów → pass."""
        mock_docker_ops.exec_run.return_value = "Modules loaded."
        result = checker.check_odoo_registry("myodoo_test")
        assert result.passed is True


class TestFilestoreExists:
    """Problem #3: Brak filestore → 500 error na web assets."""

    def test_fails_when_filestore_empty(self, checker, mock_docker_ops):
        """Filestore pusty/nieistniejący → fail."""
        mock_docker_ops.exec_run.return_value = ""
        result = checker.check_filestore_exists("myodoo_test")
        assert result.passed is False

    def test_passes_when_filestore_has_dirs(self, checker, mock_docker_ops):
        """Filestore ma podkatalogi → pass."""
        mock_docker_ops.exec_run.return_value = "00\n01\n02\nff"
        result = checker.check_filestore_exists("myodoo_test")
        assert result.passed is True


class TestRunAll:
    """Integracyjny test run_all()."""

    def test_run_all_returns_report(self, checker, mock_docker_ops):
        """run_all() zwraca HealthReport z listą CheckResult."""
        mock_docker_ops.exec_run.return_value = "ok"
        with patch("smartodoo.core.health_check.check_port_available", return_value=True):
            report = checker.run_all(db_name="myodoo_test", ports=[5432, 8069])
        assert isinstance(report, HealthReport)
        assert len(report.checks) == 4
        assert all(isinstance(c, CheckResult) for c in report.checks)

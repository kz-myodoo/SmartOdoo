import os
import subprocess
import shutil
from pathlib import Path
from typing import List

class DockerManager:
    """
    Zorientowana obiektowo abstrakcja komend Dockera.
    Używana jako usługa typu "Injected" (Dependency Injection) - zapobiega
    roznoszacym się po całym kodzie odwołaniom subprocess.
    """
    def __init__(self):
        self.compose_plugin = self._detect_compose()

    def _detect_compose(self) -> List[str]:
        if shutil.which("docker"):
            try:
                subprocess.run(
                    ["docker", "compose", "version"], 
                    check=True, 
                    capture_output=True
                )
                return ["docker", "compose"]
            except subprocess.CalledProcessError:
                pass
        
        if shutil.which("docker-compose"):
            return ["docker-compose"]
            
        raise RuntimeError("Brak środowiska Docker! Przerywam pracę.")

    def run_tests(self, project_path: Path, db: str, module: str) -> subprocess.CompletedProcess:
        """Metoda uruchamiająca zestaw testów na odoo (Mock-friendly)."""
        cmd = self.compose_plugin + ["run", "--rm", "web", "--test-enable", "-d", db, "-i", module]
        return subprocess.run(cmd, cwd=project_path, text=True)

    def execute(self, project_path: Path, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Generyczna metoda strzelająca dockerem z łapaniem błędów uprawnień WSL/Linux."""
        cmd = self.compose_plugin + args
        # Łapiemy stdErr bez uśmiercania całego procesu by wybadać powód błędu
        process = subprocess.run(cmd, cwd=project_path, text=True, capture_output=True)
        
        if process.returncode != 0:
            if "Permission denied" in process.stderr or "permission denied" in process.stderr:
                self._resolve_permissions(project_path)
                process = subprocess.run(cmd, cwd=project_path, text=True, capture_output=True)
            
            if check and process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd, process.stdout, process.stderr)
                
        # Zwaraca pomyślny wynik
        return process

    def _resolve_permissions(self, project_path: Path):
        """Uruchamia chown/chmod dla systemów Linux (Wzorzec Repair hook)."""
        if os.name != "nt":  # Unix / WSL
            subprocess.run(["sudo", "chmod", "-R", "777", str(project_path)], capture_output=True)

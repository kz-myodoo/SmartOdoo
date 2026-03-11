import subprocess
from pathlib import Path

class DockerOpsError(Exception):
    pass

class DockerOps:
    """Klasa-interfejs spinająca wywołania klienta Docker CLI z Pythonem.
    Zwraca odzyskany standard output w formie stringa lub podrzuca sformatowany exception.
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def _run_cmd(self, cmd: list[str]) -> str:
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip() if e.stderr else e.output
            raise DockerOpsError(f"Błąd uruchamiania {' '.join(cmd)}: {err_msg}")

    def compose_up(self) -> str:
        """Podnosi kontenery ze zdefiniowanego docker-compose.yml"""
        return self._run_cmd(["docker", "compose", "up", "-d"])

    def compose_stop(self) -> str:
        """Zatrzymuje zestaw kontenerów"""
        return self._run_cmd(["docker", "compose", "stop"])

    def exec_run(self, container_name: str, command: list[str], env: dict[str, str] = None, user: str = None) -> str:
        """Wykonuje polecenie wewnątrz odpalonego kontenera"""
        full_cmd = ["docker", "exec"]
        if user:
            full_cmd.extend(["--user", user])
        if env:
            for k, v in env.items():
                full_cmd.extend(["-e", f"{k}={v}"])
        full_cmd.append(container_name)
        full_cmd.extend(command)
        return self._run_cmd(full_cmd)

    def cp(self, src: str, dest: str) -> str:
        """Kopiuje pliki między hostem a kontenerem używając formatu docker cp src dest"""
        return self._run_cmd(["docker", "cp", src, dest])

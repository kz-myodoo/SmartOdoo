from pathlib import Path
import shutil
import subprocess


def try_delete_with_admin(project_fullpath: Path) -> None:
    """Attempt privileged deletion on Windows when standard deletion fails."""
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell:
        command = f'Start-Process cmd -Verb RunAs -WindowStyle Hidden -ArgumentList \'/c rmdir /s /q "{project_fullpath}"\' -Wait'
        subprocess.run([powershell, "-NoProfile", "-Command", command], text=True, check=False)
    else:
        subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", str(project_fullpath)], text=True, check=False)

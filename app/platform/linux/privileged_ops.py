from pathlib import Path
import os
import shutil
import subprocess


def try_delete_with_admin(project_fullpath: Path) -> None:
    """Attempt privileged deletion on Linux when standard deletion fails."""
    pkexec_path = shutil.which("pkexec")
    if pkexec_path and os.environ.get("DISPLAY"):
        result = subprocess.run([pkexec_path, "rm", "-rf", str(project_fullpath)], text=True, check=False)
        if result.returncode == 0:
            return

    sudo_path = shutil.which("sudo")
    if sudo_path:
        subprocess.run([sudo_path, "rm", "-rf", str(project_fullpath)], text=True, check=False)

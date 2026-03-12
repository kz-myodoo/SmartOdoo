from pathlib import Path
import shutil
import subprocess


def open_settings_file(file_path: Path) -> None:
    """Open a settings file using Linux desktop opener."""
    if not file_path.exists():
        raise FileNotFoundError(f"Not found: {file_path}")

    xdg_open = shutil.which("xdg-open")
    if not xdg_open:
        raise RuntimeError("'xdg-open' is not available in PATH.")

    subprocess.Popen([xdg_open, str(file_path)])

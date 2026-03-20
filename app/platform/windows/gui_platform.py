from pathlib import Path
from typing import Any
import subprocess


def windows_subprocess_kwargs() -> dict[str, Any]:
    """Build subprocess kwargs that hide Windows console windows."""
    kwargs: dict[str, Any] = {}
    create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if create_no_window:
        kwargs["creationflags"] = create_no_window

    startupinfo_cls = getattr(subprocess, "STARTUPINFO", None)
    if startupinfo_cls is not None:
        startupinfo = startupinfo_cls()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
        startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
        kwargs["startupinfo"] = startupinfo

    return kwargs


def open_settings_file(file_path: Path) -> None:
    """Open a settings file using Windows shell."""
    if not file_path.exists():
        raise FileNotFoundError(f"Not found: {file_path}")

    subprocess.Popen(["cmd", "/c", "start", "", str(file_path)])


def launch_installer(installer_path: Path) -> None:
    """Launch installer executable using Windows shell."""
    if not installer_path.exists():
        raise FileNotFoundError(f"Not found: {installer_path}")

    subprocess.Popen(["cmd", "/c", "start", "", str(installer_path)])

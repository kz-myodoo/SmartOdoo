from pathlib import Path
from typing import Any, Optional
import os
import subprocess
import sys

GUI_MODE_ENV = "SMARTODOO_GUI_MODE"


def windows_hidden_subprocess_kwargs() -> dict[str, Any]:
    """Hide subprocess console windows for child processes in GUI mode."""
    if os.getenv(GUI_MODE_ENV) != "1":
        return {}

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


def run(
    cmd: list[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    capture_output: bool = False,
    env: Optional[dict[str, str]] = None,
    stdin: Any = None,
) -> subprocess.CompletedProcess:
    """Run a subprocess command on Windows with GUI-safe defaults."""
    run_kwargs: dict[str, Any] = {
        "cwd": str(cwd) if cwd else None,
        "text": True,
        "check": check,
        "capture_output": capture_output,
        "env": env,
        **windows_hidden_subprocess_kwargs(),
    }

    if stdin is not None:
        run_kwargs["stdin"] = stdin

    if os.getenv(GUI_MODE_ENV) == "1" and not capture_output:
        if sys.stdout is not None:
            run_kwargs["stdout"] = sys.stdout
        if sys.stderr is not None:
            run_kwargs["stderr"] = sys.stderr

    return subprocess.run(cmd, **run_kwargs)

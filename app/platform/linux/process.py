from pathlib import Path
from typing import Any, Optional
import subprocess


def run(
    cmd: list[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    capture_output: bool = False,
    env: Optional[dict[str, str]] = None,
    stdin: Any = None,
) -> subprocess.CompletedProcess:
    """Run a subprocess command on Linux with common defaults."""
    run_kwargs: dict[str, Any] = {
        "cwd": str(cwd) if cwd else None,
        "text": True,
        "check": check,
        "capture_output": capture_output,
        "env": env,
    }

    if stdin is not None:
        run_kwargs["stdin"] = stdin

    return subprocess.run(cmd, **run_kwargs)

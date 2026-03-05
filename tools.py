from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    """Return paths without duplicates while preserving original order."""
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def detect_documents_dir() -> Path:
    """Detect user Documents directory in a locale-independent way."""
    if os.name == "nt":
        user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
        return user_profile / "Documents"

    xdg_documents_dir = os.environ.get("XDG_DOCUMENTS_DIR")
    if xdg_documents_dir:
        expanded = xdg_documents_dir.replace("$HOME", str(Path.home()))
        return Path(expanded).expanduser()

    xdg_user_dir_cmd = shutil.which("xdg-user-dir")
    if xdg_user_dir_cmd:
        detected = subprocess.run([xdg_user_dir_cmd, "DOCUMENTS"], text=True, capture_output=True, check=False)
        detected_path = detected.stdout.strip()
        if detected.returncode == 0 and detected_path:
            return Path(detected_path).expanduser()

    for fallback_name in ["Documents", "Dokumenty"]:
        fallback_dir = Path.home() / fallback_name
        if fallback_dir.exists():
            return fallback_dir

    return Path.home() / "Documents"


def resolve_projects_base(*, additional_candidates: Iterable[Path] | None = None, ensure_exists: bool = False) -> Path:
    """Resolve the best base path for DockerProjects across platforms."""
    documents_dir = detect_documents_dir()
    candidates: list[Path] = [
        documents_dir / "DockerProjects",
        Path.home() / "Dokumenty" / "DockerProjects",
        Path.home() / "Documents" / "DockerProjects",
    ]

    if os.name == "nt":
        cwd_based = Path(str(Path.cwd()).replace("SmartOdoo", "DockerProjects"))
        candidates = [cwd_based, documents_dir / "DockerProjects"] + candidates[1:]

    if additional_candidates:
        candidates.extend(additional_candidates)

    candidates = unique_paths(candidates)

    base_path = candidates[0]
    for candidate in candidates:
        if candidate.exists():
            base_path = candidate
            break

    if ensure_exists:
        base_path.mkdir(parents=True, exist_ok=True)

    return base_path


def resolve_project_path(project_name: str, *, additional_candidates: Iterable[Path] | None = None) -> Path:
    """Resolve full path for a named project inside DockerProjects."""
    base_path = resolve_projects_base(additional_candidates=additional_candidates, ensure_exists=False)
    return base_path / project_name

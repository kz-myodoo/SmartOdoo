from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TypedDict


class PlatformPaths(TypedDict):
    PROJECTS_DIR: Path
    ENTERPRISE_LOCATION: Path
    UPGRADE_UTIL_LOCATION: Path


def resolve_config_path(raw_value: str, *, base_dir: Path) -> Path:
    """Resolve configured path with env/user expansion and relative support."""
    expanded = os.path.expanduser(os.path.expandvars(raw_value.strip()))
    candidate = Path(expanded)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def load_platform_paths(*, root_dir: Path) -> PlatformPaths:
    """Load required platform-specific paths from config.json in root_dir."""
    config_path = root_dir / "config.json"
    if not config_path.exists():
        raise RuntimeError(f"Missing required config file: {config_path}")

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise RuntimeError(f"Failed to load '{config_path.name}': {error}") from error

    platform_key = "windows" if os.name == "nt" else "linux"
    platform_values = payload.get(platform_key)
    if not isinstance(platform_values, dict):
        raise RuntimeError(
            f"Missing required '{platform_key}' section in {config_path.name}."
        )

    required_keys = ["PROJECTS_DIR", "ENTERPRISE_LOCATION", "UPGRADE_UTIL_LOCATION"]
    missing_keys = [key for key in required_keys if not str(platform_values.get(key, "")).strip()]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise RuntimeError(
            f"Missing required config keys in '{platform_key}' section: {missing}"
        )

    return {
        "PROJECTS_DIR": resolve_config_path(str(platform_values["PROJECTS_DIR"]), base_dir=root_dir),
        "ENTERPRISE_LOCATION": resolve_config_path(str(platform_values["ENTERPRISE_LOCATION"]), base_dir=root_dir),
        "UPGRADE_UTIL_LOCATION": resolve_config_path(str(platform_values["UPGRADE_UTIL_LOCATION"]), base_dir=root_dir),
    }

from pathlib import Path
import re


def to_compose_path(value: Path | str) -> str:
    """Format host path for Docker Compose on Windows."""
    return str(value).replace("\\", "/")


def normalize_project_env_paths(project_fullpath: Path) -> None:
    """Normalize path-like keys in project .env to Docker-friendly path format."""
    env_path = project_fullpath / ".env"
    if not env_path.exists():
        return

    content = env_path.read_text(encoding="utf-8")
    keys = ("PROJECT_LOCATION", "ENTERPRISE_LOCATION", "UPGRADE_UTIL_LOCATION")

    for key in keys:
        match = re.search(rf"^{re.escape(key)}=(.*)$", content, flags=re.MULTILINE)
        if not match:
            continue
        value = match.group(1).strip()
        normalized = to_compose_path(value)
        content = re.sub(
            rf"^{re.escape(key)}=.*$",
            lambda _match, k=key, v=normalized: f"{k}={v}",
            content,
            flags=re.MULTILINE,
        )

    env_path.write_text(content, encoding="utf-8")

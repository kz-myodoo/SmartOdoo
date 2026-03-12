from pathlib import Path


def to_compose_path(value: Path | str) -> str:
    """Format host path for Docker Compose on Linux."""
    return str(value)

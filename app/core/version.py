import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def get_smartodoo_version(root_dir: Path | None = None) -> str:
    try:
        return version("smartodoo")
    except PackageNotFoundError:
        pass

    resolved_root = root_dir or Path(__file__).resolve().parents[2]
    setup_path = resolved_root / "app" / "setup.py"
    if setup_path.exists():
        try:
            content = setup_path.read_text(encoding="utf-8")
            match = re.search(r"version\s*=\s*['\"]([^'\"]+)['\"]", content)
            if match:
                return match.group(1)
        except OSError:
            pass

    legacy_setup_path = resolved_root / "setup.py"
    if legacy_setup_path.exists():
        try:
            content = legacy_setup_path.read_text(encoding="utf-8")
            match = re.search(r"version\s*=\s*['\"]([^'\"]+)['\"]", content)
            if match:
                return match.group(1)
        except OSError:
            pass

    return "dev"

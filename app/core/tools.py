import json
import os
import re
from pathlib import Path
from threading import Lock
from typing import Optional, TypedDict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class PlatformPaths(TypedDict):
    PROJECTS_DIR: Path
    ENTERPRISE_LOCATION: Path
    UPGRADE_UTIL_LOCATION: Path


class GithubReleaseInfo(TypedDict):
    owner: str
    repository: str
    tag_name: str
    name: str
    html_url: str
    published_at: str
    source: str
    assets: list[dict[str, str]]


DEFAULT_GITHUB_REPOSITORY_URL = "git@github.com:kz-myodoo/SmartOdoo.git"
_GITHUB_RELEASE_CACHE: dict[str, Optional[GithubReleaseInfo]] = {}
_GITHUB_RELEASE_CACHE_LOCK = Lock()


def normalize_version_tag(value: str) -> str:
    """Normalize version/tag text to lowercase form without leading 'v'."""
    return value.strip().lower().lstrip("v")


def resolve_config_json_path(*, root_dir: Path) -> Path:
    """Resolve config.json location with platform-aware fallbacks."""
    candidates: list[Path] = []
    if os.name != "nt":
        candidates.append(Path("/etc/smartodoo/config.json"))
    candidates.extend([root_dir / "config" / "config.json", root_dir / "config.json"])

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_odoo_conf_path(*, root_dir: Path) -> Path:
    """Resolve odoo.conf location with platform-aware fallbacks."""
    candidates: list[Path] = []
    if os.name != "nt":
        candidates.append(Path("/etc/smartodoo/odoo.conf"))
    candidates.append(root_dir / "config" / "odoo.conf")

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_config_path(raw_value: str, *, base_dir: Path) -> Path:
    """Resolve configured path with env/user expansion and relative support."""
    expanded = os.path.expanduser(os.path.expandvars(raw_value.strip()))
    candidate = Path(expanded)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def load_platform_paths(*, root_dir: Path) -> PlatformPaths:
    """Load required platform-specific paths from config.json in root_dir."""
    config_path = resolve_config_json_path(root_dir=root_dir)
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


def _parse_github_owner_repo(repo_url: str) -> tuple[str, str]:
    """Extract owner/repo from SSH or HTTPS GitHub URL."""
    cleaned = repo_url.strip()
    if not cleaned:
        raise ValueError("GitHub repository URL is empty.")

    ssh_match = re.match(r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", cleaned)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)

    https_match = re.match(r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", cleaned)
    if https_match:
        return https_match.group(1), https_match.group(2)

    raise ValueError(f"Unsupported GitHub repository URL: {repo_url}")


def _github_get_json(url: str) -> dict:
    """Perform GET request to GitHub API and return parsed JSON object."""
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "SmartOdoo",
        },
    )
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid JSON response from GitHub API: {url}")
    return payload


def _parse_release_payload(payload: dict, *, owner: str, repository: str, source: str) -> GithubReleaseInfo:
    """Convert GitHub release payload to normalized release info shape."""
    tag_name = str(payload.get("tag_name", "")).strip()
    if not tag_name:
        raise RuntimeError("GitHub API response does not include 'tag_name'.")

    raw_assets = payload.get("assets")
    assets: list[dict[str, str]] = []
    if isinstance(raw_assets, list):
        for item in raw_assets:
            if not isinstance(item, dict):
                continue
            asset_name = str(item.get("name", "")).strip()
            download_url = str(item.get("browser_download_url", "")).strip()
            if not asset_name or not download_url:
                continue
            assets.append({"name": asset_name, "browser_download_url": download_url})

    return {
        "owner": owner,
        "repository": repository,
        "tag_name": tag_name,
        "name": str(payload.get("name", "")).strip() or tag_name,
        "html_url": str(payload.get("html_url", "")).strip(),
        "published_at": str(payload.get("published_at", "")).strip(),
        "source": source,
        "assets": assets,
    }


def get_latest_github_release_info(
    repo_url: str = DEFAULT_GITHUB_REPOSITORY_URL,
    force_refresh: bool = False,
) -> Optional[GithubReleaseInfo]:
    """Return latest GitHub release info or None when repository has no releases.

    Cached per repository by default. Set force_refresh=True to fetch fresh data.
    """
    owner, repository = _parse_github_owner_repo(repo_url)
    cache_key = f"{owner}/{repository}".lower()

    if not force_refresh:
        with _GITHUB_RELEASE_CACHE_LOCK:
            if cache_key in _GITHUB_RELEASE_CACHE:
                return _GITHUB_RELEASE_CACHE[cache_key]

    release_api_url = f"https://api.github.com/repos/{owner}/{repository}/releases/latest"

    try:
        release_payload = _github_get_json(release_api_url)
        release_info = _parse_release_payload(release_payload, owner=owner, repository=repository, source="release")
        with _GITHUB_RELEASE_CACHE_LOCK:
            _GITHUB_RELEASE_CACHE[cache_key] = release_info
        return release_info
    except HTTPError as http_error:
        if http_error.code == 404:
            with _GITHUB_RELEASE_CACHE_LOCK:
                _GITHUB_RELEASE_CACHE[cache_key] = None
            return None
        raise RuntimeError(f"Failed to fetch latest GitHub release: HTTP {http_error.code}") from http_error
    except URLError as url_error:
        raise RuntimeError(f"Failed to fetch latest GitHub release: {url_error}") from url_error

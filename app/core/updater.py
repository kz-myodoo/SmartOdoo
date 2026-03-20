import os
import re
import tempfile
from pathlib import Path
from urllib.request import urlopen

from app.core.tools import (
    DEFAULT_GITHUB_REPOSITORY_URL,
    GithubReleaseInfo,
    get_latest_github_release_info,
    normalize_version_tag,
)


def _version_tuple(value: str) -> tuple[int, ...]:
    normalized = normalize_version_tag(value)
    numbers = re.findall(r"\d+", normalized)
    return tuple(int(number) for number in numbers) if numbers else (0,)


def is_update_available(current_version: str, latest_version: str) -> bool:
    current_norm = normalize_version_tag(current_version)
    latest_norm = normalize_version_tag(latest_version)
    if not current_norm or not latest_norm:
        return False
    return _version_tuple(latest_norm) > _version_tuple(current_norm)


def _expected_installer_extension() -> str:
    return ".exe" if os.name == "nt" else ".deb"


def select_release_installer_asset(release_info: GithubReleaseInfo) -> dict[str, str]:
    assets = release_info.get("assets", [])
    extension = _expected_installer_extension()
    release_version = normalize_version_tag(str(release_info.get("tag_name", "")))

    if not assets:
        raise RuntimeError("Latest release does not include any assets.")

    candidates: list[dict[str, str]] = []
    for asset in assets:
        name = str(asset.get("name", "")).strip()
        if not name.lower().endswith(extension):
            continue
        candidates.append(asset)

    if not candidates:
        raise RuntimeError(f"Latest release does not include a '{extension}' installer.")

    for asset in candidates:
        name_norm = normalize_version_tag(str(asset.get("name", "")))
        if release_version and release_version in name_norm:
            return asset

    return candidates[0]


def download_release_asset(asset: dict[str, str], target_dir: Path | None = None) -> Path:
    asset_name = str(asset.get("name", "")).strip()
    download_url = str(asset.get("browser_download_url", "")).strip()
    if not asset_name or not download_url:
        raise RuntimeError("Release asset is missing 'name' or 'browser_download_url'.")

    destination_dir = target_dir or Path(tempfile.gettempdir())
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / asset_name

    with urlopen(download_url, timeout=60) as response:
        destination_path.write_bytes(response.read())

    return destination_path


def prepare_latest_installer(
    current_version: str,
    repo_url: str = DEFAULT_GITHUB_REPOSITORY_URL,
    force_refresh: bool = True,
) -> tuple[Path, str]:
    release_info = get_latest_github_release_info(repo_url=repo_url, force_refresh=force_refresh)
    if release_info is None:
        raise RuntimeError("No GitHub release available.")

    latest_version = str(release_info.get("tag_name", "")).strip()
    if not latest_version:
        raise RuntimeError("Latest GitHub release has no tag name.")

    if not is_update_available(current_version, latest_version):
        raise RuntimeError("No newer update available.")

    asset = select_release_installer_asset(release_info)
    installer_path = download_release_asset(asset)
    return installer_path, latest_version

#!/bin/bash
set -euo pipefail

# Paths setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PACKAGING_DIR="$ROOT_DIR/packaging"
TEMPLATE_LINUX_DIR="$PACKAGING_DIR/template/linux"
TEMPLATE_DEBIAN_DIR="$TEMPLATE_LINUX_DIR/DEBIAN"
SOURCE_DESKTOP_FILE="$TEMPLATE_LINUX_DIR/smartodoo.desktop"
BUILD_DIR="$PACKAGING_DIR/build"
DIST_APP_DIR="$BUILD_DIR/opt/smartodoo"
DIST_ETC_DIR="$BUILD_DIR/etc/smartodoo"
DIST_DEBIAN_DIR="$BUILD_DIR/DEBIAN"
DIST_DESKTOP_DIR="$BUILD_DIR/usr/share/applications"
DIST_DESKTOP_FILE="$DIST_DESKTOP_DIR/smartodoo.desktop"
SOURCE_CONFIG="$ROOT_DIR/config/config.json"
TARGET_CONFIG="$DIST_ETC_DIR/config.json"
CONTROL_FILE="$TEMPLATE_DEBIAN_DIR/control"

# Package version extraction (source of truth: app/core/version.py)
PACKAGE_VERSION="$(python3 - "$ROOT_DIR" <<'PY'
import sys

root = sys.argv[1]
sys.path.insert(0, root)
from app.core.version import get_smartodoo_version
version = get_smartodoo_version(root_dir=None)
print(version)
PY
)"
if [ -z "$PACKAGE_VERSION" ]; then
	echo "Error: Could not resolve package version from app/core/version.py" >&2
	exit 1
fi

if [ "$PACKAGE_VERSION" = "dev" ]; then
	echo "Error: Resolved package version is 'dev'; set a release version in app/setup.py" >&2
	exit 1
fi

OUTPUT_DEB="$BUILD_DIR/smartodoo-$PACKAGE_VERSION.deb"

# Create necessary directories
mkdir -p "$DIST_APP_DIR" "$DIST_ETC_DIR" "$DIST_DESKTOP_DIR"

# Recraete DEBIAN directory and copy files
rm -rf "$DIST_DEBIAN_DIR"
mkdir -p "$DIST_DEBIAN_DIR"
cp -a "$TEMPLATE_DEBIAN_DIR/." "$DIST_DEBIAN_DIR/"
cp -a "$SOURCE_DESKTOP_FILE" "$DIST_DESKTOP_FILE"

python3 - "$DIST_DEBIAN_DIR/control" "$PACKAGE_VERSION" <<'PY'
import pathlib
import re
import sys

control_path = pathlib.Path(sys.argv[1])
package_version = sys.argv[2]
content = control_path.read_text(encoding="utf-8")

if not re.search(r"^Version:\s*.*$", content, flags=re.MULTILINE):
	raise SystemExit(f"Error: Missing 'Version:' field in {control_path}")

updated = re.sub(r"^Version:\s*.*$", f"Version: {package_version}", content, flags=re.MULTILINE)
control_path.write_text(updated, encoding="utf-8")
PY

# Recreate application directory and copy files
rm -rf "$DIST_APP_DIR/app" "$DIST_APP_DIR/docker" "$DIST_APP_DIR/scripts"
cp -a "$ROOT_DIR/app" "$DIST_APP_DIR/"
cp -a "$ROOT_DIR/docker" "$DIST_APP_DIR/"
cp -a "$ROOT_DIR/scripts/encpass.sh" "$DIST_APP_DIR/encpass.sh"
cp -a "$ROOT_DIR/requirements.txt" "$DIST_APP_DIR/requirements.txt"
cp -a "$ROOT_DIR/.env" "$DIST_APP_DIR/.env"
cp -a "$ROOT_DIR/config/odoo.conf" "$DIST_ETC_DIR/odoo.conf"

mkdir -p "$DIST_APP_DIR/.vscode"
if [ -f "$ROOT_DIR/.vscode/launch.json" ]; then
	cp -a "$ROOT_DIR/.vscode/launch.json" "$DIST_APP_DIR/.vscode/launch.json"
elif [ -f "$ROOT_DIR/launch.json" ]; then
	cp -a "$ROOT_DIR/launch.json" "$DIST_APP_DIR/.vscode/launch.json"
fi

find "$DIST_APP_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +

python3 - "$SOURCE_CONFIG" "$TARGET_CONFIG" <<'PY'
import json
import pathlib
import sys

source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])

payload = json.loads(source.read_text(encoding="utf-8"))
payload.pop("windows", None)

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(payload, indent=4, ensure_ascii=True) + "\n", encoding="utf-8")
PY

cd "$PACKAGING_DIR"
desktop-file-validate build/usr/share/applications/smartodoo.desktop
dpkg-deb --build build "$OUTPUT_DEB"
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

# Package version extraction
PACKAGE_VERSION="$(awk -F': *' '/^Version:/ {print $2; exit}' "$CONTROL_FILE")"
if [ -z "$PACKAGE_VERSION" ]; then
	echo "Error: Could not read Version from $CONTROL_FILE" >&2
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
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PACKAGING_DIR="$ROOT_DIR/packaging"
DIST_LINUX_DIR="$PACKAGING_DIR/dist/linux"
DIST_APP_DIR="$DIST_LINUX_DIR/opt/smartodoo"
DIST_ETC_DIR="$DIST_LINUX_DIR/etc/smartodoo"
SOURCE_CONFIG="$ROOT_DIR/config/config.json"
TARGET_CONFIG="$DIST_ETC_DIR/config.json"

mkdir -p "$DIST_APP_DIR" "$DIST_ETC_DIR"

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
desktop-file-validate dist/linux/usr/share/applications/smartodoo.desktop
sudo dpkg -r smartodoo && dpkg-deb --build dist/linux smartodoo.deb && sudo dpkg -i smartodoo.deb
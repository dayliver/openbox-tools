#!/usr/bin/env bash
# Link ob-grid and ob-layout into PATH and into Openbox's script dir.
# Re-run after moving this folder: the links point back here.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOCAL_BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"
OB_SCRIPTS="$HOME/.config/openbox/scripts"
GRID_CFG="$HOME/.config/ob-grid/config.toml"

if ! /usr/bin/python3 -c 'import Xlib' 2>/dev/null; then
	echo "Missing python-xlib for /usr/bin/python3 — install it: sudo pacman -S python-xlib" >&2
	exit 1
fi

mkdir -p "$LOCAL_BIN" "$OB_SCRIPTS" "$(dirname "$GRID_CFG")" "$HOME/.config/ob-layout/presets"

for tool in ob-grid ob-layout; do
	chmod +x "$ROOT/bin/$tool"
	ln -sfn "$ROOT/bin/$tool" "$LOCAL_BIN/$tool"
	ln -sfn "$ROOT/bin/$tool" "$OB_SCRIPTS/$tool"
	echo "linked: $tool -> $ROOT/bin/$tool"
done

if [[ ! -f "$GRID_CFG" ]]; then
	cp "$ROOT/config.default.toml" "$GRID_CFG"
	echo "Wrote $GRID_CFG"
else
	echo "Keeping existing $GRID_CFG"
fi

"$LOCAL_BIN/ob-grid" --version
"$LOCAL_BIN/ob-layout" --version

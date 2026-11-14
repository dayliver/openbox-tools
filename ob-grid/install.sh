#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BIN_SRC="$ROOT/bin/ob-grid"
LOCAL_BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"
OB_SCRIPTS="$HOME/.config/openbox/scripts"
CFG_DIR="$HOME/.config/ob-grid"
CFG_DST="$CFG_DIR/config.toml"

mkdir -p "$LOCAL_BIN" "$OB_SCRIPTS" "$CFG_DIR"
chmod +x "$BIN_SRC"

ln -sfn "$BIN_SRC" "$LOCAL_BIN/ob-grid"
ln -sfn "$BIN_SRC" "$OB_SCRIPTS/ob-grid"

if [[ ! -f "$CFG_DST" ]]; then
	cp "$ROOT/config.default.toml" "$CFG_DST"
	echo "Wrote $CFG_DST"
else
	echo "Keeping existing $CFG_DST"
fi

case ":$PATH:" in
	*":$LOCAL_BIN:"*) ;;
	*) echo "Note: add $LOCAL_BIN to PATH if needed" ;;
esac

echo "Installed:"
echo "  $LOCAL_BIN/ob-grid -> $BIN_SRC"
echo "  $OB_SCRIPTS/ob-grid -> $BIN_SRC"
"$LOCAL_BIN/ob-grid" --version

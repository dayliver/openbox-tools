#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOCAL_BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"
OB_SCRIPTS="$HOME/.config/openbox/scripts"

mkdir -p "$LOCAL_BIN" "$OB_SCRIPTS" "$HOME/.config/ob-layout/presets"
chmod +x "$ROOT/bin/ob-layout"
ln -sfn "$ROOT/bin/ob-layout" "$LOCAL_BIN/ob-layout"
ln -sfn "$ROOT/bin/ob-layout" "$OB_SCRIPTS/ob-layout"
echo "installed: $LOCAL_BIN/ob-layout"
"$LOCAL_BIN/ob-layout" --version

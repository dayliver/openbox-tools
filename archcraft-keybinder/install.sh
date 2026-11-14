#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

cmd=(uv sync "$@")
printf '+ %s\n' "${cmd[*]}"
exec "${cmd[@]}"

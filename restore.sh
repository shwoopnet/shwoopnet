#!/usr/bin/env bash
# Restores the research databases into kalshi-scalper/data of the current directory's repo checkout (run from the root of a checkout of claude/epic-ptolemy-0amjd9), from the files next to this script.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:-kalshi-scalper/data}"
mkdir -p "$DEST"
for f in "$HERE"/*.sqlite.xz; do xz -dc "$f" > "$DEST/$(basename "${f%.xz}")"; echo "restored $(basename "${f%.xz}")"; done
tar -xJf "$HERE/json_prices_ohlc.tar.xz" -C "$DEST"
echo "done: $DEST"

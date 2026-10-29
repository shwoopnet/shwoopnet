#!/usr/bin/env bash
# AUTO loop (research only): `python -m scalper.autoscore check` once an hour, forever, and the live watcher
# (`python -m scalper.livewatch run`) once a day, on the first hourly pass at or after 00:30 US Central, then the drift
# monitor (`python -m scalper.drift run`, which reuses the report the live watcher just saved in the scratchpad).
# Log: kalshi-scalper/data/autoscore_loop.log (data/ is git-ignored). Start it with:
#   cd kalshi-scalper && nohup bash workers/autoscore_loop.sh >/dev/null 2>&1 &
# Stop it with: pkill -f autoscore_loop.sh
# It never prints a token: the live watcher reads KALSHI_REPORT_TOKEN inside Python only.
cd "$(dirname "$0")/.." || exit 1
export PYTHONPATH=src
LOGF=data/autoscore_loop.log
MARK=data/livewatch_last_day
while true; do
  python -m scalper.autoscore check >>"$LOGF" 2>&1 || echo "autoscore check failed rc=$? at $(date -u)" >>"$LOGF"
  today=$(TZ=America/Chicago date +%F)
  hm=$(TZ=America/Chicago date +%H%M)
  if [ "$(cat "$MARK" 2>/dev/null)" != "$today" ] && [ "$hm" -ge 0030 ]; then
    echo "== livewatch $(TZ=America/Chicago date '+%F %H:%M CT')" >>"$LOGF"
    if python -m scalper.livewatch run >>"$LOGF" 2>&1; then
      echo "$today" >"$MARK"
      echo "== drift $(TZ=America/Chicago date '+%F %H:%M CT')" >>"$LOGF"
      python -m scalper.drift run >>"$LOGF" 2>&1 || echo "drift failed rc=$?" >>"$LOGF"
    else echo "livewatch failed rc=$?" >>"$LOGF"; fi
  fi
  sleep 3600
done

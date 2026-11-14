#!/usr/bin/env python3
"""MADE-UP fixture for the S3 feasibility reader (not Kalshi data). argv[1] = output root."""
import csv, gzip, os, sys
from datetime import datetime, timezone
root = sys.argv[1]
def T(s): return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000)
HDR = ["t_recv_ms", "ticker", "event_ticker", "close_time", "yes_bid", "yes_ask", "no_ask", "yes_bid_size", "volume", "legs"]
def row(t, tk, ev, close, yb, ya, na, size, vol, legs): return [T(t), tk, ev, close, yb, ya, na, size, vol, legs]
snaps = {
 ("2026-11-12", "1200"): [row("2026-11-12T12:00:00Z", "C15", "E15", "2026-11-14T12:00:00Z", .28, .32, .72, 5, 3, 3)],
 ("2026-11-13", "1200"): [
  row("2026-11-13T12:00:00Z", "C1", "E1", "2026-11-14T12:00:00Z", .28, .32, .72, 5, 3, 3),
  row("2026-11-13T12:00:00Z", "C2", "E1", "2026-11-14T12:00:00Z", .28, .32, .72, 5, 3, 3),
  row("2026-11-13T12:00:00Z", "C3", "E3", "2026-11-14T12:00:00Z", 0, .32, 1.00, 5, 3, 3),
  row("2026-11-13T12:00:00Z", "C4", "E4", "2026-11-14T12:00:00Z", .10, .12, .90, 5, 3, 3),
  row("2026-11-13T12:00:00Z", "C5", "E5", "2026-11-14T12:00:00Z", .28, .32, .72, 2, 3, 3),
  row("2026-11-13T12:00:00Z", "C6", "E6", "2026-11-14T12:00:00Z", .28, .32, .72, 5, 0, 3),
  row("2026-11-13T12:00:00Z", "C7", "E7", "2026-11-14T12:00:00Z", .28, .32, .72, 5, 3, 31),
  row("2026-11-13T12:00:00Z", "C8", "E8", "2026-11-13T12:30:00Z", .28, .32, .72, 5, 3, 3),
  row("2026-11-13T12:00:00Z", "C9", "E9", "2026-11-28T12:00:00Z", .28, .32, .72, 5, 3, 3),
  row("2026-11-13T12:00:00Z", "C10", "E10", "2026-11-20T12:00:00Z", .20, .26, .80, 3, 1, 2)],
 ("2026-11-13", "1800"): [
  row("2026-11-13T18:00:00Z", "C1", "E1", "2026-11-14T12:00:00Z", .28, .32, .72, 5, 3, 3),
  row("2026-11-13T18:00:00Z", "C11", "E11", "2026-11-15T18:00:00Z", .40, .42, .60, 4, 2, 2),
  row("2026-11-13T18:00:00Z", "C16", "E16", "2026-11-14T18:00:00Z", .28, 1.00, .70, 5, 3, 3)],
 ("2026-11-14", "1200"): [
  row("2026-11-14T12:00:00Z", "C13", "E13", "2026-11-16T12:00:00Z", .28, .32, .72, 5, 3, 3),
  row("2026-11-14T12:00:00Z", "C14", "E14", "2026-11-16T12:00:00Z", .30, .28, .72, 5, 3, 3)],
}
for (d, hm), rows in snaps.items():
    p = os.path.join(root, "combo", d, hm); os.makedirs(p, exist_ok=True)
    with gzip.open(os.path.join(p, "quotes.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f); w.writerow(HDR); w.writerows(rows)

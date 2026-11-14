#!/usr/bin/env python3 -I
"""Canonical extract of OICORE settled fills for the proven-bar read (Head of R&D, Nov 14, 2026). Local file only, no network, no token.
Usage: python3 -I oicore_extract.py <long report json (hours >= 1440)> <N: 100 or 150> <out.csv>
Rows: strategy OICORE, status filled, result yes or no, readable count, avgFill, avgFee and side. Result exit, unreadable and open (filled, unsettled) are excluded and COUNTED.
Sorted by (ts, ticker), the first N kept, fixed column order and number format, no generatedAt; prints the sha256 of the file and the counts. Fewer than N rows: refuses."""
import hashlib, json, sys
COLS = "ts,ticker,side,count,avgFill,avgFee,result"
def num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or x != x: return None
    return float(x)
def extract(report, n):
    rows, c = [], {"excluded_exit": 0, "excluded_unreadable": 0, "open_unsettled": 0}
    for o in report.get("slotOrders", []):
        if o.get("strategy") != "OICORE" or o.get("status") != "filled": continue
        if o.get("result") == "exit": c["excluded_exit"] += 1; continue
        if o.get("result") not in ("yes", "no"): c["open_unsettled"] += 1; continue
        cnt, fill, fee = num(o.get("count")), num(o.get("avgFill")), num(o.get("avgFee"))
        if cnt is None or fill is None or fee is None or o.get("side") not in ("yes", "no") or not o.get("ts") or "," in str(o.get("ticker", "")):
            c["excluded_unreadable"] += 1; continue
        rows.append((str(o["ts"]), str(o.get("ticker", "")), o["side"], cnt, fill, fee, o["result"]))
    rows.sort(key=lambda r: (r[0], r[1]))
    c["rows_available"] = len(rows)
    if len(rows) < n: raise ValueError("only %d rows, need %d" % (len(rows), n))
    lines = [COLS]
    for ts, tk, side, cnt, fill, fee, res in rows[:n]:
        cs = "%d" % cnt if cnt == int(cnt) else "%.6f" % cnt
        lines.append("%s,%s,%s,%s,%.6f,%.6f,%s" % (ts, tk, side, cs, fill, fee, res))
    return "\n".join(lines) + "\n", c
if __name__ == "__main__":
    text, c = extract(json.load(open(sys.argv[1])), int(sys.argv[2]))
    open(sys.argv[3], "w", newline="").write(text)
    print(json.dumps(dict(c, rows=int(sys.argv[2]), sha256=hashlib.sha256(text.encode()).hexdigest()), indent=1))

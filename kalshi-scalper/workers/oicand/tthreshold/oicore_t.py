#!/usr/bin/env python3
"""OICORE-NC15 threshold T reader, build 1 (Desk B). Rule: Desk A's DESK_A_FROZEN_OICORE_PLACES_DEFINITIONS_NOV13.md v5, section 1 (text only).
Per market (series): one rise per window = open interest of the 1 minute candle ending at close - 180 s minus that of the candle ending at close - 360 s;
trading day = a US Central calendar day of the window's close with at least one window whose two candles exist; T = nearest-rank 90th percentile of the rises
of the LAST 20 trading days (ceil(0.9 n)-th smallest); gate 0: fewer than 20 trading days, T <= 0 or T < 5 contracts: NOT SEATED.
Reads from the lists run ONLY ticker and close_time; from the candle runs ONLY market_ticker, end_period_ts and open_interest (or open_interest_fp).
No price, result, quote, volume or trade is read. Prints aggregates per market. Writes no file. stdlib only.
Usage: oicore_t.py --lists RUN [RUN..] --candles RUN [RUN..] [--series S ...] [--days 20]"""
import argparse, gzip, hashlib, json, math, os, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from deskb_guard import refuse_all as _refuse_all
_refuse_all()
ALLOWED = ["KXHYPE15M", "KXBNB15M"]          # the Head's final scope (Nov 14): the only series readable from the OICAND backfill
EVENT830 = ["KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M"]
CUT_DATES = ("2026-11-05", "2026-11-06", "2026-11-10", "2026-11-12", "2026-11-13")
CT = ZoneInfo("America/Chicago")
MIN_T = 5.0

def ep(iso): return int(datetime.strptime(iso.strip().rstrip("Z").split(".")[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp())

def jload(p): return json.load((gzip.open if p.endswith(".gz") else open)(p, "rt"))

def answer_files(dirs, drops):
    out = []
    for d in dirs:
        mp = os.path.join(d, "manifest.json")
        if os.path.exists(mp):
            for r in json.load(open(mp)).get("rows", []):
                if r.get("status") != 200: drops["manifest_row_not_200"] += 1; continue
                if r.get("truncated"): drops["manifest_row_truncated"] += 1; continue
                fp = os.path.join(d, os.path.basename(r.get("file") or ""))
                if not r.get("file") or not os.path.exists(fp): drops["manifest_row_file_missing"] += 1; continue
                if hashlib.sha256((gzip.open if fp.endswith(".gz") else open)(fp, "rb").read()).hexdigest() != r.get("sha256"): sys.exit("STOP: sha256 mismatch in a run folder")
                out.append(fp)
        else:
            out += sorted(os.path.join(d, n) for n in os.listdir(d) if n.endswith(".json") or n.endswith(".json.gz"))
    return out

def markets_of(p, drops):
    doc = jload(p)
    if not isinstance(doc, dict) or not isinstance(doc.get("markets"), list): drops["answer_without_markets_list"] += 1; return []
    return doc["markets"]

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def oi_of(c):
    """Desk A v3 F1: open_interest_fp is read FIRST; open_interest only if open_interest_fp is ABSENT. null, blank, bool, nan and inf are unreadable (None, a missing candle), with no fallback."""
    for k in ("open_interest_fp", "open_interest"):
        if k in c:
            v = c[k]
            if isinstance(v, bool) or v is None: return None
            try: x = float(v) if not isinstance(v, str) or v.strip() else None
            except (TypeError, ValueError): return None
            return x if x is not None and math.isfinite(x) else None
    return None

def p90(vals):
    s = sorted(vals); return s[max(0, math.ceil(0.9 * len(s) - 1e-9) - 1)]

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--lists", nargs="+", required=True); ap.add_argument("--candles", nargs="+", required=True)
    ap.add_argument("--series", nargs="+", default=ALLOWED); ap.add_argument("--allowed-series", nargs="+", default=ALLOWED)
    ap.add_argument("--cut-series", nargs="+", default=EVENT830); ap.add_argument("--days", type=int, default=20)
    a = ap.parse_args(argv); drops = Counter(); closes = {}; cutn = Counter()
    if any(x not in a.allowed_series for x in a.series): (print("STOP: series not allowed", file=sys.stderr), sys.exit(2))
    for p in answer_files(a.lists, drops):
        for m in markets_of(p, drops):
            tk = m.get("ticker")
            if not isinstance(tk, str) or tk.split("-")[0] not in a.series: continue
            try: c = ep(m["close_time"])
            except Exception: drops["list_unparseable_close"] += 1; continue
            if tk.split("-")[0] in a.cut_series and datetime.fromtimestamp(c, timezone.utc).strftime("%H:%M:%S") == "13:30:00" and datetime.fromtimestamp(c, timezone.utc).strftime("%Y-%m-%d") in CUT_DATES:
                cutn[tk.split("-")[0]] += 1; continue
            closes[tk] = c
    cand, seen = {}, set()
    for p in answer_files(a.candles, drops):
        for m in markets_of(p, drops):
            tk = m.get("market_ticker", m.get("ticker"))
            if tk in seen: sys.exit("STOP: a market_ticker repeats across candle files (run overlap)")
            seen.add(tk)
            if tk not in closes: continue
            oi = {}
            for c in m.get("candlesticks", []):
                try: t = int(c["end_period_ts"])
                except Exception: drops["candle_without_end_period_ts"] += 1; continue
                if t in oi and oi[t] is not None: sys.exit("STOP: duplicate candle timestamp inside one market")
                oi[t] = oi_of(c)
            cand[tk] = oi
    per = defaultdict(lambda: {"days": defaultdict(list), "d": Counter(), "listed": 0, "anyoi": False})
    for tk, c in closes.items():
        s = tk.split("-")[0]; P = per[s]; P["listed"] += 1; oi = cand.get(tk)
        if oi is None: P["d"]["no_candle_answer_for_listed_window"] += 1; continue
        a1, a0 = oi.get(c - 180), oi.get(c - 360)
        if c - 180 not in oi or c - 360 not in oi: P["d"]["missing_candle_at_close_180_or_360"] += 1; continue
        if a1 is None or a0 is None: P["d"]["candle_without_open_interest"] += 1; continue
        P["anyoi"] = True
        day = datetime.fromtimestamp(c, timezone.utc).astimezone(CT).strftime("%Y-%m-%d")
        P["days"][day].append(a1 - a0)
    print("OICORE-NC15 threshold T (reader build 1; open interest rises only; no price, result or quote read)")
    for s in a.series:
        P = per.get(s)
        if P is None: print("%s: no listed windows" % s); continue
        days = sorted(P["days"]); used = days[-a.days:]; rises = [r for d in used for r in P["days"][d]]
        outside = sum(len(P["days"][d]) for d in days[:-a.days]) if len(days) > a.days else 0
        drop = dict(P["d"]); 
        if cutn.get(s): drop["event830_forward_close"] = cutn[s]
        if outside: drop["windows_outside_last_days"] = outside
        dtxt = ", ".join("%s=%d" % kv for kv in sorted(drop.items())) or "none"
        if len(days) < a.days: verdict, T = "NOT SEATED: fewer than %d trading days" % a.days, None
        else:
            T = p90(rises); verdict = "SEATED" if T >= MIN_T else ("NOT SEATED: T under %d" % int(MIN_T) if T > 0 else "NOT SEATED: T of 0 or less")
        print("%s: listed windows %d | windows used (n) %d | trading days available %d, used %d | days used %s | T %s | %s | dropped: %s" % (s, P["listed"], len(rises), len(days), len(used), ("%s to %s" % (used[0], used[-1])) if used else "none", "n/a" if T is None else ("%g" % T), verdict, dtxt))
    print("markets with no open interest at all: %d" % sum(1 for s in a.series if s in per and not per[s]["anyoi"]))
    print("global drops: " + (", ".join("%s=%d" % kv for kv in sorted(drops.items())) or "none"))
    return 0

if __name__ == "__main__": sys.exit(main())

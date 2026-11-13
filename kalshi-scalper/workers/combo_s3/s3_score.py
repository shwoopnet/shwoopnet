#!/usr/bin/env python3
"""S3, combo house side: paper scorer. Registered Nov 12, 2026, BEFORE any scoring.
Registration: workers/S3_COMBO_HOUSE_SIDE_REGISTRATION.md (same constants).

Paper only. Reads the combo recorder's files (branch combo-data, public data):
  combo/DATE/HHMM/quotes.csv.gz   and, once a day,   combo/DATE/HHMM/results.csv.gz
No order, no key, no network.

Usage: python3 s3_score.py <path to a checkout of combo-data> <read time, ISO UTC> [dev|heldout]
"""
import csv
import glob
import gzip
import os
import random
import sys
from datetime import datetime, timezone
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
from deskb_guard import refuse_all as _refuse_all
_refuse_all()   # standing rule (h): refuse any HELDOUT_ folder before the first open or glob

# ---- pinned constants (the registration carries the same values) ----
START_UTC = "2026-11-13T00:00:00Z"        # development entries start here
HELDOUT_START_UTC = "2026-11-26T00:00:00Z"  # entries from here on are held-out
HELDOUT_END_UTC = "2026-12-10T00:00:00Z"
READ1_NOT_BEFORE = "2026-11-26T00:00:00Z"   # development read, once
READ2_NOT_BEFORE = "2026-12-12T00:00:00Z"   # held-out read, once
P_MIN, P_MAX = 0.60, 0.90                 # price paid for NO, after the 1c slip
SLIP = 0.01
MIN_SIZE = 3.0                            # contracts resting at the NO ask (the YES bid size)
LEGS_MIN, LEGS_MAX = 2, 30
CLOSE_MIN_S, CLOSE_MAX_S = 3600, 14 * 86400
DUE_AFTER_CLOSE_S = 48 * 3600             # a fill is due this long after its close
MAX_FILLS_PER_SNAPSHOT = 10
PROBE_DOLLARS = 2.0
KILL_DOLLARS = -40.0                      # running paper net at $2 a fill
KILL_PF, KILL_N = 1.2, 100
BAR_PER_DOLLAR, BAR_N = 0.10, 100
MIN_CLUSTERS = 10
MAX_CLUSTER_SHARE = 0.30
MAX_UNRESOLVED_SHARE = 0.10
BOOT_N, BOOT_SEED = 2000, 20261112
WEATHER_PREFIXES = ("KXHIGH", "KXLOW", "KXTEMP", "KXRAIN", "KXSNOW", "KXHURR", "KXTORN", "KXWIND")   # clarifying line of Nov 13, 2026, 00:20Z


def ts(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def fee(p):
    return 0.07 * p * (1.0 - p)


def leg_series(text):
    """Series tickers of a combo's legs from the recorder's leg_tickers column ("TICKER:side|TICKER:side|...")."""
    out = []
    for part in (text or "").split("|"):
        tk = part.strip().split(":")[0].strip()
        if tk:
            out.append(tk.split("-")[0])
    return out


LEGS = {}   # combo ticker -> leg series, from any snapshot that stored them (a combo's legs do not change)


def load(root):
    snaps, results = [], {}
    for q in sorted(glob.glob(os.path.join(root, "combo", "*", "*", "quotes.csv.gz"))):
        rows = list(csv.DictReader(gzip.open(q, "rt", newline="")))
        if rows:
            snaps.append(rows)
        for r in rows:
            ls = leg_series(r.get("leg_tickers"))
            if ls and r.get("ticker"):
                LEGS.setdefault(r["ticker"], ls)
    for r in sorted(glob.glob(os.path.join(root, "combo", "*", "*", "results.csv.gz"))):
        for row in csv.DictReader(gzip.open(r, "rt", newline="")):
            if row.get("ticker") and row.get("result"):
                results.setdefault(row["ticker"], row["result"].strip().lower())
    return snaps, results


def qualifies(r):
    t = (num(r.get("t_recv_ms")) or 0) / 1000.0
    na, size, vol, legs = num(r.get("no_ask")), num(r.get("yes_bid_size")), num(r.get("volume")), num(r.get("legs"))
    if na is None or na >= 1.0 or size is None or vol is None or legs is None or not r.get("close_time"):
        return None
    p = na + SLIP
    try:
        left = ts(r["close_time"]) - t
    except ValueError:
        return None
    if not (P_MIN <= p <= P_MAX and size >= MIN_SIZE and vol > 0 and LEGS_MIN <= legs <= LEGS_MAX and CLOSE_MIN_S <= left <= CLOSE_MAX_S):
        return None
    return {"t": t, "ticker": r["ticker"], "event": r.get("event_ticker", ""), "p": p, "close": ts(r["close_time"]), "legs": int(legs)}


def fills(snaps, lo, hi):
    seen_t, seen_e, out = set(), set(), []
    for rows in snaps:
        cand = [f for f in (qualifies(r) for r in rows) if f and lo <= f["t"] < hi]
        cand.sort(key=lambda f: f["ticker"])
        n = 0
        for f in cand:
            if n >= MAX_FILLS_PER_SNAPSHOT or f["ticker"] in seen_t or (f["event"] and f["event"] in seen_e):
                continue
            seen_t.add(f["ticker"])
            seen_e.add(f["event"])
            out.append(f)
            n += 1
    out.sort(key=lambda f: (f["t"], f["ticker"]))
    return out


def per_dollar(rows):
    cost = sum(f["cost"] for f in rows)
    return sum(f["net"] for f in rows) / cost if cost else 0.0


def pf(rows):
    won = sum(f["net"] for f in rows if f["net"] > 0)
    lost = -sum(f["net"] for f in rows if f["net"] < 0)
    return won / lost if lost else float("inf")


def describe(name, settled, due_n, unresolved, verdict):
    """The registered figures over one set of settled fills. Only the all-combos call carries the registered verdict;
    the no-weather-leg call prints the same figures as information (clarifying line of Nov 13, 2026)."""
    tag = "" if verdict else " [information only; the registered verdict is the all-combos line]"
    kill, label = ("KILLED", "LABEL") if verdict else ("would read KILLED", "would read")
    print(f"== {name}: settled {len(settled)}{tag}")
    # kill 1: running paper net at $2 a fill, in fill order
    run, killed_at = 0.0, None
    for i, f in enumerate(settled):
        run += f["net"] * PROBE_DOLLARS / f["cost"]
        if run < KILL_DOLLARS:
            killed_at = i + 1
            break
    if killed_at:
        print(f"{kill}: running paper net fell under ${KILL_DOLLARS:.0f} at settled fill {killed_at}")
        return
    if len(settled) < BAR_N:
        print(f"{label}: no evidence at n = {len(settled)} (need {BAR_N} settled fills)")
        return
    if due_n and unresolved / due_n > MAX_UNRESOLVED_SHARE:
        print(f"{label}: NOT_ENOUGH_DATA (unresolved share {unresolved/due_n:.0%} is over {MAX_UNRESOLVED_SHARE:.0%}); figures below are a description")
    # kill 2: cash PF on the FIRST 100 settled fills
    first = settled[:KILL_N]
    print(f"first {KILL_N} settled: wins {sum(1 for f in first if f['net'] > 0)} | cash PF {pf(first):.2f} | net per dollar {per_dollar(first):+.3f}")
    if pf(first) < KILL_PF:
        print(f"{kill}: cash PF under {KILL_PF} at n = {KILL_N}")
        return
    # the owner's bar: on EVERY settled fill of this window (at least 100)
    ppd, n = per_dollar(settled), len(settled)
    wins = sum(1 for f in settled if f["net"] > 0)
    print(f"all {n} settled: wins {wins} | cash PF {pf(settled):.2f} | net per dollar {ppd:+.3f} | paper net at $2 a fill ${sum(f['net'] * PROBE_DOLLARS / f['cost'] for f in settled):+.2f}")
    half = n // 2
    h1, h2 = per_dollar(settled[:half]), per_dollar(settled[half:])
    clusters = {}
    for f in settled:
        clusters.setdefault(datetime.fromtimestamp(f["close"], timezone.utc).date().isoformat(), []).append(f)
    net_total = sum(f["net"] for f in settled)
    top = max((sum(f["net"] for f in v) for v in clusters.values()), default=0.0)
    rng = random.Random(BOOT_SEED)
    keys = sorted(clusters)
    boots = sorted(per_dollar([f for k in (rng.choice(keys) for _ in keys) for f in clusters[k]]) for _ in range(BOOT_N))
    p5 = boots[int(0.05 * BOOT_N)]
    print(f"halves net per dollar {h1:+.3f} / {h2:+.3f} | close dates {len(clusters)} | largest close date share of net {top / net_total if net_total > 0 else float('nan'):.0%} | bootstrap 5th percentile by close date {p5:+.3f}")
    ok = (ppd >= BAR_PER_DOLLAR and h1 > 0 and h2 > 0 and len(clusters) >= MIN_CLUSTERS and net_total > 0 and top / net_total <= MAX_CLUSTER_SHARE and p5 > 0
          and not (due_n and unresolved / due_n > MAX_UNRESOLVED_SHARE))
    print(f"{label}: " + ("paper edge shown (unproven)" if ok else "bar not met"))
    if unresolved:
        print(f"note: {unresolved} due fills have no recorded result; if every one of them lost, the picture is worse than shown")


def main():
    root, read_iso = sys.argv[1], sys.argv[2]
    which = sys.argv[3] if len(sys.argv) > 3 else "dev"
    read_t = ts(read_iso)
    lo, hi, gate = (ts(START_UTC), ts(HELDOUT_START_UTC), ts(READ1_NOT_BEFORE)) if which == "dev" else (ts(HELDOUT_START_UTC), ts(HELDOUT_END_UTC), ts(READ2_NOT_BEFORE))
    if read_t < gate:
        print("REFUSED: this read is not allowed before its pinned date")
        return
    snaps, results = load(root)
    fl = fills(snaps, lo, hi)
    # weather legs (clarifying line of Nov 13, 2026): known from the recorder's leg_tickers column, by series prefix
    seen = {}
    for f in fl:
        ls = LEGS.get(f["ticker"])
        f["legs_known"] = bool(ls)
        f["weather"] = bool(ls) and any(x.startswith(WEATHER_PREFIXES) for x in ls)
        for x in ls or []:
            seen[x] = seen.get(x, 0) + 1
    due = [f for f in fl if f["close"] + DUE_AFTER_CLOSE_S <= read_t]
    settled, unresolved, other = [], 0, 0
    unresolved_nw = 0
    for f in due:
        res = results.get(f["ticker"])
        if res is None:
            unresolved += 1
            unresolved_nw += f["legs_known"] and not f["weather"]
            continue
        if res not in ("yes", "no"):
            other += 1
            continue
        f["cost"] = f["p"] + fee(f["p"])
        f["net"] = (1.0 - f["cost"]) if res == "no" else -f["cost"]
        settled.append(f)
    print(f"{which}: paper fills {len(fl)} | due {len(due)} | settled {len(settled)} | unresolved {unresolved} | other result {other}")
    print(f"legs: paper fills with leg tickers stored {sum(1 for f in fl if f['legs_known'])} | leg unknown {sum(1 for f in fl if not f['legs_known'])} | with a weather leg {sum(1 for f in fl if f['weather'])}")
    print("leg series seen in paper fills, with counts: " + (", ".join("%s %d" % kv for kv in sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))) or "none"))
    describe("ALL COMBOS (the registered line)", settled, len(due), unresolved, True)
    nw = [f for f in settled if f["legs_known"] and not f["weather"]]
    due_nw = sum(1 for f in due if f["legs_known"] and not f["weather"])
    describe("NO WEATHER LEG (legs known, no leg on a weather series)", nw, due_nw, unresolved_nw, False)


if __name__ == "__main__":
    main()

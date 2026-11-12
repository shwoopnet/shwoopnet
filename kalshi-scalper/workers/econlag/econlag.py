#!/usr/bin/env python3
"""ECONLAG (Idea Desk B, card 2): the staged reader. Committed Nov 12, 2026, BEFORE the calendar
pull (ECONLAG_CALENDAR) was dispatched. Registration: workers/IDEA_DESK_B_PROTOCOLS.md,
protocol 2 with amendments 1 and 2. Try number 1 against the slow-family paper screen
(docs/POLITICS_RULES.md section 8). No main-bar claim is made from this read.

Stages (each reads only kalshi-pull answer folders: manifest.json plus 0001.json.gz ...):
  calendar  <stage 1 run> <out>            print calendar, count of print days, job part A
  build-b   <out> <part A run>             choose F for each print, job part B
  scan      <out> <part B run>             the TRIGGER SCAN: a count, no outcome is read
  score     <out> <plan.json> <runs...>    the one read against the paper screen

Stop rules (amendment 2): under 30 print days after `calendar`, or under 30 print days with a
trigger after `scan`, ends the card at "no evidence at n = x" and nothing more is pulled.

No network, no key, no order. Public market data only.
"""
import csv
import gzip
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

# ---- pinned constants (the registration carries the same values) ----
RANGE_START = "2024-10-01T00:00:00Z"
RANGE_END = "2026-10-31T23:59:59Z"       # the pinned cutoff: no print after this is used
HIST_CUTOFF = "2026-09-12T00:00:00Z"     # markets settled before this are served by the historical endpoint
PRINT_SERIES = ("KXCPI", "KXPAYROLLS", "KXPCECORE", "KXFEDDECISION")
FAST_SERIES = "KXFEDDECISION"
TRIGGER = 0.08                           # F's mid move from T-5 to T+10 minutes
PRE_S, POST_S = 300, 600
BETA_DAYS, BETA_MIN_OBS = 60, 20
R2_MIN, SLOPE_MIN, SLOPE_MAX = 0.2, 0.2, 3.0
LAG_SHARE, OWED_MIN = 0.25, 0.04
ASK_MIN, ASK_MAX, SPREAD_MAX = 0.10, 0.80, 0.03
SLIP = 0.01
EXIT_A_S, EXIT_B_S, EXIT_LOOKBACK_S = 4 * 3600, 24 * 3600, 1800
MIN_EVENTS = 30
PF_BAR = 1.3
DROP_MAX = 0.10
LABEL_ORDER = {"S1": 0, "S2": 1, "S3": 2, "S4": 3}
STOP = {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
        "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}


def ts(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def day(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")


def fee(p):
    return 0.07 * p * (1.0 - p)


def price(side):
    if not isinstance(side, dict):
        return None
    for k in ("close_dollars", "close"):
        v = side.get(k)
        if v in (None, ""):
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        return v / 100.0 if v > 1.0 else v
    return None


def load_run(folder):
    """[(manifest row, decoded body)] of one pull run; rows that did not answer 200 or did not decode are skipped."""
    man = json.load(open(os.path.join(folder, "manifest.json")))
    out = []
    for row in man.get("rows", []):
        if row.get("status") != 200:
            continue
        try:
            out.append((row, json.load(gzip.open(os.path.join(folder, row["file"]), "rt"))))
        except (OSError, ValueError, KeyError):
            continue
    return out


def candle_store(folders):
    """{(ticker, period): {end_ts: (yes bid, yes ask)}} from every candle answer in the folders."""
    store = defaultdict(dict)
    for folder in folders:
        for row, body in load_run(folder):
            period = int(row.get("params", {}).get("period_interval", 0) or 0)
            found = {}
            hint = row.get("path", "").split("/markets/")[-1].split("/")[0] if "/candlesticks" in row.get("path", "") and "/markets/" in row.get("path", "") else None

            def walk(node, tk):
                if isinstance(node, dict):
                    tk = node.get("market_ticker") or node.get("ticker") or tk
                    c = node.get("candlesticks")
                    if isinstance(c, list) and c and isinstance(c[0], dict) and "end_period_ts" in c[0] and tk:
                        found.setdefault(tk, []).extend(c)
                    for v in node.values():
                        walk(v, tk)
                elif isinstance(node, list):
                    for v in node:
                        walk(v, tk)
            walk(body, hint)
            for tk, cs in found.items():
                for c in cs:
                    store[(tk, period)][int(c["end_period_ts"])] = (price(c.get("yes_bid")), price(c.get("yes_ask")))
    return store


def mid(q):
    if not q:
        return None
    b, a = q
    return (a + b) / 2.0 if (a is not None and b is not None and b > 0 and 0 < a <= 1 and a >= b) else None


def at_or_before(series, t, back):
    """The quote of the latest candle ending in (t - back, t]."""
    best = None
    for e in series:
        if t - back < e <= t and (best is None or e > best):
            best = e
    return series.get(best) if best is not None else None


def read_csv(path):
    return list(csv.DictReader(open(path, newline="")))


def write_csv(path, cols, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)


def job(job_id, purpose, heldout, endpoints, series, tickers, reqs, cap, notes, status="active"):
    return {"job_id": job_id, "owner": "DESK_B", "registration": "kalshi-scalper/workers/IDEA_DESK_B_PROTOCOLS.md", "purpose": purpose, "heldout": heldout,
            "allowed_endpoints": endpoints, "series_allowlist": series, "ticker_allowlist": tickers, "max_requests": cap, "requests": reqs, "notes": notes,
            "status": status, "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0, "stop_rules": STOP}


CANDLE_EPS = [{"name": "candles_live", "method": "GET", "path_pattern": "/series/(?P<series>[A-Z0-9]{2,32})/markets/(?P<ticker>[A-Z0-9][A-Z0-9._-]{0,63})/candlesticks",
               "params_allowed": ["start_ts", "end_ts", "period_interval"]},
              {"name": "candles_hist", "method": "GET", "path_pattern": "/historical/markets/(?P<ticker>[A-Z0-9][A-Z0-9._-]{0,63})/candlesticks",
               "params_allowed": ["start_ts", "end_ts", "period_interval"]}]


def candle_req(rid, ticker, hist, start, end, period):
    path = ("/historical/markets/%s/candlesticks" % ticker) if hist else ("/series/%s/markets/%s/candlesticks" % (ticker.split("-")[0], ticker))
    return {"id": rid, "path": path, "params": {"start_ts": int(start), "end_ts": int(end), "period_interval": period}}


# ---------------------------------------------------------------- stage 1: calendar
def cmd_calendar(run, out):
    os.makedirs(out, exist_ok=True)
    lo, hi, cut = ts(RANGE_START), ts(RANGE_END), ts(HIST_CUTOFF)
    events = defaultdict(lambda: {"closes": Counter(), "markets": {}})
    for row, body in load_run(run):
        series = row.get("params", {}).get("series_ticker")
        if series not in PRINT_SERIES or not isinstance(body.get("markets"), list):
            continue
        for m in body["markets"]:
            try:
                t = ts(m["close_time"])
            except (KeyError, ValueError, TypeError):
                continue
            e = events[(series, m.get("event_ticker", ""))]
            e["closes"][t] += 1
            e["markets"][m["ticker"]] = (m.get("open_time") or "", t, row["id"].startswith("hist_") or t < cut)
    prints, meetings = [], []
    for (series, ev), e in sorted(events.items()):
        t = e["closes"].most_common(1)[0][0]
        if series == FAST_SERIES:
            for tk, (op, c, hist) in sorted(e["markets"].items()):
                meetings.append([ev, t, tk, op, int(hist)])
        if lo <= t <= hi:
            prints.append([series, ev, t, datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), day(t)])
    prints.sort(key=lambda r: r[2])
    write_csv(os.path.join(out, "prints.csv"), ["series", "event", "t", "iso", "day"], prints)
    write_csv(os.path.join(out, "meetings.csv"), ["event", "t_meeting", "ticker", "open_time", "hist"], meetings)
    days = sorted({r[4] for r in prints})
    print(f"prints in the pinned range {len(prints)} {dict(Counter(r[0] for r in prints))} | print days {len(days)} | Fed decision markets {len(meetings)}")
    if len(days) < MIN_EVENTS:
        print(f"STOP: no evidence at n = {len(days)} (under {MIN_EVENTS} print days); nothing more is pulled")
        return
    reqs, tickers = [], []
    for ev, t, tk, op, hist in meetings:
        if t < lo:                                       # a meeting before the range cannot be F or a slow market of any print in it
            continue
        try:
            start = ts(op)
        except (ValueError, TypeError):
            start = t - 400 * 86400
        reqs.append(candle_req("d_%s" % tk, tk, hist, max(start, t - 400 * 86400), t, 1440))
        tickers.append(tk)
    j = job("ECONLAG_A", "ECONLAG part A (paper screen, try 1): daily candles of the settled Fed decision markets, to choose the fast market F for each print and, later, for the betas. No one-minute candle and no outcome.",
            "ECONLAG amendment 2: prints from 2024-10-01 to 2026-10-31 only (pinned cutoff)", CANDLE_EPS, [FAST_SERIES], sorted(set(tickers)), reqs, min(90, len(reqs) + 5),
            "One daily-candle request per settled Fed decision market of a meeting inside the range. Built by workers/econlag/econlag.py calendar from the stage 1 answers.")
    json.dump(j, open(os.path.join(out, "ECONLAG_A.json"), "w"), indent=1)
    print(f"job ECONLAG_A: {len(reqs)} requests (cap {j['max_requests']})" + (" | OVER THE 90 CAP: cut to the cap, later meetings first, before sending" if len(reqs) > 90 else ""))


# ---------------------------------------------------------------- stage 2: choose F, build part B
def meetings_of(out):
    by = defaultdict(lambda: {"t": 0, "markets": []})
    for r in read_csv(os.path.join(out, "meetings.csv")):
        by[r["event"]]["t"] = int(r["t_meeting"])
        by[r["event"]]["markets"].append((r["ticker"], r["hist"] == "1"))
    return sorted(((v["t"], ev, v["markets"]) for ev, v in by.items()))


def day_before_mid(store, ticker, t):
    series = store.get((ticker, 1440), {})
    ends = [e for e in series if e <= t - 3600]
    return mid(series[max(ends)]) if ends else None


def cmd_build_b(out, run_a):
    store = candle_store([run_a])
    meets = meetings_of(out)
    rows, reqs, tickers, no_f = [], [], [], 0
    for p in read_csv(os.path.join(out, "prints.csv")):
        t = int(p["t"])
        nxt = [m for m in meets if m[0] > t + 3600]      # the next meeting strictly after the print
        choice = None
        if nxt:
            quoted = [(day_before_mid(store, tk, t), tk, hist) for tk, hist in nxt[0][2]]
            quoted = [q for q in quoted if q[0] is not None]
            if quoted:
                choice = max(quoted, key=lambda q: (q[0], q[1]))
        if choice is None:
            no_f += 1
            continue
        pid = "%s_%s" % (p["series"], p["event"])
        rows.append([pid, p["series"], p["event"], t, p["day"], nxt[0][1], choice[1], int(choice[2])])
        reqs.append(candle_req("m_%s" % pid, choice[1], choice[2], t - 600, t + 900, 1))
        tickers.append(choice[1])
    write_csv(os.path.join(out, "f_choice.csv"), ["print", "series", "event", "t", "day", "f_meeting", "f_ticker", "hist"], rows)
    j = job("ECONLAG_B", "ECONLAG part B (paper screen, try 1): one read of one-minute candles around each print for the fast market F, for the trigger scan. A count only; no outcome is read.",
            "ECONLAG amendment 2: prints from 2024-10-01 to 2026-10-31 only (pinned cutoff)", CANDLE_EPS, [FAST_SERIES], sorted(set(tickers)), reqs, min(100, len(reqs) + 5),
            "One request per print, T minus 10 minutes to T plus 15 minutes. Built by workers/econlag/econlag.py build-b.")
    json.dump(j, open(os.path.join(out, "ECONLAG_B.json"), "w"), indent=1)
    print(f"prints with a fast market chosen {len(rows)} | prints with none (no settled next meeting, or no quote the day before) {no_f} | job ECONLAG_B: {len(reqs)} requests (cap {j['max_requests']})")
    if len(reqs) > 100:
        print("OVER THE 100 CAP for part B: do not send; report the count to the Head of R&D first")


# ---------------------------------------------------------------- stage 3: the trigger scan (a count)
def move_around(series, t):
    a = mid(at_or_before(series, t - PRE_S, 300))
    b = mid(at_or_before(series, t + POST_S, 300))
    return None if a is None or b is None else b - a


def cmd_scan(out, run_b):
    store = candle_store([run_b])
    rows, quoted = [], 0
    for r in read_csv(os.path.join(out, "f_choice.csv")):
        mv = move_around(store.get((r["f_ticker"], 1), {}), int(r["t"]))
        if mv is None:
            continue
        quoted += 1
        if abs(mv) >= TRIGGER - 1e-9:
            rows.append([r["print"], r["series"], r["event"], r["t"], r["day"], r["f_meeting"], r["f_ticker"], "%.4f" % mv])
    write_csv(os.path.join(out, "triggers.csv"), ["print", "series", "event", "t", "day", "f_meeting", "f_ticker", "f_move"], rows)
    days = sorted({r[4] for r in rows})
    all_days = {r["day"] for r in read_csv(os.path.join(out, "prints.csv"))}
    print(f"print days in the range {len(all_days)} | prints with a two-sided fast quote at both minutes {quoted} | prints with the trigger {len(rows)} | PRINT DAYS WITH THE TRIGGER {len(days)}")
    if len(days) < MIN_EVENTS:
        print(f"STOP: no evidence at n = {len(days)} (under {MIN_EVENTS} print days with the trigger; a day without it cannot have a trade). Nothing more is pulled.")
    else:
        print("The scan clears the stop rule: part C (the slow markets on trigger days) may be built and reviewed.")


# ---------------------------------------------------------------- stage 4: the one read against the screen
def beta(store, f, m, t, print_days):
    fs, ms = store.get((f, 1440), {}), store.get((m, 1440), {})
    ends = sorted(e for e in fs if e in ms and e <= t - 3600 and mid(fs[e]) is not None and mid(ms[e]) is not None)[-(BETA_DAYS + 1):]
    xs, ys = [], []
    for a, b in zip(ends, ends[1:]):
        if day(b) in print_days:
            continue                                      # print days are excluded from the fit
        xs.append(mid(fs[b]) - mid(fs[a]))
        ys.append(mid(ms[b]) - mid(ms[a]))
    n = len(xs)
    if n < BETA_MIN_OBS:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0 or syy <= 0:
        return None
    slope, r2 = sxy / sxx, (sxy * sxy) / (sxx * syy)
    return slope if (r2 >= R2_MIN and SLOPE_MIN <= abs(slope) <= SLOPE_MAX) else None


def exit_value(series, t_exit, long_yes):
    best = None
    for e in sorted(series):
        if t_exit - EXIT_LOOKBACK_S < e <= t_exit:
            b, a = series[e]
            px = b if long_yes else (None if a is None else 1.0 - a)
            if px is not None and px > 0:
                best = px
    return best


def candidate(store, trig, label, ticker, print_days):
    t, f = int(trig["t"]), trig["f_ticker"]
    slope = beta(store, f, ticker, t, print_days)
    if slope is None:
        return None
    ms = store.get((ticker, 1), {})
    mv = move_around(ms, t)
    q = at_or_before(ms, t + POST_S, 300)
    if mv is None or not q or q[0] is None or q[1] is None:
        return None
    implied = slope * float(trig["f_move"])
    direction = 1.0 if implied > 0 else -1.0
    moved = direction * mv
    owed = abs(implied) - moved
    if not (moved < LAG_SHARE * abs(implied) and owed >= OWED_MIN - 1e-9):
        return None
    long_yes = direction > 0
    ask = q[1] if long_yes else 1.0 - q[0]
    if not (ASK_MIN <= ask <= ASK_MAX and (q[1] - q[0]) <= SPREAD_MAX + 1e-9):
        return None
    paid = ask + SLIP
    cost = paid + fee(paid)
    res = {}
    for arm, hold in (("A", EXIT_A_S), ("B", EXIT_B_S)):
        px = exit_value(ms, t + hold, long_yes)
        res[arm] = None if px is None else (px - SLIP) - fee(max(px - SLIP, 0.0)) - cost
    return {"print": trig["print"], "day": trig["day"], "t": t, "label": label, "ticker": ticker, "owed": owed, "net": res}


def pf(vals):
    won = sum(v for v in vals if v > 0)
    lost = -sum(v for v in vals if v < 0)
    return won / lost if lost > 0 else float("inf")


def cmd_score(out, plan_path, runs):
    marker = os.path.join(out, "READ_ONCE_SCORE.txt")
    if os.path.exists(marker):
        print("REFUSED: the read against the screen has already been made (READ_ONCE_SCORE.txt exists)")
        return
    plan = json.load(open(plan_path))
    store = candle_store(runs)
    print_days = {r["day"] for r in read_csv(os.path.join(out, "prints.csv"))}
    trigs = read_csv(os.path.join(out, "triggers.csv"))
    by_day = defaultdict(list)
    for trig in trigs:
        for c in plan.get(trig["print"], []):
            cand = candidate(store, trig, c["label"], c["ticker"], print_days)
            if cand:
                by_day[trig["day"]].append(cand)
    chosen = [min(v, key=lambda c: (-c["owed"], c["t"], LABEL_ORDER.get(c["label"], 9))) for _d, v in sorted(by_day.items())]
    others = sum(len(v) for v in by_day.values()) - len(chosen)
    open(marker, "w").write("ECONLAG read against the paper screen made at %s\n" % datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"))
    trig_days = len({t["day"] for t in trigs})
    print(f"print days with the trigger {trig_days} | print days with a qualifying trade {len(chosen)} | other qualifying markets (description only) {others}")
    kept = [c for c in chosen if c["net"]["A"] is not None]
    dropped = len(chosen) - len(kept)
    print(f"arm A (exit four hours after the print): trades {len(chosen)} | dropped for no bid before the exit {dropped}")
    n = len(kept)
    if n < MIN_EVENTS:
        print(f"LABEL: no evidence at n = {n} (the screen needs {MIN_EVENTS} independent print days with a trade)")
    else:
        vals = [c["net"]["A"] for c in kept]
        h = n // 2
        h1, h2 = sum(vals[:h]), sum(vals[h:])
        wins = sum(1 for v in vals if v > 0)
        print(f"events {n} | winning days {wins} | cash PF {pf(vals):.2f} | net per contract {sum(vals) / n * 100:+.2f}c | halves net {h1 * 100:+.1f}c / {h2 * 100:+.1f}c")
        if chosen and dropped / len(chosen) > DROP_MAX:
            print(f"LABEL: no evidence (data limited): {dropped} of {len(chosen)} trades had no bid before the exit")
        elif pf(vals) >= PF_BAR and h1 > 0 and h2 > 0:
            print("LABEL: on the paper list (unproven). Try number 1 against the screen; about 1 in 7 rules with no edge pass it at n = 30.")
        else:
            print("LABEL: off the list (failed the screen)")
    kb = [c["net"]["B"] for c in chosen if c["net"]["B"] is not None]
    if kb:
        print(f"description only, arm B (exit 24 hours after the print): trades {len(kb)} | cash PF {pf(kb):.2f} | net per contract {sum(kb) / len(kb) * 100:+.2f}c")
    print("not computed here: the placebo (the same rule one week earlier); it needs its own candles and is asked for only if the card is listed")


def main():
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "calendar":
        cmd_calendar(a[1], a[2])
    elif len(a) >= 3 and a[0] == "build-b":
        cmd_build_b(a[1], a[2])
    elif len(a) >= 3 and a[0] == "scan":
        cmd_scan(a[1], a[2])
    elif len(a) >= 4 and a[0] == "score":
        cmd_score(a[1], a[2], a[3:])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

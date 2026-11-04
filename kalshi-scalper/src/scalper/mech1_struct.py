"""MECH1S (the structural-mechanism worker; ID MECH1 was already used by the tape worker, so files are MECH1S) (README "MECH1S structural mechanisms"; workers/MECH1S_REGISTRATION.md): twelve model-free structural mechanisms on the CHEAP side
(ask 3c to 30c), census on cached development data, then the top 3 by (eligible cheap rows x story strength) scored ONCE.
Cheap side only (owner rule): no entry above 0.30 is ever built, counted, scored or printed. No Kalshi fetch. Frozen third untouched
(only markets that have a development candle record are used, as CALIB1 and LIQ1; newlist1 is cut at its t2).

Usage: python3 -I -m scalper.mech1_struct extract   rows (NO outcome) -> MECH1S_OUT/rows.jsonl ; settled results -> MECH1S_OUT/res.json ; COUNTS ONLY
       python3 -I -m scalper.mech1_struct census    eligible cheap rows per mechanism (features only, no outcome is read)
       python3 -I -m scalper.mech1_struct score     ONE run of the registered top 3 -> workers/MECH1S_RESULT.json (refuses a second run)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from scalper import calib1 as C

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKERS, DATA = ROOT / "workers", ROOT / "data"
OUT = Path(os.environ.get("MECH1S_OUT", "/tmp/mech1s"))
ET = ZoneInfo("America/New_York")
SEED, BOOT = 20261104, 2000
MAX_PER_EVENT = 2
MIN_TRADES, MIN_PART = 150, 30
CAP = 0.30

# ---- registered constants (workers/MECH1S_REGISTRATION.md) ----
FALL_RATIO, FALL_MIN = 0.8, 0.02          # PATH_FALL: ask <= 0.8 x price an hour earlier and at least 2c lower
RISE_RATIO = 1.25                          # placebo arm
COLLAPSE_RATIO, COLLAPSE_MIN = 2.0, 0.05   # PEAK_COLLAPSE: earlier path high >= 2 x ask and 5c above it
OPEN_RATIO = 2.0                           # VS_OPEN: first quoted price >= 2 x ask
FEE_WASTE_LO, FEE_WASTE_HI = 0.02, 0.08    # cents per contract at C = 10
SPREAD_TIGHT, SPREAD_WIDE, SPREAD_ASK_MIN = 1.0, 5.0, 0.10
SHOULDER_HI, TAIL_LO = 0.30, 0.10
MIN_SIB_QUOTES, MIN_LADDER = 4, 5
STRENGTH = {"INTERIOR": 4, "SHOULDER": 3, "PEAK_COLLAPSE": 3, "PATH_FALL": 3, "VS_OPEN": 2, "YDAY": 2, "NONROUND": 2,
            "OFFHOURS": 2, "WEEKEND": 2, "VOLRANK": 2, "SPREADM": 2, "FEE_WASTE": 1}


# ---------------------------------------------------------------- feature helpers (no outcome anywhere)
def cheap_price(side, b, a):
    """Cheap side's ask-equivalent from a (bid, ask) candle: yes -> ask, no -> 1 - bid. None if the candle cannot price it."""
    if side == "yes":
        return a if a is not None and 0 < a < 1 else None
    return round(1 - b, 4) if b is not None and 0 < b < 1 else None


def strike_key(ticker):
    """Numeric strike label after the last '-' (e.g. '4.4550', 'T50', 'B4.5'); None when the suffix is not a number (team or name outcomes)."""
    m = re.match(r"^[A-Za-z]{0,2}(-?\d+(?:\.\d+)?)$", ticker.rsplit("-", 1)[-1])
    return float(m.group(1)) if m else None


def fee_waste_c(p, c=10):
    """Cents per contract the fee rounding adds at lot size c (rounded fee minus exact fee)."""
    exact = C.FEE_RATE * c * p * (1 - p) * 100
    return (math.ceil(round(exact, 6)) - exact) / c


def path_features(side, cs, look_ts):
    """cs = sorted (ts, bid, ask, vol) candles of the market. Uses only candles strictly before the look."""
    prior = [(c[0], cheap_price(side, c[1], c[2])) for c in cs if c[0] < look_ts]
    prior = [(t, p) for t, p in prior if p is not None]
    ref = None
    best = None
    for t, p in prior:                                    # candle nearest to one hour before the look, within 30 to 90 minutes
        d = look_ts - t
        if 1800 <= d <= 5400 and (best is None or abs(d - 3600) < best):
            best, ref = abs(d - 3600), p
    return {"ref": ref, "pmax": max((p for _, p in prior), default=None), "first": prior[0][1] if prior else None, "n_prior": len(prior)}


def ladder_neighbours(ticker, event_markets, quotes):
    """event_markets: all tickers of the event from the census; quotes: {ticker: (mid_yes, vol)} at the look.
    Returns None if the event is not a numeric ladder of >= MIN_LADDER, else (position, n, [neighbour mids])."""
    keys = {t: strike_key(t) for t in event_markets}
    if len(event_markets) < MIN_LADDER or any(k is None for k in keys.values()) or len(set(keys.values())) != len(keys):
        return None
    order = sorted(event_markets, key=lambda t: keys[t])
    i = order.index(ticker)
    nb = [quotes[order[j]][0] for j in (i - 1, i + 1) if 0 <= j < len(order) and order[j] in quotes]
    return i, len(order), nb


# ---------------------------------------------------------------- extraction
def _src_rows(src, cdir):
    cen = {}
    for r in C._jl(cdir / "census.jsonl"):
        if r.get("markets"):
            cen.setdefault(r["ticker"], r)
    res = {}
    for x in C._jl(cdir / ("outcomes.jsonl" if src == "sweep" else "census_results.jsonl")):
        res.update(x["r"])
    meta = {}
    for s, r in cen.items():
        for m in r["markets"]:
            meta.setdefault(m[0], (s, m))
    cls = {s: C.profile_class(r) for s, r in cen.items()}
    ev_all = {}
    for t, (s, m) in meta.items():
        ev_all.setdefault(C.event_of(t), []).append(t)
    cdl = {}
    for x in C._jl(cdir / "candles.jsonl"):
        if x["t"] not in cdl and x["c"]:
            cdl[x["t"]] = x
    out, results = [], {}
    for t, x in cdl.items():
        if t not in meta:
            continue
        s, m = meta[t]
        k = cls.get(s)
        if k is None or res.get(t) not in ("yes", "no"):
            continue
        open_ts, close_ts, anc = m[1], m[2], (m[3] or m[2])
        if not open_ts or not close_ts or not anc or anc <= open_ts:
            continue
        for T in C.LOOKS[k]:
            target = anc - T * 60
            if target <= open_ts or target >= close_ts:
                continue
            q = C.decision_quote(x["c"], target, x["iv"])
            if not q:
                continue
            cs = C.cheap_side(q[1], q[2])
            if not cs:
                continue
            side, ask = cs
            quotes = {}
            for sib in ev_all.get(C.event_of(t), []):
                y = cdl.get(sib)
                if y:
                    qq = C.decision_quote(y["c"], target, y["iv"])
                    if qq and qq[1] is not None and qq[2] is not None and 0 < qq[1] < qq[2] < 1:
                        quotes[sib] = ((qq[1] + qq[2]) / 2, float(qq[3]) if len(qq) > 3 else 0.0)
            lad = ladder_neighbours(t, ev_all.get(C.event_of(t), []), quotes)
            row = base_row(src, s, cen[s].get("cat"), t, anc - open_ts, anc, target, side, ask, q, T)
            row.update(path_features(side, x["c"], target))
            row["ladder"] = None if lad is None else {"pos": lad[0], "n": lad[1], "nb": [round(v if side == "yes" else 1 - v, 4) for v in lad[2]]}
            sibs = [v[1] for k2, v in quotes.items()]
            row["sib_n"] = len(quotes)
            row["sib_vols"] = sorted(sibs)
            out.append(row)
            results[t] = res[t]
    return out, results


def base_row(src, series, cat, ticker, life_s, anchor, look_ts, side, ask, q, T):
    return {"src": src, "series": series, "cat": C.norm_cat(cat), "life": C.life_class(life_s), "bk": C.ask_bucket(ask), "ask": ask, "side": side,
            "spread_c": round((q[2] - q[1]) * 100, 4), "vol": float(q[3] if len(q) > 3 and q[3] else 0.0), "event": C.event_of(ticker), "t": anchor,
            "market": ticker, "look": f"T{T}" if isinstance(T, int) else T, "look_ts": look_ts, "open_to_look": look_ts - (anchor - life_s)}


def _newlist_rows():
    cuts = json.loads((DATA / "newlist1_cuts.json").read_text())
    c = sqlite3.connect(str(DATA / "newlist1.sqlite"))
    res = dict(c.execute("select ticker, result from res"))
    mk = {r[0]: r for r in c.execute("select ticker, series, category, open_ts, close_ts from mk")}
    cds = {}
    for t, e, b, a, v in c.execute("select ticker, end_ts, bid, ask, vol from cd order by ticker, end_ts"):
        cds.setdefault(t, []).append((e, b, a, v))
    out, results = [], {}
    for t, cs in cds.items():
        if t not in mk or res.get(t) not in ("yes", "no"):
            continue
        _, s, cat, o, cl = mk[t]
        if not o or not cl or cl >= cuts["t2"]:
            continue
        looks = {}
        for h in C.AGE_LOOK_H:
            looks[f"A{h}h"] = next((q for q in cs if o + h * 3600 <= q[0] < o + (h + 1) * 3600), None)
        late = None
        for q in cs:
            if q[0] > cl - C.LATE_LEAD_H * 3600:
                break
            late = q
        looks["late"] = late
        for tag, q in looks.items():
            if q is None:
                continue
            cside = C.cheap_side(q[1], q[2])
            if not cside:
                continue
            row = base_row("newlist1", s, cat, t, cl - o, cl, q[0], cside[0], cside[1], (q[0], q[1], q[2], q[3]), tag)
            row.update(path_features(cside[0], cs, q[0]))
            row["ladder"], row["sib_n"], row["sib_vols"] = None, 0, []           # sample is 10 markets per family: no reliable ladder
            out.append(row)
            results[t] = res[t]
    return out, results


def build():
    rows, results = [], {}
    for src in ("sweep", "us2", "us3"):
        part, r = _src_rows(src, C.SRC[src])
        print(f"  {src}: {len(part)} cheap-side rows", file=sys.stderr)
        rows += part
        results.update(r)
    part, r = _newlist_rows()
    print(f"  newlist1: {len(part)} cheap-side rows", file=sys.stderr)
    rows += part
    results.update(r)
    out, seen = [], set()
    for e in rows:
        k = (e["market"], e["look"])
        if k not in seen:
            seen.add(k)
            out.append(e)
    return out, results


# ---------------------------------------------------------------- the twelve mechanisms: pure functions of the feature row, treated arm and placebo arm
def et_parts(r):
    d = datetime.fromtimestamp(r["look_ts"], timezone.utc).astimezone(ET)
    return d.hour, d.weekday()


def m_path_fall(r):
    return (r["ref"] is not None and r["ask"] <= FALL_RATIO * r["ref"] + 1e-9 and r["ref"] - r["ask"] >= FALL_MIN - 1e-9, r["ref"] is not None and r["ask"] >= RISE_RATIO * r["ref"] - 1e-9 and r["ask"] - r["ref"] >= FALL_MIN - 1e-9)


def m_peak_collapse(r):
    if r["n_prior"] < 2 or r["pmax"] is None:
        return (False, False)
    return (r["pmax"] >= COLLAPSE_RATIO * r["ask"] - 1e-9 and r["pmax"] - r["ask"] >= COLLAPSE_MIN - 1e-9, r["pmax"] < 1.25 * r["ask"] - 1e-9)


def m_vs_open(r):
    if r["n_prior"] < 2 or r["first"] is None:
        return (False, False)
    return (r["first"] >= OPEN_RATIO * r["ask"] - 1e-9, r["ask"] >= r["first"] - 1e-9)


def m_nonround(r):
    c = round(r["ask"] * 100)
    return (c % 5 != 0, c % 5 == 0)


def m_fee_waste(r):
    w = fee_waste_c(r["ask"])
    return (w <= FEE_WASTE_LO + 1e-9, w >= FEE_WASTE_HI - 1e-9)


def m_spreadm(r):
    if r["ask"] < SPREAD_ASK_MIN - 1e-9:
        return (False, False)
    return (r["spread_c"] <= SPREAD_TIGHT + 1e-9, r["spread_c"] >= SPREAD_WIDE - 1e-9)


def m_shoulder(r):
    L = r.get("ladder")
    if not L or r["sib_n"] < MIN_SIB_QUOTES or not L["nb"]:
        return (False, False)
    return (max(L["nb"]) >= SHOULDER_HI - 1e-9, max(L["nb"]) <= TAIL_LO + 1e-9)


def m_interior(r):
    L = r.get("ladder")
    if not L:
        return (False, False)
    edge = L["pos"] in (0, L["n"] - 1)
    return (not edge, edge)


def m_volrank(r):
    v = [x for x in r.get("sib_vols", []) if x > 0]
    if len(v) < 3 or r["vol"] <= 0:
        return (False, False)
    return (r["vol"] <= min(v) + 1e-9, r["vol"] >= max(v) - 1e-9)


def m_offhours(r):
    h, wd = et_parts(r)
    return (h < 6, 12 <= h < 18 and wd < 5)


def m_weekend(r):
    h, wd = et_parts(r)
    return (wd >= 5, 1 <= wd <= 3)


def m_yday(r):
    """Needs the previous-day winner of the same series (set by prior_winner(); None when the series has no previous-day event in the cache)."""
    w = r.get("yday_key", "NA")
    if w == "NA" or w is None:
        return (False, False)
    k = strike_key(r["market"])
    if k is None:
        return (False, False)
    return (k == w, k != w)


MECH = {"PATH_FALL": m_path_fall, "PEAK_COLLAPSE": m_peak_collapse, "VS_OPEN": m_vs_open, "NONROUND": m_nonround, "FEE_WASTE": m_fee_waste,
        "SPREADM": m_spreadm, "SHOULDER": m_shoulder, "INTERIOR": m_interior, "VOLRANK": m_volrank, "OFFHOURS": m_offhours, "WEEKEND": m_weekend, "YDAY": m_yday}


def prior_winner(rows, results):
    """For each row: strike key of the single YES-settled market in the same series' previous-day event, else None ('NA' if none exists in the cache)."""
    by = {}
    for r in rows:
        by.setdefault(r["series"], {}).setdefault(datetime.fromtimestamp(r["t"], timezone.utc).date(), set()).add(r["event"])
    allmk = {}
    for t, v in results.items():
        allmk.setdefault(C.event_of(t), []).append(t)
    win = {}
    for ev, ms in allmk.items():
        ys = [m for m in ms if results[m] == "yes"]
        win[ev] = strike_key(ys[0]) if len(ys) == 1 else None
    for r in rows:
        d = datetime.fromtimestamp(r["t"], timezone.utc).date()
        prev = by.get(r["series"], {}).get(d.fromordinal(d.toordinal() - 1))
        if not prev:
            r["yday_key"] = "NA"
        else:
            ks = {win.get(e) for e in prev}
            r["yday_key"] = ks.pop() if len(ks) == 1 else "NA"
    return rows


# ---------------------------------------------------------------- sets, cap, census
def split_events(rows):
    """Events ordered by earliest close time; first two thirds = score set (A), last third = test (T). Within A, halves D1 / D2 by the same order."""
    g = C.event_groups(rows, key="ask")
    order = sorted(g, key=lambda e: (g[e][2], e))
    k = (2 * len(order)) // 3
    A, T = order[:k], order[k:]
    h = len(A) // 2
    return set(A[:h]), set(A[h:]), set(T)


def cap_per_event(rows, k=MAX_PER_EVENT):
    by = {}
    for r in rows:
        by.setdefault(r["event"], []).append(r)
    out = []
    for e, rs in by.items():
        rs = sorted(rs, key=lambda r: hashlib.md5(f"{r['market']}|{r['look']}".encode()).hexdigest())
        out += rs[:k]
    return out


def treated(rows, name, arm=0):
    f = MECH[name]
    return [r for r in rows if f(r)[arm]]


def load_rows():
    return [json.loads(x) for x in open(OUT / "rows.jsonl")]


def extract():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, results = build()
    rows = prior_winner(rows, results)
    assert all(r["ask"] <= CAP + 1e-9 for r in rows), "a favourite-side row slipped in"
    with open(OUT / "rows.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    (OUT / "res.json").write_text(json.dumps(results))
    print(f"{len(rows)} cheap rows, {len({r['event'] for r in rows})} events, {len({r['market'] for r in rows})} markets (COUNTS ONLY)")


def census():
    rows = load_rows()
    d1, d2, te = split_events(rows)
    print(f"pool {len(rows)} rows, {len({r['event'] for r in rows})} events; D1 {len(d1)} D2 {len(d2)} test {len(te)} events")
    tab = []
    for name in MECH:
        for arm, lab in ((0, "treated"), (1, "placebo")):
            t = cap_per_event(treated(rows, name, arm))
            a = [r for r in t if r["event"] in d1 | d2]
            b = [r for r in t if r["event"] in te]
            tab.append((name, lab, len(t), len(a), len({r["event"] for r in a}), len(b)))
            print(f"{name:14s} {lab:8s} capped rows {len(t):5d} | score-set {len(a):5d} ({len({r['event'] for r in a}):4d} ev; D1 {sum(1 for r in a if r['event'] in d1):4d} D2 {sum(1 for r in a if r['event'] in d2):4d}) | test {len(b):5d} | strength {STRENGTH[name]} | rank {len(a) * STRENGTH[name] if lab == 'treated' else '-'}")
    return tab


# ---------------------------------------------------------------- scoring
def attach(rows, results):
    out = []
    for r in rows:
        won = r["side"] == results[r["market"]]
        x = dict(r)
        x["won"] = 1 if won else 0
        x["net"] = C.net_per_contract(won, r["ask"])
        x["date"] = datetime.fromtimestamp(r["t"], timezone.utc).strftime("%Y-%m-%d")
        out.append(x)
    return out


def pf(rows):
    w = sum(r["net"] for r in rows if r["net"] > 0)
    l = -sum(r["net"] for r in rows if r["net"] < 0)
    return w / l if l > 0 else float("inf")


def cell(rows, rng):
    s = C.stats(rows, rng, BOOT)
    if s["n"]:
        s["pf"] = pf(rows)
    return s


def judge(name, tr, d1, d2, te, allr):
    ok_n = allr["n"] >= MIN_TRADES and min(d1["n"], d2["n"], te["n"]) >= MIN_PART
    if not ok_n:
        return "NOT_ENOUGH_DATA"
    if d1["net"] > 0 and d2["net"] > 0 and te["net"] > 0 and allr["lo"] > 0:
        return "LEAD"
    return "FALSIFIED"


def score(top, force=False):
    path = WORKERS / "MECH1S_RESULT.json"
    if path.exists() and not force:
        raise SystemExit("already run: workers/MECH1S_RESULT.json exists (run once)")
    rows = load_rows()
    results = json.loads((OUT / "res.json").read_text())
    d1, d2, te = split_events(rows)
    rng = np.random.default_rng(SEED)
    out = {}
    for name in top:
        res = {}
        for arm, lab in ((0, "treated"), (1, "placebo")):
            t = attach(cap_per_event(treated(rows, name, arm)), results)
            assert all(r["ask"] <= CAP + 1e-9 for r in t)
            parts = {"D1": [r for r in t if r["event"] in d1], "D2": [r for r in t if r["event"] in d2], "TEST": [r for r in t if r["event"] in te]}
            st = {k: cell(v, rng) for k, v in parts.items()}
            st["ALL"] = cell(t, rng)
            res[lab] = st
        tr = res["treated"]
        res["verdict"] = judge(name, tr, tr["D1"], tr["D2"], tr["TEST"], tr["ALL"])
        out[name] = res
    path.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "extract":
        extract()
    elif cmd == "census":
        census()
    elif cmd == "score":
        top = sys.argv[2:]
        score(top)
    else:
        print(__doc__)

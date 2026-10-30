"""EVT1 (workers/EVT1_REGISTRATION.md): do KXGOLD15M and KXBTC15M misprice the 15 minute windows that contain, follow or precede a
SCHEDULED public event? Research only; nothing here places an order, reads a key or decides anything live.
    python -m scalper.evt1 counts     (event and window counts per unit, no profit or loss; safe before registration)
    python -m scalper.evt1 score      (the one read of discovery and validation; refused a second time)
    python -m scalper.evt1 parity     (forward_eval against the history scorer on validation windows, survivors only)
forward_eval(window, params) is the forward-ledger evaluator (workers/candidates/README.md).
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .paths import DATA_DIR

ROOT = Path(__file__).resolve().parents[2]
CAL = ROOT / "studies" / "EVENT_CALENDAR_2026.csv"
OUT = DATA_DIR / "evt1_result.txt"
SURV = DATA_DIR / "evt1_survivors.json"
NY = ZoneInfo("America/New_York")
UTC = timezone.utc
MARKETS = {"gold": "KXGOLD15M", "btc": "KXBTC15M"}


def _ts(y, m, d):
    return int(datetime(y, m, d, tzinfo=UTC).timestamp())


DISC = (_ts(2026, 8, 6), _ts(2026, 9, 21))
VAL = (_ts(2026, 9, 21), _ts(2026, 10, 28))
RECUR_END = _ts(2027, 1, 1)
CME_HOLIDAYS = {date(2026, 9, 7), date(2026, 11, 26), date(2026, 12, 25)}   # Labor Day, Thanksgiving, Christmas

# side rules: (look_s, lo, hi, lo_exclusive, fill) ; fill "next" = the next candle's ask, "signal" = the signal candle's ask (L1 read)
SIDES = {"FAV360": (360, 0.88, 0.97, False, "next"), "CHEAP360": (360, 0.05, 0.50, False, "next"),
         "CHEAP180": (180, 0.05, 0.50, False, "next"), "FAVMID180": (180, 0.50, 0.85, True, "next")}
L1READ = (360, 0.88, 0.97, False, "signal")
POSITIONS = ("before", "contain", "after")

CSV_MAP = {"CPI": "CPI", "PPI": "PPI", "JOBS": "JOBS", "GDP": "GDP_PCE", "PCE": "GDP_PCE", "RETAIL": "RETAIL", "CLAIMS": "CLAIMS",
           "FOMC": "FOMC", "EIA_WPSR": "EIA", "TSY_BILL": "TSY_BILL", "TSY_COUPON": "TSY_COUPON",
           "MAINT_COINBASE": "MAINT", "MAINT_KRAKEN": "MAINT", "MAINT_BITSTAMP": "MAINT"}
GROUPS = {"MACRO0830": ("CPI", "PPI", "JOBS", "GDP_PCE", "RETAIL", "CLAIMS"),
          "MONTHLY0830": ("CPI", "PPI", "JOBS", "GDP_PCE", "RETAIL"),
          "TSY": ("TSY_BILL", "TSY_COUPON"),
          "SETTLE_BTC": ("CME_BTC_CLOSE", "DERIBIT", "FUNDING")}
COMMON = ["CPI", "PPI", "JOBS", "GDP_PCE", "RETAIL", "CLAIMS", "FOMC", "EIA", "TSY_BILL", "TSY_COUPON", "MACRO0830", "MONTHLY0830", "TSY"]
UNITS = {"KXGOLD15M": COMMON + ["CME_GOLD_SETTLE"],
         "KXBTC15M": COMMON + ["CME_BTC_CLOSE", "DERIBIT", "FUNDING", "MAINT", "SETTLE_BTC"]}
# control slot shifts (seconds) per base type: default same clock slot; daily recurring events use other slots of the same days
CONTROL_SHIFT = {"FUNDING": (4 * 3600,), "CME_GOLD_SETTLE": (-7200, 7200), "CME_BTC_CLOSE": (-7200, 7200)}


# ---------------------------------------------------------------- calendar

def _utc(s):
    return int(datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC).timestamp())


def _ny(d, hh, mm):
    return int(datetime(d.year, d.month, d.day, hh, mm, tzinfo=NY).timestamp())


def calendar():
    """{base type: sorted event ts}, {base type: last ts the calendar covers}."""
    ev, cover = defaultdict(set), {}
    for r in csv.DictReader(open(CAL)):
        k = CSV_MAP.get(r["event"])
        if k is None or r["status"] == "unverified":
            continue
        if k == "MAINT" and "trading or API scope" not in r["note"]:
            continue
        ev[k].add(_utc(r["release_utc"]))
    for k, v in ev.items():
        cover[k] = max(v)
    d = date(2026, 8, 1)
    while d < date(2027, 1, 1):
        if d.weekday() < 5 and d not in CME_HOLIDAYS:
            ev["CME_GOLD_SETTLE"].add(_ny(d, 13, 30))
            ev["CME_BTC_CLOSE"].add(_ny(d, 16, 0))
        if d.weekday() == 4:
            ev["DERIBIT"].add(int(datetime(d.year, d.month, d.day, 8, 0, tzinfo=UTC).timestamp()))
        for h in (0, 8, 16):
            ev["FUNDING"].add(int(datetime(d.year, d.month, d.day, h, 0, tzinfo=UTC).timestamp()))
        d += timedelta(days=1)
    for k in ("CME_GOLD_SETTLE", "CME_BTC_CLOSE", "DERIBIT", "FUNDING"):
        cover[k] = RECUR_END
    return {k: sorted(v) for k, v in ev.items()}, cover


def components(unit):
    return GROUPS.get(unit, (unit,))


def positions(unit, ev):
    """{close_ts: {position: base type}} for one unit. The containing window is the one with close - 900 <= event < close."""
    out = defaultdict(dict)
    for base in components(unit):
        for e in ev.get(base, []):
            c0 = (e // 900) * 900 + 900
            for p, c in zip(POSITIONS, (c0 - 900, c0, c0 + 900)):
                out[c].setdefault(p, base)
    return out


def unit_cover(unit, cover):
    return min(cover.get(b, 0) for b in components(unit))


# ---------------------------------------------------------------- trades

def _sq(q, yes):
    return (q[0], q[1]) if yes else (round(1 - q[1], 4), round(1 - q[0], 4))


class _NoData(Exception):
    pass


def side_trade(cs, close_ts, rule):
    """(side, fill ask, zero_volume) or None; raises _NoData when the signal candle (or the fill candle) is missing."""
    look, lo, hi, lo_x, fill_kind = rule
    t = close_ts - look
    q = cs.get(t)
    if q is None:
        raise _NoData(f"no candle at {look}s")
    for yes in (1, 0):
        bid, ask = _sq(q, yes)
        ok_lo = ask > lo + 1e-9 if lo_x else ask >= lo - 1e-9
        if not (ok_lo and ask <= hi + 1e-9):
            continue
        if fill_kind == "signal":
            return ("yes" if yes else "no"), float(ask), (q[2] or 0) <= 0
        nq = cs.get(t + 60)
        if nq is None:
            raise _NoData(f"no fill candle at {look - 60}s")
        fill = _sq(nq, yes)[1]
        if not (0 < fill < 1):
            return None
        return ("yes" if yes else "no"), float(fill), (q[2] or 0) <= 0 or (nq[2] or 0) <= 0
    return None


def fee(p, c, m=1.0):
    return math.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def net(side, fill, result, c=10, m=1.0):
    return (1.0 if side == result else 0.0) - fill - fee(fill, c, m)


def forward_eval(window, params):
    """params: {"unit", "position", "side_rule", "series"}. Trades the side rule only in windows in that position of that unit."""
    from .fwdeval import NoData
    if window["series"] != params["series"]:
        return None
    ev, cover = calendar()
    unit = params["unit"]
    ct = window["close_ts"]
    if ct > unit_cover(unit, cover) + 1800:
        raise NoData("event calendar does not cover this window")
    if params["position"] not in positions(unit, ev).get(ct, {}):
        return None
    try:
        tr = side_trade(window["candles"], ct, SIDES[params["side_rule"]])
    except _NoData as e:
        raise NoData(str(e))
    if tr is None:
        return None
    side, fill, zv = tr
    return {"side": side, "entry": fill, "exit": None, "t": ct - SIDES[params["side_rule"]][0] + 60, "zero_volume": zv,
            "note": f"EVT1 {unit} {params['position']} {params['side_rule']}"}


# ---------------------------------------------------------------- history

def load(series):
    from .gen7 import load_windows
    return [(tk, ct, res, cs) for tk, ct, res, cs, _ in load_windows(series, DISC[0], VAL[1])]


def split_of(ct):
    return "D" if DISC[0] <= ct < DISC[1] else ("V" if VAL[0] <= ct < VAL[1] else None)


def _slot(ct):
    d = datetime.fromtimestamp(ct, UTC)
    return d.hour * 60 + d.minute


def _wk(ct):
    return int(datetime.fromtimestamp(ct, UTC).weekday() >= 5)


def _day(ct):
    return datetime.fromtimestamp(ct, UTC).strftime("%Y-%m-%d")


def pf(v):
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return w / l if l > 0 else (99.0 if w > 0 else 0.0)


def trades_by_rule(W, rule):
    """{close_ts: (side, fill, zv, result)} for windows where the rule trades; plus the set of windows with missing data."""
    T, nod = {}, set()
    for tk, ct, res, cs in W:
        try:
            tr = side_trade(cs, ct, rule)
        except _NoData:
            nod.add(ct); continue
        if tr is not None:
            T[ct] = (*tr, res)
    return T, nod


def compare(T, ev_cts, base_of, excl, split, value):
    """Event trades in ev_cts against the matched control. value(tr) -> per-trade number.
    Returns dict with the event list, residual diff and its z (day-clustered event part plus control sampling part)."""
    from .calibration import cluster_mean_z
    ctrl = defaultdict(list)
    for ct, tr in T.items():
        if split_of(ct) == split and ct not in excl:
            ctrl[(_slot(ct), _wk(ct))].append(value(tr))
    ev, res_obs, keys = [], [], defaultdict(int)
    for ct in sorted(ev_cts):
        if split_of(ct) != split or ct not in T:
            continue
        base = base_of[ct]
        shifts = CONTROL_SHIFT.get(base, (0,))
        ks = [(((_slot(ct) * 60 + s) // 60) % 1440, _wk(ct)) for s in shifts]
        pool = [x for k in ks for x in ctrl.get(k, [])]
        v = value(T[ct])
        ev.append((ct, v))
        if not pool:
            continue
        m = sum(pool) / len(pool)
        res_obs.append((_day(ct), v - m))
        keys[tuple(ks)] += 1
    if len(res_obs) < 2:
        return {"ev": ev, "d": 0.0, "z": 0.0, "nres": len(res_obs)}
    d, se_e, _ = cluster_mean_z(res_obs)
    n = len(res_obs); var_c = 0.0
    for ks, cnt in keys.items():
        pool = [x for k in ks for x in ctrl.get(k, [])]
        if len(pool) > 1:
            mu = sum(pool) / len(pool)
            var_c += (cnt / n) ** 2 * (sum((x - mu) ** 2 for x in pool) / (len(pool) - 1)) / len(pool)
    se = math.sqrt(se_e ** 2 + var_c)
    return {"ev": ev, "d": d, "z": d / se if se > 0 else 0.0, "nres": n}


def counts():
    ev, cover = calendar()
    for key, series in MARKETS.items():
        W = load(series)
        cts = {ct for _, ct, _, _ in W}
        print(f"{series}: {len(W)} settled windows in {DISC[0]}..{VAL[1]}")
        for unit in UNITS[series]:
            P = positions(unit, ev)
            row = []
            for sp in ("D", "V"):
                for p in POSITIONS:
                    w = [c for c, ps in P.items() if p in ps and c in cts and split_of(c) == sp]
                    row.append(f"{sp}-{p} {len(w)} win/{len({_day(c) for c in w})} d")
            print(f"  {unit:16s} " + " | ".join(row))


def score():
    if OUT.exists():
        print("Refusing to run again"); return
    ev, cover = calendar()
    lines, surv, l1lines = [], [], []
    ncell = 0
    for key, series in MARKETS.items():
        W = load(series)
        res_of = {ct: res for _, ct, res, _ in W}
        TR = {name: trades_by_rule(W, rule) for name, rule in SIDES.items()}
        TL1, _ = trades_by_rule(W, L1READ)
        for unit in UNITS[series]:
            P = positions(unit, ev)
            excl = set(P)
            for p in POSITIONS:
                cts = {c for c, ps in P.items() if p in ps}
                base_of = {c: P[c][p] for c in cts}
                for name in SIDES:
                    ncell += 1
                    T, nod = TR[name]
                    r = {}
                    for sp in ("D", "V"):
                        c10 = compare(T, cts, base_of, excl, sp, lambda tr: net(tr[0], tr[1], tr[3], 10))
                        vals = [v for _, v in c10["ev"]]
                        evc = [c for c, _ in c10["ev"]]
                        v1 = [net(T[c][0], T[c][1], T[c][3], 1) for c in evc]
                        vs = [net(T[c][0], T[c][1], T[c][3], 10, 1.2) for c in evc]
                        vnz = [net(T[c][0], T[c][1], T[c][3], 10) for c in evc if not T[c][2]]
                        ctrl = [net(*T[c][:2], T[c][3], 10) for c in T if split_of(c) == sp and c not in excl]
                        r[sp] = dict(n=len(vals), days=len({_day(c) for c in evc}), pf=pf(vals), pf1=pf(v1), pfs=pf(vs), sums=sum(vs),
                                     pfnz=pf(vnz), zv=len(vals) - len(vnz), mean=(sum(vals) / len(vals) if vals else 0.0), d=c10["d"],
                                     z=c10["z"], cpf=pf(ctrl), cn=len(ctrl),
                                     nod=len([c for c in cts if c in nod and split_of(c) == sp]))
                    D, V = r["D"], r["V"]
                    ok = (D["n"] >= 30 and D["pf"] >= 1.5 and D["z"] >= 2 and D["sums"] > 0 and
                          V["n"] >= 20 and V["pf"] >= 1.3 and V["z"] >= 2 and V["sums"] > 0)
                    if ok:
                        surv.append({"series": series, "unit": unit, "position": p, "side_rule": name, "disc": D, "valid": V})
                    lines.append(f"{'PASS' if ok else '    '} {series} {unit:15s} {p:7s} {name:9s} | " +
                                 " | ".join(f"{sp}: n {x['n']:3d} ({x['days']:2d} d) PF {x['pf']:5.2f} [C1 {x['pf1']:5.2f}, x1.2 {x['pfs']:5.2f}, "
                                            f"no-zv {x['pfnz']:5.2f}, zv {x['zv']}] mean {100 * x['mean']:+6.2f}c ctrl PF {x['cpf']:5.2f} (n {x['cn']}) "
                                            f"diff {100 * x['d']:+6.2f}c z {x['z']:+5.2f} nodata {x['nod']}" for sp, x in r.items()))
                # L1 read: does L1's own rule lose more often here? loss indicator, matched control, signal-ask fill
                lr = {}
                for sp in ("D", "V"):
                    c = compare(TL1, cts, base_of, excl, sp, lambda tr: 0.0 if tr[0] == tr[3] else 1.0)
                    ls = [v for _, v in c["ev"]]
                    ctrl = [0.0 if TL1[x][0] == TL1[x][3] else 1.0 for x in TL1 if split_of(x) == sp and x not in excl]
                    nets_ = [net(TL1[x][0], TL1[x][1], TL1[x][3], 10) for x, _ in c["ev"]]
                    lr[sp] = (len(ls), sum(ls), (sum(ls) / len(ls) if ls else 0.0), (sum(ctrl) / len(ctrl) if ctrl else 0.0), c["d"], c["z"], pf(nets_))
                flag = all(lr[sp][5] >= 2 for sp in lr)
                l1lines.append(f"{'BOTH z>=2' if flag else '         '} {series} {unit:15s} {p:7s} | " + " | ".join(
                    f"{sp}: n {a:3d} losses {int(b):2d} rate {100 * cc:5.1f}% ctrl {100 * dd:5.1f}% diff {100 * e:+5.1f}pt z {f:+5.2f} PF {g:5.2f}"
                    for sp, (a, b, cc, dd, e, f, g) in lr.items()))
    SURV.write_text(json.dumps(surv, indent=1))
    head = [f"EVT1 score: {ncell} side cells (+{len(l1lines)} L1 read cells); screen passes: {len(surv)}" +
            (": " + ", ".join(f"{s['series']} {s['unit']} {s['position']} {s['side_rule']}" for s in surv) if surv else " (none)"),
            "Screen: D n>=30 PF>=1.5 z>=2 and x1.2 net>0; V n>=20 PF>=1.3 z>=2 and x1.2 net>0. PF at C=10, fill at next candle's ask, held.", ""]
    txt = "\n".join(head + lines + ["", "L1 read (L1's rule, signal-ask fill, loss rate against the matched control):"] + l1lines) + "\n"
    OUT.write_text(txt); print(txt)


def parity():
    from .fwdeval import NoData
    from .fwdledger import net_per_contract
    surv = json.loads(SURV.read_text())
    ev, _ = calendar()
    bad = checked = 0
    for s in surv:
        W = load(s["series"])
        T, _ = trades_by_rule(W, SIDES[s["side_rule"]])
        P = positions(s["unit"], ev)
        hist = {c: net(T[c][0], T[c][1], T[c][3], 10) for c in T if s["position"] in P.get(c, {}) and split_of(c) == "V"}
        for tk, ct, res, cs in W:
            if split_of(ct) != "V":
                continue
            try:
                tr = forward_eval({"series": s["series"], "close_ts": ct, "candles": cs}, s)
            except NoData:
                tr = None
            checked += 1
            if tr is None:
                bad += ct in hist; continue
            if ct not in hist or abs(net_per_contract(tr, res, 10) - hist[ct]) > 1e-6:
                bad += 1
    print("parity windows checked", checked, "mismatches", bad)


if __name__ == "__main__":
    {"counts": counts, "score": score, "parity": parity}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()

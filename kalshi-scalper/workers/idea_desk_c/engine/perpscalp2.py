#!/usr/bin/env python3
"""PERPSCALP2 plugin (Idea Desk C, Nov 16, 2026), build 1. Card: ../allkalshi/perpscalp2/PERPSCALP2_CARD.md (with amendment 1).
Perps scalping, the liquid subset: 14 names, 7 follow entry rules (vol expansion r 2 and 3, opening-range breakout N 5, 15, 30, volume spike q 5 and 10) x 4 window filters
x 6 exits (target and stop in units of U = sigma1 x sqrt(10), time stops 10 and 30 minutes) = 168 cells, each read in three columns (taker/taker, maker entry with taker
exit, maker entry with maker target). Reads the perp-data layout only: <root>/kalshi1m/<date>[.only].csv.gz and <root>/funding/<date>[.only].csv.gz. No network, no result file."""
import calendar, csv, glob, gzip, hashlib, math, os, re, sys
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
NAMES = ("KXNVDAPERP", "KXMUPERP", "KXSPCXPERP", "KXCOSTPERP", "KXTSLAPERP", "KXPLTRPERP", "KXMETAPERP", "KXAAPLPERP", "KXGOOGLPERP",
         "KXUSTECH100PERP", "KXUS500PERP", "KXGOLDPERP", "KXBTCPERP", "KXETHPERP")
LMAX = {"KXNVDAPERP": 4.5, "KXMUPERP": 3.3, "KXSPCXPERP": 3.5, "KXCOSTPERP": 4.9, "KXTSLAPERP": 4.2, "KXPLTRPERP": 3.8, "KXMETAPERP": 4.5, "KXAAPLPERP": 4.9,
        "KXGOOGLPERP": 4.9, "KXUSTECH100PERP": 28.9, "KXUS500PERP": 36.1, "KXGOLDPERP": 40.0, "KXBTCPERP": 15.4, "KXETHPERP": 10.5}
MAINT = 0.045
ENTRIES = (("E1", "vol", 2), ("E2", "vol", 3), ("E3", "orb", 5), ("E4", "orb", 15), ("E5", "orb", 30), ("E6", "spike", 5), ("E7", "spike", 10))
WINDOWS = {"W0": (9 * 60 + 35, 15 * 60 + 35), "W1": (9 * 60 + 35, 10 * 60), "W2": (10 * 60, 11 * 60), "W3": (15 * 60, 15 * 60 + 35)}   # entry candle end, minutes after midnight ET
WIN_OPEN = {"W0": True, "W1": True, "W2": False, "W3": False}                    # whether the lower bound is inclusive
EXITS = tuple((tk, 1.0, T) for tk in (1.0, 1.5, 2.0) for T in (600, 1800))        # (target in U, stop in U, time stop seconds)
HAIRCUTS = (0.0002, 0.0005)                                                         # gate, stress
FEE_T, FEE_M = 0.0012, 0.0005
SPREAD_MAX, COOLDOWN, END_REG = 0.003, 900, 15 * 60 + 45
N_CELLS = len(ENTRIES) * len(WINDOWS) * len(EXITS)                                  # 7 x 4 x 6 = 168
MIN_N, MIN_DAYS, MIN_SIGNALS, ALPHA = 100, 10, 48, 0.05
END_EPOCH = 1794787199                                                              # development: candles ending through 2026-11-15 23:59:59Z
H16_START = 1797897600                                                              # H16 (NVDA, AAPL, US 500, US Tech 100, SPY, QQQ) opens 2026-12-22: rows at or after it are dropped and counted
HOLIDAYS = ("2026-11-26", "2026-12-25")                                             # no session
EARLY = ("2026-11-27", "2026-12-24")                                                # early close: regular hours end 12:45 ET
BIG = 1e9


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sess_end(d):
    """regular hours end (minutes after midnight ET) for the ET date d, or None on a holiday"""
    s = d.isoformat()
    return None if s in HOLIDAYS else (12 * 60 + 45 if s in EARLY else END_REG)


ISO_RE = re.compile(r"^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(\.\d+)?Z$")
FILE_RE = re.compile(r"^\d{4}-\d\d-\d\d(\.only)?\.csv\.gz$")
CANDLE_COLS = ("ticker", "end_period_ts", "bid_close", "ask_close", "volume")
FUND_COLS = ("ticker", "funding_time", "funding_rate")


def iso(s):
    """'2026-11-13T21:00:00Z' or with fractional seconds ('...:00.000Z') -> integer epoch (the fraction is floored); anything else raises"""
    m = ISO_RE.match(s)
    if not m:
        raise ValueError("unparsable funding_time %r" % s)
    return calendar.timegm(tuple(int(x) for x in m.groups()[:6]))


def _files(root, sub, stats):
    out = []
    for f in sorted(glob.glob(os.path.join(root, sub, "*.csv.gz"))):
        if FILE_RE.match(os.path.basename(f)):
            out.append(f)
        else:
            stats["files_skipped"] = stats.get("files_skipped", 0) + 1            # for example funding/all-history.csv.gz
    return out


def _reader(f, cols, stats, key):
    fh = gzip.open(f, "rt", newline="")
    rd = csv.DictReader(fh)
    hdr = tuple(rd.fieldnames or ())
    stats.setdefault("headers_seen", set()).add((key, hdr))
    missing = [c for c in cols if c not in hdr]
    if missing:
        raise ValueError("%s lacks columns %s" % (f, missing))
    return fh, rd


def load(root, end_epoch=END_EPOCH, manifest=None, stats=None):
    """-> ({name: {end_ts: (bid, ask, volume)}}, {name: sorted [(time, rate)]}). Unusable candles (a missing bid or ask, crossed) are dropped; a gap is never bridged.
    Files: only <date>[.only].csv.gz under kalshi1m and funding, in sorted path order; a key (name, time) seen twice keeps the FIRST file's row; duplicates are counted."""
    st = stats if stats is not None else {}
    c = {n: {} for n in NAMES}
    fu = {n: {} for n in NAMES}
    end_epoch = min(end_epoch, H16_START - 1)
    for f in _files(root, "kalshi1m", st):
        if manifest is not None:
            manifest.append((os.path.relpath(f, root), _sha(f)))
        fh, rd = _reader(f, CANDLE_COLS, st, "kalshi1m")
        with fh:
            for r in rd:
                n = r["ticker"]
                if n not in c:
                    continue
                try:
                    ts, b, a, v = int(r["end_period_ts"]), float(r["bid_close"]), float(r["ask_close"]), float(r["volume"] or 0)
                except ValueError:
                    st["candle_rows_unparsable"] = st.get("candle_rows_unparsable", 0) + 1
                    continue
                if ts % 60 != 0:
                    raise ValueError("candle end %d is off the 60 s grid" % ts)
                if ts >= H16_START:
                    st["h16_rows"] = st.get("h16_rows", 0) + 1
                    continue
                if ts > end_epoch or not (0 < b <= a < BIG):
                    continue
                if ts in c[n]:
                    k = "candle_duplicate_differs" if c[n][ts] != (b, a, v) else "candle_duplicate_first_kept"
                    st[k] = st.get(k, 0) + 1
                    continue
                c[n][ts] = (b, a, v)
    for f in _files(root, "funding", st):
        if manifest is not None:
            manifest.append((os.path.relpath(f, root), _sha(f)))
        fh, rd = _reader(f, FUND_COLS, st, "funding")
        with fh:
            for r in rd:
                n = r["ticker"]
                if n not in fu:
                    continue
                t, rate = iso(r["funding_time"]), float(r["funding_rate"])
                st.setdefault("funding_rows", {})[n] = st.get("funding_rows", {}).get(n, 0) + 1
                if t in fu[n]:
                    k = "print_duplicate_differs" if fu[n][t] != rate else "print_duplicate_first_kept"
                    st[k] = st.get(k, 0) + 1
                    continue
                fu[n][t] = rate
    return c, {n: sorted(v.items()) for n, v in fu.items()}


def mid(q):
    return (q[0] + q[1]) / 2


def et_min(ts):
    d = datetime.fromtimestamp(ts, ET)
    return d.weekday(), d.hour * 60 + d.minute, d.date()


def std(xs):
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def rets(c, lo, hi):
    """1 minute log returns of mid between candles exactly 60 s apart, both ending in (lo, hi]"""
    out = []
    for t in range(lo + 60, hi + 1, 60):
        if t in c and (t - 60) in c:
            out.append(math.log(mid(c[t]) / mid(c[t - 60])))
    return out


def sigma1(c, t):
    r = rets(c, t - 300 - 3600, t - 300)
    return std(r) if len(r) >= 40 else None


def signal_times(c, ent, day_cache):
    """-> list of (signal candle end ts, side +1 / -1) for one name and one entry rule, chronological. Regular hours only (the window filter comes later)."""
    kind, par = ent[1], ent[2]
    out = []
    if kind == "orb":
        days = {}
        for t in sorted(c):
            wd, m, d = et_min(t)
            end = sess_end(d)
            if wd < 5 and end is not None and 9 * 60 + 31 <= m <= end:
                days.setdefault(d, []).append((t, m))
        for d, L in days.items():
            rng = [t for t, m in L if m <= 9 * 60 + 30 + par]
            if len(rng) < par:
                continue                                             # an incomplete range: no signal that day (counted by the caller)
            ms = [mid(c[t]) for t in rng]
            hi, lo = max(ms), min(ms)
            for t, m in L:
                if m > 9 * 60 + 30 + par and m <= sess_end(d):
                    x = mid(c[t])
                    if x > hi or x < lo:
                        if (c[t][1] - c[t][0]) / x <= SPREAD_MAX:                   # the common spread filter; a skipped first breakout is not replaced
                            out.append((t, 1 if x > hi else -1))
                        break
        return sorted(out)
    for t in sorted(c):
        wd, m, d = et_min(t)
        end = sess_end(d)
        if wd >= 5 or end is None or not (9 * 60 + 35 <= m <= end):
            continue
        if (c[t][1] - c[t][0]) / mid(c[t]) > SPREAD_MAX:
            continue
        if kind == "vol":
            s1 = sigma1(c, t)
            r15 = rets(c, t - 900, t)
            if s1 is None or s1 == 0 or len(r15) < 10 or (t - 900) not in c:
                continue
            sd = std(r15)
            if sd is None or sd / s1 < par:
                continue
            mv = math.log(mid(c[t]) / mid(c[t - 900]))
        else:
            prev = [c[x][2] for x in range(t - 3600, t, 60) if x in c and c[x][2] > 0]
            if len(prev) < 20 or (t - 60) not in c or c[t][2] < par * (sum(prev) / len(prev)):
                continue
            mv = math.log(mid(c[t]) / mid(c[t - 60]))
        if mv != 0:
            out.append((t, 1 if mv > 0 else -1))
    return out


def tick_of(c):
    vals = sorted({v for q in c.values() for v in (q[0], q[1])})
    d = [b - a for a, b in zip(vals, vals[1:]) if b - a > 1e-12]
    return min(d) if d else 0.0


def funding_of(fu, side, e, x):
    """funding paid (negative) or received for a hold: a print counts iff entry end < print < exit end; positive rate: longs pay shorts"""
    f = sum(r for t, r in fu if e < t < x)
    return -side * f, any(e < t < x for t, r in fu)


STATS = {}


def build_trade(c, fu, tick, t, side, U, ref, k_t, k_s, T, col, N, h):
    """One trade for a signal at candle t. col 'TT' taker/taker, 'MT' maker entry taker exit, 'MM' maker entry and maker target. -> dict or None (not filled / no exit)."""
    q = c[t]
    if col == "TT":
        e = t + 60
        if e not in c:
            return None
        qe = c[e]
        en = qe[1] * (1 + h) if side > 0 else qe[0] * (1 - h)
        fee_in = FEE_T
    else:
        lim = q[0] if side > 0 else q[1]
        f = None
        for k in range(1, N + 1):
            x = t + 60 * k
            if x in c and ((side > 0 and c[x][1] <= lim - tick + 1e-9) or (side < 0 and c[x][0] >= lim + tick - 1e-9)):
                f = x
                break
        if f is None:
            return None
        e, en, fee_in = f, lim, FEE_M
    tgt = ref * (1 + side * k_t * U)
    stp = ref * (1 - side * k_s * U)
    wd, m, d = et_min(e)
    last = min(e + T, e + (sess_end(d) - m) * 60)
    ex, tx = None, None
    fee_out = FEE_T
    for x in range(e + 60, last + 1, 60):
        if x not in c:
            continue
        b, a = c[x][0], c[x][1]
        if side > 0:
            if col == "MM" and b >= tgt + tick - 1e-9:
                ex, fee_out, tx = tgt, FEE_M, x; break
            if b <= stp:
                ex, tx = b * (1 - h), x; break
            if col != "MM" and b >= tgt:
                ex, tx = b * (1 - h), x; break
        else:
            if col == "MM" and a <= tgt - tick + 1e-9:
                ex, fee_out, tx = tgt, FEE_M, x; break
            if a >= stp:
                ex, tx = a * (1 + h), x; break
            if col != "MM" and a <= tgt:
                ex, tx = a * (1 + h), x; break
    if ex is None:
        # time exit: only on a candle ending within 2 minutes of the planned exit; otherwise the trade is dropped (a gap is never bridged)
        tx = next((x for x in (last, last - 60, last - 120) if x > e and x in c), None)
        if tx is None:
            STATS["no_exit_candle"] = STATS.get("no_exit_candle", 0) + 1
            return None
        ex = c[tx][0] * (1 - h) if side > 0 else c[tx][1] * (1 + h)
        fee_out = FEE_T
    gross = (ex - en) / en if side > 0 else (en - ex) / en                # the card's formula: short = (entry - exit) / entry
    fund, crossed = funding_of(fu, side, e, tx)
    return {"e": e, "x": tx, "side": side, "net": gross - fee_in - fee_out + fund, "gross": gross, "crossed": crossed,
            "stop_dist": k_s * U, "day": datetime.fromtimestamp(e, ET).date().isoformat()}


def pf(xs):
    w = sum(x for x in xs if x > 1e-15)
    l = -sum(x for x in xs if x < -1e-15)
    return None if not xs else (float("inf") if l == 0 and w > 0 else (w / l if l else None))


def day_z(trs):
    by = {}
    for t in trs:
        by[t["day"]] = by.get(t["day"], 0.0) + t["net"]
    v = list(by.values())
    if len(v) < 2:
        return None
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    return None if sd == 0 else m / (sd / math.sqrt(len(v)))


def metrics(trs):
    trs = sorted(trs, key=lambda t: (t["e"], t["side"]))
    n = len(trs)
    h = n // 2
    xs = [t["net"] for t in trs]
    return {"n": n, "days": len({t["day"] for t in trs}), "pf": pf(xs), "h1": pf(xs[:h]), "h2": pf(xs[h:]), "z": day_z(trs),
            "mean_bps": 1e4 * sum(xs) / n if n else None, "spanning_funding": sum(1 for t in trs if t["crossed"])}


def p_one_sided(z):
    return None if z is None else 0.5 * math.erfc(z / math.sqrt(2))


def passes(g, s):
    z = lambda v: 0.0 if v is None else v
    return g["n"] >= MIN_N and g["days"] >= MIN_DAYS and z(g["pf"]) >= 1.3 and z(g["h1"]) >= 1.0 and z(g["h2"]) >= 1.0 and z(s["pf"]) >= 1.0


def margin_row(trs_by_name):
    """percent of margin and liquidation flag at 10%, 25%, 50% of each name's page max: trs_by_name {name: [trade]}"""
    out = {}
    for x in (0.10, 0.25, 0.50):
        tot, n, flagged = 0.0, 0, 0
        for nm, L in trs_by_name.items():
            lev = x * LMAX[nm]
            for t in L:
                tot += t["net"] * lev; n += 1
                if lev > 0 and t["stop_dist"] >= 1 / lev - MAINT:
                    flagged += 1
        out["%d%%" % round(x * 100)] = {"mean_pct_of_margin": None if n == 0 else 100 * tot / n, "stop_beyond_liquidation": flagged}
    return out


def run(root, m_carried=6290660, N_fill=(2, 5)):
    STATS.clear()
    manifest, st = [], {}
    c, fu = load(root, END_EPOCH, manifest, st)
    counts = {"names_loaded": sum(1 for n in NAMES if c[n]), "dropped_short_history": [], "valid_regular_candles": {}, "files_read": len(manifest),
              "manifest_sha256": hashlib.sha256(repr(sorted(manifest)).encode()).hexdigest()}
    use = []
    for n in NAMES:
        reg = sum(1 for t in c[n] if et_min(t)[0] < 5 and sess_end(et_min(t)[2]) is not None and 9 * 60 + 35 <= et_min(t)[1] <= sess_end(et_min(t)[2]))
        counts["valid_regular_candles"][n] = reg
        if reg < 600:
            counts["dropped_short_history"].append(n)
        else:
            use.append(n)
    ticks = {n: tick_of(c[n]) for n in use}
    sig = {(n, e[0]): signal_times(c[n], e, None) for n in use for e in ENTRIES}
    s1c = {}
    sigma = lambda n, t: s1c.setdefault((n, t), sigma1(c[n], t))
    COLS = ("TT", "MT2", "MT5", "MM2", "MM5")
    cells = []
    for ent in ENTRIES:
        for w, (lo, hi) in WINDOWS.items():
            for (k_t, k_s, T) in EXITS:
                res = {"TT": [], "TS": [], "MT2": [], "MT5": [], "MM2": [], "MM5": []}
                filled_taker, unfilled_taker = {2: [], 5: []}, {2: [], 5: []}
                for n in use:
                    cc = c[n]
                    busy = {k: 0 for k in COLS}
                    last_e = {k: -10 ** 12 for k in COLS}
                    for (t, side) in sig[(n, ent[0])]:
                        e = t + 60
                        wd, m, d = et_min(e)
                        end_d = sess_end(d)
                        if end_d is None:
                            continue
                        hi_d = min(hi, end_d - 10)                              # no entry in the last 10 minutes of the session
                        if not ((lo <= m <= hi_d) if WIN_OPEN[w] else (lo < m <= hi_d)):
                            continue
                        s1 = sigma(n, t)
                        if s1 is None or s1 == 0:
                            continue
                        U = s1 * math.sqrt(10)
                        ref = mid(cc[t])
                        # the hypothetical taker trade of this signal (adverse-selection comparison; ignores the position rule)
                        hyp = build_trade(cc, fu[n], ticks[n], t, side, U, ref, k_t, k_s, T, "TT", 0, HAIRCUTS[0])
                        if hyp is None:
                            continue
                        if e >= busy["TT"] and e - last_e["TT"] >= COOLDOWN:
                            hyp["name"] = n
                            trs = build_trade(cc, fu[n], ticks[n], t, side, U, ref, k_t, k_s, T, "TT", 0, HAIRCUTS[1])
                            if trs is not None:
                                trs["name"] = n
                                res["TT"].append(hyp); res["TS"].append(trs)
                                busy["TT"], last_e["TT"] = hyp["x"], e
                        for N in N_fill:
                            filled = False
                            for col in ("MT", "MM"):
                                key = "%s%d" % (col, N)
                                tr = build_trade(cc, fu[n], ticks[n], t, side, U, ref, k_t, k_s, T, col, N, HAIRCUTS[0])
                                if tr is None:
                                    continue
                                if col == "MT":
                                    filled = True                                               # the limit filled (adverse selection compares filled with unfilled signals)
                                if tr["e"] >= busy[key] and tr["e"] - last_e[key] >= COOLDOWN:       # one position per name in each column
                                    tr["name"] = n
                                    res[key].append(tr)
                                    busy[key], last_e[key] = tr["x"], tr["e"]
                            (filled_taker if filled else unfilled_taker)[N].append(hyp["net"])
                g, s = metrics(res["TT"]), metrics(res["TS"])
                by = {}
                for t in res["TT"]:
                    by.setdefault(t["name"], []).append(t)
                row = {"cell": (ent[0], w, k_t, T), "TT": g, "TS": s, "pass": passes(g, s), "margin": margin_row(by),
                       "maker": {k: metrics(res[k]) for k in ("MT2", "MT5", "MM2", "MM5")},
                       "adverse": {N: {"filled_n": len(filled_taker[N]), "filled_mean_bps": 1e4 * sum(filled_taker[N]) / len(filled_taker[N]) if filled_taker[N] else None,
                                       "unfilled_n": len(unfilled_taker[N]), "unfilled_mean_bps": 1e4 * sum(unfilled_taker[N]) / len(unfilled_taker[N]) if unfilled_taker[N] else None} for N in N_fill}}
                row["maker_only"] = (not row["pass"]) and any(passes(row["maker"][k], s) for k in row["maker"])
                cells.append(row)
    live = [(p_one_sided(r["TT"]["z"]), i) for i, r in enumerate(cells) if r["TT"]["n"] >= MIN_SIGNALS and r["TT"]["z"] is not None]
    live.sort()
    mt = N_CELLS + m_carried
    kk = 0
    for rank, (p, i) in enumerate(live, 1):
        if p <= ALPHA * rank / mt:
            kk = rank
    surv = {i for _, i in live[:kk]}
    for i, r in enumerate(cells):
        r["bh_survivor"] = i in surv
    counts["ticks"] = ticks
    counts["load"] = {k: (sorted(v) if isinstance(v, set) else v) for k, v in st.items()}
    counts["no_exit_candle"] = STATS.get("no_exit_candle", 0)
    counts["h16_rows_dropped"] = st.get("h16_rows", 0)
    return {"label": "candle replay, upper bound, not fill-checked; exit checks on bid and ask closes miss intra-minute touches (a lower bound on target and stop hits); "
                     "DEVELOPMENT through 2026-11-15, the same days as PERPSCALP1, PERPSLANE4 and POOL1; day z is a normal approximation on a few days; first week, one regime",
            "m_carried": m_carried, "m_new": N_CELLS, "m_total": mt, "counts": counts, "cells": cells, "bh_survivors": len(surv),
            "passes": [r["cell"] for r in cells if r["pass"] and r["bh_survivor"]], "maker_only_flags": [r["cell"] for r in cells if r["maker_only"]]}

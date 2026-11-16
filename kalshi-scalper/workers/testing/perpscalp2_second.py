#!/usr/bin/env python3
"""PERPSCALP2 scalping family, BUILD 2 (Testing Desk, Nov 16, 2026), written blind from Desk C's card (b2d1ce49..., commit f3ab35f82) and their answers P1 to P16 (PERPSCALP2_SECOND_HAND_CASE.md and addendum 1). Pure functions.
data[name] = {end_ts: (bid_close, ask_close, volume)}; funding[name] = {ts: rate}."""
import math
import engine1_perps_second as p
import lane4_plugin as L4

MIN = 60
_SIG = {}
_SG = {}
TAKER, MAKER = 0.0012, 0.0005
HG, HS = 0.0002, 0.0005
SPREAD_MAX = 0.003
ENTRIES = (("E1", "vol", 2), ("E2", "vol", 3), ("E3", "orb", 5), ("E4", "orb", 15), ("E5", "orb", 30), ("E6", "spike", 5), ("E7", "spike", 10))
WINDOWS = ("W0", "W1", "W2", "W3")
EXITS = tuple((kt, T) for kt in (1, 1.5, 2) for T in (600, 1800))
N_CELLS = len(ENTRIES) * len(WINDOWS) * len(EXITS)
assert N_CELLS == 168
LMAX = {"KXNVDAPERP": 4.5, "KXMUPERP": 3.3, "KXSPCXPERP": 3.5, "KXCOSTPERP": 4.9, "KXTSLAPERP": 4.2, "KXPLTRPERP": 3.8, "KXMETAPERP": 4.5, "KXAAPLPERP": 4.9, "KXGOOGLPERP": 4.9, "KXUSTECH100PERP": 28.9, "KXUS500PERP": 36.1, "KXGOLDPERP": 40.0, "KXBTCPERP": 15.4, "KXETHPERP": 10.5}
COLUMNS = ("TT", "TS", "MT2", "MT5", "MM2", "MM5")


def usable(c): return c is not None and c[0] is not None and c[1] is not None and 0 < c[0] < c[1]
def mid(c): return (c[0] + c[1]) / 2
def day_of(t): return p.et_local_day(t)
def session_end(L): return L4.et_end(L, 12, 45) if L in L4.EARLY else L4.et_end(L, 15, 45)
def is_regular(t):
    L = day_of(t); return L4.is_session(L) and L4.et_end(L, 9, 35) <= t <= session_end(L)
def sample_std(v):
    k = len(v)
    if k < 2: return None
    m = sum(v) / k; return math.sqrt(sum((x - m) ** 2 for x in v) / (k - 1))


def returns(s, ends):
    out = []
    for t in ends:
        a, b = s.get(t), s.get(t - MIN)
        if usable(a) and usable(b): out.append(math.log(mid(a) / mid(b)))
    return out


def sigma1(s, t):
    k = (id(s), t)
    if k not in _SG: _SG[k] = _sigma1(s, t)
    return _SG[k]


def _sigma1(s, t):
    r = returns(s, range(t - 64 * MIN, t - 5 * MIN + 1, MIN))
    return sample_std(r) if len(r) >= 40 else None


def spread_ok(c): return (c[1] - c[0]) / mid(c) <= SPREAD_MAX


def tick_of(s):
    v = sorted(set(x for c in s.values() if usable(c) for x in (c[0], c[1])))
    d = [b - a for a, b in zip(v, v[1:]) if b - a > 1e-12]
    return min(d) if d else None


def signals(s, kind, par):
    """-> [(t, dir)] signal candles in order (all conditions on the signal candle: regular hours, usable, spread, sigma1)"""
    ts = sorted(t for t, c in s.items() if usable(c) and is_regular(t)); out = []
    if kind == "vol":
        for t in ts:
            if not usable(s.get(t - 15 * MIN)) or not spread_ok(s[t]): continue
            sg = sigma1(s, t)
            if sg is None or sg <= 0: continue
            r = returns(s, range(t - 14 * MIN, t + 1, MIN))
            if len(r) < 10: continue
            sd = sample_std(r)
            if sd is None or not sd / sg >= par: continue
            mv = math.log(mid(s[t]) / mid(s[t - 15 * MIN]))
            if mv != 0: out.append((t, 1 if mv > 0 else -1))
    elif kind == "orb":
        by = {}
        for t in ts: by.setdefault(day_of(t), []).append(t)
        for L in sorted(by):
            o = L4.et_end(L, 9, 30); rng = [s.get(o + MIN * i) for i in range(1, par + 1)]
            if not all(usable(c) for c in rng): continue
            hi, lo = max(mid(c) for c in rng), min(mid(c) for c in rng)
            for t in by[L]:
                if t <= o + par * MIN: continue
                m = mid(s[t])
                if m > hi or m < lo:
                    if spread_ok(s[t]) and sigma1(s, t) is not None and sigma1(s, t) > 0: out.append((t, 1 if m > hi else -1))
                    break
    else:
        for t in ts:
            if not usable(s.get(t - MIN)) or not spread_ok(s[t]): continue
            prev = [s[u][2] for u in range(t - 60 * MIN, t, MIN) if u in s and (s[u][2] or 0) > 0]
            if len(prev) < 20: continue
            if not (s[t][2] or 0) >= par * (sum(prev) / len(prev)): continue
            mv = mid(s[t]) - mid(s[t - MIN])
            if mv == 0: continue
            sg = sigma1(s, t)
            if sg is None or sg <= 0: continue
            out.append((t, 1 if mv > 0 else -1))
    return out


def in_window(w, e):
    L = day_of(e)
    if not L4.is_session(L): return False
    cap = session_end(L) - 10 * MIN; o = lambda hh, mm: L4.et_end(L, hh, mm)
    if w == "W0": return o(9, 35) <= e <= cap
    if w == "W1": return o(9, 35) <= e <= min(o(10, 0), cap)
    if w == "W2": return o(10, 0) < e <= min(o(11, 0), cap)
    return o(15, 0) < e <= cap


def spanning(f, e, x): return sum(r for ts, r in (f or {}).items() if e < ts < x), sum(1 for ts in (f or {}) if e < ts < x)


def entry_of(s, t, d, col, h, tick):
    """-> (entry_end, entry_price, entry_fee) or None (no entry candle, no fill)"""
    if col in ("TT", "TS"):
        c = s.get(t + MIN)
        if not usable(c): return None
        return t + MIN, (c[1] * (1 + h) if d > 0 else c[0] * (1 - h)), TAKER
    N = int(col[2]); c0 = s[t]; limit = c0[0] if d > 0 else c0[1]
    if tick is None: return None
    for k in range(1, N + 1):
        c = s.get(t + k * MIN)
        if not usable(c): continue
        if (d > 0 and c[1] <= limit - tick + 1e-9) or (d < 0 and c[0] >= limit + tick - 1e-9): return t + k * MIN, limit, MAKER
    return None


def exit_of(s, t, d, e, entry, kt, T, h, col, tick, U):
    """-> (exit_end, exit_price, exit_fee, kind) or None (dropped: no_exit_candle)"""
    ref = mid(s[t]); tgt = ref * (1 + d * kt * U); stp = ref * (1 - d * U); L = day_of(e)
    plan = min(e + T, session_end(L)); tc = None
    for k in (0, 1, 2):
        c = s.get(plan - k * MIN)
        if plan - k * MIN > e and usable(c): tc = plan - k * MIN; break
    if tc is None: return None
    passive = col.startswith("MM")
    for u in range(e + MIN, tc + 1, MIN):
        c = s.get(u)
        if not usable(c): continue
        if d > 0:
            if passive and tick is not None and c[0] >= tgt + tick - 1e-9: return u, tgt, MAKER, "ptarget"
            if c[0] <= stp: return u, c[0] * (1 - h), TAKER, "stop"
            if not passive and c[0] >= tgt: return u, c[0] * (1 - h), TAKER, "target"
        else:
            if passive and tick is not None and c[1] <= tgt - tick + 1e-9: return u, tgt, MAKER, "ptarget"
            if c[1] >= stp: return u, c[1] * (1 + h), TAKER, "stop"
            if not passive and c[1] <= tgt: return u, c[1] * (1 + h), TAKER, "target"
    c = s[tc]; return tc, (c[0] * (1 - h) if d > 0 else c[1] * (1 + h)), TAKER, "time"


def run_cell(data, funding, ticks, cell, col, cap=None):
    """one cell and column pooled over names -> (trades, counts); trade = {name, e, side, day, net, span, ref U}"""
    (eid, kind, par), w, kt, T = cell; h = HS if col == "TS" else HG; trades, cnt = [], {"no_entry": 0, "window": 0, "cooldown": 0, "no_exit_candle": 0}
    for name in sorted(data):
        s = data[name]; last_exit = last_entry = None
        key = (id(s), kind, par)
        if key not in _SIG: _SIG[key] = signals(s, kind, par)
        for (t, d) in _SIG[key]:
            en = entry_of(s, t, d, col, h, ticks.get(name))
            if en is None: cnt["no_entry"] += 1; continue
            e, ep, ef = en
            if not in_window(w, e): cnt["window"] += 1; continue
            if last_exit is not None and not (e >= last_exit and e - last_entry >= 900): cnt["cooldown"] += 1; continue
            U = sigma1(s, t) * math.sqrt(10); ex = exit_of(s, t, d, e, ep, kt, T, h, col, ticks.get(name), U)
            if ex is None: cnt["no_exit_candle"] += 1; continue
            x, xp, xf, kind_x = ex; last_exit, last_entry = x, e
            fs, spans = spanning(funding.get(name), e, x); gross = xp / ep - 1 if d > 0 else (ep - xp) / ep
            trades.append({"name": name, "e": e, "x": x, "side": d, "day": day_of(e), "gross": gross, "ep": ep, "xp": xp, "net": gross - ef - xf - d * fs, "ef": ef, "xf": xf, "span": spans > 0, "t": t, "U": U, "kind": kind_x})
    return trades, cnt


def pf(v):
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    if not v: return None
    if neg == 0: return math.inf if pos > 0 else None
    return pos / neg


def zday(trades):
    by = {}
    for t in trades: by[t["day"]] = by.get(t["day"], 0.0) + t["net"]
    v = list(by.values()); k = len(v)
    if k < 2: return None
    m = sum(v) / k; sd = math.sqrt(sum((x - m) ** 2 for x in v) / (k - 1))
    return None if sd == 0 else m / (sd / math.sqrt(k))


def stats(trades):
    ts = sorted(trades, key=lambda t: (t["e"], t["side"])); v = [t["net"] for t in ts]; k = len(v); h = k // 2
    return {"n": k, "days": len(set(t["day"] for t in ts)), "pf": pf(v), "h1": pf(v[:h]), "h2": pf(v[h:]), "z": zday(ts), "mean_bps": (sum(v) / k * 1e4) if k else None, "spanning_funding": sum(1 for t in ts if t["span"])}


def num(x): return 0.0 if x is None else x
def meets(s, pf_min=1.3): return s["n"] >= 100 and s["days"] >= 10 and num(s["pf"]) >= pf_min and num(s["h1"]) >= 1.0 and num(s["h2"]) >= 1.0


def p_upper(z): return None if z is None else 0.5 * math.erfc(z / math.sqrt(2))


def bh(pv, m, q=0.05):
    items = sorted(((v, k) for k, v in pv.items() if v is not None), key=lambda x: (x[0], x[1])); kmax = 0
    for i, (v, k) in enumerate(items, 1):
        if v <= i * q / m: kmax = i
    return {k for v, k in items[:kmax]}


def cells():
    return [(e, w, kt, T) for e in ENTRIES for w in WINDOWS for (kt, T) in EXITS]


LEV_X = (0.10, 0.25, 0.50)


def taker_net(s, name, funding, tick, cell, t, d):
    """hypothetical TT net of one signal (no cooldown), or None (no entry candle, outside window, no exit candle)"""
    (eid, kind, par), w, kt, T = cell; en = entry_of(s, t, d, "TT", HG, tick)
    if en is None or not in_window(w, en[0]): return None
    e, ep, ef = en; U = sigma1(s, t) * math.sqrt(10); ex = exit_of(s, t, d, e, ep, kt, T, HG, "TT", tick, U)
    if ex is None: return None
    x, xp, xf, _ = ex; fs, _n = spanning(funding.get(name), e, x); gross = xp / ep - 1 if d > 0 else (ep - xp) / ep
    return gross - ef - xf - d * fs


def margin(trades, lmax=LMAX):
    """per x in 10, 25, 50 percent of page max (L = x Lmax[name]): mean_pct_of_margin = 100 x mean over trades of net x L; stop_beyond_liquidation = count of trades with U >= 1/L - 0.045 (Desk C's ruling)"""
    out = {}
    for x in LEV_X:
        s, flag, k = 0.0, 0, 0
        for tr in trades:
            L = x * lmax[tr["name"]]; k += 1; s += tr["net"] * L; flag += 1 if tr["U"] >= 1 / L - 0.045 else 0
        out["%d%%" % round(x * 100)] = {"mean_pct_of_margin": 100 * s / k if k else None, "stop_beyond_liquidation": flag}
    return out


def adverse(data, funding, ticks, cell, N):
    """per fill window N: universe = signals with a valid taker trade (ignoring cooldown); filled = maker entry within N candles AND in window AND an exit candle (the maker-entry taker-exit build returns a trade); unfilled otherwise; means of the hypothetical taker net in bps"""
    (eid, kind, par), w, kt, T = cell; col = "MT%d" % N; fl, nf = [], []
    for name in sorted(data):
        s = data[name]; tick = ticks.get(name)
        for (t, d) in signals(s, kind, par):
            tn = taker_net(s, name, funding, tick, cell, t, d)
            if tn is None: continue
            en = entry_of(s, t, d, col, HG, tick); ok = False
            if en is not None and in_window(w, en[0]):
                U = sigma1(s, t) * math.sqrt(10); ok = exit_of(s, t, d, en[0], en[1], kt, T, HG, col, tick, U) is not None
            (fl if ok else nf).append(tn)
    return {"filled_n": len(fl), "filled_mean_bps": sum(fl) / len(fl) * 1e4 if fl else None, "unfilled_n": len(nf), "unfilled_mean_bps": sum(nf) / len(nf) * 1e4 if nf else None}

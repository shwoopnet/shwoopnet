#!/usr/bin/env python3
"""ENGPERPS_POOL1 pooled stock perps pass, BUILD 2 (Testing Desk, Nov 16, 2026), written blind from Desk A's spec v2 (7bd697b4). Pure functions on in-memory data; a loader is separate.
Hand case: POOL1_SECOND_HAND_CASE.md (readings R1 to R9). data: {name: {end_ts: (bid, ask)}}, funding: {name: {print_ts: rate}}."""
import math
import engine1_perps_second as p

H = 3600
TAKER, MAKER = 0.0012, 0.0005
HS = (0.0002, 0.0005)
GAP_CLASSES = (30, 60, 100)
KS = (1, 2); TS = (15, 30, 60)
EXITS = [(kt, ks, t) for kt in KS for ks in KS for t in TS]
FUND_HOLE = 26 * H
r9 = lambda x: round(x, 9)
CUTOFF = 1794873600          # 2026-11-17T00:00:00Z: forward days stay unread (R10)


def et_end(L, hh, mm): return p.day_start_of_local(L) + hh * H + mm * 60          # the UTC instant of hh:mm ET on local ET date L


def usable(q): return p.two_sided(q)


def pool_names(data, funding):
    out = []
    for n in sorted(data):
        days = set(p.et_local_day(t) for t in data[n])
        if len(days) >= 5 and len(funding.get(n, {})) >= 2: out.append(n)
    return out


def trading_dates(data):
    ds = set()
    for n in data:
        for t in data[n]:
            L = p.et_local_day(t)
            if t == et_end(L, 9, 31) and t < CUTOFF: ds.add(L)
    return sorted(ds)


def sigma(s, e):
    rs = []
    for t in range(e - 3540, e + 1, 60):
        a, b = s.get(t), s.get(t - 60)
        if usable(a) and usable(b): rs.append(math.log(p.mid(a) / p.mid(b)))
    if len(rs) < 45: return None
    m = sum(rs) / len(rs)
    return math.sqrt(sum((x - m) ** 2 for x in rs) / len(rs))


def fund_book(funding, e, xt, long_):
    """booked funding of a long (pays a positive rate) or short (receives it) position; None = not booked (the engine's 26 h print rules)"""
    return p.funding_for(funding, e, xt, long_)


def run_exit(s, e, side, kt, ks, T, h, last_ts, u):
    """-> (exit_ts, fill, exit_price) or None (no mark)"""
    q = s.get(e)
    if not usable(q): return None
    long_ = side == "long"
    fill = q[1] * (1 + h) if long_ else q[0] * (1 - h)
    end = e + 60 * T
    if end > last_ts: return None
    tgt = kt * u; stp = ks * u
    for t in range(e + 60, end + 1, 60):
        c = s.get(t)
        if not usable(c): continue
        if long_: stop_hit, tgt_hit = c[0] <= fill * (1 - stp), c[0] >= fill * (1 + tgt)
        else: stop_hit, tgt_hit = c[1] >= fill * (1 + stp), c[1] <= fill * (1 - tgt)
        if stop_hit or tgt_hit: return t, fill, (c[0] * (1 - h) if long_ else c[1] * (1 + h))
    c = s.get(end)
    if not usable(c): return None
    return end, fill, (c[0] * (1 - h) if long_ else c[1] * (1 + h))


def gap_entries(data, cls_bp, mode, names):
    """-> list of (name, e, side), plus skip counts"""
    out, sk = [], {"gap_missing": 0}
    for L in trading_dates(data):
        for n in names:
            s = data[n]; e = et_end(L, 9, 31)
            if e not in s: continue
            Lp = L - 1; lo = min(p.et_local_day(t) for t in s)
            while Lp >= lo and et_end(Lp, 16, 0) not in s: Lp -= 1
            if Lp < lo: sk["gap_missing"] += 1; continue
            a, b = s[e], s[et_end(Lp, 16, 0)]
            if not (usable(a) and usable(b)): sk["gap_missing"] += 1; continue
            g = p.mid(a) / p.mid(b) - 1
            if not r9(abs(g) * 1e4) >= cls_bp: continue
            up = g > 0
            long_ = up if mode == "follow" else not up
            out.append((n, e, "long" if long_ else "short"))
    return out, sk


def latest_print(f, e, maxage=None):
    c = [t for t in f if t < e and (maxage is None or e - t <= maxage)]
    return max(c) if c else None


def rank_entries(data, funding, names, kind, mode):
    out, skipped = [], 0
    for L in trading_dates(data):
        e = et_end(L, 9, 31); vals = {}
        for n in names:
            f = funding.get(n, {}); lt = latest_print(f, e, 36 * H)
            if lt is None: continue
            if kind == "level": vals[n] = f[lt]
            else:
                pv = [t for t in f if t < lt]
                if not pv: continue
                pt = max(pv)
                if lt - pt > 60 * H: continue
                vals[n] = f[lt] - f[pt]
        N = len(vals)
        if N < 3: skipped += 1; continue
        order = sorted(vals, key=lambda n: (-vals[n], n)); k = math.ceil(N / 3)
        for n in order[:k]: out.append((n, e, "short" if mode == "fade" else "long"))
        for n in order[-k:]: out.append((n, e, "long" if mode == "fade" else "short"))
    return out, {"date_skipped": skipped}


def carry_trades(data, funding, names, share, h):
    """share 'A' (top third) or 'B' (top half); -> (trades, counts)"""
    cands = {}
    for n in names:
        f = funding.get(n, {})
        for T in sorted(f):
            e = T - 1800; lt = latest_print(f, e)
            if lt is None or f[lt] == 0: continue
            cands.setdefault(p.et_local_day(e), []).append((n, T, e, f[lt]))
    chosen = []
    for L in sorted(cands):
        c = sorted(cands[L], key=lambda x: (-abs(x[3]), x[0], x[1]))
        if len(set(x[0] for x in c)) < 3: continue
        M = len(c); k = math.ceil(M / 3) if share == "A" else math.ceil(M / 2)
        chosen += c[:k]
    out, cnt = [], {"no_mark": 0, "blocked": 0, "funding_not_booked": 0, "window_dropped": 0}; last = {}
    for (n, T, e, rate) in sorted(chosen, key=lambda x: (x[2], x[0])):
        if n in last and e < last[n]: cnt["blocked"] += 1; continue
        s = data[n]; xt = T + 1800; a, b = s.get(e), s.get(xt)
        if not (usable(a) and usable(b)): cnt["no_mark"] += 1; continue
        if e >= CUTOFF or xt >= CUTOFF: cnt["window_dropped"] += 1; continue
        long_ = rate < 0
        fill = a[1] * (1 + h) if long_ else a[0] * (1 - h); xp = b[0] * (1 - h) if long_ else b[1] * (1 + h)
        gross = xp / fill - 1 if long_ else (fill - xp) / fill
        last[n] = xt; fd = fund_book(funding.get(n), e, xt, long_)
        t = {"name": n, "e": e, "exit_ts": xt, "side": "long" if long_ else "short", "gross": gross, "funding": fd, "day": p.et_local_day(e)}
        if fd is None: cnt["funding_not_booked"] += 1
        else: t["net"] = gross - 2 * TAKER - fd; t["net_maker"] = gross - 2 * MAKER - fd
        out.append(t)
    return out, cnt


def rule_trades(data, funding, entries, ex, h):
    """entries: [(name, e, side)]; ex = (kt, ks, T). -> (trades, counts)"""
    kt, ks, T = ex
    out, cnt = [], {"no_entry": 0, "blocked": 0, "no_vol": 0, "no_mark": 0, "funding_not_booked": 0, "window_dropped": 0}; last = {}; lastts = {n: max(data[n]) for n in data}
    for (n, e, side) in sorted(entries, key=lambda x: (x[1], x[0])):
        s = data[n]
        if not usable(s.get(e)): cnt["no_entry"] += 1; continue
        if n in last and e < last[n]: cnt["blocked"] += 1; continue
        sg = sigma(s, e)
        if sg is None: cnt["no_vol"] += 1; continue
        r = run_exit(s, e, side, kt, ks, T, h, lastts[n], sg * math.sqrt(30))
        if r is None: cnt["no_mark"] += 1; continue
        xt, fill, xp = r; long_ = side == "long"
        if e >= CUTOFF or xt >= CUTOFF: cnt["window_dropped"] += 1; continue
        last[n] = xt
        gross = xp / fill - 1 if long_ else (fill - xp) / fill
        fd = fund_book(funding.get(n), e, xt, long_)
        t = {"name": n, "e": e, "exit_ts": xt, "side": side, "gross": gross, "funding": fd, "day": p.et_local_day(e)}
        if fd is None: cnt["funding_not_booked"] += 1
        else: t["net"] = gross - 2 * TAKER - fd; t["net_maker"] = gross - 2 * MAKER - fd
        out.append(t)
    return out, cnt


def pf(v):
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    if neg == 0: return math.inf if pos > 0 else math.nan
    return pos / neg


def booked(tr, key="net"): return sorted([t for t in tr if t.get("funding") is not None], key=lambda t: (t["e"], t["name"]))


def gate(tr_lo, tr_hi, ndays):
    a, b = booked(tr_lo), booked(tr_hi)
    if not a or not b or ndays == 0: return False, {}
    def halves(x): k = len(x) // 2; return x[:k], x[k:]
    def okpf(x, lim): v = [t["net"] for t in x]; f = pf(v); return (not math.isnan(f)) and f >= lim
    a1, a2 = halves(a); b1, b2 = halves(b)
    net = sum(t["net"] for t in a); days = {}
    for t in a: days[t["day"]] = days.get(t["day"], 0.0) + t["net"]
    share = max(days.values()) / net if net > 0 else math.inf
    info = {"n": len(a), "per_day": len(a) / ndays, "pf_lo": pf([t["net"] for t in a]), "pf_hi": pf([t["net"] for t in b]), "net_hi": sum(t["net"] for t in b), "share": share}
    ok = (len(a) / ndays >= 3 and okpf(a, 1.3) and okpf(b, 1.0) and okpf(a1, 1.3) and okpf(a2, 1.3) and okpf(b1, 1.0) and okpf(b2, 1.0) and share <= 0.3 and info["net_hi"] > 0)
    return ok, info


def trend_candidates(data, names, lookback, c, mode, sig=None):
    """{name: [(e, side, u)]} candles in order that qualify (independent of any position); lookback L minutes, threshold c in u"""
    days = set(trading_dates(data)); out = {}
    for n in names:
        s = data[n]; lst = []
        for e in sorted(s):
            L = p.et_local_day(e)
            if L not in days or not (et_end(L, 10, 31) <= e <= et_end(L, 15, 30)) or not usable(s[e]): continue
            lb = e - 60 * lookback
            if not (usable(s.get(lb)) and p.et_local_day(lb) == L and lb >= et_end(L, 9, 31)): continue
            if sig is not None and (n, e) in sig: sg = sig[(n, e)]
            else:
                sg = sigma(s, e)
                if sig is not None: sig[(n, e)] = sg
            if sg is None: continue
            u = sg * math.sqrt(30); R = math.log(p.mid(s[e]) / p.mid(s[lb]))
            if not abs(R) > c * u: continue
            up = R > 0
            lst.append((e, "long" if (up if mode == "trend" else not up) else "short", u))
        out[n] = lst
    return out


def trend_trades(data, funding, cands, ex, h):
    """cands from trend_candidates; ex = (kt, ks, T). The first qualifying candle at or after the name's previous exit end; a no-mark candle opens nothing."""
    kt, ks, T = ex; out, cnt = [], {"no_mark": 0, "funding_not_booked": 0, "window_dropped": 0}
    for n in sorted(cands):
        s = data[n]; last_ts = max(s); free = -math.inf
        for (e, side, u) in cands[n]:
            if e < free: continue
            r = run_exit(s, e, side, kt, ks, T, h, last_ts, u)
            if r is None: cnt["no_mark"] += 1; continue
            xt, fill, xp = r; long_ = side == "long"
            if e >= CUTOFF or xt >= CUTOFF: cnt["window_dropped"] += 1; continue
            free = xt; gross = xp / fill - 1 if long_ else (fill - xp) / fill
            fd = fund_book(funding.get(n), e, xt, long_)
            t = {"name": n, "e": e, "exit_ts": xt, "side": side, "gross": gross, "funding": fd, "day": p.et_local_day(e)}
            if fd is None: cnt["funding_not_booked"] += 1
            else: t["net"] = gross - 2 * TAKER - fd; t["net_maker"] = gross - 2 * MAKER - fd
            out.append(t)
    return out, cnt

"""The 42 strategies of the strategy search (rules fixed in the README, "Pre-registration: the strategy search", before this file existed).

A strategy is a SIGNAL: it reads the market at a signal candle `js` through a Ctx and returns a side or None. The trade is made by the runner
(stratsearch.py) on the NEXT candle, `js + 1`. Nothing in this file reads a result of the market being traded, a candle after the signal candle,
a spot minute that closes after the signal, or a market that had not closed: the Ctx raises Lookahead if asked. The results of EARLIER, closed
markets are reachable only through Ctx.chain / Ctx.twin_prev / Ctx.prev_any, which also check that they closed at or before the signal.

No function here takes a performance parameter. Every number is in a spec's `params`, fixed in the README before any data was read.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

from .analyze import valid_quote

BTC, GOLD = "KXBTC15M", "KXGOLD15M"
BOTH = (BTC, GOLD)
BAND = (0.10, 0.90)             # the universal entry price band (a cost universe), unless a spec narrows it
EPS = 1e-9


class Lookahead(Exception):
    """A feature asked for something that was not known at the signal candle."""


# ---------------------------------------------------------------------------------------------------------------- world and view

def make_market(ticker, series, open_ts, close_ts, res, strike, cand):
    """cand: {j: (bid_o, bid_h, bid_l, bid_c, ask_o, ask_h, ask_l, ask_c, price_c, volume, oi)} for j = 1..15."""
    return {"ticker": ticker, "series": series, "open": open_ts, "close": close_ts, "res": res, "strike": strike, "cand": cand,
            "day": datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")}


class World:
    """All markets and the Bitcoin spot minutes. Only Ctx should be used to read it from a strategy."""

    def __init__(self, markets: list[dict], spot: dict[int, float] | None = None):
        self.ms = sorted(markets, key=lambda m: (m["open"], m["series"]))
        self.by = {(m["series"], m["open"]): m for m in self.ms}
        self.series: dict[str, list[dict]] = {}
        for m in self.ms:
            self.series.setdefault(m["series"], []).append(m)
        for lst in self.series.values():
            for i, m in enumerate(lst):
                m["i"] = i
        for m in self.ms:
            cs = [m["cand"].get(j) for j in range(1, 8)]
            m["V7"] = sum(c[9] for c in cs if c is not None and c[9] is not None)
            c1 = m["cand"].get(1)
            m["vol1"] = c1[9] if c1 is not None and c1[9] is not None else None
        spot = spot or {}
        if spot:
            self.t0 = min(spot)
            n = (max(spot) - self.t0) // 60 + 1
            self.sp = [None] * n
            for ts, v in spot.items():
                self.sp[(ts - self.t0) // 60] = v
        else:
            self.t0, self.sp = 0, []
        self._range20 = None
        self._day = {}

    def spot_end(self, end_ts: int):
        """Spot close of the minute candle that ENDS at end_ts (it starts a minute earlier)."""
        i = (end_ts - 60 - self.t0) // 60
        return self.sp[i] if 0 <= i < len(self.sp) else None

    def range20(self):
        if self._range20 is None:
            sp, out = self.sp, [None] * len(self.sp)
            for i in range(19, len(sp)):
                w = sp[i - 19:i + 1]
                if None not in w:
                    out[i] = (max(w) - min(w)) / sp[i]
            self._range20 = out
        return self._range20

    def day_hilo(self, day_start: int):
        if day_start not in self._day:
            vals = [v for ts in range(day_start, day_start + 86400, 60) if (v := self.spot_end(ts + 60)) is not None]
            self._day[day_start] = (max(vals), min(vals)) if len(vals) >= 1000 else None
        return self._day[day_start]


class Ctx:
    """The market `m` as it stands at the close of candle `js`. Anything later raises Lookahead."""

    def __init__(self, w: World, m: dict, js: int):
        self.w, self.m, self.js = w, m, js
        self.cut = m["open"] + 60 * js

    # ---- the market's own candles (up to and including js)
    def _chk(self, j: int) -> None:
        if j > self.js or j < 1:
            raise Lookahead(f"candle {j} asked at signal candle {self.js}")

    def cand(self, j: int):
        self._chk(j)
        return self.m["cand"].get(j)

    def q(self, j: int):
        c = self.cand(j)
        return None if c is None or c[3] is None or c[7] is None else (c[3], c[7])

    def mid(self, j: int):
        q = self.q(j)
        return (q[0] + q[1]) / 2 if q is not None and valid_quote(*q) else None

    def vol(self, j: int):
        c = self.cand(j)
        return None if c is None or c[9] is None else c[9]

    def oi(self, j: int):
        c = self.cand(j)
        return None if c is None or c[10] is None else c[10]

    def pc(self, j: int):
        c = self.cand(j)
        return None if c is None else c[8]

    @property
    def strike(self):
        return self.m["strike"]

    # ---- other markets
    def _closed(self, pm):
        if pm is not None and pm["close"] > self.cut:
            raise Lookahead("market had not closed")
        return pm

    def chain(self, n: int):
        """The n previous CONTIGUOUS markets of this series, nearest first, or None. Each is closed by construction."""
        out, t = [], self.m["open"]
        for _ in range(n):
            t -= 900
            pm = self.w.by.get((self.m["series"], t))
            if pm is None:
                return None
            out.append(self._closed(pm))
        return out

    def strikes_back(self, n: int):
        """[x_(N-n), ..., x_N] of contiguous strikes, or None."""
        ch = self.chain(n)
        if ch is None or self.m["strike"] is None or any(p["strike"] is None for p in ch):
            return None
        return [p["strike"] for p in reversed(ch)] + [self.m["strike"]]

    def prev_any(self):
        i = self.m["i"]
        return self._closed(self.w.series[self.m["series"]][i - 1]) if i > 0 else None

    def prior(self, n: int):
        i = self.m["i"]
        lst = self.w.series[self.m["series"]]
        return [self._closed(p) for p in lst[max(0, i - n):i]]

    def twin(self):
        """The other series' market with the same open, viewed at the same signal candle (so it cannot look ahead either)."""
        other = GOLD if self.m["series"] == BTC else BTC
        tm = self.w.by.get((other, self.m["open"]))
        return Ctx(self.w, tm, self.js) if tm is not None else None

    def twin_prev(self):
        other = GOLD if self.m["series"] == BTC else BTC
        return self._closed(self.w.by.get((other, self.m["open"] - 900)))

    def at(self, series: str, open_ts: int):
        return self._closed(self.w.by.get((series, open_ts)))

    # ---- Bitcoin spot (closes that are known at the signal)
    def s(self, k: int):
        """Spot close k minutes before the signal (k = 0 is the minute that closes at the signal candle)."""
        if k < 0:
            raise Lookahead("spot from the future")
        return self.w.spot_end(self.cut - 60 * k)

    def spots(self, n: int):
        v = [self.s(k) for k in range(n)]
        return None if None in v else v

    def spot_at(self, end_ts: int):
        if end_ts > self.cut:
            raise Lookahead("spot from the future")
        return self.w.spot_end(end_ts)

    def day_hilo(self, day_start: int):
        if day_start + 86400 > self.cut:
            raise Lookahead("day not finished")
        return self.w.day_hilo(day_start)

    def range_pctl(self, q: float, lookback: int, min_present: int):
        """The q-th percentile of the 20 minute spot range over the `lookback` minutes that end at the signal."""
        w = self.w
        i = (self.cut - 60 - w.t0) // 60
        r = w.range20()
        vals = sorted(v for v in r[max(0, i - lookback + 1):i + 1] if v is not None)
        return vals[int(q * (len(vals) - 1))] if len(vals) >= min_present else None


# ---------------------------------------------------------------------------------------------------------------- small helpers

def sgn(x: float) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


def side_of(x: float):
    return "yes" if x > 0 else ("no" if x < 0 else None)


def opp(side):
    return None if side is None else ("no" if side == "yes" else "yes")


def mean(v):
    return sum(v) / len(v)


def median(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def std(v):
    m = mean(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))


def corr(a, b):
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den > 0 else 0.0


def logret(a, b):
    return math.log(a / b)


def sigma1(c: Ctx, end_k: int = 0):
    """Sample std of the 60 one minute log returns whose later close is s_end_k .. s_(end_k+59). Needs s_end_k .. s_(end_k+60)."""
    v = [c.s(end_k + k) for k in range(61)]
    if None in v:
        return None
    return std([logret(v[i], v[i + 1]) for i in range(60)])


def percentile(values, q):
    s = sorted(values)
    return s[int(q * (len(s) - 1))]


# ---------------------------------------------------------------------------------------------------------------- registry

SPECS: list[dict] = []


def strat(id_, fam, name, series, js, params=None, hold=None, band=BAND, baseline=None, universe="fixed"):
    """Register a signal. `params` is everything the signal uses, and it is what gets saved with the result."""
    p = dict(params or {})

    def deco(f):
        SPECS.append({"id": id_, "family": fam, "name": name, "series": tuple(series), "js": tuple(js), "hold": hold, "band": tuple(band),
                      "params": p, "baseline": baseline, "universe": universe, "sig": (lambda c, _f=f, _p=p: _f(c, _p))})
        return f
    return deco


UNDER = (0.10, 0.40)
OVER = (0.60, 0.90)


# ---------------------------------------------------------------------------------------------------------------- A. cross market

@strat("S01", "A", "Gold leads Bitcoin", [BTC], [5], {"thr": 0.05, "from": 1, "to": 5, "signal_market": "gold twin"})
def s01(c, p):
    t = c.twin()
    if t is None:
        return None
    a, b = t.mid(p["from"]), t.mid(p["to"])
    if a is None or b is None:
        return None
    d = b - a
    return "yes" if d >= p["thr"] - EPS else ("no" if d <= -p["thr"] + EPS else None)


@strat("S02", "A", "Bitcoin leads gold", [GOLD], [5], {"thr": 0.05, "from": 1, "to": 5, "signal_market": "Bitcoin twin"})
def s02(c, p):
    t = c.twin()
    if t is None:
        return None
    a, b = t.mid(p["from"]), t.mid(p["to"])
    if a is None or b is None:
        return None
    d = b - a
    return "yes" if d >= p["thr"] - EPS else ("no" if d <= -p["thr"] + EPS else None)


@strat("S03", "A", "Laggard catch-up", [BTC], [5], {"thr": 0.05, "from": 1, "to": 5, "tie": "Bitcoin"})
def s03(c, p):
    t = c.twin()
    if t is None:
        return None
    ab, bb, ag, bg = c.mid(p["from"]), c.mid(p["to"]), t.mid(p["from"]), t.mid(p["to"])
    if None in (ab, bb, ag, bg):
        return None
    db, dg = bb - ab, bg - ag
    th = p["thr"] - EPS
    if db >= th and dg >= th:
        return ("yes", "self" if db <= dg else "twin")          # the smaller rise; a tie is Bitcoin
    if db <= -th and dg <= -th:
        return ("no", "self" if db >= dg else "twin")           # the smaller fall
    return None


@strat("S04", "A", "Previous Bitcoin outcome carries into gold", [GOLD], [1], {"lag_windows": 1})
def s04(c, p):
    tp = c.twin_prev()
    return None if tp is None or tp["res"] not in ("yes", "no") else tp["res"]


@strat("S05", "A", "Previous gold outcome carries into Bitcoin", [BTC], [1], {"lag_windows": 1})
def s05(c, p):
    tp = c.twin_prev()
    return None if tp is None or tp["res"] not in ("yes", "no") else tp["res"]


# ---------------------------------------------------------------------------------------------------------------- B. serial structure

@strat("S06", "B", "Outcome persistence", BOTH, [1], {"lag_windows": 1})
def s06(c, p):
    ch = c.chain(1)
    return None if ch is None or ch[0]["res"] not in ("yes", "no") else ch[0]["res"]


@strat("S07", "B", "Streak exhaustion", BOTH, [1], {"streak": 3})
def s07(c, p):
    ch = c.chain(p["streak"])
    if ch is None:
        return None
    r = {x["res"] for x in ch}
    return opp(next(iter(r))) if len(r) == 1 and r <= {"yes", "no"} else None


@strat("S08", "B", "Regime majority", BOTH, [1], {"window": 12, "min_count": 8})
def s08(c, p):
    ch = c.chain(p["window"])
    if ch is None:
        return None
    y = sum(1 for x in ch if x["res"] == "yes")
    n = sum(1 for x in ch if x["res"] == "no")
    if y >= p["min_count"]:
        return "yes"
    if n >= p["min_count"]:
        return "no"
    return None


@strat("S09", "B", "Shock reversal", BOTH, [1], {"baseline_moves": 24, "mult": 2.0, "strikes_needed": 26})
def s09(c, p):
    xs = c.strikes_back(p["strikes_needed"] - 1)
    if xs is None:
        return None
    r = [logret(xs[i + 1], xs[i]) for i in range(len(xs) - 1)]      # r[-1] is the previous market's move
    m1, base = r[-1], [abs(v) for v in r[:-1]][-p["baseline_moves"]:]
    M = median(base)
    if M <= 0 or abs(m1) < p["mult"] * M - EPS:
        return None
    return side_of(-m1)


@strat("S10", "B", "Surprise clustering (L13 adjacent)", BOTH, [7], {"prev_candle": 13, "extreme": 0.85}, band=UNDER, baseline="under")
def s10(c, p):
    ch = c.chain(1)
    if ch is None:
        return None
    pm = ch[0]
    q = pm["cand"].get(p["prev_candle"])
    if q is None or q[3] is None or q[7] is None or not valid_quote(q[3], q[7]):
        return None
    mid = (q[3] + q[7]) / 2
    if (mid >= p["extreme"] - EPS and pm["res"] == "no") or (mid <= 1 - p["extreme"] + EPS and pm["res"] == "yes"):
        return "under"
    return None


@strat("S11", "B", "Autocorrelation regime of strike moves", BOTH, [1], {"moves": 24, "rho": 0.2})
def s11(c, p):
    xs = c.strikes_back(p["moves"])
    if xs is None:
        return None
    r = [logret(xs[i + 1], xs[i]) for i in range(len(xs) - 1)]
    rho = corr(r[:-1], r[1:])
    if rho >= p["rho"] - EPS:
        return side_of(r[-1])
    if rho <= -p["rho"] + EPS:
        return side_of(-r[-1])
    return None


# ---------------------------------------------------------------------------------------------------------------- C. calendar

def _when(c):
    return datetime.fromtimestamp(c.m["open"], timezone.utc)


@strat("S12", "C", "US cash open underdog (L13 adjacent)", [BTC], [7], {"opens_utc": ["13:30", "13:45", "14:00", "14:15"], "weekdays": "Mon-Fri"},
       band=UNDER, baseline="under")
def s12(c, p):
    t = _when(c)
    return "under" if t.weekday() < 5 and f"{t.hour:02d}:{t.minute:02d}" in p["opens_utc"] else None


@strat("S13", "C", "Weekend quiet favorite (L13 adjacent)", [BTC], [7], {"weekdays": "Sat, Sun"}, band=OVER, baseline="over")
def s13(c, p):
    return "over" if _when(c).weekday() >= 5 else None


@strat("S14", "C", "Gold reopen gap fade", [GOLD], [1], {"min_gap_s": 2700, "min_abs_log_gap": 0.0005})
def s14(c, p):
    pm = c.prev_any()
    if pm is None or c.m["open"] - pm["open"] < p["min_gap_s"] or pm["strike"] is None or c.strike is None:
        return None
    g = logret(c.strike, pm["strike"])
    return side_of(-g) if abs(g) >= p["min_abs_log_gap"] - EPS else None


@strat("S15", "C", "London open breakout of the Asian range", BOTH, [1],
       {"trade_opens_utc": ["07:00", "09:45"], "range_opens_utc": ["00:00", "06:45"], "min_present": 20})
def s15(c, p):
    day0 = c.m["open"] - c.m["open"] % 86400
    off = c.m["open"] - day0
    if not (7 * 3600 <= off <= 9 * 3600 + 45 * 60) or c.strike is None:
        return None
    xs = []
    for k in range(28):
        pm = c.at(c.m["series"], day0 + 900 * k)
        if pm is not None and pm["strike"] is not None:
            xs.append(pm["strike"])
    if len(xs) < p["min_present"]:
        return None
    if c.strike > max(xs):
        return "yes"
    if c.strike < min(xs):
        return "no"
    return None


# ---------------------------------------------------------------------------------------------------------------- D. Bitcoin spot path

@strat("S16", "D", "Acceleration", [BTC], [6], {"short": 3, "ratio": 1.5, "sigma_mult": 0.75})
def s16(c, p):
    v, sg = c.spots(2 * p["short"] + 1), sigma1(c)
    if v is None or sg is None:
        return None
    k = p["short"]
    ra, rb = logret(v[0], v[k]), logret(v[k], v[2 * k])
    if ra == 0 or sgn(ra) != sgn(rb) or abs(ra) < p["ratio"] * abs(rb) - EPS or abs(ra) < p["sigma_mult"] * sg * math.sqrt(k) - EPS:
        return None
    return side_of(ra)


@strat("S17", "D", "Large 5 minute move fade", [BTC], [7], {"minutes": 5, "sigmas": 2.0})
def s17(c, p):
    a, b, sg = c.s(0), c.s(p["minutes"]), sigma1(c)
    if None in (a, b, sg):
        return None
    r = logret(a, b)
    return side_of(-r) if abs(r) >= p["sigmas"] * sg * math.sqrt(p["minutes"]) - EPS else None


@strat("S18", "D", "Stretch from the hour's mean fade", [BTC], [8], {"mean_minutes": 60, "z": 1.5, "scale_sqrt": 20})
def s18(c, p):
    v, sg = c.spots(p["mean_minutes"]), sigma1(c)
    if v is None or sg is None:
        return None
    z = logret(v[0], mean(v)) / (sg * math.sqrt(p["scale_sqrt"]))
    return side_of(-z) if abs(z) >= p["z"] - EPS else None


@strat("S19", "D", "Compression breakout", [BTC], [6], {"range_minutes": 20, "pctl": 0.25, "lookback_minutes": 10080, "min_present": 5000})
def s19(c, p):
    v = c.spots(p["range_minutes"])
    if v is None:
        return None
    s0 = v[0]
    if s0 == max(v) and s0 > min(v):
        side = "yes"
    elif s0 == min(v) and s0 < max(v):
        side = "no"
    else:
        return None
    q = c.range_pctl(p["pctl"], p["lookback_minutes"], p["min_present"])
    return side if q is not None and (max(v) - min(v)) / s0 <= q + EPS else None


@strat("S20", "D", "Multi scale trend agreement", [BTC], [8], {"scales": [5, 15, 60], "sigma_mult": 0.5})
def s20(c, p):
    s0, sg = c.s(0), sigma1(c)
    if s0 is None or sg is None:
        return None
    rs = []
    for k in p["scales"]:
        sk = c.s(k)
        if sk is None:
            return None
        rs.append(logret(s0, sk))
    if len({sgn(r) for r in rs}) != 1 or rs[0] == 0 or abs(rs[-1]) < p["sigma_mult"] * sg * math.sqrt(p["scales"][-1]) - EPS:
        return None
    return side_of(rs[0])


@strat("S21", "D", "Jump reversal", [BTC], [7], {"window": 10, "baseline_window": 60, "sigmas": 3.0})
def s21(c, p):
    v = c.spots(p["window"] + p["baseline_window"] + 1)
    if v is None:
        return None
    r = [logret(v[i], v[i + 1]) for i in range(len(v) - 1)]
    win, base = r[:p["window"]], r[p["window"]:]
    sb = std(base)
    star = max(win, key=abs)
    return side_of(-star) if sb > 0 and abs(star) >= p["sigmas"] * sb - EPS else None


@strat("S22", "D", "Capitulation bounce", [BTC], [8], {"hilo_minutes": 180, "draw": 0.01, "extreme_minutes": 15})
def s22(c, p):
    v = c.spots(p["hilo_minutes"])
    if v is None:
        return None
    s0, recent = v[0], v[:p["extreme_minutes"]]
    if s0 <= max(v) * (1 - p["draw"]) + EPS and s0 == min(recent):
        return "yes"
    if s0 >= min(v) * (1 + p["draw"]) - EPS and s0 == max(recent):
        return "no"
    return None


@strat("S23", "D", "Run exhaustion", [BTC], [7], {"run": 5})
def s23(c, p):
    v = c.spots(p["run"] + 1)
    if v is None:
        return None
    r = [logret(v[i], v[i + 1]) for i in range(p["run"])]
    return side_of(-r[0]) if r[0] != 0 and all(sgn(x) == sgn(r[0]) for x in r) else None


@strat("S24", "D", "Prior day extreme rejection", [BTC], [6], {"band": 0.001})
def s24(c, p):
    day0 = c.cut - c.cut % 86400 - 86400
    hl = c.day_hilo(day0)
    s0 = c.s(0)
    if hl is None or s0 is None:
        return None
    hi, lo = hl
    if hi * (1 - p["band"]) - EPS <= s0 <= hi:
        return "no"
    if lo <= s0 <= lo * (1 + p["band"]) + EPS:
        return "yes"
    return None


@strat("S25", "D", "Minute autocorrelation regime", [BTC], [7], {"rho": 0.15, "r3_minutes": 3, "sigma_mult": 0.5})
def s25(c, p):
    v = c.spots(61)
    if v is None:
        return None
    r = [logret(v[i], v[i + 1]) for i in range(60)]
    rho = corr(r[:-1], r[1:])
    k = p["r3_minutes"]
    r3, sg = logret(v[0], v[k]), std(r)
    if abs(r3) < p["sigma_mult"] * sg * math.sqrt(k) - EPS:
        return None
    if rho >= p["rho"] - EPS:
        return side_of(r3)
    if rho <= -p["rho"] + EPS:
        return side_of(-r3)
    return None


@strat("S26", "D", "Hourly open anchor", [BTC], [7], {"open_minutes": [15, 30, 45], "z": 1.5})
def s26(c, p):
    mn = (c.m["open"] % 3600) // 60
    if mn not in p["open_minutes"]:
        return None
    top = c.cut - c.cut % 3600
    h0, s0, sg = c.spot_at(top), c.s(0), sigma1(c)
    m = (c.cut - top) // 60
    if None in (h0, s0, sg) or sg <= 0 or m <= 0:
        return None
    z = logret(s0, h0) / (sg * math.sqrt(m))
    return side_of(-z) if abs(z) >= p["z"] - EPS else None


# ---------------------------------------------------------------------------------------------------------------- E. the market's own price path

@strat("S27", "E", "Spike fade scalp", BOTH, range(3, 11), {"jump": 0.12}, hold=3)
def s27(c, p):
    a, b = c.mid(c.js - 1), c.mid(c.js)
    if a is None or b is None or abs(b - a) < p["jump"] - EPS:
        return None
    return side_of(a - b)


@strat("S28", "E", "Choppy market underdog (L13 adjacent)", BOTH, [9], {"crossings": 3, "candles": 9}, band=UNDER, baseline="under")
def s28(c, p):
    seq = []
    for j in range(1, p["candles"] + 1):
        m = c.mid(j)
        if m is not None and m != 0.5:
            seq.append(1 if m > 0.5 else -1)
    return "under" if sum(1 for a, b in zip(seq, seq[1:]) if a != b) >= p["crossings"] else None


@strat("S29", "E", "Wick rejection scalp", BOTH, range(3, 11), {"wick": 0.10, "close_band": [0.15, 0.85]}, hold=3)
def s29(c, p):
    cd = c.cand(c.js)
    if cd is None or None in (cd[1], cd[3], cd[6], cd[7]):
        return None
    lo, hi = p["close_band"]
    up = cd[1] - cd[3] >= p["wick"] - EPS and lo <= cd[3] <= hi
    dn = cd[7] - cd[6] >= p["wick"] - EPS and lo <= cd[7] <= hi
    if up and not dn:
        return "no"
    if dn and not up:
        return "yes"
    return None


@strat("S30", "E", "Last trade flow proxy (L11 proxy)", BOTH, [6], {"candles": [4, 5, 6], "thr": 0.01, "min_obs": 2})
def s30(c, p):
    f = []
    for j in p["candles"]:
        m, pc = c.mid(j), c.pc(j)
        if m is not None and pc is not None:
            f.append(pc - m)
    if len(f) < p["min_obs"]:
        return None
    a = mean(f)
    return "yes" if a >= p["thr"] - EPS else ("no" if a <= -p["thr"] + EPS else None)


@strat("S31", "E", "Dwell reversion", BOTH, [10], {"candles": 10, "min_valid": 8, "share": 0.7})
def s31(c, p):
    mids = [c.mid(j) for j in range(1, p["candles"] + 1)]
    valid = [m for m in mids if m is not None]
    if len(valid) < p["min_valid"] or mids[-1] is None:
        return None
    f = sum(1 for m in valid if m > 0.5) / len(valid)
    if f >= p["share"] - EPS and mids[-1] < 0.5:
        return "yes"
    if f <= 1 - p["share"] + EPS and mids[-1] > 0.5:
        return "no"
    return None


@strat("S32", "E", "One sided quote pull", BOTH, range(3, 11), {"pull": 0.03, "other_side_slack": 0.01})
def s32(c, p):
    a, b = c.q(c.js - 1), c.q(c.js)
    if a is None or b is None or not valid_quote(*a) or not valid_quote(*b):
        return None
    dbid, dask = b[0] - a[0], b[1] - a[1]
    bear = dbid <= -p["pull"] + EPS and dask >= -p["other_side_slack"] - EPS
    bull = dask >= p["pull"] - EPS and dbid <= p["other_side_slack"] + EPS
    return "no" if bear and not bull else ("yes" if bull and not bear else None)


@strat("S33", "E", "Market price compression breakout", BOTH, [9], {"from": 2, "to": 8, "min_valid": 6, "max_range": 0.08, "break": 0.03})
def s33(c, p):
    mids = [m for m in (c.mid(j) for j in range(p["from"], p["to"] + 1)) if m is not None]
    m9 = c.mid(c.js)
    if len(mids) < p["min_valid"] or m9 is None or max(mids) - min(mids) > p["max_range"] + EPS:
        return None
    if m9 > max(mids) + p["break"] - EPS:
        return "yes"
    if m9 < min(mids) - p["break"] + EPS:
        return "no"
    return None


# ---------------------------------------------------------------------------------------------------------------- F. spread, volume, open interest

def _prior_vols(c, lo, hi, need=3):
    v = [c.vol(j) for j in range(lo, hi + 1)]
    v = [x for x in v if x is not None and x > 0]
    return v if len(v) >= need else None


@strat("S34", "F", "Spread shock", BOTH, range(4, 11), {"spread": 0.03, "mult": 3.0, "min_prior": 3, "move": 0.03})
def s34(c, p):
    q = c.q(c.js)
    if q is None or not valid_quote(*q) or q[1] - q[0] < p["spread"] - EPS:
        return None
    prior = []
    for j in range(2, c.js):
        qj = c.q(j)
        if qj is not None and valid_quote(*qj):
            prior.append(qj[1] - qj[0])
    if len(prior) < p["min_prior"] or q[1] - q[0] < p["mult"] * median(prior) - EPS:
        return None
    a, b = c.mid(c.js - 2), c.mid(c.js)
    if a is None or b is None or abs(b - a) < p["move"] - EPS:
        return None
    return side_of(b - a)


@strat("S35", "F", "Volume surge follow-through", BOTH, range(5, 12), {"mult": 3.0, "min_prior": 3, "move": 0.04})
def s35(c, p):
    v = c.vol(c.js)
    prior = _prior_vols(c, 2, c.js - 1, p["min_prior"])
    if v is None or prior is None or v < p["mult"] * mean(prior) - EPS:
        return None
    a, b = c.mid(c.js - 1), c.mid(c.js)
    if a is None or b is None or abs(b - a) < p["move"] - EPS:
        return None
    return side_of(b - a)


@strat("S36", "F", "Open interest new money", BOTH, [8], {"from": 5, "to": 8, "oi_growth": 0.10, "move": 0.05})
def s36(c, p):
    o0, o1, m0, m1 = c.oi(p["from"]), c.oi(p["to"]), c.mid(p["from"]), c.mid(p["to"])
    if None in (o0, o1, m0, m1) or o0 <= 0 or o1 / o0 - 1 < p["oi_growth"] - EPS:
        return None
    d = m1 - m0
    return "yes" if d >= p["move"] - EPS else ("no" if d <= -p["move"] + EPS else None)


@strat("S37", "F", "Thin move reversion scalp", BOTH, range(4, 11), {"move": 0.08, "vol_frac": 0.5, "min_prior": 3}, hold=3)
def s37(c, p):
    v = c.vol(c.js)
    prior = _prior_vols(c, 2, c.js - 1, p["min_prior"])
    if v is None or prior is None or v > p["vol_frac"] * mean(prior) + EPS:
        return None
    a, b = c.mid(c.js - 1), c.mid(c.js)
    if a is None or b is None or abs(b - a) < p["move"] - EPS:
        return None
    return side_of(a - b)


@strat("S38", "F", "Volume event underdog (L13 adjacent)", BOTH, [7], {"candles": 7, "pctl": 0.90, "prior_markets": 96, "min_prior": 48},
       band=UNDER, baseline="under")
def s38(c, p):
    V = sum(c.vol(j) or 0.0 for j in range(1, p["candles"] + 1))
    prior = [pm["V7"] for pm in c.prior(p["prior_markets"]) if pm["V7"] > 0]
    if V <= 0 or len(prior) < p["min_prior"]:
        return None
    return "under" if V >= percentile(prior, p["pctl"]) else None


@strat("S39", "F", "Opening burst lean", BOTH, [1], {"pctl": 0.90, "prior_markets": 96, "min_prior": 48, "lean": 0.05})
def s39(c, p):
    v1, m1 = c.vol(1), c.mid(1)
    prior = [pm["vol1"] for pm in c.prior(p["prior_markets"]) if pm["vol1"] is not None and pm["vol1"] > 0]
    if v1 is None or m1 is None or len(prior) < p["min_prior"] or v1 < percentile(prior, p["pctl"]) - EPS:
        return None
    return "yes" if m1 >= 0.5 + p["lean"] - EPS else ("no" if m1 <= 0.5 - p["lean"] + EPS else None)


# ---------------------------------------------------------------------------------------------------------------- G. strike relative

@strat("S40", "G", "Four hour channel extreme fade", BOTH, [1], {"previous_strikes": 15})
def s40(c, p):
    xs = c.strikes_back(p["previous_strikes"])
    if xs is None:
        return None
    x, prev = xs[-1], xs[:-1]
    return "no" if x > max(prev) else ("yes" if x < min(prev) else None)


@strat("S41", "G", "Efficiency ratio trend", BOTH, [1], {"steps": 8, "er": 0.6})
def s41(c, p):
    xs = c.strikes_back(p["steps"])
    if xs is None:
        return None
    path = sum(abs(xs[i + 1] - xs[i]) for i in range(len(xs) - 1))
    net = xs[-1] - xs[0]
    return side_of(net) if path > 0 and abs(net) / path >= p["er"] - EPS else None


@strat("S42", "G", "Common factor trend", BOTH, [1], {"steps": 4})
def s42(c, p):
    a = c.strikes_back(p["steps"])
    t = c.twin()
    b = t.strikes_back(p["steps"]) if t is not None else None
    if a is None or b is None:
        return None
    da, db = a[-1] - a[0], b[-1] - b[0]
    return side_of(da) if da != 0 and sgn(da) == sgn(db) else None


IDS = [s["id"] for s in SPECS]

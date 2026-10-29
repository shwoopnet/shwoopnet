"""XLEAD1 (worker FAM2, 2026-10-29): macro futures (ES=F, DX-Y.NYB, ^TNX) leading
the 15 minute Kalshi Bitcoin, Ethereum and gold quotes. Rule as registered in
kalshi-scalper/workers/FAM2_REGISTRATION.md. Usage:
  python -m scalper.xlead1 <yahoo_dir> [--holdout]
Without --holdout only W1 and W2 are scored."""
import json, math, sqlite3, sys, datetime as dt
from collections import defaultdict

DBS = ["data/book.sqlite", "data/fresh.sqlite", "data/five.sqlite"]
START = int(dt.datetime(2026, 10, 1, 14, tzinfo=dt.timezone.utc).timestamp())
W2_START = int(dt.datetime(2026, 10, 10, tzinfo=dt.timezone.utc).timestamp())
W3_START = int(dt.datetime(2026, 10, 19, tzinfo=dt.timezone.utc).timestamp())

TRIES = {
    "V1": (("KXBTC15M", "KXETH15M"), "es", +1, "hold"),
    "V2": (("KXBTC15M", "KXETH15M"), "es", +1, "exit3"),
    "V3": (("KXGOLD15M",), "dxy", -1, "hold"),
    "V4": (("KXGOLD15M",), "tnx", -1, "hold"),
}


def fee(c, p):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def window(close_ts):
    return "W1" if close_ts < W2_START else ("W2" if close_ts < W3_START else "W3")


def load_kalshi():
    markets, candles = {}, {}
    for db in DBS:
        c = sqlite3.connect(db)
        for t, s, o, cl, r, k, n in c.execute(
                "select * from market where series in ('KXBTC15M','KXETH15M','KXGOLD15M')"):
            if cl < START or r not in ("yes", "no"):
                continue
            markets[t] = (s, o, cl, r)
            candles[t] = {}
        for row in c.execute(
                "select ticker,end_ts,bid_c,ask_c,volume from candle where series in ('KXBTC15M','KXETH15M','KXGOLD15M')"):
            if row[0] in candles:
                candles[row[0]][row[1]] = row[2:]
    return markets, candles


def quote(cd):
    """(bid, ask) or None when the book is not two sided."""
    if cd is None:
        return None
    b, a, v = cd
    if b is None or a is None or b <= 0.001 or a >= 0.999 or a < b:
        return None
    return b, a


def load_bars(d, name):
    return {int(t): float(p) for t, p in json.load(open(f"{d}/{name}1m.json"))}


def shock(bars, D):
    """+1/-1/0, using only bars that started at or before D - 120 (ended by D - 60)."""
    a, b = bars.get(D - 120), bars.get(D - 300)
    if a is None or b is None or a <= 0 or b <= 0:
        return 0
    ch = []
    for s in range(D - 3660, D - 120 + 1, 60):
        x, y = bars.get(s - 60), bars.get(s)
        if x and y and x > 0 and y > 0:
            ch.append(math.log(y / x))
    if len(ch) < 45:
        return 0
    m = sum(ch) / len(ch)
    sd = math.sqrt(sum((x - m) ** 2 for x in ch) / (len(ch) - 1))
    if sd <= 0:
        return 0
    r3 = math.log(a / b)
    if abs(r3) >= 2.0 * sd * math.sqrt(3):
        return 1 if r3 > 0 else -1
    return 0


def side_px(q, side):
    b, a = q
    return (a, b) if side == "yes" else (1 - b, 1 - a)  # (ask, bid) of the side


def run(ydir, holdout):
    markets, candles = load_kalshi()
    bars = {k: load_bars(ydir, k) for k in ("es", "dxy", "tnx")}
    out = {}
    for name, (series, src, sign, mode) in TRIES.items():
        trades = []  # dicts
        for t, (s, o, C, r) in markets.items():
            if s not in series:
                continue
            w = window(C)
            if w == "W3" and not holdout:
                continue
            cd = candles[t]
            for D in range(C - 780, C - 240 + 1, 60):
                sh = shock(bars[src], D)
                if sh == 0:
                    continue
                side = "yes" if sh * sign > 0 else "no"
                rec = {"t": t, "w": w, "day": C // 86400, "side": side, "win": r == side}
                for tag, E in (("p", D), ("n", D + 60)):
                    q = quote(cd.get(E))
                    if q is None:
                        continue
                    ask, _ = side_px(q, side)
                    if not (0.10 <= ask <= 0.90):
                        continue
                    vol0 = (cd[E][2] or 0) == 0
                    exit_bid = None
                    if mode == "exit3" and tag == "p":
                        qx = quote(cd.get(E + 180))
                        if qx is not None and E + 180 <= C - 60:
                            exit_bid = side_px(qx, side)[1]
                    rec[tag] = (ask, vol0, exit_bid)
                trades.append(rec)
                break  # first shock minute only
        out[name] = trades
    return out


def pnl(entry, win, c, fx=1.0):
    ask, vol0, xb = entry
    cost = c * ask + fee(c, ask) * fx
    if xb is not None:
        return c * xb - fee(c, xb) * fx - cost
    return (c if win else 0) - cost


def stats(rows, c, fx=1.0):
    nets = [pnl(e, w, c, fx) for e, w, d in rows]
    g = sum(x for x in nets if x > 0); l = -sum(x for x in nets if x < 0)
    pf = g / l if l > 0 else float("inf")
    byday = defaultdict(float)
    for (e, w, d), x in zip(rows, nets):
        byday[d] += x
    v = list(byday.values()); n = len(v)
    z = 0.0
    if n > 1:
        m = sum(v) / n; sd = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1))
        z = m / (sd / math.sqrt(n)) if sd > 0 else 0.0
    mean = sum(nets) / len(nets) / c if nets else 0.0
    return pf, len(nets), mean * 100, z


def report(out, holdout):
    ws = ["W1", "W2"] + (["W3"] if holdout else [])
    lines = []
    for name, trades in out.items():
        lines.append(f"{name}: signals {len(trades)}")
        for w in ws:
            for tag, label in (("p", "fill at D"), ("n", "next candle")):
                rows = [(r[tag], r["win"], r["day"]) for r in trades if r["w"] == w and tag in r]
                rows0 = [x for x in rows if not x[0][1]]
                if not rows:
                    lines.append(f"  {w} {label}: n 0"); continue
                s1 = stats(rows, 1); s10 = stats(rows, 10); sx = stats(rows, 1, 1.2)
                s0 = stats(rows0, 1) if rows0 else (0, 0, 0, 0)
                held = sum(1 for x in rows if x[0][2] is None) if name == "V2" and tag == "p" else None
                lines.append(
                    f"  {w} {label}: n {s1[1]} days {len(set(x[2] for x in rows))} PF1 {s1[0]:.2f} PF10 {s10[0]:.2f} "
                    f"mean {s1[2]:+.2f}c z {s1[3]:+.2f} feex1.2 mean {sx[2]:+.2f}c | zero-vol dropped n {s0[1]} PF1 {s0[0]:.2f}"
                    + (f" | V2 held to settlement {held}" if held is not None else ""))
    return "\n".join(lines)


def lag_profile(ydir):
    markets, candles = load_kalshi()
    bars = {k: load_bars(ydir, k) for k in ("es", "dxy", "tnx")}
    res = []
    for src, series in (("es", ("KXBTC15M", "KXETH15M")), ("dxy", ("KXGOLD15M",)), ("tnx", ("KXGOLD15M",))):
        b = bars[src]
        for k in range(-2, 4):
            xs, ys = [], []
            for t, (s, o, C, r) in markets.items():
                if s not in series:
                    continue
                cd = candles[t]
                for st in range(o, C - 60, 60):
                    x0, x1 = b.get(st - 60), b.get(st)
                    if not x0 or not x1:
                        continue
                    E = st + 60 + 60 * k
                    q1, q0 = quote(cd.get(E)), quote(cd.get(E - 60))
                    if q1 is None or q0 is None:
                        continue
                    m1, m0 = sum(q1) / 2, sum(q0) / 2
                    if not (0.15 <= m0 <= 0.85):
                        continue
                    xs.append(math.log(x1 / x0)); ys.append(m1 - m0)
            n = len(xs)
            if n < 30:
                res.append(f"  {src} k={k:+d}: n {n}"); continue
            mx, my = sum(xs) / n, sum(ys) / n
            cov = sum((a - mx) * (b_ - my) for a, b_ in zip(xs, ys))
            vx = sum((a - mx) ** 2 for a in xs); vy = sum((b_ - my) ** 2 for b_ in ys)
            res.append(f"  {src} k={k:+d}: n {n} corr {cov / math.sqrt(vx * vy):+.3f}")
    return "\n".join(res)


if __name__ == "__main__":
    ydir = sys.argv[1]; ho = "--holdout" in sys.argv
    print(report(run(ydir, ho), ho))
    if "--lag" in sys.argv:
        print("Lag profile (information):"); print(lag_profile(ydir))

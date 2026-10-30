"""NEWH1: five new mechanisms on KXGOLD15M and KXBTC15M (research only).

Registration: workers/NEWH1_REGISTRATION.md (pushed before any scoring).
H1 BASIS (perp premium), H2 ROUND (round-number barrier), H3 STALE0 (frozen
zero-volume quote while spot moved), H4 GTIE (gold >= tie on a frozen feed),
H5 FLIPREV (reversal after a last-minute flip). Held to settlement, fill at the
next candle's closing ask, C = 10 screen.

Run: PYTHONPATH=src python -m scalper.newh1
"""
import csv
import io
import math
import sqlite3
import statistics
import zipfile
from collections import defaultdict
from datetime import datetime, timezone

from scalper.paths import DATA_DIR

FILES = ["l1b.sqlite", "book.sqlite", "fresh.sqlite"]
START = int(datetime(2026, 8, 6, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 9, 21, tzinfo=timezone.utc).timestamp())
END = int(datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp())


def day(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def load(series, start=START, end=END):
    """{close_ts: dict(ticker, close, result, strike, c={offset: (bid, ask, vol)})}."""
    win, owner = {}, {}
    for f in FILES:
        p = DATA_DIR / f
        if not p.exists():
            continue
        con = sqlite3.connect(p)
        for t, close, res, k in con.execute(
                "select ticker, close_ts, result, strike from market where series=? "
                "and close_ts>=? and close_ts<? and result in ('yes','no')",
                (series, start, end)):
            if close in win:
                continue
            win[close] = {"ticker": t, "close": close, "result": res, "strike": k, "c": {}}
            owner[t] = f
        bytk = {w["ticker"]: w for w in win.values()}
        for t, e, bid, ask, vol in con.execute(
                "select ticker, end_ts, bid_c, ask_c, volume from candle where series=?",
                (series,)):
            if owner.get(t) != f:
                continue
            w = bytk[t]
            w["c"][e - w["close"]] = (bid, ask, vol)
    return win


# ---------- Binance 1 minute closes: {minute end ts (s): close} ----------

def _read_zip(path, out):
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            with z.open(name) as fh:
                for row in csv.reader(io.TextIOWrapper(fh)):
                    if not row or not row[0].isdigit():
                        continue
                    ot = int(row[0])
                    ot = ot // 1000 if ot < 10 ** 14 else ot // 1000000
                    out[ot + 60] = float(row[4])


def binance(kind):
    """kind 'spot' or 'futures_um'; BTCUSDT closes keyed by kline end."""
    out = {}
    for d in (DATA_DIR / "binance", DATA_DIR / "newh1"):
        if not d.exists():
            continue
        for p in sorted(d.glob(f"{kind}_BTCUSDT-2026-*.zip")):
            _read_zip(p, out)
    return out


# ---------- money ----------

def fee(p, c=10, mult=1.0):
    return math.ceil(round(0.07 * c * p * (1 - p) * mult * 100, 9)) / 100


def net(fill, won, c=10, mult=1.0):
    return c * ((1.0 if won else 0.0) - fill) - fee(fill, c, mult)


def pf(nets):
    g = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return float("inf") if l == 0 else g / l


def side_ask(row, side):
    if row is None:
        return None
    bid, ask = row[0], row[1]
    a = ask if side == "yes" else (None if bid is None else round(1 - bid, 6))
    if a is None or not (0 < a < 1):
        return None
    return a


def mid(row):
    if row is None or row[0] is None or row[1] is None:
        return None
    return (row[0] + row[1]) / 2


def dayz(trades):
    d = defaultdict(float)
    for t in trades:
        d[t["day"]] += t["n10"]
    v = list(d.values())
    if len(v) < 3:
        return float("nan")
    sd = statistics.stdev(v)
    return statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else float("nan")


def make_trade(w, side, sig_off, lo, hi):
    """Fill at the candle after sig_off; None when no valid fill in band."""
    fr = w["c"].get(sig_off + 60)
    a = side_ask(fr, side)
    if a is None or not (lo <= a <= hi):
        return None
    won = w["result"] == side
    sa = side_ask(w["c"].get(sig_off), side)
    late = side_ask(w["c"].get(sig_off + 120), side) if sig_off + 120 < 0 else None
    return {"close": w["close"], "day": day(w["close"]), "side": side, "fill": a, "won": won,
            "vol0": (fr[2] or 0) == 0,
            "n1": net(a, won, 1), "n10": net(a, won, 10), "n10x": net(a, won, 10, 1.2),
            "sig": None if sa is None else net(sa, won, 10),
            "late": None if late is None else net(late, won, 10),
            "tie": None}


# ---------- the rules ----------

def rule_basis(win, spot, perp, reverse=False, T=600):
    out = []
    for w in win.values():
        t = w["close"] - T
        bs = []
        for k in range(1, 61):
            m = t - 60 * k
            if m in spot and m in perp:
                bs.append(math.log(perp[m] / spot[m]))
        if len(bs) < 50 or t not in spot or t not in perp:
            continue
        sd = statistics.pstdev(bs)
        if sd <= 0:
            continue
        z = (math.log(perp[t] / spot[t]) - statistics.mean(bs)) / sd
        if z >= 2:
            side = "yes"
        elif z <= -2:
            side = "no"
        else:
            continue
        if reverse:
            side = "no" if side == "yes" else "yes"
        tr = make_trade(w, side, -T, 0.10, 0.90)
        if tr:
            out.append(tr)
    return out


def rule_round(win, spot, R, control=False, T=600):
    out = []
    for w in win.values():
        t = w["close"] - T
        S, K = spot.get(t), w["strike"]
        if S is None or K is None:
            continue
        lo, hi = min(S, K), max(S, K)
        n = math.floor(hi / R) * R
        between = lo < n < hi
        if between == control:
            continue
        side = "yes" if S >= K else "no"
        tr = make_trade(w, side, -T, 0.55, 0.92)
        if tr:
            out.append(tr)
    return out


def rule_stale0(win, spot):
    out = []
    for w in win.values():
        for off in range(-780, -179, 60):
            r0, rp = w["c"].get(off), w["c"].get(off - 60)
            if r0 is None or rp is None or None in (r0[0], r0[1], rp[0], rp[1]):
                continue
            if (r0[2] or 0) != 0 or r0[0] != rp[0] or r0[1] != rp[1]:
                continue
            t = w["close"] + off
            if t not in spot or t - 60 not in spot:
                continue
            rets = []
            for k in range(1, 61):
                a, b = t - 60 * k, t - 60 * (k + 1)
                if a in spot and b in spot:
                    rets.append(math.log(spot[a] / spot[b]))
            if len(rets) < 50:
                continue
            s1 = statistics.pstdev(rets)
            r = math.log(spot[t] / spot[t - 60])
            if s1 <= 0 or abs(r) < 2 * s1:
                continue
            tr = make_trade(w, "yes" if r > 0 else "no", off, 0.10, 0.90)
            if tr:
                out.append(tr)
            break  # first qualifying minute only
    return out


def rule_gtie(win, tol):
    out = []
    for w in win.values():
        p = win.get(w["close"] - 900)
        if p is None or p["strike"] is None or w["strike"] is None:
            continue
        m = round(w["strike"] - p["strike"], 6)
        if abs(m) > tol + 1e-9:
            continue
        tr = make_trade(w, "yes", -840, 0.30, 0.70)
        if tr:
            nx = win.get(w["close"] + 900)
            tr["tie"] = None if nx is None or nx["strike"] is None else round(nx["strike"] - w["strike"], 6) == 0
            out.append(tr)
    return out


def rule_fliprev(win):
    out = []
    for w in win.values():
        p = win.get(w["close"] - 900)
        if p is None:
            continue
        m60 = mid(p["c"].get(-60))
        if m60 is None:
            continue
        res = 1.0 if p["result"] == "yes" else 0.0
        if abs(res - m60) < 0.6:
            continue
        side = "no" if res - m60 > 0 else "yes"
        tr = make_trade(w, side, -840, 0.30, 0.70)
        if tr:
            out.append(tr)
    return out


# ---------- report ----------

def summary(trs):
    if not trs:
        return {"n": 0}
    n10 = [t["n10"] for t in trs]
    s = {"n": len(trs), "days": len({t["day"] for t in trs}),
         "win": sum(t["won"] for t in trs) / len(trs),
         "fill": statistics.mean(t["fill"] for t in trs),
         "pf10": pf(n10), "pf1": pf([t["n1"] for t in trs]), "pfx": pf([t["n10x"] for t in trs]),
         "net10": sum(n10), "netx": sum(t["n10x"] for t in trs), "z": dayz(trs)}
    nz = [t for t in trs if not t["vol0"]]
    s["n_nz"], s["pf10_nz"] = len(nz), pf([t["n10"] for t in nz]) if nz else float("nan")
    sg = [t["sig"] for t in trs if t["sig"] is not None]
    s["pf_sig"] = pf(sg) if sg else float("nan")
    lt = [t["late"] for t in trs if t["late"] is not None]
    s["pf_late"], s["n_late"] = (pf(lt) if lt else float("nan")), len(lt)
    ties = [t["tie"] for t in trs if t["tie"] is not None]
    s["tie_share"] = (sum(ties) / len(ties)) if ties else None
    return s


def fmt(s):
    if s["n"] == 0:
        return "n 0"
    out = (f"n {s['n']:4d} days {s['days']:3d} win {s['win']:.3f} fill {s['fill']:.3f} "
           f"PF10 {s['pf10']:.2f} PF1 {s['pf1']:.2f} PFx1.2 {s['pfx']:.2f} net10 ${s['net10']:+.2f} "
           f"netx ${s['netx']:+.2f} z {s['z']:+.2f} | vol>0 n {s['n_nz']} PF10 {s['pf10_nz']:.2f} | "
           f"sigfill PF {s['pf_sig']:.2f} | late n {s['n_late']} PF {s['pf_late']:.2f}")
    if s["tie_share"] is not None:
        out += f" | settle=strike {s['tie_share']:.3f}"
    return out


def verdict(d, v):
    if d["n"] < 100:
        return "NOT_ENOUGH_DATA"
    if d["pf10"] < 1.5:
        return "FALSIFIED"
    if v["n"] < 50:
        return "NOT_ENOUGH_DATA"
    if v["pf10"] < 1.3 or v["netx"] <= 0:
        return "FALSIFIED"
    if v.get("pf_late", 0) < 1.0:
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED"


def split(trs):
    return ([t for t in trs if t["close"] < DISC_END], [t for t in trs if t["close"] >= DISC_END])


def main():
    btc, gold = load("KXBTC15M"), load("KXGOLD15M")
    spot, perp = binance("spot"), binance("futures_um")
    print(f"windows: BTC {len(btc)} gold {len(gold)}; spot minutes {len(spot)} perp minutes {len(perp)}")
    print(f"spot range {datetime.fromtimestamp(min(spot), timezone.utc)} to {datetime.fromtimestamp(max(spot), timezone.utc)}")
    for nm, ws in (("BTC", btc), ("gold", gold)):
        d = sum(1 for c in ws if c < DISC_END)
        print(f"  {nm}: discovery {d} validation {len(ws) - d}")
    rules = [
        ("BASIS_F", lambda: rule_basis(btc, spot, perp)),
        ("BASIS_R", lambda: rule_basis(btc, spot, perp, reverse=True)),
        ("ROUND500", lambda: rule_round(btc, spot, 500)),
        ("ROUND1000", lambda: rule_round(btc, spot, 1000)),
        ("STALE0", lambda: rule_stale0(btc, spot)),
        ("GTIE0", lambda: rule_gtie(gold, 0.0)),
        ("GTIE5", lambda: rule_gtie(gold, 0.05)),
        ("FLIPREV_GOLD", lambda: rule_fliprev(gold)),
        ("FLIPREV_BTC", lambda: rule_fliprev(btc)),
    ]
    controls = [
        ("ctrl ROUND500 (no level)", lambda: rule_round(btc, spot, 500, control=True)),
        ("ctrl ROUND1000 (no level)", lambda: rule_round(btc, spot, 1000, control=True)),
    ]
    stage = __import__("os").environ.get("NEWH1_STAGE", "disc")
    for nm, fn in rules + controls:
        d, v = split(fn())
        sd = summary(d)
        print(f"{nm:26s} DISC {fmt(sd)}")
        if stage == "val":
            sv = summary(v)
            print(f"{'':26s} VAL  {fmt(sv)}")
            if not nm.startswith("ctrl"):
                print(f"{'':26s} verdict {verdict(sd, sv) if sv['n'] else ('NOT_ENOUGH_DATA' if sd['n'] < 100 else verdict(sd, {'n': 0}))}")


if __name__ == "__main__":
    main()

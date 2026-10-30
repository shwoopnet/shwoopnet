"""NEWH6: three round-trip mechanisms on Kalshi's 15 minute gold and Bitcoin markets (research only).

Registration: workers/NEWH6_REGISTRATION.md (pushed before any scoring).
H1 STOPRUN (buy a former 85c+ favourite after its bid first breaks 30c, sell 2 minutes later), H2 CLOCKFLOW (F: front-run the
6 minute favourite wave, R: fade it), H3 OPENLEAN (fade the first quote's lean toward the previous window's leader).
Every trade is bought at the next candle's ask and sold at a bid inside the window; never held to settlement.

    PYTHONPATH=src python -m scalper.newh6 run        (the first run: STOPRUN, CLOCKFLOW; OPENLEAN scored zero entries)
    PYTHONPATH=src python -m scalper.newh6 openlean   (the amendment's one OPENLEAN re-read, first candle's closing quote)
"""
from __future__ import annotations

import sqlite3
import statistics
from collections import defaultdict

from .newh2 import START, DISC_END, END, day, fee, pf, dayz
from .paths import DATA_DIR

GOLD, BTC = "KXGOLD15M", "KXBTC15M"
FILES = {BTC: ("l1b", "book", "fresh"), GOLD: ("l1b", "book", "fresh", "five")}
LAST_SALE = -120


def load(series, start=START, end=END):
    """{close: {close, result, c: {offset: dict}}}; first file wins per close."""
    win = {}
    for name in FILES[series]:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        for tk, close, res in db.execute(
                "select ticker, close_ts, result from market where series=? and close_ts>=? and close_ts<?",
                (series, start, end)).fetchall():
            if close in win or res not in ("yes", "no"):
                continue
            cs = {}
            for e, bo, ao, bc, ac, v in db.execute(
                    "select end_ts, bid_o, ask_o, bid_c, ask_c, volume from candle where ticker=? "
                    "and bid_c is not null and ask_c is not null", (tk,)):
                cs[e - close] = {"bo": bo, "ao": ao, "b": bc, "a": ac, "v": v or 0.0}
            if cs:
                win[close] = {"ticker": tk, "close": close, "result": res, "c": cs}
    return win


# ---------- quotes for a side ----------

def ask(r, side):
    if r is None:
        return None
    a = r["a"] if side == "yes" else round(1 - r["b"], 6)
    return a if 0 < a < 1 else None


def bid(r, side):
    if r is None:
        return None
    return r["b"] if side == "yes" else round(1 - r["a"], 6)


def other(side):
    return "no" if side == "yes" else "yes"


def round_trip(w, side, fill_off, exit_off, lo, hi):
    """Buy `side` at the ask of candle fill_off; sell at the bid of exit_off (zero bid or missing: next candle, up to -120;
    still none: booked at 0). Returns a trade dict or None (no fill)."""
    c = w["c"]
    fr = c.get(fill_off)
    a = ask(fr, side)
    if a is None or not (lo - 1e-9 <= a <= hi + 1e-9):
        return None
    sale, sold_off, nosale = None, None, False
    off = exit_off
    while off <= LAST_SALE:
        b = bid(c.get(off), side)
        if b is not None and b > 0:
            sale, sold_off = b, off
            break
        off += 60
    if sale is None:
        sale, nosale = 0.0, True
    won = w["result"] == side
    t = {"close": w["close"], "day": day(w["close"]), "side": side, "fill": a, "sale": sale, "nosale": nosale, "won": won,
         "fill_off": fill_off, "sale_off": sold_off,
         "vol0": fr["v"] == 0 or (sold_off is not None and c[sold_off]["v"] == 0)}
    for key, cc, m in (("n1", 1, 1.0), ("n10", 10, 1.0), ("n10x", 10, 1.2)):
        t[key] = cc * (sale - a) - fee(a, cc, m) - (fee(sale, cc, m) if sale > 0 else 0.0)
    # information only: what holding to settlement would have given
    t["hold10"] = 10 * ((1.0 if won else 0.0) - a) - fee(a, 10)
    return t


# ---------- the rules (each: window -> trade or None; raise-free; gaps counted by caller via 'gap') ----------

def stoprun(w):
    c = w["c"]
    for s in range(-600, -299, 60):
        r, rp = c.get(s), c.get(s - 60)
        if r is None or rp is None:
            continue
        for side in ("yes", "no"):
            b, bp = bid(r, side), bid(rp, side)
            if not (0 < b <= 0.30 + 1e-9 and bp > 0.30 + 1e-9):
                continue
            peak = max((bid(c[o], side) for o in range(-840, s, 60) if o in c), default=0)
            if peak >= 0.85 - 1e-9:
                return round_trip(w, side, s + 60, s + 180, 0.05, 0.45), s
    return None, None


def clock_f(w):
    r = w["c"].get(-480)
    if r is None:
        return "gap"
    for side in ("yes", "no"):
        a = ask(r, side)
        if a is not None and 0.88 - 1e-9 <= a <= 0.95 + 1e-9:
            return round_trip(w, side, -420, -300, 0.88, 0.96)
    return None


def clock_r(w):
    r = w["c"].get(-300)
    if r is None:
        return "gap"
    for side in ("yes", "no"):
        a = ask(r, side)
        if a is not None and 0.88 - 1e-9 <= a <= 0.97 + 1e-9:
            return round_trip(w, other(side), -240, -180, 0.03, 0.15)
    return None


def prev_leader(prev):
    if prev is None:
        return None
    r = prev["c"].get(0) or prev["c"].get(-60)
    if r is None:
        return None
    m = (r["b"] + r["a"]) / 2
    if abs(m - 0.5) < 1e-9:
        return None
    return "yes" if m > 0.5 else "no"


def open_lean(w, prev, opening=False):
    """(lean toward the previous leader, leader) or None. opening=True is the registered first-second quote (bid_o, ask_o),
    which is an empty book in every window (NOT_RUNNABLE); the amendment uses the first candle's closing quote."""
    L = prev_leader(prev)
    r = w["c"].get(-840)
    if L is None or r is None:
        return None
    b, a = (r["bo"], r["ao"]) if opening else (r["b"], r["a"])
    if b is None or a is None or not (b > 0 and a < 1):
        return None
    m = (b + a) / 2
    return (m - 0.5 if L == "yes" else 0.5 - m), L


def openlean(w, prev, opening=False):
    ol = open_lean(w, prev, opening)
    if ol is None:
        return "gap"
    lean, L = ol
    if lean >= 0.05 - 1e-9:
        return round_trip(w, other(L), -780, -540, 0.20, 0.55)
    return None


# ---------- forward evaluator (one candidate per rule; source 'candles') ----------

def _fw_window(window):
    cs = {}
    for e, row in window["candles"].items():
        b, a, v = row[0], row[1], row[2]
        if b is None or a is None:
            continue
        cs[e - window["close_ts"]] = {"bo": None, "ao": None, "b": b, "a": a, "v": v or 0.0}
    return {"close": window["close_ts"], "result": window["result"], "c": cs}


def forward_eval(window, params):
    """STOPRUN, CLOCK_F, CLOCK_R on closing quotes (OPENLEAN needs opening quotes the forward source does not carry)."""
    from .fwdeval import NoData
    w = _fw_window(window)
    rule = params["rule"]
    if rule == "STOPRUN":
        t, _ = stoprun(w)
    elif rule == "CLOCK_F":
        t = clock_f(w)
    elif rule == "CLOCK_R":
        t = clock_r(w)
    else:
        raise NoData(f"rule {rule} not runnable on the candles source")
    if t == "gap":
        raise NoData("signal candle missing")
    if t is None:
        return None
    return {"side": t["side"], "entry": t["fill"], "exit": t["sale"], "t": window["close_ts"] + t["fill_off"],
            "zero_volume": t["vol0"], "note": "no sale, booked at 0" if t["nosale"] else ""}


# ---------- report ----------

def summ(tr):
    if not tr:
        return {"n": 0}
    nv = [t for t in tr if not t["vol0"]]
    return {"n": len(tr), "days": len({t["day"] for t in tr}), "fill": statistics.mean(t["fill"] for t in tr),
            "sale": statistics.mean(t["sale"] for t in tr), "up": sum(t["sale"] > t["fill"] for t in tr) / len(tr),
            "nosale": sum(t["nosale"] for t in tr), "pf10": pf([t["n10"] for t in tr]), "pf1": pf([t["n1"] for t in tr]),
            "pfx": pf([t["n10x"] for t in tr]), "net10": sum(t["n10"] for t in tr), "netx": sum(t["n10x"] for t in tr),
            "z": dayz(tr), "n_v": len(nv), "pf10_v": pf([t["n10"] for t in nv]) if nv else float("nan"),
            "pf_hold": pf([t["hold10"] for t in tr])}


def line(name, s):
    if not s["n"]:
        return f"{name:<16} n    0"
    return (f"{name:<16} n {s['n']:4d} days {s['days']:3d} fill {s['fill']:.3f} sale {s['sale']:.3f} up {s['up']:.3f} "
            f"nosale {s['nosale']:3d} PF10 {s['pf10']:.2f} PF1 {s['pf1']:.2f} PFx1.2 {s['pfx']:.2f} net10 {s['net10']:+8.2f} "
            f"netx {s['netx']:+8.2f} z {s['z']:+.2f} | vol>0 n {s['n_v']} PF10 {s['pf10_v']:.2f} | info hold PF {s['pf_hold']:.2f}")


def verdict(d, v):
    if d["n"] < 100:
        return "NOT_ENOUGH_DATA"
    if d["pf10"] < 1.5 or d["netx"] <= 0:
        return "FALSIFIED"
    if v["n"] < 50:
        return "NOT_ENOUGH_DATA"
    if v["pf10"] < 1.3 or v["netx"] <= 0:
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED"


def score(series, only=None, open_original=True):
    W = load(series)
    print(f"\n=== {series}: {len(W)} windows "
          f"({sum(c < DISC_END for c in W)} discovery, {sum(c >= DISC_END for c in W)} validation)")
    rules = {"STOPRUN": defaultdict(list), "CLOCK_F": defaultdict(list), "CLOCK_R": defaultdict(list),
             "OPENLEAN": defaultdict(list)}
    gaps = defaultdict(int)
    leans = defaultdict(list)
    for c, w in sorted(W.items()):
        part = "disc" if c < DISC_END else "val"
        t, _ = stoprun(w)
        if t:
            rules["STOPRUN"][part].append(t)
        for name, fn in (("CLOCK_F", clock_f), ("CLOCK_R", clock_r)):
            t = fn(w)
            if t == "gap":
                gaps[name, part] += 1
            elif t:
                rules[name][part].append(t)
        prev = W.get(c - 900)
        if open_original:
            gaps["OPENLEAN_ORIGINAL_runnable", part] += open_lean(w, prev, True) is not None
        ol = open_lean(w, prev)
        if ol:
            leans[part].append(ol[0])
        t = openlean(w, prev)
        if t == "gap":
            gaps["OPENLEAN", part] += 1
        elif t:
            rules["OPENLEAN"][part].append(t)
    for part in ("disc", "val"):
        v = leans[part]
        if v:
            print(f"descriptive {part}: opening lean toward the previous leader, n {len(v)}, mean {statistics.mean(v):+.4f}, "
                  f"share >= +0.05 {sum(x >= 0.05 - 1e-9 for x in v) / len(v):.3f}, share <= -0.05 "
                  f"{sum(x <= -0.05 + 1e-9 for x in v) / len(v):.3f}")
    out = {}
    if open_original:
        print(f"registered OPENLEAN (opening quote bid_o/ask_o) runnable windows: disc {gaps['OPENLEAN_ORIGINAL_runnable', 'disc']}, "
              f"val {gaps['OPENLEAN_ORIGINAL_runnable', 'val']} (NOT_RUNNABLE)")
    for name, parts in rules.items():
        if only and name not in only:
            continue
        d, v = summ(parts["disc"]), summ(parts["val"])
        vd = verdict(d, v)
        out[name] = (d, v, vd)
        print(f"-- {name} (gaps disc {gaps[name, 'disc']}, val {gaps[name, 'val']})")
        print("  disc " + line(name, d))
        print("  val  " + line(name, v))
        print(f"  verdict {vd}")
    return out


def run(only=None):
    res = {s: score(s, only) for s in (GOLD, BTC)}
    print("\nSummary:")
    for s, r in res.items():
        for name, (d, v, vd) in r.items():
            if only and name not in only:
                continue
            print(f"  {s:<10} {name:<9} disc n {d['n']:4d} PF10 {d.get('pf10', float('nan')):.2f} | "
                  f"val n {v['n']:4d} PF10 {v.get('pf10', float('nan')):.2f} | {vd}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run()
    elif len(sys.argv) > 1 and sys.argv[1] == "openlean":   # the amendment's one re-read (OPENLEAN only)
        run(only={"OPENLEAN"})
    else:
        print(__doc__)

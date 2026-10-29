"""EXIT1, REGIME1 and GOLD1D (README, pre-registrations of 2026-10-29): studies on L1's own entries. Research only.
Usage: python -m scalper.l1studies exit1 | regime1 | gold1d   (each once)
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict
from datetime import datetime, timezone

from .calibration import cluster_mean_z
from .paths import DATA_DIR

LEFT = 360


def fee(p, c=1, m=1.0):
    return math.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return w / l if l > 0 else (99.0 if w > 0 else 0.0)


def load(left=LEFT):
    from . import feat1 as F
    from .flat_r import load_rep
    from .fwd_reads import load_fresh
    from .hs1 import load as hl
    mk = {}
    for m in hl() + load_fresh() + load_rep():
        if m[1].endswith("15M") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), left)
    for r in rows:
        r["won"] = round(r["net"] + r["price"] + 0.07 * r["price"] * (1 - r["price"]))
        r["path"] = [(e, b, a) for e, b, a, *_ in mk[r["ticker"]][2] if r["close_ts"] - left < e <= r["close_ts"] - 60]
        r["entry_q"] = next(((b, a) for e, b, a, *_ in mk[r["ticker"]][2] if e == r["close_ts"] - left), None)
    closes = sorted({r["close_ts"] for r in rows})
    cut = (closes[len(closes) // 3], closes[2 * len(closes) // 3])
    for r in rows:
        r["win"] = 0 if r["close_ts"] < cut[0] else (1 if r["close_ts"] < cut[1] else 2)
    return rows


def side_bid(r, q):
    return q[1] if r["side"] == "yes" else round(1 - q[2], 4)


def hold(r, c=1):
    return r["won"] - r["price"] - fee(r["price"], c)


def line_exit(r, line, c=1, frac=1.0):
    for e, b, a in r["path"]:
        sb = b if r["side"] == "yes" else round(1 - a, 4)
        if sb <= line + 1e-9:
            sold = frac * (sb - fee(sb, c) if sb > 0 else 0.0) + (1 - frac) * r["won"]
            return sold - r["price"] - fee(r["price"], c)
    return hold(r, c)


def drop_exit(r, x, c=1):
    return line_exit(r, r["price"] - x, c)


def time_exit(r, c=1):
    if not r["path"]:
        return hold(r, c)
    e, b, a = r["path"][-1]
    sb = b if r["side"] == "yes" else round(1 - a, 4)
    if sb < r["price"]:
        return (sb - fee(sb, c) if sb > 0 else 0.0) - r["price"] - fee(r["price"], c)
    return hold(r, c)


def table(rows, fn, label):
    out = []
    for w in range(3):
        v = [fn(r) for r in rows if r["win"] == w]
        out.append(f"{['disc', 'valid', 'HOLD'][w]} PF {pf(v):.3f} n={len(v)} mean {100 * sum(v) / max(len(v), 1):+.2f}c")
    return f"  {label:22s} " + " | ".join(out)


def exit1():
    p = DATA_DIR / "exit1_result.txt"
    if p.exists():
        print("Refusing to run again"); return
    rows = load()
    lines = [f"EXIT1: {len(rows)} L1 entries (6 minute look, 88c to 97c), windows by close-date thirds; PF per contract at 1 contract (10 contracts in brackets for hold)"]
    rules = [("hold to settlement", hold), ("live 25c line", lambda r: line_exit(r, 0.25)), ("DROP10", lambda r: drop_exit(r, 0.10)), ("DROP20", lambda r: drop_exit(r, 0.20)),
             ("HALF25", lambda r: line_exit(r, 0.25, frac=0.5)), ("TIME1", time_exit), ("hold, 10 contracts", lambda r: hold(r, 10))]
    for name, fn in rules:
        lines.append(table(rows, fn, name))
    passes = [n for n, fn in rules[2:6] if all(pf([fn(r) for r in rows if r["win"] == w]) >= 1.5 for w in range(3))]
    lines.insert(0, "EXIT1 VERDICT: " + ("NOT_YET_FALSIFIED " + str(passes) if passes else "FALSIFIED (no new exit shape reaches PF 1.5 in every window)"))
    p.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


def regime1():
    p = DATA_DIR / "regime1_result.txt"
    if p.exists():
        print("Refusing to run again"); return
    rows = load()
    by_series = defaultdict(list)
    for r in sorted(rows, key=lambda r: r["close_ts"]):
        by_series[r["series"]].append(r)
    # (d) recent volatility: mean absolute YES-mid move of the series' previous 4 windows, from the entry candles we hold
    vol = {}
    for s, rs in by_series.items():
        mids = {r["close_ts"]: ((r["entry_q"][0] + r["entry_q"][1]) / 2 if r["entry_q"] else None) for r in rs}
        ks = sorted(mids)
        for i, k in enumerate(ks):
            prev = [mids[x] for x in ks[max(0, i - 4):i] if mids[x] is not None]
            vol[(s, k)] = sum(abs(prev[j] - prev[j - 1]) for j in range(1, len(prev))) / max(len(prev) - 1, 1) if len(prev) > 1 else None
    disc_vols = sorted(v for (s, k), v in vol.items() if v is not None and any(r["close_ts"] == k and r["win"] == 0 for r in by_series[s][:1]) or False)
    allv = sorted(v for v in vol.values() if v is not None)
    d80 = allv[int(0.8 * len(allv))] if allv else 1.0
    lastloss = {}
    flags = {}
    for s, rs in by_series.items():
        last = None
        for r in rs:
            flags[id(r)] = last is not None and r["close_ts"] - last <= 7200
            if r["won"] == 0:
                last = r["close_ts"]
    F = {"(a) 22-02 UTC": lambda r: datetime.fromtimestamp(r["close_ts"], timezone.utc).hour in (22, 23, 0, 1),
         "(b) weekend": lambda r: datetime.fromtimestamp(r["close_ts"], timezone.utc).weekday() >= 5,
         "(c) spread >= 2c": lambda r: r["entry_q"] is not None and r["entry_q"][1] - r["entry_q"][0] >= 0.02 - 1e-9,
         "(d) high recent vol": lambda r: (vol.get((r["series"], r["close_ts"])) or 0) > d80,
         "(e) loss in series < 2h": lambda r: flags[id(r)]}
    lines = [f"REGIME1: {len(rows)} entries; stand-down filters, kept vs removed; (d) threshold {d80:.4f}"]
    verdicts = []
    for name, fn in F.items():
        parts, ok = [], True
        for w in range(3):
            kept = [hold(r) for r in rows if r["win"] == w and not fn(r)]; rem = [hold(r) for r in rows if r["win"] == w and fn(r)]
            ks = [r["won"] - r["price"] - fee(r["price"], m=1.2) for r in rows if r["win"] == w and not fn(r)]
            nc = len({r["close_ts"] for r in rows if r["win"] == w and not fn(r)})
            parts.append(f"{['disc', 'valid', 'HOLD'][w]} kept PF {pf(kept):.3f} n={len(kept)} | removed PF {pf(rem):.3f} n={len(rem)} net {100 * sum(rem) / max(len(rem), 1):+.2f}c")
            ok = ok and pf(kept) >= 1.5 and pf(ks) >= 1.2 and nc >= 30
        verdicts.append(f"{name} {'NOT_YET_FALSIFIED' if ok else 'FALSIFIED'}")
        lines.append(f"  {name}: " + " || ".join(parts))
    lines.insert(0, "REGIME1 VERDICTS: " + "; ".join(verdicts))
    p.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


def gold1d():
    p = DATA_DIR / "gold1d_result.txt"
    if p.exists():
        print("Refusing to run again"); return
    lines = ["GOLD1D: gold's L1 entries in the history"]
    res = {}
    for left in (600, 360):
        rows = [r for r in load(left) if r["series"] == "KXGOLD15M"]
        days = sorted({r["day"] for r in rows}); half = days[len(days) // 2]
        h1 = [hold(r) for r in rows if r["day"] < half]; h2 = [hold(r) for r in rows if r["day"] >= half]
        weeks = defaultdict(list)
        for r in rows:
            weeks[datetime.fromtimestamp(r["close_ts"], timezone.utc).strftime("%G-W%V")].append(hold(r))
        wk = {k: pf(v) for k, v in weeks.items() if len(v) >= 10}
        sizes = " / ".join(f"{pf([hold(r, c) for r in rows]):.2f}" for c in (1, 3, 5, 10))
        silver = [r for r in load(left) if r["series"] == "KXSILVER15M"]
        res[left] = (pf(h1), pf(h2), sum(1 for v in wk.values() if v >= 1.5) / max(len(wk), 1))
        lines.append(f"  look {left // 60} min: gold PF {pf([hold(r) for r in rows]):.2f} n={len(rows)} days {len(days)}; halves {pf(h1):.2f} / {pf(h2):.2f}; "
                     f"weeks with 10+ entries {len(wk)}, PF >= 1.5 in {sum(1 for v in wk.values() if v >= 1.5)} ({', '.join(f'{k} {v:.2f}' for k, v in sorted(wk.items()))}); "
                     f"size steps 1/3/5/10 PF {sizes}; silver PF {pf([hold(r) for r in silver]):.2f} n={len(silver)}")
    ok = all(a >= 1.5 and b >= 1.5 and c >= 0.75 for a, b, c in res.values())
    lines.insert(0, "GOLD1D: history stability claim " + ("HOLDS" if ok else "FAILS") + " on the 1.5 bar (both looks, both halves, 75% of weeks); live record and the daily ladder are added from the export and LADL1 when available")
    p.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"exit1": exit1, "regime1": regime1, "gold1d": gold1d}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()

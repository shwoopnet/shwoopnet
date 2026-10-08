"""P2: would a resting buy one tick below the touch beat crossing, for L1 signals? (rules in the README, "Pre-registration: L1 in the
90c to 95c band, and resting-limit entries" and its amendment, fixed before this file existed.)

Reads data/ob.sqlite (scalper.recorder, top five levels every ~10 s). For each market that closed after START the L1 signal is the FIRST
snapshot 330 to 400 seconds before close in which a side's ask is 0.90 to 0.97. Taker: buy at that ask. Resting: a buy limit one tick below it,
filled only by a LATER snapshot, still inside the window, whose own side's ask is STRICTLY below the limit (the sell side traded through our price,
so whatever queued ahead of us was eaten; a print AT our price is not counted, as in H3, which understates fills, and the report says so).
The maker fee is set EQUAL to the taker fee for the verdict; lower rates are printed as information only and can never create a pass.

Unfilled signals count as zero for the maker and are always reported next to the filled ones: a profit that rises while the fill rate
collapses is selection, not execution. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.bookmaker   (after python -m scalper.recorder and python -m scalper.backfill 1 for the results)
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timezone

from .calibration import cluster_mean_z
from .paths import DATA_DIR, DB
from .scalps import FEE_RATE, MIN_N, STRESS, Z_BAR

OB = DATA_DIR / "ob.sqlite"
START = 1791428400            # 2026-10-08 03:00:00 UTC: only markets closing after this are used
BAND = (0.90, 0.97)
WINDOW = (330, 400)           # seconds before close
MIN_DAYS = 5
INFO_COEFFS = (0.0, 0.0175)


def fee(p: float, mult: float = 1.0) -> float:
    return FEE_RATE * mult * p * (1 - p)


def tick(price: float) -> float:
    """One tick below a touch: 0.1c above 90c, 1c at or below it."""
    return 0.001 if price > 0.90 + 1e-9 else 0.01


def simulate(snaps: list[dict], close_ts: float, res: str) -> dict | None:
    """One market. snaps: dicts with ts, yes_ask, no_ask (None for an empty side). Returns None if there is no signal."""
    win = sorted((s for s in snaps if close_ts - WINDOW[1] <= s["ts"] <= close_ts - WINDOW[0]), key=lambda s: s["ts"])
    sig = None
    for i, s in enumerate(win):
        for side, ask in (("yes", s["yes_ask"]), ("no", s["no_ask"])):
            if ask is not None and BAND[0] - 1e-9 <= ask <= BAND[1] + 1e-9:
                sig = (i, side, round(ask, 4))
                break
        if sig:
            break
    if sig is None:
        return None
    i, side, ask = sig
    limit = round(ask - tick(ask), 4)
    key = "yes_ask" if side == "yes" else "no_ask"
    fill_strict = any(s[key] is not None and s[key] < limit - 1e-9 for s in win[i + 1:])
    fill_at = any(s[key] is not None and s[key] <= limit + 1e-9 for s in win[i + 1:])
    won = 1.0 if res == side else 0.0
    return {"side": side, "ask": ask, "limit": limit, "filled": fill_strict, "filled_at": fill_at, "won": won,
            "t": win[i]["ts"], "day": datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d"), "close": close_ts}


def taker(o: dict, mult: float = 1.0) -> float:
    return o["won"] - o["ask"] - fee(o["ask"], mult)


def maker(o: dict, mult: float = 1.0, coeff: float | None = None, flag: str = "filled") -> float:
    """Net for the resting order, unfilled counted as zero. The fee defaults to the taker formula (the verdict's assumption)."""
    if not o[flag]:
        return 0.0
    f = fee(o["limit"], mult) if coeff is None else coeff * mult * o["limit"] * (1 - o["limit"])
    return o["won"] - o["limit"] - f


def verdict(sigs: list[dict]) -> tuple[str, dict]:
    n, days = len(sigs), len({o["day"] for o in sigs})
    info = {"n": n, "days": days}
    if n:
        fl = [o for o in sigs if o["filled"]]
        mi = [o for o in sigs if not o["filled"]]
        info.update(fill_rate=len(fl) / n, filled_n=len(fl),
                    filled_maker=sum(maker(o) for o in fl) / len(fl) if fl else None,
                    filled_taker=sum(taker(o) for o in fl) / len(fl) if fl else None,
                    missed_taker=sum(taker(o) for o in mi) / len(mi) if mi else None,
                    taker_all=sum(taker(o) for o in sigs) / n, maker_per_signal=sum(maker(o) for o in sigs) / n)
        info["fill_rate_at"] = sum(1 for o in sigs if o["filled_at"]) / n
        for c in INFO_COEFFS:
            info[f"maker_per_signal_fee{c}"] = sum(maker(o, coeff=c) for o in sigs) / n
    if n < MIN_N or days < MIN_DAYS:
        return "NOT_ENOUGH_DATA", info
    diff = [(o["day"], maker(o) - taker(o)) for o in sigs]
    mean, _, z = cluster_mean_z(diff)
    ordered = sorted(sigs, key=lambda o: o["close"])
    h = len(ordered) // 2
    halves = [sum(maker(o) - taker(o) for o in part) / len(part) for part in (ordered[:h], ordered[h:])]
    stress = sum(maker(o, STRESS) - taker(o, STRESS) for o in sigs) / n
    info.update(diff=mean, z=z, halves=halves, stress=stress)
    ok = mean > 0 and z >= Z_BAR and all(x > 0 for x in halves) and stress > 0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), info


def load(ob_path=OB, db_path=DB, start: float = START) -> list[dict]:
    results = {t: (c, r) for t, c, r in sqlite3.connect(db_path).execute("SELECT ticker, close_ts, result FROM market")}
    by: dict = defaultdict(list)
    close_iso: dict = {}
    for ts, ticker, close, ya, na in sqlite3.connect(ob_path).execute("SELECT ts, ticker, close_ts, yes_ask, no_ask FROM ob"):
        by[ticker].append({"ts": ts, "yes_ask": ya, "no_ask": na})
        close_iso[ticker] = close
    sigs = []
    for ticker, snaps in by.items():
        if ticker not in results or results[ticker][1] not in ("yes", "no"):
            continue
        close_ts = results[ticker][0]
        if close_ts <= start:
            continue
        o = simulate(snaps, close_ts, results[ticker][1])
        if o:
            sigs.append(o)
    return sigs


def main() -> None:
    sigs = load()
    v, i = verdict(sigs)
    print(f"{i['n']} signals on {i['days']} day(s) (markets closing after {START}); verdict: {v}")
    if i["n"]:
        f = lambda x: "n/a" if x is None else f"{x * 100:+.2f}c"
        print(f"fill rate {i['fill_rate'] * 100:.1f}% (strictly through; counting a touch as a fill: {i['fill_rate_at'] * 100:.1f}%), filled {i['filled_n']}")
        print(f"filled: maker {f(i['filled_maker'])} vs the same signals taken {f(i['filled_taker'])}; missed signals, taken: {f(i['missed_taker'])}")
        print(f"per signal (unfilled = 0): maker {f(i['maker_per_signal'])}, taker {f(i['taker_all'])}")
        print("information only, lower maker fees: " + ", ".join(f"coefficient {c}: {f(i[f'maker_per_signal_fee{c}'])}" for c in INFO_COEFFS))
        if "diff" in i:
            print(f"maker minus taker per signal {f(i['diff'])}, z {i['z']:+.2f}, halves {f(i['halves'][0])} / {f(i['halves'][1])}, fees x{STRESS} {f(i['stress'])}")
    print("NOT_ENOUGH_DATA means the numbers above are information only." if v == "NOT_ENOUGH_DATA" else "No verdict here means trade.")


if __name__ == "__main__":
    main()

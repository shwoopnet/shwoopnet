"""Recorder analysis, INFORMATION ONLY (no claim, no verdict, no try): how fast do Kalshi quotes follow the spot index in the last minute, how deep is the book where the favourite is, and how much of the day does the recorder catch.
Complements RECORD1 (the registered claim, scalper/record1.py). Usage: python -m scalper.record_info
"""
from __future__ import annotations

import statistics as st
import subprocess
import sys
from collections import defaultdict

from . import record1 as R
from .paths import DATA_DIR

JUMP_BP, JUMP_SPAN_S, FOLLOW_C, MAX_WAIT_S = 3.0, 5, 0.01, 20


def jumps(idx: dict[int, float], lo: int, hi: int) -> list[tuple[int, float]]:
    """(second, signed bp change) of non-overlapping index moves of at least JUMP_BP over JUMP_SPAN_S seconds inside [lo, hi]."""
    out, t = [], lo
    while t + JUMP_SPAN_S <= hi:
        a, b = idx.get(t), idx.get(t + JUMP_SPAN_S)
        if a and b and abs(b / a - 1) * 1e4 >= JUMP_BP:
            out.append((t + JUMP_SPAN_S, (b / a - 1) * 1e4))
            t += JUMP_SPAN_S
        else:
            t += 1
    return out


def follow_delay(polls: list[dict], t_sec: int, direction: int):
    """Seconds from t_sec until the quote mid has moved by at least FOLLOW_C in `direction` relative to its value at t_sec, else None (not within MAX_WAIT_S)."""
    base = next((q for q in polls if q["t"] >= t_sec * 1000), None)
    if base is None:
        return None
    m0 = (base["bid"] + base["ask"]) / 2
    for q in polls:
        if q["t"] <= base["t"]:
            continue
        if q["t"] > (t_sec + MAX_WAIT_S) * 1000:
            return None
        if direction * ((q["bid"] + q["ask"]) / 2 - m0) >= FOLLOW_C:
            return (q["t"] - base["t"]) / 1000
    return None


DIP_C, DIP_LOOK_S, REBOUND_S = 0.03, 2.0, 3.0


def dips(polls: list[dict], fav_yes: bool) -> list[int]:
    """Poll times (ms) at which the favourite side's ask is at least DIP_C below its highest value in the previous DIP_LOOK_S seconds AND rebounds by at least half the dip within REBOUND_S seconds (a dip and a bounce)."""
    ask = [(q["t"], q["ask"] if fav_yes else 1 - q["bid"]) for q in polls]
    out, last = [], -10 ** 12
    for i, (t, a) in enumerate(ask):
        prior = [x for tt, x in ask[:i] if t - tt <= DIP_LOOK_S * 1000]
        if not prior or t - last < REBOUND_S * 1000:
            continue
        drop = max(prior) - a
        if drop >= DIP_C and any(x >= a + drop / 2 for tt, x in ask[i + 1:] if tt - t <= REBOUND_S * 1000):
            out.append(t)
            last = t
    return out


def analyse(allr: dict[str, dict[str, list[dict]]]) -> list[str]:
    delays, events, sizes, cover = [], 0, defaultdict(list), []
    for f, run in allr.items():
        by_t = defaultdict(list)
        for r in run["quotes"]:
            if r["status"] == "active" and r["yes_bid"] and r["yes_ask"]:
                by_t[r["ticker"]].append({"t": int(r["t_recv_ms"]), "bid": float(r["yes_bid"]), "ask": float(r["yes_ask"]), "bid_size": float(r["bid_size"] or 0), "ask_size": float(r["ask_size"] or 0)})
        idxs = {a: R.index_by_second(run["spot"], a) for a in set(R.ASSET.values())}
        for res in run["results"]:
            tk = res["ticker"]
            asset = R.ASSET.get(tk.split("-")[0])
            polls = sorted(by_t.get(tk, []), key=lambda q: q["t"])
            if not polls or asset is None:
                continue
            from datetime import datetime, timezone
            close_s = int(datetime.strptime(res["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
            for t_sec, bp in jumps(idxs[asset], close_s - 150, close_s - 5):
                events += 1
                d = follow_delay(polls, t_sec, 1 if bp > 0 else -1)
                delays.append(d)
            for s in R.SECONDS:
                q = next((p for p in polls if p["t"] >= (close_s - s) * 1000), None)
                if q:
                    fav_ask = q["ask"] if q["ask"] >= 0.5 or q["bid"] >= 0.5 else None
                    sizes[s].append(q["ask_size"] if (q["bid"] + q["ask"]) / 2 >= 0.5 else q["bid_size"])
        cover.append((f, len(run["results"]), sum(int(c["polls"]) for c in run["coverage"]), sum(int(c["n429"]) for c in run["coverage"])))
    dip_win, nodip_win = [], []
    for f, run in allr.items():
        by_t2 = defaultdict(list)
        for r in run["quotes"]:
            if r["status"] == "active" and r["yes_bid"] and r["yes_ask"]:
                by_t2[r["ticker"]].append({"t": int(r["t_recv_ms"]), "bid": float(r["yes_bid"]), "ask": float(r["yes_ask"])})
        for res in run["results"]:
            polls = sorted(by_t2.get(res["ticker"], []), key=lambda q: q["t"])
            if len(polls) < 20 or res["result"] not in ("yes", "no"):
                continue
            first = polls[0]
            fav_yes = (first["bid"] + first["ask"]) / 2 >= 0.5
            fav_ask = first["ask"] if fav_yes else 1 - first["bid"]
            if not 0.88 <= fav_ask <= 0.97:
                continue
            fav_won = (res["result"] == "yes") == fav_yes
            (dip_win if dips(polls, fav_yes) else nodip_win).append(fav_won)
    out = [f"recorder runs: {len(allr)}; windows x markets recorded: {sum(c[1] for c in cover)}; polls {sum(c[2] for c in cover)}; refused (429) {sum(c[3] for c in cover)}"]
    got = [d for d in delays if d is not None]
    out.append(f"index moves of at least {JUMP_BP:g} bp within {JUMP_SPAN_S} s in the last 150 s: {events}; quote mid followed by {FOLLOW_C * 100:g}c within {MAX_WAIT_S} s in {len(got)}"
               + (f"; delay median {st.median(got):.1f} s, 90th percentile {sorted(got)[int(0.9 * (len(got) - 1))]:.1f} s" if got else ""))
    for s in R.SECONDS:
        v = sizes.get(s, [])
        if v:
            out.append(f"favourite-side size at {s} s left: n={len(v)}, median {st.median(v):.0f}, share >= 5: {100 * sum(1 for x in v if x >= 5) / len(v):.0f}%, share >= 20: {100 * sum(1 for x in v if x >= 20) / len(v):.0f}%")
    if dip_win or nodip_win:
        fmt = lambda v: f"{len(v)} windows, favourite lost {sum(1 for w in v if not w)}" + (f" ({100 * sum(1 for w in v if not w) / len(v):.0f}%)" if v else "")
        out.append(f"favourites starting the last 150 s at 0.88 to 0.97: with a dip-and-bounce of {DIP_C * 100:g}c or more: {fmt(dip_win)}; without: {fmt(nodip_win)}")
    return out


def main() -> None:
    subprocess.run(["git", "fetch", "-q", "origin", "quote-data"], check=False)
    out = analyse(R.runs())
    (DATA_DIR / "record_info.txt").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()

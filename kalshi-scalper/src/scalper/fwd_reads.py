"""The forward reads on fresh public candles, written BEFORE any fresh-day result was looked at: FWD7 (pooled 10 minute entry, with its YES-over-NO secondary claim),
JUMP1, JUMP1b, TIB1, DIP1, FWD10 (crowded windows) and the three ML1 claims. Each follows its README registration exactly. Research only. Verdict words:
FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.fwd_reads look     an INFORMATION look at whatever fresh days exist (labelled as such; decides nothing; may be repeated)
       python -m scalper.fwd_reads read     the REGISTERED read; refused until 30 fresh days exist or the date is 2026-12-01 or later, and refused a second time
                                            unless data/fwd_reads_result.txt is deleted on purpose (a crash fix only, logged in the README)
Fresh days are markets closing from 2026-10-13 00:00 UTC in data/fresh.sqlite (scalper.backfill range downloads). Pairing note for the 10 minute against 6 minute and ML1
comparisons: each arm is taken from its OWN entries and compared per day (day-clustered), never restricted to markets that qualify under both (that restriction
conditions on the future, the flaw found in EL1 and HS1).
"""
from __future__ import annotations

import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from . import lstrats as L
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalps import STRESS

# ---- fixed in the README before any fresh day was read ----
FRESH_DB, RESULT = DATA_DIR / "fresh.sqlite", DATA_DIR / "fwd_reads_result.txt"
START_TS = int(datetime(2026, 10, 13, tzinfo=timezone.utc).timestamp())
READ_DATE_TS = int(datetime(2026, 12, 1, tzinfo=timezone.utc).timestamp())
MIN_DAYS_READ = 30
FWD7_Z, FWD7_DIFF_Z, FWD7_MIN_N, FWD7_MIN_DAYS, FWD7_MIN_SERIES_POS, SIDE_Z, SIDE_MIN = 2.4, 2.0, 1500, 20, 10, 2.4, 200
CUT_Z, CUT_MIN = 2.4, 200
JUMP_CUT, JUMP_CUT_B, TIB_HI, TIB_LO, DIP_CUT = 0.05, 0.20, 4, 1, 0.60
LIVE6 = ("KXBTC15M", "KXGOLD15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXNATGAS15M")
FWD10_SERIES, FWD10_Z, FWD10_MIN_ALONE, FWD10_MIN_DAYS = ("KXBTC15M", "KXNATGAS15M", "KXDOGE15M"), 2.4, 60, 20
ML1 = {"KXGOLD15M": 420, "KXBTC15M": 600, "KXETH15M": 540}          # seconds before the close, against the 360 second rule
ML1_Z, ML1_MIN_DAYS = 2.4, 25
POOL18 = ["KXBNB15M", "KXBTC15M", "KXCOPPER15M", "KXDOGE15M", "KXETH15M", "KXEURUSD15M", "KXGBPUSD15M", "KXGOLD15M", "KXHYPE15M", "KXNATGAS15M", "KXNEAR15M",
          "KXPALLADIUM15M", "KXPLATINUM15M", "KXSILVER15M", "KXUSDJPY15M", "KXWTI15M", "KXXRP15M", "KXZEC15M"]


def load_fresh(path=FRESH_DB, series=POOL18, start_ts=START_TS) -> list[tuple]:
    db = sqlite3.connect(path)
    by: dict = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
    for s, tk, end, bc, ac, close_ts, res in db.execute(
            "SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, m.close_ts, m.result FROM candle c JOIN market m ON m.ticker = c.ticker WHERE m.close_ts >= ? ORDER BY c.ticker, c.end_ts", (start_ts,)):
        if s not in series or bc is None or ac is None:
            continue
        m = by[tk]
        m["c"].append((end, bc, ac, bc, ac)); m["close"] = close_ts; m["res"] = res; m["s"] = s
    return [(tk, m["s"], m["c"], m["close"], m["res"]) for tk, m in by.items()]


def entries(markets: list[tuple], left_s: int) -> list[dict]:
    return L.hold_rule(markets, left_s, L.L1["band"])


def features(markets: list[tuple], ents: list[dict], left_s: int) -> list[dict]:
    """Adds tib, dip and rise (the held side's 3 minute change of mid) to each entry, from candles up to the decision candle only. Entries without the needed candles are dropped."""
    idx = {m[0]: m[2] for m in markets}
    out = []
    for e in ents:
        c = idx[e["ticker"]]
        t, side = e["close_ts"] - left_s, e["side"]
        byt = {x[0]: x for x in c}
        now, p3 = byt.get(t), byt.get(t - 180)
        if now is None or p3 is None:
            continue
        ask = lambda x: x[2] if side == "yes" else 1 - x[1]
        mid = lambda x: (x[1] + x[2]) / 2 if side == "yes" else 1 - (x[1] + x[2]) / 2
        tib, k = 0, t - 60
        while k in byt and ask(byt[k]) >= 0.88:
            tib += 1
            k -= 60
        earlier = [mid(x) for x in c if x[0] < t]
        if not earlier:
            continue
        out.append({**e, "tib": tib, "dip": min(earlier), "rise": mid(now) - mid(p3)})
    return out


def fresh_days(markets: list[tuple]) -> int:
    return len({datetime.fromtimestamp(m[3], timezone.utc).strftime("%Y-%m-%d") for m in markets})


def diff(a: list[dict], b: list[dict]):
    """Each group from its own entries, per day difference of means, day clustered: (mean, z, days)."""
    d = defaultdict(lambda: [[], []])
    for e in a:
        d[e["day"]][0].append(e["net"])
    for e in b:
        d[e["day"]][1].append(e["net"])
    rows = [(k, st.mean(v[0]) - st.mean(v[1])) for k, v in d.items() if v[0] and v[1]]
    if len(rows) < 2:
        return 0.0, 0.0, len(rows)
    m, _, z = cluster_mean_z(rows)
    return m, z, len(rows)


def own(es: list[dict]):
    return cluster_mean_z([(e["day"], e["net"]) for e in es]) if len(es) > 1 else (0.0, 0.0, 0.0)


def halves_positive(es: list[dict], key="net") -> bool:
    o = sorted(es, key=lambda e: e["close_ts"])
    h = len(o) // 2
    return bool(o) and st.mean(e[key] for e in o[:h]) > 0 and st.mean(e[key] for e in o[h:]) > 0


def claim(label: str, hi: list[dict], lo: list[dict], z_bar: float, min_hi: int, min_lo: int, hi_name: str, lo_name: str):
    """hi minus lo, own entries per day, day-clustered z; hi group above zero by itself. Returns (text, verdict)."""
    if len(hi) < min_hi or len(lo) < min_lo:
        return f"{label}: NOT_ENOUGH_DATA ({hi_name} {len(hi)}, {lo_name} {len(lo)})", "NOT_ENOUGH_DATA"
    hm, _, hz = own(hi)
    lm, _, _ = own(lo)
    dm, dz, nd = diff(hi, lo)
    v = "NOT_YET_FALSIFIED" if (dm > 0 and dz >= z_bar and hm > 0) else "FALSIFIED"
    c = lambda x: f"{x * 100:+.2f}c"
    return (f"{label}: {hi_name} n={len(hi)} at {c(hm)} (z {hz:+.2f}); {lo_name} n={len(lo)} at {c(lm)}; difference per day {c(dm)} (day clustered z {dz:+.2f}, {nd} days); VERDICT: {v}"), v


def fwd7(markets: list[tuple]):
    lines = []
    e10 = entries(markets, 600)
    e6 = entries(markets, 360)
    n, days = len(e10), len({e["day"] for e in e10})
    m, _, z = own(e10)
    h1h2 = halves_positive(e10)
    stress = st.mean(e["stress"] for e in e10) if e10 else 0.0
    by = defaultdict(list)
    for e in e10:
        by[e["series"]].append(e["net"])
    pos = sum(1 for v in by.values() if st.mean(v) > 0)
    dm, dz, _ = diff(e10, e6)
    if n < FWD7_MIN_N or days < FWD7_MIN_DAYS:
        v = "NOT_ENOUGH_DATA"
    else:
        v = "NOT_YET_FALSIFIED" if (m > 0 and z >= FWD7_Z and h1h2 and stress > 0 and pos >= FWD7_MIN_SERIES_POS and dm > 0 and dz >= FWD7_DIFF_Z) else "FALSIFIED"
    c = lambda x: f"{x * 100:+.2f}c"
    lines.append(f"FWD7: 10 minute entries n={n} on {days} days, net {c(m)} (z {z:+.2f}); both halves positive {h1h2}; at fees x{STRESS} {c(stress)}; series positive {pos} of {len(by)}; "
                 f"6 minute arm n={len(e6)} at {c(own(e6)[0])}; 10 minus 6 minute per day {c(dm)} (day clustered z {dz:+.2f}); VERDICT: {v}")
    yes = [e for e in e10 if e["side"] == "yes"]
    no = [e for e in e10 if e["side"] == "no"]
    lines.append(claim("FWD7 secondary (YES favourite minus NO favourite at 10 minutes)", yes, no, SIDE_Z, SIDE_MIN, SIDE_MIN, "YES", "NO")[0])
    return lines


def cut_claims(markets: list[tuple]):
    f = features(markets, entries(markets, 360), 360)
    return [claim("JUMP1 (rise under 5c minus 5c or more)", [e for e in f if e["rise"] < JUMP_CUT], [e for e in f if e["rise"] >= JUMP_CUT], CUT_Z, CUT_MIN, CUT_MIN, "stable", "jumped")[0],
            claim("JUMP1b (rise under 20c minus 20c or more)", [e for e in f if e["rise"] < JUMP_CUT_B], [e for e in f if e["rise"] >= JUMP_CUT_B], CUT_Z, CUT_MIN, CUT_MIN, "below 20c", "20c or more")[0],
            claim("TIB1 (4 or more minutes in band minus 1 or less)", [e for e in f if e["tib"] >= TIB_HI], [e for e in f if e["tib"] <= TIB_LO], CUT_Z, CUT_MIN, CUT_MIN, "firm", "new")[0],
            claim("DIP1 (lowest earlier mid 0.60 or more minus below 0.60)", [e for e in f if e["dip"] >= DIP_CUT], [e for e in f if e["dip"] < DIP_CUT], CUT_Z, CUT_MIN, CUT_MIN, "never doubted", "doubted")[0]]


def fwd10(markets: list[tuple]):
    live = [m for m in markets if m[1] in LIVE6]
    es = entries(live, 360)
    win = defaultdict(list)
    for e in es:
        win[e["close_ts"]].append(e)
    lines = []
    for s in FWD10_SERIES:
        alone = [e for k, g in win.items() if len(g) == 1 for e in g if e["series"] == s]
        crowd = [e for k, g in win.items() if len(g) >= 2 for e in g if e["series"] == s]
        days = len({e["day"] for e in alone})
        if len(alone) < FWD10_MIN_ALONE or days < FWD10_MIN_DAYS:
            lines.append(f"FWD10 {s}: NOT_ENOUGH_DATA (alone {len(alone)} on {days} days, crowded {len(crowd)})")
        else:
            lines.append(claim(f"FWD10 {s} (alone minus crowded)", alone, crowd, 2.4, FWD10_MIN_ALONE, 1, "alone", "crowded")[0])
    return lines


def ml1(markets: list[tuple]):
    lines = []
    for s, left in ML1.items():
        mm = [m for m in markets if m[1] == s]
        a, b = entries(mm, left), entries(mm, 360)
        days = len({e["day"] for e in a})
        if days < ML1_MIN_DAYS:
            lines.append(f"ML1 {s} at {left // 60} minutes: NOT_ENOUGH_DATA ({days} days)")
            continue
        dm, dz, nd = diff(a, b)
        am, _, az = own(a)
        v = "NOT_YET_FALSIFIED" if (dm > 0 and dz >= ML1_Z and am > 0) else "FALSIFIED"
        c = lambda x: f"{x * 100:+.2f}c"
        lines.append(f"ML1 {s} at {left // 60} minutes: n={len(a)} at {c(am)} (z {az:+.2f}); 6 minute n={len(b)} at {c(own(b)[0])}; difference per day {c(dm)} (day clustered z {dz:+.2f}, {nd} days); VERDICT: {v}")
    return lines


def report(markets: list[tuple]) -> list[str]:
    return fwd7(markets) + cut_claims(markets) + fwd10(markets) + ml1(markets)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] not in ("look", "read"):
        print(__doc__)
        return
    markets = load_fresh()
    days = fresh_days(markets)
    last = max((m[3] for m in markets), default=0)
    if argv[1] == "read":
        if days < MIN_DAYS_READ and time.time() < READ_DATE_TS:
            print(f"Refusing the registered read: {days} fresh days and the date is before 2026-12-01.")
            return
        if RESULT.exists():
            print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
            return
    head = (f"{'REGISTERED READ' if argv[1] == 'read' else 'INFORMATION LOOK, NOT THE REGISTERED READ (decides nothing)'}: {len(markets)} markets, {days} fresh days, "
            f"last close {datetime.fromtimestamp(last, timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    out = "\n".join([head] + report(markets))
    if argv[1] == "read":
        RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)

"""REV1 (README, Pre-registration: REV1): forward claim, Bitcoin 15 minute markets, buy the cheap NO side (ask 0.03 to 0.45) with 2 to 3 minutes left, hold. Research only.
Usage: python -m scalper.rev1 run   (once; refuses before 2026-11-05 and a second time). Run `python -m scalper.fresh_update` first.
"""
from __future__ import annotations

import sys
import time

from . import under1 as U
from .calibration import cluster_mean_z
from .paths import DATA_DIR

RESULT, START, READ_AFTER = DATA_DIR / "rev1_result.txt", "2026-10-28", "2026-11-05"
MIN_N, MIN_DAYS, BAR_C, BAR_Z = 400, 10, 0.010, 2.0


# ---- REV1SPLIT (workers/REV1_SPLIT_AMENDMENT.md): the same entries split by whether OICORE fired in the window. Information, not the verdict.
FIXED_DOI = 86299.56000000001      # REF_GEN6_OICORE.json
TRAIL_S, TRAIL_GAP_S, TRAIL_MIN, PCT = 86400, 900, 40, 90      # mechoi1.trailing_thr


def split_windows(lo: int, hi: int) -> list[tuple]:
    """Settled Bitcoin windows closing in [lo, hi): (ticker, close_ts, result, candles end_ts -> (bid, ask, vol, oi or None)), close order."""
    from . import oicorex1
    M = oicorex1.load_series("KXBTC15M", lo, hi)
    return [(tk, ct, res, cs) for tk, (ct, res, cs, _) in sorted(M.items(), key=lambda x: x[1][0]) if res in ("yes", "no")]


def window_doi(cs: dict, ct: int):
    """OICORE's trigger quantity: open interest at the candle ending 180 s before the close minus the one ending 360 s before. None if unknown."""
    a, b = cs.get(ct - 360), cs.get(ct - 180)
    if a is None or b is None or a[3] is None or b[3] is None:
        return None
    return float(b[3] - a[3])


def trailing_p90(items: list[tuple]) -> dict:
    """items (ct, doi or None) -> {ct: threshold or None}: 90th percentile of doi over windows closed in [ct - 24h, ct - 900 s], None with fewer than 40."""
    import numpy as np
    known = sorted((c, d) for c, d in items if d is not None)
    cts = np.array([c for c, _ in known]); ds = np.array([d for _, d in known])
    out = {}
    for ct, _ in items:
        m = (cts >= ct - TRAIL_S) & (cts <= ct - TRAIL_GAP_S)
        out[ct] = float(np.percentile(ds[m], PCT)) if m.sum() >= TRAIL_MIN else None
    return out


def split_entries(wins: list[tuple], fee_fn=None, looks=(120, 180), sides=("no",), lo=0.03, hi=0.45) -> list[dict]:
    """REV1's entries (default: NO side, ask 0.03 <= ask < 0.45, candle ending 120 or 180 s before the close, bought at that candle's ask, held),
    each tagged with OICORE's doi, whether it fired under the fixed threshold and under the trailing p90 ('yes', 'no' or 'unknown')."""
    from datetime import datetime, timezone
    fee_fn = fee_fn or U.fee
    thr = trailing_p90([(ct, window_doi(cs, ct)) for _, ct, _, cs in wins])
    out = []
    for tk, ct, res, cs in wins:
        doi = window_doi(cs, ct)
        fx = "unknown" if doi is None else ("yes" if doi > FIXED_DOI else "no")
        t = thr[ct]
        tp = "unknown" if (doi is None or t is None) else ("yes" if doi > t else "no")
        day = datetime.fromtimestamp(ct, timezone.utc).strftime("%Y-%m-%d")
        for ls in looks:
            c = cs.get(ct - ls)
            if c is None:
                continue
            for side in sides:
                ask = c[1] if side == "yes" else round(1 - c[0], 4)
                if lo <= ask < hi:
                    out.append({"tk": tk, "ct": ct, "day": day, "ls": ls, "side": side, "ask": ask, "win": 1.0 if res == side else 0.0,
                                "net": (1.0 if res == side else 0.0) - ask - fee_fn(ask), "doi": doi, "fixed": fx, "p90": tp})
    return out


def _line(name: str, rows: list[dict]) -> str:
    if not rows:
        return f"  {name}: n 0"
    days = sorted({r["day"] for r in rows}); cut = days[len(days) // 2]
    m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    h1 = [r["net"] for r in rows if r["day"] < cut]; h2 = [r["net"] for r in rows if r["day"] >= cut]
    h = f"{100 * sum(h1) / len(h1):+.2f}/{100 * sum(h2) / len(h2):+.2f}c" if h1 and h2 else "n/a"
    pos = sum(r["net"] for r in rows if r["net"] > 0); neg = -sum(r["net"] for r in rows if r["net"] < 0)
    pf = pos / neg if neg > 0 else float("inf")
    return (f"  {name}: n {len(rows)} ({len({r['tk'] for r in rows})} windows) on {len(days)} days, win {100 * sum(r['win'] for r in rows) / len(rows):.1f}% "
            f"vs price paid {100 * sum(r['ask'] for r in rows) / len(rows):.1f}%, PF {pf:.2f}, mean {100 * m:+.2f}c, z {z:+.2f}, halves {h}")


def split_report(rows: list[dict]) -> str:
    """Printed after the registered line. NOT the registered verdict."""
    out = ["REV1 split by whether OICORE fired in the window (information, NOT the registered verdict; workers/REV1_SPLIT_AMENDMENT.md)"]
    for key, label in (("fixed", f"fixed doi > {FIXED_DOI:,.2f}"), ("p90", "trailing 24h p90 of doi")):
        out.append(f" version: {label}")
        parts = {k: [r for r in rows if r[key] == k] for k in ("yes", "no", "unknown")}
        out.append(_line("pooled          ", rows))
        out.append(_line("OICORE fired    ", parts["yes"]))
        out.append(_line("OICORE not fired", parts["no"]))
        out.append(_line("unknown (no OI) ", parts["unknown"]))
        out.append(f"  overlap: {len(parts['yes'])} entries in {len({r['tk'] for r in parts['yes']})} windows where OICORE also fired")
        if parts["no"]:
            m = sum(r["net"] for r in parts["no"]) / len(parts["no"])
            out.append("  NOT-fired half alone is " + ("NEGATIVE" if m < 0 else "not negative") + f" (mean {100 * m:+.2f}c)")
    return "\n".join(out)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    if time.strftime("%Y-%m-%d", time.gmtime()) < READ_AFTER:
        print(f"Refusing to read before {READ_AFTER}."); return
    rows = [r for r in U.rows_for() if r["series"] == "KXBTC15M" and r["side"] == "no" and r["ls"] in (120, 180) and r["day"] >= START]
    days = sorted({r["day"] for r in rows})
    if len(rows) < MIN_N or len(days) < MIN_DAYS:
        out = f"REV1 NOT_ENOUGH_DATA: {len(rows)} entries on {len(days)} days"
    else:
        cut = days[len(days) // 2]
        m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
        h1 = [r["net"] for r in rows if r["day"] < cut]; h2 = [r["net"] for r in rows if r["day"] >= cut]
        stress = sum(r["net"] - 0.2 * 0.07 * (1 - r["net"]) * 0 for r in rows) / len(rows)
        ok = m >= BAR_C and z >= BAR_Z and sum(h1) > 0 and sum(h2) > 0
        v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if m < 0 else "NOT_ENOUGH_DATA")
        out = f"REV1 {v}: n {len(rows)} on {len(days)} days, mean {100 * m:+.2f}c, z {z:+.2f}, halves {100 * sum(h1) / len(h1):+.2f}/{100 * sum(h2) / len(h2):+.2f}c"
    try:
        from datetime import datetime, timezone
        lo = int(datetime.strptime(START, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
        rows2 = split_entries(split_windows(lo, 2 ** 40))
        out += "\n" + split_report(rows2)
    except Exception as e:      # the split must never block the registered line
        out += f"\nREV1 split unavailable: {e!r}"
    RESULT.write_text(out + "\n"); print(out)


if __name__ == "__main__":
    main(sys.argv)

"""IDEAS20D (README, Pre-registration: IDEAS20D): Bitcoin and Ethereum rules from three families no earlier test used: the trading SESSION (six hour blocks of the UTC day and the US cash open),
CROSS-ASSET state (the other coin's favourite at the same time) and a scheduled-data window. Each rule is scored against the same coin's own baseline for the same entry, discovery on the first two
thirds of the days, confirmation on the last third. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.ideas20d run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone

from . import ideas20 as I
from . import lstrats as L
from .paths import DATA_DIR

# ---- fixed in the README before any outcome was split by these rules ----
COINS = ("KXBTC15M", "KXETH15M")
ENTRIES = {"E540": (540, (0.80, 0.93)), "L1360": (360, (0.88, 0.97))}
RESULT = DATA_DIR / "ideas20d_result.txt"


def hour_of(m: dict) -> float:
    d = datetime.fromtimestamp(m["close"], timezone.utc)
    return d.hour + d.minute / 60


def minute_of_day(m: dict) -> int:
    d = datetime.fromtimestamp(m["close"], timezone.utc)
    return d.hour * 60 + d.minute


def make_rules(other: dict[str, dict[int, dict]]):
    """Rules take (market, decision candle, earlier candles, band, left) and return (side, price) or None. `other` maps a coin to {close_ts: market}."""
    def fav(c, band):
        return L.favorite(c["bid"], c["ask"], band)

    def session(lo, hi):
        def rule(m, c, e, band, left, coin):
            f = fav(c, band)
            return f if f and lo <= hour_of(m) < hi else None
        return rule

    def us_open(m, c, e, band, left, coin):               # windows closing 13:15 to 14:00 or 14:15 to 15:00 UTC: the US cash open in summer and in winter
        f = fav(c, band)
        h = hour_of(m)
        return f if f and (13.25 <= h < 14.0 or 14.25 <= h < 15.0) else None

    def data_window(m, c, e, band, left, coin):           # windows closing 12:30 to 13:00 or 13:30 to 14:00 UTC (the window before, during and after an 8:30 ET release, summer and winter)
        f = fav(c, band)
        return f if f and hour_of(m) in (12.5, 12.75, 13.0, 13.5, 13.75, 14.0) else None

    def cross(agree):
        """agree: the other coin is also in the band on the same side. alone: the other coin has no favourite in the band at all (it is undecided or already decided)."""
        def rule(m, c, e, band, left, coin):
            f = fav(c, band)
            if not f:
                return None
            o = next((x for k, v in other.items() if k != coin for x in [v.get(m["close"])] if x), None)
            if o is None:
                return None
            oc, _ = I.at(o, left)
            if oc is None:
                return None
            of = L.favorite(oc["bid"], oc["ask"], band)
            return f if ((of is not None and of[0] == f[0]) if agree else of is None) else None
        return rule

    return [("SESSION_00_06", session(0, 6)), ("SESSION_06_12", session(6, 12)), ("SESSION_12_18", session(12, 18)), ("SESSION_18_24", session(18, 24)),
            ("US_OPEN", us_open), ("DATA_0830ET", data_window), ("CROSS_AGREE", cross(True)), ("CROSS_ALONE", cross(False))]


def baseline(mk: dict, left: int, band) -> list[dict]:
    return I.entries(mk, left, lambda m, c, e, ps: L.favorite(c["bid"], c["ask"], band))


def rows_for(mks: dict[str, dict], rule, left: int, band, cut: str) -> list[dict]:
    """Rule entries pooled over both coins; net and stress are minus the coin's own all-entries mean of the same entry in the same period (discovery or confirmation)."""
    by_close = {coin: {m["close"]: m for m in mk.values()} for coin, mk in mks.items()}
    out = []
    for coin, mk in mks.items():
        base = baseline(mk, left, band)
        b = {}
        for part in (True, False):
            sel = [r for r in base if (r["day"] < cut) == part]
            b[part] = (st.mean(r["net"] for r in sel), st.mean(r["stress"] for r in sel)) if sel else (0.0, 0.0)
        rr = I.entries(mk, left, lambda m, c, e, ps: rule(m, c, e, band, left, coin))
        for r in rr:
            adj = b[r["day"] < cut]
            out.append({**r, "raw": r["net"], "net": r["net"] - adj[0], "stress": r["stress"] - adj[1], "series": coin})
    return out


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mks = {c: I.load_btc(c) for c in COINS}
    cut = I.cut_day({tk: m for mk in mks.values() for tk, m in mk.items()})
    other = {c: {m["close"]: m for m in mk.values()} for c, mk in mks.items()}
    out = [f"IDEAS20D: Bitcoin {len(mks['KXBTC15M'])} and Ethereum {len(mks['KXETH15M'])} markets, discovery before {cut}"]
    for ename, (left, band) in ENTRIES.items():
        for name, rule in make_rules(other):
            rows = rows_for(mks, rule, left, band, cut)
            j = I.judge(rows, cut, [{**r, "net": r["raw"]} for r in rows])
            pos = sum(1 for s in COINS if (v := [x["net"] for x in rows if x["series"] == s]) and st.mean(v) > 0)
            if j["verdict"] == "NOT_YET_FALSIFIED" and pos < 2:
                j["verdict"] = "NOT_ENOUGH_DATA"
            out.append(f"{ename:5s} {name:15s} {j['verdict']:18s} disc n={j['nd']:5d} {100 * j['dm']:+6.2f}c z {j['dz']:+5.2f} | conf n={j['nc']:5d} {100 * j['cm']:+6.2f}c z {j['cz']:+5.2f} | all {100 * j['am']:+6.2f}c z {j['az']:+5.2f} PF {j['pf']:.2f} coins+ {pos}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)

"""The market scout (README, "The market scout"): a read-only, repeatable screen of Kalshi's non-15-minute prediction markets. Public data only; places nothing; decides nothing.
Usage: python -m scalper.scout census          every hourly, daily and weekly series with its settled markets and volume over the last 69 days -> data/scout_census.json
       python -m scalper.scout screen          a generic L1 (the favourite at 60% of the market's life) on the liquid ones -> studies/scout_YYYY-MM-DD.md
       python -m scalper.scout report          prints the last screen's table
A series is flagged a LEAD only with at least 150 entries on 10 days, mean net at least +1.0c and day-clustered z at least 2.5: a lead is a reason to pre-register a test on unseen days.
"""
from __future__ import annotations

import itertools
import json
import statistics as st
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

from . import api
from .analyze import valid_quote
from .backfill import iso_ts, parse_candle
from .calibration import cluster_mean_z
from .paths import DATA_DIR

FREQS = ("hourly", "daily", "weekly")
WINDOW_DAYS, FRAC, BAND = 69, 0.60, (0.88, 0.97)
MIN_MARKETS, MIN_MEDIAN_VOLUME, MAX_LIFE_S, SAMPLE = 100, 500.0, 3 * 86400, 220
LEAD_N, LEAD_DAYS, LEAD_NET, LEAD_Z = 150, 10, 0.01, 2.5
CENSUS, STUDIES = DATA_DIR / "scout_census.json", DATA_DIR.parent / "studies"


def fee(p: float) -> float:
    return 0.07 * p * (1 - p)


def decision_candle(candles: list[tuple], open_ts: int, close_ts: int, frac: float = FRAC):
    """The last candle (end, bid, ask) ending at or before open + frac x life, or None. Candles are (end_ts, bid_c, ask_c)."""
    target = open_ts + frac * (close_ts - open_ts)
    best = None
    for c in sorted(candles):
        if c[0] <= target:
            best = c
    return best


def entry_of(c: tuple, band=BAND):
    """(side, price) of the favourite at a candle, or None."""
    _, bid, ask = c
    if bid is None or ask is None or not valid_quote(bid, ask):
        return None
    if band[0] <= ask <= band[1]:
        return "yes", ask
    no = round(1 - bid, 4)
    if band[0] <= no <= band[1]:
        return "no", no
    return None


def net_of(side: str, price: float, result: str) -> float:
    return (1.0 if side == result else 0.0) - price - fee(price)


CAP_MARKETS = 600                                                     # per series; "markets" is a floor when "capped" is true


def census() -> None:
    now = int(time.time())
    lo = now - WINDOW_DAYS * 86400
    allseries = api._get("/series", {"limit": 20000}).get("series", [])
    cand = [s for s in allseries if s.get("frequency") in FREQS]
    print(f"{len(allseries)} series, {len(cand)} hourly, daily or weekly", flush=True)
    partial = DATA_DIR / "scout_census_partial.json"
    out = json.loads(partial.read_text()) if partial.exists() else {}          # resumable: a restart keeps what is done
    if out:
        print(f"resuming with {len(out)} series already done", flush=True)
    for k, s in enumerate(sorted(cand, key=lambda x: x["ticker"])):
        if s["ticker"] in out:
            continue
        try:
            ms = list(itertools.islice(api.settled_markets(s["ticker"], lo, now), CAP_MARKETS))      # a busy series needs no more than a floor for ranking
        except Exception as e:                                   # a series that errors is recorded as such, not guessed
            out[s["ticker"]] = {"error": str(e)[:80], "frequency": s.get("frequency"), "category": s.get("category"), "title": s.get("title")}
            continue
        vols = [float(m.get("volume_fp") or 0) for m in ms]
        lives = [(iso_ts(m.get("close_time")) or 0) - (iso_ts(m.get("open_time")) or 0) for m in ms]
        out[s["ticker"]] = {"frequency": s.get("frequency"), "category": s.get("category"), "title": s.get("title"), "markets": len(ms), "total_volume": sum(vols),
                            "median_volume": st.median(vols) if vols else 0.0, "median_life_s": st.median(lives) if lives else 0, "days": len({(m.get("close_time") or "")[:10] for m in ms}), "capped": len(ms) >= CAP_MARKETS}
        if len(out) % 5 == 0:                                                   # every 5 done, not by index: skipped series must not hide the save
            partial.write_text(json.dumps(out))
            print(f"  {len(out)} done / {len(cand)}", flush=True)
        time.sleep(0.15)
    CENSUS.write_text(json.dumps({"as_of": now, "series": out}))
    if partial.exists():
        partial.unlink()
    traded = [v for v in out.values() if v.get("markets")]
    print(f"done: {len(traded)} of {len(cand)} had a settled market in {WINDOW_DAYS} days")


def screen() -> None:
    snap = json.loads(CENSUS.read_text())
    ser = snap["series"]
    elig = sorted([(v["total_volume"], t) for t, v in ser.items() if v.get("markets", 0) >= MIN_MARKETS and v.get("median_volume", 0) >= MIN_MEDIAN_VOLUME and 0 < v.get("median_life_s", 0) <= MAX_LIFE_S], reverse=True)
    now = int(time.time())
    lo = now - WINDOW_DAYS * 86400
    partial = DATA_DIR / "scout_screen_partial.json"
    results = json.loads(partial.read_text()) if partial.exists() else {}               # resumable: a restart keeps the series already screened
    for vol, t in elig:
        if t in results or t in results.get("_empty", []):
            continue
        try:
            ms = [m for m in api.settled_markets(t, lo, now) if m.get("result") in ("yes", "no")]
        except Exception:
            continue
        ms.sort(key=lambda m: m.get("close_time") or "", reverse=True)
        ms = ms[:SAMPLE]
        life = st.median([(iso_ts(m["close_time"]) - iso_ts(m["open_time"])) for m in ms if iso_ts(m.get("close_time")) and iso_ts(m.get("open_time"))] or [0])
        interval = 1 if life <= 7200 else 60
        rows, step = [], 20
        todo = sorted(ms, key=lambda m: m["close_time"])
        i = 0
        while i < len(todo):
            chunk = todo[i:i + step]
            o = min(iso_ts(m["open_time"]) for m in chunk)
            c = max(iso_ts(m["close_time"]) for m in chunk)
            try:
                got = api._get("/markets/candlesticks", {"market_tickers": ",".join(m["ticker"] for m in chunk), "start_ts": o, "end_ts": c, "period_interval": interval})
                cmap = {x.get("market_ticker"): x.get("candlesticks", []) for x in got.get("markets", [])}
            except Exception:
                if step > 1:
                    step = max(1, step // 2)
                    continue
                cmap = {}
            for m in chunk:
                cs = [parse_candle(x, m["ticker"], t) for x in cmap.get(m["ticker"], [])]
                cs = [(r[2], r[6], r[10]) for r in cs if r]
                dc = decision_candle(cs, iso_ts(m["open_time"]), iso_ts(m["close_time"]))
                en = entry_of(dc) if dc else None
                if en:
                    rows.append((m["close_time"][:10], net_of(en[0], en[1], m["result"]), en[1], 1 if en[0] != m["result"] else 0, float(m.get("volume_fp") or 0)))
            i += len(chunk)
            time.sleep(0.3)
        if rows:
            mean, _, z = cluster_mean_z([(d, n) for d, n, *_ in rows]) if len(rows) > 1 else (0.0, 0.0, 0.0)
            results[t] = {"n": len(rows), "days": len({r[0] for r in rows}), "net": mean, "z": z, "loss": sum(r[3] for r in rows) / len(rows), "price": st.mean(r[2] for r in rows),
                          "median_volume": st.median(r[4] for r in rows), "title": ser[t].get("title"), "category": ser[t].get("category"), "frequency": ser[t].get("frequency"), "life_h": life / 3600}
        print(f"  {t}: {len(rows)} entries", flush=True)
        partial.write_text(json.dumps(results))
    results.pop("_empty", None)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    STUDIES.mkdir(exist_ok=True)
    (STUDIES / f"scout_{today}.json").write_text(json.dumps({"census_as_of": snap["as_of"], "results": results}, indent=1))
    lines = [f"# Market scout, {today}", "", f"Census: {len(ser)} hourly, daily and weekly series; {sum(1 for v in ser.values() if v.get('markets'))} had a settled market in {WINDOW_DAYS} days; screened {len(results)} liquid ones "
             f"(at least {MIN_MARKETS} markets, median volume {MIN_MEDIAN_VOLUME:.0f}, life up to 3 days). Generic L1: favourite 0.88 to 0.97 at {FRAC:.0%} of the market's life, held to settlement, fee 7%.", "",
             "| Series | Frequency | Entries | Days | Net per contract | z | Loss rate | Mean price | Median volume | Flag |", "|---|---|---|---|---|---|---|---|---|---|"]
    for t, r in sorted(results.items(), key=lambda kv: -kv[1]["z"]):
        flag = "LEAD" if (r["n"] >= LEAD_N and r["days"] >= LEAD_DAYS and r["net"] >= LEAD_NET and r["z"] >= LEAD_Z) else ""
        lines.append(f"| {t} {r['title'] or ''} | {r['frequency']} | {r['n']} | {r['days']} | {r['net'] * 100:+.2f}c | {r['z']:+.2f} | {r['loss'] * 100:.1f}% | {r['price'] * 100:.1f}c | {r['median_volume']:.0f} | {flag} |")
    (STUDIES / f"scout_{today}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def report() -> None:
    files = sorted(STUDIES.glob("scout_*.md"))
    print(files[-1].read_text() if files else "no scout report yet")


if __name__ == "__main__":
    {"census": census, "screen": screen, "report": report}[sys.argv[1]]()

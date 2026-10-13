"""PM1 (README, Pre-registration: PM1): does Polymarket's 15 minute price carry information Kalshi's does not. Rules fixed in the README before any Polymarket price was downloaded.
Research only: nothing here places an order and the Polymarket API is only read. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

History goes into its OWN database (`data/pm1.sqlite`). Usage: python -m scalper.pm1 fetch   then   python -m scalper.pm1 run
"""
from __future__ import annotations

import json
import sqlite3
import statistics as st
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from . import lstrats as L
from .analyze import valid_quote
from .calibration import cluster_mean_z
from .paths import DATA_DIR, DB

PM_DB = DATA_DIR / "pm1.sqlite"
ASSETS = {"KXBTC15M": "btc", "KXETH15M": "eth"}
ENTRY_LEFT_S = 360
MAX_AGE_S = 180
BLEND = 0.5
MIN_OBS = 500
MIN_DAYS = 10
Z_BAR = 2.1
AUDIT_GAIN = 0.002
DISAGREE = 0.05
GAMMA = "https://gamma-api.polymarket.com/events"
CLOB = "https://clob.polymarket.com/prices-history"
BATCH = 40


def slug(asset: str, close_ts: int) -> str:
    """Polymarket names a window by its START: the Kalshi close minus 900 s."""
    return f"{asset}-updown-15m-{close_ts - 900}"


def last_point(points: list[tuple[int, float]], cutoff: int, max_age: int = MAX_AGE_S) -> float | None:
    """The latest price at or before `cutoff` and no more than `max_age` seconds older; a point after the cutoff is never read."""
    ok = [(t, p) for t, p in points if t <= cutoff and cutoff - t <= max_age]
    return max(ok)[1] if ok else None


def paired_d(p_k: float, p_pm: float, y: float) -> float:
    """Positive when the fixed 50/50 blend predicts the outcome better (smaller squared error) than Kalshi's mid alone."""
    return (p_k - y) ** 2 - (BLEND * p_k + (1.0 - BLEND) * p_pm - y) ** 2


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def _get(url: str, params: list[tuple[str, str]] | dict, retries: int = 6):
    q = urllib.parse.urlencode(params)
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(f"{url}?{q}", headers={"User-Agent": "Mozilla/5.0 research"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:                   # a dropped connection, a 429 or a 5xx: back off and retry
            last = e
            time.sleep(min(2 ** i, 30))
    raise RuntimeError(f"GET {url} failed: {last}")


def windows() -> list[dict]:
    """Kalshi windows of the two registered series that have a result and a valid quote at the entry candle."""
    db = sqlite3.connect(DB)
    out = []
    for t, s, c, r in db.execute("SELECT ticker, series, close_ts, result FROM market WHERE series IN ('KXBTC15M','KXETH15M') AND result IN ('yes','no')"):
        row = db.execute("SELECT bid_c, ask_c FROM candle WHERE ticker=? AND end_ts=?", (t, c - ENTRY_LEFT_S)).fetchone()
        if row and valid_quote(row[0], row[1]):
            out.append({"ticker": t, "series": s, "close_ts": c, "yes": r == "yes", "bid": row[0], "ask": row[1]})
    return sorted(out, key=lambda w: w["close_ts"])


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    pm = sqlite3.connect(PM_DB)
    pm.executescript("""CREATE TABLE IF NOT EXISTS event(slug TEXT PRIMARY KEY, token TEXT, volume REAL);
CREATE TABLE IF NOT EXISTS pt(slug TEXT, t INTEGER, p REAL, PRIMARY KEY(slug, t));""")
    done = {r[0] for r in pm.execute("SELECT slug FROM event")}
    todo = [(slug(ASSETS[w["series"]], w["close_ts"]), w["close_ts"]) for w in windows()]
    todo = [x for x in todo if x[0] not in done]
    print(f"{len(todo)} windows to fetch", flush=True)
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        evs = _get(GAMMA, [("slug", s) for s, _ in chunk] + [("limit", "100")])
        by = {e["slug"]: e for e in evs}
        for s, close in chunk:
            e = by.get(s)
            token, vol = None, None
            if e and e.get("markets"):
                m = e["markets"][0]
                outs, toks = json.loads(m.get("outcomes") or "[]"), json.loads(m.get("clobTokenIds") or "[]")
                if outs and toks and outs[0] == "Up":
                    token, vol = toks[0], float(m.get("volume") or 0.0)
            if token:
                h = _get(CLOB, {"market": token, "startTs": close - 1200, "endTs": close - ENTRY_LEFT_S, "fidelity": 1}).get("history", [])
                pm.executemany("INSERT OR REPLACE INTO pt VALUES(?,?,?)", [(s, int(x["t"]), float(x["p"])) for x in h if int(x["t"]) <= close - ENTRY_LEFT_S])
            pm.execute("INSERT OR REPLACE INTO event VALUES(?,?,?)", (s, token, vol))
        pm.commit()
        time.sleep(0.2)
        if (i // BATCH) % 10 == 9:
            print(f"  {i + len(chunk)} windows", flush=True)
    print("done", flush=True)


def observations(wins: list[dict], pts: dict[str, list[tuple[int, float]]]) -> list[dict]:
    """One row per window with a recent Polymarket point at the entry second. `pts` maps a slug to its (t, p) points."""
    out = []
    for w in wins:
        pp = last_point(pts.get(slug(ASSETS[w["series"]], w["close_ts"]), []), w["close_ts"] - ENTRY_LEFT_S)
        if pp is None:
            continue
        p_k = (w["bid"] + w["ask"]) / 2.0
        y = 1.0 if w["yes"] else 0.0
        out.append({"series": w["series"], "close_ts": w["close_ts"], "day": _day(w["close_ts"]), "p_k": p_k, "p_pm": pp, "y": y, "d": paired_d(p_k, pp, y), "bid": w["bid"], "ask": w["ask"]})
    return out


def verdict(obs: list[dict]) -> tuple[str, dict]:
    days = sorted({o["day"] for o in obs})
    if len(obs) < MIN_OBS or len(days) < MIN_DAYS:
        return "NOT_ENOUGH_DATA", {"n": len(obs), "days": len(days)}
    mean, se, z = cluster_mean_z([(o["day"], o["d"]) for o in obs])
    mid = days[len(days) // 2]
    h1 = [o["d"] for o in obs if o["day"] < mid]
    h2 = [o["d"] for o in obs if o["day"] >= mid]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    ok = mean > 0 and z >= Z_BAR and m1 > 0 and m2 > 0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": len(obs), "days": len(days), "mean": mean, "z": z, "h1": m1, "h2": m2, "audit": mean > AUDIT_GAIN}


def disagreement_split(obs: list[dict]) -> dict:
    """Information only: L1-style entries (favourite's ask 0.88 to 0.97) split by whether Polymarket's price for that side is DISAGREE or more below Kalshi's mid."""
    groups = {"disagrees": [], "agrees": []}
    for o in obs:
        pick = L.favorite(o["bid"], o["ask"], L.L1["band"])
        if pick is None:
            continue
        side, price = pick
        yes = o["y"] == 1.0
        k_side = o["p_k"] if side == "yes" else 1.0 - o["p_k"]
        pm_side = o["p_pm"] if side == "yes" else 1.0 - o["p_pm"]
        groups["disagrees" if pm_side <= k_side - DISAGREE + 1e-12 else "agrees"].append(L.net(side, price, yes))
    return groups


def run() -> None:
    wins = windows()
    pm = sqlite3.connect(PM_DB)
    pts: dict = {}
    for s, t, p in pm.execute("SELECT slug, t, p FROM pt"):
        pts.setdefault(s, []).append((t, p))
    obs = observations(wins, pts)
    print(f"{len(wins)} Kalshi windows with a quote, {len(obs)} with a recent Polymarket point. Signal counts first.\n")
    f = lambda v: f"{v:+.4f}"
    for series in ASSETS:
        mine = [o for o in obs if o["series"] == series]
        v, s = verdict(mine)
        print(f"{series}: {len(mine)} observations of {sum(1 for w in wins if w['series'] == series)} windows")
        if "mean" in s:
            print(f"    mean Brier gain of the 50/50 blend over Kalshi alone {f(s['mean'])}, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}" + ("  AUDIT TRIGGER: gain above +0.002" if s["audit"] else ""))
        print(f"    -> {v}")
        if mine:
            br = lambda key: st.mean((o[key] - o["y"]) ** 2 for o in mine)
            print(f"    Brier: Kalshi {br('p_k'):.4f}, Polymarket {br('p_pm'):.4f}, blend {st.mean((BLEND * o['p_k'] + (1 - BLEND) * o['p_pm'] - o['y']) ** 2 for o in mine):.4f}; "
                  f"median |gap| {st.median(abs(o['p_pm'] - o['p_k']) for o in mine) * 100:.1f}c")
            g = disagreement_split(mine)
            for name, nets in g.items():
                if nets:
                    print(f"    L1-style entries where Polymarket {name}: n={len(nets)} loss rate {sum(1 for x in nets if x < 0) / len(nets):.1%} mean net {st.mean(nets) * 100:+.2f}c (information only)")


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()

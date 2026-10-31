"""ECONNEW2 (workers/ECONNEW2_REGISTRATION.md): two angles, research only (discovery lane).
 (A) GAS-RBOB: Kalshi weekly AAA gas ladder (KXAAAGASW) against a pass-through model from RBOB futures (Yahoo RB=F).
 (B) PCE-NOWCAST: Kalshi core PCE strikes (KXPCECORE) against the Cleveland Fed core PCE nowcast (a reword of CPI1 on a new series).
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. Nothing here means trade.
    python -m scalper.econnew2 fetch     (public data into data/econnew2/: RB=F daily bars, Cleveland nowcast, Kalshi market listings; resumable)
    python -m scalper.econnew2 prep      (angle A: fit the pass-through on DISCOVERY only, freeze it, write both universes; no price is read)
    python -m scalper.econnew2 candles   (hourly candles for the two universes; resumable)
    python -m scalper.econnew2 run       (the one scored read; refused a second time)
Historical candles name their fields close/volume, live candles close_dollars/volume_fp: pick() reads both (the ECONNEW1 parser bug).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

from . import api
from .calibration import cluster_mean_z
from .econnew1 import fee, line, pick, pnl, stats
from .paths import DATA_DIR

D = DATA_DIR / "econnew2"
RESULT = DATA_DIR / "econnew2_result.txt"
NC_URL = "https://www.clevelandfed.org/-/media/files/webcharts/inflationnowcasting/nowcast_month.json"
RB_URL = "https://query1.finance.yahoo.com/v8/finance/chart/RB=F?period1=1688169600&period2=1793500000&interval=1d"
ET = ZoneInfo("America/New_York")
UTC = timezone.utc
EDGE, LEAD_S, MAX_AGE_S, MAX_SPREAD = 0.05, 86400, 6 * 3600, 0.10
UNIV = (0.10, 0.90)
# windows by market close date, fixed in the registration (first 60% / next 20% / last 20% of the eligible events)
CUT = {"A": (datetime(2025, 11, 14, tzinfo=UTC), datetime(2026, 5, 8, tzinfo=UTC)),
       "B": (datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 6, 1, tzinfo=UTC))}
MIN_TR = {"A": (100, 50), "B": (100, 50)}
BAR_PF, BAR_Z = 1.5, 5.27
MONTHS = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}
MIN_ERR_MONTHS = 36


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def window(angle, close):
    a, b = CUT[angle]
    return "disc" if close < a else ("val" if close < b else "hold")


def get_text(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode()


def num(v):
    try:
        return float(str(v).replace("$", "").replace("%", "").replace(",", ""))
    except ValueError:
        return None


# ---------------------------------------------------------------- fetch
def list_markets(series):
    out = {}
    for s in series:
        for path, key in (("/historical/markets", "hist"), ("/markets", "live")):
            cur = None
            while True:
                p = {"series_ticker": s, "limit": 1000}
                if key == "live":
                    p["status"] = "settled"
                if cur:
                    p["cursor"] = cur
                d = api._get(path, p)
                for m in d.get("markets", []):
                    if m.get("result") in ("yes", "no"):
                        out[m["ticker"]] = {"t": m["ticker"], "ev": m["event_ticker"], "res": m["result"], "close": m["close_time"], "strike": m.get("floor_strike"),
                                            "type": m.get("strike_type"), "val": m.get("expiration_value"), "src": key, "series": s}
                cur = d.get("cursor")
                if not cur or not d.get("markets"):
                    break
    return out


def fetch():
    D.mkdir(exist_ok=True)
    if not (D / "rbob.json").exists():
        for i in range(5):
            try:
                r = json.loads(get_text(RB_URL))["chart"]["result"][0]
                (D / "rbob.json").write_text(json.dumps({"ts": r["timestamp"], "close": r["indicators"]["quote"][0]["close"]}))
                break
            except Exception as e:
                print("yahoo", e); time.sleep(15 * (i + 1))
    if not (D / "nowcast.json").exists():
        (D / "nowcast.json").write_text(get_text(NC_URL))
    if not (D / "markets.json").exists():
        (D / "markets.json").write_text(json.dumps(list_markets(["KXAAAGASW", "KXPCECORE"])))
    print("fetched; nowcast sha256", hashlib.sha256((D / "nowcast.json").read_bytes()).hexdigest()[:16], flush=True)


# ---------------------------------------------------------------- angle A: AAA weekly vs RBOB
def rb_bars():
    r = json.loads((D / "rbob.json").read_text())
    bars = {}
    for t, c in zip(r["ts"], r["close"]):
        if c is not None:
            bars[datetime.fromtimestamp(t, UTC).astimezone(ET).date()] = c
    return sorted(bars.items())


def rb_before(bars, d):
    """Last RBOB daily close with bar date strictly before the date d (ET)."""
    v = None
    for bd, c in bars:
        if bd < d:
            v = c
        else:
            break
    return v


def aaa_events(markets):
    """Events in close order with the AAA settled value of each; eligibility uses dates only (previous two events 5.5 to 8.5 days apart)."""
    ev = {}
    for x in markets.values():
        if x["series"] == "KXAAAGASW" and x["type"] == "greater" and x["strike"] is not None:
            e = ev.setdefault(x["ev"], {"ev": x["ev"], "close": ts(x["close"]), "val": None, "mk": []})
            e["mk"].append(x)
            if e["val"] is None:
                e["val"] = num(x["val"])
    evs = sorted(ev.values(), key=lambda e: e["close"])
    bars = rb_bars()
    for i, e in enumerate(evs):
        e["ok"] = False
        if i < 2:
            continue
        if not all(5.5 <= (evs[i - k + 1]["close"] - evs[i - k]["close"]).total_seconds() / 86400 <= 8.5 for k in (1, 2)):
            continue
        look = e["close"] - timedelta(seconds=LEAD_S)
        ld = look.astimezone(ET).date()
        r1, r0 = rb_before(bars, ld), rb_before(bars, ld - timedelta(days=14))
        a1, a2 = evs[i - 1]["val"], evs[i - 2]["val"]
        if None in (r1, r0, a1, a2, e["val"]):
            continue
        e.update(ok=True, x1=r1 - r0, x2=a1 - a2, a1=a1, y=e["val"] - a1)
    return evs


def fit_a(evs):
    disc = [e for e in evs if e["ok"] and window("A", e["close"]) == "disc"]
    X = np.array([[1.0, e["x1"], e["x2"]] for e in disc]); y = np.array([e["y"] for e in disc])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    r = y - X @ b
    scale = float(np.sqrt(len(y) / (len(y) - 3)))
    return {"coef": b.tolist(), "resid": r.tolist(), "scale": scale, "n": len(y)}


def fair_a(model, e, strike):
    b = model["coef"]
    centre = e["a1"] + b[0] + b[1] * e["x1"] + b[2] * e["x2"]
    n = sum(1 for r in model["resid"] if centre + model["scale"] * r > strike)
    return (n + 0.5) / (len(model["resid"]) + 1)


def prep():
    mk = json.loads((D / "markets.json").read_text())
    evs = aaa_events(mk)
    model = fit_a(evs)
    uni = {}
    for e in evs:
        if not e["ok"]:
            continue
        for x in e["mk"]:
            f = fair_a(model, e, x["strike"])
            if UNIV[0] <= f <= UNIV[1]:
                uni[x["t"]] = dict(x, fair=f, angle="A", w=window("A", e["close"]))
    # angle B universe: every strike of an eligible event (no model filter, as CPI1)
    for x in pce_markets(mk).values():
        uni[x["t"]] = x
    (D / "model_a.json").write_text(json.dumps(model)); (D / "universe.json").write_text(json.dumps(uni))
    ne = sum(1 for e in evs if e["ok"])
    print("angle A: events", len(evs), "eligible", ne, {w: sum(1 for e in evs if e["ok"] and window("A", e["close"]) == w) for w in ("disc", "val", "hold")})
    print("coef (a, b_rbob14d, b_prev_change)", [round(c, 4) for c in model["coef"]], "resid sd", round(float(np.std(model["resid"])), 4), "n", model["n"])
    print("universe: A", sum(1 for x in uni.values() if x["angle"] == "A"), "B", sum(1 for x in uni.values() if x["angle"] == "B"))


# ---------------------------------------------------------------- angle B: core PCE vs Cleveland
def nowcast_table():
    raw = json.loads((D / "nowcast.json").read_text())
    out = {}
    for x in raw:
        labels = [c["label"] for c in x["categories"][0]["category"]]
        ds = {s["seriesname"]: [v.get("value", "") for v in s["data"]] for s in x["dataset"]}
        nc, act = ds.get("Core PCE Inflation", []), ds.get("Actual Core PCE Inflation", [])
        vals = [(labels[i], float(nc[i])) for i in range(min(len(nc), len(labels))) if nc[i] not in ("", None)]
        actual = next((float(a) for a in reversed(act) if a not in ("", None)), None)
        out[x["chart"]["subcaption"]] = {"nc": vals, "actual": actual}
    return out


def ref_month(ev):
    s = ev.split("-")[-1]
    mon = MONTHS.get(s[2:5])
    return (2000 + int(s[:2]), mon) if mon else None


def pce_errors(tbl):
    out = []
    for ref, t in tbl.items():
        if t["actual"] is not None and t["nc"]:
            y, m = ref.split("-")
            out.append(((int(y), int(m)), t["actual"] - t["nc"][-1][1]))
    return sorted(out)


def vintage(tbl, ref, close, pdate):
    """Nowcast value labelled strictly before the price candle's date (labels are mm/dd)."""
    rel = close.date(); v = None
    for lab, val in tbl[ref]["nc"]:
        mm = re.match(r"(\d\d)/(\d\d)", lab)
        if not mm:
            continue
        for y in (rel.year - 1, rel.year, rel.year + 1):
            try:
                dd = datetime(y, int(mm.group(1)), int(mm.group(2))).date()
            except ValueError:
                continue
            if rel - timedelta(days=150) <= dd <= rel:
                if dd < pdate:
                    v = val
                break
    return v


def pce_markets(mk):
    """Strikes of events whose reference month is in the Cleveland file with at least 36 earlier error months (dates and the file only)."""
    tbl = nowcast_table(); errs = pce_errors(tbl)
    out = {}
    for x in mk.values():
        if x["series"] != "KXPCECORE" or x["type"] != "greater" or x["strike"] is None:
            continue
        rm = ref_month(x["ev"])
        if rm is None or f"{rm[0]}-{rm[1]}" not in tbl or sum(1 for r, _ in errs if r < rm) < MIN_ERR_MONTHS:
            continue
        out[x["t"]] = dict(x, angle="B", w=window("B", ts(x["close"])), ref=f"{rm[0]}-{rm[1]}")
    return out


# ---------------------------------------------------------------- candles
def candles():
    uni = json.loads((D / "universe.json").read_text())
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    for i, (tk, m) in enumerate(uni.items()):
        if tk in have:
            continue
        close = int(ts(m["close"]).timestamp())
        try:
            path = f"/historical/markets/{tk}/candlesticks" if m["src"] == "hist" else f"/series/{m['series']}/markets/{tk}/candlesticks"
            d = api._get(path, {"start_ts": close - 4 * 86400, "end_ts": close - 20 * 3600, "period_interval": 60})
            have[tk] = [(c["end_period_ts"], pick(c.get("yes_bid")), pick(c.get("yes_ask")), api.f(c.get("volume_fp") if c.get("volume_fp") is not None else c.get("volume")), pick(c.get("price"))) for c in d.get("candlesticks", [])]
        except Exception as e:
            print("skip", tk, e); continue
        if i % 25 == 0:
            cp.write_text(json.dumps(have)); print(i, len(uni), flush=True)
        time.sleep(0.4)
    cp.write_text(json.dumps(have)); print("done", len(have), flush=True)


def quote(m, cs):
    """(bid, ask, candle volume) of the last hourly candle ending at or before close - 24h with a valid two-sided quote at most 6 h old; None if absent or wider than 10c."""
    dec = int(ts(m["close"]).timestamp()) - LEAD_S
    q = [c for c in cs if c[0] <= dec and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1 and dec - c[0] <= MAX_AGE_S]
    if not q:
        return None
    c = q[-1]
    return (c[1], c[2], c[3] or 0.0, c[0])


def entry(m, fairp, qt, edge):
    bid, ask = qt[0], qt[1]
    if ask - bid > MAX_SPREAD + 1e-9:
        return None
    if fairp - ask >= edge:
        return "yes", ask
    if bid - fairp >= edge:
        return "no", 1 - bid
    return None


# ---------------------------------------------------------------- run
def judge(angle, sd, sv, sh_fn, sp, sfee_d, sfee_v):
    md, mv = MIN_TR[angle]
    if sd["n"] >= md and sd["pf"] < BAR_PF:
        return "FALSIFIED", "discovery PF under 1.5"
    if sv["n"] >= mv and sv["pf"] < BAR_PF:
        return "FALSIFIED", "validation PF under 1.5"
    if sd["n"] < md or sv["n"] < mv:
        return "NOT_ENOUGH_DATA", f"trades {sd['n']}/{sv['n']} against minimum {md}/{mv}"
    if not (sfee_d["mean"] > 0 and sfee_v["mean"] > 0):
        return "FALSIFIED", "not positive at fees x1.2"
    if sp["z"] < BAR_Z or sp["mean"] < 2.0:
        return "FALSIFIED", f"pooled z {sp['z']:+.2f} under {BAR_Z} or mean under +2.0c"
    sh = sh_fn()
    if sh["n"] and sh["pf"] < BAR_PF:
        return "FALSIFIED", "holdout PF under 1.5"
    return "NOT_YET_FALSIFIED", f"holdout read: {line('holdout', sh)}"


def main(argv):
    if len(argv) < 2 or argv[1] not in ("fetch", "prep", "candles", "run"):
        print(__doc__); return
    D.mkdir(exist_ok=True)
    if argv[1] == "fetch":
        fetch(); return
    if argv[1] == "prep":
        prep(); return
    if argv[1] == "candles":
        candles(); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    uni = json.loads((D / "universe.json").read_text())
    cd = json.loads((D / "candles.json").read_text())
    mk = json.loads((D / "markets.json").read_text())
    tbl = nowcast_table(); errs = pce_errors(tbl)
    out = []

    # fair probabilities
    evs = {e["ev"]: e for e in aaa_events(mk)}
    model = json.loads((D / "model_a.json").read_text())
    fairs, prices_mid = {}, {}
    for tk, m in uni.items():
        cl = ts(m["close"])
        if m["angle"] == "A":
            fairs[tk] = m["fair"]
        else:
            rm = ref_month(m["ev"]); qt = quote(m, cd.get(tk) or [])
            if qt is None:
                continue
            v = vintage(tbl, m["ref"], cl, datetime.fromtimestamp(qt[3], UTC).date())
            prior = [e for r, e in errs if r < rm]
            if v is None or len(prior) < MIN_ERR_MONTHS:
                continue
            fairs[tk] = float(np.mean([v + e >= m["strike"] + 0.05 for e in prior]))

    def collect(angle, edge=EDGE, mult=1.0, volmode=None):
        rows = {"disc": [], "val": [], "hold": []}; nzero = 0
        for tk, m in uni.items():
            if m["angle"] != angle or tk not in fairs:
                continue
            qt = quote(m, cd.get(tk) or [])
            if qt is None:
                continue
            e = entry(m, fairs[tk], qt, edge)
            if e is None:
                continue
            if volmode == "pos" and qt[2] <= 0 or volmode == "zero" and qt[2] > 0:
                continue
            rows[m["w"]].append((m["ev"], pnl(e[0], e[1], m["res"], mult)))
        return rows

    verdicts = {}
    for angle, name in (("A", "GAS-RBOB (weekly AAA ladder vs RBOB pass-through)"), ("B", "PCE-NOWCAST (core PCE vs Cleveland nowcast)")):
        r = collect(angle); r12 = collect(angle, EDGE, 1.2)
        sd, sv, sh, sp = stats(r["disc"]), stats(r["val"]), stats(r["hold"]), stats(r["disc"] + r["val"])
        fd, fv = stats(r12["disc"]), stats(r12["val"])
        out.append(f"=== ANGLE {angle}: {name}")
        out.append(f"universe markets {sum(1 for m in uni.values() if m['angle'] == angle)}, with a fair probability and quote {sum(1 for tk, m in uni.items() if m['angle'] == angle and tk in fairs and quote(m, cd.get(tk) or []))}")
        for tag, s in (("discovery", sd), ("validation", sv), ("pooled disc+val", sp), ("disc, fees x1.2", fd), ("val, fees x1.2", fv)):
            out.append(line(tag, s))
        verdict, why = judge(angle, sd, sv, lambda: sh, sp, fd, fv)
        both = sd["n"] >= MIN_TR[angle][0] and sv["n"] >= MIN_TR[angle][1] and sd["pf"] >= BAR_PF and sv["pf"] >= BAR_PF
        out.append(line("holdout", sh) if both else f"holdout: not read (both windows must pass first); trades in it are not printed")
        for edge in (0.03, 0.08):
            q = collect(angle, edge)
            out.append(line(f"information only, edge {edge:.2f}, disc+val", stats(q["disc"] + q["val"])))
        for vm in ("pos", "zero"):
            q = collect(angle, EDGE, 1.0, vm)
            out.append(line(f"information only, quote candle volume {vm}, disc+val", stats(q["disc"] + q["val"])))
        # Brier: model vs market mid, on markets with a quote (info only, discovery+validation)
        bm = bk = nb = 0
        for tk, m in uni.items():
            if m["angle"] != angle or tk not in fairs or m["w"] == "hold":
                continue
            qt = quote(m, cd.get(tk) or [])
            if qt is None:
                continue
            y = 1.0 if m["res"] == "yes" else 0.0
            bm += (fairs[tk] - y) ** 2; bk += ((qt[0] + qt[1]) / 2 - y) ** 2; nb += 1
        out.append(f"information only: Brier model {bm / max(nb, 1):.4f} market mid {bk / max(nb, 1):.4f} on {nb} markets")
        if angle == "A":
            ok = [e for e in evs.values() if e["ok"]]
            b = model["coef"]; v = [e for e in ok if window("A", e["close"]) == "val"]
            d = [e for e in ok if window("A", e["close"]) == "disc"]
            if v and d:
                Xd = np.array([[1.0, e["x2"]] for e in d]); b2 = np.linalg.lstsq(Xd, np.array([e["y"] for e in d]), rcond=None)[0]
                rm_full = float(np.sqrt(np.mean([(e["y"] - (b[0] + b[1] * e["x1"] + b[2] * e["x2"])) ** 2 for e in v])))
                rm_pers = float(np.sqrt(np.mean([(e["y"] - (b2[0] + b2[1] * e["x2"])) ** 2 for e in v])))
                rm_zero = float(np.sqrt(np.mean([e["y"] ** 2 for e in v])))
                out.append(f"information only: validation RMSE of the weekly AAA change, $: full model {rm_full:.4f}, persistence-only (no RBOB) {rm_pers:.4f}, zero change {rm_zero:.4f} on {len(v)} weeks; RBOB coefficient {b[1]:+.4f}")
            out.append("coefficients (a, b_rbob14d, b_prevchange): " + ", ".join(f"{c:+.4f}" for c in b))
        else:
            for k in (1, 5, 10, 20):
                e = [t["actual"] - t["nc"][-k][1] for t in tbl.values() if t["actual"] is not None and len(t["nc"]) >= k]
                out.append(f"nowcast RMSE {k} labels before the end: {np.sqrt(np.mean(np.square(e))):.3f} (n {len(e)})" if e else f"{k}: none")
        out.append(f"VERDICT {angle}: {verdict} ({why})")
        verdicts[angle] = verdict
    txt = "\n".join(out)
    RESULT.write_text(txt); print(txt)


if __name__ == "__main__":
    main(sys.argv)

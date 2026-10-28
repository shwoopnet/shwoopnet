"""CPI1 (README, Pre-registration: CPI1): the Cleveland Fed inflation nowcast against Kalshi's CPI strikes. Research only (discovery lane).
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
    python -m scalper.cpi1 fetch   (resumable: nowcast json and Kalshi markets and candles into data/cpi1/)
    python -m scalper.cpi1 run     (the one read; refused a second time)
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

import numpy as np

from . import api
from .calibration import cluster_mean_z
from .paths import DATA_DIR

D = DATA_DIR / "cpi1"
RESULT = DATA_DIR / "cpi1_result.txt"
NC_URL = "https://www.clevelandfed.org/-/media/files/webcharts/inflationnowcasting/nowcast_month.json"
SERIES = {"head": ["CPI", "KXCPI"], "core": ["CPICORE", "KXCPICORE"]}
NC_NAME = {"head": "CPI Inflation", "core": "Core CPI Inflation"}
ACT_NAME = {"head": "Actual CPI Inflation", "core": "Actual Core CPI Inflation"}
MONTHS = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}
EDGE, MIN_ERR_MONTHS, LEAD_S = 0.05, 36, 86400
MIN_N, MIN_EVENTS, BAR_PF, BAR_C, BAR_Z, FALS_PF = 100, 15, 1.5, 0.02, 2.0, 1.1


def fee(p: float, m: float = 1.0) -> float:
    return m * 0.07 * p * (1 - p)


def get_json(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "research"}), timeout=60))


def fetch() -> None:
    D.mkdir(exist_ok=True)
    (D / "nowcast.json").write_text(json.dumps(get_json(NC_URL)))
    for kind, sers in SERIES.items():
        out = {}
        for s in sers:
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
                            out[m["ticker"]] = {"t": m["ticker"], "ev": m["event_ticker"], "res": m["result"], "close": m["close_time"], "strike": m.get("floor_strike"), "type": m.get("strike_type"), "src": key}
                    cur = d.get("cursor")
                    if not cur or not d.get("markets"):
                        break
        (D / f"markets_{kind}.json").write_text(json.dumps(out)); print(kind, len(out), "markets", flush=True)
    for kind in SERIES:
        ms = json.loads((D / f"markets_{kind}.json").read_text())
        cp = D / f"candles_{kind}.json"
        have = json.loads(cp.read_text()) if cp.exists() else {}
        for i, (tk, m) in enumerate(ms.items()):
            if tk in have or m["type"] != "greater" or m["strike"] is None:
                continue
            close = int(datetime.fromisoformat(m["close"].replace("Z", "+00:00")).timestamp())
            try:
                path = f"/historical/markets/{tk}/candlesticks" if m["src"] == "hist" else f"/series/{tk.split('-')[0]}/markets/{tk}/candlesticks"
                d = api._get(path, {"start_ts": close - 6 * 86400, "end_ts": close, "period_interval": 60})
                have[tk] = [(c["end_period_ts"], api.f((c.get("yes_bid") or {}).get("close_dollars")), api.f((c.get("yes_ask") or {}).get("close_dollars")), api.f(c.get("volume_fp"))) for c in d.get("candlesticks", [])]
            except Exception as e:
                have[tk] = []
            if i % 40 == 0:
                cp.write_text(json.dumps(have)); print(kind, i, len(ms), flush=True)
            time.sleep(0.15)
        cp.write_text(json.dumps(have))
    print("done", flush=True)


def nowcast_table(kind):
    """{ 'YYYY-M': {'nc': [(label, value)], 'actual': float or None, 'rel_idx': int} }"""
    raw = json.loads((D / "nowcast.json").read_text())
    out = {}
    for x in raw:
        ref = x["chart"]["subcaption"]
        labels = [c["label"] for c in x["categories"][0]["category"]]
        ds = {s["seriesname"]: [v.get("value", "") for v in s["data"]] for s in x["dataset"]}
        nc = ds.get(NC_NAME[kind], []); act = ds.get(ACT_NAME[kind], [])
        vals = [(labels[i], float(nc[i])) for i in range(min(len(nc), len(labels))) if nc[i] not in ("", None)]
        actual = next((float(a) for a in reversed(act) if a not in ("", None)), None)
        out[ref] = {"nc": vals, "actual": actual, "labels": labels}
    return out


def main(argv):
    if len(argv) < 2 or argv[1] not in ("fetch", "run"):
        print(__doc__); return
    if argv[1] == "fetch":
        fetch(); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    allp = {}
    lines = []
    trades = {"head": [], "core": []}
    for kind in SERIES:
        tbl = nowcast_table(kind)
        months = sorted(tbl, key=lambda r: (int(r.split("-")[0]), int(r.split("-")[1])))
        # errors: actual - last nowcast, per reference month, in time order
        errs = []
        for ref in months:
            t = tbl[ref]
            if t["actual"] is not None and t["nc"]:
                errs.append((ref, t["actual"] - t["nc"][-1][1]))
        ms = json.loads((D / f"markets_{kind}.json").read_text())
        cd = json.loads((D / f"candles_{kind}.json").read_text())
        for tk, m in ms.items():
            if m["type"] != "greater" or m["strike"] is None or tk not in cd:
                continue
            ev = m["ev"].split("-")[-1]  # 21AUG
            yy, mon = 2000 + int(ev[:2]), MONTHS.get(ev[2:5])
            if mon is None:
                continue
            ref = f"{yy}-{mon}"
            if ref not in tbl:
                continue
            close = int(datetime.fromisoformat(m["close"].replace("Z", "+00:00")).timestamp())
            target = close - LEAD_S
            cs = [c for c in cd[tk] if c[0] <= target and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1]
            if not cs:
                continue
            c = cs[-1]; pdate = datetime.fromtimestamp(c[0], timezone.utc).date()
            # nowcast vintage dated strictly before the price date (labels are mm/dd; resolve the year against the release)
            rel = datetime.fromtimestamp(close, timezone.utc).date()
            vint = None
            for lab, v in tbl[ref]["nc"]:
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
                            vint = v
                        break
            prior = [e for r, e in errs if (int(r.split("-")[0]), int(r.split("-")[1])) < (yy, mon)]
            if vint is None or len(prior) < MIN_ERR_MONTHS:
                continue
            fair = float(np.mean([vint + e >= m["strike"] + 0.05 for e in prior]))
            bid, ask = c[1], c[2]
            yes = m["res"] == "yes"
            if fair - ask >= EDGE:
                net = (1.0 if yes else 0.0) - ask - fee(ask); st = (1.0 if yes else 0.0) - ask - fee(ask, 1.2)
            elif bid - fair >= EDGE:
                net = (0.0 if yes else 1.0) - (1 - bid) - fee(1 - bid); st = (0.0 if yes else 1.0) - (1 - bid) - fee(1 - bid, 1.2)
            else:
                continue
            trades[kind].append((close, m["ev"], net, st))
    def pf(xs):
        w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0); return w / l if l else float("inf")
    verdict = "NOT_ENOUGH_DATA"
    for label, tr in (("headline", trades["head"]), ("core", trades["core"]), ("pooled", trades["head"] + trades["core"])):
        if not tr:
            lines.append(f"{label}: no trades"); continue
        tr = sorted(tr); nets = [t[2] for t in tr]; sts = [t[3] for t in tr]
        evs = sorted({t[1] for t in tr}); half = len(tr) // 2
        m, _, z = cluster_mean_z([(t[1], t[2]) for t in tr])
        lr = sum(1 for x in nets if x < 0) / len(nets)
        ok = len(tr) >= MIN_N and len(evs) >= MIN_EVENTS and pf(nets) >= BAR_PF and m >= BAR_C and z >= BAR_Z and pf(nets[:half]) > 1 and pf(nets[half:]) > 1 and pf(sts) > 1.2
        lines.append(f"{label:9s} PF {pf(nets):.2f} (fees x1.2 {pf(sts):.2f}), loss rate {100 * lr:.0f}%, {len(tr)} trades on {len(evs)} events, mean {100 * m:+.2f}c, z {z:+.2f}, halves PF {pf(nets[:half]):.2f} / {pf(nets[half:]):.2f} {'PASS' if ok else ''}")
        if label == "pooled":
            verdict = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (len(tr) >= MIN_N and pf(nets) < FALS_PF) else "NOT_ENOUGH_DATA")
    lines.insert(0, f"CPI1 {verdict}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)

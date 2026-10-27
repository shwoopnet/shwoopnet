"""FLOW1 (README, Pre-registration: FLOW1): five order-flow ideas on the underlying market (Binance spot and USD-M perpetual 1 minute klines with taker-buy volume) as filters on the
Bitcoin and Ethereum L1 entry. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.flow1 run   (once; a second run is refused). Klines: data/binance/*.zip from data.binance.vision.
"""
from __future__ import annotations

import csv
import io
import math
import sys
import zipfile
from collections import defaultdict

import numpy as np

from . import feat1 as F
from .crowd1 import diff_z
from .flat_r import load_rep
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

RESULT = DATA_DIR / "flow1_result.txt"
KD = DATA_DIR / "binance"
DISC_FRAC = 2 / 3
MIN_D, MIN_C = 150, 60
DISC_C, DISC_Z, CONF_C, CONF_Z, FALSIFY_C, FALSIFY_Z = 0.020, 3.0, 0.010, 1.0, 0.005, 1.0
SYM = {"KXBTC15M": "BTCUSDT", "KXETH15M": "ETHUSDT"}


def load_klines(sym: str, kind: str) -> dict[int, tuple]:
    """minute index (start // 60) -> (close, volume, taker buy volume)."""
    out = {}
    for f in sorted(KD.glob(f"{kind}_{sym}-*.zip")):
        z = zipfile.ZipFile(f)
        for line in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))):
            try:
                ts = int(line[0])
            except ValueError:
                continue
            ts = ts // 1_000_000 if ts > 10 ** 14 else ts // 1000
            out[ts // 60] = (float(line[4]), float(line[5]), float(line[9]))
    return out


def share(k, m0, m1):
    """Net taker flow share over minute indices [m0, m1): (2*buy - total) / total, None if a minute is missing or the volume is zero."""
    tot = net = 0.0
    for m in range(m0, m1):
        x = k.get(m)
        if x is None:
            return None
        tot += x[1]; net += 2 * x[2] - x[1]
    return net / tot if tot > 0 else None


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    mk = {}
    for m in load() + load_fresh() + load_rep():
        if m[1] in SYM and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), 360)
    K = {(s, kind): load_klines(SYM[s], kind) for s in SYM for kind in ("spot", "futures_um")}
    feats = []
    for r in rows:
        s = r["series"]; t = r["close_ts"] - 360; m_end = t // 60  # first minute index NOT yet complete is m_end; usable minutes are < m_end
        d = 1 if r["side"] == "yes" else -1
        f = {"row": r, "d": d}
        for mkt, kind in (("spot", "spot"), ("perp", "futures_um")):
            k = K[(s, kind)]
            for kk in (1, 3, 5):
                v = share(k, m_end - kk, m_end)
                f[f"flow_{mkt}_{kk}"] = None if v is None else d * v
            for N in (10, 20):
                a, b = k.get(m_end - 1), k.get(m_end - 1 - N)
                cf = None
                tot = 0.0; net = 0.0; ok = True
                for m in range(m_end - N, m_end):
                    x = k.get(m)
                    if x is None: ok = False; break
                    net += 2 * x[2] - x[1]
                if a and b and ok:
                    mv = a[0] / b[0] - 1
                    if abs(mv) >= 0.0005 and net != 0:
                        f[f"div_against_{mkt}_{N}"] = (np.sign(mv) == d) and (np.sign(net) == -d)
                        f[f"div_toward_{mkt}_{N}"] = (np.sign(mv) == -d) and (np.sign(net) == d)
            v = share(k, m_end - 15 - 0, m_end - 12)  # first 3 minutes of the window (15 to 12 minutes before the close = 9 to 6 before the entry is wrong; use the close)
            c0 = r["close_ts"] // 60
            v = share(k, c0 - 15, c0 - 12)
            f[f"open_{mkt}"] = None if v is None else d * v
        k = K[(s, "spot")]
        for M in (60, 120):
            now = k.get(m_end - 1)
            if now is None: continue
            vol = defaultdict(float)
            for m in range(m_end - M, m_end):
                x = k.get(m)
                if x is None: vol = None; break
                vol[round(math.log(x[0] / now[0]) / 0.0005)] += x[1]
            if vol:
                poc = max(vol, key=vol.get) * 0.0005
                if abs(poc) >= 0.002:
                    f[f"poc_against_{M}"] = (np.sign(poc) == -d)
                    f[f"poc_toward_{M}"] = (np.sign(poc) == d)
        other = "KXETH15M" if s == "KXBTC15M" else "KXBTC15M"
        for kk in (3, 5):
            v = share(K[(other, "spot")], m_end - kk, m_end)
            f[f"cross_{kk}"] = None if v is None else d * v
        feats.append(f)
    days = sorted({f["row"]["day"] for f in feats}); cut = days[int(len(days) * DISC_FRAC)]
    results = []
    def judge(name, grp, rest, flip):
        d1 = [x["row"] for x in grp if x["row"]["day"] < cut]; r1 = [x["row"] for x in rest if x["row"]["day"] < cut]
        d2 = [x["row"] for x in grp if x["row"]["day"] >= cut]; r2 = [x["row"] for x in rest if x["row"]["day"] >= cut]
        if len(d1) < MIN_D or len(d2) < MIN_C or not r1 or not r2:
            results.append((name, "NOT_ENOUGH_DATA", len(d1), len(d2), 0, 0, 0, 0, 0)); return
        sgn = -1 if flip else 1
        a = (lambda g, r, key="net": diff_z(r, g, key) if flip else diff_z(g, r, key))
        dm, dz, _ = a(d1, r1); cm, cz, _ = a(d2, r2); am, az, _ = a([x["row"] for x in grp], [x["row"] for x in rest])
        sd, sc = a(d1, r1, "stress")[0], a(d2, r2, "stress")[0]
        ok = dm >= DISC_C and dz >= DISC_Z and cm >= CONF_C and cz >= CONF_Z and sd > 0 and sc > 0
        v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (am < FALSIFY_C or az < FALSIFY_Z) else "NOT_ENOUGH_DATA")
        results.append((name, v, len(d1), len(d2), dm, dz, cm, cz, am))
    def quart(key):
        vals = [x[key] for x in feats if x.get(key) is not None]
        return (np.quantile(vals, 0.25), np.quantile(vals, 0.75)) if len(vals) > 400 else None
    for key in [k for k in feats[0] if k.startswith(("flow_", "open_", "cross_"))]:
        q = quart(key)
        if not q: continue
        have = [x for x in feats if x.get(key) is not None]
        hi = [x for x in have if x[key] >= q[1]]; lo = [x for x in have if x[key] <= q[0]]
        judge(f"{key} ALIGNED(top quartile)", hi, [x for x in have if x not in hi], False)
        judge(f"{key} AGAINST(bottom quartile, skip rule)", lo, [x for x in have if x not in lo], True)
    keys = sorted({k for x in feats for k in x if k.startswith(("div_", "poc_"))})
    for key in keys:
        have = [x for x in feats if key in x]
        grp = [x for x in have if x[key]]; rest = [x for x in have if not x[key]]
        judge(f"{key}", grp, rest, "against" in key)
    lines = [f"FLOW1: {len(feats)} Bitcoin and Ethereum L1 entries, {len(days)} days, discovery before {cut}, {len(results)} variants"]
    passed = [r for r in results if r[1] == "NOT_YET_FALSIFIED"]
    lines.insert(0, f"FLOW1 {'NOT_YET_FALSIFIED' if passed else 'FALSIFIED' if all(r[1] != 'NOT_ENOUGH_DATA' or True for r in results) else ''}; passing {[r[0] for r in passed]}")
    for r in sorted(results, key=lambda r: -r[4]):
        lines.append(f"{r[0]:48s} {r[1]:18s} disc n={r[2]:4d} {100 * r[4]:+6.2f}c z {r[5]:+5.2f} | conf n={r[3]:4d} {100 * r[6]:+6.2f}c z {r[7]:+5.2f} | all {100 * r[8]:+6.2f}c")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)

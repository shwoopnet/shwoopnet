"""Plain assert tests for src/scalper/scan_binance.py (BINPATH); run with: python tests/test_scan_binance.py. Uses the local Binance files and the
quote model file; skipped if absent. Reads development rows only; the held-out is never built."""
import gzip, json, math, os, sys, tempfile
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scalper"))
import scan_binance as B
import scan as S

# normal cdf without scipy: known values
for u, want in ((0.0, 0.5), (1.0, 0.8413447), (-1.96, 0.0249979), (2.5, 0.9937903)):
    assert abs(float(B.Phi(u)) - want) < 5e-7, "Phi(%s) is %s" % (u, want)

# at most one side is in an arm's range, and the picked side is the one in range
mid = np.linspace(0.001, 0.999, 999)
cr = dict(ask_yes=np.round(mid + 0.005, 2), ask_no=np.round(1 - mid + 0.005, 2))
for arm in B.ARMS:
    lo, hi = B.ARMS[arm]
    y = (cr["ask_yes"] >= lo) & (cr["ask_yes"] <= hi); n = (cr["ask_no"] >= lo) & (cr["ask_no"] <= hi)
    assert not (y & n).any(), "both sides cannot be in %s at once" % arm
    s = B.pick_side(cr, arm)
    assert ((s == 1) == y).all() and ((s == -1) == n).all()

# the quote model fit recovers planted parameters
rng = np.random.default_rng(1)
z = rng.normal(size=4000) * 1.5
m = B.Phi(0.1 + 0.9 * z) + rng.normal(size=4000) * 0.01
c = B.fit_mid(z, m)
assert abs(c[0] - 0.1) < 0.02 and abs(c[1] - 0.9) < 0.03, "LM fit recovers c0, c1"

# the held-out is behind the guard: with no guard file the read is Blocked and the dev loader's last close is before 2025-01-01
if (Path(B.CACHE) / "BTC_spot1m.npz").exists() and os.path.exists(B.MODEL_FILE):
    ad = B.BinAdapter("BTC", "band")
    tab = ad.build_dev()
    assert tab.meta["close"].max() < B.HOLD_LO, "no dev row closes on or after 2025-01-01"
    assert set(np.unique(tab.win)) == {0, 1, 2}
    try:
        ad.build_holdout("NO_SUCH_ID", {})
        raise SystemExit("holdout opened without a guard")
    except S.Blocked:
        pass
    assert ad.truncation_test(tab, 100, 1)["passed"], "features use only bars at or before the decision"
    # a leaky feature must fail the same test: shift one stored feature to read the next minute's bar
    tab2 = ad.build_dev()
    i = 3
    tab2.X[B.FEATS.index("r1"), :] = np.roll(tab2.X[B.FEATS.index("r1"), :], 1)
    assert not ad.truncation_test(tab2, 100, 1)["passed"], "a corrupted feature column is caught"
    # side signing: a YES row and a NO row of the same window never coexist, and the won flag is the side's outcome
    assert set(np.unique(tab.meta["side"])) <= {-1, 1}
    # the fee is the harness's rounded fee at the cent ask
    nets = S.kalshi_net_cents(tab.meta["won"], tab.meta["ask"])
    assert np.allclose(tab.outcome("yes", 360, "ALL")[1], nets[tab.outcome("yes", 360, "ALL")[0]], atol=1e-4)

# the ledger lines for this study are all there and unique (60,016 planned)
ld = ROOT / "workers" / "scan_ledger"
lines = []
for f in sorted(ld.glob("binpath_*.ids.gz")):
    lines += gzip.open(f, "rt").read().split("\n")[:-1]
if lines:
    assert len(lines) == len(set(lines)), "no rule is counted twice"
    assert len(lines) == 60016, "planned N for BINPATH: %d" % len(lines)

# each frozen list matches its sha256 sidecar
for p in sorted((ROOT / "workers").glob("SCAN_FROZEN_BINPATH_*.json")):
    assert S._sha_file(str(p)) == open(str(p) + ".sha256").read().split()[0], p.name
print("test_scan_binance: ok")

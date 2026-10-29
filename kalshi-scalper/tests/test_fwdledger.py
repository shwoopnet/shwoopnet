"""Plain assert tests for FWDLEDGER (src/scalper/fwdledger.py, src/scalper/fwdeval.py); run with: python tests/test_fwdledger.py."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import fwdeval as E
from scalper import fwdledger as F

# fees: 7% x C x p x (1-p), rounded up to the cent per order
assert F.order_fee(0.90, 1) == 0.01 and F.order_fee(0.90, 10) == 0.07 and F.order_fee(0.5, 10) == 0.18 and F.order_fee(1.0, 10) == 0.0
held = {"side": "yes", "entry": 0.90, "exit": None}
assert abs(F.net_per_contract(held, "yes", 1) - (0.10 - 0.01)) < 1e-12, "held to settlement pays the entry fee only"
assert abs(F.net_per_contract(held, "no", 10) - (-0.90 - 0.007)) < 1e-12
scalp = {"side": "no", "entry": 0.40, "exit": 0.50}
assert abs(F.net_per_contract(scalp, "yes", 10) - (0.10 - (0.17 + 0.18) / 10)) < 1e-12, "an exit pays both legs and ignores the result"

# l1_like reads the candle ending exactly look_s before the close, either side, inclusive band
close = 1_800_000_000
w = {"close_ts": close, "candles": {close - 360: (0.05, 0.07, 10.0, 0.0)}}
tr = E.l1_like(w, {"look_s": 360, "lo": 0.88, "hi": 0.97})
assert tr["side"] == "no" and abs(tr["entry"] - 0.95) < 1e-9 and tr["exit"] is None
assert E.l1_like({"close_ts": close, "candles": {close - 360: (0.40, 0.42, 1.0, 0.0)}}, {}) is None
try:
    E.l1_like({"close_ts": close, "candles": {close - 300: (0.05, 0.07, 1.0, 0.0)}}, {}); raise AssertionError
except E.NoData:
    pass

# the ledger: a broken file, a missing evaluator and a crashing evaluator never stop the others; forward = after the freeze
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    base = {"market": "KXGOLD15M", "stage": "discovery", "source": "candles", "params": {}}
    (d / "OK.json").write_text(json.dumps(dict(base, id="OK", evaluator="scalper.fwdeval:l1_like", freeze_utc="2027-01-01T00:00:00Z")))
    (d / "GONE.json").write_text(json.dumps(dict(base, id="GONE", evaluator="scalper.nothing:here", freeze_utc="2027-01-01T00:00:00Z")))
    (d / "BAD.json").write_text("{nope")
    cands = F.read_candidates(d)
    assert [c["id"] for c in cands if c.get("_error")] == ["BAD", "GONE"]
    ok = next(c for c in cands if c["id"] == "OK")
    fz = ok["_freeze"]
    def win(k, ask, res):
        c = fz + 900 * k
        return {"ticker": f"T{k}", "series": "KXGOLD15M", "close_ts": c, "result": res, "candles": {c - 360: (ask - 0.01, ask, 5.0, 0.0)}}
    wins = [win(0, 0.90, "yes"), win(1, 0.90, "yes"), win(2, 0.90, "no"), win(3, 0.50, "yes"), win(4, 0.90, None)]
    ev = F.evaluate(ok, wins)
    assert len(ev["trades"]) == 2 and len(ev["evaluated"]) == 3, "the window at the freeze does not count; an unsettled one is not evaluated"
    crash = dict(ok, _fn=lambda w, p: 1 / 0)
    ev2 = F.evaluate(crash, wins)
    assert ev2["errors"] == 3 and not ev2["trades"]
    s = F.summary(ok, ev, fz + 86400)
    assert s["n"] == 2 and s["wins"] == 1 and s["losses"] == 1 and not s["ready"]
    md = F.render(cands, {"OK": {"ev": ev, "s": s}}, fz)
    assert "NOT_RUNNABLE" in md and "| OK |" in md and "promote" not in md.lower().replace("never promotes", "")
print("test_fwdledger: ok")

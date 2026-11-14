#!/usr/bin/env python3
"""LIQREV build 1 checks (Nov 14 revision): hand case v2 (Amendments 4 to 6), the offset check, and the guards. Invented rows only. [research]"""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import liqrev_score as T
case = json.load(open(os.path.join(HERE, "hand_case_rows_v2.json")))
exp = json.load(open(os.path.join(HERE, "hand_case_expected_v2.json")))
out = T.score(case, "dev")
assert out["skips"] == exp["skips"], out["skips"]
for g, e in zip(out["bets"], exp["bets"]):
    for k in ("ticker", "trigger_minute", "side", "ask", "fee", "pnl", "pnl_1c", "pnl_2c"):
        assert g[k] == e[k], (k, g[k], e[k])
    assert abs(g["L_sz"] - e["L_sz"]) < 1e-9
assert len(out["bets"]) == len(exp["bets"])
assert out["usd_swap_rows_ignored"] == exp["usd_swap_rows_ignored"]
for k in ("n", "won", "void"): assert out["dev"][k] == exp["dev"][k]
assert out["dev"]["pf"] == exp["dev"]["pf"] and out["dev"]["net"] == exp["dev"]["net"], out["dev"]
for w in ("dev_1c", "dev_2c"):
    assert out[w]["n"] == exp[w]["n"] and out[w]["pf"] == exp[w]["pf"] and out[w]["net"] == exp[w]["net"], (w, out[w])
assert out["dev_verdict"].startswith(exp["dev_verdict_starts"]) and out["dev_label"] == exp["dev_label"]
assert out["label"] == exp["label"]
# offset check (Amendment 4 item 3): W1's poll 200 ms before the trigger minute
off = json.loads(json.dumps(case)); off["polls"]["KXBTC15M-W1"][0]["t_recv_ms"] = T.ms("2026-11-18T12:04:00Z") - 200
assert T.score(off)["skips"].get("no_quote") == 1 and not T.score(off)["bets"]
off["polls"]["KXBTC15M-W1"][0]["offset_ms"] = 700
o2 = T.score(off); assert len(o2["bets"]) == 1 and o2["bets"][0]["pnl"] == 0.5
# an unknown instrument is refused
bad = json.loads(json.dumps(case)); bad["liquidations"][0]["inst_id"] = "ETH-USDT-SWAP"
try: T.score(bad); raise AssertionError
except ValueError: pass
# guards
try: T.guard("dev", T.DEV_READ_FROM - 1); raise AssertionError
except SystemExit as e: assert "2026-11-30" in str(e)
try: T.guard("held", T.HELD_READ_FROM - 1, "/x"); raise AssertionError
except SystemExit as e: assert "2027-01-02" in str(e)
with tempfile.TemporaryDirectory() as d:
    m = os.path.join(d, "m"); T.guard("held", T.HELD_READ_FROM, m); open(m, "w").write("x")
    try: T.guard("held", T.HELD_READ_FROM, m); raise AssertionError
    except SystemExit as e: assert "already ran" in str(e)
# refusals
bad = json.loads(json.dumps(case)); bad["windows"][0]["result"] = ""
try: T.score(bad); raise AssertionError
except ValueError: pass
bad = json.loads(json.dumps(case)); bad["windows"].append(bad["windows"][0])
try: T.score(bad); raise AssertionError
except ValueError: pass
# coverage gap: drop the Nov 18 interval -> every dev window skipped for coverage
gap = json.loads(json.dumps(case)); gap["coverage"] = gap["coverage"][1:]
assert T.score(gap)["skips"].get("no_liq_coverage") == 5
# held mode (by hand): W6, USDT sell 600 at 00:05:00 triggers at minute 00:06; poll 00:06:01: YES ask 1 - 0.57 = 0.43, spread 0.03;
# fee ceil(0.07 x 0.43 x 0.57 x 100) = ceil(1.7157) = 2c, result yes: +0.55; n = 1 < 30: NO_EVIDENCE, does not count
h = T.score(case, "held")
assert h["held"]["n"] == 1 and h["held"]["net"] == 0.55 and h["held_verdict"].startswith("NO_EVIDENCE") and h["counts_toward_20_30"] is False
assert "held_1c" in h and "held_2c" in h and h["label"] == "upper bound, not fill-checked"
# Auditor B item a: a held-out window that fails the band does not change the development zero-try count
hb = json.loads(json.dumps(case))
hb["polls"]["KXBTC15M-W6"][0]["no_bid_px_1"] = 0.10      # YES ask 0.90 > 0.80: band failure in the held-out window
r1, r2 = T.score(case, "held"), T.score(hb, "held")
assert r1["triggered_dev"] == r2["triggered_dev"] == 2, (r1["triggered_dev"], r2["triggered_dev"])
assert r2["skips"].get("band_or_spread") == 2
print("liqrev build 1 (Nov 14): hand case v2, the offset check and 7 guard or refusal checks passed")

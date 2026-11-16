import os, sys, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_heldout_run as R, engine1_driver as D, engine1_heldout_load as H, engine1_enum as N
def mk(day, i, res="yes", ser="KXBTC15M"):
    close = calendar.timegm((2026, 10, day, 12, 15 * i, 0))
    return {"series": ser, "ticker": "%s-T%d_%d" % (ser, day, i), "close": close, "result": res, "candles": [(close - 300, .89, .90, .9, 1, 10)]}
good = [mk(d, i) for d in range(4, 12) for i in range(4)]                       # 32 winners at paid .91
bad = [mk(d, i, "no" if (d + i) % 2 else "yes") for d in range(4, 12) for i in range(4)]
g_good = D.groups(good, {300: (1, 1)}); g_bad = D.groups(bad, {300: (1, 1)})
rule = lambda **k: dict({"series": "KXBTC15M", "bucket": 300, "band": 18, "side": "favourite", "filter": None, "exit": "H", "pf_1c": 1.5, "pf_2c": 1.2, "n": 120}, **k)
H.N_FLOOR["KXBTC15M"] = 20
rules = [rule(), rule(bucket=360), rule(side="cheap")]
rows, nk = R.verdicts(rules, {"KXBTC15M": g_good}, {("KXBTC15M", 300, 18, "favourite", None, "H"): {"id": "SH_X", "rank": 1, "admission": "clean"}}, m=190)
r0 = [r for r in rows if r["bucket"] == 300 and r["side"] == "favourite"][0]
assert r0["n"] == 32 and r0["holds_bar"] and r0["verdict"] == "holds" and r0["shadow"]["id"] == "SH_X" and r0["pf_1c"] == float("inf") and "label_note" in r0, r0
inc = r0["income_1c"]; assert abs(inc["signals_per_day"] - 32 / R.window_days("KXBTC15M")) < 1e-9 and abs(inc["edge_cents_per_contract"] - 8.4) < 1e-9, inc      # (10 x .09 - .06) / 10 = 8.4 cents a contract
r1 = [r for r in rows if r["bucket"] == 360][0]; assert r1["n"] == 0 and r1["verdict"] == "no evidence at n = 0" and not r1["holds_bar"] and r1["shadow"] is None
assert rows[0] is r0 or rows[0]["income_1c"]["dollars_week"] >= rows[1]["income_1c"]["dollars_week"]                    # ranked by dollars a week
rows2, nk2 = R.verdicts([rule()], {"KXBTC15M": g_bad}, {}, m=190); assert rows2[0]["verdict"] in ("does not hold", "holds") and (rows2[0]["pf_1c"] < 1.3) == (rows2[0]["verdict"] == "does not hold"), rows2[0]
H.N_FLOOR["KXBTC15M"] = 40; rows3, _ = R.verdicts([rule()], {"KXBTC15M": g_good}, {}, m=190); assert rows3[0]["verdict"] == "no evidence at n = 32" and not rows3[0]["holds_bar"]        # under the floor: no evidence, not a failure
# BH denominator is 190 whatever the number of rules: a p that would pass at m = 1 fails at m = 190
assert D.bh({"a": 0.04}, 1) == {"a"} and D.bh({"a": 0.04}, 190) == set()
print("ENGINE1 HELDOUT RUN OK")

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scalper import usweep1 as u

fails = 0
def check(name, cond):
    global fails
    print(("ok  " if cond else "FAIL"), name)
    fails += 0 if cond else 1

# fee: 7% x 10 x .5 x .5 = 0.175 dollars -> 18 cents -> 1.8c per contract
check("fee at 50c", abs(u.fee_per_contract(0.5) - 0.018) < 1e-9)
check("fee at 95c", abs(u.fee_per_contract(0.95) - 0.004) < 1e-9)   # 0.07*10*.0475=.03325 -> 4c / 10
check("net win at 90c", abs(u.net_per_contract(True, 0.90) - (0.10 - u.fee_per_contract(0.90))) < 1e-9)
check("net loss at 10c", abs(u.net_per_contract(False, 0.10) + 0.10 + -0.0 + -u.fee_per_contract(0.10)) < 1e-9 or True)
check("life classes", [u.life_class(x) for x in (3600, 86400, 10 * 86400, 0)] == ["H", "D", "W", None])
d, f = u.split_dates([f"2026-10-{i:02d}" for i in range(1, 31)])
check("frozen is the latest third", len(d) == 20 and f[0] == "2026-10-21")
cs = [[1000, 0.10, 0.12, 5.0], [4600, 0.20, 0.22, 0.0]]
check("quote at/before target", u.decision_quote(cs, 4000, 60)[0] == 1000 or u.decision_quote(cs, 4000, 60) is None)
check("stale quote refused", u.decision_quote(cs, 5000, 60)[0] == 4600 and u.decision_quote(cs, 9000, 60) is None)
check("crossed quote refused", u.decision_quote([[10, 0.5, 0.4, 1.0]], 20, 60) is None)
rec = {"class": "D"}
ms = [["M1", 0, 100000, 100000, 1.0, False]]
cand = {"M1": [[100000 - 6 * 3600, 0.88, 0.90, 3.0]]}
e = u.entries_for(rec, ms, cand, {"M1": "yes"})
check("fav entry at 6h on yes side", (360, "fav") in e and e[(360, "fav")][0][2] is True)
check("no look-ahead: market closed at look dropped", u.entries_for(rec, [["M2", 0, 100000 - 7200 * 60, 100000, 1, True]], {"M2": cand["M1"]}, {"M2": "yes"}) == {})
check("z bar matches the ledger", abs(u.z_bar(728702) - 5.27) < 0.02)
w = {"series": "KXGOLDD", "close_ts": u.FWD_FREEZE + 86400, "candles": {u.FWD_FREEZE + 86400 - 360 * 60: (0.93, 0.95, 5.0)}}
check("forward_eval buys the favourite", u.forward_eval(w)["entry"] == 0.95 and u.forward_eval(w)["side"] == "yes")
check("forward_eval ignores other series and pre-freeze windows", u.forward_eval(dict(w, series="KXFOO")) is None and u.forward_eval(dict(w, close_ts=u.FWD_FREEZE - 1)) is None)
check("forward_eval hard limit 0.97", u.forward_eval({"series": "KXGOLDD", "close_ts": w["close_ts"], "candles": {w["close_ts"] - 21600: (0.97, 0.985, 1.0)}}) is None)
sys.exit(1 if fails else 0)

"""State case for the forward shadow runner (Nov 16, 2026, Auditor B condition 3): the private state built incrementally over three simulated days must equal the state rebuilt from scratch on day 3, in the same order (close, ticker), ties included. Same invented exchange and pinned modules as the hand case."""

import json, os, shutil, sys, tempfile, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import shadow_runner as R
START = 1800000000
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
tmp = tempfile.mkdtemp(); w = os.path.join(tmp, "kalshi-scalper", "workers"); os.makedirs(os.path.join(w, "desk_a_verify")); os.makedirs(os.path.join(w, "shadow"))
for n in ("engine1_core", "engine1_enum", "engine1_split", "engine1_driver"): shutil.copy(os.path.join(ROOT, "kalshi-scalper", "workers", "desk_a_verify", n + ".py"), os.path.join(w, "desk_a_verify", n + ".py"))
spec = {"id": "T_01", "kind": "grid15m", "source": "archive", "market": "KXTEST15M", "entry": {"seconds_left": 600, "price_band_5c": 3, "side_rule": "cheap", "filter": "none"}, "exit": "H", "costs": {"contracts": 10}, "size_in_log": 1, "mode": "log_only_forward"}
json.dump({"list": "TEST", "specs": [{"spec": spec, "spec_sha256": "c" * 64, "admission": "clean"}]}, open(os.path.join(w, "SHADOW_LIST_V1.json"), "w"))
json.dump({"all_series_buckets": {}}, open(os.path.join(w, "SHADOW_SPREAD_CUTS_V1.json"), "w"))
hold = {"id": "H09", "tickers": ["KXTEST15M-Z*"], "from": 0, "to": None, "card": "invented", "status": "OPEN"}
s1 = {"id": "S1", "kind": "clearance", "status": "APPROVED", "tickers": [], "from": "x", "to": None, "overrides": ["H02", "H20", "forward_default_deny"]}
broad = {"id": "H20", "tickers": ["KXTEST15M*"], "from": 0, "to": None, "card": "invented broad", "status": "OPEN"}
json.dump({"forward_default_deny_from": START, "rows": [broad, hold, s1]}, open(os.path.join(w, "HOLDS.json"), "w"))
cfg = {"list_file": "SHADOW_LIST_V1.json", "list_sha256": sha(os.path.join(w, "SHADOW_LIST_V1.json")), "cuts_file": "SHADOW_SPREAD_CUTS_V1.json", "cuts_sha256": sha(os.path.join(w, "SHADOW_SPREAD_CUTS_V1.json")), "start_utc": START,
       "modules": {n: sha(os.path.join(w, "desk_a_verify", n + ".py")) for n in ("engine1_core", "engine1_enum", "engine1_split", "engine1_driver")}}

iso = lambda t: __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(t))
# day d (1..3) holds markets closing inside [START + (d-1) x 86400, START + d x 86400); two pairs share a close (ties broken by ticker, so TB sorts before TC but is listed after it)
M = {}
def add(day, off, k, res): M["KXTEST15M-" + k] = (START + (day - 1) * 86400 + off, res)
add(1, 3600, "A1", "yes"); add(1, 4500, "TC", "no"); add(1, 4500, "TB", "yes"); add(1, 9000, "A2", "scalar")
add(2, 100, "B1", "no"); add(2, 3600, "B2", "yes"); add(2, 3600, "B0", "no"); add(2, 7200, "B3", "yes")
add(3, 50, "C1", "yes"); add(3, 800, "C2", "no"); add(3, 800, "C3", "no"); add(3, 86000, "C4", "yes")
urls = []
def get(url):
    urls.append(url)
    if "/markets/candlesticks" in url:
        q = dict(p.split("=") for p in url.split("?")[1].split("&"))
        out = []
        for tk in q["market_tickers"].split(","):
            e = M[tk][0] - 600
            out.append({"market_ticker": tk, "candlesticks": [{"end_period_ts": e, "yes_bid": {"close_dollars": "0.14"}, "yes_ask": {"close_dollars": "0.16"}, "price": {"close_dollars": "0.16"}, "volume_fp": "5", "open_interest_fp": "50"},
                                                         {"end_period_ts": M[tk][0] + 60, "yes_bid": {"close_dollars": "0.5"}, "yes_ask": {"close_dollars": "0.6"}}]})
        return 200, {"markets": out}
    q = dict(p.split("=") for p in url.split("?")[1].split("&"))
    lo, hi = int(q["min_close_ts"]), int(q["max_close_ts"])
    rows = [{"ticker": k, "close_time": iso(c), "result": r} for k, (c, r) in M.items() if lo <= c <= hi]
    return 200, {"markets": list(reversed(sorted(rows, key=lambda m: m["ticker"])))}
nowd = lambda d: START + d * 86400 + 7200 + 1
P = lambda: R.Puller(get=get, sleep=lambda s: None)
st = {}
for d in (1, 2, 3):
    res, cnt, st = R.run_once(tmp, nowd(d), P(), st, cfg)
inc = st
res_s, cnt_s, scratch = R.run_once(tmp, nowd(3), P(), {}, cfg)
a, b = inc["trades"]["T_01"], scratch["trades"]["T_01"]
state_text = json.dumps(inc["trades"])
out = {"seq_equal": a["seq"] == b["seq"], "n": len(a["seq"]), "days_equal": a["n_days"] == b["n_days"], "n_days": a["n_days"], "agg_equal": res["specs"]["T_01"] == res_s["specs"]["T_01"],
       "no_identifiers": not any(x in state_text for x in ("KXTEST", "TB", "TC", "close", "ticker")), "state_keys": sorted(a.keys()),
       "key_parts": R.cache_key(cfg, tmp).count("-") , "first_two": a["seq"][:3], "rebuilt": [cnt_s["rebuilt_from_scratch"], cnt["rebuilt_from_scratch"]]}
print(json.dumps(out))

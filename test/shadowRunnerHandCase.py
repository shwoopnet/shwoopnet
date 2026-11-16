"""Hand case for the forward shadow runner (Nov 16, 2026), worked on paper BEFORE the code ran. An invented list of one spec on an invented series; an invented exchange; the real pinned ENGINE1 modules.
Spec: bucket 600, band 3 (15c to 19c), cheap side, no filter, hold to settlement, 10 contracts. Entry candle at close - 600: bid 0.14, ask 0.16 (cheap side is YES at 16c, band 3, raw ask 0.16).
 M1 result yes (win), M2 result no (loss), M3 result void; M4 has ask 0.30 (out of band: no entry); M5 closes before the start (never counts); M6 is inside an OPEN hold the clause does not override (refused, counted).
 Fee form: fee_up_order(p, n) = ceil(round(0.07 x n x p x (1 - p) x 100, 9)) / 100.
 1c: paid 0.17, fee = ceil(0.07 x 10 x 0.17 x 0.83 x 100) = ceil(9.877) = 10 -> 0.10; cost = 1.70 + 0.10 = 1.80. win = 10 - 1.80 = 8.20; loss = -1.80; void = -0.10 (the entry fee only).
 2c: paid 0.18, fee = ceil(0.07 x 10 x 0.18 x 0.82 x 100) = ceil(10.332) = 11 -> 0.11; cost = 1.80 + 0.11 = 1.91. win = 8.09; loss = -1.91; void = -0.11.
 Aggregates: n 3, wins 1, voids 1; net 1c = 8.20 - 1.80 - 0.10 = 6.30; PF 1c = 8.20 / 1.90 = 4.316; net 2c = 8.09 - 1.91 - 0.11 = 6.07; PF 2c = 8.09 / 2.02 = 4.005.
 Halves (n = 3, half = 1, trades ordered by close): first half [8.20] has no losses (PF None, no_losses true); second half [-1.80, -0.10] has no wins (PF 0.0).
 Status: collecting (n under 100). Days to 100: n is 3, under 5, so None."""
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
C = {"A": START + 3600, "B": START + 4500, "C": START + 5400, "D": START + 6300, "E": START - 900, "Z": START + 7200}
RES = {"A": "yes", "B": "no", "C": "scalar", "D": "yes", "E": "yes", "Z": "yes"}
ASK = {"A": 0.16, "B": 0.16, "C": 0.16, "D": 0.30, "E": 0.16, "Z": 0.16}
urls = []
def get(url):
    urls.append(url)
    if "/markets/candlesticks" in url:
        q = dict(p.split("=") for p in url.split("?")[1].split("&"))
        out = []
        for tk in q["market_tickers"].split(","):
            k = tk.split("-")[1]; e = C[k] - 600
            out.append({"market_ticker": tk, "candlesticks": [{"end_period_ts": e, "yes_bid": {"close_dollars": str(round(ASK[k] - 0.02, 2))}, "yes_ask": {"close_dollars": str(ASK[k])}, "price": {"close_dollars": str(ASK[k])}, "volume_fp": "5", "open_interest_fp": "50"},
                                                         {"end_period_ts": C[k] + 60, "yes_bid": {"close_dollars": "0.5"}, "yes_ask": {"close_dollars": "0.6"}}]})
        return 200, {"markets": out}
    return 200, {"markets": [{"ticker": "KXTEST15M-" + k, "close_time": iso(C[k]), "result": RES[k]} for k in C if C[k] >= int(url.split("min_close_ts=")[1].split("&")[0])]}
NOW = START + 86400
res, cnt, st = R.run_once(tmp, NOW, R.Puller(get=get, sleep=lambda s: None), {}, cfg)
a = res["specs"]["T_01"]
want = {"n": 3, "wins": 1, "voids": 1, "net_1c": 6.3, "pf_1c": 4.316, "net_2c": 6.07, "pf_2c": 4.005, "pf_half1_1c": None, "no_losses_half1_1c": True, "pf_half2_1c": 0.0, "status": "collecting", "days_to_100": None, "refused_by_guard": 1}
got = {k: a[k] for k in want}
# the guard: M6 (Z) is inside H09 which S1 does not override; M5 (E) closes before the start so it is never read as a trade and never counted as refused
out = {"match": got == want, "got": got, "want": want,
       "all_get": all(u.startswith("https://api.elections.kalshi.com/trade-api/v2/") for u in urls), "min_close_is_start": any("min_close_ts=%d" % START in u for u in urls),
       "counts": cnt["specs"][0], "labels": sorted(res["labels"]), "keys_ok": sorted(a.keys()) , "state_has_trades": len(st["trades"]["T_01"]), "pulled_until": st["pulled_until"]["KXTEST15M"], "max_close": NOW - R.SETTLE_LAG_S,
       "second_run_requests": None}
n1 = len(urls)
res2, cnt2, st2 = R.run_once(tmp, NOW + 60, R.Puller(get=get, sleep=lambda s: None), st, cfg)
out["second_run_same_n"] = res2["specs"]["T_01"]["n"] == 3 and len(st2["trades"]["T_01"]) == 3
out["second_run_new_requests"] = len(urls) - n1
print(json.dumps(out))

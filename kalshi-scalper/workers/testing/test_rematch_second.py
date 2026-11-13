"""Synthetic tests of rematch_second.py (stage 1 independent reader). Invented rows only."""
import calendar, gzip, json, os, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rematch_second as R
from zoneinfo import ZoneInfo
from datetime import datetime

def folder(bodies):
    d = tempfile.mkdtemp(); rows = []
    for i, b in enumerate(bodies, 1):
        fn = "%04d.json.gz" % i; gzip.open(os.path.join(d, fn), "wt").write(json.dumps(b)); rows.append({"id": "r%d" % i, "status": 200, "file": fn})
    json.dump({"rows": rows}, open(os.path.join(d, "manifest.json"), "w")); return d
MON = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
def key(ts):
    l = datetime.fromtimestamp(ts, ZoneInfo("America/New_York")); return "%02d%s%02d%02d%02d" % (l.year % 100, MON[l.month - 1], l.day, l.hour, l.minute)
iso = lambda ts: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
T0 = calendar.timegm((2026, 10, 16, 14, 0, 0))                     # inside the slice

def build(n_pairs=12, fall=0.07, ent_ask=0.45, ent_bid=0.43, a_close_gap=720, a_winner="P1", drop_dec_exact=False, a_tie=False, held=False):
    mk, cd = [], []
    for i in range(n_pairs):
        pa, pb = "P%d" % (2 * i + 1), "P%d" % (2 * i + 2)
        SA = T0 + i * 7200; SB = SA + 3600; evA = "KXESOCCERGAME-%sXX%d" % (key(SA), i); evB = "KXESOCCERGAME-%sYY%d" % (key(SB), i)
        for ev, S, close, res in ((evA, SA, SA + a_close_gap, a_winner), (evB, SB, SB + 720, None)):
            for code in (pa, pb):
                r = None if res is None else ("yes" if (code == (pa if res == "P1" else pb)) else "no")
                mk.append({"ticker": "%s-%s" % (ev, code), "event_ticker": ev, "close_time": iso(close), "open_time": iso(S - 3600), "result": r or "no"})
            mk.append({"ticker": "%s-TIE" % ev, "event_ticker": ev, "close_time": iso(close), "open_time": iso(S - 3600), "result": "yes" if (a_tie and ev == evA) else "no"})
        loser = pb if a_winner == "P1" else pa; lt = "%s-%s" % (evB, loser)
        def c(ts, mid, half=0.01): return {"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % (mid - half)}, "yes_ask": {"close_dollars": "%.4f" % (mid + half)}, "volume_fp": "1"}
        ser = [c(SA - 120, 0.50), c(SB - 360, 0.50 - fall)] if not drop_dec_exact else [c(SA - 120, 0.50), c(SB - 420, 0.50 - fall)]
        ser.append({"end_period_ts": SB - 300, "yes_bid": {"close_dollars": "%.4f" % ent_bid}, "yes_ask": {"close_dollars": "%.4f" % ent_ask}, "volume_fp": "1"})
        cd.append({"market_ticker": lt, "candlesticks": ser})
    if held:
        SH = calendar.timegm((2026, 10, 25, 12, 0, 0)); ev = "KXESOCCERGAME-%sHH" % key(SH)
        for code in ("H1", "H2"): mk.append({"ticker": "%s-%s" % (ev, code), "event_ticker": ev, "close_time": iso(SH + 720), "open_time": iso(SH - 3600), "result": "yes"})
        mk.append({"ticker": "%s-TIE" % ev, "event_ticker": ev, "close_time": iso(SH + 720), "open_time": iso(SH - 3600), "result": "no"})
    return folder([{"markets": mk}]), folder([{"markets": cd}])

L, C = build(); r = R.stage1([L], [C]); F = r["funnel"]
assert r["counts_first"]["start_check_passes_80_percent"] and r["counts_first"]["matches_in_the_slice"] == 24, r["counts_first"]
assert F["pairs_by_schedule_B_in_slice"] == 12 and F["earlier_has_a_winner"] == 12 and F["earlier_closed_300s_before_decision"] == 12 and F["loser_two_sided_at_reference"] == 12 and F["state_true_fall_5c_or_more"] == 12 and F["entries"] == 12, F
assert r["instants_read"] == {"exact": 36, "carried": 0}, r["instants_read"]
cost = 0.01 + R.fee_up(0.46); assert abs(r["one_way_cost_median_all_quotes"] - round(cost, 4)) < 1e-9 and r["cost_over_4c"] is False and r["bets_floor_300_passes"] is False        # 12 entries x 15/8 is far under 300
# a fall of exactly 5c counts; 4.99c does not; a move under 2c is the placebo pool
assert R.stage1(*[[x] for x in build(fall=0.05)])["funnel"]["state_true_fall_5c_or_more"] == 12 and R.stage1(*[[x] for x in build(fall=0.0499)])["funnel"]["state_true_fall_5c_or_more"] == 0
fp = R.stage1(*[[x] for x in build(fall=0.01)])["funnel"]; assert fp["placebo_pool_move_under_2c"] == 12 and fp["placebo_entries"] == 12 and fp["entries"] == 0
# the entry band: ask above 80c or a 5c spread is no entry (but the state stays true)
fe = R.stage1(*[[x] for x in build(ent_ask=0.85, ent_bid=0.83)])["funnel"]; assert fe["state_true_fall_5c_or_more"] == 12 and fe["entries"] == 0
fs = R.stage1(*[[x] for x in build(ent_ask=0.48, ent_bid=0.43)])["funnel"]; assert fs["entries"] == 0                    # spread 5c
fs2 = R.stage1(*[[x] for x in build(ent_ask=0.47, ent_bid=0.43)])["funnel"]; assert fs2["entries"] == 12                   # spread exactly 4c counts (tolerance)
# the earlier match must have closed 300 s before the decision minute (S_B - 6 min): A closes 720 s after its start; B starts 3600 s after A's: ok. A closing 3500 s after its start does not.
fl = R.stage1(*[[x] for x in build(a_close_gap=3500)])["funnel"]; assert fl["earlier_has_a_winner"] == 12 and fl["earlier_closed_300s_before_decision"] == 0
# a Tie in the earlier match: no winner
ft = R.stage1(*[[x] for x in build(a_tie=True)])["funnel"]; assert ft["earlier_winner_missing_or_tie"] == 12 and ft["earlier_has_a_winner"] == 0
# a missing decision candle: the last present candle at most 5 minutes earlier is carried (counted as carried), never a later one
fc = R.stage1(*[[x] for x in build(drop_dec_exact=True)]); assert fc["funnel"]["entries"] == 12 and fc["instants_read"]["carried"] == 12 and fc["one_way_cost_median_exact_minute_quotes"] is None and fc["cost_line_worse_decides"] is not None
# held-out market refused and counted; a HELDOUT_ folder refused
Lh, Ch = build(held=True); assert R.stage1([Lh], [Ch])["counts_first"]["held_out_refused"] == 1
with tempfile.TemporaryDirectory() as d:
    hd = os.path.join(d, "HELDOUT_E", "run"); os.makedirs(hd); open(os.path.join(hd, "manifest.json"), "w").write('{"rows": []}')
    try: R.stage1([hd], [C]); raise AssertionError("HELDOUT_ must be refused")
    except SystemExit: pass
print("rematch_second synthetic tests passed")

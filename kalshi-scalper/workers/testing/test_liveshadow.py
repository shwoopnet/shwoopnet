"""Test for liveshadow.py: INVENTED rows only (LIVESHADOW_HAND_CASE.md). Run: python3 -W ignore test_liveshadow.py"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import liveshadow as ls

T0 = 1000.0
def row(tk, side, filled, fill=None, ordered=None, send=T0):
    return {"ticker": tk, "side": side, "count": filled, "orderedCount": filled if ordered is None else ordered, "fill": fill, "sentAtMs": None if send is None else send * 1000}
def poll(dt, yes=None, no=None): return {"t": T0 + dt, "yes_bids": yes or [], "no_bids": no or []}
live = [row("W1", "no", 3, 0.10, 3), row("W2", "yes", 2, 0.15, 2), row("W3", "yes", 1, 0.20), row("W4", "no", 1, 0.30), row("W6", "yes", 2, 0.10), row("W7", "yes", 1, 0.11),
        row("W8", "no", 0, None, 2), row("W9", "yes", 1, 0.50), row("W9", "no", 1, 0.50)]
shadow = {"W1": ("trade", "no", 0.10), "W2": ("trade", "yes", 0.13), "W3": ("trade", "no", 0.20), "W4": ("no_trade", "edge under 5c"), "W5": ("trade", "yes", 0.12),
          "W6": ("no_data", "no decision candle"), "W7": ("trade", "yes", 0.11), "W8": ("trade", "no", 0.25), "W9": ("trade", "yes", 0.50), "W10": ("no_trade", "spread above 3c")}
books = {"W1": [poll(-1, yes=[(0.90, 5)])], "W2": [poll(-2, no=[(0.87, 4)])], "W3": [poll(-1, no=[(0.78, 3)])], "W4": [poll(-3, yes=[(0.68, 5)])],
         "W6": [poll(-0.5, no=[(0.90, 9)])], "W7": [poll(-5, no=[(0.89, 9)])]}
o = ls.compare(live, ["W%d" % i for i in range(1, 11)], shadow, books)
assert o["windows_considered"] == 10
# 9 live attempts (W9 has two), W8 is unfilled: 8 filled
assert o["live_orders"] == 9 and o["filled_live_orders"] == 8, (o["live_orders"], o["filled_live_orders"])
assert o["agreement_universe"] == 9 and o["agree"] == 4 and abs(o["agreement_rate"] - 4 / 9) < 1e-12, o
assert o["codes"] == {"AGREE": 3, "AGREE_LIVE_NOFILL": 1, "SIDE_MISMATCH": 1, "LIVE_ONLY_SHADOW_NO_TRADE": 1, "LIVE_ONLY_SHADOW_NO_DATA": 1, "SHADOW_ONLY": 1, "LIVE_BOTH_SIDES": 1}, o["codes"]
fg = o["fill_gap"]
assert fg["orders_with_a_touch"] == 5 and fg["filled_orders_with_no_touch"] == 3, fg          # W7 (poll too old) and the two W9 orders; the unfilled W8 is excluded
assert abs(fg["median_cents"] - 0.0) < 1e-9 and abs(fg["mean_cents"] - (-0.4)) < 1e-9 and abs(fg["worse_than_touch_share"] - 0.2) < 1e-12 and abs(fg["max_cents"] - 2.0) < 1e-9 and abs(fg["min_cents"] + 2.0) < 1e-9, fg
dis = {d["ticker"]: (d["code"], d["detail"]) for d in o["disagreements"]}
assert dis == {"W3": ("SIDE_MISMATCH", "live yes, shadow no"), "W4": ("LIVE_ONLY_SHADOW_NO_TRADE", "edge under 5c"), "W5": ("SHADOW_ONLY", "shadow yes"),
               "W6": ("LIVE_ONLY_SHADOW_NO_DATA", "no decision candle"), "W9": ("LIVE_BOTH_SIDES", "live sides ['no', 'yes']")}, dis
# the sign of the gap: W2 live .15 against touch .13 is +2c (worse); W3 live .20 against .22 is -2c (better)
assert abs(ls.compare([row("A", "yes", 1, 0.15)], ["A"], {"A": ("trade", "yes", 0.13)}, {"A": [poll(-2, no=[(0.87, 4)])]})["fill_gap"]["mean_cents"] - 2.0) < 1e-9
# touch edges: a poll exactly 4 s before counts, 4.1 s does not, a poll AFTER the send time is ignored, the best opposite bid is the highest price
assert abs(ls.touch_seen([poll(-4.0, no=[(0.80, 1), (0.70, 5)])], "yes", T0) - 0.20) < 1e-12 and ls.touch_seen([poll(-4.1, no=[(0.80, 1)])], "yes", T0) is None
assert ls.touch_seen([poll(+0.1, no=[(0.80, 1)])], "yes", T0) is None and ls.touch_seen([poll(-1, no=[])], "yes", T0) is None and ls.touch_seen(None, "yes", T0) is None and ls.touch_seen([poll(-1, no=[(0.8, 1)])], "yes", None) is None
assert abs(ls.touch_seen([poll(0.0, yes=[(0.90, 1)])], "no", T0) - 0.10) < 1e-12          # a poll AT the send time counts
# the last eligible poll wins: an older better poll does not hide a newer worse one
two = [poll(-3, no=[(0.90, 1)]), poll(-1, no=[(0.80, 1)])]; assert abs(ls.touch_seen(two, "yes", T0) - 0.20) < 1e-12
# fill in cents is read as cents; a row with no send time has no touch; tickStartMs is the fallback send time
assert ls._price(15) == 0.15 and ls._price(0.15) == 0.15 and ls._price(None) is None and ls._price("1") == 1.0
r1 = {"ticker": "A", "side": "yes", "count": 1, "orderedCount": 1, "fill": 15, "tickStartMs": T0 * 1000}
assert ls.compare([r1], ["A"], {"A": ("trade", "yes", .13)}, {"A": [poll(-2, no=[(0.87, 4)])]})["fill_gap"]["orders_with_a_touch"] == 1
assert ls.compare([dict(r1, tickStartMs=None)], ["A"], {"A": ("trade", "yes", .13)}, {"A": [poll(-2, no=[(0.87, 4)])]})["fill_gap"]["filled_orders_with_no_touch"] == 1
# live order with no shadow decision supplied is LIVE_ONLY_SHADOW_NO_DATA; an unfilled attempt with no shadow trade likewise; empty inputs do not divide by zero
e = ls.compare([row("Z", "yes", 1, 0.2)], [], {}, {}); assert e["codes"]["LIVE_ONLY_SHADOW_NO_DATA"] == 1 and e["disagreements"][0]["detail"] == "no shadow decision supplied"
e = ls.compare([], [], {}, {}); assert e["agreement_rate"] is None and e["windows_considered"] == 0 and e["fill_gap"] == {"orders_with_a_touch": 0, "filled_orders_with_no_touch": 0}
# a row that is not an attempt (orderedCount 0, count 0) is ignored
assert ls.compare([row("Y", "yes", 0, None, 0)], ["Y"], {}, {})["live_orders"] == 0
# no live figure leaks: the output keys carry counts, rates and cents gaps only
assert set(o) == {"windows_considered", "live_orders", "filled_live_orders", "agreement_universe", "agree", "agreement_rate", "codes", "fill_gap", "disagreements", "note"}

# --- the CFRTI-K adapter, on the audited reader's own functions (invented perp mids and candles) ---
import cfrti_k_heldout_second as r
A = 0.0005; SD = A * math.sqrt(10 / 9) * math.sqrt(4 / 3)
def mids_for(C, z):
    m = {C - 120 - 60 * j: (100.0 if j % 2 == 0 else 100.0 * math.exp(A)) for j in range(11)}; m[C - 900] = 100.0 * math.exp(-z * SD); return m
C1 = 1_800_000_000
mk = {"KXBTC15M-A": {"series": "KXBTC15M", "close": C1, "result": "no", "event": "e", "floor": 1e5}, "KXBTC15M-B": {"series": "KXBTC15M", "close": C1 + 900, "result": "no", "event": "e", "floor": 1e5},
      "KXBTC15M-C": {"series": "KXBTC15M", "close": C1 + 1800, "result": "no", "event": "e", "floor": 1e5}, "KXBTC15M-D": {"series": "KXBTC15M", "close": C1 + 2700, "result": "no", "event": "e", "floor": 1e5},
      "KXETH15M-X": {"series": "KXETH15M", "close": C1, "result": "no", "event": "e", "floor": 1e5}}
cs = {"KXBTC15M-A": [{"ts": C1 - 120, "bid": .90, "ask": .91}], "KXBTC15M-B": [{"ts": C1 + 900 - 120, "bid": .70, "ask": .71}], "KXBTC15M-C": [{"ts": C1 + 1800 - 120, "bid": .90, "ask": .94}]}
mids = {}
for i, z in enumerate((1.0, 0.5, 1.0)): mids.update(mids_for(C1 + 900 * i, z))
sh = ls.cfrti_k_shadow(mk, cs, mids)
assert sh["KXBTC15M-A"] == ("trade", "no", sh["KXBTC15M-A"][2]) and abs(sh["KXBTC15M-A"][2] - 0.10) < 1e-12          # as hand case H1: NO at .10
assert sh["KXBTC15M-B"] == ("no_trade", "edge under 5c")           # as H4
assert sh["KXBTC15M-C"] == ("no_trade", "spread above 3c")          # as H5
assert sh["KXBTC15M-D"] == ("no_data", "no decision candle") and "KXETH15M-X" not in sh
print("test_liveshadow: all checks passed")

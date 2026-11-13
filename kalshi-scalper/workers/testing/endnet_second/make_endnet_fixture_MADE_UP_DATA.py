"""INVENTED rows for the ENDNET second build (Testing Desk, Nov 13, 2026). Every game, score, quote and result is made up; no Kalshi request, no data. The input layout here is MY OWN invention (the real feed layout is not known):
{"games": [ {"game_id", "close_ts" (epoch s), "minutes": [ {"end_ts", "period", "left_s", "home", "away"} ... one per minute ... ], "strikes": {ticker: floor_strike}, "candles": {ticker: [ {"end_ts", "bid", "ask"} ]}, "results": {ticker: "yes"|"no"|"void"} } ]}
Prices are cents. Usage: python3 make_endnet_fixture_MADE_UP_DATA.py <out folder>. Written BEFORE the scorer; the hand-worked expected file is EXPECTED_hand.md."""
import calendar, json, os, sys
T = lambda y, m, d, hh, mm: calendar.timegm((y, m, d, hh, mm, 0))

def game(gid, close, lefts, scores, strikes, quotes, final_total, result_override=None, periods=None, quote_minutes=None):
    """lefts: clock seconds left at the end of each feed minute (third period unless periods given); scores: (home, away) per minute; quotes: {ticker: (bid, ask)} given at the ENTRY candle only
    (quote_minutes: which feed-minute indexes carry the candle, default: every minute from the first with left <= 240)."""
    base = close - 3600; mins = []
    for i, (l, sc) in enumerate(zip(lefts, scores)):
        mins.append({"end_ts": base + 60 * i, "period": (periods[i] if periods else 3), "left_s": l, "home": sc[0], "away": sc[1]})
    candles = {tk: [] for tk in strikes}
    for i, m in enumerate(mins):
        if quote_minutes is not None and i not in quote_minutes: continue
        for tk, (b, a) in quotes.items():
            candles[tk].append({"end_ts": m["end_ts"], "bid": b, "ask": a})
    res = {tk: ("yes" if final_total > f else "no") for tk, f in strikes.items()}
    if result_override: res.update(result_override)
    return {"game_id": gid, "close_ts": close, "minutes": mins, "strikes": strikes, "candles": candles, "results": res}

L = [600, 540, 480, 420, 360, 300, 240, 180, 120, 60, 0]            # clock left at each minute end (index 7 is 180 s: the first minute at or under 3:00)
L1 = [601, 541, 481, 421, 361, 301, 241, 181, 121, 61, 1]           # offset by one second: 181 is NOT at or under 180; 121 is the first that is
S = lambda *a: list(a)
def flat(n, sc): return [sc] * n
games = [
 # G01 standard entry at index 7: 3-2 (one apart), total 5, strikes 4.5 / 5.5 / 6.5, quote on 5.5: bid 30 ask 34 (spread 4), final total 6 -> YES
 game("G01", T(2026, 11, 18, 3, 30), L, flat(11, (3, 2)), {"T45": 4.5, "T55": 5.5, "T65": 6.5}, {"T55": (30, 34)}, 6, quote_minutes=[7]),
 # G02 tied at index 7 (3-3), 4-3 from index 8: entry index 8 (left 120), total 7, strike 7.5, quote 18/20, final total 7 -> NO
 game("G02", T(2026, 11, 18, 4, 10), L, flat(8, (3, 3)) + flat(3, (4, 3)), {"T65": 6.5, "T75": 7.5}, {"T75": (18, 20)}, 7, quote_minutes=[8]),
 # G03 two goals apart all the time: no state
 game("G03", T(2026, 11, 19, 2, 0), L, flat(11, (4, 2)), {"T55": 5.5}, {"T55": (20, 24)}, 6, quote_minutes=[7]),
 # G04 state at index 7 (1-0) but NO candle at that minute for any strike (later minutes have quotes: must not be used)
 game("G04", T(2026, 11, 19, 3, 0), L, flat(11, (1, 0)), {"T15": 1.5}, {"T15": (20, 24)}, 1, quote_minutes=[8, 9]),
 # G05 entry minute quote one-sided (bid 0)
 game("G05", T(2026, 11, 20, 2, 30), L, flat(11, (2, 1)), {"T35": 3.5}, {"T35": (0, 40)}, 4, quote_minutes=[7]),
 # G06 ask 46 (out of the 15 to 45 band), bid 44
 game("G06", T(2026, 11, 20, 3, 40), L, flat(11, (2, 1)), {"T35": 3.5}, {"T35": (44, 46)}, 4, quote_minutes=[7]),
 # G07 integer line equal to the total 5 (f - total = 0), ask 15 bid 12 (inclusive lower band), final total 6 -> YES (6 > 5.0)
 game("G07", T(2026, 11, 19, 4, 20), L, flat(11, (3, 2)), {"T50": 5.0}, {"T50": (12, 15)}, 6, quote_minutes=[7]),
 # G08 ask 45 bid 41 (spread 4, band upper edge inclusive), total 3, strike 3.5, final total 3 -> NO
 game("G08", T(2026, 11, 22, 1, 0), L, flat(11, (2, 1)), {"T35": 3.5}, {"T35": (41, 45)}, 3, quote_minutes=[7]),
 # G09 spread 5 (bid 30 ask 35)
 game("G09", T(2026, 11, 23, 2, 0), L, flat(11, (2, 1)), {"T35": 3.5}, {"T35": (30, 35)}, 4, quote_minutes=[7]),
 # G10 the only strikes are 2.5 (f - total = -0.5) and 4.5 (f - total = 1.5) beside total 3: no strike fits 0 <= f - total < 1
 game("G10", T(2026, 11, 23, 3, 10), L, flat(11, (2, 1)), {"T25": 2.5, "T45": 4.5}, {"T25": (30, 34), "T45": (10, 14)}, 4, quote_minutes=[7]),
 # G11 one goal apart with the clock under 3:00 but in the SECOND period (every minute is period 2): no state
 game("G11", T(2026, 11, 23, 4, 0), L, flat(11, (1, 0)), {"T15": 1.5}, {"T15": (20, 24)}, 2, periods=[2] * 11, quote_minutes=[7]),
 # G12 void result: entered at ask 28 + 1 = 29, price refunded, fee kept
 game("G12", T(2026, 11, 24, 3, 30), L, flat(11, (2, 1)), {"T35": 3.5}, {"T35": (26, 28)}, 3, result_override={"T35": "void"}, quote_minutes=[7]),
 # G13 candle at index 6 (left 240, good quote) but none at the entry minute (index 7): nothing is carried
 game("G13", T(2026, 11, 25, 3, 0), L, flat(11, (2, 1)), {"T35": 3.5}, {"T35": (30, 34)}, 4, quote_minutes=[6]),
 # G14 offset clock: one apart at 181 (not at or under 180) and at 121 (first that is): entry index 8 (left 121), 3-2, strike 5.5 quote 25/29, final total 6 -> YES
 game("G14", T(2026, 11, 26, 3, 30), L1, flat(11, (3, 2)), {"T55": 5.5}, {"T55": (25, 29)}, 6, quote_minutes=[7, 8]),
]
# the same game cut into a held-out date (closes 2026-12-16): a run on it must be refused
outside = [game("H01", T(2026, 12, 16, 3, 30), L, flat(11, (3, 2)), {"T55": 5.5}, {"T55": (30, 34)}, 6, quote_minutes=[7])]
if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    json.dump({"games": games}, open(os.path.join(out, "dev.json"), "w")); json.dump({"games": outside}, open(os.path.join(out, "outside.json"), "w"))
    print(len(games), "development games,", len(outside), "outside")

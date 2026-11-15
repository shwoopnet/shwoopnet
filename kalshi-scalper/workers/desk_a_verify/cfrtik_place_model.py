"""CFRTI-K place model (Desk A, Nov 15 2026): the DECISION part of the wheel's CFRTI-K places, from DESK_A_FROZEN_WHEEL_DEFINITIONS_NOV13.md section 1, as one pure function. No file, network or clock; offline. Test: cfrtik_place_model_test.py (the 20 committed parity vectors, DESK_A_CFRTI_K_PARITY_VECTORS.json, plus missing-data cases).
decide(strike, yes_bid, yes_ask, marks, open_mark): marks = [mark 0 .. mark 10] (index k = the perp mark at D - 60 k, None if missing), open_mark = the perp mark at close - 900 s (None if missing). A mark is (bid close + ask close) / 2 x 10,000 of the perp candle with end_period_ts = t; a side missing or 0 = the mark is missing (never reference_price).
Returns (decision dict or None, reason). Reasons are the sheet's: 'no quote', 'spread over 3c or crossed', 'not cheap', 'no mark 0', 'no opening mark', 'under 6 changes', 'no volatility', 'no strike', 'no edge', 'trade'.
A day with NO perp archive file is NOT a reason here: the caller must report it as 'no data', never as a no-signal window."""
import math
E = 1e-9; SPREAD = 0.03; LO, HI = 0.05, 0.30; EDGE = 0.05
def Phi(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
def mark(bid_close, ask_close):
    try: b, a = float(bid_close), float(ask_close)
    except (TypeError, ValueError): return None
    if not (b == b and a == a) or b <= 0 or a <= 0: return None
    return (b + a) / 2 * 10000.0
def decide(strike, yes_bid, yes_ask, marks, open_mark):
    if yes_bid is None or yes_ask is None: return None, "no quote"
    if yes_ask - yes_bid <= 0 or yes_ask - yes_bid > SPREAD + E: return None, "spread over 3c or crossed"
    side = "yes" if LO - E <= yes_ask <= HI + E else ("no" if LO - E <= 1 - yes_bid <= HI + E else None)
    if side is None: return None, "not cheap"
    if not strike: return None, "no strike"
    if not marks or not marks[0]: return None, "no mark 0"
    if not open_mark: return None, "no opening mark"
    xs = list(marks) + [None] * (11 - len(marks))
    lr = [math.log(xs[k] / xs[k + 1]) for k in range(10) if xs[k] and xs[k + 1]]
    if len(lr) < 6: return None, "under 6 changes"
    m = sum(lr) / len(lr); sd = math.sqrt(sum((x - m) ** 2 for x in lr) / (len(lr) - 1)) * math.sqrt(4 / 3)
    if sd <= 0: return None, "no volatility"
    index = strike * (xs[0] / open_mark)
    py = Phi(math.log(index / strike) / sd)
    p = yes_ask if side == "yes" else 1 - yes_bid
    chance = py if side == "yes" else 1 - py
    edge = chance - p
    if edge < EDGE - E: return None, "no edge"
    return dict(side=side, price=p, edge=edge, sd=sd, index=index, n_changes=len(lr)), "trade"

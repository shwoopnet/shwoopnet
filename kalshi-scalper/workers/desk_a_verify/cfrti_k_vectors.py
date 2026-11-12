"""CFRTI-K parity vectors for Main's pure function (Desk A, Nov 12 2026). DEVELOPMENT sample only (closes before 2026-11-05, post-cutover); INPUTS and DECISIONS only: no result column, no outcome, no pnl.
  python3 -I cfrti_k_vectors.py <lists dir> <binary candles dir> <perp candles dir> <out.json>
For each chosen window it writes: ticker, close time, floor_strike, the 11 perp marks used for the volatility (times and prices; mark 0 = the candle ending at close-120 s) and the opening mark (candle ending at close-900 s), the log changes, index, sd, model YES, the quote used (YES bid and ask = the 1 minute market candle ending at close-120 s CLOSE values in the development; the live bot uses the live quote at that instant), the side, the edge and the decision with its reason.
It re-derives every decision with its own copy of the formula and requires it to equal cfrti_k.decide() (the frozen scorer's reason string) on every window it prints."""
import sys, os, math, json, collections, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cfrti_k as K
def explain(mk, cands, perp):
    t0 = mk["close"] - 120; E = 1e-9; o = dict(ticker=mk["tk"], close_time=datetime.datetime.fromtimestamp(mk["close"], datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), close_ts=mk["close"], floor_strike=mk["strike"], decision_ts=t0)
    c = cands.get(t0)
    o["marks"] = [{"end_ts": t0 - 60 * k, "price": perp.get(t0 - 60 * k)} for k in range(11)]; o["open_mark"] = {"end_ts": mk["close"] - 900, "price": perp.get(mk["close"] - 900)}
    if not c: o.update(decision="no order", reason="no decision candle"); return o
    bid, ask = c; o["yes_bid"], o["yes_ask"] = bid, ask
    if ask <= bid or ask - bid > K.SPREAD + E: o.update(decision="no order", reason="spread over 3c or crossed"); return o
    side = "yes" if K.LO - E <= ask <= K.HI + E else ("no" if K.LO - E <= 1 - bid <= K.HI + E else None)
    if side is None: o.update(decision="no order", reason="not cheap"); return o
    xs = [perp.get(t0 - 60 * k) for k in range(11)]
    lr = [math.log(xs[k] / xs[k + 1]) for k in range(10) if xs[k] and xs[k + 1]]; o["log_changes"] = lr; o["n_changes"] = len(lr)
    if len(lr) < 6: o.update(decision="no order", reason="under 6 changes"); return o
    m = sum(lr) / len(lr); sd = math.sqrt(sum((x - m) ** 2 for x in lr) / (len(lr) - 1)) * math.sqrt(4 / 3); o["sd"] = sd
    if sd <= 0 or not xs[0]: o.update(decision="no order", reason="no volatility"); return o
    p_open = perp.get(mk["close"] - 900)
    if not p_open: o.update(decision="no order", reason="no opening minute"); return o
    index = mk["strike"] * (xs[0] / p_open); py = K.Phi(math.log(index / mk["strike"]) / sd); p = ask if side == "yes" else 1 - bid; chance = py if side == "yes" else 1 - py
    o.update(index=index, model_yes=py, side=side, side_price=p, side_chance=chance, edge=chance - p)
    if chance - p < K.EDGE - E: o.update(decision="no order", reason="no edge"); return o
    o.update(decision="BUY " + side.upper(), reason="trade"); return o
def main(lists, cands, perpd, out):
    mks = K.load_markets(lists); binary = K.load_binary(cands); perp = K.load_perp(perpd)
    by = collections.defaultdict(list)
    for tk, mk in sorted(mks.items(), key=lambda kv: kv[1]["close"]):
        if mk["close"] < K.DEV_FROM or mk["close"] >= K.CUTOFF: continue
        e = explain(mk, binary.get(tk, {}), perp); t, w = K.decide(mk, binary.get(tk, {}), perp); assert e["reason"] == w, (e["reason"], w, tk)       # same decision as the frozen scorer
        key = e["reason"] if e["reason"] != "trade" else "trade " + e["side"]
        if e["reason"] == "under 6 changes" and e["n_changes"] == 0: key = "under 6 changes (none)"
        by[key].append(e)
    pick = []
    for key, n in (("trade yes", 3), ("trade no", 3), ("no edge", 2), ("not cheap", 3), ("spread over 3c or crossed", 2), ("under 6 changes", 2), ("no opening minute", 1), ("no decision candle", 1), ("no volatility", 1)):
        L = by.get(key, []); step = max(1, len(L) // n) if L else 1
        pick += [dict(e, case=key) for e in L[::step][:n]]
    # near-miss cases: edge just under and just over 0.05, ask exactly 0.30, a NO ask exactly 0.30
    tr = [e for k, v in by.items() if k.startswith("trade") for e in v]; ne = by.get("no edge", [])
    if ne: pick.append(dict(max(ne, key=lambda e: e["edge"]), case="no edge: largest edge below 0.05"))
    if tr: pick.append(dict(min(tr, key=lambda e: e["edge"]), case="trade: smallest edge at or above 0.05"))
    edge30 = [e for v in by.values() for e in v if "side_price" in e and abs(e["side_price"] - 0.30) < 1e-9]
    if edge30: pick.append(dict(edge30[0], case="side price exactly 0.30 (band edge, cent-inclusive)"))
    # CONSTRUCTED cases (made from a real development trade window by removing perp marks; labelled so): boundary of "at least 6 log changes", a missing opening mark, a missing decision-minute mark
    base = next((e for e in tr if True), None); synth = []
    def variant(tk, drop, label):
        mk = mks[tk]; p2 = {t: v for t, v in perp.items() if t not in drop}
        e = explain(mk, binary.get(tk, {}), p2); t, w = K.decide(mk, binary.get(tk, {}), p2); assert e["reason"] == w, (e["reason"], w); return dict(e, case="CONSTRUCTED: " + label + " (real window " + tk + " with the listed perp marks removed)", removed_marks=sorted(drop))
    for e in tr:
        t0 = e["decision_ts"]; ts = lambda ks: {t0 - 60 * k for k in ks}
        v6 = variant(e["ticker"], ts([3, 6]), "exactly 6 log changes left")
        if v6["reason"] == "trade" and v6["n_changes"] == 6:
            synth.append(v6); synth.append(variant(e["ticker"], ts([3, 6, 10]), "exactly 5 log changes left"))
            synth.append(variant(e["ticker"], {e["close_ts"] - 900}, "opening mark missing")); synth.append(variant(e["ticker"], ts([0]), "decision-minute mark missing"))
            break
    pick += synth
    json.dump({"note": "DEVELOPMENT only (closes 2026-09-12 to before 2026-11-05); inputs and decisions, no outcome. perp price = mid of bid close and ask close of the 1 minute KXBTCPERP candle x 10000 (the unit cancels in every ratio). Quote = the market's own 1 minute candle close ending at close-120 s in the development; live: the live quote at that instant.", "counts": {k: len(v) for k, v in by.items()}, "vectors": pick}, open(out, "w"), indent=1)
    print({k: len(v) for k, v in by.items()}, "vectors", len(pick), "of which constructed", len(synth))
if __name__ == "__main__": main(*sys.argv[1:5])

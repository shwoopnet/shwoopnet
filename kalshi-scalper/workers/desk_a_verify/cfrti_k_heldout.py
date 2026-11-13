"""CFRTI-K HELD-OUT reader (Desk A, Nov 13 2026), written BEFORE 2026-11-14T00:00:00Z on the Head of R&D's order, same rules as `cfrti_k.py` (the development scorer, sha256 79966ef8..., imported unchanged for decide(), the loaders and pf()).
  python3 -I cfrti_k_heldout.py <lists dir> <binary candles dir> <perp candles run folder>
Reads ONLY closes on or after HELD_FROM = 2026-11-14T00:00:00Z (a date constant). REFUSES before READ_NOT_BEFORE = 2026-11-20T00:00:00Z (the registered read date) unless the lists folder carries MADE_UP_DATA (a test fixture). READ-ONCE: the marker file beside this script is checked BEFORE any data is read; a second real run refuses. Below 50 held-out trades (registered minimum, CFRTI_K_REGISTRATION section 4) it prints ONLY 'NOT_ENOUGH_DATA, n trades = x' and writes no marker, so the read stays unspent (the Head: under 50 is NOT_ENOUGH_DATA, not a fail; read once on the first day that has 50 rows, no peeking).
At 50 or more it writes the marker, then prints the registered line and ONE label: PASS = cleared its registered bar (cash PF 1.3 or better, a positive mean, n of 50 or more; a re-test lead into the shadow gate, never a research-bar pass); FAIL = n of 50 or more and the bar not cleared, or cash PF under 1.0 (the owner's decision of 2026-11-13: CFRTI-K is then CLOSED FOR GOOD). No other figure, no thirds are labels. Prints the heldout_guard_v2 list-hash line first. HELDOUT_ folders and listed pull runs are refused by the guard."""
import sys, os, calendar, time, json, collections, datetime, math
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import cfrti_k as K
HELD_FROM = calendar.timegm(time.strptime("2026-11-14", "%Y-%m-%d"))
READ_NOT_BEFORE = calendar.timegm(time.strptime("2026-11-20", "%Y-%m-%d"))
MIN_TRADES = 50
MARKER = os.path.join(here, "cfrti_k_heldout_read_marker.txt")
def refuse_if_read(marker=None):
    m = marker or MARKER
    if os.path.lexists(m): sys.exit("REFUSED: the one registered CFRTI-K held-out read has been made (%s exists)" % m)
def load_markets_ho(folder):
    """settled KXBTC15M markets closing on or after HELD_FROM, with a strike (the development loader's cutoff is the other way round)"""
    out = {}
    for b in K.bodies(folder):
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            if m.get("ticker", "").startswith("KXBTC15M-") and m.get("result") in ("yes", "no") and m.get("floor_strike") is not None:
                c = K.iso(m["close_time"])
                if c >= HELD_FROM: out[m["ticker"]] = dict(tk=m["ticker"], close=c, strike=float(m["floor_strike"]), yes=m["result"] == "yes")
    return out
def trades_of(markets, binary, perp):
    tr = []
    for tk, mk in markets.items():
        t, _ = K.decide(mk, binary.get(tk, {}), perp)
        if t: tr.append(t)
    tr.sort(key=lambda t: t["close"]); return tr
def label(trades):
    """the registered held-out call. n under 50: NOT_ENOUGH_DATA; PASS needs cash PF 1.3 or better and a positive mean; anything else at n of 50 or more is FAIL"""
    n = len(trades)
    if n < MIN_TRADES: return "NOT_ENOUGH_DATA"
    pn = [t["pnl"] for t in trades]; p = K.pf(pn)
    return "PASS" if p >= 1.3 and sum(pn) > 0 else "FAIL"
def lines(trades):
    pn = [t["pnl"] for t in trades]; n = len(trades); p = K.pf(pn)
    L = ["CFRTI-K HELD-OUT (closes from 2026-11-14T00:00:00Z) | n %d | cash PF %s | mean %+.2fc | win %.1f%% | days %d" % (n, "inf" if p == float("inf") else "%.2f" % p, 100 * sum(pn) / n, 100 * sum(t["win"] for t in trades) / n, len({t["day"] for t in trades}))]
    lab = label(trades)
    L.append("LABEL: " + ("PASS: cleared its registered bar (cash PF 1.3 or better, positive mean, n >= 50); a re-test lead, never a research-bar pass" if lab == "PASS" else "FAIL: missed its registered bar (the owner's decision of 2026-11-13: CLOSED FOR GOOD)"))
    return L
def run(lists, cands, perp_path, now=None, marker=None, fixture=False):
    sys.path.insert(0, here); import heldout_guard_v2 as G
    print(G.list_line())
    now = time.time() if now is None else now
    if not fixture and now < READ_NOT_BEFORE: sys.exit("REFUSED: before 2026-11-20T00:00:00Z the held-out read does not run (registered read date)")
    if not fixture: refuse_if_read(marker)
    mk = load_markets_ho(lists); tr = trades_of(mk, K.load_binary(cands), K.load_perp(perp_path))
    if len(tr) < MIN_TRADES:
        print("NOT_ENOUGH_DATA, n trades = %d (needs %d); nothing else is printed and the read is not spent" % (len(tr), MIN_TRADES)); return tr
    if not fixture:
        with open(marker or MARKER, "x") as f: f.write("read at %s UTC\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)))
    print("\n".join(lines(tr))); return tr
if __name__ == "__main__":
    if len(sys.argv) != 4: sys.exit(__doc__)
    lists = os.path.abspath(sys.argv[1])
    run(lists, os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]), fixture=os.path.exists(os.path.join(lists, "MADE_UP_DATA")))

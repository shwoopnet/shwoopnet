"""CFRTI-K HELD-OUT reader (Desk A, Nov 13 2026), written BEFORE 2026-11-14T00:00:00Z on the Head of R&D's order, same rules as `cfrti_k.py` (the development scorer, sha256 79966ef8..., imported unchanged for decide(), the loaders and pf()).
  python3 -I cfrti_k_heldout.py <lists dir> <binary candles dir> <perp candles run folder>
Reads ONLY closes STRICTLY AFTER HELD_FROM = 2026-11-14T00:00:00Z (the 00:00Z window is excluded, DEPTH1 read it first, the Head Nov 14) (a date constant). REFUSES before READ_NOT_BEFORE = 2026-11-20T00:00:00Z (the registered read date) unless the lists folder carries MADE_UP_DATA (a test fixture). READ-ONCE: the marker file beside this script is checked BEFORE any data is read; a second real run refuses. Thresholds (the card's latest dated lines; the Head, 17:10Z, FINAL): every label needs n of 50 or more; n under 50 = NOT_ENOUGH_DATA; n of 50 or more = the three labels. NOT_ENOUGH_DATA prints ONLY 'NOT_ENOUGH_DATA, n trades = x', writes no marker (the read stays unspent) and appends the run with its date and n to cfrti_k_heldout_run_log.txt beside this script.
At 50 or more it writes the marker, then prints the registered line and ONE of three labels (the registration's labels govern, the Head 17:04Z): PASS = cash PF 1.3 or better, a mean above 0, n of 50 or more (a re-test lead into the shadow gate, never a research-bar pass); NO CALL = cash PF from 1.0 up to 1.3 at n of 50 or more (what it means for the live seat is the owner's decision); FAIL = cash PF under 1.0 at n of 50 or more (the owner's decision of 2026-11-13: CFRTI-K is then CLOSED FOR GOOD). No other figure, no thirds are labels. Prints the heldout_guard_v2 list-hash line first. HELDOUT_ folders and listed pull runs are refused by the guard."""
import sys, os, calendar, time, json, collections, datetime, math
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import cfrti_k as K
HELD_FROM = calendar.timegm(time.strptime("2026-11-14", "%Y-%m-%d"))
READ_NOT_BEFORE = calendar.timegm(time.strptime("2026-11-20", "%Y-%m-%d"))
MIN_TRADES = 50      # every label needs n of 50 or more (the card's latest dated line; the Head, 17:10Z, final)
LOG = os.path.join(here, "cfrti_k_heldout_run_log.txt")
MARKER = os.path.join(here, "cfrti_k_heldout_read_marker.txt")
def refuse_if_read(marker=None):
    m = marker or MARKER
    if os.path.lexists(m): sys.exit("REFUSED: the one registered CFRTI-K held-out read has been made (%s exists)" % m)
def load_markets_ho(folder):
    """settled KXBTC15M markets closing STRICTLY AFTER HELD_FROM (the window closing exactly at HELD_FROM was read first by DEPTH1, the Head, Nov 14, 2026), with a strike (the development loader's cutoff is the other way round)"""
    out = {}
    for b in K.bodies(folder):
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            if m.get("ticker", "").startswith("KXBTC15M-") and m.get("result") in ("yes", "no") and m.get("floor_strike") is not None:
                c = K.iso(m["close_time"])
                if c > HELD_FROM: out[m["ticker"]] = dict(tk=m["ticker"], close=c, strike=float(m["floor_strike"]), yes=m["result"] == "yes")
    return out
def boundary_excluded(folder):
    """how many settled KXBTC15M markets with a strike close EXACTLY at HELD_FROM (excluded, printed with the result)"""
    seen = set()
    for b in K.bodies(folder):
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            if m.get("ticker", "").startswith("KXBTC15M-") and m.get("result") in ("yes", "no") and m.get("floor_strike") is not None and K.iso(m["close_time"]) == HELD_FROM: seen.add(m["ticker"])
    return len(seen)
def trades_of(markets, binary, perp):
    """(trades, reasons): every held-out window is either a trade or counted under the reason decide() gave (zero volatility drops the window and counts it as 'no volatility', as the Verification Analyst's second build does)"""
    tr, why = [], collections.Counter()
    for tk, mk in markets.items():
        t, w = K.decide(mk, binary.get(tk, {}), perp); why[w] += 1
        if t: tr.append(t)
    tr.sort(key=lambda t: t["close"]); return tr, why
def label(trades):
    """the registered held-out call (CFRTI_K_REGISTRATION section 4). n under 50: NOT_ENOUGH_DATA; at n of 50 or more: PASS = cash PF 1.3 or better and a mean above 0; NO CALL = cash PF from 1.0 up to 1.3; FAIL = cash PF under 1.0"""
    n = len(trades)
    if n < MIN_TRADES: return "NOT_ENOUGH_DATA"
    pn = [t["pnl"] for t in trades]; p = K.pf(pn)
    if p >= 1.3 and sum(pn) > 0: return "PASS"
    return "FAIL" if p < 1.0 else "NO CALL"      # the registration's labels govern (the Head, 17:04Z): PF from 1.0 up to 1.3 is its own "no call at n = x"
def lines(trades):
    pn = [t["pnl"] for t in trades]; n = len(trades); p = K.pf(pn)
    L = ["CFRTI-K HELD-OUT (closes strictly after 2026-11-14T00:00:00Z) | n %d | cash PF %s | mean %+.2fc | win %.1f%% | days %d" % (n, "inf" if p == float("inf") else "%.2f" % p, 100 * sum(pn) / n, 100 * sum(t["win"] for t in trades) / n, len({t["day"] for t in trades}))]
    lab = label(trades)
    L.append("LABEL: " + ("PASS: cleared its registered bar (cash PF 1.3 or better, positive mean, n >= 50); a re-test lead, never a research-bar pass" if lab == "PASS" else ("NO CALL: cash PF from 1.0 up to 1.3 at n >= 50 (the registration's own 'no call'); what it means for the live seat is the owner's decision" if lab == "NO CALL" else "FAIL: cash PF under 1.0 at n >= 50 (the owner's decision of 2026-11-13: CLOSED FOR GOOD)")))
    return L
def run(lists, cands, perp_path, now=None, marker=None, fixture=False, log=None):
    sys.path.insert(0, here); import heldout_guard_v2 as G
    print(G.list_line())
    now = time.time() if now is None else now
    if not fixture and now < READ_NOT_BEFORE: sys.exit("REFUSED: before 2026-11-20T00:00:00Z the held-out read does not run (registered read date)")
    if not fixture: refuse_if_read(marker)
    mk = load_markets_ho(lists); tr, why = trades_of(mk, K.load_binary(cands), K.load_perp(perp_path))
    if label(tr) == "NOT_ENOUGH_DATA":
        print("NOT_ENOUGH_DATA, n trades = %d (a call needs 50); nothing else is printed and the read is not spent" % len(tr))
        if not fixture:      # every run that writes no marker is logged with its date and n
            with open(log or LOG, "a") as f: f.write("%s n=%d NOT_ENOUGH_DATA no marker\n" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), len(tr)))
        return tr
    if not fixture:
        with open(marker or MARKER, "x") as f: f.write("read at %s UTC\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)))
    print("\n".join(lines(tr))); print("held-out windows %d | decisions: %s" % (len(mk), dict(why))); print("excluded: %d settled window(s) closing exactly at 2026-11-14T00:00:00Z (DEPTH1 read it first); the held-out is closes strictly after it" % boundary_excluded(lists)); return tr
if __name__ == "__main__":
    if len(sys.argv) != 4: sys.exit(__doc__)
    lists = os.path.abspath(sys.argv[1])
    run(lists, os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]), fixture=os.path.exists(os.path.join(lists, "MADE_UP_DATA")))

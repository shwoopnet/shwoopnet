"""OIVER-SPREAD scorer, BUILD 1 (Desk A, Nov 13 2026; the Head's order of 19:50Z), built to DESK_A_OICORE_VERSIONS_NOV13.md card 1 (741092a7). History screen only: it is NOT a takeover (7g takeover is a forward read beside the parent). Offline, sends nothing. Written to be queued behind V1; NO real run.
  python3 -I oiver_spread.py dev <lists dir> <candles dir>
DEVELOPMENT only: windows closing from 2026-09-12T00:00:00Z (inclusive) to before 2026-11-09T00:00:00Z (exclusive) (the Head's ruling, 21:12Z). (A held-out mode is NOT built here: the Head sets its read date and the marker rule first.)
INPUT (kalshi-pull run folders, both pass spxoi1_threshold.check_run and heldout_guard_v2): lists carry `ticker`, `close_time`, `result` (yes or no; anything else is dropped and counted); candles are KXBTC15M 1 minute candles with `end_period_ts`, yes bid and yes ask close, and `open_interest_fp` (string, read first) or `open_interest`.
THE PARENT (OICORE as registered, README SLOT-OICORE, with the live 8c floor), on candles; MY READING of the registered text, the same convention for parent and version so the comparison is paired (absolute figures may differ from V2's): decision candle = the one ending at close - 180 s; fired if open interest at it minus open interest at the candle ending close - 360 s is at least T = 86,300 (a missing candle or unreadable open interest = not scored, counted); the cheaper side by price (YES price = yes ask, NO price = 1 - yes bid; a tie goes to YES; a book that is not two-sided is skipped and counted as 'not two-sided': it needs 0 < bid, ask < 1 and bid < ask, 1e-9 slack, which also covers a missing bid or ask and a locked or crossed book); that side's decision price must be inside 0.08 to 0.50 inclusive (1e-9 slack); it is filled at that ASK SEEN, with no +0.01 slip (OICORE's slip was switched off in PR 895) and no next-candle fill check; held to settlement; C = 20 contracts, fee = 0.07 x p x (1 - p) per contract on 20 contracts rounded UP to the cent per order; cash per contract = (1 if the side wins else 0) - price - fee / 20. Halves (for the second-half comparison) are by COUNT: the trades in date order, the first floor(n / 2) and the rest.
THE VERSION (OIVER-SPREAD): the parent's trade ONLY IF (yes ask - yes bid) at the decision candle is at most 0.03 (1e-9 slack). So every version trade is a parent trade (a subset on the same windows).
OUTPUT: parent and version n, win rate, cash PF, mean per contract; share of parent signals removed; the paired comparison on the same windows (PF difference, net per contract-week, halves by date); and the 7g bar check as a list of parts (n >= 60; PF difference >= 0.10; net per contract-week not lower; second-half PF not worse than the parent's second half), labelled HISTORY SCREEN, NOT A TAKEOVER. Under 100 version trades: 'no evidence at n = x'."""
import sys, os, gzip, json, math, calendar, time, re, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import spxoi1_threshold as S
DEV_FROM = calendar.timegm(time.strptime("2026-09-12", "%Y-%m-%d"))      # the development range (the Head, 21:12Z): closes from here (inclusive) ...
DEV_TO = calendar.timegm(time.strptime("2026-11-09", "%Y-%m-%d"))        # ... to before here (exclusive); R6 and the CFRTI cards hold the later windows
T_OI, BAND, SPREAD_MAX, EPS, CONTRACTS = 86300.0, (0.08, 0.50), 0.03, 1e-9, 20      # no limit slip (OICORE's slip was switched off in PR 895); C = 20 contracts for the fee rounding
def fee_up(p, n=CONTRACTS): return math.ceil(0.07 * n * p * (1 - p) * 100 - 1e-9) / 100
def pf(v):
    if not v: return None
    a = sum(x for x in v if x > 0); b = -sum(x for x in v if x < 0); return a / b if b else float("inf")
def _price(d):
    if isinstance(d, dict):
        for k in ("close", "close_dollars"):
            if d.get(k) not in (None, ""): return S._num(d[k])
    return S._num(d)
def load_candles(folder):
    out = {}
    for b in S.bodies(folder):
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            tk = m.get("market_ticker") or m.get("ticker")
            for c in m.get("candlesticks", []):
                e = c.get("end_period_ts")
                if e is None or not isinstance(tk, str): continue
                try: out.setdefault(tk, {})[int(e)] = dict(bid=_price(c.get("yes_bid")), ask=_price(c.get("yes_ask")), oi=S.oi_of(c))
                except (TypeError, ValueError): pass
    return out
def load_windows(lists):
    out, bad = {}, 0
    for b in S.bodies(lists):
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            tk, ct, res = m.get("ticker"), m.get("close_time"), m.get("result")
            if not (isinstance(tk, str) and tk.startswith("KXBTC15M-") and isinstance(ct, str)): continue
            c = S.iso(ct)
            if c is None or c < DEV_FROM or c >= DEV_TO: continue                      # development range only
            if res in ("yes", "no"): out[tk] = dict(close=c, yes=res == "yes")
            else: bad += 1
    return out, bad
def decide(w, cs):
    """(trade dict or None, reason). The parent's rule on candles; the trade carries `spread_ok` for the version."""
    c = w["close"]; D = cs.get(c - 180); P = cs.get(c - 360)
    if D is None or P is None: return None, "missing candle"
    if D["oi"] is None or P["oi"] is None: return None, "unreadable open interest"
    if D["oi"] - P["oi"] < T_OI - EPS: return None, "not fired"
    bid, ask = D["bid"], D["ask"]
    if bid is None or ask is None or not (bid > EPS and ask < 1 - EPS and bid < ask - EPS): return None, "not two-sided"      # rule 18 (the Head, 21:14Z): 0 < bid, ask < 1 and bid < ask (1e-9 slack); a missing, zero or one-sided, locked or crossed book scores nothing
    py, pn = ask, 1 - bid; side = "yes" if py <= pn else "no"; pD = py if side == "yes" else pn
    if not (BAND[0] - EPS <= pD <= BAND[1] + EPS): return None, "outside 0.08 to 0.50"
    win = w["yes"] == (side == "yes")      # filled at the ask SEEN at the decision candle: no slip, no next-candle fill check (the Head, 19:52Z)
    cash = (1.0 if win else 0.0) - pD - fee_up(pD) / CONTRACTS
    return dict(close=c, side=side, p=pD, win=win, cash=cash, spread_ok=(ask - bid) <= SPREAD_MAX + EPS), "trade"
def halves(trades):
    """halves by COUNT (the Head, 19:52Z and 19:54Z): the trades in date order, the first floor(n / 2) and the rest"""
    tr = sorted(trades, key=lambda t: t["close"]); k = len(tr) // 2; return tr[:k], tr[k:]
def weeks(trades_all):
    cl = [t["close"] for t in trades_all]
    return max(1.0, (max(cl) - min(cl)) / (7 * 86400.0)) if cl else 1.0
def line(name, tr):
    c = [t["cash"] for t in tr]; n = len(tr)
    if not n: return "%s: n 0" % name
    p = pf(c); return "%s: n %d | win %.1f%% | cash PF %s | mean %+.2fc a contract" % (name, n, 100 * sum(t["win"] for t in tr) / n, "inf" if p == float("inf") else "%.2f" % p, 100 * sum(c) / n)
def report(windows, cands):
    parent, why = [], collections.Counter()
    for tk, w in windows.items():
        t, r = decide(w, cands.get(tk, {})); why[r] += 1
        if t: parent.append(t)
    parent.sort(key=lambda t: t["close"]); ver = [t for t in parent if t["spread_ok"]]
    L = ["OIVER-SPREAD HISTORY SCREEN (development, closes 2026-09-12 to before 2026-11-09; NOT A TAKEOVER) | windows %d (result not yes or no, dropped before: counted elsewhere) | decisions: %s" % (len(windows), dict(why)), line("parent OICORE", parent), line("version SPREAD <= 3c", ver)]
    if not parent: return L
    removed = 1 - len(ver) / len(parent); L.append("share of parent signals removed by the spread condition: %.1f%%" % (100 * removed))
    if not ver: return L
    wk = weeks(parent); pp, pv = pf([t["cash"] for t in parent]), pf([t["cash"] for t in ver])
    nets = (sum(t["cash"] for t in parent) / wk, sum(t["cash"] for t in ver) / wk)
    p1, p2 = halves(parent); v1, v2 = halves(ver); pp2, pv2 = pf([t["cash"] for t in p2]), pf([t["cash"] for t in v2])
    L.append("paired, same windows: PF difference (version - parent) %s | net per contract-week parent %+.3f version %+.3f | second-half PF parent %s version %s" % (
        "n/a" if pp is None or pv is None or math.isinf(pp) or math.isinf(pv) else "%+.2f" % (pv - pp), nets[0], nets[1], "n/a" if pp2 is None else "%.2f" % pp2, "n/a" if pv2 is None else "%.2f" % pv2))
    parts = {"n >= 60 version signals": len(ver) >= 60,
             "PF difference >= 0.10": pp is not None and pv is not None and (pv - pp >= 0.10 - 1e-12 if not (math.isinf(pp) or math.isinf(pv)) else (pv > pp)),
             "net per contract-week not lower": nets[1] >= nets[0] - 1e-12,
             "second-half PF not worse than the parent's": pv2 is not None and pp2 is not None and pv2 >= pp2 - 1e-12}
    L.append("7g bar parts (a history screen only; the takeover is a forward read beside the parent): " + "; ".join("%s: %s" % (k, "yes" if v else "NO") for k, v in parts.items()))
    if len(ver) < 100: L.append("no evidence at n = %d version trades" % len(ver))
    return L
def main(lists, cands):
    import heldout_guard_v2 as G; print(G.list_line())
    windows, bad = load_windows(lists); print("\n".join(report(windows, load_candles(cands)))); print("windows dropped for a result that is not yes or no: %d" % bad)
if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "dev": sys.exit(__doc__)
    main(os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]))

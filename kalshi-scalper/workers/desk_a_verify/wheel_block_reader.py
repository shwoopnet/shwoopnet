"""WHEEL BLOCK READER (Desk A, Nov 13 2026): applies ROTATION_LANE.md section 4 (rnd-queue 7c4c71d2, the Head's four rulings of 02:05Z included) to the per-signal records of ONE place. Generic for any wheel place. A separate file from the frozen NC15 scorer (nc15_wheel_replay.py v2, 8d1055df); it reads records, no book and no result of its own.
  python3 -I wheel_block_reader.py <records.csv> [--kind=either|cheap|above50|fav88] [--place=SERIES]   (made-up folders only unless WHEEL_BLOCK_READ=1; HELDOUT_ paths refused)
Records (canonical CSV): ticker,series,signal_t,status,result,win,cash  (signal_t = the signal poll's estimated exchange time, epoch seconds; status 'fillable' for a fillable signal, anything else is not a signal; result scored | void | pending; win 1/0; cash dollars). Forensics' CSV (signal_exchange, status 'fillable, scored|void|open') is read too.
THE RULE. Fillable signals only, in decision order (signal_t, then ticker). A block grows signal by signal and is READ ONCE at the first signal where all hold: n >= 60 (150 for kind fav88, a rule buying at 88c or above), at least 7 different US Central days (America/Chicago, from signal_t), and the rarer outcome (kind either: at least 10 wins AND 10 losses; cheap: 10 wins; above50 and fav88: 10 losses; a void is a fee-only loss and counts as a loss). A block must be complete within 21 x 24 hours from its first signal's time to its last signal's time: a signal beyond that ends the block UNREAD as EXPIRED (no profit factor read) and STARTS the next block. Read: cash PF >= 1.3 on the block, >= 1.0 in each half (the first floor(n/2) signals, then the rest), no single day more than 30 percent of a positive net; any of these failing = FAILED (reasons listed), else CLEARED. After CLEARED the next 30 fillable signals (they belong to no block) must hold PF >= 1.0: then QUALIFIED (and reading stops), else CONFIRMATION FAILED. Blocks never overlap; the next block starts at the next signal after a read or a confirmation. A block (or confirmation) holding a signal whose result is still pending WAITS: nothing after it is read. Every comparison carries the 1e-9 tolerance (PF 1.3 passes at exactly 1.3; no losses with wins passes)."""
import sys, os, csv, io, math, collections
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
CT = ZoneInfo("America/Chicago"); EPS = 1e-9
MIN_N = {"either": 60, "cheap": 60, "above50": 60, "fav88": 150}; SPAN_S = 21 * 86400; CONF_N = 30
def day_of(t): return datetime.fromtimestamp(t, timezone.utc).astimezone(CT).date().isoformat()
def pf_ok(vals, num, den):
    """cash PF >= num/den with the 1e-9 tolerance; no losses with wins passes; nothing at all fails."""
    w = sum(v for v in vals if v > 0); l = -sum(v for v in vals if v < 0)
    if l <= EPS: return w > EPS
    return den * w - num * l >= -EPS
def pf_val(vals):
    w = sum(v for v in vals if v > 0); l = -sum(v for v in vals if v < 0); return (w / l) if l > EPS else (float("inf") if w > EPS else 0.0)
def load(path):
    out = []
    for r in csv.DictReader(open(path, newline="")):
        st = r.get("status", ""); 
        if not st.startswith("fillable"): continue
        res = r.get("result") or ""
        if "," in st: res = {"fillable, scored": "scored", "fillable, void": "void", "fillable, open": "pending"}.get(st, res)
        t = r.get("signal_t") or r.get("signal_exchange")
        out.append(dict(ticker=r["ticker"], series=r.get("series", ""), t=float(t), result=res, win=int(float(r["win"])) if r.get("win") not in ("", None) else 0, cash=float(r["cash"]) if r.get("cash") not in ("", None) else None))
    return out
def read_place(sigs, kind="either"):
    """sigs: fillable signals of one place. Returns (blocks, state) where blocks is a list of dicts in order."""
    sigs = sorted(sigs, key=lambda s: (s["t"], s["ticker"])); blocks = []; cur = []; i = 0; need_n = MIN_N[kind]
    def finals(b): return all(s["result"] in ("scored", "void") for s in b)
    def rarer_ok(b):
        wins = sum(1 for s in b if s["win"] == 1); losses = len(b) - wins
        return (wins >= 10 and losses >= 10) if kind == "either" else (wins >= 10 if kind == "cheap" else losses >= 10)
    while i < len(sigs):
        s = sigs[i]
        if cur and s["t"] - cur[0]["t"] > SPAN_S + EPS:                                        # (b) EXPIRED, unread; the signal that crossed 21 days starts the next block
            blocks.append(dict(status="EXPIRED", n=len(cur), first=cur[0]["ticker"], last=cur[-1]["ticker"], span_days=(cur[-1]["t"] - cur[0]["t"]) / 86400)); cur = []
        cur.append(s); i += 1
        if s["result"] == "pending" or any(x["result"] == "pending" for x in cur):
            return blocks, dict(waiting=True, why="a signal in the block still has no final result", block_n=len(cur), next_signal=i)
        days = len({day_of(x["t"]) for x in cur})
        if len(cur) >= need_n and days >= 7 and rarer_ok(cur):
            n = len(cur); cash = [x["cash"] for x in cur]; h = n // 2; net = sum(cash); byday = collections.defaultdict(float)
            for x in cur: byday[day_of(x["t"])] += x["cash"]
            top = max(byday.values()); fails = []
            if not pf_ok(cash, 13, 10): fails.append("profit factor under 1.3")
            if not pf_ok(cash[:h], 1, 1) or not pf_ok(cash[h:], 1, 1): fails.append("a half under 1.0")
            if net > EPS and top > 0.30 * net + EPS: fails.append("one day holds %.0f%% of the net, over 30%%" % (100 * top / net))
            b = dict(status="FAILED" if fails else "CLEARED", n=n, wins=sum(1 for x in cur if x["win"] == 1), losses=sum(1 for x in cur if x["win"] != 1), voids=sum(1 for x in cur if x["result"] == "void"), net=net, pf=pf_val(cash), half_pf=(pf_val(cash[:h]), pf_val(cash[h:])), days=days, span_days=(cur[-1]["t"] - cur[0]["t"]) / 86400, top_day_share=(top / net if net > EPS else None), fails=fails, first=cur[0]["ticker"], last=cur[-1]["ticker"])
            blocks.append(b); cur = []
            if b["status"] == "CLEARED":
                conf = sigs[i:i + CONF_N]
                if len(conf) < CONF_N: return blocks, dict(waiting=False, confirmation_in_progress=len(conf), of=CONF_N)
                if any(x["result"] == "pending" for x in conf): return blocks, dict(waiting=True, why="a confirmation signal still has no final result", confirmation_n=len(conf))
                cc = [x["cash"] for x in conf]; ok = pf_ok(cc, 1, 1); b["confirmation"] = "QUALIFIED" if ok else "CONFIRMATION FAILED"; b["confirmation_pf"] = pf_val(cc); i += CONF_N
                if ok: return blocks, dict(waiting=False, qualified=True)
    return blocks, dict(waiting=False, block_in_progress=len(cur), days=len({day_of(x["t"]) for x in cur}), wins=sum(1 for x in cur if x["win"] == 1), losses=sum(1 for x in cur if x["win"] != 1))
def lines(place, blocks, state):
    out = []
    for k, b in enumerate(blocks, 1):
        if b["status"] == "EXPIRED": out.append("%s BLOCK %d: EXPIRED (unread; too slow for the wheel) | n %d span %.1f days | %s to %s" % (place, k, b["n"], b["span_days"], b["first"], b["last"])); continue
        out.append("%s BLOCK %d: %s | n %d (%s to %s) wins %d losses %d voids %d | net %.2f PF %.2f halves %.2f / %.2f | days %d span %.1f top day %s%s%s" % (place, k, b["status"], b["n"], b["first"], b["last"], b["wins"], b["losses"], b["voids"], b["net"], b["pf"], b["half_pf"][0], b["half_pf"][1], b["days"], b["span_days"], ("%.0f%%" % (100 * b["top_day_share"])) if b["top_day_share"] is not None else "n/a", (" | fails: " + "; ".join(b["fails"])) if b["fails"] else "", (" | confirmation: %s (PF %.2f)" % (b["confirmation"], b["confirmation_pf"])) if b.get("confirmation") else ""))
    out.append("%s STATE: %s" % (place, state)); return out
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: sys.exit(__doc__)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import heldout_guard; heldout_guard.refuse_heldout(os.path.abspath(a[0]), "wheel block reader")
    kind = next((x.split("=", 1)[1] for x in sys.argv if x.startswith("--kind=")), "either"); only = next((x.split("=", 1)[1] for x in sys.argv if x.startswith("--place=")), None)
    sigs = load(a[0]); places = sorted({s["series"] for s in sigs})
    for p in places:
        if only and p != only: continue
        b, st = read_place([s for s in sigs if s["series"] == p], kind); print("\n".join(lines(p, b, st)))

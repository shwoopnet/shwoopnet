"""MWIDE1: passive bids on wide-spread daily/weekly/monthly markets (research only, no orders).

census:  python3 -I src/scalper/mwide1.py census      (quotes only, no outcome, no tape)
fetch:   python3 -I src/scalper/mwide1.py fetch       (tape for triggered markets only; run after registration is pushed)
score:   python3 -I src/scalper/mwide1.py score       (refuses a second run)
Registration: workers/MWIDE1_REGISTRATION.md
"""
from __future__ import annotations
import collections, datetime, json, math, os, sqlite3, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CUT = 1791043200  # 2026-10-03T16:00Z, frozen third starts here: never fetch
DB = "data/newlist1.sqlite"
MIN_SPREAD, LO, HI = 0.04, 0.03, 0.30
LIFE_MIN_S, MARGIN_S = 12 * 3600, 2 * 3600
TAPE = "data/mwide1_tape.json"
OUT = "data/mwide1_result.txt"


def load():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    mk = {t: (s, cat, o, cl) for t, s, e, cat, cr, o, cl in c.execute("select * from mk")}
    cd = collections.defaultdict(list)
    for t, e, b, a, v in c.execute("select ticker,end_ts,bid,ask,vol from cd order by ticker,end_ts"):
        cd[t].append((e, b, a, v))
    return c, mk, cd


def trigger(t, mk, cd):
    """First priced hourly candle with spread >= 4c whose cheap side bid is 3c..30c.
    Returns (post_ts, side, bid_price, spread) or None. Quotes only, no outcome."""
    s, cat, o, cl = mk[t]
    if cl >= CUT or cat == "Sports" or cl - o < LIFE_MIN_S:
        return None
    for e, b, a, v in cd[t]:
        if e < o + MARGIN_S or e > cl - MARGIN_S:
            continue
        if not (b >= 0.01 and a <= 0.99 and a > b) or a - b < MIN_SPREAD - 1e-9:
            continue
        yb, nb = round(b, 4), round(1 - a, 4)
        ok_y, ok_n = LO <= yb <= HI, LO <= nb <= HI
        if ok_y and ok_n:
            return (e, "Y" if yb <= nb else "N", min(yb, nb), round(a - b, 4))
        if ok_y:
            return (e, "Y", yb, round(a - b, 4))
        if ok_n:
            return (e, "N", nb, round(a - b, 4))
    return None


def triggers():
    c, mk, cd = load()
    out = {}
    for t in cd:
        r = trigger(t, mk, cd)
        if r:
            out[t] = r + (mk[t][0], mk[t][3])
    return c, mk, out


def fee10(p):
    return math.ceil(0.07 * 10 * p * (1 - p) * 100 - 1e-9) / 100 / 10  # per contract, order of 10


def census():
    c, mk, tr = triggers()
    cls = sorted(v[5] for v in tr.values())
    mid = cls[len(cls) // 2]
    print("orders", len(tr), "median close", mid, datetime.datetime.utcfromtimestamp(mid).isoformat())
    print("by side", collections.Counter(v[1] for v in tr.values()))
    print("families", len({v[4] for v in tr.values()}))
    return mid


def _ts(iso):
    return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def fetch():
    from scalper import api
    c, mk, tr = triggers()
    tape = json.load(open(TAPE)) if os.path.exists(TAPE) else {}
    todo = sorted(t for t in tr if t not in tape)
    print("to fetch", len(todo), "done", len(tape), flush=True)
    for i, t in enumerate(todo):
        post, side, bid, sp, fam, close = tr[t]
        assert close < CUT
        prints, cursor, pages, trunc = [], None, 0, False
        while True:
            p = {"ticker": t, "limit": 1000, "min_ts": int(post), "max_ts": int(close)}
            if cursor:
                p["cursor"] = cursor
            try:
                d = api._get("/markets/trades", p, retries=10)
            except Exception as e:
                print("ERR", t, e, flush=True); prints = None; break
            for x in d.get("trades", []):
                prints.append((_ts(x["created_time"]), x["taker_side"], float(x["yes_price_dollars"]), float(x["no_price_dollars"]), float(x.get("count_fp") or 0)))
            pages += 1
            cursor = d.get("cursor")
            if not cursor:
                break
            if pages >= 12:
                trunc = True
                break
        if prints is None:
            continue
        tape[t] = {"prints": prints, "truncated": trunc}
        if i % 20 == 0:
            json.dump(tape, open(TAPE, "w")); print(i, len(todo), flush=True)
    json.dump(tape, open(TAPE, "w"))
    print("fetch done", len(tape))


def fee(p, k=1.0):
    return math.ceil(k * 0.07 * 10 * p * (1 - p) * 100 - 1e-9) / 100 / 10


def stats(rows):
    """rows: (cluster, price, win, net). Returns dict."""
    from scalper.calibration import cluster_mean_z
    n = len(rows)
    if not n:
        return {"n": 0}
    gw = sum(r[3] for r in rows if r[3] > 0)
    gl = -sum(r[3] for r in rows if r[3] < 0)
    m, se, z = cluster_mean_z([(r[0], r[3]) for r in rows])
    return {"n": n, "win": sum(r[2] for r in rows) / n, "price": sum(r[1] for r in rows) / n,
            "net_c": 100 * m, "PF": (gw / gl if gl else float("inf")), "z": z, "days": len({r[0] for r in rows})}


def fmt(name, d):
    if not d["n"]:
        return f"{name}: n=0"
    return (f"{name}: n={d['n']} days={d['days']} win={100*d['win']:.1f}% price={100*d['price']:.1f}c gap={100*(d['win']-d['price']):+.1f}pt "
            f"net={d['net_c']:+.2f}c PF={d['PF']:.2f} z={d['z']:+.2f}")


def score():
    if os.path.exists(OUT):
        sys.exit("refusing a second run: " + OUT)
    c, mk, tr = triggers()
    cd = collections.defaultdict(dict)
    for t in tr:
        for e, b, a, v in c.execute("select end_ts,bid,ask,vol from cd where ticker=?", (t,)):
            cd[t][e] = (b, a)
    res = dict(c.execute("select ticker,result from res"))
    tape = json.load(open(TAPE))
    MID = 1789797600
    rows = collections.defaultdict(list)  # key -> rows
    info = collections.Counter()
    unf, ctl_all, ctl_fill = [], [], []
    for t, (post, side, bid, sp, fam, close) in sorted(tr.items()):
        r = res.get(t)
        if r not in ("yes", "no"):
            info["no_result"] += 1
            continue
        if t not in tape:
            info["no_tape"] += 1
            continue
        tp = tape[t]
        win = 1.0 if r == ("yes" if side == "Y" else "no") else 0.0
        day = datetime.datetime.fromtimestamp(close, datetime.timezone.utc).strftime("%Y-%m-%d")
        half = "D1" if close < MID else "D2"
        pess = opt = False
        for ts, ts_side, yp, np_, cnt in tp["prints"]:
            if ts <= post or ts > close:
                continue
            if side == "Y" and ts_side == "no":
                pess |= yp < bid - 1e-9; opt |= yp <= bid + 1e-9
            if side == "N" and ts_side == "yes":
                pess |= np_ < bid - 1e-9; opt |= np_ <= bid + 1e-9
        if tp["truncated"]:
            info["truncated"] += 1
        info["posted"] += 1
        info["pess"] += pess; info["opt"] += opt
        net = lambda k=1.0: win - bid - fee(bid, k)
        b0, a0 = cd[t][post]
        ask = a0 if side == "Y" else round(1 - b0, 4)
        ctl = None
        if LO <= ask <= HI:
            ctl = (day, ask, win, win - ask - fee(ask))
            ctl_all.append(ctl)
        for fam_key, ok in (("pess", pess), ("opt", opt)):
            if ok:
                rows[fam_key].append((day, bid, win, net()))
                rows[fam_key + "_" + half].append((day, bid, win, net()))
                rows[fam_key + "_x12"].append((day, bid, win, net(1.2)))
                rows[fam_key + "_m0"].append((day, bid, win, win - bid))
                rows[fam_key + "_" + side].append((day, bid, win, net()))
        if pess:
            if ctl:
                ctl_fill.append(ctl)
            rows["pess_all_posted"].append((day, bid, win, net()))
        else:
            unf.append((day, bid, win, win - bid - fee(bid)))
        rows["posted_per_order"].append((day, bid, win, net() if pess else 0.0))
        rows["pess_fam_" + fam].append((day, bid, win, net() if pess else None))
    out = ["MWIDE1 score (run once)", f"info {dict(info)}"]
    for k in ("pess", "pess_D1", "pess_D2", "pess_x12", "pess_m0", "pess_Y", "pess_N", "opt", "opt_D1", "opt_D2"):
        out.append(fmt(k, stats(rows[k])))
    out.append(fmt("UNFILLED_hypothetical_at_bid", stats(unf)))
    out.append(fmt("TAKER_CONTROL_all_triggers(ask<=30c)", stats(ctl_all)))
    out.append(fmt("TAKER_CONTROL_on_pess_filled", stats(ctl_fill)))
    po = rows["posted_per_order"]
    out.append(f"per posted order (unfilled=0): n={len(po)} mean={100*sum(r[3] for r in po)/max(1,len(po)):+.2f}c")
    fams = collections.defaultdict(list)
    for k, v in rows.items():
        if k.startswith("pess_fam_"):
            fams[k[9:]] = [x for x in v if x[3] is not None]
    out.append("families with fills (info): " + "; ".join(f"{f} n={len(v)} net={100*sum(x[3] for x in v)/len(v):+.1f}c" for f, v in sorted(fams.items(), key=lambda kv: -len(kv[1])) if v)[:3000])
    txt = "\n".join(out)
    print(txt)
    open(OUT, "w").write(txt + "\n")


if __name__ == "__main__":
    {"census": census, "fetch": fetch, "score": score}[sys.argv[1]]()

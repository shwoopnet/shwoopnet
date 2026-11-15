#!/usr/bin/env python3
"""S3 combo house side, BUILD 2 (Testing Desk, Nov 15, 2026). Paper only: reads gzip CSV files it is given, sends nothing, places nothing, writes nothing.
Built from S3_COMBO_HOUSE_SIDE_REGISTRATION.md (claude/idea-desk-b, 8f10fc49, file sha256 700ca935e8286075) ONLY, not from Desk B's scorer. Hand case: S3_SECOND_HAND_CASE.md (committed first). Test: test_s3_second.py (INVENTED files only).
Usage: s3_second.py <dev|held|monitor> <as-of ISO instant, e.g. 2026-11-26T00:00:00Z> <root holding combo/DATE/HHMM/quotes.csv.gz and results.csv.gz>
Aggregates only: no ticker and no per-fill line is printed. The clock is never read: the as-of is an argument."""
import calendar, csv, gzip, math, os, random, re, sys

DEV_START_MS, DEV_END_MS = 1794528000000, 1795651200000          # 2026-11-13T00:00:00Z, 2026-11-26T00:00:00Z (exclusive)
HELD_START_MS, HELD_END_MS = 1795651200000, 1796860800000          # 2026-11-26T00:00:00Z, 2026-12-10T00:00:00Z (exclusive)
READ_NOT_BEFORE = {"dev": 1795651200, "held": 1797033600}          # as-of seconds: 2026-11-26T00:00:00Z, 2026-12-12T00:00:00Z (checked against calendar.timegm in the test)
BAND_LO, BAND_HI, SLIP, TOL = 0.60, 0.90, 0.01, 1e-9
MIN_SIZE, MIN_LEGS, MAX_LEGS, CLOSE_MIN_S, CLOSE_MAX_S, CAP = 3, 2, 30, 3600, 1209600, 10
DUE_AFTER_CLOSE_S, MIN_SETTLED, KILL1_NET, KILL2_PF, BAR_NPD, BAR_DATES, BAR_SHARE, UNRESOLVED_MAX = 48 * 3600, 100, -40.0, 1.2, 0.10, 10, 0.30, 0.10
BOOT_SEED, BOOT_DRAWS, BOOT_INDEX = 20261112, 2000, 100
WEATHER = ("KXHIGH", "KXLOW", "KXTEMP", "KXRAIN", "KXSNOW", "KXHURR", "KXTORN", "KXWIND")
REQ_Q = ("t_recv_ms", "ticker", "event_ticker", "close_time", "no_ask", "yes_bid_size", "volume", "legs", "leg_tickers")
REQ_R = ("ticker", "result")


def stop(msg): raise SystemExit("STOP: " + msg)


def iso_ms(s):
    """ISO 8601 ending in Z (an optional fraction) to epoch milliseconds, or None."""
    m = re.fullmatch(r"(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.(\d{1,6}))?Z", (s or "").strip())
    if not m: return None
    y, mo, d, h, mi, se = (int(m.group(i)) for i in range(1, 7)); frac = m.group(7) or "0"
    try: return calendar.timegm((y, mo, d, h, mi, se, 0, 0, 0)) * 1000 + int(frac.ljust(3, "0")[:3])
    except (ValueError, OverflowError): return None


def num(s):
    try:
        v = float(str(s).strip())
        return v if math.isfinite(v) else None
    except (ValueError, TypeError): return None


def files(root, name):
    out = []
    base = os.path.join(root, "combo")
    for d in sorted(os.listdir(base)) if os.path.isdir(base) else []:
        for h in sorted(os.listdir(os.path.join(base, d))):
            p = os.path.join(base, d, h, name)
            if os.path.isfile(p): out.append(p)
    return sorted(out)


def read_rows(path, required):
    with gzip.open(path, "rt", newline="") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames is None or any(c not in rd.fieldnames for c in required): stop("%s lacks a required column" % os.path.basename(os.path.dirname(path)) + "/" + os.path.basename(path))
        return list(rd)


def parse_legs(cell):
    """leg_tickers: `TICKER:side` joined by `|`; may be empty or end in `|...`; only well-formed entries are legs. Returns the list of leg tickers, or None if no leg is stored."""
    out = []
    for e in (cell or "").split("|"):
        e = e.strip()
        if ":" not in e: continue
        t, sd = e.rsplit(":", 1)
        if t.strip() and sd.strip().lower() in ("yes", "no"): out.append(t.strip())
    return out or None


def cost_of(p): return p + 0.07 * p * (1 - p)


def qualify(r):
    """-> (ticker, event, t_recv_ms, close_ms, p) or None. Any unreadable required field: not a candidate."""
    ts = num(r.get("t_recv_ms")); close = iso_ms(r.get("close_time", "")); na = num(r.get("no_ask")); sz = num(r.get("yes_bid_size")); vol = num(r.get("volume")); lg = num(r.get("legs"))
    tk = (r.get("ticker") or "").strip()
    if None in (ts, close, na, sz, vol, lg) or not tk or ts != int(ts) or lg != int(lg): return None
    ts = int(ts)
    if na >= 1.0: return None
    p = na + SLIP
    if not (BAND_LO - TOL <= p <= BAND_HI + TOL): return None
    if sz < MIN_SIZE or not vol > 0 or not (MIN_LEGS <= int(lg) <= MAX_LEGS): return None
    if not (CLOSE_MIN_S * 1000 <= close - ts <= CLOSE_MAX_S * 1000): return None
    return tk, (r.get("event_ticker") or "").strip(), ts, close, p


def walk(root, mode):
    """The fills of the read window. Blocking (one per ticker and per event, ever) is walked from the development start in BOTH modes."""
    rs, re_ = (DEV_START_MS, DEV_END_MS) if mode in ("dev", "monitor") else (HELD_START_MS, HELD_END_MS)
    filled_t, filled_e, fills, legs = set(), set(), [], {}
    for path in files(root, "quotes.csv.gz"):
        rows = read_rows(path, REQ_Q)
        for r in rows:
            tk = (r.get("ticker") or "").strip(); lg = parse_legs(r.get("leg_tickers"))
            if tk and lg and tk not in legs: legs[tk] = lg
        cands = []
        for r in rows:
            q = qualify(r)
            if q and DEV_START_MS <= q[2] < re_: cands.append(q)
        cands.sort(key=lambda q: q[0])          # stable: equal tickers keep file order
        n = 0
        for tk, ev, ts, close, p in cands:
            if n >= CAP: break
            if tk in filled_t or (ev and ev in filled_e): continue
            filled_t.add(tk); n += 1
            if ev: filled_e.add(ev)
            fills.append({"ticker": tk, "event": ev, "ts": ts, "close": close, "p": p, "cost": cost_of(p)})
    fills = [f for f in fills if f["ts"] >= rs]
    fills.sort(key=lambda f: (f["ts"], f["ticker"]))
    for f in fills: f["legs"] = legs.get(f["ticker"])
    return fills


def results_map(root):
    res = {}
    for path in files(root, "results.csv.gz"):
        for r in read_rows(path, REQ_R):
            tk = (r.get("ticker") or "").strip()
            if tk and tk not in res: res[tk] = re.sub(r"\s+", "", (r.get("result") or "")).lower()
    return res


def is_weather(f): return bool(f["legs"]) and any(l.split("-")[0].startswith(WEATHER) for l in f["legs"])


def classify(fills, res, asof_ms):
    """Adds status: not_due, unresolved, other, settled (with net)."""
    for f in fills:
        f["due"] = f["close"] + DUE_AFTER_CLOSE_S * 1000 <= asof_ms
        r = res.get(f["ticker"])
        if not f["due"]: f["status"] = "not_due"
        elif r is None: f["status"] = "unresolved"
        elif r in ("yes", "no"): f["status"] = "settled"; f["net"] = (1 - f["cost"]) if r == "no" else -f["cost"]; f["paper"] = f["net"] * 2 / f["cost"]; f["day"] = f["close"] // 86400000
        else: f["status"] = "other"
    return fills


def pf(vals):
    pos = sum(v for v in vals if v > 0); neg = abs(sum(v for v in vals if v < 0))
    return math.inf if neg == 0 else pos / neg


def npd(fs): return sum(f["net"] for f in fs) / sum(f["cost"] for f in fs)


def bootstrap(settled):
    days = sorted({f["day"] for f in settled}); by = {d: [f for f in settled if f["day"] == d] for d in days}; rng = random.Random(BOOT_SEED); out = []
    for _ in range(BOOT_DRAWS):
        ch = [rng.choice(days) for _ in days]; fs = [f for d in ch for f in by[d]]; out.append(npd(fs))
    out.sort(); return out[BOOT_INDEX]


def evaluate(fills, mode):
    S = [f for f in fills if f["status"] == "settled"]; due = sum(1 for f in fills if f["due"]); unres = sum(1 for f in fills if f["status"] == "unresolved")
    other = sum(1 for f in fills if f["status"] == "other"); n = len(S)
    L1 = due > 0 and unres > UNRESOLVED_MAX * due
    out = {"fills": len(fills), "due": due, "settled": n, "unresolved": unres, "other_result": other, "wins": sum(1 for f in S if f["net"] > 0), "L1": L1,
           "unresolved_share": None if due == 0 else unres / due}
    run, k1 = 0.0, None
    for i, f in enumerate(S, 1):
        run += f["paper"]
        if run < KILL1_NET: k1 = i; break
    out["kill1_at"] = k1; out["paper_net_dollars"] = sum(f["paper"] for f in S)
    out["cash_pf"] = pf([f["net"] for f in S]) if S else None; out["net_per_dollar"] = npd(S) if S else None
    if n >= MIN_SETTLED:
        first = S[:MIN_SETTLED]; out["kill2_pf"] = pf([f["net"] for f in first]); out["kill2_fired"] = out["kill2_pf"] < KILL2_PF
        h = n // 2; halves = (npd(S[:h]) if h else None, npd(S[h:])); dates = {f["day"] for f in S}; tot = sum(f["net"] for f in S)
        share = None if not tot > 0 else max(sum(f["net"] for f in S if f["day"] == d) for d in dates) / tot
        boot = bootstrap(S)
        out["bar"] = {"net_per_dollar": npd(S), "net_ok": npd(S) >= BAR_NPD, "halves": halves, "halves_ok": h > 0 and halves[0] > 0 and halves[1] > 0, "dates": len(dates), "dates_ok": len(dates) >= BAR_DATES,
                      "share": share, "share_ok": share is not None and share <= BAR_SHARE, "boot_p5": boot, "boot_ok": boot > 0}
        out["bar_met"] = all(out["bar"][k] for k in ("net_ok", "halves_ok", "dates_ok", "share_ok", "boot_ok"))
    if n < MIN_SETTLED: out["label"] = "no evidence at n = %d" % n
    elif L1: out["label"] = "NOT_ENOUGH_DATA"
    elif out["kill2_fired"]: out["label"] = "KILLED (cash profit factor under 1.2 on the first 100)"
    elif out["bar_met"]: out["label"] = "paper edge shown (unproven)" if mode == "dev" else "bar met on the held-out read"
    else: out["label"] = "bar not met"
    return out


def render_block(title, o, tag=None):
    f = lambda x: "n/a" if x is None else ("inf" if x == math.inf else "%.6f" % x)
    L = [title]
    if o["kill1_at"] is not None: L.append("  KILL 1: " + ("would read KILLED (description only)" if o["L1"] else "KILLED") + " as of settled fill %d (paper net under -$40 at $2 a fill)" % o["kill1_at"])
    L.append("  paper fills %d, due %d, settled %d, unresolved %d (%s of due), other result %d, wins %d" % (o["fills"], o["due"], o["settled"], o["unresolved"], f(o["unresolved_share"]), o["other_result"], o["wins"]))
    L.append("  paper net at $2 a fill %s, cash PF %s, net per dollar %s" % (f(o["paper_net_dollars"]), f(o["cash_pf"]), f(o["net_per_dollar"])))
    if "bar" in o:
        b = o["bar"]; kd = "would read KILLED (description only)" if o["L1"] and o["kill2_fired"] else ("KILLED" if o["kill2_fired"] else "not killed")
        L.append("  KILL 2 (first 100 settled): cash PF %s, %s" % (f(o["kill2_pf"]), kd))
        L.append("  bar: net per dollar %s (needs 0.10) %s; halves %s, %s %s; close dates %d %s; largest date share %s %s; bootstrap 5th percentile %s %s" % (f(b["net_per_dollar"]), b["net_ok"], f(b["halves"][0]), f(b["halves"][1]), b["halves_ok"], b["dates"], b["dates_ok"], f(b["share"]), b["share_ok"], f(b["boot_p5"]), b["boot_ok"]))
    lab = o["label"] if not o["L1"] or o["settled"] < MIN_SETTLED else "NOT_ENOUGH_DATA, description only"
    L.append("  " + ("would read: " + lab + " (information only; the registered verdict is the all-combos line)" if tag else "LABEL: " + lab))
    return L


def run(mode, asof, root):
    a = iso_ms(asof)
    if a is None: stop("as-of is not an ISO instant ending in Z")
    if mode in READ_NOT_BEFORE and a // 1000 < READ_NOT_BEFORE[mode]: stop("a %s read is not made before its date" % mode)
    fills = classify(walk(root, mode), results_map(root), a)
    if mode == "monitor":
        S = [f for f in fills if f["status"] == "settled"]
        return ["MONITOR, not the registered verdict; the Nov 26 read is the verdict",
                "paper fills %d, due %d, settled %d, unresolved %d, wins among the settled %d, cash PF so far %s, net per dollar so far %s" % (
                    len(fills), sum(1 for f in fills if f["due"]), len(S), sum(1 for f in fills if f["status"] == "unresolved"), sum(1 for f in S if f["net"] > 0),
                    "n/a" if not S else ("inf" if pf([f["net"] for f in S]) == math.inf else "%.6f" % pf([f["net"] for f in S])), "n/a" if not S else "%.6f" % npd(S))]
    allo = evaluate(fills, mode); known = [f for f in fills if f["legs"] and not is_weather(f)]; nw = evaluate(known, mode)
    lines = ["S3 build 2, %s read, as-of %s" % (mode, asof)] + render_block("ALL COMBOS (the registered line)", allo) + render_block("COMBOS WITH LEGS KNOWN AND NO WEATHER LEG", nw, tag=True)
    cnt = {}
    for f in fills:
        for l in (f["legs"] or []): cnt[l.split("-")[0]] = cnt.get(l.split("-")[0], 0) + 1
    lines.append("leg series seen over the paper fills (each leg of each fill once): " + (", ".join("%s %d" % (k, cnt[k]) for k in sorted(cnt)) or "none"))
    lines.append("combos with no stored legs (in the all-combos line only): %d" % sum(1 for f in fills if not f["legs"]))
    return lines


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 3 and a[0] in ("dev", "held", "monitor"): print("\n".join(run(a[0], a[1], a[2])))
    else: print(__doc__)

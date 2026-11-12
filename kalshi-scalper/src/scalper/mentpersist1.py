"""MENTPERSIST1 (workers/MENTPERSIST1_PROTOCOL.md). plan | fetch | score.
plan : offline, builds b (R1, R2), PREV, pool order (md5) -> scratch plan.json. No outcome of a target is used for selection.
fetch: candle reads, 1 per 15 s, 429 -> pause 300 s, retry once, second 429 -> stop (cursor kept). Resumable.
score: development first; held-out only with --heldout and only for a rule that passed development.
commit-cut [--cap N]: when the reads STOP (cursor_index == pool length, or reads >= cap), writes the cut (close time of the first held-out
  new market) and a READ-ONCE MARKER into workers/MENTPERSIST1_PROTOCOL.md and commits it. `score --heldout` REFUSES unless that committed
  line exists, the cursor still equals the committed one, and the committed marker still says not yet read (Nov 12, 2026 integrity fix:
  the old cut was two thirds of whatever had been read when scoring ran, which moves while reads continue)."""
import os, sys, json, math, sqlite3, hashlib, bisect, collections, time, urllib.request, urllib.error, urllib.parse, datetime
from statistics import NormalDist
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DB = os.path.join(ROOT, "data", "ment1.sqlite")
SCR = "/tmp/claude-0/-home-user-shwoopnet/026f6e8f-6dc4-5e3b-8c3b-e0089b12fb94/scratchpad/mp1"
READLOG = os.path.join(ROOT, "workers", "MENTPERSIST1_READLOG.json")
QCSV = os.path.join(ROOT, "workers", "MENTPERSIST1_QUOTES.csv")
PROTO_REL = "workers/MENTPERSIST1_PROTOCOL.md"
PROTO = os.path.join(ROOT, PROTO_REL)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import readonce
CUT_PREFIX = "COMMITTED CUT:"
def committed_cut():
    """(cut_ts, cursor_index) from the COMMITTED protocol file, or None."""
    import re, subprocess
    r = subprocess.run(["git", "-C", ROOT, "show", "HEAD:kalshi-scalper/" + PROTO_REL], capture_output=True)
    if r.returncode != 0: return None
    for l in r.stdout.decode().splitlines():
        if l.startswith(CUT_PREFIX):
            m = re.search(r"ts=(\d+); cursor_index=(\d+)", l)
            if m: return int(m.group(1)), int(m.group(2))
    return None
BASE = "https://api.elections.kalshi.com/trade-api/v2"
LOOK = 6 * 3600
md5 = lambda s: hashlib.md5(s.encode()).hexdigest()
def fam(ser): return "EARN" if ("EARNINGSMENTION" in ser or "MENTIONEARN" in ser) else "NONEARN"
def fee_r(p): return math.ceil(0.07 * p * (1 - p) * 100 - 1e-9) / 100
def fee_u(p): return 0.07 * p * (1 - p)
os.makedirs(SCR, exist_ok=True)

def build():
    db = sqlite3.connect(DB)
    M = db.execute("select ticker,series,close_ts,result,src,chosen from mk").fetchall()
    seqs = collections.defaultdict(list)  # (s,w) -> [(close, ticker, o)]
    for tk, ser, c, res, src, ch in M:
        seqs[(ser, tk.rsplit("-", 1)[1])].append((c, tk, 1 if res == "yes" else 0))
    pairs = collections.defaultdict(list)  # key -> [(next_close, yes)]
    for (ser, w), L in seqs.items():
        L.sort()
        for i in range(1, len(L)):
            o = L[i - 1][2]
            pairs[(fam(ser), o)].append((L[i][0], L[i][2]))
            pairs[("ALL", o)].append((L[i][0], L[i][2]))
    cum = {}
    for k, v in pairs.items():
        v.sort(); cl = [x[0] for x in v]; cs = [0]
        for x in v: cs.append(cs[-1] + x[1])
        cum[k] = (cl, cs)
    def pool(k, thr):
        cl, cs = cum.get(k, ([], [0])); i = bisect.bisect_right(cl, thr); return i, (cs[i] / i if i else None)
    info = {}
    for tk, ser, c, res, src, ch in M:
        thr = c - LOOK; w = tk.rsplit("-", 1)[1]; L = seqs[(ser, w)]
        earlier = [x for x in L if x[0] <= thr]
        if not earlier: continue
        prev = earlier[-1]; o = prev[2]
        n, bp = pool((fam(ser), o), thr)
        if n < 300: n, bp = pool(("ALL", o), thr)
        if bp is None or n < 300: continue
        nw = len(earlier); kw = sum(x[2] for x in earlier)
        b1 = bp; b2 = (kw + 10 * bp) / (nw + 10) if nw >= 3 else None
        info[tk] = dict(series=ser, c=c, src=src, chosen=ch, b1=b1, b2=b2, nw=nw, o=o, fam=fam(ser))
    return info, {tk: (res) for tk, ser, c, res, src, ch in M}

def quote_for(db, tk, c):
    q = [r for r in db.execute("select end_ts,bid_c,ask_c from candle where ticker=?", (tk,)) if r[0] <= c - LOOK and r[1] is not None and r[2] is not None]
    if not q: return None
    ts, b, a = max(q)
    if b <= 0 or a >= 1 or a <= b or a - b > 0.05: return None
    return b, a

def fires(b, a, bb):
    """returns (side, price) or None for base rate bb."""
    if bb is None: return None
    if 0.10 <= a <= 0.60 and a <= bb - 0.10: return ("yes", a)
    pn = 1 - b
    if 0.10 <= pn <= 0.60 and pn <= (1 - bb) - 0.10: return ("no", pn)
    return None

def cmd_plan():
    info, _ = build()
    pool = sorted([tk for tk, d in info.items() if not d["chosen"]], key=md5)
    held = [tk for tk, d in info.items() if d["chosen"]]
    json.dump(dict(pool=pool, held=held), open(os.path.join(SCR, "plan.json"), "w"))
    print("markets with PREV and b:", len(info), "pool (new):", len(pool), "held500 with PREV:", len(held))

def get(path, params, log):
    q = "?" + urllib.parse.urlencode(params)
    for attempt in range(2):
        w = 15 - (time.time() - get.last)
        if w > 0: time.sleep(w)
        get.last = time.time()
        try:
            with urllib.request.urlopen(BASE + path + q, timeout=30) as r:
                return 200, json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                log["pauses"] = log.get("pauses", 0) + 1
                log.setdefault("stops429", []).append(datetime.datetime.utcnow().isoformat() + "Z")
                save_log(log)
                if attempt == 0:
                    print("429, pausing 300 s", flush=True); time.sleep(300); continue
                return 429, None
            if e.code == 404: return 404, None
            return e.code, None
        except Exception as e:
            return -1, None
    return 429, None
get.last = 0.0

def save_log(log): json.dump(log, open(READLOG, "w"), indent=1)

def counts(info, db, tks):
    c = {"R1": 0, "R2": 0}
    for tk in tks:
        d = info[tk]; q = quote_for(db, tk, d["c"])
        if not q: continue
        if fires(*q, d["b1"]): c["R1"] += 1
        if d["b2"] is not None and fires(*q, d["b2"]): c["R2"] += 1
    return c

def commit_state(log, info, db, tks):
    with open(QCSV, "w") as f:
        f.write("ticker,close_ts,bid,ask,b1,b2,fire_r1,fire_r2\n")
        for tk in tks:
            d = info[tk]; q = quote_for(db, tk, d["c"])
            if not q: continue
            f1 = fires(*q, d["b1"]); f2 = fires(*q, d["b2"]) if d["b2"] is not None else None
            f.write("%s,%d,%.2f,%.2f,%.4f,%s,%s,%s\n" % (tk, d["c"], q[0], q[1], d["b1"], "" if d["b2"] is None else "%.4f" % d["b2"], f1[0] if f1 else "", f2[0] if f2 else ""))
    os.system("cd %s && git add workers/MENTPERSIST1_READLOG.json workers/MENTPERSIST1_QUOTES.csv && git commit -q -m 'MENTPERSIST1 cursor %d reads' -m 'Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>' -m 'Claude-Session: https://claude.ai/code/session_01PSWvZpN1MLodfM5W2dqtii' && git pull -q --rebase --autostash origin claude/epic-ptolemy-0amjd9 && git push -q -u origin claude/epic-ptolemy-0amjd9" % (ROOT, log["reads"]))

def cmd_fetch(cap):
    info, _ = build(); plan = json.load(open(os.path.join(SCR, "plan.json")))
    db = sqlite3.connect(DB)
    log = json.load(open(READLOG)) if os.path.exists(READLOG) else {"reads": 0, "log": [], "cursor_index": 0, "pool_md5_order": "ascending md5(ticker) over new markets with PREV, plan.json"}
    pool = plan["pool"]; held = plan["held"]; got = set(r[0] for r in db.execute("select ticker from done"))
    run = 0
    while log["cursor_index"] < len(pool) and log["reads"] < cap:
        tk = pool[log["cursor_index"]]
        if tk in got: log["cursor_index"] += 1; continue
        d = info[tk]; ser = d["series"]; c = d["c"]
        path = f"/historical/markets/{tk}/candlesticks" if d["src"] == "hist" else f"/series/{ser}/markets/{tk}/candlesticks"
        st, js = get(path, {"start_ts": c - 30 * 3600, "end_ts": c, "period_interval": 60}, log)
        if st == 429:
            print("second 429 in a row: stopping, cursor saved", flush=True); save_log(log); commit_state(log, info, db, held + pool[:log["cursor_index"]]); return
        if st == 200:
            json.dump(js, open(os.path.join(SCR, "raw_" + tk + ".json"), "w"))
            rs = []
            for x in js.get("candlesticks", []):
                b, a = (x.get("yes_bid") or {}).get("close"), (x.get("yes_ask") or {}).get("close")
                f = lambda v: None if v in (None, "") else float(v)
                if x.get("end_period_ts") is not None: rs.append((tk, int(x["end_period_ts"]), f(b), f(a)))
            db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", rs)
            db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (tk, len(rs))); db.commit(); n = len(rs)
        elif st == 404:
            db.execute("INSERT OR REPLACE INTO done VALUES(?,0)", (tk,)); db.commit(); n = 0
        else:
            print("status", st, tk, flush=True); n = None
        log["reads"] += 1; run += 1
        log["log"].append({"n": log["reads"], "ticker": tk, "status": st, "candles": n, "at": datetime.datetime.utcnow().isoformat() + "Z"})
        if st in (200, 404): log["cursor_index"] += 1
        else:
            log["fail_streak"] = log.get("fail_streak", 0) + 1
            if log["fail_streak"] >= 3: print("3 failures, stop"); save_log(log); return
            continue
        log["fail_streak"] = 0
        save_log(log)
        if log["reads"] % 200 == 0 or log["reads"] % 50 == 0 and False:
            cn = counts(info, db, held + pool[:log["cursor_index"]])
            log.setdefault("block_counts", []).append({"reads": log["reads"], **cn}); save_log(log)
            print("BLOCK", log["reads"], cn, flush=True)
            commit_state(log, info, db, held + pool[:log["cursor_index"]])
            if max(cn.values()) >= 130: print("trade count >= 130, stop reads"); return
        elif log["reads"] % 20 == 0: print("reads", log["reads"], flush=True)
    save_log(log); commit_state(log, info, db, held + pool[:log["cursor_index"]])

def stats(rows, feef):
    """rows: (call, series, cash). returns dict"""
    x = [r[2] for r in rows]
    if not x: return None
    w = sum(t for t in x if t > 0); l = -sum(t for t in x if t < 0)
    by = collections.defaultdict(float); cnt = collections.defaultdict(int); bs = collections.defaultdict(float)
    for ev, s, t in rows: by[ev] += t; cnt[ev] += 1; bs[s] += t
    n = len(x); mean = sum(x) / n
    se = math.sqrt(sum((by[e] - mean * cnt[e]) ** 2 for e in by)) / n
    net = sum(x)
    return dict(n=n, calls=len(by), pf=(w / l if l > 0 else 99.0), mean=mean, z=(mean / se if se > 0 else 0.0), net=net,
                maxcall=(max(by.values()) / net if net > 0 else None), maxser=(max(bs.values()) / net if net > 0 else None))

def cmd_commit_cut(cap):
    if committed_cut(): raise SystemExit("refused: a COMMITTED CUT line already exists in " + PROTO_REL)
    if os.system("cd %s && git diff --quiet HEAD -- %s" % (ROOT, PROTO_REL)) != 0: raise SystemExit("refused: uncommitted edits in " + PROTO_REL)
    info, _ = build(); plan = json.load(open(os.path.join(SCR, "plan.json"))); log = json.load(open(READLOG))
    cur, n_pool = log["cursor_index"], len(plan["pool"])
    if not (cur == n_pool or log["reads"] >= cap):   # the pull must be COMPLETE: whole pool read, or the registered cap reached
        raise SystemExit("refused: pull incomplete (cursor_index %d of %d, reads %d, cap %d)" % (cur, n_pool, log["reads"], cap))
    nr = sorted(plan["pool"][:cur], key=lambda t: info[t]["c"])
    if len(nr) < 3: raise SystemExit("refused: too few markets read to cut")
    cut_ts = info[nr[2 * len(nr) // 3]]["c"]
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    iso = datetime.datetime.fromtimestamp(cut_ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(PROTO, "a") as f:
        f.write("\n## Committed cut (%s; written by `mentpersist1.py commit-cut` when the reads stopped; no outcome was used)\n" % today)
        f.write("%s ts=%d; cursor_index=%d; pool=%d; reads=%d; new markets read %d; development new = close time before %s, held-out new = on or after it\n" % (CUT_PREFIX, cut_ts, cur, n_pool, log["reads"], len(nr), iso))
        f.write("READ-ONCE MARKER: not yet read; MENTPERSIST1 first read allowed on or after %s; after the read: READ ON <date>, commit <hash>\n" % today)
    os.system("cd %s && git add %s && git commit -q -m 'MENTPERSIST1 committed cut %s' -m 'Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>' -m 'Claude-Session: https://claude.ai/code/session_01PSWvZpN1MLodfM5W2dqtii'" % (ROOT, PROTO_REL, iso))
    print("cut committed:", iso, "-- push the branch before scoring held-out")

def cmd_score(heldout):
    cc = committed_cut()
    if heldout:
        if not cc: raise SystemExit("refused: no committed cut line; run `commit-cut` when the reads stop, commit it, then score --heldout")
        readonce.require_unread(PROTO_REL, "MENTPERSIST1")
        if json.load(open(READLOG))["cursor_index"] != cc[1]: raise SystemExit("refused: cursor_index moved since the cut was committed")
        print("After this read, replace the marker line in %s with 'READ-ONCE MARKER: MENTPERSIST1 READ ON <date>, commit <hash>' and commit it." % PROTO_REL)
    info, res = build(); plan = json.load(open(os.path.join(SCR, "plan.json"))); db = sqlite3.connect(DB)
    done = set(r[0] for r in db.execute("select ticker from done where n>0"))
    cur = json.load(open(READLOG))["cursor_index"]
    newread = [tk for tk in plan["pool"][:cur]]
    newq = [tk for tk in newread if tk in done]
    newq.sort(key=lambda t: info[t]["c"])
    # split NEW by call date: earliest 2/3 dev, last third held-out (of the new markets read, quoted or not)
    nr = sorted(newread, key=lambda t: info[t]["c"])
    if cc and cc[1] == cur: devnew = {t for t in nr if info[t]["c"] < cc[0]}; honew = {t for t in nr if info[t]["c"] >= cc[0]}   # committed cut
    else: cut = 2 * len(nr) // 3; devnew = set(nr[:cut]); honew = set(nr[cut:])   # no committed cut yet: development printing only, heldout is refused above
    print("new read", len(nr), "dev new", len(devnew), "held-out new", len(honew), "held500 with PREV", len(plan["held"]))
    skipped = sum(1 for t in nr if not quote_for(db, t, info[t]["c"]))
    print("new markets read with no usable quote:", skipped)
    ZB = NormalDist().inv_cdf(1 - 0.05 / 1100002); print("bar z (N 1.1M)", round(ZB, 2), " small-count bar", round(NormalDist().inv_cdf(1 - 0.05 / 9009), 2))
    out = {}
    for rule, key in (("R1", "b1"), ("R2", "b2")):
        for feen, ff in (("rounded", fee_r), ("unrounded", fee_u)):
            for part, tks in (("dev", [t for t in plan["held"]] + [t for t in nr if t in devnew]), ("heldout", [t for t in nr if t in honew])):
                if part == "heldout" and not heldout: continue
                rows = []
                for tk in tks:
                    d = info[tk]; bb = d[key]; q = quote_for(db, tk, d["c"])
                    if not q or bb is None: continue
                    f = fires(q[0], q[1], bb)
                    if not f: continue
                    side, p = f; won = (res[tk] == "yes") == (side == "yes")
                    rows.append((tk.rsplit("-", 1)[0], d["series"], (1.0 if won else 0.0) - p - ff(p), d["c"], p))
                s = stats([(a, b_, c_) for a, b_, c_, _, _ in rows], ff)
                half = None
                if part == "dev" and rows:
                    rs = sorted(rows, key=lambda r: r[3]); h = len(rs) // 2
                    half = [stats([(a, b_, c_) for a, b_, c_, _, _ in rs[:h]], ff), stats([(a, b_, c_) for a, b_, c_, _, _ in rs[h:]], ff)]
                cheap = [r for r in rows if r[4] < 0.35]; mid = [r for r in rows if r[4] >= 0.35]
                print(rule, feen, part, s, "halves PF", [h_ and round(h_["pf"], 2) for h_ in half] if half else None, "cheap n", len(cheap), "mid n", len(mid))
                out[(rule, feen, part)] = s
    return out

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "plan": cmd_plan()
    elif c == "fetch": cmd_fetch(int(sys.argv[sys.argv.index("--cap") + 1]) if "--cap" in sys.argv else 1600)
    elif c == "commit-cut": cmd_commit_cut(int(sys.argv[sys.argv.index("--cap") + 1]) if "--cap" in sys.argv else 1600)
    elif c == "score": cmd_score("--heldout" in sys.argv)

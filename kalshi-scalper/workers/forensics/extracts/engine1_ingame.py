#!/usr/bin/env python3
"""ENGINE1 in-game extract (Forensics desk, Nov 16, 2026): the in-game recorder's observations (sports-data, ingame/<date>/<HHMM>/obs.csv.gz) in the engine's poll schema, rows with t_recv_ms BEFORE 2026-11-13T00:00Z (epoch 1794528000, verified with calendar.timegm; Auditor B's hold map: rows from then on are the third-3 held-out of INGAME1, IGUNDER1, IGFADE1, IGTOTDOG1, PREDRIFT1 and INGAMELAG1).
Schema: market(ticker, series, close_ts NULL, result NULL, src, event, kind, strike) one row per ticker; candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi NULL, bid_size, ask_size, t_recv_ms): one row per poll, end_ts = t_recv_ms // 1000. NO game outcome or result is read or stored (the files carry none; the coverage file is not read).
Duplicates (same ticker and t_recv_ms) kept once and counted; a row with no readable bid or ask is kept with NULLs and counted. usage: python3 -I engine1_ingame.py <sports-data dir> <out dir> <tag>"""
import sys, os, csv, gzip, glob, sqlite3, json, hashlib, collections, calendar
CUT_MS = calendar.timegm((2026, 11, 13, 0, 0, 0)) * 1000
def num(x):
    try: return float(x) if x not in ("", None) else None
    except ValueError: return None
def main(a):
    root, out, tag = a; os.makedirs(out, exist_ok=True); dst = os.path.join(out, "ENGINE1_ingame_%s_extract.sqlite" % tag)
    if os.path.exists(dst): os.remove(dst)
    o = sqlite3.connect(dst); o.execute("create table market(ticker, series, close_ts, result, src, event, kind, strike)")
    o.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi, bid_size, ask_size, t_recv_ms)")
    seen = set(); mk = {}; c = collections.Counter(); nfiles = 0
    for p in sorted(glob.glob(os.path.join(root, "ingame", "*", "*", "obs.csv.gz"))):
        nfiles += 1
        for r in csv.DictReader(gzip.open(p, "rt", newline="")):
            t = int(r["t_recv_ms"])
            if t >= CUT_MS: c["at or after 2026-11-13T00:00Z (held out, dropped)"] += 1; continue
            k = (r["ticker"], t)
            if k in seen: c["duplicate"] += 1; continue
            seen.add(k); b, s = num(r["yes_bid"]), num(r["yes_ask"])
            if b is None or s is None: c["missing bid or ask (NULL)"] += 1
            if r["ticker"] not in mk: mk[r["ticker"]] = (r["ticker"].split("-")[0], r["event"], r["kind"], r["strike"])
            o.execute("insert into candle values(?,?,?,?,?,?,?,?,?,?)", (r["ticker"], t // 1000, b, s, num(r["last_price"]), num(r["volume"]), None, num(r["bid_size"]), num(r["ask_size"]), t)); c["polls"] += 1
    for tk, (s, ev, kind, strike) in mk.items(): o.execute("insert into market values(?,?,?,?,?,?,?,?)", (tk, s, None, None, "ingame", ev, kind, strike))
    o.commit(); o.execute("create index ix on candle(ticker)"); o.commit(); o.execute("vacuum"); o.close()
    sha = hashlib.sha256(open(dst, "rb").read()).hexdigest(); db = sqlite3.connect(dst)
    by = db.execute("select m.series,m.kind,count(distinct m.ticker),count(*),min(c.t_recv_ms),max(c.t_recv_ms) from market m join candle c on c.ticker=m.ticker group by m.series,m.kind order by m.series,m.kind").fetchall()
    L = {"tag": tag, "files_read": nfiles, "cut_ms": CUT_MS, "counts": dict(c), "by_series_kind": by, "markets": len(mk), "extract_sha256": sha}
    json.dump(L, open(os.path.join(out, "ENGINE1_ingame_%s_cutlog.json" % tag), "w"), indent=1)
    print(json.dumps({"files": nfiles, "counts": dict(c), "markets": len(mk), "sha": sha}, indent=1)); [print(r) for r in by]
if __name__ == "__main__": main(sys.argv[1:])

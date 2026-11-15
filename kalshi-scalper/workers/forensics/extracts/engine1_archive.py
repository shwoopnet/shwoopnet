#!/usr/bin/env python3
"""ENGINE1 extract (a): the 19 archive 15 minute series in ONE schema (Forensics desk, Nov 15, 2026; the Head's order).
Schema: market(ticker, series, close_ts, result, src); candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi). Closes before 2026-10-03T00:00Z (KXSOL15M before 2026-09-30T09:30Z). Fixed source order l1b, book, e3b, alts4, alts2, alts3, rep (first source wins on a duplicate ticker).
Candles ending after the market's close are DROPPED and counted. Only the columns above are read. usage: python3 -I engine1_archive.py <archive_dir> <out_dir>"""
import sys, os, sqlite3, json, hashlib, collections
SERIES = ["KXBTC15M", "KXBNB15M", "KXCOPPER15M", "KXDOGE15M", "KXETH15M", "KXEURUSD15M", "KXGBPUSD15M", "KXGOLD15M", "KXHYPE15M", "KXNATGAS15M", "KXNEAR15M", "KXPALLADIUM15M", "KXPLATINUM15M", "KXSILVER15M", "KXSOL15M", "KXUSDJPY15M", "KXWTI15M", "KXXRP15M", "KXZEC15M"]
SOURCES = ["l1b", "book", "e3b", "alts4", "alts2", "alts3", "rep"]
CUT, SOL_CUT = 1790985600, 1790760600
def main(a):
    arch, out = a[0], a[1]; os.makedirs(out, exist_ok=True); dst = os.path.join(out, "ENGINE1_archive_extract.sqlite")
    if os.path.exists(dst): os.remove(dst)
    o = sqlite3.connect(dst); o.execute("create table market(ticker, series, close_ts, result, src)"); o.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    seen = set(); cnt = collections.Counter(); per = collections.Counter()
    for s in SOURCES:
        c = sqlite3.connect("file:%s?mode=ro" % os.path.join(arch, s + ".sqlite"), uri=True)
        for ser in SERIES:
            cut = SOL_CUT if ser == "KXSOL15M" else CUT
            ts = {}
            for tk, close, res in c.execute("select ticker, close_ts, result from market where series=? and close_ts<?", (ser, cut)):
                if tk in seen: cnt["duplicate_later_source"] += 1; continue
                seen.add(tk); ts[tk] = close; o.execute("insert into market values(?,?,?,?,?)", (tk, ser, close, res, s)); per[(ser, s)] += 1
            for tk, end, b, k, last, v, oi in c.execute("select c.ticker, c.end_ts, c.bid_c, c.ask_c, c.price_c, c.volume, c.oi from candle c join market m on m.ticker=c.ticker where m.series=? and m.close_ts<? order by c.ticker, c.end_ts", (ser, cut)):
                if tk not in ts: continue
                if end > ts[tk]: cnt["post_close_candle_dropped"] += 1; continue
                o.execute("insert into candle values(?,?,?,?,?,?,?)", (tk, end, b, k, last, v, oi)); cnt["candles"] += 1
    o.commit(); o.execute("create index ix on candle(ticker)"); o.commit(); o.execute("vacuum"); o.close()
    sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()
    c = sqlite3.connect(dst); by = c.execute("select series,count(*),min(close_ts),max(close_ts) from market group by series order by series").fetchall()
    L = {"extract": "ENGINE1 archive", "sources_in_order": SOURCES, "series": SERIES, "cut": CUT, "sol_cut": SOL_CUT, "counts": dict(cnt), "markets_by_series": by, "markets": c.execute("select count(*) from market").fetchone()[0], "extract_sha256": sha,
         "from_source": [[k[0], k[1], v] for k, v in sorted(per.items())]}
    json.dump(L, open(os.path.join(out, "ENGINE1_archive_cutlog.json"), "w"), indent=1); print(L["markets"], dict(cnt), sha)
    for r in by: print(r)
if __name__ == "__main__": main(sys.argv[1:])

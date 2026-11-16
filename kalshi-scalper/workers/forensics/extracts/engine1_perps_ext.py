#!/usr/bin/env python3
"""ENGINE1 extract (c) EXTENSION: KXUS500PERP and KXUSTECH100PERP (the owner released EVM4, Nov 16, 2026; Forensics desk). KXGOLDPERP has NO rows in kalshi1m (the perps candle recorder takes only the Equities and Indices classes, plus a few others), so it is not in this file. Same schema and rules as engine1_perps.py; the original four-perp extract is untouched.
Schema as the archive extract: market(ticker, series, close_ts, result, src) with close_ts and result NULL (perps have no settlement), candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi) = bid_close, ask_close, price_close, volume, open_interest of the 1 minute candle. Prices are in dollars of the underlying, NOT on a 0 to 1 scale.
Duplicate (ticker, end_ts) rows across daily files are kept once (first file wins) and counted. A candle with a missing bid or ask is kept with NULLs and counted. usage: python3 -I engine1_perps.py <perp-data dir> <out_dir>"""
import sys, os, csv, gzip, glob, sqlite3, json, hashlib, collections
T = ["KXUS500PERP", "KXUSTECH100PERP"]
def num(x):
    try: return float(x) if x not in ("", None) else None
    except ValueError: return None
def main(a):
    root, out = a[0], a[1]; os.makedirs(out, exist_ok=True); dst = os.path.join(out, "ENGINE1_perps_ext_extract.sqlite")
    if os.path.exists(dst): os.remove(dst)
    o = sqlite3.connect(dst); o.execute("create table market(ticker, series, close_ts, result, src)"); o.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    for t in T: o.execute("insert into market values(?,?,?,?,?)", (t, t, None, None, "kalshi1m"))
    seen = set(); cnt = collections.Counter(); files = []
    for p in sorted(glob.glob(os.path.join(root, "kalshi1m", "*.csv.gz"))):
        files.append(os.path.basename(p))
        for r in csv.DictReader(gzip.open(p, "rt", newline="")):
            if r["ticker"] not in T: continue
            k = (r["ticker"], int(r["end_period_ts"]))
            if k in seen: cnt["duplicate_row"] += 1; continue
            seen.add(k); b, s = num(r["bid_close"]), num(r["ask_close"])
            if b is None or s is None: cnt["missing_bid_or_ask"] += 1
            o.execute("insert into candle values(?,?,?,?,?,?,?)", (k[0], k[1], b, s, num(r["price_close"]), num(r["volume"]), num(r["open_interest"]))); cnt["candles"] += 1
    o.commit(); o.execute("create index ix on candle(ticker)"); o.commit(); o.execute("vacuum"); o.close()
    sha = hashlib.sha256(open(dst, "rb").read()).hexdigest(); c = sqlite3.connect(dst)
    by = c.execute("select ticker,count(*),min(end_ts),max(end_ts),sum(yes_bid is null or yes_ask is null),sum(oi is not null) from candle group by ticker order by ticker").fetchall()
    L = {"extract": "ENGINE1 perps extension (index perps)", "files": files, "tickers": T, "counts": dict(cnt), "by_ticker": by, "extract_sha256": sha}
    json.dump(L, open(os.path.join(out, "ENGINE1_perps_ext_cutlog.json"), "w"), indent=1); print(dict(cnt), sha); [print(r) for r in by]
if __name__ == "__main__": main(sys.argv[1:])

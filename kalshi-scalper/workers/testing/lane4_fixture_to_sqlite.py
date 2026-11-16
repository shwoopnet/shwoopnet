#!/usr/bin/env python3
"""Converts lane4_fixture_second.json.gz to the sqlite layout Forensics' second build reads: candle(ticker, end_ts, yes_bid, yes_ask), funding(ticker, ts, rate), underlying(ticker, et_date, u_open, u_prev). Usage: lane4_fixture_to_sqlite.py <fixture.json.gz> <out.sqlite>"""
import gzip, json, sqlite3, sys, time
J = json.load(gzip.open(sys.argv[1])); db = sqlite3.connect(sys.argv[2])
db.execute("create table candle(ticker, end_ts, yes_bid, yes_ask)"); db.execute("create table funding(ticker, ts, rate)"); db.execute("create table underlying(ticker, et_date, u_open, u_prev)")
for n, s in J["data"].items(): db.executemany("insert into candle values (?,?,?,?)", [(n, int(t), v[0], v[1]) for t, v in s.items()])
for n, f in J["funding"].items(): db.executemany("insert into funding values (?,?,?)", [(n, int(t), r) for t, r in f.items()])
for n, u in J["under"].items(): db.executemany("insert into underlying values (?,?,?,?)", [(n, time.strftime("%Y-%m-%d", time.gmtime(int(L) * 86400)), v[0], v[1]) for L, v in u.items()])
db.commit(); db.close()

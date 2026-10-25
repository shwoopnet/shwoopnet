"""SEARCH5K data (README, Pre-registration: SEARCH5K): Deribit perpetual 1 minute OHLCV, funding history and DVOL OHLC for Bitcoin and Ethereum.
Research only. Resumable. python -m scalper.search5k_fetch"""
from __future__ import annotations

import sqlite3
import time

from .iv1 import _get
from .paths import DATA_DIR

DB = DATA_DIR / "search5k.sqlite"
INST = {"BTC": "BTC-PERPETUAL", "ETH": "ETH-PERPETUAL"}


def main(days: int = 82) -> None:
    con = sqlite3.connect(DB)
    con.execute("create table if not exists bar(cur text, ts integer, o real, h real, l real, c real, v real, primary key(cur, ts))")
    con.execute("create table if not exists fund(cur text, ts integer, i8 real, i1 real, idx real, primary key(cur, ts))")
    con.execute("create table if not exists dv(cur text, ts integer, o real, h real, l real, c real, primary key(cur, ts))")
    end = int(time.time()) * 1000
    start0 = end - days * 86_400_000
    for cur, inst in INST.items():
        have = con.execute("select max(ts) from bar where cur=?", (cur,)).fetchone()[0]
        t = (have + 60_000) if have else start0
        while t < end:
            t2 = min(end, t + 4_000 * 60_000)
            d = _get(f"https://www.deribit.com/api/v2/public/get_tradingview_chart_data?instrument_name={inst}&start_timestamp={t}&end_timestamp={t2}&resolution=1")["result"]
            con.executemany("insert or ignore into bar values (?,?,?,?,?,?,?)", [(cur, int(a), o, h, l, c, v) for a, o, h, l, c, v in zip(d["ticks"], d["open"], d["high"], d["low"], d["close"], d["volume"])])
            con.commit()
            t = t2 + 60_000
        have = con.execute("select max(ts) from fund where cur=?", (cur,)).fetchone()[0]
        t = (have + 3_600_000) if have else start0
        while t < end:
            t2 = min(end, t + 30 * 86_400_000)
            d = _get(f"https://www.deribit.com/api/v2/public/get_funding_rate_history?instrument_name={inst}&start_timestamp={t}&end_timestamp={t2}")["result"]
            con.executemany("insert or ignore into fund values (?,?,?,?,?)", [(cur, int(x["timestamp"]), x["interest_8h"], x["interest_1h"], x["index_price"]) for x in d])
            con.commit()
            t = t2 + 1000
        have = con.execute("select max(ts) from dv where cur=?", (cur,)).fetchone()[0]
        t = (have + 60_000) if have else start0
        while t < end:
            t2 = min(end, t + 900 * 60_000)
            d = _get(f"https://www.deribit.com/api/v2/public/get_volatility_index_data?currency={cur}&start_timestamp={t}&end_timestamp={t2}&resolution=60")["result"]["data"]
            con.executemany("insert or ignore into dv values (?,?,?,?,?,?)", [(cur, int(x[0]), x[1], x[2], x[3], x[4]) for x in d])
            con.commit()
            t = t2 + 60_000
        for tb in ("bar", "fund", "dv"):
            print(cur, tb, con.execute(f"select count(*) from {tb} where cur=?", (cur,)).fetchone()[0], flush=True)


if __name__ == "__main__":
    main()

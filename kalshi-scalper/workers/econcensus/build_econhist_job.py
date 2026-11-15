#!/usr/bin/env python3
"""Builds ECONHIST_LISTS (Desk B, Nov 15, 2026, the Head's GO): the historical (pre 2026-09-10) markets of 10 US release series. Lists only; no candle.
The historical endpoint takes no date bound, so the whole history comes back; every held-out window is cut in the READER by close_time first (reader: econhist_table.py)."""
import json, sys
SERIES = ["KXCPI", "KXPAYROLLS", "KXPCECORE", "KXJOBLESSCLAIMS", "KXCONTCLAIMS", "KXUE", "KXISMPMI", "KXUSISMSERV", "KXUSPPIYOY", "KXCPINDEX"]
PAGES = {"KXJOBLESSCLAIMS": 4, "KXCONTCLAIMS": 4}
def job():
    req = [{"id": "hist_" + s, "path": "/historical/markets", "params": {"series_ticker": s, "limit": 1000}, "max_pages": PAGES.get(s, 3)} for s in SERIES]
    cap = sum(r["max_pages"] for r in req)
    return {"job_id": "ECONHIST_LISTS", "owner": "DESK_B", "status": "active", "registration": "kalshi-scalper/workers/econcensus/ECONHIST_NOTE.md",
            "purpose": "Stage 2 of the economics census: the historical markets of 10 US release series (CPI, payrolls, core PCE, two claims series, unemployment, two ISM, PPI, CPI index) to count releases and markets. Lists only, no candle, no Fed series.",
            "heldout": "The historical endpoint cannot take a date bound, so the raw pages carry every close up to 2026-09-10, including results of windows other cards hold out. The READER cuts by close_time FIRST (before any other field) at every held-out date Auditor B's map names; the raw pages stay in the run's scratch; the run goes on HELDOUT_PULL_RUNS.md as LOADED, read only for tickers, close times and counts. No Fed series is requested.",
            "allowed_endpoints": [{"name": "hist_markets_list", "method": "GET", "path_pattern": "/historical/markets", "params_allowed": ["series_ticker", "limit", "cursor"]}],
            "series_allowlist": SERIES, "ticker_allowlist": [], "max_requests": cap + 12,
            "notes": "At most %d pages plus 12 for repeats after a 429; at 5 s about %d minutes. A series with fewer pages stops at its cursor's end." % (cap, (cap + 12) * 5 // 60 + 1),
            "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
            "requests": req}
if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "ECONHIST_LISTS.json"; j = job(); json.dump(j, open(out, "w"), indent=1); print(out, "max_requests", j["max_requests"], "requests", len(j["requests"]))

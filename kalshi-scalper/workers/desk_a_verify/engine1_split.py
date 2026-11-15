"""ENGINE1 split constants (Desk A, Nov 15 2026), written from Forensics' cut-log ranges (market close dates only) BEFORE any candle or result is read.
SEARCH = a market's UTC close date at or before the series' LAST_SEARCH date; VALIDATE = every later date. The last SEARCH date is the floor(D/2)-th distinct UTC close date (D from the extract's log).
Perps: the UTC date of the ENTRY candle's end_ts, same rule. Thin series (D under 20) are listed; the n >= 100 gate will drop most of their cells."""
import time
D = {"BNB": 58, "BTC": 58, "COPPER": 36, "DOGE": 58, "ETH": 58, "EURUSD": 9, "GBPUSD": 9, "GOLD": 56, "HYPE": 58, "NATGAS": 37, "NEAR": 58, "PALLADIUM": 14, "PLATINUM": 14, "SILVER": 56, "SOL": 45, "USDJPY": 9, "WTI": 57, "XRP": 58, "ZEC": 58, "SPYPERP": 8, "QQQPERP": 8, "NVDAPERP": 7, "AAPLPERP": 7}
LAST_SEARCH = {"BNB": "2026-09-03", "BTC": "2026-09-03", "COPPER": "2026-09-13", "DOGE": "2026-09-03", "ETH": "2026-09-03", "EURUSD": "2026-09-27", "GBPUSD": "2026-09-27", "GOLD": "2026-09-03", "HYPE": "2026-09-03", "NATGAS": "2026-09-13", "NEAR": "2026-09-03", "PALLADIUM": "2026-09-24", "PLATINUM": "2026-09-24", "SILVER": "2026-09-03", "SOL": "2026-09-07", "USDJPY": "2026-09-27", "WTI": "2026-09-03", "XRP": "2026-09-03", "ZEC": "2026-09-03", "SPYPERP": "2026-11-10", "QQQPERP": "2026-11-10", "NVDAPERP": "2026-11-09", "AAPLPERP": "2026-11-09"}
THIN = tuple(k for k, v in D.items() if v < 20)
def phase(series, ts):
    d = time.strftime("%Y-%m-%d", time.gmtime(ts))
    return "search" if d <= LAST_SEARCH[series] else "validate"

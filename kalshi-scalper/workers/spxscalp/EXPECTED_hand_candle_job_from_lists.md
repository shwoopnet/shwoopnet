# SPXOI1 candle job builder fix: hand case, written BEFORE the builder code

Problem (Auditor B, Nov 14): the first SPXOI1_CANDLES job built each ticker from the close minute (-00, -15, -45) and 10 Nov 5 tickers did not exist (the listed suffix was -30), so those windows came back empty. Fix: the builder takes each ticker EXACTLY as listed in a lists run and never rebuilds one from a minute. It reads only the ticker and the close_time of each listed KXINX15M market (no price, no result, no other field).

Made-up fixture lists (3 markets, listed out of order): KXINX15M-26NOV051330-30 closes 2026-11-05T18:30:00Z; KXINX15M-26NOV051300-30 closes 2026-11-05T18:00:00Z (the minute says 00, the suffix says 30); KXINX15M-26NOV051315-15 closes 2026-11-05T18:15:00Z. A fourth listed market KXINXU-26NOV05H1300-T7000 (another series) and a KXINX15M market closing 2026-11-14T15:00:00Z (outside the dates) must be left out.

Expected requests, sorted by close time, ids c001.., one ticker a request, period_interval 1, start_ts = close - 1800, end_ts = close - 120 (the Auditor B recommendation already in the job):
- c001: KXINX15M-26NOV051300-30, start_ts 1793899800, end_ts 1793901480 (close 1793901600).
- c002: KXINX15M-26NOV051315-15, start_ts 1793900700, end_ts 1793902380 (close 1793902500).
- c003: KXINX15M-26NOV051330-30, start_ts 1793901600, end_ts 1793903280 (close 1793903400).
max_requests = 3. The builder must STOP if a listed ticker repeats across the run's files, if a market's series is not KXINX15M, or if no market is kept. Every ticker in the output must equal a listed ticker (a gate the builder checks before it writes).

## Addendum (Nov 14, before the code change): --exclude-job
The owner approved a 10-request patch pull for the Nov 5 windows whose first job asked a wrong ticker. The builder gets `--exclude-job OLDJOB.json`: every ticker already asked in the old job is left out, so the patch asks only the tickers the first job did not ask. Hand case on the same made-up lists with an old job that asked KXINX15M-26NOV051300-00 (wrong), KXINX15M-26NOV051315-15 (right, listed) and KXINX15M-26NOV051330-30 (right, listed): expected output is ONE request, c001 KXINX15M-26NOV051300-30, start_ts 1793899800, end_ts 1793901480, max_requests 1. (A request whose ticker equals a listed ticker is dropped as already asked; the wrong -00 ticker does not match any listed one, so it removes nothing.) If the exclusion leaves no request the builder STOPS.

## Addendum 2 (Nov 14, before the code change): ticker_allowlist
The runner's check refuses a request whose ticker is not in the job's own ticker_allowlist, and the template's list still held the OLD (wrong) tickers. The builder must therefore set ticker_allowlist to exactly the requested tickers, sorted, so the allowlist and the requests agree. Hand case (same made-up lists, no exclusion): ticker_allowlist = [KXINX15M-26NOV051300-30, KXINX15M-26NOV051315-15, KXINX15M-26NOV051330-30]; with the exclusion case: [KXINX15M-26NOV051300-30]. The runner's check_job must accept the output.

# HISTETH1 PROTOCOL (registered Nov 8, 2026, before any rule is scored)

The ETH replication of HISTBTC1 (`workers/HISTBTC1_PROTOCOL.md`), same everything except the series. Research only, no trading code, no key, no order, no fetching in this task. Real Kalshi candle quotes, entry at the actual ask. Caveat on every result: /historical feed, Jun to Aug 2026, a quote regime that may differ from today's.

Data: data/hist15/KXETH15M.sqlite, 6,267 settled markets with candles, closes 2026-05-31 to 2026-08-05. Adapter `hist_eth_cheap` (`scan.HIST_ETH`): same cut as BTC, dev = closes before 2026-07-15 (ts 1784073600; 45 dates, 23,675 cheap-side rows, W1/W2/W3 = 7,891 / 7,976 / 7,808, thirds of the dev dates); held-out = closes from 2026-07-15 (2,079 markets), behind `scan.guard_check`, read ONCE. Only row counts were looked at, no outcome. Cheap side only (ask 3c to 30c), looks 840 to 180 s, one contract, taker at the ask, rounded fee, x1.2 stress, held to settlement. Harness bar unchanged: PF 1.5 in each of W1, W2, W3, floors 40 / 150 / 3 dates, deflated by the one-sided Bonferroni z at 0.05 / N.

Runs: 3 x 10,000 distinct rules, seeds 81201, 81202, 81203 (30,000 rules, N 1,320,505 to about 1,350,505, z about 5.38). Every run appends to the ledger before scoring. Survivors (if any): freeze, audit (7 hooks), then the held-out ONCE. No second try on this data.

Prediction (before scoring): zero survivors (about 85%), as for BTC. Kill rule: zero survivors closes the 15 minute ETH cheap-side family on this data; two NOT_ENOUGH_DATA in a row from this source closes it. A survivor must also hold on the Oct 2026 fresh data before anything is claimed. No promote verb.

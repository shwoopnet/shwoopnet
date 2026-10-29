# FALS1 registration: falsifier for MKTTIME1's gold 20:00 to 24:00 Central block (Strategy Research V2, 2026-10-29, research only)

Written before any scoring by this worker. `src/scalper/mkttime1.py` and `tstop1.py` are NOT read until the independent version below has produced its numbers.

**Lead under attack.** MKTTIME1: skipping KXGOLD15M L1 entries whose entry time (close minus 360 s) falls 20:00 to 24:00 US Central lifted gold's PF in all three close-date thirds (+0.19, +0.14, +0.11), 24 losses among 315 skipped entries, day-clustered z +0.98. The job is to break it, not confirm it.

**Counterparty claimed by the lead.** Thin gold quoting in the US evening / Asia morning (01:00 to 05:00 UTC). Honest alternative: chance.

## Reimplementation (try 1)

- Data: `data/l1b.sqlite`, `data/book.sqlite`, `data/fresh.sqlite`, `data/rep.sqlite` (rep holds no gold). Universe: every KXGOLD15M market with result yes/no; a ticker in more than one database is taken once (from the database with more candles for it, ties to the earlier database).
- Signal candle: the candle with `end_ts == close_ts - 360` exactly; no such candle means no entry. YES ask = `ask_c`; NO ask = `1 - bid_c`. Buy the side whose ask is in [0.88, 0.97] (if both are, the higher ask; counted and reported). Fill at that ask, hold to settlement, 1 contract. Fee = ceil(7 x C x p x (1-p) cents) per order.
- Block = US Central (America/Chicago) hour of the entry time; 20-24 means hour 20 to 23.
- Thirds: distinct UTC close dates of gold entries, sorted, split into three equal-count groups (A, B, C).
- PF = gross wins / gross losses of the net per entry. Lift = PF(kept) - PF(all). Net kept share = net(kept) / net(all).
- Day-clustered z: (mean per entry of the rest - mean of the block) over its standard error clustered by Central date (two-sample, cluster-robust).

## Robustness checks (each fixed now, each one try)

- (a) DST: report the UTC offsets present in the entries. Expectation stated now: the history ends before 2026-11-01 (the US change), so every entry is CDT (UTC-5) and this check cannot break the lead; not a try beyond stating it.
- (b1) block 19:00 to 23:00 CT; (b2) block 21:00 to 01:00 CT. Each: per-third lift.
- (c) fill at the ask of the next candle (`end_ts == close_ts - 300`) for the side chosen at the signal; no entry if that candle is missing or the ask is 1.00 or more.
- (d) 10 contracts (fee rounded at C = 10).
- (e) fees x1.2 (rounded up after the multiplier).
- (f) entries whose signal candle has volume 0 dropped (and the count reported).
- (g) day-block bootstrap: resample Central dates with replacement, 2,000 times, seed 1; report the pooled PF lift's 2.5 / 50 / 97.5 percentiles, the share of resamples with pooled lift at or below 0, and (resampling days within each third) the share with lift at least 0.10 in all three thirds.
- (h) permutation: within each Central weekday, shuffle the 6 block labels among gold's entries, 1,000 times, seed 2. Statistic S = max over the 6 blocks of (min over thirds of the PF lift). p = share of permutations with S at least the observed S of the 20-24 block. Also reported: the share where any block has lift at least the observed lift in each third separately.
- (i) price and spread: mean price paid and mean spread (YES ask - YES bid at the signal candle) inside vs outside the block; the block-vs-rest per-entry mean difference within price buckets 0.88-0.90, 0.91-0.93, 0.94-0.97 and within spread at or below vs above the median.

## Kill criteria (BROKEN)

The lead is BROKEN if any of: the reimplementation fails to reproduce a lift of at least 0.10 in all three thirds; (b1) or (b2) shows the lift is a knife edge (lift below 0.05 in any third for BOTH shifted blocks); (c), (d), (e) or (f) turns any third's lift below 0.10 or net kept share below 70%; (g) share of pooled lift at or below 0 above 20%; (h) p above 0.10; (i) the block-vs-rest gap vanishes (same sign in fewer than 2 of 3 price buckets).

Otherwise: SURVIVES THE FALSIFIER, which leaves it only the registered forward test MKTTIME1-F, never a live change. Verdict word for the lead in the ledger stays FALSIFIED as MKTTIME1 registered it (statistics far from the deflated bar).

**Prediction (stated now):** reproduces within a few hundredths; at least one of (g) or (h) breaks it (p above 0.10), because 24 losses carry the whole effect.

**Tries:** 1 reimplementation + b1, b2, c, d, e, f, g, h, i = 10 tries (running count about 438,905 + 10 = about 438,915).

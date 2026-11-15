# CALIB1: underdog-bias calibration census on the 15 minute candles we already hold (History Miner, card written 2026-11-15 ~16:10Z; the Head's brief of 16:04Z; NOT run until the Head says go)

**What it is.** A descriptive calibration table, not a rule. No try is counted until a rule is registered from it, in its own card, before any held-out read. It asks whether the side priced at x actually wins about x of the time, by series, price and time left.

## Data and cuts (the same as UNDERDOG2X, Amendments 1 and 2)
- research-data archive (Oct 29, WHOLE sha256 15788a025e39d48725...), sources l1b, book, e3b, alts4, alts2, alts3, rep, first source wins on a duplicate ticker; candles after a close dropped.
- The same 19 series. Cut: closes before 2026-10-03T00:00Z, except KXSOL15M before 2026-09-30T09:30:00Z (GEN13's unread held-out).
- The same per-series thirds (UNDERDOG2X registration section 2). **Thirds 1 and 2 only.** Every third-3 market is dropped in the first pass (ticker, series, close only) before any candle or result is read, as in underdog2x.load().
- **Held-out confirmation:** Auditor B confirmed these cuts for the 19 series at 16:01Z and 16:03Z (no OPEN card's window before Oct 3, SOL's own cut). CALIB1 reads the same rows plus no new column (yes_bid, yes_ask, result), so I ask Auditor B only to confirm that this still holds before the run.

## Looks, sides, buckets
- **Looks:** the candle ending EXACTLY close - 600 s (10 min), close - 300 s (5 min), close - 120 s (2 min). A missing look candle, or one that is not two-sided (0 < bid < ask < 1), gives no row, counted per look as "missing" or "not two-sided". Nothing is carried from another minute.
- **Both sides per look:** the YES side at its ask (yes_ask) and the NO side at its ask (1 - yes_bid). A market adds up to 2 observations per look (one per side) and up to 3 looks.
- **Buckets:** the side's ask in 5c buckets [0.00, 0.05), [0.05, 0.10), ..., [0.95, 1.00); each edge belongs to the higher bucket, with 1e-9 slack.
- **Outcome:** the side wins if the market's result is that side. Voids (no yes or no result) are excluded and counted.

## Printed per series (and pooled over the 19), per look, per bucket, per third (1, 2) and thirds 1+2
- n; wins; win rate w; mean ask a; gap g = w - a (in cents);
- the mean per-contract fee at the ask, rounded per order at 1 contract (ceil(100 x 0.07 x a(1 - a)) / 100), averaged over the bucket's rows;
- a binomial z of the gap, (wins - sum of asks) / sqrt(sum a(1 - a)). It is stated as NOT independent: see the caveats.
- Also the bucket's median spread at the look.

## What a "mispriced bucket" would need (fixed now, before any read)
A bucket (series or pooled, one look, one side's price range) is a CANDIDATE for a rule card only if ALL hold:
1. at least 300 observations in third 1 AND at least 300 in third 2;
2. in EACH of thirds 1 and 2, the gap g is above the bucket's mean fee + 2c (the C7 haircut covering spread and slip). For a buy, g >= fee + 0.02. For the opposite trade (selling the side, which is buying the other side at 1 - bid), the mirror bucket must meet the same test on its own side's row, never inferred;
3. the same sign in both thirds.

A candidate is only a candidate:
- the rule card is written from it before any held-out read;
- its tries are counted then (each look x bucket x side x series it chooses);
- it is read once on third 3 on the Head's go.

The table itself counts no try, but **the number of buckets inspected is printed (19 series + pooled) x 3 looks x 20 buckets x 2 sides**, so the later rule's deflation can count what was looked at.

## Caveats stated now
- **Not independent:** the YES and NO rows of one market at one look are the same event; the three looks of one market share an outcome; one series' markets in one window move together. The z is a screen, not a test; a rule card must use clustered statistics (by market close day).
- **Candle ask, not book:** the C2 1c entry haircut is not applied in the table; the 2c in point 2 covers it and the spread.
- **Thin series:** the FX pairs, platinum and palladium have 10 to 15 days and will rarely reach 300 a third. That is stated, not padded.
- **Selection:** any later rule chosen from this table is selected on thirds 1 and 2, so third 3 is its only clean test.

## Gate
- One build (this desk), a hand case before the code, Auditor B's CLEAN and the held-out reconfirmation, the Head's go.
- The table is committed blind and figures go by message only. No live figure.

## Amendment 1 (the Head, 16:05Z: approved as written, GO on conditions)
- Every candidate bucket is reported WITH its two neighbours (the buckets on either side, same series or pool, same look, same side), so a lone spike reads differently from a smooth slope. The print carries, for each candidate, the neighbours' n, win rate, mean ask and gap in each third.
- Third 3 stays unread for any later rule card.

## Amendment 2 (2026-11-15 ~16:25Z, Auditor B's points of 16:05Z, before the code is cleared and before any read)
1. **Third 3 is shared with UNDERDOG2X.**
   - UNDERDOG2X was FALSIFIED on development (0 of 60, recorded by the Head at 16:04Z), so it has no passing variant and its third 3 is NOT read. A rule card from CALIB1 would therefore be the FIRST read of third 3.
   - The order is fixed: if UNDERDOG2X's third 3 were ever to be read, every CALIB1 candidate rule must first be registered (dated line, tries counted). After any read of third 3 for another card, a CALIB1 rule's read of it is a RE-USE, stated as such, and judged against a stricter bar set by the Head before that read.
2. **Expected chance candidates under the null:**
   - For each bucket with n >= 300 in both thirds, the code computes, assuming calibration (win probability = ask) and independent rows, P(pass third t) = 1 - Phi((fee_t + 0.02) / sd_t), with sd_t = sqrt(sum over rows of a(1 - a)) / n_t, and P(pass both) as the product of the two thirds.
   - Summed over all such buckets, this is printed as "expected_chance_candidates_null", beside the number of eligible buckets and the number of candidates found.
   - It UNDERSTATES the chance count, because rows are not independent (both sides of a market, three looks, markets of one window), and it is labelled so.
   - Example: 300 rows at 0.50 in each third (fee 2c, threshold 4c): sd 0.0289, z 1.386, P(one third) 0.0829, P(both) 0.0069.

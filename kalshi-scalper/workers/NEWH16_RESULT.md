# NEWH16 result (run once, 2026-10-30, research only)

Registration `workers/NEWH16_REGISTRATION.md` (commit 8180dda) and the code `src/scalper/newh16.py` were pushed before the run; the run's raw
output is the table below. Digest: `workers/NEWH16_DIGEST.md`. Times UTC unless stated. Fees 7% x C x p x (1 - p) rounded up per order, C = 10,
PF at fees x1.2 and C = 1 shown where they matter. Every fill was a coin flip price (35c to 65c). No fill candle had zero volume (all PF
"volume above 0" columns equal the headline). The frozen holdout (2026-10-18 on) was NOT read for any try, because no try passed both earlier
windows; the T3 Polymarket holdout fetch was therefore not made.

## Verdicts

| Try | Discovery (Aug 6 to Sep 21; T3 to Sep 14) | Validation (to Oct 18; T3 Sep 14 to Oct 13) | Verdict |
|---|---|---|---|
| T1 Bitcoin, 4 hour trend, FOLLOW | n 557, win 47.0% vs 49.5% paid, PF 0.84, x1.2 0.83, day z -2.97 | n 311, PF 0.99, z -0.14 | FALSIFIED (discovery PF) |
| T1 Bitcoin, 4 hour trend, FADE | n 560, win 51.4% vs 50.8%, PF 0.95, z -0.71 | n 315, PF 0.84, z -1.69 | FALSIFIED (discovery PF) |
| T1 gold, 4 hour trend, FOLLOW | n 399, win 43.1% vs 49.8%, PF 0.71, z -2.92 | n 146, PF 0.67, z -2.84 | FALSIFIED (discovery PF) |
| T1 gold, 4 hour trend, FADE | n 395, win 55.7% vs 50.7%, PF 1.14, x1.2 1.13, z +1.13 | n 145, win 56.6%, PF 1.18, z +1.03 | FALSIFIED (discovery PF 1.14 under 1.5) |
| T2 Bitcoin, fade the extreme previous move | n 118, win 55.1% vs 50.4%, PF 1.13, z +0.78 | n 80, win 48.7%, PF 0.84, z -0.64 | FALSIFIED (discovery PF) |
| T2 gold, fade the extreme previous move | n 94 (needs 100), PF 0.99 | n 33, PF 1.62 (not screened) | NOT_ENOUGH_DATA (discovery n 94) |
| T3 Bitcoin, Polymarket gap of 6c or more | n 625, win 49.9% vs 49.0%, PF 0.96, z -0.41 | n 428, PF 0.94, z -0.76 | FALSIFIED (discovery PF) |
| T3 Ethereum, Polymarket gap of 6c or more | n 516, win 49.6% vs 48.4%, PF 0.98, z -0.27 | n 393, PF 0.99, z -0.05 | FALSIFIED (discovery PF) |

Information only (not screened, not tries): T2 follow direction, Bitcoin discovery n 118 PF 0.65, validation n 80 PF 0.98; gold n 93 PF 0.93, n 34
PF 0.49. Cut points from discovery only: |4h move| 0.74% Bitcoin and 0.64% gold (80th percentile), |previous window move| 0.36% Bitcoin and 0.27% gold
(95th percentile). Data gaps (missing prior window or candle): T1 Bitcoin 129, gold 423; T2 Bitcoin 20, gold 55; T3 28 and 29. Fills refused by the
35c to 65c band: 100 to 700 per try.

## Reading

- The predictions held for seven of eight tries: PF between 0.67 and 1.14, win rate within about 5 points of the price paid, fees of 1.8c a contract
  at 50c taking the rest. Break even needs about 53.5 percent, the bar about 58 percent; the best win rate over 100 trades was 56.6 percent.
- **Gold fade is the one to remember, and it is not a lead.** The 4 hour trend faded on gold has the same sign in both windows (win 55.7% and 56.6%
  against 50.7% paid, PF 1.14 and 1.18, day z +1.13 and +1.03). It misses the registered PF 1.5 by a wide margin, so it is FALSIFIED and the holdout
  stays unread. Its opposite (follow) lost clearly in both windows (PF 0.71 and 0.67, z about -2.9 each), so the pair is a mirror and is one idea
  seen twice, tested at the price of two tries; the gold windows are 32 and 19 days, thin.
- T2 gold sits 6 trades under the discovery minimum by construction (the 95th percentile of a 6 week sample): NOT_ENOUGH_DATA, and no cut point was moved.
- T3 confirms PM1: Polymarket's price carries no usable information Kalshi's ask lacks (hit rate within one to two points of the price paid, in
  both windows, both coins). With only a midpoint on file the test is generous to the rule, and it still failed.

## Counts

Tries: 8 (T1 4, T2 2, T3 2). Looks: 2. New running count **about 728,658** (was about 728,648). Information lines add none. The deflated bar
(z about 5.27) was never reached by anything, so it was never the binding rule.

## Proposals for the owner (nothing built, nothing deployed)

1. **Venue settlement disagreement count (no trade, counts only).** Polymarket's 15 minute windows resolve on a Chainlink TWAP over the whole
   window; Kalshi on two one minute averages of a CF index. The public gamma API returns resolved outcomes. Joining them to `fresh.sqlite` results
   would say, for Bitcoin and Ethereum, how often the venues disagree and by what close margin; if it is more than a few percent in windows
   priced at 80c or more on both, a cross venue structure would exist to be priced. This needs no recorder, only a fetch of about 3,000 resolved
   event records; it can be a worker task.
2. **Polymarket book recorder, last 10 minutes of each window, Bitcoin and Ethereum** (best bid and ask with sizes from the public CLOB book, about
   every 5 seconds, public, no key, same pattern as `record_book.py`). Only with it can PMGAP-type tests use a price we could hit instead of a midpoint
   and a real fee. Worth it only if proposal 1 finds disagreement.
3. **Do not spend more tries on coin flip entries from trailing price features.** Eight more tries here and about 100 elsewhere (BTC1, QUIRK1, FLOW1,
   PERPFLOW1) agree with the fee arithmetic: a 50c taker entry needs a 58 percent hit rate and the literature's best documented 15 minute effects are
   worth 1 to 2 points. If the owner wants more search, the unexplored ground is structure (two venues, two settlement indexes, hourly against 15 minute
   ladders at the same instant), not another trailing feature.

## Proposed README section (for the lead to merge; this file is the only place it exists now)

```
## Result: NEWH16 (documented short horizon binary market edges, held coin flip entries; run once 2026-10-30; research only)

Registered first (`workers/NEWH16_REGISTRATION.md`, commit 8180dda; digest `workers/NEWH16_DIGEST.md` with the sources, none a tested edge at our cost).
Eight tries, all held to settlement at 35c to 65c asks: T1 four hour strike trend followed and faded (Bitcoin, gold), T2 fade of an extreme (top 5
percent) previous window (Bitcoin, gold), T3 Polymarket price 6c or more above Kalshi's ask (Bitcoin, Ethereum). Windows: discovery Aug 6 to Sep 21,
validation to Oct 18, holdout Oct 18 on (never read, nothing passed). 7 FALSIFIED (discovery PF 0.71 to 1.14, best win rate 56.6 percent against
a 53.5 percent break even), 1 NOT_ENOUGH_DATA (T2 gold, discovery n 94 of 100). Gold fade of the four hour trend kept its sign in both windows
(PF 1.14 and 1.18, z about +1.1 each) and is not a lead. Looks 2. Running count about 728,658. Nothing to build; two data proposals in the result file.
```

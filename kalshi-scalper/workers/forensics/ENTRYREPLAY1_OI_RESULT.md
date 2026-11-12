# ENTRYREPLAY1-OI result: OICORE's trigger windows against the same-week baseline (2026-11-12)

Registration: `ENTRYREPLAY1_OI_REGISTRATION.md` (commit f5eb01c, before anything was computed). Script `entryreplay1_oi.py`, raw output `results/ENTRYREPLAY1_OI.json`. Input: Refinement's public-data trigger list (commit 01fd17ac on `claude/refine-live`). Public data only, zero Kalshi requests, nothing about the live account: these are the MODEL's trigger windows, not the bot's orders. Tries: 1.

**The answer in one sentence.** It cannot be answered on the books held: only 14 trigger windows with the cheap side in the 8c to 50c band close before Nov 5, so the trigger-against-baseline comparison is "no evidence at n = 14".

## Why so few: the trigger mostly fires when the market is already decided

Of 937 Bitcoin 15 minute windows with a book at the look (closes Oct 29 22:15Z to Nov 11), 431 are trigger windows (46%). Where the cheap side's ask sat at the look (178 seconds before the close):

| Cheap side's ask at the look | Trigger windows | Other windows | Share of that row that is a trigger |
|---|---|---|---|
| 2c or less | 274 (63.6% of triggers) | 22 | 93% |
| 2c to 5c | 68 (15.8%) | 50 | 58% |
| 5c to 8c | 34 (7.9%) | 57 | 37% |
| 8c to 20c | 34 (7.9%) | 146 | 19% |
| 20c to 35c | 12 (2.8%) | 122 | 9% |
| 35c to 50c | 9 (2.1%) | 109 | 8% |

- **87% of trigger windows have the cheap side at 8c or less, 64% at 2c or less.** Open interest is counted in contracts, and a contract at 1c costs a cent, so a rise of 86,300 contracts is cheap to produce when one side is nearly worthless. The trigger is, for the most part, a marker of a market that is already decided.
- **Inside the band the rule may buy (8c to 50c) the trigger is rare and leans cheap:** 55 of 432 in-band windows (13%), 19% of the windows at 8c to 20c against 8% at 35c to 50c. So a trigger sample is priced lower than a baseline sample of the same band, and any comparison of the two has to be made within price buckets or it measures the price mix.
- The median open interest rise is larger where the price is lower (about 213,000 contracts at 2c or less, about 128,000 at 8c to 20c, about 102,000 at 35c to 50c).

## Part B, outcome (closes before Nov 5 only): no evidence at n = 14

| | Trigger windows in band | Other windows in band |
|---|---|---|
| Windows | 14 | 164 |
| Mean ask at the look | 18.5c | 26.1c |
| Taker at the look ask, cash PF | 2.31 (0.56 to 7.62) | 1.34 (0.94 to 1.87) |
| Taker, mean per contract | +16.2c (-8.6 to +43.9) | +5.6c (-1.4 to +12.9) |
| Resting buy (pessimistic), cash PF | 2.71 (0.65 to 8.79) | 1.48 (1.04 to 2.13) |
| Resting minus taker, same windows | +2.5c (+1.9 to +3.1) | +1.5c (+0.1 to +2.6) |

Trigger minus other, taker mean per contract: +10.6c, interval -14.4c to +37.1c. **By the registered rule this is "no evidence at n = 14".** The point estimate favours the trigger and means nothing at this count: 14 windows, a third of them winners, at a lower average price than the comparison group, in a week when the whole baseline ran hot (PF 1.34 here; the same baseline was 0.61 the week after, which this file does not re-read).

## Part A, execution, no outcome (closes to Nov 11): no sign the trigger minutes are harder to trade

| | Trigger windows in band (56) | Other windows in band (379) |
|---|---|---|
| Immediate-or-cancel, +1c limit, filled in full: 2 s / 6 s / 10 s | 80.4% / 76.8% / 69.6% | 75.5% / 71.2% / 70.2% |
| Limit at the ask seen: 2 s / 6 s / 10 s | 66.1% / 67.9% / 64.3% | 62.5% / 63.6% / 64.9% |
| Resting buy at the bid: orders filled | 56 of 56 | 98.2% |
| Price and fee saved on a resting fill | +1.7c (+0.9 to +2.5) | +2.2c (+1.9 to +2.6) |
| Mid of the bought side 30 s later | -0.8c (-3.9 to +2.3) | -0.6c (-2.0 to +0.8) |

With 56 trigger windows the intervals on the fill shares are about 10 points either way, so "no evidence at n = 56" of any difference. What can be said: nothing here suggests the taker miss rate is worse or the resting fill rarer when the trigger fires; every one of the 56 resting orders was traded through. The saving on a resting fill is a little smaller on trigger windows (1.7c against 2.2c) because the price, and so the fee, is lower.

## What would settle it

More closes. At about 4 in-band trigger windows a day, 100 need about 25 days of books. R6 records Bitcoin to Nov 20 and every close from Nov 5 on is inside the CFRTI held-out block until that read is done, so the earliest honest re-read is after Nov 20 with whatever has accrued (about 60 to 70 in-band trigger windows from Oct 29 to Nov 20, still under 100). The same comparison on Kalshi's 1 minute candles would have months of windows; whether a candle is a fair price is what CANDLEVSBOOK1 measures.

## Caveats

About 1.2% of windows in the list's date range were not examined by the open interest cache and count as "other" here. The cheap side and its price are taken from the book at 178 seconds; the bot's own decision price comes from a different read. Ten days of books with gaps. Not checked by the Verification Analyst.

# Size ladder review: gold and Dogecoin L1 orders, with real numbers (Oct 31, 2026, 9:40 PM CT; read only; no recommendation)

Source: the nightly report, `?hours=2160&orders=1` (the longest it allows; the first order in it is Oct 7, 2026), L1 gold and Dogecoin orders that filled and settled. 363 orders over 19 trading days, **17 losses** (10 gold, 7 Dogecoin). Balance used for percentages: $779 (the main session's figure). Dollars are after fees.

## 1. What the record shows by order size

| Market | Contracts | Orders | Lost | Loss rate | Net | Cents per contract | Average loss | Worst single |
|---|---|---|---|---|---|---|---|---|
| Gold | 1 to 5 | 52 | 3 | 5.8% | +$0.35 | +0.20 | -$3.64 | -$4.49 |
| Gold | 6 to 10 | 104 | 3 | 2.9% | +$28.63 | +3.44 | -$5.99 | -$9.44 |
| Gold | 11 to 15 | 50 | 4 | 8.0% | +$0.53 | +0.08 | -$8.88 | -$9.58 |
| Gold | 16 or more | 9 | 0 | 0% | +$12.97 | +7.13 | none | none |
| Dogecoin | 1 to 5 | 142 | 7 | 4.9% | +$7.38 | +1.85 | -$2.31 | -$3.93 |
| Dogecoin | 11 to 15 | 6 | 0 | 0% | +$4.48 | +5.82 | none | none |

Reading, with the caution it needs: a larger bucket is not a cleaner one. Gold at 11 to 15 contracts lost 4 of 50 orders and made almost nothing (+$0.53); gold at 6 to 10 lost 3 of 104 and made +$28.63; gold at 16 or more has 9 orders and no losses, which says nothing yet (nine orders). The buckets also come from different weeks, different balances and different prices, so differences between them are not a size effect I can prove. Dogecoin at ladder size is 6 orders, all wins, since Oct 30; before that it was 1 to 5 contracts.

The whole record holds only 17 losses. Every figure below that depends on a loss (worst day, drawdown) rests on a handful of events.

## 2. What a loss costs, in dollars

A full loss on a 93c contract is about 93c to 97c a contract; an early sell at the 25c line is about 68c to 75c a contract. Observed loss per contract on gold's four biggest losses: $0.74 (13 contracts), $0.94 (10), $0.69 (11), $0.79 (12). So one gold loss costs roughly **$0.70 to $0.95 times the order size**.

- Worst single loss in the record: **-$9.58** (gold, 13 contracts, Oct 25), 1.2% of $779.
- Worst calendar day (US Central) as traded: **-$7.26**, 0.9% of $779.
- Worst rolling 24 hours as traded: **-$11.30**, 1.5%.
- Maximum drawdown (peak to trough of cumulative result): **-$15.96**, 2.0%.
- Losses came in clusters in 4 stretches: Oct 21 (3 gold/Doge in 17 hours), Oct 26 (3 in 15 hours), Oct 27 to 28 (3 in 23 hours), Oct 30 (2 in 1 hour). The loss stop is 12% of the sizing base and counts an open window as lost.

## 3. What the ladder setting actually changes at today's balance

Order size is the smaller of two things (`l1Count`, kalshiLiveLib.js line 519): the cap from the ladder (balance divided by the dollars-per-contract step) and the 2% rule (2% of cash divided by about $0.93 a contract). The add-on from reinvested profit sits on top, at most a quarter of the base (line 531).

At $779:
| Step | Ladder cap | 2% rule | Base size | With the full add-on (a quarter) |
|---|---|---|---|---|
| $30 | 25 | 16 | **16** | 20 |
| $43 (now) | 18 | 16 | **16** | 20 |
| $60 | 12 | 16 | **12** | 15 |
| $80 | 9 | 16 | **9** | 11 |

So today **$30 and $43 give the same size**: the 2% rule is already the binding limit, the ladder cap is not. Only $60 and $80 would make orders smaller. This changes as the balance grows: the ladder cap overtakes the 2% rule only if the step is set above about $49.

Implied worst loss at those sizes, at $0.70 to $0.95 a contract, before and after the add-on:
- $30 or $43: 16 to 20 contracts, about **$11 to $19** (1.4% to 2.4% of $779)
- $60: 12 to 15 contracts, about **$8 to $14** (1.1% to 1.8%)
- $80: 9 to 11 contracts, about **$6 to $10** (0.8% to 1.3%)

The loss stop (12% of the base, about $94) and the window cap (5.5%, about $43 per window) are unchanged in all four.

## 4. Replay of the live record (in-sample, not a prediction)

Method (stated plainly): for each real filled order I kept its result per contract and re-scaled it to the size a setting would have allowed at a $779 balance, which is the smaller of the real contract count and the setting's cap. This can only make an order smaller, never larger, because the 2% rule at a lower past balance already limited the real size. It does NOT re-simulate the account balance, the 3 day steps, the add-on pool or fill rates, and it uses today's $779 for the cap on orders that were placed at much lower balances (about $200 to $500 for most of the record). Fractional contract counts (for example 6.65) are used as recorded.

**As traded** (gold and Dogecoin orders as they were sent):

| Step | Cap | Net | Worst day | Worst rolling 24h | Max drawdown | Worst single loss |
|---|---|---|---|---|---|---|
| $30 | 25 | +$54.09 | -$7.26 (-0.9%) | -$11.30 (-1.5%) | -$15.96 (-2.0%) | -$9.58 |
| $43 | 18 | +$52.96 | -$7.26 (-0.9%) | -$11.30 (-1.5%) | -$15.96 (-2.0%) | -$9.58 |
| $60 | 12 | +$47.86 | -$7.56 (-1.0%) | -$10.86 (-1.4%) | -$15.52 (-2.0%) | -$9.53 |
| $80 | 9 | +$45.09 | -$7.03 (-0.9%) | -$9.27 (-1.2%) | -$11.50 (-1.5%) | -$8.50 |

**With Dogecoin resized to ladder size** (each Dogecoin order re-scaled to the smaller of 13 contracts and the cap, since Dogecoin moved onto gold's ladder on Oct 30; a stretch, because 142 of its 148 orders were 1 to 5 contracts and fills may differ at 13):

| Step | Cap | Net | Worst day | Worst rolling 24h | Max drawdown | Worst single loss |
|---|---|---|---|---|---|---|
| $30 | 25 | +$88.49 | -$7.04 (-0.9%) | -$9.90 (-1.3%) | -$18.33 (-2.4%) | -$11.39 |
| $43 | 18 | +$87.36 | -$7.04 (-0.9%) | -$9.90 (-1.3%) | -$18.33 (-2.4%) | -$11.39 |
| $60 | 12 | +$78.96 | -$7.02 (-0.9%) | -$9.60 (-1.2%) | -$16.92 (-2.2%) | -$10.51 |
| $80 | 9 | +$66.56 | -$6.98 (-0.9%) | -$8.43 (-1.1%) | -$12.69 (-1.6%) | -$8.50 |

Why the worst days barely move: in the real record most orders were already at or below 12 contracts, so a cap of 12 or 9 changes few of them. The loss-making orders were mostly 3 to 13 contracts.

## 5. Plain table: what each setting would have earned and what its worst day would have cost

| Setting | Implied order size today (with add-on) | Replay net, as traded | Replay net, Dogecoin at ladder size | Worst day (as traded / Dogecoin ladder) | Worst day % of $779 | Worst rolling 24h |
|---|---|---|---|---|---|---|
| $30 | 16 (20) | +$54.09 | +$88.49 | -$7.26 / -$7.04 | 0.9% | -$11.30 / -$9.90 |
| $43 (now) | 16 (20) | +$52.96 | +$87.36 | -$7.26 / -$7.04 | 0.9% | -$11.30 / -$9.90 |
| $60 | 12 (15) | +$47.86 | +$78.96 | -$7.56 / -$7.02 | 1.0% / 0.9% | -$10.86 / -$9.60 |
| $80 | 9 (11) | +$45.09 | +$66.56 | -$7.03 / -$6.98 | 0.9% | -$9.27 / -$8.43 |

## 6. Why this replay is weak, and what it cannot say

- **17 losses in 19 days.** One more loss or one fewer moves every worst-day figure. Any gap between settings smaller than a loss or two is noise.
- **The balance is not replayed.** Most of the record was traded at $200 to $500, so a $60 or $80 step would have bound much harder then than the table shows, and the lower balance would have set different caps; the table uses $779 throughout.
- **Larger sizes have not been seen.** The record has 9 gold orders at 16 or more contracts and none above 28, and the replay never makes an order larger than it was. The first Dogecoin orders at ladder size are 6. A run at 16 to 20 contracts has no loss history yet. Slippage at larger sizes (GOLDSLIP: +1.82c at 16 to 20 on 6 orders) is not in the replay.
- **Profit factor does not rescale.** Re-scaling by contracts keeps each order's result per contract, so it cannot show any change in fill rate or price at a different size.
- **A bigger order is a bigger loss on the same day.** A day with two losses at 20 contracts is about $28 to $38 (3.6% to 4.9%), against about $14 to $19 at 10 contracts. The record's worst day was a day of small and mid orders.
- **Loss stop.** At the base of $779 the 12% stop is about $94, so four 20-contract full losses in a row (about $56 to $76) would stay inside it and leave roughly $18 to $38 of room before it ends the bot.

I make no recommendation. The owner decides.

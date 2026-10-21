# Kalshi strategy ideas (2026-10-21)

The owner asked for a list of markets, patterns and trade ideas beyond L1, and for three strategies tested fast. This is the list, with where each one stands. The research record is `kalshi-scalper/README.md`; nothing here is a verdict. Status words: **tested** (a registered run exists), **running** (forward days are accumulating), **next** (worth registering), **parked** (a reason it is not worth it yet).

## New markets (same or similar rule)

| Idea | Market | Status |
|---|---|---|
| L1's rule on AUD/USD, USD/CAD and natural gas 15 minute markets | forex and gas, 15 min | running (PAPER1, read on or after 2026-11-30) |
| Gas price ladder, national | `KXAAAGASD`, daily, about 1,000 markets | tested tonight as GAS1 |
| Gas price ladders by state | 35+ series, `KXAAAGASD` plus a state code | next, only if GAS1 is not falsified (same mechanism, many more independent days) |
| Trump approval ladder | `KXTRUMPAPPROVE`, daily, 441 markets | tested tonight as APP1 |
| Generic ballot ladder | `KXVHGCB`, 232 markets | parked behind APP1 (same mechanism) |
| Commodity daily ladders | Brent, WTI, gold, silver, natural gas, copper | tested tonight as CMD1 |
| Commodity hourly ladders | WTI, gold, silver, platinum, palladium hourly | parked: median volume 0 to 56 contracts |
| Index up or down on the day | `KXINXDUD`, `KXNASDAQDUD` | parked: one market a day, 46 days, 300 are needed |
| Rain markets | `KXRAIN`, daily | parked: weather is crossed off (WX1 -3.3c) |
| More weather cities | 12 more high-temperature series | parked: a reword of WX1 |
| Economic releases (CPI, jobs, claims) | monthly and weekly | parked: few observations, needs a consensus forecast feed |
| Treasury yield 15 minute | 2, 5, 10, 30 year | parked: 1 to 4 contracts a market |
| Sports favourites | game winners | tested (SP1 -4.2c), crossed off |

## Patterns on markets already traded

| Idea | Status |
|---|---|
| Skip Bitcoin and Ethereum entries in a busy minute | running (VOL1, read on or after 2026-11-16) |
| Skip entries where Polymarket disagrees by 5 points | running (PM3, same day) |
| Cash out at 99c | tested (TP1), FALSIFIED in both windows |
| A different entry band (90c to 95c, 92c to 95c) | tested (P1, F9, B1 to B3) |
| Resting limit entries | tested (P2): fills select the losers |
| Second look, early and late slots | tested (the four slot search) |
| Weight size toward gold | next: needs a forward scoreboard first (gold +1.54c, z 2.94 on 68 days; Bitcoin is the weakest) |
| Scalps (cheap side, favourite dip, early drift, taker flow) | tested (C1 to C3, F1 to F3, T1 to T5), all FALSIFIED: cost wins |
| Market making | tested (H5), FALSIFIED |

## Ideas that need data we do not have yet

| Idea | What is missing |
|---|---|
| Use gasoline futures to improve GAS1 (the AAA price follows wholesale by days) | a clean daily gasoline futures feed; only if GAS1 is not falsified |
| Use an implied-volatility estimate for the commodity ladders instead of recent realised vol | an options feed |
| News and release-minute windows | an event calendar with exact times |

# STRUCT1 Part A: hold to settlement versus the 25c exit, per market (information only, Strategy Research V2, 2026-10-29)

Registration: `workers/STRUCT1_REGISTRATION.md` (pushed before scoring). 0 tries: this is a per-market cut of EXIT2 (README, "Result: EXIT2", 2026-10-28: pooled over every 15 minute series, hold PF 1.016 against the 25c line's 0.981, 11% of sold positions would have won) and EXIT1 (README, "Results: EXIT1, REGIME1, GOLD1D", 2026-10-29: hold 0.961 / 0.928 / 0.898 against the 25c line 0.921 / 0.897 / 0.869 at 1 contract, pooled). The owner declined to change the exit; nothing below proposes a change. It only states the numbers.

**Method.** `tstop1.load()` (33,698 entries today; TIMEX1 had 32,499, because `fresh.sqlite` has grown, so the thirds cut a little later and the per-market figures differ slightly from TIMEX1's). 6 minute look, 88c to 97c, fill at the decision ask. 25c exit: the first candle in `r["path"]` (candles ending 5 to 1 minutes before the close; the candle ending at the close is not in it, EXIT2's was) whose bought-side bid is at or below 25c, sold at that bid. Fee rounded up per order on the buy and on the sale. Mean net per contract in cents. Thirds A / B / C by close time (as `tstop1`).

## History, 1 contract

| Market | Third | n | Hold PF | Hold mean | 25c PF | 25c mean | Exits | of which would have won | Losses if held |
|---|---|---|---|---|---|---|---|---|---|
| gold | A | 634 | 1.434 | +1.77c | 1.402 | +1.67c | 17 | 3 | 28 |
| gold | B | 574 | 1.005 | +0.03c | 1.016 | +0.09c | 12 | 1 | 37 |
| gold | C | 518 | 1.296 | +1.37c | 1.339 | +1.52c | 13 | 1 | 26 |
| gold | all | 1,726 | 1.221 | +1.07c | 1.228 | +1.10c | 42 | 5 | 91 |
| Bitcoin | A | 859 | 0.974 | -0.16c | 1.010 | +0.06c | 40 | 2 | 57 |
| Bitcoin | B | 774 | 1.282 | +1.31c | 1.168 | +0.85c | 31 | 7 | 39 |
| Bitcoin | C | 784 | 0.774 | -1.65c | 0.777 | -1.62c | 47 | 4 | 62 |
| Bitcoin | all | 2,417 | 0.971 | -0.17c | 0.961 | -0.23c | 118 | 13 | 158 |
| Ethereum | A | 924 | 1.134 | +0.68c | 1.165 | +0.82c | 36 | 2 | 51 |
| Ethereum | B | 808 | 1.011 | +0.06c | 0.973 | -0.16c | 40 | 6 | 50 |
| Ethereum | C | 737 | 0.770 | -1.71c | 0.753 | -1.85c | 51 | 7 | 59 |
| Ethereum | all | 2,469 | 0.961 | -0.23c | 0.951 | -0.30c | 127 | 15 | 160 |
| Dogecoin | A | 907 | 1.298 | +1.32c | 1.075 | +0.39c | 42 | 13 | 43 |
| Dogecoin | B | 872 | 1.296 | +1.32c | 1.076 | +0.40c | 43 | 12 | 42 |
| Dogecoin | C | 752 | 1.105 | +0.55c | 1.074 | +0.40c | 42 | 6 | 43 |
| Dogecoin | all | 2,531 | 1.233 | +1.09c | 1.075 | +0.40c | 127 | 31 | 128 |
| XRP | A | 985 | 1.238 | +1.10c | 1.195 | +0.93c | 40 | 6 | 49 |
| XRP | B | 888 | 1.183 | +0.90c | 1.055 | +0.30c | 40 | 10 | 47 |
| XRP | C | 798 | 1.005 | +0.03c | 1.101 | +0.53c | 35 | 0 | 50 |
| XRP | all | 2,671 | 1.141 | +0.71c | 1.117 | +0.60c | 115 | 16 | 146 |
| live five | A | 4,309 | 1.185 | +0.91c | 1.144 | +0.73c | 175 | 26 | 228 |
| live five | B | 3,916 | 1.153 | +0.77c | 1.056 | +0.31c | 166 | 36 | 215 |
| live five | C | 3,589 | 0.937 | -0.39c | 0.949 | -0.31c | 188 | 18 | 240 |
| live five | all | 11,814 | 1.087 | +0.47c | 1.050 | +0.27c | 529 | 80 | 683 |

At 10 contracts (fee rounded per order at C = 10) every PF is higher by about 0.08 to 0.12 and the order between hold and 25c is the same in every cell; all-days PF hold / 25c: gold 1.320 / 1.332, Bitcoin 1.050 / 1.044, Ethereum 1.041 / 1.036, Dogecoin 1.338 / 1.174, XRP 1.237 / 1.219, live five 1.178 / 1.143. Fees x1.2 change nothing at C = 1 (the fee rounds to 1c at every price in the band).

**What the numbers say.** Hold is ahead of the 25c exit in 9 of the 15 market-thirds and over all days in four of the five markets. Gold is the exception: there the exit is level or slightly ahead (1.228 against 1.221 all days; ahead in B and C), because only 5 of its 42 exits (12%) would have recovered. The gap is largest in Dogecoin: 31 of its 127 exits (24%) would have settled a win, and the exit costs it about 0.7c a contract (PF 1.233 held, 1.075 with the exit) in every third. For Bitcoin, Ethereum and XRP the two are within about 0.13 PF in every third and swap places between thirds. Pooled over the five markets, 80 of 529 exits (15%) would have won, close to EXIT2's 11% over all series.

## Live: the 50 exits in the last 30 days of the nightly report (2026-09-29 to 2026-10-29 18:16 UTC)

Market result from `data/fresh.sqlite` (all 50 found). Price paid estimated as the bought side's ask on the candle ending at the order's minute; 9 had no candle in `fresh.sqlite` (the two forex probes, one Bitcoin and one Ethereum order), and their hold figure uses 92c, so it is approximate. Realised = the report's `settledPnl` (dollars at the real sizes, after fees). Hold = what the same contracts would have paid at settlement. Rows stay in the scratchpad (`struct1_live_exits.json`).

| Market | Exits | Contracts | Would have won if held | Realised exit P/L | Estimated hold P/L | Hold minus exit |
|---|---|---|---|---|---|---|
| gold | 7 | 60.65 | 1 | -$41.64 | -$45.83 | -$4.19 |
| Bitcoin | 8 | 60 | 1 | -$46.67 | -$48.64 | -$1.97 |
| Ethereum | 9 | 45 | 3 | -$30.29 | -$26.88 | +$3.41 |
| Dogecoin | 6 | 17 | 1 | -$12.23 | -$12.61 | -$0.38 |
| XRP | 9 | 18 | 1 | -$13.90 | -$12.93 | +$0.97 |
| AUD/USD (probe) | 4 | 4 | 0 | -$3.06 | -$3.72 | -$0.66 |
| USD/CAD (probe) | 3 | 3 | 2 | -$2.30 | -$0.79 | +$1.51 |
| natural gas (probe) | 4 | 8 | 0 | -$5.77 | -$7.10 | -$1.33 |
| **all** | **50** | **215.65** | **9** | **-$155.85** | **-$158.49** | **-$2.63** |

**What the numbers say.** Over the last 30 days the 50 live exits lost $155.85; holding the same contracts to settlement would have lost about $158.49, so the exits saved about $2.63 in all. 9 of the 50 (18%) would have settled a win. By market the sign differs: holding would have been worse on gold, Bitcoin, Dogecoin and two of the probes, and better on Ethereum (3 of 9 recovered) and XRP. These are 50 orders, so each market's figure rests on 3 to 9 exits.

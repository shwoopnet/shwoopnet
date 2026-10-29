# PPW1 ideas: levers that raise L1's profit per win (Strategy Research V2, 2026-10-29, research only)

The owner: "we need more profit per win, not just scaling". L1 buys the side priced 88c to 97c at the 6 minute look and holds; a win pays 3c to 12c, a loss costs 88c to 97c. Simply buying a cheaper favourite raises the win but loses more often (B1 to B3, B4, BAND1), so it is not counted as a lever here. Each line: the lever, its status in the ledger (`README.md`, `studies/SCOREBOARD_2026-10-28.md`), one line why.

| # | Lever | Status | Why |
|---|---|---|---|
| 1 | Sub-band per market (buy only 91c to 94c etc.) | tested as BAND1 (FALSIFIED), B1 to B3 | Discovery best bands fell apart in validation and holdout. |
| 2 | Look time per market (10, 8, 6, 4, 3 minutes) | tested as LOOK1 (FALSIFIED), FWD7/FWD8, TS1 | An earlier look pays more per win; chosen looks did not repeat. |
| 3 | A lower band, 84c to 88c | tested as B4 (FALSIFIED) | Bigger wins, more losses, net worse. |
| 4 | Take profit at 99c instead of holding | tested as TP1 (FALSIFIED) | Selling at 99c gives up the last cent on winners and saves nothing on losers. |
| 5 | Take 99c then re-enter at 92c, or reverse at 92c | tested as RT1, RT2 (FALSIFIED) | Re-entries after a drop are the flips. |
| 6 | Exit lines and shapes (25c line, drops, half, time exits) | tested as EXIT1, EXIT2, TIMEX1, X1 to X8, EX10 (FALSIFIED) | Exits cut losses less than they cost on recoveries; holding is best. |
| 7 | Resting bid entry (earn spread, maker fee) | tested as MAKER2, MAKER3 (FALSIFIED), P2 | Fills concentrate on the losers (adverse selection). |
| 8 | Order size chosen for fee rounding | tested as ROUND1 (FALSIFIED), SIZE1, SIZE2 | Rounding saves a fraction of a cent; does not change the edge. |
| 9 | Fee tier / maker fee schedule / volume rebate | tested as information (fee schedule section 2026-10-21) and MAKER2/3; NOT_RUNNABLE otherwise | Kalshi's taker fee is a fixed formula with no volume tier for retail that this data can see; the only cheaper fee is the maker fee, which needs a resting order (lever 7). |
| 10 | Buy only when the opposite side's bid is thin (less adverse flow) | tested in effect, post hoc: order scan 2026-10-25 | For a YES buy the NO bid is the YES ask, so its size is our ask depth; thin ask depth (under 20) was WORSE live (12.5% loss, -5.0c). History candles carry no sizes, so it cannot be scored on history; only the live depth log (`depthAtLimit`) can read it forward. |
| 11 | The CHEAPER of correlated markets in the same window (Bitcoin, Ethereum, XRP, Dogecoin) instead of list order | **new** as a registered test (an in-sample information line in the live diagnosis of 2026-10-22 said "choosing the cheapest price instead keeps +74c a day" against +56c for list priority; disclosed) | Live sends at most one crypto order per window by list order; choosing the cheapest in-band one raises the win per contract without adding trades. Counterparty question: is the cheaper of two near-identical bets mispriced or just riskier? |
| 12 | Gold vs silver in the same window: silver instead of gold when silver is the cheaper favourite | **new** as a substitution (CONF1 TWIN used silver only as a filter, FALSIFIED) | Same mechanism as 11 on the metals pair. |
| 13 | Scale in: a second contract if the side dips 3c to 6c after the entry with 3 minutes or more left | **new** | Pays 3c to 6c more per win on the add; the owner's "and recovers before 3 minutes left" needs the future, so the honest version adds at the dip, before knowing. Prior is negative (fills well below the decision price lost 16% live, FWD3). |
| 14 | The hourly ladder strike that pays more for the same outcome at coincident closes | tested as LOCK2H (dominant cases: 4 of 704 closes, NOT_ENOUGH_DATA), XM1, E4, LADL1 (FALSIFIED) | A strike that wins whenever the 15 minute favourite wins and costs less is a lock, and locks are rare; a strike that pays more but wins less is a cheaper favourite on another book (fair or worse). LOCK2 reads the recorder forward. |
| 15 | Hedge the favourite with the cheap side of another market | tested as HL1, HS1, HS1b, SL1 (FALSIFIED) | Lowers the loss size and the profit; net worse. |
| 16 | Prefer YES over NO | information only (live diagnosis 2026-10-22, XRP no/yes scan) | Not a per-win lever; same prices either side. |
| 17 | Retry a missed fill at 5 minutes | ledger O15, NEW but a volume lever | Adds trades at a later, dearer price; lowers profit per win. |
| 18 | Filters that pick "better" windows (confluence, regime, hours, spread, shape, trees) | tested as CONF1/CONF2, REGIME1, MKTTIME1, HOURS1/2, FEAT1 to FEAT4, TREE1/2, SMOOTH2 | They change which trades, not what a win pays. |
| 19 | Market-wide size up after a loss (S1, start 50 and halve) | tested as S1, SIZE1 | Scaling, which the owner excluded. |

Picked for testing (at most 3, all on existing data): 11 (CHEAP1-C), 12 (CHEAP1-M), 13 (SCALEIN1). Registration: `workers/PPW1_REGISTRATION.md`.

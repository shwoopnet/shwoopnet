# Account guardrails proposal (the owner said "go option 1" in the research session on 2026-10-24)

These are LIVE changes (items 1 and 2), so the build session confirms with the owner before building. Items 3 to 5 are report-only checks run by the research session; no code.

## 1. Weekly stop (code)
If the account's net P/L over a rolling 7 days is at or below -6% of the balance at the start of that 7 day window, every series that has a fixed size (XRP, Dogecoin, natural gas, Bitcoin, Ethereum; FIXED_CONTRACTS) trades 1 contract per order for the next 7 days, then returns to its size by itself. Gold keeps its ladder (its own stop and cap apply). The 12% day stop, the 5.5% window cap and the 25c exit are untouched. Log the trigger time and the lift time on the account record so the live book can be split around it.
Why: the 12% day stop cannot see a slow bleed of a few percent a day. At $500 the trigger is -$30 in 7 days, about half of one stop day. Under the history edge it should be rare (the replay's 5th percentile 30 day result at gold's ceiling of 9 is +$12, its worst 95th percentile drawdown $56); under a stressed 6.6% loss rate it would fire often, which is the point.

## 2. Drawdown de-risking (code)
If the balance (excluding savings) is at or below 90% of its highest value in the last 30 days, gold's size ceiling is halved (rounded down, minimum 2) until the balance makes a new 30 day high; the fixed-size series are also at 1 contract while it lasts. The skim and the weekly size review otherwise unchanged.
Why: it ties size to the account's actual results, so a bad stretch is not traded at full size.

## 3. Per-series health check (research, report-only)
Weekly, from the owner's export: live loss rate against the history's rate by series (gold 5.3%, XRP 5.2%, Dogecoin 5.1%, natural gas 5.4% at 10 minutes, Bitcoin and Ethereum smooth-only to be set from their first 100 fills), the binomial tail, minimum 40 orders. Flag when the tail is under 5%; the owner decides any step-down.

## 4. Concentration (research, report-only)
Weekly share of net P/L and of risked dollars by series; flag if gold exceeds 60% of either over 30 days or any other single series exceeds 40%.

## 5. Live against backtest (research, report-only)
Weekly net per contract by series against the replay's range. Three weeks in a row below the replay's 5th percentile means stop scaling and investigate (slippage `avgFill` against `seenAsk`, fill rate, the 25c exit, the entry timing).

## Not proposed
Raising gold's ceiling, any size change on XRP, Dogecoin or natural gas before the ladder gate (100 live fills, positive net, loss rate at or under 6.0%, slippage within +0.3c, size at or under 1% of two-minute volume) is met.

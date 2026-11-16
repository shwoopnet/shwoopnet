# GAPFILL1: restart gap fill on non-crypto (NC15) 15 minute markets. Registered Nov 16, 2026, BEFORE any read (Testing Desk)

Mechanism (not favourite-late, open interest, lead-lag, jump-fade or previous-window result): after a trading halt of 30 minutes or more (the daily break and the weekend) a 15 minute market restarts with a strike set at the reopening price. Positions and stale quotes built over the halt may pull the price back toward the pre-halt level in the first half hour. Prediction: in the first two windows after a halt, the side toward the pre-halt strike beats its price. Counterparty guess: restart quotes anchored on the new strike at 50c while the pre-halt level is not priced in. One variant, tried 1.

Data: the OIREL-X extract already held, series KXGOLD15M, KXSILVER15M, KXCOPPER15M, KXPLATINUM15M, KXPALLADIUM15M, KXWTI15M, KXNATGAS15M, KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M (strike must be present; a market with a missing strike is skipped and counted). Candles ending after the close dropped first. Aug 6 to Oct 2 closes only.

Rule: per series order markets by close_ts. A halt is a step of 1800 s or more between consecutive closes. The break-first window is the first market after a halt (K1) and the next market with close = K1 close + 900 (K2); K2 counts only if it exists and no halt lies between K1 and K2. The reference strike is the strike of the last market before the halt. Gap = strike(K) - reference. Zero gap or a missing strike: skip. Side: gap > 0 buys NO (price falls back), gap < 0 buys YES. Entry: the candle ending 600 s before the market's close; skip if bid or ask missing, bid <= 0, ask >= 1 or ask <= bid. The side's ask (YES ask, or 1 - YES bid for NO) must be 0.35 to 0.65 inclusive. Hold to settlement, 10 contracts; void: price refunded, entry fee kept.

Haircut and cash: C1 to C11: price = ask + h (cap 0.99), h in {0, 0.01, 0.02}, fee_up_order(price, 10) = ceil(round(0.07 x 10 x p x (1-p) x 100, 9)) / 100 per order, cash = 10 x (win - price) - fee. 2c is primary for NC15. Label "upper bound, not fill-checked".

Pass bar (lighter gate, set knowing the sample is small: roughly 100 halts in the extract): n >= 80 trades; 2c PF >= 1.5 with both halves (floor(n/2) by close time) >= 1.0; 1c PF >= 1.5; day-clustered z >= 2.0 at 2c. Fewer than 80 trades is "insufficient", not a pass. Daily line: "tried 1, passed 0 or 1".

Process: hand case before code; one build; Auditor B sanity check; run once; print sha256 committed before reading; figures by message only; no extract data in the repo.

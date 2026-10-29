# Gold first: a proposal for how the bot sizes each market

Written 2026-10-21 for the owner to review. **Nothing here is built.** Plain words on purpose.

## What the live record says (303 settled trades, 2026-10-07 to 2026-10-21, bot only)

| Market | Trades | Losses | Net as traded | Net if every trade had been 1 contract |
|---|---|---|---|---|
| Gold | 98 | 2 | positive | positive |
| Bitcoin | 127 | 9 | negative | negative |
| Ethereum | 65 | 6 | negative | negative |
| XRP | 8 | 1 | negative | negative |
| Dogecoin | 4 | 1 | negative | negative |
| **All** | 302 | 20 | **slightly negative** | positive |

- Gold's losses never landed in the same window as Bitcoin's. Ethereum's losses mostly did (4 of its 6 came with a Bitcoin loss), so Ethereum adds the same bet twice.
- The earlier 68-day backtest agrees on gold and on nothing else: gold was the only series that cleared the bar on its own (+1.54c a contract, z 2.94).
- **Counterfactual, in the same data (so it flatters itself):** gold as traded and everything else at 1 contract would have made clearly positive instead of slightly negative. The number is not a forecast. Gold's live result (+4.5c a contract) is about three times its backtest, so expect some of it to come back.
- Overall the record is indistinguishable from break-even (+0.6c a contract, give or take 1.2c). Size scales the same coin flip; it does not add edge.

## The proposal: size is earned by a market's own live record

1. **Gold is the only market that keeps the size ladder** (today 4 contracts). It goes **first** in the list, so it gets a window's room before anything else.
2. **Bitcoin, Ethereum, XRP and Dogecoin drop to 1 contract each**, like the three probe markets (AUD/USD, USD/CAD, natural gas). They keep trading, so their record keeps growing, but a bad run on them costs about $0.90, not $4.
3. **Promotion (back to ladder size):** a market at 1 contract moves up only after at least **150 settled trades** at 1 contract, a per-contract result above **+0.5c**, and a positive result in both halves of those trades. I read this weekly and propose the edit; the code is changed by a reviewed edit, never by a stored value (the same rule as the list of markets).
4. **Demotion:** a ladder-sized market drops to 1 contract if its **last 100 settled trades** have a negative per-contract result.
5. **The loss stop (12%), the window limit (5.5%) and the 25c exit stay exactly as they are.**

## What I would build (small)

- A list `CAPPED_SERIES` next to `PROBE_SERIES` in `functions/kalshiLiveLib.js`; a market on it is always 1 contract and never uses reinvested profit (the same line that handles the probes today).
- `L1_SERIES` reordered so gold is first.
- Gates: capped markets are 1 contract while gold gets the ladder size; gold is sent first; no callable or stored value changes either list.
- A weekly per-market table (result per contract, trades, losses, last 100) in the roadmap, so promotion and demotion are read off numbers.

## Options for you

- **A (recommended):** the proposal above.
- **B:** remove Bitcoin, Ethereum, XRP and Dogecoin entirely and trade gold plus the three probes. Simplest and lowest risk, but nothing new to learn about the others.
- **C:** change nothing and read again in two weeks.

## What could go wrong

- **Gold's luck runs out.** Two losses in 98 trades (2%) against a backtest of about 4.5% means some regression is likely. Gold is still the best-supported market, but the record shows it is not safe: one gold loss at 4 contracts costs about $3.70.
- **Concentration.** Most of the size ends up in one market. The window limit and 12% stop already bound a bad window.
- **Bitcoin might simply be negative.** At 1 contract it costs little to find out, which is why it is demoted, not removed.
- **Selection.** I picked gold after looking at this record. The reason it is not just fitting noise is that the backtest, done on different days, picked it first.

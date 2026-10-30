# MECH1 registration: who is on the other side of the Bitcoin open interest core (research only)

Written 2026-10-30 by worker MECH1 and pushed BEFORE any tape is joined to an outcome. Before this commit I read `workers/RULES.md`, `workers/FALS4_RESULT.md`, `workers/SLOTEX_RESULT.md`, `src/scalper/fals4.py`, the TAPE20 / SWEEP1 headers in `README.md`, and the fetch code of `sweep1.py`, `maker4.py`, `goldfill.py`. The tape download (`python -m scalper.mech1 fetch`) had started when this was written; it stores trades only, and `describe` reads no `result` column. No outcome has been joined to any tape figure.

This is a mechanism study, not a new strategy. It does not change the core rule, the forward rows `REF_GEN6_OICORE` / `REF_GEN6_OIDRIFT`, or anything that trades.

## The core (unchanged, from GEN6 / FALS4)

`KXBTC15M`. Signal candle ends 180 s before the close. Cheap side = the side whose ask at the signal candle is in [0.05, 0.50] (YES first). Condition: `oi(-180) - oi(-360) > 86,299.56`. Fill at the -120 candle's ask, held. History: discovery (Aug 6 to Sep 20) n 222, PF 2.28; validation (Sep 21 to Oct 27) n 333, PF 1.85. Nothing closing on or after 2026-10-28 00:00 UTC is loaded.

## Hypothesis under test (the counterparty)

Late favourite buyers OPENING new contracts: they take the favourite's ask, so the resting buyers of the cheap side are filled as their counterparties (a YES buy and a NO buy matched create a contract). Their demand pushes the favourite above fair, which leaves the cheap side underpriced at -180.

## Data

Kalshi public trade tape (`/historical/trades`, then `/markets/trades` if empty), no key, for the interval (close - 360, close - 180], exactly the trades behind the open interest jump. Windows: all 555 firing windows (222 / 333), plus 555 matched CONTROLS: one per firing window, same stage, same 5c bucket of the cheap side's ask at -180, open interest jump NOT above the threshold, drawn with seed 30102601 from candles only. MAKER4's cached October tape is reused where it covers the interval. A window whose tape comes back empty is reported, never dropped silently.

Taker side = `taker_outcome_side`. "Favourite" = the side opposite the cheap side at the signal candle.

## Descriptive measures (no outcome; cost 0 tries)

Per window: favourite taker share = contracts bought by takers on the favourite side / all contracts traded in the interval; trade count, total volume, median print size, share of volume in the 10 largest prints, share in prints of 1,000 contracts or more; open ratio = doi / volume (the part of the traded volume that created contracts); favourite mid change from -360 to -180 (candles); favourite takers' VWAP minus the favourite mid at -180. Tables: firing vs control, per stage, and by cheap-ask bucket; corr(doi, favourite net taker flow) and corr(doi, volume) in firing windows.

## Predictions (numeric, fixed now)

- **P1 (the hypothesis' core claim).** In firing windows the median favourite taker share is at least **5 points above** the matched controls, in both stages. My prior: 55%. (If late favourite openers are the flow, the jump in contracts should be mostly favourite takers.)
- **P2 (who prints).** Not a few whales: in firing windows the median share of volume in the 10 largest prints is **below 30%**, and the median print size is within a factor of 2 of the controls'. Prior 65%.
- **P3 (price).** The favourite's mid rose over -360 to -180 in **at least 65%** of firing windows, and the mean rise in firing windows is **not larger** than in controls (FALS4: the cheap side fell 9 to 12 points in core windows against 14 to 15 in all windows). Prior 60%. Note now: if P3's second half holds, "pushed above fair" is not a price push larger than usual; the story would then have to be about who is paying, not how far price moved.
- **P4 (opening).** Median open ratio in firing windows is **at least 2 times** the controls' (by construction the jump is large; the question is whether it comes with ordinary volume or with unusually one-way opening). Prior 80% (close to mechanical).
- **P5 (the ONE scored look).** Split firing windows at their own stage's median favourite taker share; core trade (cheap side, -120 ask, C = 10, held, fee 7% x C x p x (1-p) rounded up per order; fees x1.2 also shown) for each half. If the hypothesis is the mechanism, the HIGH half's PF exceeds the LOW half's in **both** stages, by at least 0.5. My prior that this happens: **35%**.

## What counts as "the hypothesis held"

HELD: P1 holds in both stages AND P5 holds (HIGH above LOW by at least 0.5 in both stages). PARTLY: exactly one of the two. NOT HELD: neither. A HELD result names the counterparty in numbers; it is not a strategy finding and earns nothing beyond a sentence in the counterparty line of the forward row. Verdict words for the split itself: the HIGH half is not a new rule; nothing here is promoted.

## Tries (N)

The descriptive tables cost 0. The scored look is 1 split with 2 halves, counted as **2** (each half's PF is a reported strategy figure). Fees x1.2 shown alongside, not counted separately. `score` refuses to run twice. Running count about 592,030 + 2 = **about 592,032**.

## Kill / honesty

If more than 10% of firing windows return empty tape, P1 and P5 are reported as NOT_ENOUGH_DATA rather than read. The tape counts trades, not openings: a favourite taker can be closing a NO position; the open ratio is the only opening measure available and is per window, not per trade. This limit is stated in the result whatever it shows.

# Week 1 shadow registrations (Nov 9, 2026), for functions/kalshiShadowLib.js validateShadowRule

Registered BEFORE any forward shadow row exists. Basis: cash, PF per contract (equal weight), wins and losses recomputed from avgFill and avgFee, exits corrected. N tried for deflation about 670 (121 cells in W-HUNT1) on top of about 540 earlier; Bonferroni z about 5.2 is unreachable at these n, so every candidate is a SHADOW candidate, never a pass. Shadow rows assume a fill at the touch (an upper bound): read wouldFill. Set registeredAt to the merge date.

Common pass rule (from the lifecycle spec): 150 forward shadow signals, cash PF at least 1.3 per contract, second half at least 1.2, at least 14 days, no single day above 30 percent of net. Common kill: net under -1c per contract after 50 shadow signals, or under 40 signals in 30 days (retire). Counterparty: none named for any of the three. Return path after a pass: incubator ($20 cap, $5 per order), then ladder step 1, owner approves.

```js
{ id: "ETHNO6", series: ["KXETH15M"], entry: { sideRule: "no", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "ETHNO6" },
{ id: "BTCHI6", series: ["KXBTC15M"], entry: { sideRule: "favourite", priceMin: 0.92, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "BTCHI6" },
{ id: "XRPYES10", series: ["KXXRP15M"], entry: { sideRule: "yes", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 640, leftMinSec: 570 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "XRPYES10" },
{ id: "ETHL1", series: ["KXETH15M"], entry: { sideRule: "favourite", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "ETHL1" }
```
(the `readme` value is whatever string the validator expects; if it must be a README anchor, use the anchor of the section below.)

## ETHNO6
Rule: Ethereum 15 minute, buy NO when NO is priced 0.88 to 0.97 at the 6 minute look (330 to 400 s left), hold, 1 contract. History (live orders, cash, per contract): PF 2.59, n 53, halves 2.70 (26) and 2.48 (27); skips 53 percent of Ethereum fills; about 16 signals a week. No candle history to check it. Prediction: cash PF at least 1.3 forward. Prior low to medium: best of 121 cells, selection bias likely.

## BTCHI6
Rule: Bitcoin 15 minute, buy the favourite priced 0.92 to 0.97 at the 6 minute look, hold, 1 contract. History: PF 2.60, n 91, halves no losses (45) and 1.32 (46); candle model 1.14 (n 1101) not contradicting; skips 41 percent; about 25 a week. Prediction: at least 1.3. Prior low: the first half had no losses.

## XRPYES10
Rule: XRP 15 minute, buy YES priced 0.88 to 0.97 at the 10 minute look (570 to 640 s left), hold, 1 contract. History: PF 1.71, n 52, halves 2.43 and 1.36 (26 each); no candles; skips 40 percent; about 13 a week. XRP overall is 0.63. Prior low.

## ETHL1 (re-shadow of L1 on Ethereum)
Rule: Ethereum 15 minute, the L1 rule without the smooth-climb gate (favourite 0.88 to 0.97 at the 6 minute look). The smooth gate cannot be expressed in the shadow entry; apply it offline from public candles when reading. History: Ethereum overall cash PF 1.24 per contract (1.17 dollar-weighted, n 113). Prior low to medium.

## Not expressible today
AUD/USD resume (KXAUDUSD15M): its quotes are not held by the bot (the shadow lib allows only series the bot quotes), so it needs a quote read added first; live history cash PF 1.37 per contract (n 59), first half 1.28, so it is below the shortlist bar anyway.

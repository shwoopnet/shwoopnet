# Week 1 shadow registrations (Nov 9, 2026), for functions/kalshiShadowLib.js validateShadowRule

Registered BEFORE any forward shadow row exists. Basis: cash, PF per contract (equal weight), wins and losses recomputed from avgFill and avgFee, exits corrected. N tried for deflation about 670 (121 cells in W-HUNT1) on top of about 540 earlier; Bonferroni z about 5.2 is unreachable at these n, so every candidate is a SHADOW candidate, never a pass. Shadow rows assume a fill at the touch (an upper bound): read wouldFill. Set registeredAt to the merge date.

[live figure removed, ask Main] Counterparty: none named for any of the three. [live figure removed, ask Main]

```js
{ id: "ETHNO6", series: ["KXETH15M"], entry: { sideRule: "no", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "kalshi-scalper/refine_tools/SHADOW_REGISTRATIONS_WEEK1.md#ETHNO6" },
{ id: "BTCHI6", series: ["KXBTC15M"], entry: { sideRule: "favourite", priceMin: 0.92, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "kalshi-scalper/refine_tools/SHADOW_REGISTRATIONS_WEEK1.md#BTCHI6" },
{ id: "XRPYES10", series: ["KXXRP15M"], entry: { sideRule: "yes", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 640, leftMinSec: 570 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "kalshi-scalper/refine_tools/SHADOW_REGISTRATIONS_WEEK1.md#XRPYES10" },
{ id: "ETHL1", series: ["KXETH15M"], entry: { sideRule: "favourite", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "kalshi-scalper/refine_tools/SHADOW_REGISTRATIONS_WEEK1.md#ETHL1" }
```
(readme anchors point at the sections below; GitHub lowercases them, the validator accepts \w and - in the anchor, so keep ids as written and confirm at merge that the anchor text matches your README convention.)

## ETHNO6
[live figure removed, ask Main] [live figure removed, ask Main] No candle history to check it. [live figure removed, ask Main] Prior low to medium: best of 121 cells, selection bias likely.

## BTCHI6
[live figure removed, ask Main] Prediction: at least 1.3. Prior low: the first half had no losses.

## XRPYES10
[live figure removed, ask Main] Prior low.

## ETHL1 (re-shadow of L1 on Ethereum)
[live figure removed, ask Main] The smooth gate cannot be expressed in the shadow entry; apply it offline from public candles when reading. [live figure removed, ask Main] Prior low to medium.

## Not expressible today
[live figure removed, ask Main]

---
# Batch 2 (Nov 9, 2026), found by re-running the 120-cell on-deck grids on the corrected fee model (retraction 18)

Registered before any forward row exists. Same basis, pass and kill rules as batch 1. These are the best of 120 cells (N about 760): selection bias is likely, so they are SHADOW candidates only. Candle model, unrounded per-contract fee (matches live avgFee), PF per contract, halves by date. The +1c rows are the cautious ones; +0c rows are optimistic (ask with no slip).

```js
{ id: "XRPFAV6", series: ["KXXRP15M"], entry: { sideRule: "favourite", priceMin: 0.88, priceMax: 0.92, leftMaxSec: 400, leftMinSec: 330, maxSpread: 0.02 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "kalshi-scalper/refine_tools/SHADOW_REGISTRATIONS_WEEK1.md#XRPFAV6" },
{ id: "GOLDHI6S", series: ["KXGOLD15M"], entry: { sideRule: "favourite", priceMin: 0.92, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330, maxSpread: 0.02 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "kalshi-scalper/refine_tools/SHADOW_REGISTRATIONS_WEEK1.md#GOLDHI6S" },
{ id: "BTCHI10", series: ["KXBTC15M"], entry: { sideRule: "favourite", priceMin: 0.92, priceMax: 0.97, leftMaxSec: 640, leftMinSec: 570 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "kalshi-scalper/refine_tools/SHADOW_REGISTRATIONS_WEEK1.md#BTCHI10" },
{ id: "XRPFAV10", series: ["KXXRP15M"], entry: { sideRule: "favourite", priceMin: 0.88, priceMax: 0.92, leftMaxSec: 640, leftMinSec: 570 }, contracts: 1, registeredAt: "2026-11-10", forwardReadDate: "2026-12-14", readme: "kalshi-scalper/refine_tools/SHADOW_REGISTRATIONS_WEEK1.md#XRPFAV10" }
```

## XRPFAV6
[live figure removed, ask Main] Prior low.

## GOLDHI6S
[live figure removed, ask Main] Prior low.

## BTCHI10
[live figure removed, ask Main] Prior low.

## XRPFAV10
[live figure removed, ask Main] Prior low.

[live figure removed, ask Main]

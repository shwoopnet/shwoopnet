# OICOREX1 registration: the Bitcoin open interest core on the other 15 minute markets (2026-10-31, written and pushed BEFORE any scoring)

Worker OICOREX1, Strategy Research V2. Owner decision relayed Oct 30 evening: "lets go on the other oicore markets". Research only: no trading code, no deploy, no recorder, no promote verb.

**Plain statement for the owner.** Even a hit here would be a capped probe like OICORE, not a finding, until it clears the bar below (profit factor 1.5 or better in each window after the fee, z at the deflated bar, a named counterparty) and survives its forward days. The Bitcoin core worked on Bitcoin and nowhere else among 5,000 rules on gold, and failed on Ethereum (SLOTEX-ETH) and gold (GEN6, GEN7). The likeliest outcome is that every market below is FALSIFIED.

Before this commit I read: `src/scalper/gen6.py`, `workers/GEN6_FROZEN.md`, `workers/candidates/REF_GEN6_OICORE.json`, the README sections GEN6, FALS4, FALS5, OIDRIFT, OIREL, MECH1 and SLOTEX-ETH, `workers/OIFWD_AUDIT.md`, `workers/SLOTEX_ETH_REGISTRATION.md`. I have read NO settlement result of any non-Bitcoin series for this task. The only data touched: the inventory (`workers/OICOREX1_INVENTORY.md`: counts and spreads), Bitcoin's discovery open interest, and each market's discovery open interest and 5c to 50c side counts (features and quotes, never `result`).

## (a) The rule (exactly REF_GEN6_OICORE, moved to market M)

- Market M `KX<name>15M`. Signal candle = the candle ending 180 s before the close. Cheap side = the side (YES first, then NO) whose ask at the signal candle is 5c to 50c (gen6 `LO_ASK`, `HI_ASK`).
- doi = oi(signal candle) minus oi(candle ending 360 s before the close). Fire when doi **>** M's threshold (strictly greater). A window where either of those two candles or its `oi` is missing does not fire (no trade). This is one deliberate difference from gen6's loader, which turns a NULL `oi` into 0: for these series that would turn a missing value into a fake jump, so the loader here drops those windows (Bitcoin has none, so its numbers are unchanged).
- Fill at the NEXT candle's (ending 120 s before the close) ask of that side; no next candle = no trade. Hold to settlement (`market.result`), no sell fee. Fee 7% x C x p x (1-p) rounded up to the cent per order, `gen6.fee`/`vfee`; C = 10 is the headline, C = 1 and fees x1.2 are reported.
- Code path: rows from `gen6.window_rows` (the same function the forward evaluator uses), the strategy `{L_hi:180, L_lo:180, side:both, conds:[[doi, gt, M's threshold]], e:0 (hold)}` selected by `gen6.trades`, scored by `gen6.score` and `gen6.nets`. Nothing about the fill, fee or selection is re-implemented. `src/scalper/oicorex1.py` only loads windows (with the null-oi rule above) and packs them. Parity check before the read: the Bitcoin row must reproduce discovery 222 trades / PF 2.28 and validation 333 / 1.85; that run uses Bitcoin outcomes only (already read in GEN6) and is not a try.

## (b) Each market's own threshold, fixed from discovery data only

GEN6 took Bitcoin's 86,299.56 as `np.nanpercentile(doi, 90)` over EVERY discovery row of its generator (looks 240, 180, 120 and 60 s, both sides, ask 5c to 50c, windows closing 2026-08-06 to 2026-09-20). I rebuilt Bitcoin's number that way from the raw candles and got 86299.56000000001 exactly, so that is the rule: **per market, the 90th percentile (numpy linear interpolation) of the `doi` feature over all discovery rows of that market built by `gen6.window_rows` (all four looks, both sides, ask 5c to 50c, windows with the two open interest candles), discovery windows closing 2026-08-06 00:00 to 2026-09-21 00:00 UTC.** Computed now, before any outcome is read (committed in `workers/OICOREX1_thresholds.json`; `score` refuses to run if recomputation differs):

| market | threshold (doi >) | discovery windows with oi | discovery rows | discovery windows with a 5c to 50c side at 180 s | validation windows with oi | of those with a side at 180 s | holdout windows (>= 10-28) |
|---|---|---|---|---|---|---|---|
| KXBTC15M (reference) | 86299.56 | 4357 | 8180 | 2431 | 3512 | 1863 | 268 |
| KXDOGE15M | 2993.33 | 4356 | 7750 | 2302 | 3512 | 1720 | 268 |
| KXXRP15M | 4666.15 | 4357 | 7730 | 2313 | 3512 | 1728 | 268 |
| KXNEAR15M | 1139.04 | 4356 | 8829 | 2586 | 3512 | 1775 | 268 |
| KXZEC15M | 1531.01 | 4354 | 8344 | 2457 | 3512 | 1687 | 268 |
| KXBNB15M | 2980.79 | 4352 | 7606 | 2248 | 3512 | 1722 | 268 |
| KXHYPE15M | 3712.44 | 4353 | 7068 | 2142 | 3512 | 1645 | 268 |
| KXSILVER15M | 5344.83 | 3159 | 7225 | 2053 | 2453 | 1483 | 258 |
| KXWTI15M | 7281.53 | 3159 | 7148 | 2022 | 2672 | 1717 | 268 |

The percentile is over rows, so a market's rule fires on roughly a tenth of its candidate windows (about 200 to 250 in discovery), which clears the n floor if the rule behaves.

**Which markets (the try cap is 8).** The two named (Dogecoin, XRP), then the six remaining markets with usable open interest and a full discovery period that have the most discovery windows with a 5c to 50c side at 180 s, an outcome-free rank: NEAR 2586, ZEC 2457, BNB 2248, HYPE 2142, silver 2053, WTI 2022. NOT scored because of the cap: SOL (1727; also no history after Oct 22), natural gas (1169), copper (1124). NOT scored because they have no discovery data or no usable open interest: see the inventory (rates, Brent, AUD, CAD, EUR, GBP, JPY, palladium, platinum), each NOT_ENOUGH_DATA at no try. Gold and Ethereum are NOT reopened: FALSIFIED by GEN6/GEN7 and SLOTEX-ETH; I have no different angle.

## (c) Universe (fixed from information before entry)

Windows by close time only. A window enters the universe if both open interest candles exist and a 5c to 50c side exists at the 180 s candle; the fill candle is needed to trade but is not used to select. Nothing about the result, the fill price or later quotes selects a window.

## (d) Counterparty

Claimed for Bitcoin (GEN6): late takers who overpay for the near-certain side as new contracts open, leaving the cheap side underpriced. MECH1 tested that on the Bitcoin public tape and it **did not hold** (favourite taker share about 52%, controls 50% to 53%, no whales, no single taker type carries the edge); the Bitcoin core's counterparty is still unnamed. For these markets I can name nothing more: **none named for any of the eight.** I cannot read these markets' tape cheaply here and will not invent a story. So even a pass would fail the bar's counterparty line, which keeps any survivor a capped probe.

## (e) Numeric prediction (prior, before scoring)

The core worked on Bitcoin and nowhere else (Ethereum 1.08 / 0.84; gold and thousands of rules). I expect every market FALSIFIED: validation PF between 0.6 and 1.3 per market, discovery PF between 0.8 and 1.5, a pooled average near 1.0. Probability that at least one of the eight is NOT_YET_FALSIFIED: 10%; for any single market 2% to 3%; Dogecoin and XRP no likelier than the rest. Probability any market clears the z bar in validation: under 1%. Co-loss with Bitcoin where both fire: observed both-lost at least 1.2 times independence for the crypto markets.

## (f) Kill criteria and the bar (fixed now, per market, no tuning)

Headline = C = 10 net per order after fees. Stages: discovery and validation (dates in (g)).
- **NOT_ENOUGH_DATA**: discovery n under 100 or validation n under 50 (or no discovery data).
- **FALSIFIED**: n clears the floors and any of: discovery PF under 1.5; validation PF under 1.5; PF at fees x1.2 at or under 1.0 in either stage.
- **NOT_YET_FALSIFIED**: n clears the floors, PF at least 1.5 in BOTH stages at C = 10, PF over 1.0 at fees x1.2 in both. History alone can never earn more than this for a market without a named counterparty.
- The deflated z bar: running N about 728,677 plus one try per scored market (8) = **728,685**, one-sided z bar **5.27** (0.05/N). The day-clustered z (gen6 `cluster_mean_z`) of validation is reported; below 5.27 the market is at best NOT_YET_FALSIFIED and is flagged "below the deflation bar" (Bitcoin's own validation z was 4.53, also below).
- Validation is read ONCE (`score` refuses a second run); no tuning on it. The **holdout** (windows closing 2026-10-28 00:00 UTC to the end of the data on file, about 3 days: a few hundred windows, so it can only confirm or contradict, not decide) is read only for a market that passes discovery and validation.
- Zero-volume signal or fill candles: reported both ways (`pf_nozv`); not a criterion.

## (g) Splits (identical to GEN6, by close time, UTC)

Discovery 2026-08-06 00:00 to 2026-09-21 00:00. Validation 2026-09-21 00:00 to 2026-10-28 00:00 (GEN6's Bitcoin validation end; gold's went to Oct 30 but all markets here use the Bitcoin dates so the co-loss windows line up). Holdout 2026-10-28 00:00 UTC onward, only if both pass. (The owner's "latest 12 days" is not used for the holdout, because those days sit inside validation; a holdout must not overlap the stage it checks.)

## (h) CO-LOSS report (read after this registration is pushed)

Windows close at the same instant, so the markets may lose together. For every window where Bitcoin's core (86,299.56, as scored) AND market M's core both fire, matched on `close_ts`, per stage (discovery, validation), C = 10, base cost: n windows, joint outcomes (both won, both lost, only Bitcoin lost, only M lost), net dollars by market, and the both-lost count against independence (n x Bitcoin loss rate x M loss rate, the rates taken inside those windows). Also the number of windows where at least 2 of the 9 cores (Bitcoin plus the eight) fire and the net on those windows. A report, no verdict. Not a try.

## Tries (N)

One per scored market: **8** (Dogecoin, XRP, NEAR, ZEC, BNB, HYPE, silver, WTI). C = 1, fees x1.2, the nozv split, holdout and co-loss are reports of that try, not new ones. Running count before: about 728,677 (z bar 5.27). After: **728,685**.

## Outputs

`src/scalper/oicorex1.py`, `workers/OICOREX1_RESULT.md` (a table per market, the co-loss table, a proposed README section; README.md is NOT edited). If a market is NOT_YET_FALSIFIED, a forward candidate JSON in `workers/candidates/` (evaluator `scalper.oicorex1:forward_eval`, freeze at the next full hour UTC after the result is pushed); it is a capped probe, not a finding.

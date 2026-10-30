# NEWH15 result (2026-10-30, research only; registration `workers/NEWH15_REGISTRATION.md`, commit 2db0996, before any race outcome)

Owner request: "research new kalshi 15 min prediction market strategies". Code `src/scalper/newh15.py` (scorer), `src/scalper/newh15_fetch.py`
(public batch candlesticks into `data/newh15/candles.sqlite`, never committed). Inventory: `workers/NEWH15_INVENTORY.md`.

## Inventory in one paragraph

38 series are listed with 15 minute markets; 27 have settled windows (Kalshi serves history only from 2026-08-24), 11 have none (ADA, BCH, TON,
S&P 500, Nasdaq 100, Dow, USD/MXN, Coffee, Crypto Comparison, KPOW, a GBPUSD test). 21 series clear 1,500 settled windows and every one
already has L1-shape tests in the ledger (FLAT2, FLAT-R, GEN1 pool, per-series probes) except **KXCRYPTOLEAD15M, the Coin Race**: 6,343 events,
31,715 markets, first settled 2026-08-24, no test anywhere (FLAT-R named it and left it out). It is the only family tested. The other
ideas were not run because they reword a tested rule, fail by arithmetic (tie premium 1.3c at most against a 1.75c fee) or have under 100
possible trades (scheduled releases, rates with 476 windows): table in the inventory.

## The test: three tries, Coin Race given the BTC15M price at 10 minutes left

State read from the liquid `KXBTC15M` book (UP: mid >= 0.70; DOWN: mid <= 0.30); entry at the next candle's ask on a race book (fill 0.15 to
0.85), held to settlement, fee 7% x C x p x (1-p) rounded up at C = 10. Windows: discovery 2026-08-24 to 09-28, validation 09-28 to 10-18,
holdout 10-18 to 10-30 (**not read: no rule passed discovery or validation**).

**Mechanism check (discovery, information only, no try).** The leader's identity does flip with market direction, as the mechanism says:

| State at 10 min left (events) | BTC | ETH | SOL | XRP | HYPE |
|---|---|---|---|---|---|
| UP (777) | 9.3% | 11.8% | 17.6% | 31.0% | 30.2% |
| MID (1,766) | 16.6% | 13.3% | 16.2% | 20.7% | 33.2% |
| DOWN (673) | 27.2% | 12.9% | 13.5% | 14.9% | 31.5% |

BTC leads 9% of up windows and 27% of down windows (fair 20%). The mechanism is real; it is simply priced. The race books at the fill candle have a **median
spread of 8c** (15,519 quotes), and fills come at 0.38 to 0.40 for a 36% win rate.

| Rule | Window | n (days) | PF C=10 | PF C=1 | PF x1.2 | net C=10 | win / mean fill | day z | zero-vol trades, PF without |
|---|---|---|---|---|---|---|---|---|---|
| H1 RACE-UP-HYPE (YES HYPE when UP) | discovery | 473 (35) | 0.80 | 0.78 | 0.79 | -$215.18 | 35.9% / 0.390 | -2.04 | 241, 0.65 (n 232) |
| | validation | 308 (20) | 0.76 | 0.74 | 0.75 | -$173.18 | 35.7% / 0.399 | -2.23 | 180, 0.70 (n 128) |
| H2 RACE-DOWN-BTC (YES BTC when DOWN) | discovery | 464 (35) | 0.83 | 0.81 | 0.82 | -$171.37 | 35.8% / 0.380 | -1.90 | 222, 0.85 (n 242) |
| | validation | 323 (20) | 0.60 | 0.59 | 0.59 | -$335.79 | 30.7% / 0.396 | -4.70 | 204, 0.53 (n 119) |
| H3 RACE-UP-BTCNO (NO BTC when UP) | discovery | 104 (33) | 0.74 | 0.72 | 0.73 | -$58.53 | 67.3% / 0.716 | -1.17 | 50, 0.70 (n 54) |
| | validation | 102 (19) | 0.87 | 0.85 | 0.86 | -$27.84 | 64.7% / 0.660 | -0.74 | 67, 0.71 (n 35) |

Funnels (all events, three windows): H1 968 trades, 573 outside the band, 20 no quote; H2 1,030 trades, 424 outside the band; H3 264 trades, 1,225 outside
the band (the NO side usually costs above 0.85), 72 no quote.

**Verdicts (registered rule: discovery PF under 1.0 with n >= 100 and validation PF under 1.0 with n >= 50):**
**H1 RACE-UP-HYPE FALSIFIED. H2 RACE-DOWN-BTC FALSIFIED. H3 RACE-UP-BTCNO FALSIFIED.** All three lose after fees in both windows; nothing was
close to 1.5. Half of each rule's fills were on zero-volume candles (a quote with no trade), and the PF without them is lower still (0.53 to 0.85). My
registered expectation (PF 0.85 to 1.10, FALSIFIED) was right for H1 discovery and H2 discovery and too kind for the others.

What the table says in plain words: the race books are quoted with the direction already in them. The win rate of the chosen coin is the
mechanism's 30% to 36% and the fill is 0.38 to 0.40: the price for a ticket that wins about 36% of the time is about 39c plus an 8c spread plus 1.7c fee.
The counterparty named in the registration (slow thin-book quoters) did not exist at the minute tested.

## Tries and count

Tries: **3** (H1, H2, H3); looks: **1** (the discovery mechanism table, information only). Running count after NEWH16 about 728,658, new running
count **about 728,662**; Bonferroni z bar 5.27 (unchanged to two places).

## Recorder / data proposals for the owner (nothing built)

1. None needed for the Coin Race as tested (public candles were enough).
2. If the owner wants the Coin Race kept open as a family: the unobserved part is the book depth (median 294 contracts a market; 10 contract fills are
   modelled, not seen) and the quotes between candle minutes. A recorder of the five race books beside BTC15M in minutes 1 to 10 would test whether a
   resting order on the race books earns the 8c spread (a maker test, like MAKER5 on the ladder). Not recommended before the owner's other recorders
   report, because the taker version lost 20% to 40% of every ticket.
3. The eleven shell series (ADA, BCH, TON, S&P 500, Nasdaq 100, Dow, USD/MXN, Coffee, Crypto Comparison, KPOW, GBPUSD test) should be re-inventoried
   weekly with `python -m scalper.newh15_fetch`-style listing: the day one of them settles 1,500 windows it becomes testable (the index series are the
   most interesting: a closed session makes ties likely, and ties resolve YES).

## Proposed README section (for the lead to merge; I did not edit README.md)

### NEWH15 (2026-10-30, owner: "research new kalshi 15 min prediction market strategies"): inventory of all 15 minute series; the Coin Race

Kalshi lists 38 series with 15 minute markets; 27 have settled windows since 2026-08-24, 11 are empty shells (ADA, BCH, TON, S&P 500, Nasdaq 100, Dow,
USD/MXN, Coffee, Crypto Comparison, KPOW, a GBPUSD test). Every series with 1,500 or more windows already had L1-shape tests except `KXCRYPTOLEAD15M`
(Coin Race: which of BTC, ETH, SOL, XRP, HYPE has the highest 15 minute return; 6,343 events, 31,715 markets, median 294 contracts a market, 8c
spread). Three tries, entry at 9 minutes left on a race book after reading the BTC15M price at 10 minutes left (UP >= 0.70, DOWN <= 0.30), held
to settlement: YES HYPE when UP (discovery n 473 PF 0.80; validation n 308 PF 0.76), YES BTC when DOWN (n 464 PF 0.83; n 323 PF 0.60), NO BTC when UP (n 104
PF 0.74; n 102 PF 0.87): **all three FALSIFIED**, holdout unread. The mechanism is real (BTC leads 9% of up windows and 27% of down windows, HYPE 30% to 33%)
but priced: fills cost 0.38 to 0.40 for a 36% win rate. Ties resolve YES but the tie premium (WTI 2.7% of windows, at most 1.3c) is below the fee.
Tries +3 (running count about 728,662, z bar 5.27). `workers/NEWH15_INVENTORY.md`, `workers/NEWH15_REGISTRATION.md`, `workers/NEWH15_RESULT.md`.

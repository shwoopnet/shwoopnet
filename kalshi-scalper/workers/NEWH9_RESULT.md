# NEWH9 result (V2 worker NEWH9, 2026-10-30, research only)

Registration `workers/NEWH9_REGISTRATION.md` (commit 1b679e1, pushed before any fill or outcome was read). Code
`src/scalper/newh9.py` (`counts` reads no outcome; `dv` scored once; `holdout` never run). Printout
`studies/newh9_result_2026-10-30.txt` (aggregates only). Nothing was changed after the score. Data: local 1 minute candles only
(KXBTC15M 8,053 windows, KXGOLD15M 5,819, KXBTCD 1,544 hourly events, KXGOLDH 1,026). Fees rounded up per order and per leg (C = 10
and C = 1, x1.2 at C = 10). **Zero volume both ways:** only one trade (LADLOCK gold) touched a zero-volume candle; every other line
is identical with and without.

**No rule passed discovery and validation, so the frozen holdout (2026-10-18 to 2026-10-30) was NOT read for any rule.**

## Verdicts (PF at C = 10)

| Rule | Market | Discovery n / PF10 / PF1 / PF x1.2 / day z | Validation n / PF10 / PF x1.2 / day z | Verdict |
|---|---|---|---|---|
| H1 LADLOCK (YES at K1 + NO at K2 below $1 after fees, adjacent strikes) | KXBTCD | 0 signals in 1,544 events | 0 | NOT_ENOUGH_DATA |
| H1 LADLOCK | KXGOLDH | 0 trades (2 signals in 1,026 events, 1 no fill) | 1 / 0.00 (the next candle cost $1.05 a set) | NOT_ENOUGH_DATA |
| H2 LADLEAN (hourly ladder's lean at the 15 minute open) | KXBTC15M | 440 / 0.89 / 0.88 / 0.87 / -1.28 | 423 / 0.95 / 0.94 / -0.52 | FALSIFIED |
| H3 ASIAGOLD (gold UP at the open, Shanghai session) | KXGOLD15M | 543 / 0.88 / 0.87 / 0.87 / -1.53 | 327 / 0.79 / 0.78 / -1.83 | FALSIFIED |
| H4 NYGOLD (gold DOWN at the open, COMEX session) | KXGOLD15M | 397 / 0.90 / 0.90 / 0.89 / -1.13 | 259 / 0.88 / 0.86 / -1.11 | FALSIFIED |
| H5 BTC10AM (Bitcoin DOWN at the open, 9:30 to 10:15 ET) | KXBTC15M | 74 / 0.54 / 0.54 / 0.54 / -3.19 | 43 / 0.80 / 0.79 / -0.67 | NOT_ENOUGH_DATA (74 discovery trades against 100) |

Funnels: LADLEAN 1,077 gaps (no ladder event or no bracketing strike at the window's first minute), 1,422 flat (ladder p 0.45 to
0.55), 502 outside the 30c to 70c band at the fill. Session rules: ASIAGOLD 1,549 windows by clock, 528 outside 35c to 65c at the
fill; NYGOLD 1,200 and 433; BTC10AM 240 and 107. Net at fees x1.2 is negative in every scored cell.

## What it says

- **H1 LADLOCK:** the ladders keep strict monotonicity at minute resolution. Bitcoin's hourly ladder never offered YES at a lower strike
  plus NO at the next strike for under $1 after fees in 1,544 events; gold's did twice in 1,026, and the one that could be filled was
  gone a minute later (cost $1.05 a set). This confirms the 2026-10-26 snapshot (0 locks in 4,064 pairs) over three months of
  history. Cross-strike arbitrage on these ladders is closed.
- **H2 LADLEAN:** the ladder's lean at the 15 minute open does carry the direction (YES leans settle YES 57%, NO leans 38% to 41%),
  but the 15 minute book has ALREADY moved further than the ladder by the end of its first minute, so the fill costs more than the
  win rate pays. **Information look I1:**

  | Stage, lean | n | ladder p | 15 minute YES mid at the first candle | YES outcome rate |
  |---|---|---|---|---|
  | discovery, YES | 218 | 0.589 | 0.626 | 0.569 |
  | discovery, NO | 222 | 0.408 | 0.371 | 0.410 |
  | validation, YES | 250 | 0.590 | 0.623 | 0.568 |
  | validation, NO | 173 | 0.413 | 0.365 | 0.376 |

  In these windows the outcome rate sits close to the ladder's p, and the 15 minute first-minute mid overshoots it by 3c to 5c in
  both stages. That is a post-hoc observation (the rule was not built to test it); it is NOT a result. Fading the 15 minute open
  toward the ladder would be a new hypothesis, and it would cross a spread and pay a fee at about 37c to 40c; it needs its own
  registration on data no one has scored (the NEWH9 holdout from 2026-10-18 is still unread for it, and forward days).
- **H3, H4 (gold session drift):** no session pattern at the 15 minute open. Gold UP in the Shanghai session won 46% to 49% at an
  average price of 50c; gold DOWN in COMEX hours won 48% to 49%. Both lose the fee plus the spread, as QUIRK1 found pooled.
- **H5 BTC10AM:** 74 discovery trades against the registered 100. The point estimate is the opposite of the "10 AM dump" story
  (Bitcoin DOWN won 38% in discovery, 47% in validation). The mirror (buying UP) was not registered and is not a try; at 74 and 43
  trades a 38% rate is about 2 standard deviations, and the validation half is near 50%, so it is not a lead.

## Count

**N added: 7** (6 tries: LADLOCK btc, LADLOCK gold, LADLEAN btc, ASIAGOLD, NYGOLD, BTC10AM; plus information look I1). Running count
about 627,838 (after GEN8) + 7 = **about 627,845**, plus GEN9's own count when it lands. Deflated one-sided z bar 5.24.

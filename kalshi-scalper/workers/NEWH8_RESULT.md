# NEWH8 result (V2 worker NEWH8, 2026-10-30, research only)

Registration `workers/NEWH8_REGISTRATION.md` (commit 11a23ba, pushed before any fill or outcome was read). Code
`src/scalper/newh8.py` (`describe` reads no outcome; `run` scored once). Printout `studies/newh8_result_2026-10-30.txt`
(aggregates only). Nothing was changed after the score. Data: local 1 minute candles only (Bitcoin 7,869 windows, Ethereum 7,869,
gold 5,645; Aug 6 to Oct 27; nothing closing on or after 2026-10-28 loaded). Every rule buys the cheap side (5c to 50c at 180 s),
fills at the next candle's ask and holds; no rule sells, so the zero-bid rule never applied. Fees rounded up per order (C = 10 and
C = 1, x1.2 at C = 10). **Zero volume both ways:** no signal or fill candle in any rule had volume 0, so both lines are identical.

Cut points from discovery features only: V90 (Bitcoin 3 minute volume) = 610,392; E90 (Ethereum doi) = 8,800.1; OICORE 86,299.56.
REF_GEN6_OICORE reproduced exactly (n 222 PF 2.28; n 333 PF 1.85).

## Verdicts (PF at C = 10; overlap = with REF_GEN6_OICORE's entries)

| Rule | Market | Disc n / PF10 / PF1 / PF x1.2 / day z | Val n / PF10 / PF x1.2 / day z | Overlap (Jaccard; share of OICORE; share of rule), disc / val | Verdict |
|---|---|---|---|---|---|
| R1 BUSYCALM (3 min volume above V90, cheap side has not led in 3 min, fell less than 10c) | Bitcoin | 48 / 2.42 / 2.32 / 2.39 / 1.77 | 148 / 1.71 / 1.69 / 2.49 | 0.07; 0.08; 0.38 / 0.18; 0.22; 0.49 | NOT_ENOUGH_DATA (48 discovery trades against 100) |
| R2 PEEROI-X (Ethereum doi above E90 while Bitcoin's doi did NOT fire) | Bitcoin | 113 / 1.13 / 1.07 / 1.12 / 0.48 | 432 / 0.86 / 0.85 / -0.99 | 0 by construction | FALSIFIED |
| R3 GOLDX (gold's cheap side when Bitcoin's doi fired) | gold | 452 / 1.09 / 1.05 / 1.08 / 0.70 | 659 / 1.08 / 1.06 / 0.65 | 0.20; 0.51; 0.25 / 0.16; 0.40; 0.20 (by close time) | FALSIFIED (not independent: same trigger, 51% of OICORE's discovery windows) |
| R4 SETTLED (cheap side last led 6+ min ago, mid moved under 3c in 3 min) | Bitcoin | 237 / 0.88 / 0.84 / 0.87 / -0.59 | 147 / 0.37 / 0.37 / -3.58 | 0.06; 0.11; 0.10 / 0.10; 0.13; 0.29 | FALSIFIED |
| R4 SETTLED | gold | 233 / 0.69 / 0.65 / 0.68 / -2.02 | 162 / 0.98 / 0.97 / -0.06 | 0.03; 0.05; 0.05 / 0.04; 0.05; 0.11 | FALSIFIED |

**Screen passes: 0.** No candidate file was written, so no parity check was needed. `forward_eval` exists in the module (same rule
code as the history) in case the lead registers R1 forward.

## Part 1: what else is true in the OICORE windows

From `describe` (features at 180 s only, no outcome; Bitcoin firing vs the rest, medians, discovery / validation):
- **Cheaper cheap side:** 12c vs 19c, 14c vs 22c.
- **The cheap side has not led recently:** it led within the last 3 minutes in 12% / 14% of firing windows, against 35% / 38% of the
  rest. There are fewer flips (median 1 vs 2), a smaller 3 minute fall (10c vs 13c) and a smaller intra-minute range.
- **Much more activity:** 3 minute volume 493k vs 369k; open interest level 455k vs 331k.
- **The last print sits near the cheap side's bid** (favourite buyers took last).
- **The same spread (1c).** The hour leans to 13 to 19 UTC.
- **The other markets jump too:** Ethereum's doi is 1.4x to 1.6x higher in the same windows; gold's busy windows coincide with
  Bitcoin's.

Splitting OICORE's own entries (information, counted):
- **I2 (not led in 3 min) holds the edge in validation:** PF 2.10 on 285, against 1.16 on 48 where the cheap side had led.
- **I1 ("calm", moved under 3c) is the WEAKER part:** 1.28 / 1.47 on 27 / 47, against 2.46 / 1.89 on the rest.

So the exception is **not calm**. It is a window where the favourite has held for at least 3 minutes, still firmed a little, and a
large wave of new contracts appears at the same time.

## Is there an independent condition? No, not on this data

- **R4 (the "settled" shape alone)** is the plain longshot: PF 0.37 to 0.98. The calm, settled cheap side is the most overpriced one,
  as UNDER1 and TAIL found.
- **R2:** a new-contract wave on Ethereum without Bitcoin's own adds nothing (0.86 in validation). The edge does not travel through
  the peer's count.
- **R3:** the same trigger does nothing for gold (1.09 / 1.08, z under 1).

The OICORE mechanism, whatever it is, is Bitcoin-specific and lives in Bitcoin's own count. That points away from a cross-market
contract writer as the counterparty (MECH1 also left it unnamed).

## R1 BUSYCALM, the only lead, and why it is not independent in effect

- **Point estimates:** PF 2.42 then 1.71 (z 2.49). Discovery has only 48 trades: the fixed volume cut was set on discovery, and
  volume grew, so validation fires three times as often. That is the same drift caveat as OICORE's.
- **By entries it looks independent:** every overlap measure is under 0.5 (the largest is 0.49, the share of its validation entries
  that fall in OICORE windows).
- **By effect it is not (I3):**
  - outside OICORE windows: discovery 2.21 on 30, **validation 0.91 on 75**;
  - inside OICORE windows: 2.60 on 18, then 3.19 on 73.
- **Disclosure:** it was modelled on the OICORE windows, which were themselves selected on validation, so it was never blind.

Read it as **OICORE seen through volume**, not as a second bet. If a forward row is wanted, the cleaner choice is OICORE's own
drift-threshold version (FALS4's note), not R1.

## Part 2 and part 3

- **Part 2:** selling the overpriced cheap side was not done (it is buying the favourite, closed).
- **Part 3:** no new mechanism with a named counterparty outside the closed list was found. Declined without a try:
  - spot distance from the strike and fair value (IV1, LAG2, H7, L8, L9);
  - the last print's location (MECH1's taker split; also not readable from forward-ledger candles);
  - intra-minute wick, one-sided pull and compression (S29, S32, S33).
  R2 and R3 tested the one new counterparty story (a cross-market writer), and it failed.

## Count

**N added: 8** (R1, R2, R3, R4 Bitcoin, R4 gold, information looks I1, I2, and I3, which was added after the first read and is
disclosed as such). Running count about 592,086 (after NEWH7) plus other workers' additions, plus 8.

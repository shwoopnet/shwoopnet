# NEWH10 result (V2 worker NEWH10, 2026-10-30, research only)

Registration `workers/NEWH10_REGISTRATION.md` (commit 30f37b1, pushed before any fill or outcome was read). Code
`src/scalper/newh10.py` (`counts` reads no quote or outcome; `dv` scored once; `holdout` never run). Printout
`studies/newh10_result_2026-10-30.txt` (aggregates only). Nothing was changed after the score. Data: local 1 minute candles of the
hourly ladders (KXBTCD from `conf2_lad` then `lad2`; KXGOLDH from `newh2_goldh`) and the event calendar
`studies/EVENT_CALENDAR_2026.csv`. Fees rounded up per order (C = 10 and C = 1, x1.2 at C = 10).

**No rule passed discovery and validation, so the frozen holdout (2026-10-18 to 2026-10-30) was NOT read for any rule.**

## Verdicts (PF at C = 10)

| Rule | Counterparty named | Discovery n / PF10 / PF1 / PF x1.2 / day z | Validation n / PF10 / PF x1.2 / day z | Verdict |
|---|---|---|---|---|
| H1 WKNDWIDE (Bitcoin ladder too wide at weekends: buy the 58c to 82c side of the strike whose wing is nearest 30c, 45 min left) | makers with a clock-blind width; weekend wing takers | 147 (8 days) / 1.23 / 1.19 / 1.21 / +1.24 | 109 (7 days) / 1.26 / 1.24 / +1.16 | FALSIFIED (PF under 1.5) |
| H2 USNARROW-BTC (ladder too narrow in US cash hours: buy the wing nearest 30c, 45 min left) | the same makers; wing sellers in busy hours | 126 (19 d) / 0.97 / 0.95 / 0.96 / -0.14 | 133 (20 d) / 1.00 / 0.98 / -0.01 | FALSIFIED |
| H3 ASIAWIDE-GOLD (gold hourly ladder too wide in Asian hours, 14 min left) | gold makers with one width all day | 44 / 0.70 / 0.67 / 0.69 / -1.07 | 23 / 0.55 / 0.54 / -1.44 | NOT_ENOUGH_DATA (44 against 100; both below 1.0) |
| H4 USNARROW-GOLD (gold hourly ladder too narrow in US hours, 14 min left) | as H3 | 37 / 0.65 / 0.64 / 0.64 / -1.35 | 31 / 0.36 / 0.36 / -2.17 | NOT_ENOUGH_DATA (37 against 100; both below 1.0) |

Win rate against price paid: WKNDWIDE 77.6% vs 72.4c (discovery), 77.1% vs 71.4c (validation); USNARROW-BTC 31.0% vs 30.0c, 31.6% vs
30.1c; ASIAWIDE 65.9% vs 72.1c, 60.9% vs 72.4c; USNARROW-GOLD 24.3% vs 31.3c, 12.9% vs 27.3c.

Funnels (all three windows, events by clock): WKNDWIDE 431 events, 88 no wing, 33 outside the band; USNARROW-BTC 329, 14 band;
ASIAWIDE 363, 236 no wing, 45 band; USNARROW-GOLD 317, 209 no wing, 22 band. The gold file holds only strikes within $12 of the 15
minute strike, so most gold events have no strike whose cheap side sits at 20c to 40c 14 minutes before the close.

**Zero volume both ways.** Bitcoin: one trade touched a zero-volume candle; every PF is unchanged without it. Gold: most trades did
(ASIAWIDE 32 of 44 and 9 of 23; USNARROW-GOLD 34 of 37 and 18 of 31). Without them: ASIAWIDE 0.58 / 0.90, USNARROW-GOLD 1.19 (on 3
trades) / 0.46. The gold hourly wings barely trade; nothing changes a verdict.

## Information looks (counted, not rules)

- **I1, WKNDWIDE's rule on weekdays:** 433 trades PF 0.81 (win 67.7% vs 70.6c, day z -2.62) and 424 trades PF 0.92 (70.3% vs
  70.5c). So the weekend arm beat its weekday twin by about 0.4 of PF in both windows, in the direction the width story predicts
  (weekend wings settle in the money about 5 points less often than priced; weekday wings about as often or more). But it sits far
  under 1.5, its day z is about 1.2 on only 7 and 8 weekend days per window (the local ladder files cover about half the weekends),
  and the comparison was not the registered test. Not a lead at this bar; a forward read would need months of weekends.
- **I2, the 8:30 ET macro release hour on the Bitcoin ladder (the brief's macro family):** event closing 13:00 UTC, signal 12:25
  UTC, 5 minutes before the release. Release days: ladder width (probit s) median $264 on 15 events against $247 on 24 other
  weekdays, i.e. about 7% wider. The cheap wing nearest 30c, bought at 12:26 UTC: release days 15 trades, won 53% against 28.5c paid
  (PF 2.56, day z 1.68); other weekdays 22 trades, won 18% against 27.7c (PF 0.55). Point estimates say the makers barely widen
  before a scheduled release and the wings were cheap, but 15 events cannot carry any claim (the bar needs 100 in discovery alone),
  and on history there is no more data: the calendar holds 23 release days in the whole sample. Recorded so that a forward
  registration could be written on it if the owner wants one (about 9 qualifying 8:30 ET release days a month, so 100 trades would
  take close to a year on one ladder).

## What it says

- On the Bitcoin hourly ladder at 45 minutes left, a 30c wing is priced about right on weekdays and in US cash hours (win rate
  within 1 to 3 points of price, PF 0.81 to 1.00); at weekends it settled in the money about 5 points less often than priced, worth
  PF 1.2 to 1.3 to the other side: real-looking, small, and not near the bar.
- The gold hourly ladder's wings near the close are thin and mostly untraded; neither session arm reached 100 trades and both point
  estimates are below 1.0.
- The macro family: on the 15 minute markets EVT1 already holds it (NOT_ENOUGH_DATA); on the ladder the history has 15 release
  events. Declined as a rule; read as I2 only.
- Declined without a try (see the registration): KXGOLDD and KXGOLDW width (about 60 daily and 9 weekly closes in all of history:
  NOT_RUNNABLE at this bar), a model-based implied against realised read of KXBTCD (LAD1), weekend 15 minute windows (S13, REGIME1,
  QUIRK1).

## Count

**N added: 6** (4 tries: WKNDWIDE btc, USNARROW btc, ASIAWIDE gold, USNARROW gold; 2 information looks: I1, I2). Running count about
627,846 (after LADFADE) + 6 = **about 627,852**. Deflated one-sided z bar 5.24.

## Proposed README section (for the lead to merge)

## Result: NEWH10 (does the hourly ladders' width follow the clock? weekends, US hours, Asian hours, macro releases), 2026-10-30

Registered first (`workers/NEWH10_REGISTRATION.md`, commit 30f37b1), result `workers/NEWH10_RESULT.md`, code `src/scalper/newh10.py`,
local ladder candles only; discovery to Sep 21, validation to Oct 18, holdout to Oct 30 NOT read because nothing passed. One rule,
four clocks: the strike whose cheap side sits nearest 30c (20c to 40c, spread at most 3c), filled at the next candle's ask, held.
**WKNDWIDE** (Bitcoin KXBTCD at weekends, 45 minutes left, buy the 58c to 82c side): PF 1.23 / 1.26 on 147 / 109 (day z 1.24 / 1.16,
8 and 7 weekend days), **FALSIFIED** (under 1.5); its weekday twin (information) 0.81 / 0.92, so weekend wings are a little rich but
nowhere near the bar. **USNARROW-BTC** (buy the wing in US cash hours): 0.97 / 1.00, **FALSIFIED**. **ASIAWIDE-GOLD** and
**USNARROW-GOLD** (KXGOLDH, 14 minutes left): 44 and 37 discovery trades, PF 0.70 and 0.65, mostly on zero-volume candles,
**NOT_ENOUGH_DATA**. Macro releases: the 15 minute version is EVT1; on the Bitcoin ladder the 8:30 ET release hour (information I2,
15 events) showed the ladder only about 7% wider before a release and the 30c wing winning 53% (PF 2.56) against 18% on other
weekdays: 15 events cannot carry a claim and history has no more; a forward read would take about a year. KXGOLDD and KXGOLDW width:
NOT_RUNNABLE (about 60 daily and 9 weekly closes in all history). N +6; running count about 627,852 (z bar 5.24).

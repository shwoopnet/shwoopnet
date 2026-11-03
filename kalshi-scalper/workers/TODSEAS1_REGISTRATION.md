# TODSEAS1 registration: time-of-day seasonality on the non-crypto 15 minute series (Strategy Research V2, worker TODSEAS1, research only)

Written 2026-11-03 BEFORE any win, loss, profit factor or result of any slot window was computed. Only the hour-of-day distribution of
market close times (metadata, no result, no quote) was looked at, to check that markets exist around 17:00 ET (they do, thinner in the hour
after the CME halt). Code: `src/scalper/todseas1.py`, tests `tests/test_todseas1.py`. Nothing here means trade. No promote verb. Touches no live
code, `functions/`, L1 or OICORE.

**Plain statement.** The likeliest outcome is FALSIFIED or NOT_ENOUGH_DATA on every slot. The baseline cheap side loses (EVENT1: PF 0.84 to 0.86
for the same rule at hard limit 0.50) and the owner's own sibling reads (EVENT1 FALSIFIED, PUB20 P03/P06/P09/P10) found no clock effect.

## Question and mechanism
Do the cheap sides (ask 5c to 30c) of the 15 minute FX, metals and energy markets win more often than their price implies in windows that
close at a known exchange clock time, compared with the neighbouring windows of the same series on the same day? **Mechanism:** liquidity
thins or volatility jumps at known clock times (a venue halts, reopens, rolls or hands over between Asia and Europe) and the market maker
that quotes the 15 minute book does not adjust the longshot price for the hour. **Counterparty:** the maker selling the cheap side at a price
set for an average hour. Honest prior of a survivor: 3%.

## Duplicate check (done before registering)
`grep -n -i "EVENT1\|PUB20\|NEWH10\|EVENT830\|OICORE_SHAPE_INVENTORY"` and a read of the P03/P06/P09/P10 text and `EVENT1_REGISTRATION.md`.
**Already covered, NOT re-tested:**
- EVENT1 Try A: windows CLOSING at NYSE open 9:30 ET, NYSE close 16:00 ET, London open 08:00 London, Tokyo open 09:00 JST, Hong Kong open
  09:30 HKT, at all 8:30 ET releases, ISM/Conference Board 10:00 ET, FOMC 14:00 ET, EIA 10:30 ET (silver, copper, WTI, EURUSD, GBPUSD, USDJPY,
  HYPE, BNB; limit 0.50): FALSIFIED. EVENT1 Try B (windows OPENING at those events): information only, PF 1.13 / 0.86.
- EVENT830 (forward freeze of EVENT1's 8:30 ET slice).
- PUB20 P03 Friday afternoon (FALSIFIED), P06 benchmark fix windows 16:00 London / 10:00 ET / 12:00 London silver (W3 FALSIFIED, pooled n 97 PF 1.09),
  P09 settlement windows (silver 13:30, copper 13:00, WTI and gas 14:30 ET; NOT_ENOUGH_DATA), P10 REOPEN first hour after a gap of 90 minutes or more
  (the weekend; the daily 60 minute break was expressly NOT a trigger), P07 month end.
- NEWH10 (hourly ladder width by clock; gold/Bitcoin), NEWH2 GREOPEN/GBREAK (gold only, excluded here), S15 London-open breakout (Bitcoin and gold).
**Not covered, tested here:** the CME daily halt and reopen (daily, not the weekend gap), the FX 17:00 ET roll, the Tokyo fixing and Tokyo close,
the pre-London handoff from Asia, the LSE close, the pre-US-open half hour, the US midday lull and the late US afternoon. No slot below
is a window that EVENT1 Try A, P06 or P09 used; 17:00 ET on commodity windows is not in P09.

## Universe (fixed on metadata)
Nine series: KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M, KXSILVER15M, KXCOPPER15M, KXWTI15M, KXNATGAS15M, KXPLATINUM15M, KXPALLADIUM15M (same as PUB20
universe A). KXAUDUSD15M and KXUSDCAD15M have only 2026-10-06 to 10-19 on file (`rep.sqlite`), entirely in the frozen holdout W3, so they are
left out (stated, not silently dropped). Crypto and gold excluded (L1/OICORE). FX candles start 2026-09-23 (W2 and W3 only); platinum and palladium
start 2026-09-18.

## Trade rule (one rule for every slot, same as EVENT1 except the limit)
Window with close `c`. At the 1 minute candle ending 180 s before the close require 0 < bid < ask < 1 and ask - bid <= 0.10. The cheaper side is YES if
its ask is 0.05 to 0.30, else NO if its ask (1 - YES bid) is 0.05 to 0.30, else no trade. **Fill at that side's ask on the candle ending 120 s
before the close with a HARD LIMIT at 0.30** (a fill ask above 0.30 is no trade, never filled higher). Held to settlement, 1 order per series per
window, C = 10, taker at the ask. **Fee 7% x C x p x (1-p) rounded up to the cent per order** (`gen6.fee`); x1.2 reported. Worst single loss
$3.15 at 10 contracts (300c + 15c fee), $1.58 at 5, $0.32 at 1.

## The slots (registered now, clock = the window CLOSE time in the named zone, zone rules incl. summer time; local weekdays as stated)
| id | clock (close) | days | series | story |
|---|---|---|---|---|
| S1 HALT_IN | 17:00 ET | Mon-Thu | silver, copper, WTI, gas, platinum, palladium | window ending as the CME Globex 60 minute daily break begins |
| S2 HALT_OUT | 18:15 ET (window opens at the 18:00 ET reopen) | Mon-Thu | same six | first window after the daily reopen (Sunday excluded: P10) |
| S3 FX_ROLL | 17:00 ET | Mon-Thu | EURUSD, GBPUSD, USDJPY | window ending at the FX New York roll / value-date cutoff |
| S4 TOKYO_FIX | 10:00 JST | Mon-Fri | USDJPY | window ending after the 9:55 JST fixing |
| S5 TOKYO_CLOSE | 15:30 JST | Mon-Fri | all nine | Asia equity cash close, hand to Europe |
| S6 PRE_LONDON | 07:00 London | Mon-Fri | all nine | the hour before London (Asia/Europe handoff, thin books) |
| S7 LSE_CLOSE | 16:30 London | Mon-Fri | all nine | LSE cash close (P06's fix is 16:00, the close is a different print) |
| S8 PRE_US | 09:00 ET | Mon-Fri | all nine | half hour before the US cash open (EVENT1 used 9:30) |
| S9 NY_MIDDAY | 12:00 ET | Mon-Fri | all nine | the US midday liquidity trough |
| S10 US_LATE | 15:00 ET | Mon-Fri | all nine | the last hour of the US cash session (P09 settles 13:00 to 14:30, EVENT1 16:00) |
Event-free filter: a slot window is dropped if EVENT1's calendar (`workers/EVENT1_CALENDAR.csv`, all event types) has an event within
c - 900 <= e <= c (so a release, the NYSE open and a slot never mix); US/UK/Japan holidays are NOT removed, same in every window (disclosed).
**Family test FAM (one more try):** all ten slots pooled (no window can be in two slots; the clocks differ), same rules.

## Control (separates a slot effect from the general cheap-side loss)
Neighbour control: eligible trades (same rule, same limit) of the SAME series on the SAME local date whose close is 30 or 60 minutes before or after
the slot's close (4 windows), excluding any window that is itself in a slot, in an EVENT1 event window (Try A or B) or inside the same
CME halt hour for S1 to S3. A slot trade's control value = the mean net (cents per contract after fee) of those; if a series-day has none, the
mean over all series that day with a neighbour trade for that slot; if none, the trade is dropped from the difference and counted. Diff =
mean(net - control), day-clustered z (`calibration.cluster_mean_z`, combined with the control standard error as in EVENT1). The "same clock slot
on days the slot has no scheduled release" half is empty by construction (every slot is a daily clock and event-days are removed by the filter);
that is stated rather than faked. A baseline row (all event-free, non-slot cheap-side trades of the same series, same weekday class) is reported
once for the general loss.

## Windows
Three date thirds as in EVENT1 and PUB20: W1 2026-08-06 to 09-04, W2 09-05 to 10-04, **W3 10-05 to the end of the data is the FROZEN HOLDOUT, not
loaded by the scoring command** unless a slot passes W1 and W2 and the owner-style rule below says to read it. Halves = W1 and W2 pooled over
series (FX has W2 only; its absence in W1 is reported, not filled).

## Numeric prediction (recorded first)
Per slot: win rate 12% to 16% against an average fill of 13c to 17c, payoff 5 to 7, **PF 0.80 (0.55 to 1.15)**, mean -2c (-5c to +1c), slot
minus control within +-3c. Eligible trades W1+W2 per slot: S1 to S2 and S5 to S10 about 40 to 140 (daily slots over about 43 weekdays and 6 to 9
series), S3 about 10 to 25, S4 about 4 to 12. **Most slots NOT_ENOUGH_DATA (under 150) about 90%**; FAM about 450 to 1,000 trades, PF 0.85.
Chance at least one slot shows PF 1.5 or better in both W1 and W2 by luck alone with this many cells: about 8%; chance any survives W3: 1%.
Longest losing run at a 14% win rate in 100 trades: mean about 14, 95th about 24 (`streaks.py` in the result).

## Kill rules (decided now)
Per slot and FAM, on trades with a settled result:
1. **NOT_ENOUGH_DATA** if pooled W1+W2 trades < 150 (the row is still reported with n, win, fill, PF, diff; nothing is widened).
2. **FALSIFIED** if PF < 1.5 in W1 or in W2 (a window with < 30 trades counts as not reached, so the slot is NOT_ENOUGH_DATA rather than
   passed), OR slot-minus-control is not positive in both halves, OR PF at fees x1.2 is at or under 1.0.
3. Else **W3 is read once** (`score --w3`): PF < 1.5 or diff not positive in W3 = FALSIFIED; else NOT_YET_FALSIFIED. A z below the deflated
   bar (about 5.27, N recorded in the README) is never a pass: at best NOT_YET_FALSIFIED.
4. Any slot with a mechanism and positive mean net after fees in BOTH W1 and W2 AND positive diff in both is flagged with a capped-probe spec
   (1 contract, hard limit 0.30, kill at 40 fills with PF < 1.2 or net < -$5, worst day, date by which 40 fills would exist). Information for the owner,
   never a recommendation.
5. Run once; `data/todseas1_score.json` makes a second run refuse. No slot, clock, series, limit or rule changes after any outcome is seen.

## N (tries)
10 slots + FAM = 11 tries, **+22** (2 per try, as the lead's convention). Per-series, per-class and per-month breakdowns are reports, not tries.

## Expected read date
W1 and W2 on 2026-11-03 (data on file: candles to 2026-11-03 09:15Z for all nine). W3 only if a slot passes. A forward re-score of the same
frozen code would add about 5 to 8 trades per slot per week (mid December for 150 pooled); not needed unless a slot is NOT_YET_FALSIFIED.

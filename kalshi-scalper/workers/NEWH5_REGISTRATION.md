# NEWH5 registration (V2 worker NEWH5, 2026-10-30, research only; written and pushed before any outcome is read)

Four skip filters on live L1's gold entry (KXGOLD15M, the one market with the size ladder). Nothing here touches the live bot.

**Scope note.** The owner's 2026-10-28 instruction ("no further research on the buy-the-favourite-and-hold idea") is in the README.
This is run on the V2 lead's brief, which asks for L1 gold upkeep filters in the same way the 2026-10-29 owner requests via the
main session did (MKTTIME1, HOUSE1 to HOUSE3, BAND2, SIZE3, EXITOI-G). If the lead did not have the owner's go-ahead, read this file
as information only. Gold's 20:00 to 24:00 CT block (MKTTIME1-F) is not touched: no filter here uses the hour.

**Looked at before writing (no outcome, no price at an entry time):** README headings and the L1 filter registrations listed in the
brief, plus TREE1, FEAT1, the entry-quality table (`tib`, `dip`), IDEAS20 and IDEAS20B (Bitcoin), REGIME1, CONF1, CONF2, NEWH1 to
NEWH4, EXITOI-G; the column list and the gold market count of `l1b`, `book`, `fresh`, `five` and the size of
`data/newh2_goldh.sqlite` (1,026 hourly closes). No quote, volume, open interest, result or trade of any gold window was read.

## Common to all four (fixed now)

- **Parent (L1 on gold, as live):** gold 15 minute markets from `l1b`, `book`, `fresh`, `five` (first file wins per close). Signal
  candle = the one ending 360 s before the close; side = YES if its ask is 0.88 to 0.97, else NO if 1 - YES bid is 0.88 to 0.97.
  Fill at the NEXT candle's closing ask for that side (the candle ending 300 s before the close), no fill if missing or above 0.99
  (the `newh3.h3` / EXITOI-G convention). **Headline exit = the live 25c exit at minute closes:** the first candle ending 240, 180,
  120 or 60 s before the close whose side bid is at or under 0.25 sells at that bid (sell fee charged); otherwise held to settlement.
  Hold-to-settlement reported beside it.
- **Windows by close (UTC):** DISCOVERY 2026-08-06 to 2026-09-20; VALIDATION 2026-09-21 to 2026-10-27. Nothing closing on or after
  2026-10-28 is loaded. A survivor gets only a forward-read registration.
- **Sizes and fees:** 7% x C x p x (1 - p) rounded up to the cent per order, at C = 10 and at C = 16 (gold's typical live size, 13 to
  20). Fees x1.2 at both sizes reported. Zero volume both ways: every figure also with fills whose fill candle had volume 0 removed.
- **A filter only removes entries.** Baseline = all gold L1 entries in the window; kept = baseline minus the flagged ones. An entry
  where the filter's input is missing is KEPT (the filter cannot act) and counted.
- **Bar (the brief), all of it in BOTH windows, at BOTH C = 10 and C = 16:** (1) net per opportunity rises: kept total net > baseline
  total net (the same as: the skipped entries' net is negative), also at fees x1.2; (2) the worst day (UTC day sum of net) of the kept
  set is no worse than the baseline's worst day; (3) day-clustered z of (mean net per kept entry minus mean net per skipped entry) at
  least 2.0 (clustered by UTC day, covariance of the two means on shared days included). Reported: trades removed and their net,
  PF of kept, skipped and baseline.
- **Verdicts:** fewer than 20 skipped entries in either window: NOT_ENOUGH_DATA. All of the bar met: NOT_YET_FALSIFIED (forward read
  only; deflated z for N about 592,000 is about 5.2, which none of these can reach on this history). Otherwise FALSIFIED. Missing
  data that stops the rule from running at all: NOT_RUNNABLE.

## F1 GLADF: the hourly gold ladder disagrees with the 15 minute favourite (the brief's ladder idea)

- **Rule:** only at windows closing at the top of an hour with KXGOLDH candles in `data/newh2_goldh.sqlite`. At the signal candle
  (-360 s), ladder P(YES) = linear interpolation in strike of the two YES mids of the nearest strikes K_lo <= K15 < K_hi with both a
  bid and an ask and K_hi - K_lo <= $6 (NEWH2 H4's construction). Ladder probability of the favourite side = P(YES) for a YES entry,
  1 - P(YES) for NO. **Skip if it is at least 0.05 below the favourite's signal-candle price.**
- **Reason / counterparty:** if the deeper ladder says the favourite is less sure than the 15 minute book, the 15 minute sellers may
  know something. **Honest prior against:** NEWH2 found the ladder is the one that is wrong when the two disagree (GLADH lost in both
  windows), and CONF2 found ladder confluence did nothing for Bitcoin.
- **Prediction:** the filter does nothing: skipped entries win at least as often as the kept ones; skipped net is not negative. Expect
  fewer than 20 skipped entries per window (top-of-hour only, ladder from about Aug 23): **NOT_ENOUGH_DATA is the likely verdict**.

## F2 GTHIN: a thin window (few contracts traded before the decision)

- **Rule:** V = sum of candle volume (contracts) over the window's candles ending at or before the signal candle. **Skip if V is
  below the 20th percentile of V over DISCOVERY gold L1 entries** (computed from the feature only, inside the run, before any outcome
  is joined; the same number is used for validation).
- **Reason / counterparty:** in a thin window the 88c to 97c favourite price is set by a few quotes and a few takers, so it carries
  less information and the favourite is more often wrong; the seller who sold it there was not outnumbered. Gold is thinner than
  Bitcoin (IDEAS20 found Bitcoin's minute volume too steady for volume features to grab; THIN and INACTIVE there were relative to the
  window's own earlier minutes or the previous window, never an absolute level, and never on gold).
- **Prediction:** skipped entries lose about 1.5 times as often as kept ones; the filter adds about +0.5c per opportunity per contract.
  Chance of passing the bar about 15%.

## F3 GOIDROP: open interest fell before the decision

- **Rule:** skip if open interest at the signal candle is at most 0.95 times the open interest at the candle ending 540 s before the
  close (both present and the earlier one above 0).
- **Reason / counterparty:** positions being closed in the three minutes before the look; on L1 entries a later fall in open interest
  marked failing favourites (EXITOI on Bitcoin, triggered entries lost 62%; EXITOI-G pooled 35% to 46%). Moved before the entry it is
  a skip, not a late sale, so it cannot give back recoveries the way the exits did. **Honest prior against:** on Bitcoin, IDEAS20's
  OIFLAT (open interest flat or falling over 3 minutes before an L1 entry, at most 1.10x) was a weak POSITIVE lead (+2.95c, n 128),
  and SMOOTH2's open interest path variables were flat. Not tested on gold before.
- **Prediction:** skipped entries lose at least twice as often as kept ones. Chance of passing the bar about 10%.

## F4 GPRIOR: the previous 15 minutes of gold moved hard against the favourite

- **Rule:** M = this window's strike minus the strike of the gold window closing 900 s earlier (both 15 minute strikes are Pyth gold
  at their opens, so M is gold's move over the previous 15 minutes, known at this window's open). Signed toward the favourite: s = M
  for a YES entry, -M for NO. **Skip if s < 0 and |M| is at or above the 80th percentile of |M| over DISCOVERY gold L1 entries**
  (feature only, computed in the run before any outcome is joined).
- **Reason / counterparty:** a favourite that is leading against a large prior move is leaning on a short reversal; if gold's
  15 minute moves carry on, the window's quoters, who price from the distance to the strike and gold's volatility, overprice it.
  **Honest prior against:** on Bitcoin, PRIORMOVE (FALSIFIED) and TREND4_OPP (NOT_ENOUGH_DATA) found nothing that held; REGIME1's
  recent volatility stand-down did not lift PF. Direction against the favourite on gold is new.
- **Prediction:** skipped entries lose about 1.5 times as often; chance of passing about 10%.

## Declined (not tried, not counted)

- **How close the favourite came to flipping earlier in the window:** that is `dip` (the lowest earlier mid of the held side), in
  TREE1, FEAT1, the 2026-10-22 entry-quality table and the forward claim DIP1. Reworded tested idea.
- **Was the favourite the favourite at the window's open, or did it flip into it:** the side of the first mid is `dip` < 0.5 at the
  first candle, and the climb from the open is SMOOTH20 / SMOOTH2 (CLEANSTART_SMOOTH, GAPOPEN on Bitcoin) and `tib`. Reworded.
- **Size tilts and entry-timing changes:** SIZE3 (price), BAND2, EL1 / HUNT2 (entry times) cover them; nothing new here.

## Count

**N added: 4** (F1 to F4, one rule each, no variants). Running count about 592,070 (after NEWH4) plus other workers' additions, plus 4.

Code: `src/scalper/newh5.py` (`run`, both windows once). Result: `workers/NEWH5_RESULT.md`.

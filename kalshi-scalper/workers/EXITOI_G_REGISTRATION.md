# EXITOI-G registration (V2 worker EXITOI-G, 2026-10-30, research only; written and pushed before any outcome is read)

NEWH3's H3 EXITOI (`workers/NEWH3_REGISTRATION.md`, result `workers/NEWH3_RESULT.md`) on Bitcoin beat holding in both windows
but had 26 and 29 triggers (NOT_ENOUGH_DATA). This runs the SAME pre-fixed rule, no tuning, on L1's other live markets: gold
(KXGOLD15M, the one ladder market), Dogecoin (KXDOGE15M) and Ethereum (KXETH15M), each judged on its own, plus one pooled line
across gold, Dogecoin, Ethereum and Bitcoin. Nothing here touches L1's code or anything live.

**Looked at before writing (no outcome, no quote, no open interest of any window below):** NEWH3's registration, result and code;
the ledger lines of TIMEX1 and DCAP1 in the README; per series and per file, the COUNT of settled markets by month and the count of
candles with a null open interest (zero in every file). Ledger check: no exit triggered by open interest exists in the README,
studies or workers apart from NEWH3's H3, so this is the brief's own extension of an untested-elsewhere rule, not a reword.

## Rule (copied from NEWH3 H3, unchanged; code path `newh3.h3`)

- **Entries (L1's own, as NEWH3 scored them):** at the candle ending 360 s before the close, the side whose price to buy (YES ask,
  or 1 - YES bid) is in [0.88, 0.97] (YES first); filled at the closing ask of the next candle (ending 300 s), fill <= 0.99, else
  no entry (counted as a gap). One entry per market. Held to settlement unless the rule sells.
- **Exit:** if open interest at the candle ending 180 s before the close is at most 0.95 x open interest at the candle ending 360 s,
  sell at the closing bid of the candle ending 120 s for the side held (YES bid, or 1 - YES ask), fee on the sale. **A bid of 0 (or
  no candle) at 120 s means no sale: the entry is held to settlement** and is reported as "triggered, zero bid".
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order, on the buy and on any sell. Headline at C = 10; C = 1 and fees x1.2
  at C = 10 reported. Gold's ladder size: neither NEWH3 nor TIMEX1 registered one, so none is used (no size chosen after the look).
- **Zero volume both ways:** the per-market summary also reported with entries whose fill candle had volume 0 removed.

## Universe and data (chosen on time and file coverage only)

- Settled markets closing >= 2026-08-06 00:00Z and < 2026-10-28 00:00Z. Nothing on or after 2026-10-28 is loaded.
- Files, first file wins per ticker: gold, Ethereum, Bitcoin `l1b`, `book`, `fresh` (NEWH3's set); Dogecoin `e3b`, `alts2`,
  `fresh` (the files that hold Dogecoin with open interest; `l1b` and `book` have none).
- **Windows by close:** DISCOVERY Aug 6 to Sep 20; VALIDATION Sep 21 to Oct 27. These windows have been read by NEWH3 (Bitcoin) and,
  by date thirds, by TIMEX1, EXIT1, EXIT2 and others on the hold leg, so they are not a fresh holdout; the third window is the
  FORWARD record (closes after this commit), read only if the bar is met.
- **Pooled line** includes Bitcoin, whose outcome is already known from NEWH3; it is disclosed as not independent of that read.

## Bar (NEWH3's H3 bar, the TIMEX1 "better than hold" form, applied to each of the 4 lines)

On the same entries: rule PF >= hold PF + 0.03 at C = 10 in BOTH windows, with >= 50 triggered entries in EACH window, and a
day-clustered z of the per-day sum of (rule minus hold) at C = 10 >= 2.0 over both windows. Fewer than 50 triggered in either
window: NOT_ENOUGH_DATA. Bar met: NOT_YET_FALSIFIED (earns only a forward check proposal). Otherwise FALSIFIED.

**Kill:** any of the three conditions failing with >= 50 triggers per window is FALSIFIED. Positive net difference at fees x1.2 is
also required (reported); if the C = 10 bar is met but the x1.2 difference is <= 0 in either window: FALSIFIED.

## Counterparty / mechanism

Holders who close the favourite in the final minutes regardless of price; if their exit predicts losses (they know something or the
reversal has started), selling with them at 120 s beats holding. NEWH3's reading on Bitcoin: the fall is a symptom of a reversal
already in the price.

## Reported per market and pooled

Entries, triggers, sold, zero-bid share among triggered at 120 s, hold PF vs rule PF (C = 10, C = 1, x1.2), net difference rule
minus hold at C = 10 and at x1.2, loss rate triggered vs untriggered, day z, gaps.

## Prediction

The trigger fires on 1% to 3% of entries on every market. Gold (a calmer, thinner book) triggers least: fewer than 50 per window,
NOT_ENOUGH_DATA. Ethereum and Dogecoin also NOT_ENOUGH_DATA. The pooled line likely reaches 50 triggers per window; there rule minus
hold is positive but under 0.03 PF in at least one window or day z under 2.0: FALSIFIED. Triggered loss rate >= 40% on every market
against about 5% untriggered.

## Count

N tried: **4** (gold, Dogecoin, Ethereum, pooled). Running count about 592,061 before (NEWH3), about 592,065 after (plus other
workers' additions).

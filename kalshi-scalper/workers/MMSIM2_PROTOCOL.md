# MMSIM2 (registered Nov 11, 2026, before any variant is scored): pre-registered variants of MMSIM1, simulation only
Research only, no live change, no network call except git on this repo. Base = MMSIM1 (`workers/MMSIM1_PROTOCOL.md`, `src/scalper/mmsim1.py`): same data (`quote-data` branch, `book/` hourly KXBTCD books and trade tape), same queue model (join the back of the visible queue, fill when cumulative taker contracts at the price reach queue ahead + 1, cancels ignored), same fees (maker bound 0 and 0.0175 x p(1-p); taker exit 0.07 p(1-p)), same development events, cash basis, one contract per side, one quote per side per strike, a pair is held to settlement and pays 1, a single is sold at the best bid at the flatten time.
DEVELOPMENT ONLY. Development = the 171 events (168 quotable) closing before the Nov 8 cutoff, defined as the first 171 events by close time. NO event closing at or after the cutoff is read into a score; the script drops them before simulating. The held-out set stays for the parent to read once on or after 2026-11-17.
Data check: `book15` (3 files) and `book15r6` (288 files) hold 15 minute BTC books that start about 11 minutes before the close, so MMSIM1's T-50 post and T-15 flatten cannot be applied; they are NOT used here.

## Variants (each counted; every variant changes ONE thing from base)
- V1 post one tick (1c) inside the best bid on each side instead of at the touch, only when the book spread is at least 3c (yes_bid + no_bid <= 0.97), otherwise at the touch. Queue ahead = 0. Price priority: a YES bid at p' is filled by taker-no trades at yes price <= p', a NO bid at q' by taker-yes trades at yes price >= 1 - q'.
- V2 inventory skew, event level (a one-shot per-strike quote already stops a side after its fill, so the literal rule is vacuous): within an event, once one YES (or NO) leg has filled on any strike, every other YES (or NO) fill in that event after it is voided (the quote is cancelled when inventory on that side reaches one contract). Ties by strike order.
- V3 only quote strikes whose mid ((yes_bid + (1 - no_bid)) / 2) at post time is between 0.20 and 0.80.
- V4a flatten (and stop quoting) at T-20 minutes. V4b flatten at T-10 minutes.
- V5 quote only the 4 strikes nearest the money (smallest |mid - 0.5| at post time).
- V6 post at T-35 minutes instead of T-50 (flatten stays T-15).
- V7 cancel a side's resting order at the first book poll where that side's best bid has fallen 2c or more below our price (the market moving against the quote); a fill before that poll stands.
- V8 per-strike cap on fills, 14-day style: per UTC day, per strike rank (nearness to the money, 1 to 7, at post time) and side, at most 3 fills count; later fills that day on that rank and side are voided. (Interpretive: tickers rotate hourly, so rank stands in for the strike.)
N added = 9 variants (V4 has two) x 2 fee bounds = 18, on top of MMSIM1's 1 (ledger about 5,190 + 1 + 18).
Bar (per variant, at the 0.0175 bound): cash PF >= 1.5 on per-event P&L over >= 300 events AND a positive mean per event in each third of development. Honest note: development has only 168 events, so the n >= 300 rule cannot be met by ANY variant here; each variant is at best NOT_ENOUGH_DATA, and a PF >= 1.5 with positive thirds is "worth the held-out read", never a pass. No variant beats MMSIM1 unless PF exceeds 1.28 at the bound; with 9 variants tried, the best of them is biased upward, so no variant is selected on development alone for a live version.
Prediction: none beats base by more than noise (per-event sd about 42c on a mean of +3.7c; 168 events cannot separate variants).
Output: cash PF, n events, fills per day, mean per event, day-clustered z, positives by third; daily cash P&L of the best variant for the correlation-with-gold plan (no live data fetched). Script `src/scalper/mmsim2.py`.

## Result (Nov 11, 2026, development events only; held-out NOT read)
Development = the 171 events closing before 2026-11-07T15:00Z (the MMSIM1 cutoff by its own rule, first 171 events by close time); the script drops all later events before simulating. BASE reproduces MMSIM1 exactly (168 events, PF 1.28 at the bound, 1.41 at 0). Cash, unrounded, one contract per side. Day-clustered z over 10 UTC days.

| variant | n events | PF at 0.0175 | PF at 0 | fills/day | mean per event (c) | day z | thirds mean (c) | positive thirds |
|---|---|---|---|---|---|---|---|---|
| BASE | 168 | 1.28 | 1.41 | 79.1 | +3.71 | 1.60 | +9.6/-6.0/+7.6 | 2/3 |
| V1 | 168 | 1.28 | 1.41 | 79.1 | +3.71 | 1.60 | +9.6/-6.0/+7.6 | 2/3 |
| V2 | 168 | 1.02 | 1.09 | 28.6 | +0.15 | 0.11 | +5.6/-3.1/-2.1 | 1/3 |
| V3 | 167 | 1.07 | 1.15 | 45.0 | +0.86 | 0.36 | +6.3/-7.6/+4.0 | 2/3 |
| V4a | 168 | 1.21 | 1.35 | 75.6 | +2.39 | 0.99 | +9.0/-8.4/+6.6 | 2/3 |
| V4b | 169 | 1.35 | 1.47 | 83.4 | +5.25 | 2.32 | +8.8/-1.8/+8.7 | 2/3 |
| V5 | 168 | 1.26 | 1.37 | 57.2 | +3.28 | 1.54 | +8.4/-5.8/+7.3 | 2/3 |
| V6 | 168 | 1.11 | 1.22 | 71.9 | +1.24 | 0.50 | +4.6/-5.0/+4.2 | 2/3 |
| V7 | 168 | 1.32 | 1.39 | 40.7 | +3.14 | 1.30 | +4.7/+0.2/+4.5 | 3/3 |
| V8 | 168 | 1.21 | 1.30 | 37.0 | +1.68 | 0.87 | +5.0/-4.2/+4.2 | 2/3 |

Daily cash P&L in dollars per day (one contract per side per quoted strike, maker bound 0.0175), UTC close date, for the correlation-with-gold plan:
| date | BASE | V4b | V7 |
|---|---|---|---|
| 2026-10-29 | +2.009 | +2.179 | -0.580 |
| 2026-10-30 | +0.252 | -0.273 | +1.520 |
| 2026-10-31 | +1.352 | +1.988 | +1.408 |
| 2026-11-01 | +0.828 | +0.486 | -1.255 |
| 2026-11-02 | -1.038 | -1.112 | +0.543 |
| 2026-11-03 | -1.879 | +0.426 | -0.610 |
| 2026-11-04 | +0.733 | +0.147 | +2.923 |
| 2026-11-05 | +0.752 | +0.889 | -0.144 |
| 2026-11-06 | +1.748 | +2.839 | +0.006 |
| 2026-11-07 | +1.482 | +1.310 | +1.464 |

Reading:
- No variant reaches PF 1.5 at the bound. Highest: V4b (flatten at T-10) 1.35, mean +5.25c per event, day z 2.32, but its middle third is -1.79c (2 of 3 positive thirds). V7 (cancel when the market moves 2c against the quote) is 1.32 and the only variant positive in all three thirds (but thirds +4.7, +0.18, +4.54, so the middle is flat), at about half the fills per day.
- Only V4b and V7 beat MMSIM1's 1.28 at the bound; V5 (1.26) is level; V1 is IDENTICAL to base: every recorded book had a 1c spread (yes bid + no bid = 0.99) in the quoted window, so a one tick inside quote was never available and the rule fell back to the touch. V2, V3, V6, V8 are worse (PF 1.02, 1.07, 1.11, 1.21), V4a 1.21.
- n is 167 to 169 for all variants, below 300, so EVERY variant is NOT_ENOUGH_DATA under the bar; no variant passes. Differences between variants (gaps of 0.05 to 0.1 PF) are well inside the noise (per-event sd about 42c, 168 events), and 9 variants were tried, so the best one (V4b) is selected upward. The sensible read: nothing here shows a better rule than base; V4b and V7 are worth carrying to the held-out read only because they were registered first, not because development picked them.
- The correlation with gold L1 and OICORE is not computed (the bar is not met, and live data is not fetched); the daily series above is for that plan.
- N added 18 (9 variants x 2 bounds). Script `src/scalper/mmsim2.py`; run with `python3 -I`. The 15 minute books (`book15`, `book15r6`) were inspected and not used (they start about 11 minutes before the close).

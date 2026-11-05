# LADCOH1 result (2026-11-05, 10:00 AM Central, research only): FALSIFIED (book, M2); NOT_ENOUGH_DATA (daily, M1 and B1, 7 snapshots)

Registration `workers/LADCOH1_REGISTRATION.md` (pushed before any count). Code `src/scalper/ladcoh1.py` (quotes only, no outcome column read; no outcome was needed because every set is riskless). Recorder files on `quote-data` as of 2026-11-05 16:03 UTC. N +3, running count about 730,443, bar z about 5.27 (not applicable to an arithmetic lock; no directional claim made).

## Numbers first
| Rule | Data | Looked at | Locks at net of at least +1c a set (C = 10, fees x1.2 too) | Best seen |
|---|---|---|---|---|
| M2 nested pair, KXBTCD book | 39 book files, Oct 29 to Nov 5, 137,216 cycles of 7 strikes | 1,815,601 pair-cycles | **0** (0 persistent, 0 even non-persistent skew crossings) | max (bid of higher strike minus ask of lower strike) = **0.000** |
| M1 nested pair, 52 RECDAILY series | 7 snapshots (Nov 4 01:37 UTC to Nov 5 09:37 UTC), 166 event-snapshots | 18,398 pairs (incl. monthly touch ladders, weekly FX and commodity) | **0** (none even within 1c of break-even after fee) | none |
| B1 bracket partition | 11 partition event-snapshots (EURUSD, USDJPY, WTI weekly, S&P and Nasdaq 100 range) | all | **0** | sum of YES asks 1.47 to 11.39 (never near 1.00); sum of YES bids 0.00 to 0.97 (never above 1.00). No set was fully two sided (tails quote a zero bid). |

M2 is a real sample (a week of 3 second cycles, with the 5 level book; the best crossing in 1.8 million pair-cycles was exactly zero, a touching book, never a crossed one). The matching engine and the quoters keep the ladder monotone, so no depth or size question arises. Time skew between strikes (read up to 1 s apart) could only have created false locks, and it created none, which makes the zero stronger.

## Reading
- The prediction (zero real locks, a handful of artifacts) was right except there were no artifacts at all.
- Bracket sets are heavily over-round on the ask (median several times 100c on illiquid FX and index buckets) and under-round on the bid; this is the thin-maker shape RACELOCK and ARB1 saw, not an opening.
- Daily M1 and B1: 7 snapshots (about 3 hours apart) cannot say how often a stale quote appears at a given moment; it says only that none of 166 event-snapshots had one. Verdict word for the daily data is NOT_ENOUGH_DATA, not FALSIFIED, per the registration.
- Not tested and not claimed: cross-event nesting (a daily and a weekly ladder on the same underlying settle on different references), size beyond level 1 (not needed, no lock), the 15 minute books (excluded by the standing rule).

## Forward plan
Nothing to build. RECDAILY already records M1 and B1 inputs; one more read of the same code on 2026-12-05 (about 1,500 half hour snapshots) costs a minute and is the only follow up. A ladder family with no active maker (new listings) would be where a lock could appear; it would need a new recorder, which is not recommended. The coherence family is closed on the data available.

# Idea Desk B, second wave (Nov 12, 2026): ideas testable on data we hold or will hold within 7 days, with no Kalshi read

**Result: no new card.** Asked for a second wave restricted to held data, this desk looked at every recorder branch from the events and information angle and found nothing that is both new and able to reach a verdict. Padding the list would break the charter, so this file records what was examined and why each candidate was dropped. No Kalshi read was made.

## What the recorders hold that this angle could use (checked Nov 12)

| Branch and folder | What is there | Use for this angle |
|---|---|---|
| `pol-data` `polrec/` | ONE snapshot (Nov 11, 19:32Z): 14 politics series, 210 quote rows; nothing since (see `IDEA_DESK_B_POWER.md` section 5) | too little for any test; not accruing |
| `quote-data` `wxens/` | NWS forecast highs at three looks, observed highs, bracket quotes and results, 14 cities since Nov 4; about 6 usable day-ahead city-days a day | weather singles are a family that has failed three times; combos cannot be priced |
| `quote-data` `daily/`, `raincal/`, `ref/`, `deribit/`, `oklq/` | V2's and Refinement's registered forward tests | owned and registered elsewhere |
| `nc-data` `nc15/` | 11 non-crypto 15 minute books every 5 seconds, from Nov 11 | the largest fresh sample (about 1,000 windows a day), but see below |
| `sports-data` `ingame/` | 20 second in-game quotes | Desk A's angle; needs game-clock data from barred hosts for anything event-based |

## Candidates examined and dropped

1. **Scheduled fixing and settlement times on the 15 minute currency and commodity markets** (the 4 PM London fix, the Tokyo fix, the ECB reference rate, the daily futures settlement windows, the 4 PM Eastern fund pricing time for Bitcoin): a known price-insensitive flow at a known minute, with a reversal afterwards. It fits the new non-crypto books well. **Already tested, so a duplicate:** V2's PUB20 (P06 fix windows: 16:00 London, 10:00 Eastern, silver 12:00 London; P09 settlement windows; P07 month end; P10 weekend reopen), FXUSD (the window closing at the 4 PM London fix), TODSEAS1 (Tokyo fix, daily halt and reopen, FX roll) and EVENT1 Try A (exchange opens and closes, 8:30 releases). Not carded.
2. **Three ladders on one weekly count (Strait of Hormuz: weekly total, peak day, which day is the peak):** one daily distribution must explain all three, so two ladders price the third. Real and unusual, but it exists for ONE series: one independent event a week. By the power table it could not reach a verdict in a decade. Not carded. Its lock version (IMPLY1) was checked on the held snapshot and is 25c from a lock (`IDEA_DESK_B_POWER.md` section 3).
3. **Forecast revision between two looks, before the bracket reprices:** this is Refinement's row 75 (WXREVISE), listed there as needing a forward logger. Not this desk's card, but a pointer: the held `wxens/nws` files already carry a day-ahead look at 10:00 and a same-day look at 07:00 for the same target day, so row 75's first count can be made on held data without a new logger.
4. **Release-window behaviour in the new 5 second non-crypto books** (who is left resting at the print): a pick-off inside the first seconds. The bot decides once a minute, so it could not act on it; rows 2, 13, 39, 63 and 67 already scored the minute-level versions (failed or too thin). Not carded.
5. **Scheduled macro days on the daily index and commodity ladders** (tails underpriced on print days): the same logic as EVENT830 on another market, so a version, and V2's STRESSDAY1 already sits on that recorder. Not carded.
6. **Daily approval markets at 30 minute resolution** (when the quote converges after the source publishes): this is ROLLOFF's forward log and row 72's "determined fact" check, both already carded; and the data is not accruing.

## What would make a new events card possible (stated instead of "menu empty")

- **A politics recorder that actually accrues** (the existing one, fixed): without it nothing daily in politics can be tested forward. No new recorder is proposed.
- **A source of real combo asks** (a recorder of the live combo book, or quote requests from the owner's account): all four combo cards are closed for lack of a price. That is an owner decision and is not proposed here.
- **Markets that settle daily on an official number**: the power table says only daily-or-faster markets can reach the bar. Today that means the approval, weather, daily rate and daily commodity series, which are all already under test by someone.

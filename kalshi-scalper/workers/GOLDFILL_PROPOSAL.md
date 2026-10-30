# GOLDFILL proposal: two registered tests built on the gold fill model (V2 worker GOLDFILL, 2026-10-30, research only)

This file is the registration of both cards. It is written and pushed BEFORE any outcome of any window either card will be scored on has been read, and before any scorer for either card exists. The model these cards use (`workers/GOLDFILL_MODEL.md`, `src/scalper/goldfill.py`) reads quotes and trades only: no `result`, no `results.csv.gz`, no settlement price. Both cards are scored ONLY on recorder R6 (`book15r6/` on `quote-data`), whose first window closed 2026-10-29 22:15 UTC, after every history window the model used (last close 2026-10-29 20:45 UTC). So the model's history and the cards' scoring data do not overlap.

**Disclosure.** GF2's idea came from a model table: on history, the market-implied value at T-120 s (the bought side's bid at T-120 s minus the price paid; a price, not a settlement) of signals a 1c-inside bid did NOT fill was about +5.8c, against +1.2c for all signals. That is a price-path observation made before writing this card; it is why GF2 exists. It is not an outcome of any R6 window.

**Ledger check.**
- MAKER2 (rest at the bid, 3 minutes, no fallback): FALSIFIED, the fills are the dips. MAKER3 (rest at the bid, cross at the later ask after W = 60 or 120 s, no chase cap): FALSIFIED, -0.56c and -0.78c per opportunity. Both on minute candles with no tape and no queue.
- L1Q1 (R6T): rest at the BID until T-120 s, variant a skip, variant b cross at T-120 s. MAKER5: two-sided quotes 12 to 7 minutes before the close.
- GF1 differs from all of these in three fixed ways: the price is 1c under the ask (on gold that is usually UNDER the best bid, since the spread at the decision is 0.1c to 0.3c; the model shows it fills 59% of the time within 30 s anyway, by the price ticking through it), the wait is 30 s (the model's knee), and the chase is capped at 1c above the signal ask. It is still MAKER3's shape, and the prediction below says so.
- GF2 is not an execution card. It is a 30 second post-signal hold filter: the nearest tested ideas are FLAT1 and FLAT-R (a firm favourite in the 5 minutes BEFORE the entry), the SMOOTH family (the path before the decision) and EL1 (entry at 10 minutes instead of 6). None looks at the 30 s after the signal. It is GF1's chase leg on its own, so the two cards decompose one rule.

## Shared rules (both cards)

**Data, clock, queue, crossing, fees, unit, statistics, usable windows:** exactly R6T's shared rules and L1Q1's usable-window rule (`workers/R6T_REGISTRATION.md`, "Shared rules" and "Kill criteria"), not restated here and not changed. In short: five series (`KXGOLD15M, KXBTC15M, KXETH15M, KXDOGE15M, KXXRP15M`, chosen by what R6 records); an order is live 1.0 s after its posting poll (clock from the Date header); a resting order joins behind all displayed size at its price, only trades move it forward, it fills by taker volume at its price past the queue or wholly by a print or a recorded quote at or through its price, at OUR price; a crossing walks the 5 recorded levels; fees 7% x C x p x (1-p) rounded up per order, maker fills at the taker rate for the verdict (information: 1.75% and zero), stress x1.2; C = 1 and C = 10, the verdict needs both; one window of one market is the unit, z clustered by US Central date; windows by close-time thirds, the last third the holdout read once; windows with no trade reported both ways.

**Signal (both cards):** L1Q1's. Signal poll S = the last poll at or before T-360 s, within 10 s of it; the bought side is the side whose ask at S is 0.88 to 0.97 (YES ask = 1 - best NO bid; NO ask = 1 - best YES bid); neither or both: no signal. The live bot's portfolio rules (one crypto order per window, window cap, smooth gate, XRP pause) are not applied, as in L1Q1. **Gold is reported on its own beside the pooled verdict** (the model was built for gold; gold alone will have about 250 to 300 signals by the recorder's end, so the pooled five-series set is what reaches the sample).

**Plain L1 (the comparison, not a try):** cross for C at the first poll at or after S + 1.0 s, walking the ask side, taker fee, held to settlement (L1Q1's).

**Read date and sample.** The scorer refuses before **2026-11-14 00:00 UTC** (R6 records no window opening at or after 2026-11-13 23:59 UTC), refuses a second run, and the verdict is `NOT_ENOUGH_DATA` if fewer than **300 scored windows had an order** (GF1: an order posted; GF2: an entry made).

**Bar (RULES.md, not loosened).** `NOT_YET_FALSIFIED` only if, at the verdict fee and at BOTH C = 1 and C = 10: PF at least 1.5 in each of the three date windows and pooled; both halves above 1; net per window above 0; at fees x1.2 net above 0 and PF above 1.2; date-clustered z of per-window P/L at least **5.17**; and the card gate below. Otherwise `FALSIFIED`. A pass earns only a forward test registration and the owner's decision. **Stated plainly:** L1 itself on gold has a history PF of roughly 1.1 to 1.3 (wins of 3c to 12c against losses of 88c to 97c), so the strategy bar is very unlikely to be met by ANY execution of L1; the card gates and the reported differences are where the owner's decision about order type will come from, and they are reported whatever the verdict.

**Kill criteria (both).** `NOT_RUNNABLE`: the R6 schema changes, or more than 20% of usable windows lack a clock. `NOT_ENOUGH_DATA`: under 300 scored windows with an order. `FALSIFIED`: any gate failed with at least 300. Rules are not widened after the result. A card whose scorer finds an ambiguity not covered here takes the more conservative reading and says so.

## GF1: rest 1c inside the ask for 30 seconds, then cross with a 1c chase cap

**Rule (exact).**
1. At S, post a resting buy of C of the bought side at **L = ask(S) - 0.01** (side price, rounded to 0.001). Live at S + 1.0 s. Queue: L1Q1's (the displayed size at L on our side's bids at the posting poll, and the larger of that and the size at L on the first poll after it is live; if L is below all 5 recorded bid levels of a full side, the size ahead at L is unknown and is taken as infinite, so only a print or quote through L fills it).
2. At **S + 31.0 s** (30 s after live) the unfilled remainder is cancelled. Then, at the first poll at or after S + 31.0 s: if the side's ask there is 0.88 to 0.97 AND at most **ask(S) + 0.01**, the remainder is crossed, walking the book, taking only levels priced at most ask(S) + 0.01 (size beyond them is not bought and is counted); otherwise nothing more. A partial resting fill is kept either way.
3. Everything bought is held to settlement.

**Counterparty.** Resting leg: takers who sell the favourite into the book in the 30 s after the 6 minute mark (profit takers, stop-outs, a market maker leaning its quotes down), paid 1c of spread by us instead of the other way. Chase leg: L1's own counterparty (whoever sells a 88c to 97c favourite into the close). **The obstacle, from MAKER2 and MAKER3 and the model:** the resting leg fills when the price ticks down (in history 99% of full fills at this price came from the price coming down through it: a taker sale below it 68%, an ask lifted at or under it 29%, a quote 1%; takers selling AT our price past the queue were under 1%), so it buys the dips; the chase leg buys the risers at a higher price.

**Report.** Signals; resting full, partial and no fill shares at 30 s; chase share, skip share and chase price minus ask(S); PF and net per contract of the resting fills, of the chase fills, and of the same signals at plain L1's price; net per opportunity of GF1 and plain L1 on the same windows and the difference with its date-clustered z; per market, gold first.

**Card gate (in addition to the bar):** GF1's net per opportunity above plain L1's on the same windows in every third, at both sizes, and in gold alone over all thirds pooled.

**Numeric prediction.** FALSIFIED. Resting leg fully filled by 30 s: **50% to 65%** of gold signals (model, history: 59%; the other series are not modelled and are not predicted). Chase leg taken on 25% to 40% of gold signals, skipped (out of band or more than 1c up) on 5% to 15%; chase price ask(S) + 0.2c to + 0.8c. Net per opportunity, GF1 minus plain L1: **-0.6c to +0.1c** per contract (MAKER3's W = 60 s was -0.56c on candles; the 1c saving on about 60% of signals is about +0.6c, and the risers it loses or re-buys higher cost about as much or more). Verdict PF 0.9 to 1.3 at both sizes. Prior of a pass under 1%; prior that the card gate alone holds about 15%.

**Tries:** 2 sizes x 3 fee assumptions = **6** (the 2 verdict rows decide; stress is a gate).

## GF2: the 30 second hold: enter only if the favourite did not tick 1c down in the 30 s after the signal

**Rule (exact).** No resting order is placed. At S + 31.0 s, look at what GF1's resting bid at L = ask(S) - 0.01 WOULD have seen between S + 1.0 s and S + 31.0 s, by the same rules: if it would have been fully filled at C = 1 (a taker sale at or through L past the queue, or a print or recorded side ask at or through L), **no entry**. Otherwise, at the first poll at or after S + 31.0 s, if the side's ask is 0.88 to 0.97 and at most ask(S) + 0.01, cross for C walking the book on levels priced at most ask(S) + 0.01 (taker fee), and hold to settlement; otherwise no entry. The C = 1 test decides for both sizes (the filter must not depend on the order size).

**Counterparty.** L1's: sellers of a favourite late in the window (the longshot side's buyers, people closing), at a moment the favourite has just shown it is not dipping. **The obstacle:** waiting 30 s pays a higher ask on the entries it keeps, and a 30 s path may carry no information about a 15 minute contract that settles on one price at the close (gold settles on a single Pyth print at the close instant, `studies/SETTLEMENT_MECHANICS_2026-10-29.md`).

**Report.** Signals, entries, the entry share, entry price minus ask(S); PF, win rate and net per contract of GF2's entries; the same windows' plain L1 net per contract on ALL signals and on the signals GF2 dropped; per market, gold first.

**Card gate (in addition to the bar):** GF2's net per contract above plain L1's net per contract (all signals, same windows) in every third, at both sizes, with the date-clustered z of the per-window difference (GF2's entries against plain L1 on the same windows) at least 2.0, and in gold alone over all thirds pooled.

**Numeric prediction.** FALSIFIED on the bar. Entries **25% to 40%** of gold signals (model: 41% of gold signals not filled by 30 s, less the chase skips). Entry price ask(S) + 0.2c to + 0.8c. Net per contract of GF2's entries above plain L1's by **+0.3c to +2.0c** (the kept signals are the ones whose price was rising at the time), win rate 1 to 3 points above plain L1's, net per opportunity BELOW plain L1's (fewer trades). PF of entries 1.1 to 1.8. Prior of a pass of the full bar about 3%; prior that the card gate holds about 25%.

**Tries:** 2 sizes x 1 fee assumption (GF2 never rests, so only the taker rate applies) = **2**, plus the stress gate.

## Count and code

GOLDFILL tries: 6 (GF1) + 2 (GF2) = **8**. Running count about 439,124 (R6T) + 8 = **about 439,132** at the time of writing (the lead reconciles with any card registered in between). Deflated bar z about 5.17.

**Code.** Not written yet, on purpose: the scorer (`src/scalper/gf12.py`, `count` and `run gf1` / `run gf2`, each refusing before 2026-11-14 00:00 UTC, below 300, or a second time) reuses `scalper.goldfill.rest_fill` for the resting leg and the GF2 test, and R6T's `r6tests.py` loaders and crossing for the rest. It is to be built and tested on a synthetic fixture only, before the read date, and wired into `autoscore.py` like L1Q1.

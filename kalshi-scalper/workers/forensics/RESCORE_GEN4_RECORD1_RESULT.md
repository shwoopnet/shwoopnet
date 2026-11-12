# Re-scores on R6 order books: GEN4 forward rows and RECORD1 (2026-11-12)

Method: `RESCORE_GEN4_RECORD1_NOTE.md` (commit 0361baa, before either script ran). Scripts `gen4_rescore.py`, `gen4_rescore_check.py`, `record1_rescore.py`; raw output `results/GEN4_RESCORE.csv` (all 52 rows, every line), `results/GEN4_RESCORE.json`, `results/GEN4_RESCORE_CHECK.json`, `results/RECORD1_RESCORE.json`.

**Each is the same test: V2's own evaluator code imported unmodified, registered rule and bar unchanged, only the price source swapped from the quote recorder's market-list copy to the R6 order book. No new try.** Public recorded data, zero Kalshi requests, nothing about the live account. No Bitcoin close on or after 2026-11-05 was opened.

Lines: **L0** the old figure as V2 wrote it. **L1** V2's code on `quotes.csv`, on the windows that also have an R6 book. **L2 (primary)** V2's code on R6 book rows: signal and fill at the same poll. **L3** as L2, but the order fills only if the book 2 s (or 6 s) later still offers the ask seen or better; a miss is no trade. **L4** the rule picks its poll on `quotes.csv` exactly as it ran and pays the book's ask at that moment.

## 1. GEN4 forward rows (52 rows, Bitcoin 15 minute, closes Oct 30 to Nov 4)

**Windows.** 287 have both quote-recorder rows and an R6 book (the ledger scored 354). **Reproduction check:** V2's code on all 368 recorder windows with the recorder's own results gives every one of the 52 rows within 4 to 8 trades and within 0.09 of the ledger's PF (the 14 extra windows had not landed when the ledger last ran). So the old figures are reproduced, and L1 against L2 is a like-for-like comparison.

### What happened, in one table

PF at 1 contract; fees as V2 registered them (rounded up to the cent per order).

| Group | Rows | L0 ledger | L1 quotes, same windows | **L2 book** | L3 book, 2 s fill rule | Quote ask against book ask at the signal |
|---|---|---|---|---|---|---|
| Favourite-side rows | 42 | median 0.80 | median 0.77 | **median 0.70** (range 0.54 to 0.97) | median 0.89 | quote 1.0c below the book on average |
| Other rows (spot-momentum, underdog and NO side) | 10 | median 1.30 | median 1.84 (1.23 to 2.09) | **median 1.13** (1.01 to 1.74) | median 1.20 | quote 4.5c below the book on average; 2c or more below on about half the picks |

Rows at PF 1.0 or better: 15 of 52 on the quote file, 10 of 52 on the book. Rows at 1.5 or better: 7 on the quote file, 2 on the book.

### The rows the audit named

Mean = cents per trade at 1 contract. Gap = quote ask minus book ask at the signal (negative: the quote showed a cheaper ask than the book had).

| Row (side; conditions) | L0 ledger | L1 quotes | **L2 book** | L3 book, 2 s | L3 book, 6 s | L4 quote signal, book price | Gap |
|---|---|---|---|---|---|---|---|
| B42 (underdog; spot moved its way over 15 s) | 1.73, n 98 | 1.98, n 81, +10.8c | **1.07, n 76, +1.0c** | 1.01, n 42 | 1.32, n 45 | 1.32, n 78 | -6.3c |
| B35 (underdog; same, tight spread) | 1.68, n 95 | 2.09, n 79, +11.7c | **1.14, n 65, +1.9c** | 1.55, n 36 | 1.35, n 40 | 1.38, n 76 | -6.1c |
| B37 (NO; spot fell over 5 s) | 1.29, n 103 | 1.87, n 83, +9.0c | **1.08, n 74, +1.0c** | 1.31, n 47 | 1.31, n 45 | 1.32, n 79 | -5.7c |
| B03 (NO; three conditions) | 1.20, n 102 | 1.58, n 84, +9.6c | **1.06, n 79, +1.1c** | 1.05, n 43 | 0.95, n 37 | 1.40, n 80 | -5.6c |
| B05 (NO; spot fell over 30 s) | 1.39, n 92 | 1.98, n 79, +10.3c | **1.50, n 74, +5.8c, z 1.3** | 1.74, n 45 | 1.42, n 42 | 1.61, n 76 | -4.5c |
| B06 (NO; same, tight spread) | 1.44, n 122 | 1.90, n 100, +9.9c | **1.58, n 92, +7.1c, z 1.8** | 2.28, n 48 | 1.51, n 48 | 1.58, n 97 | -3.2c |
| B11 (NO; same, with a book balance condition) | 1.31, n 109 | 1.80, n 88, +8.7c | **1.74, n 92, +8.4c, z 2.1** | 1.53, n 44 | 1.75, n 43 | 1.63, n 86 | -2.2c |
| REF_FAV150 (favourite, no condition) | 0.81, n 113 | 0.74, n 92 | **0.71, n 94, -7.1c** | 0.92, n 46 | 1.18, n 42 | 0.71, n 92 | -1.0c |
| B01 (favourite) | 0.81, n 110 | 0.85, n 91 | **0.70, n 104, -6.7c** | 1.06, n 45 | 0.94, n 41 | 0.81, n 91 | -1.1c |

### Reading

1. **Most of the spot-momentum result was the copy.** Seven of the ten non-favourite rows fall from PF 1.2 to 2.1 on the quote file to 1.0 to 1.2 on the book, and their mean falls from about +9c to +12c a trade to about +1c to +3c. On those rows the quote the rule read was 5c to 6c cheaper than the real ask on average. An order sent at the quote's ask would have filled about a third of the time (B42: 33%, and those fills lose, PF 0.40, n 27).
2. **The favourite rows were dead before and are dead on the book** (median PF 0.70). Nothing to re-open.
3. **Three rows did not fall to 1.0, and the prediction written before the run was wrong about them.** B05, B06 and B11 are one rule seen three times: buy NO when spot fell over the last 30 seconds (the three differ by one extra condition and share most of their trades). On the book at the same poll they are PF 1.50 to 1.74, mean +5.8c to +8.4c, n 74 to 92. **Label: no evidence at n = 92.** Reasons it is not a finding:
   - z is 1.3 to 2.1 on six days against a research bar of 5.46, and these are the best three of 52 rows chosen after the fact.
   - Its nearest neighbour in the same frozen list, the same rule with a looser threshold (B09, spot not rising), is at PF 1.11 on the book.
   - It appears on the NO side only; there is no reason a spot lead would work one way. NO won 50.9% of the windows that week, so it is not a drift in the market, which leaves chance as the plain reading.
   - L2 assumes the order fills at the instant of the signal. With the fill rule only about half the orders fill (n 44 to 48); the PF on those is 1.5 to 2.3, which at that n says nothing either way.
4. **It is the same family as Refinement's W-SPOTLEAD1** (spot moves, then buy at the current book ask), on the same recorder and overlapping dates, so it is not independent support for that test. W-SPOTLEAD1 is already registered on R6 books with its own bar; that is where this question is read. Nothing new should be registered from this re-score.
5. **The ledger's flag** ("PF 1.5 or better at 1 and at 10 contracts on 30 or more trades over 10 or more trade days") is met by no row on any line: there are six trade days.

**Verdict for the audit row:** the GEN4 forward figures priced on `quotes.csv` are withdrawn. The book-priced lines above replace them. The 52 rows should stop being scored from `quotes.csv`; if V2 wants the ledger to keep running for these rows it must read R6.

## 2. RECORD1, covered part (closes Oct 29 22:15Z to Nov 3 21:00Z; Bitcoin, Ethereum, XRP, Dogecoin)

844 windows have both sources (212, 205, 210, 217). The rule: model chance from per-second spot beats the ask by 3c after the fee, at 60, 45, 30 or 15 s before the close, at least 5 contracts shown, 1 contract held. Fee unrounded, as registered. z is by date, V2's function.

| Line | Trades | Mean per trade | z | PF | Note |
|---|---|---|---|---|---|
| L0, registered read of Nov 3 (five series, Oct 22 to Nov 3) | 300 | +3.81c | 1.60 | n/a | NOT_ENOUGH_DATA |
| L1, quotes, these windows | 88 | -0.4c | -0.1 | 0.97 | Bitcoin 41, Ethereum 29, XRP 18, Dogecoin 0 |
| **L2, book, same poll** | **66** | **-5.0c** | **-2.2** | **0.66** | 22 wins |
| L3, book, 2 s fill rule | 39 of 66 filled | -7.4c | -1.9 | 0.48 | |
| L3, book, 6 s fill rule | 37 of 66 filled | -6.5c | -1.6 | 0.46 | |
| L4, quote signal, book price | 78 of 88 priced | -4.5c | -1.7 | 0.66 | paid 3.8c above the quote's ask on average |
| L4, same, only if the book ask is at or under the quote's | 34 of 88 | -7.0c | -2.1 | 0.59 | |

### Reading

1. **On the part that can be checked, the stale quote was worth about 4c to 5c a trade to this rule**: the same windows give -0.4c on the quote file and -5.0c on the book, and a rule that picked on the quote paid 3.8c more than the quote's ask at the book. That is the size of the registered read's whole mean (+3.81c).
2. **Label: no evidence at n = 66**, direction negative (five dates, so the z is weak). Against the prediction written before the run: the trade count fell by a quarter, not sharply, and the mean is below zero, not at zero.
3. **The covered part was not positive even on the quote file** (-0.4c, n 88). The registered read's positive mean came from the dates before Oct 29 and from Solana, which cannot be re-scored and stay VOID.
4. On the registered bar (mean 2c or more with z 3 or more, at 300 trades on 10 dates) the covered part is NOT_ENOUGH_DATA by count. It gives no support to the lag reading, and RECORD1B (already VOID as registered) has nothing here to stand on.

**Verdict for the audit row:** RECORD1's positive mean is withdrawn as evidence of a lag. The covered part on books is "no evidence at n = 66, direction negative"; the uncovered part is VOID.

## What the two re-scores say together

The two largest positive figures built on the quote recorder do not survive a current price. What is left is one small unproven thread, already under test elsewhere on the right data: whether spot leads the Kalshi BOOK by enough to pay the fee (W-SPOTLEAD1). Nothing here could become a live probe, and nothing here is a cost saving. The practical gain is negative knowledge: the ledger's "favourite rules died, spot rules lived" split was mostly an artefact, and no one should build on the quote-file figures.

## Caveats

Six days (GEN4) and five (RECORD1), with gaps in R6. R6 polls every 2 s where the quote recorder polled every 0.6 s, so a rule can find its first qualifying poll up to 2 s later on the book than it would on a faster book feed. The spot index is the recorder's own (three exchanges' public trades), used through V2's functions; its timing against the book was not separately checked. L3's fill rule is this desk's convention (FILLHAIRCUT1), not part of either registration. Not checked by the Verification Analyst.

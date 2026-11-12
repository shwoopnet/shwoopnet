# WHEEL0: does a hot block predict the next block? The premise test of the rotation lane

**Registered 2026-11-12, before any outcome was joined to any signal of this test.** Ordered by the owner by popup ("run the premise test now"), designed by the Head of R&D (messages of 19:53Z and 19:57Z, rulings of 20:02Z), built by the Forensics desk. Research only: public recorded data, no order, no account figure.

**Tries: 1.** One read, on the Head of R&D's go, after Auditor B's leak audit of `wheel0.py`, **not before 2026-11-14T00:00Z and not before DEPTH1's read has been made** (Amendment 1). The scorer refuses to write a second result.

**Amendment 1 (section 15, 2026-11-12 20:30Z, before any outcome was joined) changes sections 5, 7, 8 and 9. Where the two differ, the amendment is right; the sections below are already corrected to match it.**

**Who chose what.** The templates, bands, looks, order, block rule, verdict lines and data bounds are the Head of R&D's. This desk chose none of them, on purpose: it has printed baseline outcomes on these series (section 9). The only numbers this desk supplied are measurements made with no outcome loaded (the fill shares, the luck rates) and they are fixed in files named below.

## 1. The question

The rotation lane (`ROTATION_LANE.md`, v1.1, approved by the owner) gives a rule a small live seat after a block of fill-checked signals at cash profit factor 1.3. That only pays if a rule that has just been hot stays better than a rule that has not. WHEEL0 asks exactly that, on recorded data, before any seat: **after a HOT block, is the next block better than after a block that was not HOT?**

## 2. Templates (18 a market, fixed by the Head)

- **Look L:** 600, 360 or 180 seconds before the market's close.
- **Side:** the cheap side (the lower ask) or the favourite side (the higher ask). YES ask is the quote's ask; NO ask is 1 minus the YES bid. Equal asks: no signal for either side.
- **Band on that side's ask:** cheap [5c, 20c), [20c, 35c), [35c, 50c]; favourite (50c, 65c], (65c, 80c], (80c, 88c).
- **Spread:** YES ask minus YES bid of 4c or less at the look; a one-sided quote is no signal.
- A third line, apart: favourite ask 88c to 97c (section 6).

## 3. The order

10 contracts, limit = the ask seen plus 1c, held to settlement. Fee 0.07 x p x (1 - p) x 10 rounded up to the cent. Cash result per order: win 10 x (1 - p) minus the fee, loss minus 10 x p minus the fee. A market with no yes or no result: price refunded, fee kept, counted as a loss (the Head's standing void rule).

Two price sources. They are never mixed in one figure.

**Candle read (the main read).** The look is the 1 minute candle ending exactly at close minus L (bid close and ask close). A missing candle is no signal. No candle after the look is read. The order is then kept or dropped at random at its template's measured fill share (`WHEEL0_DROP_TABLE.json`): gold, XRP and Dogecoin take the rate pooled over those three; Bitcoin and Ethereum take the XRP and Dogecoin pooled rate. The draw is a hash of the seed 20261112, the ticker, the look and the side, so it cannot depend on the outcome. Price paid = the ask seen.

**Book read (the cross-check, gold, XRP and Dogecoin only).** Recorder R6 books. The look poll is the first poll at or after close minus L, and it must arrive within 10 seconds, else no look. The fill check: the first later poll, within 4 seconds of the look poll, must still offer 10 contracts at or under the limit, walking the levels; the price paid is the average walked; no such poll, or not enough size, is no trade.

**Caveat, to be printed in the first lines of the result.** Real misses lean toward winners: on books an order that fills pays on average 0.1c to 2.5c less than the ask seen, because it fills when the price has moved against the buyer. A random drop cannot copy that. So the candle read overstates the LEVEL of every profit factor. The comparison D between HOT and not-HOT is the number that carries the verdict. Candle freshness was measured on the Bitcoin 15 minute series only.

## 4. Blocks (the lane's own rule, ruling 1)

Per template and market, in time order:

- A block is at least 60 filled signals and runs on until it holds at least 10 of the rarer outcome: wins for a cheap-side template, losses for a favourite-side template.
- The next block starts at the next signal and is built the same way. Blocks never overlap. A tail that never completes is not a block.
- **HOT** = cash PF 1.3 or better on the block, and 1.0 or better in each half (the first floor(n/2) signals, then the rest).
- Each block is paired with the next block of the same template and market.

Blocks therefore differ in length by band. On made-up fair bets the median is 60 in five bands and 88 in the cheap 5c to 20c band; the result reports the median length per band.

**Differences from the lane's full rule, stated:** WHEEL0 does not apply the lane's "within the last 21 days, on at least 7 days, no day above 30 percent of net" conditions, and it uses candles for the main read where the lane's own record allows only logged quotes or books.

## 5. Primary numbers, pooled and per market

1. **Cash PF of all orders in next-blocks that follow a HOT block.**
2. **D** = mean cash result per order (of 10 contracts) in next-blocks after HOT blocks, minus the same after not-HOT blocks. Two one-sided p values are printed (Amendment 1): (a) a bootstrap that resamples UTC days, 10,000 draws, seed 20261112 (days are the unit because templates in one market share windows); (b) the null-calibrated p: every order is kept as it is, every market's result is redrawn at random with a chance equal to its YES mid at its latest look, blocks and labels are rebuilt and D recomputed, 500 runs, fixed seed; the p is the share of those runs whose D is at least the observed D.
3. **How many blocks were HOT against luck.** Luck per band, from `wheel0_null_sim.py` on made-up fair bets under this block rule (`WHEEL0_NULL_SIM.json`): 9.3%, 6.5%, 5.7% (cheap, low to high), 6.9%, 8.7%, 6.8% (favourite, low to high).

Also reported: how often a sister template in the same market is HOT at the same moment as a HOT block (mirror side at the same look; same side at another look; another band), against that market's plain HOT share.

**Secondary, same file:** the wheel's real rule. A HOT block, then the next 30 signals at PF 1.0 or better, then the 60 after those: their pooled PF, for confirmed and not confirmed.

## 6. Third line: favourites at 88c to 97c

The owner's rule: a block is at least 150 signals and runs on to its 10th loss; HOT as above; paired with the next such block. Reported apart, never pooled into the primary numbers or the verdict.

## 7. Verdict (fixed now; no other label)

On the pooled candle read:

- **PREMISE SUPPORTED** if PF after HOT is 1.15 or better AND D is above 0 with BOTH p values (the day bootstrap and the null-calibrated p) at 0.05 or less AND there are at least 30 HOT pairs.
- **PREMISE NOT SUPPORTED** if, with at least 30 HOT pairs, PF after HOT is under 1.0 or D is 0 or less.
- Otherwise **"no evidence at n = x HOT pairs"**.

The book read and the per-market lines are printed with the same three labels for comparison only. They do not change the verdict.

## 8. Data and bounds

| Series | Source | Closes used |
|---|---|---|
| Bitcoin 15 minute | candles already landed (`CFRTI_K_CANDLES`), results from `CFRTI_K_LISTS` | 2026-09-12 to before 2026-10-29 |
| Ethereum 15 minute | candles and lists to pull (`WHEEL0_LISTS`, `WHEEL0_CANDLES_ETH`) | 2026-09-12 to before 2026-10-29 |
| XRP, Dogecoin, gold 15 minute | candles and lists to pull; R6 books for the cross-check | 2026-09-12 to before 2026-11-13; books from 2026-10-29. **Gold's recorded windows of Oct 30 to Nov 13 are DEPTH1's: see the precondition below** |

- **Standing rule (h).** Bitcoin and Ethereum are held out by other cards on recorded dates. The scorer drops any Bitcoin or Ethereum market closing on or after 2026-10-29T00:00Z at the reader, on its close time, before anything else sees it, and it keeps no Bitcoin or Ethereum book row (the recorder's book files hold all five series and are filtered by ticker as they are loaded; the candle answers are filtered the same way). The Ethereum pull is bounded by the same date in the job file. Any `HELDOUT_` folder is refused, typed, nested, relative or through a link, for lists, candles and the books root.
- **Gold and DEPTH1 (Amendment 1).** DEPTH1 is registered on the gold (and Bitcoin) R6 windows of Oct 30 to Nov 13 and reads them once from 2026-11-14T00:00Z. WHEEL0 keeps gold whole, so its read joins gold outcomes on those windows. **Hard precondition, in code:** the scorer refuses to run before 2026-11-14T00:00Z AND until `WHEEL0_PRECONDITION.md` carries the committed line that DEPTH1's read has been made. One read, with gold, after DEPTH1; no early partial read. If DEPTH1's read has not been made by 2026-11-14T06:00Z, the question goes back to the Head of R&D.
- **XRP and Dogecoin:** no card known to the Head of R&D or to this desk on Nov 12 holds their recorded dates. Checked by this desk in the registrations it can see: Desk A's RESIL1 held out the five R6 series from Nov 5, but it was FALSIFIED on development and is out; the old research team's registrations that name XRP or Dogecoin all have results. That is a statement about what was checked, not about every branch.
- WHEEL0 has no held-out block of its own: it is one read of everything.
- Results come from the settled lists. Pull: about 900 requests (lists about 25, candles about 880), public GETs through the pull runner, job files checked by Main.

## 9. Disclosure (rule (h), line 7)

This desk has printed aggregate baseline outcomes on these series earlier today: the cheap side of Bitcoin 15 minute and the favourite side of gold and four crypto 15 minute series, for closes Oct 29 to Nov 8 (`FORENSICS_RESULT_NOV12.md`), and re-scores of old tests on Bitcoin closes before Nov 5. None was by template, block or streak. That is why the Head of R&D fixed every choice in this design. The old research team also read results on these series under other rules.

## 10. What was measured before registration, with no outcome loaded

- **Books-only count** (`wheel0_count.py`, `results/WHEEL0_COUNT.json`): gold, XRP and Dogecoin, 2,674 windows, closes Oct 29 22:15Z to Nov 12 12:00Z. 79% of signals at the look pass the fill check (59% to 94% by template). On books alone about 61 block pairs exist, so about 4 HOT pairs by luck: "no evidence" for certain. That is why the main read is on candles.
- **Fill shares per template** from that count: `WHEEL0_DROP_TABLE.json`.
- **Luck rates** from made-up bets: `WHEEL0_NULL_SIM.json`.
- A format check on landed Bitcoin candles: a candle exists at each of the three looks in 116 of 120 sampled markets.

## 11. Power, said plainly

Expected on candles, scaled from the book signal rates: about 1,150 block pairs and about 70 HOT pairs by luck (about 59 without Ethereum). One order of 10 has a standard deviation of about 44c a contract. Templates in one market share windows, so a design factor of about 2.5 is allowed for. The smallest D the one-sided test sees 80% of the time is about 2.7c a contract at 70 HOT pairs and about 4c at 30. The verdict's "PF 1.15 after HOT" is roughly +3.5c a contract at mid prices. So at 70 HOT pairs the test can just see the effect the verdict asks for; at 30 it would miss a real effect of that size about half the time. A "no evidence" or "not supported" result therefore does not prove that no persistence exists; it says none of the size the wheel needs was seen.

## 12. What this test cannot say

- It is two months of five 15 minute markets. It says nothing about sports, politics or any other family the wheel may run on.
- The templates are plain price-band rules. A rule with a real mechanism may persist where these do not.
- Most of the read is a candle read with a random drop. The book cross-check covers two weeks of three markets.

## 13. Files and hashes

`wheel0.py` (the scorer; `selftest`: 28 checks on made-up data after Amendment 1), `wheel0_null_sim.py`, `WHEEL0_NULL_SIM.json`, `WHEEL0_DROP_TABLE.json`, `WHEEL0_PRECONDITION.md`, `WHEEL0_LISTS.json`, `build_wheel0_candles.py`, `../wheel0_count.py`. The sha256 of the scorer, the drop table and the luck table are sent to the Head of R&D for the queue at commit time and printed in the result.

## 14. Read-once marker

`WHEEL0 READ: not yet run.` This line is replaced by the date, the Head's go line and the scorer's sha256 in the commit made immediately BEFORE the read.

## 15. Amendment 1 (2026-11-12 20:30Z; before any outcome was joined; no list or candle of this test had landed)

Cause: Auditor B's leak audit of `wheel0.py` at commit 2281057 (sha256 72b4594d...) and the Head of R&D's rulings of 20:20Z and 20:21Z on it.

1. **One defect, fixed.** The `--books` root had no `HELDOUT_` refusal. It now has one, in `main` and in `orders_from_books`, on the real path.
2. **Cross-card conflict, ruled.** DEPTH1 holds the gold R6 windows of Oct 30 to Nov 13. Ruling: gold stays whole and the read waits; the precondition of section 8 is now in the scorer (`precondition`, `NOT_BEFORE`, `WHEEL0_PRECONDITION.md`). The sentence "gold is held out by no card" was wrong and is corrected. The list and candle pulls may land earlier: the recorder branches already carry those gold results (rule (h) point 7), and the protection is the precondition, the default-closed guards and the ban on joining before the read.
3. **Which p carries the verdict, ruled.** Auditor B ran 360 no-effect replicates through this pipeline: D is unbiased, but the day bootstrap gives p at or under 0.05 in 7.5% of them, not 5%. A null-calibrated p is added (section 5). **SUPPORTED now needs both p values at or under 0.05.** NOT SUPPORTED and "no evidence" are unchanged. This can only make SUPPORTED harder.
4. **Two weak selftests, strengthened.** Two deliberately broken copies of the scorer had passed the selftest: (a) one that labelled a block by its OWN flag in the PF lists only; (b) one whose bootstrap p was forced to zero. New checks kill both: on no-effect data PF after HOT must be within noise of PF after not-HOT; and across three seeds of no-effect data the bootstrap p must not be tiny and must differ. A third new check runs the null calibration on no-effect data. The selftest is now 28 checks.
5. **Wording.** "Never reads a Bitcoin or Ethereum book" is replaced by what is true: no Bitcoin or Ethereum row is kept; the files are parsed whole and filtered by ticker.
6. **Calibration numbers for the result page (Auditor B's, on made-up no-effect data: two series, 50 days, drop 0.8):** D mean +0.005 and standard deviation 0.111 dollars per order of 10; 0 of 360 runs SUPPORTED; PF after HOT averages 0.89 under no effect (the fee drag), so a PF after HOT near 0.9 is what "nothing there" looks like, not a sign of harm.
7. Everything else Auditor B tested was clean, by mutants of this scorer run through its own selftest: the look minute, the drop's independence from the result, the fee rounding, the halves, the block pairing, the label direction, the verdict thresholds at their edges, rule (h) at the reader to the second, and the count path holding no result.

Not changed: the templates, the order, the block rule, the drop table, the luck table, the data bounds, the tries (1).

## 16. Amendment 2 (2026-11-12 20:45Z; before any outcome was joined): exact text for what section 3 to 6 left open

Cause: the Testing Desk built a second scorer from this registration alone and found places where the words allow more than one reading. **Nothing in `wheel0.py` changes (sha256 42b31450... stands).** This section states what the committed scorer does, so a second build can match it bit for bit. On the Testing Desk's made-up fixture the two builds already agree on every market, every rule (h) drop and every signal before the drop (39,766 of 39,766).

1. **The random drop.** u = the first 8 bytes of sha256 of the text `20261112|<ticker>|<L>|<side>`, read as a big-endian integer, divided by 2^64. `<L>` is 600, 360 or 180. **`<side>` is the contract bought, the word `yes` or `no`** (not "cheap" or "fav"). The order is kept if u is strictly below its fill share. The share is looked up by (group, L, cheap or fav, band) in `WHEEL0_DROP_TABLE.json`; group is `gold_xrp_doge` for gold, XRP and Dogecoin and `xrp_doge` for Bitcoin and Ethereum. The 88c to 97c line has its own rows.
2. **Quotes.** A two-sided quote is bid and ask both present with 0 < bid < ask < 1. NO ask = 1 minus YES bid. Asks equal within 1e-9: no signal. Spread at most 0.04 + 1e-9. Band edges are compared with a tolerance of 1e-9; the 88c to 97c line is 0.88 <= ask <= 0.97, and an ask of exactly 0.88 belongs to it, not to 80c to 88c. The price paid is the ask rounded to 4 decimals.
3. **Order of signals.** Inside a template and market: the market's close time, then the ticker. An order's day is the UTC date of its market's close.
4. **Blocks and HOT.** As section 4. A void counts as a loss (never a win) in the rarer-outcome count and in every PF. PF with losses of zero and wins above zero is infinite and passes any PF bar; PF of nothing is "none" and passes no bar. Thresholds are compared with a tolerance of 1e-9.
5. **The day bootstrap.** Rows are the orders inside next-blocks (every block except a template's first), the 88c to 97c line left out. Python `random.Random(20261112)`. Days are the distinct UTC days of those rows in ascending order; each draw picks as many day indices as there are days with `randrange`; D of a draw is (sum of cash after HOT / count after HOT) minus the same after not-HOT over the drawn days, a day drawn twice counted twice; a draw with either count at zero is left out. p = the share of kept draws with D at or below 0. The interval is the 2.5% and 97.5% order statistics.
6. **The null calibration.** Python `random.Random(20261113)` (the seed plus 1). The chance for a market is its YES mid at the smallest L that has a two-sided candle. In each of 500 runs one `random()` is drawn per ticker, over every ticker that has at least one kept order in any template (the 88c to 97c line included), in ascending ticker order; the market's made-up result is yes if the draw is below its chance. Every order keeps its side and price; no void exists in a run. Blocks, HOT flags and D are rebuilt as in sections 4 and 5 (the 88c to 97c line left out); a run with no order on one side of D is left out. p = (1 + the number of runs with D at least the observed D minus 1e-9) / (runs kept + 1).
7. **Rounding before the verdict.** The verdict is applied to the figures as printed: PF to 3 decimals, D and both p values to 4.
8. **Sister templates.** For a HOT block X: its moment is the midpoint of the close times of its first and last order. A sister template (same market, any of the other 17) counts if one of its completed blocks spans that moment (first order's close <= moment <= last order's close); that block's HOT flag is tallied. Kinds: "mirror side, same look" (same L, other side, any band); "same side, another look" (same side, other L, any band); "same side and look, another band"; "other"; and all sisters together. The plain HOT share is HOT blocks over blocks of that market.
9. **Secondary rule.** For every HOT block ending at position e of its template's order list that has at least 90 later orders: the next 30 are the confirmation (confirmed if their PF is 1.0 or better; no loss is confirmed), the 60 after those are the seat; seat orders are pooled by confirmed and not confirmed.
10. **HOT against luck.** Expected = the sum over bands of (blocks in the band) x (the band's rate in `WHEEL0_NULL_SIM.json`).

11. **Secondary rule and the block grid.** The secondary's 30 and 60 are counted on the template's own order list, starting at the order after the HOT block's last order, and do not use the block grid: the 30 confirmation orders are not part of the 60 seat orders, and both may lie inside what the primary numbers call the next block. A HOT block with fewer than 90 later orders (so also one with fewer than 30) is left out of the secondary line and is not counted as confirmed or not confirmed.
12. **Sisters, against the Head's wording.** The Head's intent was "blocks of two templates in the same market whose date ranges overlap, both HOT". Point 8 is the exact form used: of all sister blocks that overlap a HOT block, the one that spans the HOT block's midpoint is the one tallied, so each HOT block and sister template gives at most one comparison.
13. **A ticker with no chance value.** The null calibration leaves out an order whose market has no two-sided candle at any look. On a candle read that cannot happen (an order needs a two-sided candle at its own look), so the observed read and the null runs use the same orders.
14. **Code against text.** One place where the committed code and the registration's own words disagreed: section 3 said "the side" for the drop and section 2 used "side" for cheap or favourite; the code uses the contract word. Point 1 settles it by stating the code. No other disagreement was found by this desk, Auditor B (CLEAN at 2f0cc1e2, the same scorer file) or the second build so far.

A made-up-data comparison file is in `fixture_check/` (the Testing Desk's fixture, seed 11: invented markets, candles and results; nothing real).

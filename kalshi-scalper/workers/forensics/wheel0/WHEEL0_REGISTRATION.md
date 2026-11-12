# WHEEL0: does a hot block predict the next block? The premise test of the rotation lane

**Registered 2026-11-12, before any outcome was joined to any signal of this test.** Ordered by the owner by popup ("run the premise test now"), designed by the Head of R&D (messages of 19:53Z and 19:57Z, rulings of 20:02Z), built by the Forensics desk. Research only: public recorded data, no order, no account figure.

**Tries: 1.** One read, on the Head of R&D's go, after Auditor B's leak audit of `wheel0.py`. The scorer refuses to write a second result.

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
2. **D** = mean cash result per order (of 10 contracts) in next-blocks after HOT blocks, minus the same after not-HOT blocks. One-sided p from a bootstrap that resamples UTC days, 10,000 draws, seed 20261112. Days are the unit because templates in one market share windows.
3. **How many blocks were HOT against luck.** Luck per band, from `wheel0_null_sim.py` on made-up fair bets under this block rule (`WHEEL0_NULL_SIM.json`): 9.3%, 6.5%, 5.7% (cheap, low to high), 6.9%, 8.7%, 6.8% (favourite, low to high).

Also reported: how often a sister template in the same market is HOT at the same moment as a HOT block (mirror side at the same look; same side at another look; another band), against that market's plain HOT share.

**Secondary, same file:** the wheel's real rule. A HOT block, then the next 30 signals at PF 1.0 or better, then the 60 after those: their pooled PF, for confirmed and not confirmed.

## 6. Third line: favourites at 88c to 97c

The owner's rule: a block is at least 150 signals and runs on to its 10th loss; HOT as above; paired with the next such block. Reported apart, never pooled into the primary numbers or the verdict.

## 7. Verdict (fixed now; no other label)

On the pooled candle read:

- **PREMISE SUPPORTED** if PF after HOT is 1.15 or better AND D is above 0 with p of 0.05 or less AND there are at least 30 HOT pairs.
- **PREMISE NOT SUPPORTED** if, with at least 30 HOT pairs, PF after HOT is under 1.0 or D is 0 or less.
- Otherwise **"no evidence at n = x HOT pairs"**.

The book read and the per-market lines are printed with the same three labels for comparison only. They do not change the verdict.

## 8. Data and bounds

| Series | Source | Closes used |
|---|---|---|
| Bitcoin 15 minute | candles already landed (`CFRTI_K_CANDLES`), results from `CFRTI_K_LISTS` | 2026-09-12 to before 2026-10-29 |
| Ethereum 15 minute | candles and lists to pull (`WHEEL0_LISTS`, `WHEEL0_CANDLES_ETH`) | 2026-09-12 to before 2026-10-29 |
| XRP, Dogecoin, gold 15 minute | candles and lists to pull; R6 books for the cross-check | 2026-09-12 to before 2026-11-13; books from 2026-10-29 |

- **Standing rule (h).** Bitcoin and Ethereum are held out by other cards on recorded dates. The scorer drops any Bitcoin or Ethereum market closing on or after 2026-10-29T00:00Z at the reader, on its close time, before anything else sees it, and it never reads a Bitcoin or Ethereum book. The Ethereum pull is bounded by the same date in the job file. Gold, XRP and Dogecoin are held out by no card (Head of R&D, 19:53Z). Any `HELDOUT_` folder is refused, typed or through a link.
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

`wheel0.py` (the scorer; `selftest`: 22 checks on made-up data), `wheel0_null_sim.py`, `WHEEL0_NULL_SIM.json`, `WHEEL0_DROP_TABLE.json`, `WHEEL0_LISTS.json`, `build_wheel0_candles.py`, `../wheel0_count.py`. The sha256 of the scorer, the drop table and the luck table are sent to the Head of R&D for the queue at commit time and printed in the result.

## 14. Read-once marker

`WHEEL0 READ: not yet run.` This line is replaced by the date, the Head's go line and the scorer's sha256 in the commit made immediately BEFORE the read.

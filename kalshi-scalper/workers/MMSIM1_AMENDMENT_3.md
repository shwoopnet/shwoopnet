# MMSIM1 Amendment 3 (Nov 12, 2026, committed BEFORE the held-out read): the read is reported under both fill rules and judged on price priority

**What this amends.** `kalshi-scalper/workers/MMSIM1_PROTOCOL.md` on branch `claude/epic-ptolemy-0amjd9` (with its Amendments 1 and 2), and through it the held-out reads of `workers/MMHOUR1_PROTOCOL.md` and `workers/MMPOWER1_PROTOCOL.md` on the same branch, which use MMSIM1's base rule. Written by Idea Desk A on the order of the Head of R&D (Nov 12, 2026), because Research V2 is retired and cannot amend its own file. This file lives on `claude/idea-desk-a`; nothing on V2's branch was edited. Research and simulation only: no order, no key, no Kalshi request. No held-out row was opened to write it.

**Why.** `workers/DESK_A_MMSIM1_FILL_MODEL_NOV12.md` (this branch, commit df016de): the registered fill rule fills a resting bid only when the queue ahead is cleared AT our price and never when the market trades THROUGH it. An exchange fills the best price first, so those are real fills, and they are the adverse ones. On the 168 development events the registered rule reads PF 1.41 (maker 0) with 35.5% of quotes filled; with the missing fills added the same quoting rule reads PF 0.16 to 0.29 with about 89% filled. The finding is the working truth of the R&D group pending the Verification Analyst's independent re-run. V2's own earlier registration on this market, `workers/Q2B_REGISTRATION.md` (QUOTE2B, Oct 29, item 4b), already filled an order when "the price trades or quotes THROUGH ours"; MMSIM1 dropped that clause.

## 1. What does NOT change

- The date: one read, on or after **2026-11-24**. Nobody runs early.
- The cutoff: the date constant `PINNED_CUTOFF = "2026-11-07T15:00:00Z"`. Development = events closing before it; held-out = events closing at or after it.
- The read-once marker in `MMSIM1_PROTOCOL.md` and `src/scalper/readonce.py`: one scoring run, refused a second time and refused before the date.
- The five SPENT events (closing 2026-11-07T15:00Z to 19:00Z, already scored once in the REBATE1 rerun): the read is reported both ways, with and without them.
- The quoting rule itself: 7 recorded strikes, one contract a side, posted at the first book poll at or after T-50 at each side's best bid, never repriced, cancelled at T-15; a one-sided fill is sold at that side's best bid at T-15 (taker fee); a filled pair pays exactly 1.
- The report set of Amendment 1 (one contract unrounded, one contract with the fee rounded up to the cent, ten contracts rounded; each at maker 0 and at the 0.0175 x p x (1 - p) bound) and of Amendment 2 (the fractional-size share of the fills, beside every PF).
- The gold correlation clause and the n of at least 300 events in the original bar. They are reported; see section 3 for what is judged.

## 2. The two fill rules

**Rule Q (as registered).** A resting YES bid at price p is filled when the cumulative contracts traded at yes price p by takers selling YES (`taker_outcome_side` "no") after the post time reach the queue ahead plus 1; a resting NO bid at q likewise at yes price 1 - q with taker side "yes". Cancels ahead are ignored.

**Rule P (price priority).** The order is filled at OUR price at the EARLIEST of:
1. the Rule Q condition;
2. a taker print through our price: for a YES bid at p, a taker-"no" trade at a yes price strictly below p; for a NO bid at q, a taker-"yes" trade at a yes price strictly above 1 - q; with the trade's `created_time` after the post time and not after T-15;
3. the book: the first book poll after the post, before T-15, at which that side's best bid is below our price or absent.
A quote moving AWAY from our price in our favour is not a fill. Everything after the fill (pair, one-sided sale at T-15, fees) is as registered.

Reference implementation: `workers/desk_a_fillmodel/mm_probe_prio2.py` (mode "book" is conditions 1 and 3, mode "tape" is 1 and 2; Rule P is the union of all three). **Before the read**, the runner ports Rule P into a copy of `src/scalper/mmsim1.py` and shows, on DEVELOPMENT events only, that the copy reproduces Rule Q exactly (168 events, 1,113 strikes, 400 and 391 fills, 174 pairs, 443 one-sided, PF 1.41 at maker 0 and 1.28 at the bound) and reads Rule P inside the range of the note (quotes filled 85% to 91%, PF at maker 0 between 0.16 and 0.29). The port's commit hash is recorded in the read's write-up. If the port cannot reproduce Rule Q on development, the read does not happen until it can.

## 3. Reported under both, judged on Rule P

The single held-out run prints every figure of Amendments 1 and 2 twice: under Rule Q and under Rule P. **The verdict is taken from Rule P**, on the registered basis (one contract, fee unrounded, maker at the 0.0175 bound), with the other sizes and the maker 0 figure beside it:

| Held-out result under Rule P | Label |
|---|---|
| PF under 1.0 on about 400 events (at least 300) | **FALSIFIED** |
| PF 1.3 or better AND a positive mean of the daily results | **LEAD CONFIRMED**: keep recording, read again at about 1,900 events |
| anything else | **NO CALL** |

- The Rule Q figure is reported for the record and decides nothing. A Rule Q "pass" beside a Rule P fail is written up as what it is: the fill model, not an edge.
- Nov 24 still cannot be a research-bar pass (Amendment 2): the bar needs about 1,900 events.
- For scale, development under Rule P (168 events): mean about -18c an event at one contract, standard deviation about 63c, 1 positive day of 10. If the held-out resembles development, FALSIFIED is the expected label.

## 4. MMHOUR1 and MMPOWER1

- **MMHOUR1.** Its two cells carried to the held-out read (the 12 to 18 Central block, and high touch depth) are read in the same single run, under both fill rules, and judged under Rule P with the same three labels. Their development figures (PF 2.59 and 2.11, the best of 92 looks) were computed under Rule Q and are not evidence under Rule P. "High depth is better" under Rule Q is expected to weaken or reverse under Rule P: a long queue made Rule Q fill less, which is the very thing it got wrong.
- **MMPOWER1.** Its power figures (the chance of reading PF 1.3 or 1.5 at a given n) were bootstrapped from Rule Q development results and do not describe the Rule P read. They stay in the file as computed and are not quoted for the Nov 24 read. Under Rule P the development mean is about -3.8 standard errors below zero on 168 events, so 300 to 400 held-out events are enough for a FALSIFIED label if the held-out resembles development.
- **MMSIM2** (9 variants, development only, NOT_ENOUGH_DATA) has no held-out read; its figures are Rule Q figures and are not evidence under Rule P.

## 5. Who runs it, and how it reaches the owner

The runner is Idea Desk A (order of the Head of R&D), with V2's committed script and the Rule P port side by side. The result goes to the Verification Analyst through Main before any figure reaches the owner. N tried: 0 added (the same one registered rule; a correction to its fill model, fixed before the read).

## 6. One open conflict, for the Head of R&D

`QUOTE2B` (`workers/Q2B_REGISTRATION.md`) is an unread registered test on the SAME market and recorder files, with a through-price fill rule, re-quoting each boundary, and its own last-third holdout; its first read was allowed from 2026-11-12. Its holdout overlaps MMSIM1's held-out events. Reading QUOTE2B before Nov 24 would show, under a near-identical rule, what the MMSIM1 held-out contains. Until ruled otherwise this desk treats QUOTE2B as NOT to be read before the MMSIM1 read.

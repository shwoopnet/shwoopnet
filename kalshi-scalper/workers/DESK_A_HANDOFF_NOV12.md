# Idea Desk A handoff (written Nov 12, 2026, about 16:20Z, for a fresh Desk A session)

The first Desk A session is large; the Head of R&D asked for this handoff so a fresh session carries the open work. Read this file, then `docs/RND_CHARTER.md`, `docs/STRATEGY_LIFECYCLE.md` (sections 3, 6, 7b to 7g) and `docs/POLITICS_RULES.md` on main. Session ids are not written here (public repo); the Head of R&D gives them in the opening message.

## 1. Who you are and the rules that never bend

- Idea Desk A: market STRUCTURE and CROSS-MARKET mechanisms. You report research to the **Head of R&D**. **Main** (Chief of Staff and Head of Engineering) keeps engineering, merges, recorders and anything live. Research V2 is **retired**; its branch `claude/epic-ptolemy-0amjd9` is read-only history. Refinement owns live performance and the sports cell.
- Research and simulation only. Never place, change or cancel an order; never spend; never ask for, store or write a key, token, password or account number.
- **Zero Kalshi API calls** unless the Head of R&D allocates reads. The pull workflow (`workers/KALSHI_PULL_DESIGN.md`) is a design on HOLD until a person reads Kalshi's Developer Agreement.
- Only sources whose terms were read and allow automated access. Barred by gates or rulings: ESPN, NHL, MLB, NBA.com, Yahoo, Polymarket, Rotten Tomatoes, Metacritic, Billboard, kworb, Open-Meteo, RealClearPolling, Silver Bulletin, VoteHub, X, Reddit, Facebook, TikTok, Kalshi comment pages.
- **The repo is PUBLIC. No live account figure of any kind** (P&L, PF of live orders, fill prices, a market named with its result) in any file or branch. Verification of live numbers goes by message only, as match or mismatch.
- No model name in commits. Commit messages end with only the `Claude-Session:` line. Ordinary commits only: **no force push, no history rewrite** (the owner settled the old commit: history stays).
- No pull request unless asked. Work on branch `claude/idea-desk-a`.
- Cutoffs are DATE CONSTANTS, never "two thirds of what is on the branch". Held-out blocks are read once, on their date, by the named runner. A FAIL needs about 100 trades; below that write "no evidence at n = x". Every registered variant counts as a try. Three FALSIFIED close a family.
- Never pad. If there is nothing new, say so. Lead reports with the result; plain words; cash PF with n and window; times in US Central for the owner.

## 2. What exists on this branch (all under `kalshi-scalper/workers/`)

| File | What it is |
|---|---|
| `IDEA_DESK_A_NOV11.md` | The 11 cards and their status table |
| `IDEA_DESK_A_PROTOCOLS.md`, `IDEA_DESK_A_PROTOCOLS2.md` | Protocols P1 to P8, Q1 to Q3 |
| `DESK_A_VERIFY_NOV12.md`, `desk_a_verify/` | Re-derivation of MMSIM1 (arithmetic only, see section 3) and CFRTI1-BTC |
| `DESK_A_HELD_DATA_NOV12.md`, `desk_a_held/` | CRONCLUSTER1 and RETAILFRAC1 re-derived; MMMAP1 on the five R6 series; the fractional-taker fact |
| `DESK_A_POWER_NOV12.md` | Sample sizes the bars need; the queue row by row; rulings received |
| `DESK_A_MMSIM1_FILL_MODEL_NOV12.md`, `desk_a_fillmodel/` | **The fill-model finding** |
| `MMSIM1_AMENDMENT_3.md` | The Nov 24 read: both fill rules, judged on price priority |
| `MMSIM1_SHADOW_BASELINE.md` | The baseline shadow registration, start 2026-11-24T00:00Z |
| `KALSHI_PULL_DESIGN.md`, `desk_a_jobs/` | Pull workflow design (HOLD) and three job files |

Cards: 7 closed or retired (CRONCLUSTER1, TIECOND1, EXDIV1, RETAILFRAC1, BASEFX1, TWINLOCK1, AUCTION1). ORHARVEST1 and RACEMAKE1 parked (resting-order cards, blocked on data, and must be simulated under price priority). RESIL1 and PERPBIN1: **not now** (Head of R&D). POL-n1: no reads. ECONFADE: one falsification run only when a pull route exists.

## 3. The finding everything now rests on

MMSIM1 (V2's two-sided resting quotes on the hourly Bitcoin ladder, KXBTCD) read PF 1.41 on 168 development events. Its fill rule fills a resting bid only when the queue ahead clears AT our price (Rule Q) and never when the market trades THROUGH it. An exchange fills the best price first. With those fills added (Rule P: earliest of queue cleared, a taker print through our price, best bid on our side below our price) about 89% of quotes fill instead of 35.5% and the same rule reads PF 0.16 to 0.29, about -18c an event at one contract. About 890 of 1,113 strikes become pairs (+1c); about 210 stay one-sided and lose about 20c each. Accepted by the Head of R&D as the working truth, pending the Verification Analyst's re-run through Main. **Any resting-order simulation from now on uses Rule P.**

## 4. Your tasks, in the Head of R&D's order (zero Kalshi reads for all)

**Done by the old session:** task 1 (Amendment 3) and task 2 (baseline shadow registration).

**Task 3. Repaired rule, one design pass, due Nov 14.** ONE registration committed before any scoring. At most 4 variants (cancel or reprice; short quote life; chase the second leg), each a counted try. The 168 development events only (closing before `2026-11-07T15:00:00Z`). Rule P fills. Fees: maker 0 and the 0.0175 x p x (1 - p) bound; taker fee rounded up to the cent. State that FALSIFIED on development = cash PF under 1.0 on the BEST variant, and that the forward gate is the lifecycle's: 300 forward events over 14 or more days, cash PF 1.3, second half 1.2, no day above 30% of net, then the owner's popup. **Write the family's falsified count into the registration** (section 5 below) and that this pass may be the family's last try.
Design notes from the old session (thoughts, NOT registered; choose and fix before scoring):
- The arithmetic to beat: a pair earns 1c, a one-sided strike loses about 20c, and there are about 4 pairs per one-sided strike. A repair must cut the one-sided loss to a few cents or cut their number about fivefold.
- Chase the second leg: after one side fills, move the OTHER side's bid to that side's current best bid at each decision time until it fills or T-15. A late pair then costs p + q' and loses the adverse move so far (a few cents) with no taker fee, instead of a taker sale 20c away. This is the variant I would register first.
- Short quote life: cancel unfilled quotes after N minutes and re-post at the new best bid; and a time stop on a one-sided fill (sell N minutes after the fill, not at T-15).
- Cancel on a thinning level: cancel when the visible size at our price falls under a fraction of what it was at posting. Rule P's condition 3 means a cancel must come BEFORE the level empties to matter.
- Decisions only at a cadence the bot has: the 10 second exit loop or the 1 minute function. The book is polled every 3 seconds; do not let a variant act faster than 10 seconds.
- Every strike showed a 1c spread in the quoted window (1,100 of 1,113), so "quote inside the spread" does not exist here.
- Re-posting needs the queue ahead at the new post, read from the poll at that moment; the same Rule P applies to each new order.
- Check before registering: `QUOTE2B` (`Q2B_REGISTRATION.md` on V2's branch) is an UNREAD registered test on the same market with a through-price fill rule and re-quoting at boundaries. Do not read it before Nov 24 (it overlaps MMSIM1's held-out); ask the Head of R&D whether the design pass should simply adopt its quoting rule as one of the four.

**Task 4. Runner for the dated reads** (V2's committed script and your own version side by side; each result to the Verification Analyst through Main before any figure reaches the owner; nobody runs early):
- **MMMAP1, NC15 part: Nov 15** (when `nc-data:nc15/` holds 3 full days). Protocol P8. Script `desk_a_held/mmmap1_r6.py` works on NC15 with the series list and `MM_DATES` changed (same columns; 5 second books). Reading rule fixed in P8: +0.5c at one minute with the interval above zero, 500 trades, 3 dates, median touch under 2,000.
- **NC15DEPTH1 pooled-cell registration, counts only: before Nov 19.** One pooled cell, registered before any outcome is read; V2's `POWER2_QUEUE.md` says the 3c effect is an assumption and per-series cells cannot be powered.
- **CFRTI1-BTC: first allowed Nov 20, at 50 Bitcoin edge rows.** `HELDOUT_FIRST_DAY = "2026-11-05"` in V2's `src/scalper/cfrti1.py` (line 11); marker in `WATCH_CFRTI1_BTC.md`. Registered pass = PF 1.3 with a positive mean at n 50; V2 puts the false-pass rate at 24%, so a pass is a RE-TEST lead, a PF under 1.0 is "falsified", nothing else is a call. My own re-derivation script: `desk_a_verify/cfrti_rederive.py` (venue times come in three formats: Coinbase ISO, Kraken epoch seconds, Bitstamp epoch microseconds).
- **MMSIM1 (with MMHOUR1's two cells): Nov 24**, per `MMSIM1_AMENDMENT_3.md`. Before the read, port Rule P into a copy of V2's `mmsim1.py` and reproduce the development figures listed in the amendment.

**Task 5. Shadows for CFRTI1-BTC (forward start Nov 23) and W-SPOTLEAD1 (forward start Nov 13):** read-time joins on `quote-data`, one pinned script each, one committed row per window. Draft: sections 2 and 3 of V2's `SHADOW_RULES_NOV12.md` (commit 79724f0). Check each for a moving cutoff or a running tally before adopting, and tell the Head of R&D what you changed. Section 1 of that file (MMSIM1) is superseded by `MMSIM1_SHADOW_BASELINE.md`.

## 5. The market-making family's record (for the task 3 registration)

Two-sided resting quotes, by V2's README and workers files:
- **FALSIFIED: 3.** H5 (Oct 6, quoting both sides, the first test of the idea), MAKER1 (Oct 27, tennis, all six fill and fee assumptions), MAKER4 (Oct 28, two-sided maker scalp on the Bitcoin, Ethereum and gold 15 minute markets).
- NOT_ENOUGH_DATA with a profit factor about zero: QUOTE1 (Oct 28, last 150 seconds; a later README line calls it falsified). NOT_ENOUGH_DATA or not runnable: MM1 (Oct 29, gold).
- Registered, never read: QUOTE2B (hourly Bitcoin ladder, through-price fills) and MAKER5 (15 minute, on R6).
- MMSIM1: NOT_YET_FALSIFIED as registered (Rule Q); under Rule P its development result is a loss. MMSIM2 (9 variants) and MMHOUR1 (92 looks): both closed NOT_ENOUGH_DATA, all on Rule Q.
- One-sided maker ENTRIES (a different family by MMSIM1's own card): MAKER2, MAKER3 and MWIDE1 FALSIFIED; MAKERTAIL1 and MAKERMID1 NOT_ENOUGH_DATA with a negative sign.
So the family already had three FALSIFIED before the three-falsified rule was written (Nov 11), and the owner approved MMSIM1 as a simulation after them (Nov 11, liquidity provision counted as unique). Whether the count restarts at that approval is the Head of R&D's ruling, to be quoted in the registration.

## 6. Data: where it is and the cuts you must honour

Nothing from the old session's scratchpad survives. Copy what you need from the data branches with `git show origin/<branch>:<path> > <file>` (never check a data branch out over the work tree; `quote-data` is over 700 MB).
- `quote-data:book/<date>/<hhmm>/{book,trades}.csv.gz`: hourly Bitcoin ladder, 7 strikes, top 5 levels every 3 s from T-55, tape with `trade_id`. **Development = `close_time` before `2026-11-07T15:00:00Z`; drop later rows AT LOAD.**
- `quote-data:book15r6/<date>/<HHMM>/{book,trades,coverage}.csv.gz`: five 15 minute series, 2 s books, full tape. **Nothing closing 2026-11-09 to 2026-11-13 is opened (frozen for DEPTH1).** Bitcoin and Ethereum continue to Nov 20.
- `quote-data:quotes/`: CFRTI1's inputs; development = run folders dated before 2026-11-05.
- `nc-data:nc15/`: eleven non-crypto 15 minute series, 5 s books, from Nov 12.
- `quote-data:wxens/`: weather quotes at three MORNING looks only (at least 16.5 hours before the close). It cannot support any test of prices near the close.
- `perp-data`, `sports-data`, `pol-data`: see `CLAUDE.md` on main.
Environment: python3 with pandas 3 and numpy; run analysis scripts with `python3 -I`; keep data and scripts in separate scratchpad folders.

## 7. Mistakes already made here, so you do not repeat them

1. **Confirmed a number without questioning its fill model** (MMSIM1). For any resting order: an order is filled when price trades through it. Check a simulation's rule against how an exchange matches before re-deriving its arithmetic.
2. **Committed live figures to this public branch** (removed by an ordinary commit; history stays by the owner's decision). Live numbers go by message only.
3. **Assumed a recorder's coverage** (the weather recorder) instead of reading its files first.
4. **Parsed three timestamp formats with one parser** and silently dropped two venues. Count rows in and rows out at every join.
5. A three day cell that looked like an edge (maker selling the favourite at 70c to 90c) failed its registered confirmation on five other days. Register the confirmation before loading the second sample; it works.
6. Trade and book clocks come from different machines. Require the book snapshot at least 0.25 s before a trade, and prefer book-only conditions where one exists.

## 8. Open questions waiting on someone else

- The Verification Analyst's independent re-run of the fill-model finding (through Main).
- The Head of R&D: whether QUOTE2B stays unread until Nov 24 and whether its quoting rule becomes one of the four variants; whether the family's falsified count restarts at the owner's Nov 11 approval.
- Main (engineering): a coverage row on the hourly book recorder; a results branch and schedule for shadow rows; a person to read Kalshi's fee schedule for the maker fee on KXBTCD; the R6 Bitcoin extension past Nov 20 (to the owner).

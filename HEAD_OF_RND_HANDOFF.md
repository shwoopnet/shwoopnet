# Head of R&D handoff (written Nov 12, 2026, 16:45Z; no live account figure in this file)

For whoever holds the Head of R&D role next: a fresh session, or this one after its context is compacted. Read this, then RND_QUEUE.md, DEFLATION_LEDGER.md and PROBE_SPECS.md on this branch (rnd-queue), then CLAUDE.md, docs/RND_CHARTER.md, docs/POLITICS_RULES.md and docs/STRATEGY_LIFECYCLE.md section 7e on main.

## The role

Created by the owner on Nov 12, 2026. The Head of R&D runs research; the Chief of Staff (Main) runs engineering, merges, deploys, recorders, kalshi-pull and everything live. Research and simulation only: never an order, a merge, a deploy, a spend, an account, a credential. Nothing goes live without the owner's own popup with an exact spec, and then only through Main. The Verification Analyst is independent of research and is reached through Main. Report to the EA: a line every 6 hours and anything the owner must decide at once. Lead each line with the account line Main uses (ask Main for the current one; it is message-only), then the research counts: tests registered, pulled, scored, closed, alive, desk hours idle, Databento spend.

**Restructure, Nov 12 16:49Z (owner-directed, relayed by the EA):** all research desks (A, B, Forensics, Testing, Stocks, any new one) report to the Head of R&D, who also holds the retired breadth job (breadth check, closed-family bans, draft briefs) and owns V2's pending reads. The Verification Analyst and security stay under the Chief of Staff; Refinement keeps live strategies.

## Sessions (send_message by session id)

- Chief of Staff and Head of Engineering (Main): session_01PYvNscv7toqH6sCw7ADjw2
- Executive Assistant (relays the owner): session_01PSWvZo2wc4Z8m4JHMvaQMA
- Refinement / Head of Live Strategy Performance: session_01PSWvZpZPD3ULyjU4sQhPcX (branch claude/refine-live)
- Desk A (fresh session since Nov 12 15:01Z): session_01PSWvZn6mGV21Lppbpapybi (branch claude/idea-desk-a). The old Desk A session session_01PSWvZpRsGYgz8k99mrZJ8V has stopped.
- Desk B: session_01PSWvZpwmrFdTUNmT36ngYQ (branch claude/idea-desk-b)
- Live-Data Forensics: session_01PSWvZn9mqpQ8DM1QEXpyVo (branch claude/forensics-desk)
- Verification Analyst (under Main, not research): session_01PSWvZqX5pfCnCJfvqJpDCL (Kalshi work); a second analyst for STOCKS only, session_01PSWvZpYSAd94xYoxBEakpq (private repo), created by Main Nov 12 17:34Z
- Retired or stopped Nov 12: V2 (session_01PSWvZpN1MLodfM5W2dqtii; handoff kalshi-scalper/V2_HANDOFF_NOV12.md on claude/epic-ptolemy-0amjd9), Probe Engineering (session_01PSWvZnv28Wm8fCqua9FMzq; handoff docs/probes/HANDOFF_PROBE_DESK_NOV12.md on claude/probe-desk).
- History Miner (created by the EA Nov 12 18:24Z, reports to the Head of R&D): session_01PSWvZoybUAdQYEKBwGN15o. Finds families with thousands of fetchable settled events and registers rules readable against the bar by Friday.
- Testing Desk (created Nov 12 16:44Z by Main): session_01PSWvZoWZGK1VYgdMTA25vo (branch claude/testing-desk). First task WXDAYEND's remaining count.
- Stocks Desk: session_01PSWvZo2zpvsQRUqdZwnNoW (third session, confirmed by Main about 17:18Z Nov 12; private repo attached; public branch claude/stocks-desk). Earlier: session_01PSWvZm6Fiw2pwNzcbUhudN (second, handed over and stopped) and session_01PSWvZkxSgedtJBD4vHPwcs (first; the owner typed the Databento allowance there; it runs the registered $0.30 pilot once, reports, and stops). Databento under the owner's $25 cap.

## FRIDAY FOCUS (owner, Nov 12 18:13Z)

"we still have the friday deadline of 5 strategies, so... do whatever you NEED to do to get to that point and nothing else until then". See the section of that name at the top of RND_QUEUE.md: five candidates only (stock S2 long leg, TIE3, CFRTI-K, approval NO side, PERPBIN1), everything else paused, and the owner's answer at 18:19Z: "5 live, keep the bar" (no orders before evidence, bar unchanged, goal is live strategies). Report each Friday read to the EA as it lands, one line. One-page shadow packets from each desk are due Fri Nov 13 16:00Z.

## Standing rules I set or enforce

1. Registration and scoring script are committed BEFORE data lands; every pull is scored within the hour it finishes; a held-out cutoff is a date constant and its read-once marker is a committed line.
2. Shared strict N is about 2,113,000 and the research bar is z 5.46 (one-sided) with cash PF 1.5 in each of three windows. "1.1 million, z 5.34" is withdrawn. The "lenient" ledger is retired as a bar. A test that clears only its own registered bar is reported as "cleared its registered bar", never as a research-bar pass.
3. Labels: PASS (research bar), LEAD, FALSIFIED (cash PF under 1.0 at about 100 trades or more), NO SURVIVOR (a grid with populated cells and none supporting), "no evidence at n = x" below about 100 (30 for the slow-family paper screen), "on the paper list (unproven)".
4. Price only from order books, trade tapes or sources Forensics has cleared (kalshi-scalper/workers/forensics/DATA_SOURCES_FRESHNESS.md on claude/forensics-desk). Any bid or ask from a market LIST is a copy up to about 11 seconds old. Every taker rule also reports a true book replay at +2 and +6 seconds or the haircut line (drop about 34 percent of fills at the ask seen, 24 to 27 percent at +1c, at a live-like delay); live use is judged on the 6 second line.
5. Research holds zero reads on the shared Kalshi address. Pulls go through kalshi-pull job files sent to Main (1 request a second, 1,200 a run, 200 MB a run, 6 real runs a UTC day; a PR to raise the daily limit to 12 was being cut).
6. Three FALSIFIED close a family for good; I do not restart a count in research's favour. Family = entry mechanism plus exit style (lifecycle 7f).
7. Owner rulings in force: no pre-evidence live orders (every probe spec is conditional on its read); no live probe may read Coinbase or Bitstamp without the owner's popup naming that source (research reads of both are an owner-accepted terms risk); the closing-buy family is not researched further (Oct 28) and V2's scheduled forward reads are RETIRED UNREAD (Nov 12); Databento approved for STOCKS research with a $25 total cap, a free cost estimate recorded before every pull, no raw Databento data in the repo, licence clause on storage read first (spend about $0.29 by recorded estimates at 18:25Z Nov 12; on that day the owner typed a STANDING allowance in the Stocks Desk chat: any Databento historical download the Head of R&D approves, estimate first, scratch only, nothing in a public repo, up to $25 total, so the Head of R&D is the approver of each pull).
8. A denied action stays denied: when a desk's tool call is refused, nobody else does it for that desk; it goes to the owner through the EA.
9. No live account figure in any file or branch. Live numbers travel by message only.

## Usage, the binding constraint since 16:30Z

The account hit its 5 hour usage limit for desk workers at 16:30Z (reset 18:20Z). Charter rule: no new workers at a warning, stop at overage. I had told desks to use workers freely at 16:00Z; that was too loose. Desks should batch reports (one digest an hour, or at once only when a ruling is needed or a verdict lands), because every message to the Head of R&D costs a full read of a very large context. This session was at about 747,000 of 1,000,000 tokens at 16:40Z and will be compacted at about 784,000.

## State of the research (details in RND_QUEUE.md)

- Probe-ready: 0. Passed the research bar: 0. Proven: 0. Conditional probe specs left: 0 (CFRTI-K development read Nov 12: PF 1.07 on 601, 0.16 with ran rows dropped: no tradable edge; PERPBIN1 FALSIFIED on development; the approval NO side did not clear its development read and is closed). The stock S2 long leg was read on development at 18:53Z: below the bar, closed, held-out never opened (figures private); Databento spend ends at about $2.70. THE STOCKS SEARCH IS FINISHED (the desk's own answer: no stock test is worth the remaining allowance); both stock sessions can be archived after the stocks analyst reproduces the one read. Of the original five Friday candidates only the TIE3 measurement remains; behind them MAPBREAK and the History Miner's tennis, soccer and e-soccer rules.
- CLOSED on Nov 12: two-sided market making (family; confirmed twice by the Verification Analyst; on the declined list); ROLLOFF; weather forecast-against-market (family); taker order flow on the 15 minute tape (family; RESIL1 the third FALSIFIED; analyst re-run and declined row requested); RAINCAL (retired unread); ORHARVEST1 and RACEMAKE1 (parked inside the closed market-making family); the CFRTI1-BTC lead's quoted figure (priced at a stale copy, not tradable).
- READ Nov 12 16:44Z: the sports SPREAD cell FAILED on both lines (n 172, PF 0.596; n 173, PF 0.636); REPRODUCED by the Verification Analyst (PF 0.553 and 0.592 with the registered fee) and reported to the owner at 16:48Z. Forensics' re-scores withdrew GEN4's forward figures and RECORD1's positive mean (313a509); the GEN4 forward ledger is closed. V2's perps forward reads were 20, not 11: 18 RETIRED UNREAD, 2 KEPT with the Testing Desk (PERPEQ1, read from Dec 22; CASHSPREAD1 part B, Dec 1, conditional); ABSORB-F RETIRED UNREAD (closing favourite and hold, declined list). The Testing Desk also prepares POL-i2 and UNRATEROUND.
- ALIVE: CFRTI-K (Kalshi-only Bitcoin rebuild on 1 minute candles; specification FROZEN after section 11; CANDLEVSBOOK1 cleared candles as a current price on Nov 12, a87b5c4; development read runs once when its candle sample lands); CFRTI-B (signal and price from the R6 book; read in the Nov 20 sitting); PERPBIN1 (2 tries; waits on the same candles); approval NO side (NOSIDE1, one run, PR 816); approval calibration full pull (PR 823; can give NO SURVIVOR, cannot pass); S3 combo house side (paper; read Nov 26); NC15DEPTH1 pooled cell (forward from Nov 19); DEPTH1 (one read from Nov 14); in-game lag CLOSED Nov 12 (no lag at one minute resolution, 0 tries); NHLOT price measurement stands (zero tries); census cards TIE3 and SOCDERIV approved as zero-try measurements (Testing Desk builds and runs); ECONLAG (paper screen, count-only stages); W-SPOTLEAD1 (not live-able as registered: Coinbase signal and a favourite-side rule).
- DATED READS (Desk A runs them): DEPTH1 on or after Nov 14 00:00Z; MMMAP1 Nov 15; the CFRTI sitting from Nov 20 (all versions, one sitting); MMSIM1 and QUOTE2B held-outs Nov 24 (record only, the family is closed); S3 Nov 26 (Desk B). Refinement: OICORE forward read Nov 13 with the within-price-bucket comparison; FLIP1, FLOOR1, THIN1 from the owner's export on or after Nov 14; Monday rotation report Nov 16.
- DEFECT BEING FIXED: the Nov 20 script's "book replay" lines replayed the stale quote file; Desk A is replacing them with a true R6 replay using Forensics' code. Check the commit before Nov 20.

- STOCKS (17:00Z): ten cards written, first wave S1, S2, S7 plus four screens, costed about $12.75; the owner ruled at 17:04Z "Treat it as personal use" (personal Databento account, owner-accepted terms risk; named lists only, NO all-symbols requests, $25 cap); named-list pulls may start (pilot, S1, 8 ETF minute bars); the one bounded ranking pull ($0.59, May 2018 only, hard stop above $1) is allowed (the EA confirmed "no all symbols" was its wording, not the owner's); nothing scored until registrations are in shwoopnet/shwoopnet-private. Nothing derived from Databento goes in the repo.

- STOCKS (17:10Z update): S1, S3, S4, S5, S7 RETIRED UNREAD; S2 long leg ruled GO at 17:33Z (gated on the owner typing the allowance in the desk of record's chat and on the Nasdaq half of the pilot; pulls about $0.59 and $2.0 to $2.5; development read first, held-out only on my go) (PF 1.5 on an every-day rule is an annual Sharpe near 2.6; published anomalies net about 0.05 a trade). S6, S8, S9 were then RETIRED UNREAD too (17:15Z); only S2 long leg is held, behind the $0.30 pilot, which the FORMER desk runs once (the owner typed the allowance into that session) and then stops. The paid pull route is refused by the desk session's permission check; with the EA and Main. The statistics schema close is "last trade", not proven to be the auction print: the pilot must show SPY 2026-08-27 = 771.10.

## Owed to me at the time of writing

- Desk B: the RE-OPEN RANKING (18:30Z); top 3 registered (21:30Z); the untouched-family census first cut (about 22:00Z, slipped by the usage limit) and ten new cards this week, the first three by Nov 13 16:00Z.
- Forensics: re-scores of GEN4's forward rows and RECORD1's covered part on R6 books (21:30Z); CANDLEVSBOOK1 within the hour its slice lands; measured costs by family for the census (21:30Z).
- Desk A: the R6 replay fix; a card for a perpetual-fed model against the hourly Bitcoin ladder's real order book (19:30Z; not registered until I rule).
- Refinement: the SPREADCELL1 read when the 36 land; NOSIDE1 verdict within the hour it lands; rotation report skeleton (22:00Z); the gold latch watch (message only).
- Main: Testing Desk and Stocks Desk ids; landings of each pull; the daily run limit PR; the Verification Analyst's verdicts (SPREADCELL1 first).
- Stocks Desk, once created: data plan in 3 hours (with Databento cost estimates), ten pre-registered stock mechanisms in 6 hours.

## Owed by me

- DONE Nov 12 17:11Z: V2's whole estate ruled (no KEEP beyond PERPEQ1 and CASHSPREAD1 part B); Main told which recorders have no research reader. Still owed: a ruling on DEPTH1's family when Desk A's note arrives (before Nov 14), and on the stock cards S6, S8, S9 after the desk's page (20:00Z).

- The six-hour line to the EA at about 21:00Z (3 PM CT): desks, cards added, the stocks data plan, first stock test dates, counts, Databento spend.
- Rulings on: Desk B's ranking; Desk A's ladder card; any SPREADCELL1 result (wording: "cleared its registered bar, probe-eligible by the owner's popup", and only if line 2 also holds).
- Scheduled wake-ups I set for this session: 17:27Z (desk outputs), 18:40Z (the two audits), 20:50Z (the six-hour line).

## Things I got wrong today, so the next holder does not repeat them

1. Repeated "1.1 million tries" before tracing it; the real count was about 2.1 million.
2. Told desks V2's forward reads would be run later, before checking the owner's Oct 28 instruction; Desk A caught it.
3. Specified a stress line for CFRTI-K that was degenerate for a cheap-side rule; Desk A's selftest caught it.
4. Told the owner "about a third" of picked rows were stale before Forensics' band correction made it "no evidence at n = 15".
5. Wrote queue header times ahead of the real clock, twice (run `date -u` before writing any time). Stock results go to the private repo shwoopnet/shwoopnet-private once Main attaches it to the Stocks Desk (owner, Nov 12).
6. Told desks to use workers freely; the account hit its usage limit half an hour later.
7. Passed a licence sentence to the owner as a Databento term without checking its source; it was from a Nasdaq agreement on Alpaca's site. Ask for the document name and URL of any quoted clause before it travels.
10. Told the owner "PF 0.16 on the trades an order could actually get" from a diagnostic split that is partly selection by the next price; the analyst corrected it. A split made on a later price is never quoted as what a real order would earn.
9. Told the owner a tie-contract rule could be read on history within days "with enough events" before anyone had counted the priceable history (about 630 contracts against 1,200 needed). Count the events available in the pullable window before quoting a date for any read.
8. Withdrew a ruling on a relayed phrase ("no all symbols requests") that turned out to be the EA's wording, not the owner's; when an owner instruction contradicts a standing ruling, ask whether the words are verbatim.

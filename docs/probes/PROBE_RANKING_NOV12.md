# Probe desk: leads ranked by days to a first live order (Nov 12, 2026)

**Status: a desk note. Nothing here is live, approved or deployed.** Written by the R&D Probe Engineering Desk (started Nov 12, 2026) for the Chief of Staff. Every probe below is UNPROVEN: a tiny live test to learn from real fills, not an edge. Each one needs the owner's own popup before any order (`docs/RND_CHARTER.md` section 7). No live account figure is in this file; every number is a research result on public data, a rule, or a cap. [research]

## What "days" means

Working days from an owner YES today to the first real order, counting: the build, the security agent's review, the Verification Analyst's four checks, the owner's merge, and the deploys the owner runs. It does not count waiting for a research read; where the rules require a read or paper evidence first, that wait is shown separately.

If gold L1 latches off, the account still has OICORE and EVENT830 as live probes, so it does not reach zero. Neither is at the proven bar.

## The table

| Rank | Lead | Probe in one line | Days to first order | Calendar blocker | Worst loss per order | What is missing |
|---|---|---|---|---|---|---|
| 1 | **CFRTI1-BTC** (settlement-index model, cheap side) | Bitcoin 15 minute market, 1 contract of the cheap side (5c to 30c) when a three-venue spot model says it is underpriced by 5c or more, held to settlement | **3 to 5** | None in the rules. The research held-out read is Nov 22 to 24; a probe before it is an information purchase | about $0.32 | (1) a person reads the market data terms of the three spot venues for commercial use; (2) security review of the code on this branch; (3) the Verification Analyst scores uniqueness (risk: it buys the same cheap side of the same market in the same minute as OICORE, so the 0.3 correlation check may fail); (4) the owner's popup; (5) a small activation pull request (page text, labels, final pre-registration, switch); (6) two deploys. No new function, no new cost beyond a few public reads a window |
| 2 | **W-SPOTLEAD1** (spot lead, mid band) | Same engine as rank 1, the 50c to 87c side when the model edge is 10c or more, Bitcoin first | **4 to 6** (rank 1 plus half a day) | Needs the owner's written exception to the buy-the-favourite-and-hold ban (it buys the likelier side and holds). The queue lists it closed as data limited; R6 records to Nov 20 | about $0.89 | Everything in rank 1, plus the exception, plus a decision whether it is a second strategy or a version of rank 1 (same signal, another price band: lifecycle 7g says version) |
| 3 | **MMSIM1 / MMHOUR1** (two-sided resting quotes, hourly Bitcoin ladder) | One contract resting on each side of ONE strike, cancel and flatten 15 minutes before the close; first purpose is to measure whether real orders fill as simulated | **8 to 12** | The owner deferred the first-live questions (popups 45 to 48) to the Nov 24 read; a probe before it needs the owner to open them early, and an exception to "no short round trips" | about $1 per strike-hour (a one-sided fill sold at the bid; usually a few cents) | (1) a new engine: resting orders, cancels, a flatten, restart recovery (5 to 6 build days, the largest review surface of any lead); (2) one new scheduled function; (3) API facts confirmed (post-only, cancel, order status) and one supervised dry run; (4) the maker fee on this series and which exchange shard it uses, and money on that shard (the owner moves it); (5) Flatten and Stop must also cancel resting orders; (6) the owner's exception and popup |
| 4 | **Approval NO side / nothing happens** | NO at 60c to 88c on a "will X happen by date" or approval market, 1 contract, at most $5 at risk per market, held up to 30 days | **0 to 1 by hand, 7 to 10 by bot code** | The rules say paper first (`docs/POLITICS_RULES.md` sections 1, 5, 8 in pull request 794). No cell has 30 events; the held calibration read says the 75c to 90c NO cells lose. Paper evidence is weeks away at best | up to $0.90 | Paper evidence; the shard politics singles use and money there; for bot code a new slow-market engine (daily look, 30 day hold, a stop that still counts an order older than 24 hours, the $200 lifetime budget counter). The rulebook allows the owner to place a probe by hand, which needs no code |
| 5 | **Combo house side** | NO on a high-priced combo, $2, held to settlement | **Not buildable today** | Combos showed no resting quotes in research (0 of 34 sampled; they are quoted on request). The combo book recorder's first read is about Nov 26. Paper edge of 10c per dollar over 100 settled combos is required first | $2 | A buyable quote must exist at all; then request-for-quote order code (a new order path), the combo exchange shard funded, and the paper edge. Could stay not buildable |

## Honest odds

- **Rank 1.** The pooled rule FAILED its registered bar (five series, profit factor 1.14 against 1.3). The Bitcoin cell (36 trades, profit factor 2.54, win rate one in three) was picked after the split was seen. Independent re-derivation matched it (2.18 to 2.51 on 35 to 40 trades). Research's own prior after the fail: about 1%. A probe buys real fills at about 30c a try, nothing more. [research]
- **Rank 2.** 58 fired windows, profit factor 1.58, missed its own bar of 80 and both halves; the desk that ran it leans FAIL (prior 5% to 8%). [research]
- **Rank 3.** Development profit factor 1.41 at a maker fee of zero on 168 events, 1.26 for one contract with the fee rounded to the cent, 1.15 at the fee bound. Research's written warning: the Nov 24 read is unlikely to pass. The live unknown is fills: a resting order is filled mostly when the price moves against it, and the simulation cannot see cancels ahead of us or orders that jump the queue. [research]
- **Rank 4.** Underpowered, and what was measured points the wrong way. [research]
- **Rank 5.** No evidence of any kind yet; the test cannot be priced.

## Why this order

Rank 1 and 2 fit the bot's existing second slot almost unchanged: an immediate-or-cancel buy of one contract, the direction lock, the shared 12% stop and 5.5% window cap, the settle sweep, the report. The only new part is the model reading. Rank 3 teaches the most (it answers the question the simulation cannot) but needs a kind of order the bot has never sent, so it has the most ways to go wrong and the longest review. Ranks 4 and 5 are blocked by the owner's own paper-first rules, not by engineering.

## What cannot be made safe at tiny size

- **Rank 3 at more than one strike.** Seven strikes with two resting orders each is fourteen ways to be half filled in a fast market at once. The probe spec quotes ONE strike. That measures fills; it does not test the profit claim, which needed all seven strikes.
- **Rank 5.** A $2 probe is small, but the money is locked to settlement (some combos close in 2027) and there is no exit, so "tiny" is the only safety it has.

## Next from this desk

Build-ready specs for ranks 1 and 3 (`docs/probes/PROBE_SPEC_CFRTIBTC.md`, `docs/probes/PROBE_SPEC_MMPROBE1.md`; rank 2 is covered inside the rank 1 spec as a later registry entry), then the code for rank 1 on branch `claude/probe-desk`, off by default, with tests.

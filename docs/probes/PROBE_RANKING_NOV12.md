# Probe desk: the fastest honest route to a tiny live probe (Nov 12, 2026, revision 2)

**Status: a desk note. Nothing here is live, approved or deployed.** Written by the R&D Probe Engineering Desk for the Head of R&D and the Chief of Staff. Every probe below is UNPROVEN: an information purchase to learn from real fills, not an edge. No bar for "proven" is lowered. Each probe needs the owner's own popup with its exact spec before any order (`docs/RND_CHARTER.md` section 7). No live account figure is in this file. [research]

**Revision 3 (owner decisions through the Executive Assistant, Nov 12, relayed by the Head of R&D and the Chief of Staff):** (1) NO pre-evidence orders: every probe is conditional on its read, so the "before any read" route is gone. (2) No live probe may read two of the three spot venues the CFRTI1 rule uses, so the rank 2 code is NOT ACTIVATABLE as built; it can run only in a form research has yet to register (one allowed venue, or Kalshi's own Bitcoin perpetual). (3) YES to the Chief of Staff building, switched off, the order path for a 1 contract order on a market that is not a 15 minute market; this desk's brief for that build is `PROBE_BUILD_BRIEF_LONGHOLD.md`.

**Revision 2 (the Head of R&D's rulings, Nov 12):** the market-making probe is OFF the pipeline (Idea Desk A showed the simulated profit came from a fill rule that leaves out the fills a resting order cannot avoid; with them back the same rule loses badly; `PROBE_SPEC_MMPROBE1.md` is withdrawn). The sports SPREAD cheap cell is the new rank 1, as scoping only. CFRTI1-BTC is rank 2 and conditional on its read. W-SPOTLEAD1 is a VERSION of rank 2 (lifecycle 7g), not a strategy. Combos do show posted quotes, so that row is "paper first".

If gold L1 latches off, the account still has OICORE and EVENT830 as live probes, so it does not reach zero. Neither is at the proven bar.

## The table (dates are the earliest each read allows; working days)

| Rank | Lead | Probe in one line | Fastest honest first order | What the owner could approve tonight to pull the date in | Worst loss per order |
|---|---|---|---|---|---|
| 1 | **Sports SPREAD cheap cell** (W-SPREAD-CELL1) | 1 contract of YES at 5c up to 15c on one sports spread market about 48 hours before its close, held to settlement | **By hand: 1 day after a PASS, so about Nov 16 to 18. By bot code: 1 to 2 days after a PASS once the long-hold order path is built** (the owner has approved building it, switched off; about 4 to 5 build days plus review, so about Nov 20 to 24 at the earliest). All of it only on a PASS, which research puts at 3% to 5% | (1) "merge 795" (the kalshi-pull pull request), so the 274-request read can run; (2) a conditional yes to ONE hand-placed order on a PASS, with the exact spec; (3) which loss budget a sports single uses. (Building the long-hold path, off, is already approved) | about $0.17 |
| 2 | **CFRTI1-BTC** (three-venue spot model, cheap side of the Bitcoin 15 minute market) | 1 contract of the cheaper side (5c to 30c) when the model says it is underpriced by 5c or more, held to the close | **Mid December at the earliest, and only in a form that does not exist yet.** The first read (Nov 20 to 24) must clear, then a fresh re-test; a clear without the re-test would be Nov 26 to 30 and needs the owner to ask. The code is written and switched off, but NOT ACTIVATABLE as built (the venue ruling above): research must first register a one-venue or Kalshi-only form and show its own result | Nothing tonight moves it: pre-evidence orders are ruled out and the venue ruling is made. "Merge" of the dormant code after the security re-check keeps the engine ready for whichever form research registers | about $0.32 |
| 2v | W-SPOTLEAD1, a version of rank 2 | The same engine buying the 50c to 87c side on a 10c model edge | About Nov 24 to 25, only if its own read (about Nov 21 to 23) passes | A written exception to the buy-the-favourite-and-hold ban for this version only, conditional on its read | about $0.89 |
| 3 | **Combo house side** | NO on a high-priced combo, $2, held to settlement | Paper first. The combo recorder's first read is Nov 26; a live $2 probe needs a paper edge of 10c per dollar over 100 settled combos, so December at the earliest. By hand once that exists | Nothing tonight moves it. A conditional yes to a hand-placed $2 probe on a paper edge would save a day later | $2 |
| 4 | **Approval NO side / nothing happens** | NO at 60c to 88c, 1 contract, held up to 30 days | No date. The paper read so far leans against it | Nothing; it should not be pulled in | up to $0.90 |
| off | MMSIM1, MMHOUR1, MMPOWER1 | Resting quotes on the hourly Bitcoin ladder | Off the pipeline | Not to be built | n/a |

## What is missing for each, exactly

- **Rank 1.** The read (274 requests through kalshi-pull). Then either a hand-placed order (no code; the bot would show it as unmatched account activity, so it needs a manual log line), or the build scoped in `PROBE_SCOPE_SPORTSSPREAD.md`: the second slot cannot hold a two day position today. One check before the read is trusted: which "close" the research look was measured from (see that file, section 2).
- **Rank 2.** A registered form on allowed data with its own development figure. The one-venue form was run and closed on Nov 12 (no evidence at 32 trades), so the only form left is the Kalshi-only one on Kalshi's Bitcoin perpetual, not yet scored; the read and the re-test; the uniqueness score (it buys the same cheap side of the same market in the same minute as OICORE, so the 0.3 correlation check may fail); the owner's popup; a small activation pull request; two deploys. Spec: `PROBE_SPEC_CFRTIBTC.md`.
- **Rank 3.** A paper edge. Then by hand, or new order code (scoped in section 6 of the sports file, the same named-market path, plus fractional counts and the combo exchange shard).
- **Rank 4.** Evidence, which is pointing the wrong way.

## Honest odds

- **Rank 1.** The best of about 58 cells in a sweep where no cell reached even a naive z of 2. Chance of a PASS on the new read: 3% to 5%. [research]
- **Rank 2.** The pooled five-coin rule failed its registered bar. The Bitcoin cell is 36 picked trades. A rule with no edge clears the first read about one time in four, which is why a clear means re-test. Research's prior: about 1%. [research]
- **Rank 3 and 4.** No evidence yet, or evidence against.

## Shadow logging each lead needs (owner order 2; the Head of R&D coordinates)

| Lead | Forward record with no money | New code or recorder? |
|---|---|---|
| Sports SPREAD cheap cell | For each event of the six spread series, about 48 hours before its SCHEDULED close: the market in the 5c to 15c YES ask bucket nearest a 0.5 mid, its bid, ask, sizes and the scheduled close; later its result | A small public recorder (a handful of paged reads an hour). Refinement's shadow rule S2 defines the row; it is not expressible in the bot's shadow registry, which carries only 15 minute price rules |
| CFRTI1-BTC | Per Bitcoin window: the three venues' trades and the Kalshi quote at the look | None. The quote recorder already records both, and the research scorer reads them. Check that recorder's stop date. A bot-side shadow (the model run in the minute function, logging only) would be about one build day but makes the same venue reads, so it waits on the same terms answer |
| W-SPOTLEAD1 version | The R6 book recorder plus spot candles | None until Nov 20, when R6 stops; an extension is a reviewed stop-date edit |
| Combo house side | Posted combo quotes and settlements | None. The combo recorder is running (`combo-data`) |
| Approval NO side | Approval series quotes and results | None. The politics recorder (`pol-data`) covers the listed series |

## What cannot be made safe at tiny size

- **Rank 3.** $2 is small, but the money is locked to settlement (some combos close in 2027) and there is no exit.
- **A resting-order market maker.** Withdrawn for the reason above, not for size.

## Files from this desk (branch `claude/probe-desk`)

`docs/probes/PROBE_BUILD_BRIEF_LONGHOLD.md` (the build brief for the Chief of Staff), `docs/probes/HANDOFF_PROBE_DESK_NOV12.md` (handoff), `docs/probes/PROBE_SCOPE_SPORTSSPREAD.md` (rank 1 scoping, design only), `docs/probes/PROBE_SPEC_CFRTIBTC.md` (rank 2, conditional, with popup text), `docs/probes/PROBE_SPEC_MMPROBE1.md` (withdrawn, kept as a record), and the rank 2 code, off by default, with `test/cfrtiProbeGates.test.js`.

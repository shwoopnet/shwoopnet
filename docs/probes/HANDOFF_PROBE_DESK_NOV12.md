# Handoff: R&D Probe Engineering Desk (Nov 12, 2026)

For a fresh session taking over this desk. No live account figure is in this file; live numbers stay in messages. Nothing this desk made is live.

## Who is who

- **The owner** decides every popup and every "merge". The Executive Assistant relays.
- **Head of R&D** (new role, Nov 12) owns the probe pipeline and sequencing. This desk reports to it.
- **Chief of Staff (Main)** owns pull requests, merges on the owner's word, security reviews and deploys. Copy it on specs. It opened pull request 807 for this branch.
- This desk writes specs and reviewable code. It never places, changes or cancels an order, never deploys, never merges, makes no Kalshi API call without an allocation, and opens no pull request unless Main asks.

## Standing rulings that bind this desk (Nov 12)

1. No pre-evidence orders. Every probe is conditional on its research read.
2. No live probe may read two of the three spot venues the CFRTI1 rule used; the third's terms are not stated. Do not name the two ruled-out venues in `functions/` (test CB6 fails if you do).
3. The market-making family (MMSIM1, MMHOUR1, MMPOWER1) is off the pipeline. No resting orders, no cancel path.
4. W-SPOTLEAD1 is a version of CFRTI1-BTC (lifecycle 7g), not a strategy.
5. Main builds, switched off, the order path for a 1 contract order on a market that is not a 15 minute market. This desk's brief for it is `PROBE_BUILD_BRIEF_LONGHOLD.md`. The build belongs to Main or a fresh session.
6. No live figures in the repo. No model name in commits or pull requests. No em dashes.

## What is on branch `claude/probe-desk` (pull request 807)

| File | What it is |
|---|---|
| `docs/probes/PROBE_RANKING_NOV12.md` | The pipeline note, revision 3: dates, what the owner could approve, shadow logging per lead |
| `docs/probes/PROBE_SCOPE_SPORTSSPREAD.md` | What the bot lacks to hold a two day position (12 gaps), by hand against by bot code |
| `docs/probes/PROBE_BUILD_BRIEF_LONGHOLD.md` | The build brief for Main: a named market, one shot entry, the stop fix first |
| `docs/probes/PROBE_SPEC_CFRTIBTC.md` | The conditional spec, popup text, and section 13: the two forms that could run (one venue, or Kalshi's own Bitcoin perpetual) |
| `docs/probes/PROBE_SPEC_MMPROBE1.md` | Withdrawn and superseded; a record only |
| `functions/kalshiSpotIndexLib.js` | The model as pure functions and a one venue reader. NOT ACTIVATABLE as built: the rule needs three venues, one is allowed, so it returns null and makes no request |
| `functions/kalshiSlotLib.js` | `SLOT_PROBE_CANDIDATES`, `SLOT_PROBE_SWITCH` (all false), the 1 contract cap, the sticky budget (`probeState`), the `modelEdgeMin` entry field |
| `functions/kalshiSlotRunLib.js`, `functions/index.js` | The model step in the engine and the one wiring line |
| `test/cfrtiProbeGates.test.js` | CB1 to CB10 |
| `kalshi-scalper/README.md#SLOT-CFRTIBTC` | A DRAFT pre-registration, not a registration |

Checks at handoff: every test file passes (install `functions/` dependencies first, or `kalshiPushGates` cannot load); pre-ship clean; the security scan has no FAIL. The security agent passed commit 87cf56a; the rework after the venue ruling needs its re-check.

## Open items

1. **Security re-check** of the reworked reader (Main runs it). Its two low findings are fixed: the venue call shares the overall abort timer, and a declared body length over the cap is refused before the body is read.
2. **Which CFRTI form, if any.** Research (the Head of R&D, Desk A, V2) is scoring a one-venue form and a Kalshi-only form. Change no code until one is registered with a result. Then: one venue is two constants; the Kalshi-only form is a small second reader (spec section 13).
3. **The CFRTI1-BTC read**, Nov 20 to 24, then a re-test (mid December). Under the bar, the candidate should be removed, not left dormant.
4. **The sports spread read** (274 requests through kalshi-pull, after "merge 795"). Refinement is fixing the look to a known-in-advance time. On a PASS: one hand-placed order by the owner is the fast route; the named-entry build is the bot route.
5. **Uniqueness and the OICORE correlation** for any CFRTI form: the Verification Analyst, through Main.
6. **A loss budget for a live sports single**: none exists in the rulebook; the popup must name one.
7. The first commit on the branch carries a model name in a trailer; the pull request is squash-merge only, which drops it.

## Things learned the hard way today

- A simulation's fill rule deserves the same suspicion as its profit figure. This desk ranked the market-making probe on a number it had not questioned.
- An open second-slot order older than 24 hours drops out of the shared 12% stop. It cannot bite today, and it must be fixed before any long hold.
- A look defined from a market's close is only tradable if that close was known at the look.
- Peer sessions can give instructions that pull apart (rework now, or wait). The owner's ruling is the fixed point: here, remove what may never run, keep the rest dormant, and change no model until research registers one.

# Politics and parlay rules (owner decisions, Nov 11, 2026)

**Status: recorded from the owner's popup answers of Nov 11, 2026.** It sits under `docs/CHARTER.md` (which only the owner changes) and `docs/RND_CHARTER.md`. Where they differ, the Charter wins.

**Nothing here authorizes a live order.** Every live probe, single or parlay, still needs paper edge first, a written spec, and the owner's own popup for that exact probe. These rules are the limits a probe spec must stay inside, and the research rules for the politics program.

## 1. Research rules

- **Scheduled events first.** Votes, confirmations, shutdowns and deadlines are tested before the other politics families.
- **Forward shadow recording.** The thin politics series are recorded forward (`record-politics.yml`, branch `pol-data`) so history accrues. The 14 day cap applies.
- **14 day maximum hold** to settlement for every politics or parlay position. Longer markets go on a "later only" list and are not scored.
- **Parlays are in.** 2 to 5 legs. Work is on weather, mentions and sports (NBA, NFL) combos, on Kalshi's own prices only. Whether any politics combo market exists is still being checked; if none does, politics parlays are simulation only.
- **Linked legs are allowed.** The link between legs must be stated in writing before the test runs.
- **"Nothing happens"** (the NO arm of dramatic "will X happen by date" markets) is allowed as a politics family, distinct from the declined favourite-late gold hold (different market, different data). Paper first.
- **Terms rule and host gates** are unchanged: only sources whose terms allow automated reads; new hosts go through the allowlist and its gate.
- **PF 1.5 bar, counted deflation, the uniqueness test and the declined list** are unchanged.

## 2. Limits a live probe must stay inside

These are caps, not permission. A probe starts only after the owner approves its exact spec.

| Item | Rule |
|---|---|
| Single politics probe size | 3 contracts |
| Early live parlay probe size | $2 per parlay |
| Parlay probes stop automatically at | $40 total loss |
| Paper edge before an early live parlay probe | 10c per dollar after fees (the spec must define exactly what is measured and over how many settled trades) |
| Exit | hold to settlement |
| Open positions at once | up to 10 politics or parlay positions |
| Side | either side, whichever the test supports |
| Entry price | 10c to 90c |
| Hold | 14 days at most to settlement |

## 3. Kill and return

- **Kill (single politics probe):** net under -$15 after 20 fills, or 5 losses in a row. The probe stops and stays stopped.
- **Kill (parlay probes):** $40 total loss.
- **Return after a kill:** a 14 day cool-off, then a shadow PF of 1.3 or better, then the owner approves. Nothing resumes on a date alone.
- **Scheduled events:** trading around a scheduled event is allowed only if the strategy was built and tested for that window.

## 4. Further rules (owner popups 17 to 28, Nov 11, 2026)

- **Weather combos:** same city, linked days or brackets first.
- **Mention combos:** words in the same speech or call first.
- **Sports combos:** price consistency only, against Kalshi's own single markets. No outside sports data.
- **Conflicts:** the first strategy in holds the market; the other skips it.
- **Poll sources:** only those whose terms were read and allow it. Today that is the Wikipedia polling tables via its API.
- **Attention signals (Wikipedia pageviews, GDELT):** test both directions, pre-registered.
- **Trump approval and generic ballot:** run the calibration test on both now (the fastest real politics verdict).
- **Foreign politics:** only markets settling within 14 days.
- **Activity counts (executive orders, bills signed):** base rates plus the count so far this week, via GovInfo.
- **Mention base rates:** Kalshi's own settled mention history.
- **Resolution-rule edge cases:** flagged to the owner with the rule text, never automatic.
- **News fade:** pre-register three delays (15 minutes, 1 hour, 4 hours), all counted in the deflation.

## 6. What is not decided

- No code places any politics or parlay order, and the second slot registry (`functions/kalshiSlotLib.js`) holds none. Admitting one is a separate reviewed pull request and the owner's own popup.
- The exact meaning of "10c per dollar after fees" is left to each probe spec to define and the owner to approve.
- How a parlay would be placed if Kalshi offers no politics combo market is undecided; today it would be a simulation only.

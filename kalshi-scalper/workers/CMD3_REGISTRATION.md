# CMD3 registration: futures roll windows (2026-11-06, before any score)

Shared rules: `workers/CMD_COMMON.md`. 1 try (N +1).

**Mechanism.** Yahoo's GC=F, SI=F, HG=F, CL=F, ES=F and NQ=F are continuous front-month series, so a roll shows as a one minute gap that is not a price move. If the perp is built on the same contract it either jumps with it (basis unchanged) or does not (the basis jumps by the roll spread and the perp is the cheap or rich side until it re-bases). Counterparty: a perp holder across the contract change.

**Event.** Flagged minute as defined in the shared file (futures |change| at least 30 bp, perp under 20 percent of it) with the futures session otherwise open, one event per pair per CME session. **Rule R:** after an event at T, d (basis deviation measured against the pre-event 60 minute median) at T+5; if |d| at least 15 bp the perp is expected to converge to the futures: trade the perp toward the futures at the T+5 quote, exit T+35 minutes. Prediction (artefact reading): the perp does not follow, the basis stays at the gap, and the trade loses cost plus the gap; net below -24 bp.

**Calendar.** Known expiries: CLZ6 last trade 2026-11-20, then roughly monthly; GC, SI, HG, PL roll before the late-November first notice dates; ES and NQ Dec 18 2026. None inside development (2026-10-30 to 11-03), so zero events in development is the expected outcome (checked by the flag count, which is the only thing computed).
**Verdict bar:** 30 independent events on 15 dates. Roughly 8 events a quarter across the six pairs: about **2027-09 to 2027-10**; a CL-only read (one roll a month) with 6 events is **2027-04-20**. NOT_ENOUGH_DATA until then.

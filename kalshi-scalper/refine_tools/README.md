HISTORY (Nov 13, 2026, owner ruling): this note predates the privacy scrub; lines marked "[live figure removed, ask Main]" are blank on purpose. Read it as history, not as a current rule.

# Refinement tools (read only)

Copied from the refinement session scratchpad on Nov 9, 2026 so a fresh session can rebuild. They only read the nightly order report JSON (fetched with the report token by a local dash script that is NOT in the repo); they place no order and call no Kalshi endpoint except the public market GETs in the trackers that score against settlements.

[live figure removed, ask Main]
- halfsize_fwd.py  S-HALFSIZE1 (OICORE fills priced under 0.10, read at 40)
- [live figure removed, ask Main]
- oibands_fwd.py   S-OIBANDS1 (start 2026-11-08T12:44Z; groups <=0.07 at 40, >0.20 at 20)
- [live figure removed, ask Main]
- oicheapskip.py   S-OICHEAPSKIP1 (reads the deploy time 2026-11-08T18:57:10Z from a DEPLOY_TS file next to it; read at 40 skipped signals)
- stop_headroom.py replay of the shared 12 percent stop (prints UTC times labelled CT; set the base by hand)
- [live figure removed, ask Main]
- logentry.py      appends a stamped entry to REFINE_STATUS.md (does not commit)
REGISTRATION_*.md are the registrations written before each tracker ran. [live figure removed, ask Main]

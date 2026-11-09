# Refinement tools (read only)

Copied from the refinement session scratchpad on Nov 9, 2026 so a fresh session can rebuild. They only read the nightly order report JSON (fetched with the report token by a local dash script that is NOT in the repo); they place no order and call no Kalshi endpoint except the public market GETs in the trackers that score against settlements.

Run each as `python3 -I <script> <report.json> [start timestamp]`:
- halfsize_fwd.py  S-HALFSIZE1 (OICORE fills priced under 0.10, read at 40)
- hvs_fwd.py       S-HOLDVSSELL (start 2026-11-07T20:24Z; read at 30 new gold early sells)
- oibands_fwd.py   S-OIBANDS1 (start 2026-11-08T12:44Z; groups <=0.07 at 40, >0.20 at 20)
- esfeat_fwd.py    S-ESFEAT1 (start 2026-11-08T12:44Z; gold early-sell leads, read at 20 early sells)
- oicheapskip.py   S-OICHEAPSKIP1 (reads the deploy time 2026-11-08T18:57:10Z from a DEPLOY_TS file next to it; read at 40 skipped signals)
- stop_headroom.py replay of the shared 12 percent stop (prints UTC times labelled CT; use base 979.25)
- lim_review.py    S-LIM1-LIVE review (NO avgFill flipped; see retraction 16)
- logentry.py      appends a stamped entry to REFINE_STATUS.md (does not commit)
REGISTRATION_*.md are the registrations written before each tracker ran. Rules: flip avgFill for NO orders (paid = 1 - avgFill); say limit-booked vs cash-booked (PR 741, cash after 2026-11-07T21:42Z).

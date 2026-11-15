# UNDERDOG2X development read (thirds 1 and 2), run once 2026-11-15 16:03:20Z to 16:03:26Z, on Auditor B's CLEAN (16:03Z)

- Code: underdog2x.py bad4514f (commit c439dd45). Auditor B's CLEAN named 2c766ba6. The only change since is Amendment 2's SOL cut, which Auditor B confirmed does not touch the development read (SOL's thirds 1 and 2 end Sep 17; third 3 is dropped in the first pass). Supplement a_fallthrough.py 9e6ede79 (Auditor B's requested count; it changes no figure). Exit 0 for both.
- Data: the research-data archive (Oct 29, WHOLE sha256 15788a025e39d4872515a88bcad2eb4666936632b863bd88c6eecc43b2efe227), the .sqlite files l1b, book, e3b, alts4, alts2, alts3, rep, unpacked in scratch. Only thirds 1 and 2 were read beyond ticker and close (per load()'s two passes).
- Guard list HELDOUT_PULL_RUNS.md c561184a (equal to main). Touched: the archive in scratch and this repo's code.
- Prints, committed before reading them:
  - UNDERDOG2X_DEV.json, sha256 cf0f2774a347575ca7eb24da2963803637bbe7b05c45c3bd4dfe32f7595be14e
  - UNDERDOG2X_DEV_a_fallthrough.json, sha256 8762ee03f78a1e317ec9cf1b314d855533460efbfdff776e1885eb5edaf3b8d7
- Read with the prints: a development read only (third 3 unread); upper bound, not fill-checked; per-order rounded fee (1 contract for a and b, a 2-lot for c). A pass needs the Testing Desk's second build before 16b, and the held-out is read once in one pass on the Head's go.

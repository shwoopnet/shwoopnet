# Shadow scaling (Nov 13, 2026, phase P2 of the scalability plan)

Log only. Nothing here places an order, reads a key or changes a rule; `SHADOW_RULES` still holds exactly one rule (GOLDOFF), and with one rule the deployed minute function makes the same reads and writes it made before.

What changed, so that many shadow rules cost about the same as a few:

1. **Shared reads.** A candle read (for an open interest rule) is made once per market window and serves every rule that needs it, in the same minute and in later minutes of that window (a successful answer is kept in memory; a missing candle is never kept, so it is tried again). A second look at a row is one read per market, not one per rule. The whole tick still draws from the one hard budget of 3 public reads a minute (`SHADOW_READS_PER_MINUTE`).
2. **Per market settling.** The settle sweep (every fifth minute) reads each market once and settles every row of it. The per sweep read limit now counts markets, taken oldest close first so none starves.
3. **A reviewed list of allowed shadow markets.** `SHADOW_ALLOWED_SERIES` replaces "whatever L1 trades". Today it equals the L1 list, so nothing changes. Adding a market is a reviewed edit; if L1 does not read it, the minute function reads it under the shared budget even with a session on.
4. **The lane's second look.** The rotation lane asks for a second look at the same market a few seconds after the decision. That already exists behind the rule field `secondRead` (it writes `askAfter` and `wouldFillAfter`, about 4 seconds later, one read a row). Nothing was added to the single rule case, because any new field would need a new read. The one change is that the look is shared per market. Follow up, not built: the lane's slower log variant (the next poll within 6 seconds) belongs to the recorders, not here.

Tests: `test/shadowScalingGates.test.js` SC1 to SC8.

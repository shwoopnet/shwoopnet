# In-game event_rule specs on the PR 960 cadence (History Miner, registered Nov 16, 2026 ~16:30Z, before any row from Nov 17 exists)

The Head (Nov 16 15:44Z): 3 to 4 in-game event_rule specs, registered and frozen now, run automatically once 3 days of the new cadence have landed (about Nov 19). Forward only, first close 2026-11-17T00:00Z (PR 960 merged 15:27Z Nov 16). Each spec is one try. No lead-lag; no trade tape. Primary haircut 2c (PF 1.3 line) with 1c (the second line is printed). Contracts 10.
Data: the forward version of ingame_load.py (same walls as the CLEAN 6ac835f4, window from Nov 17, results from a forward listing of the ticker wall), plus one scorer plugin, ingame_events.py, written with a hand case and audited once before the first run. Neither exists yet: both are needs_new_code.
SPORTS-PRE holds KXNBAGAME and KXNFLGAME outcomes to 2027-01-01, so NBA and NFL moneylines are in no wall.

- IGFADE2 (version of IGFADE1, which was NOT RUNNABLE at the old cadence): two consecutive polls of one ticker no more than 60 s apart, both two-sided, mid moved 10c or more: buy the side that fell at 15c to 60c, one per game and kind, hold. Counterparty: takers chasing a score. Prediction 2c PF >= 1.3. Kill: under 1.0 on the first read.
- IGLATEDRIFT1: at tip + 120 min, if the market's mid moved 8c or more since tip + 90 min, buy the side it moved toward at 20c to 80c, hold. Counterparty: slow late-game repricing. Prediction 2c PF >= 1.3. Kill: under 1.0 on the first read.
- IGDOG1: at tip + 75 min, buy the NHL moneyline underdog priced 15c to 35c, hold. The Head asked for "the favourite at a fixed game-clock point"; favourite-and-hold is on the declined list (7e), so the underdog side is registered and the change is flagged to the Head. Counterparty: fans of the leader overpricing it. Prediction 2c PF >= 1.3 (NHL only, n 100 needs about 7 weeks). Kill: under 1.0 on the first read.
Tip = occurrence_datetime minus 3 h, a schedule-shaped proxy, truth unproven; the PREDRIFT1 schedule test applies (NFL weaker). A game whose tip proxy fails that test is dropped and counted.

## Amendment 1 (2026-11-16 ~16:50Z, Auditor B 16:20Z, before any forward row)
KXNFLSPREAD removed from IGFADE2's wall, the loader and the listing job (BOOKS2 W3 holds it until the Head closes BOOKS2). The specs now carry Desk A's signing fields (c04cdbd89): holds as epochs, look_ahead, sources, plugin hashes, subset_rationale, halves, fee_form, n_floor; spec_check passes, 1 rule each. Loader ingame_fwd_load.py c7f90926, plugin ingame_events.py 5f5d739a, hand case 25bcc5ff.

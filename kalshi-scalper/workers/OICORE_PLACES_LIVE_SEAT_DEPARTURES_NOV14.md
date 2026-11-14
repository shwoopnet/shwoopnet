# OICORE places: LIVE seat departures (HYPE and BNB), dated 2026-11-14

Separate note, NOT part of `DESK_A_FROZEN_OICORE_PLACES_DEFINITIONS_NOV13.md` (v5), so the sheet's version rule does not apply and no shadow place's start time or forward record is reset. Added at the Head's instruction (07:14Z and 07:17Z). The v5 shadow definitions are unchanged; this adds nothing to the shadow rules.

The LIVE activity seats on OICORE-HYPE and OICORE-BNB depart from v5 on four points:
1. **T is fixed**, computed once by v5's rule (L9) on the 20 trading days to 2026-11-12: HYPE 6796.75, BNB 4351.84 (two builds equal, a8aa5fed and b32bb999). A refresh is only a reviewed edit.
2. **Entry span** is OICORE's live 180 to 120 s before the close.
3. **Size** is 3 contracts under the activity terms and the slot kill rules.
4. **They skip EVENT830's listed 13:30Z windows.**

Reason: a data-only seat on the live engine.

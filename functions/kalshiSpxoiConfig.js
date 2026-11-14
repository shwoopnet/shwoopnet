"use strict";
// SPXOI1 trial seat: the ONE number that is not known yet (Nov 13, 2026).
//
// SET Nov 14, 2026 to 5463.9 (two builds equal, n = 140, Desk A print SPXOI1_T_BUILD1_PRINT_NOV14, Testing c52d7f6d).
// SPXOI1_T is the open interest rise (contracts, the candle ending 180 s before the close minus the candle ending 360 s before it) a KXINX15M window must show before the seat may buy.
// It is the 90th percentile of that rise over the KXINX15M windows of Nov 5 to Nov 13, 2026, computed from the candles the manual data pull jobs SPXOI1_LISTS and SPXOI1_CANDLES fetch.
// Nobody may guess it. It is null until that computation exists and Auditor B has checked it; the seat is NOT in the registry while it is null (the slot library), so a null here places nothing.
// Setting it is a one-line reviewed edit of this file, together with the page and registry rows listed in CLAUDE.md "SPXOI1 trial seat (Nov 13, 2026)" (gate SX9 fails if the page is left behind).
// Pure data: no network, no clock, no Firestore, nothing else imported.
// HYPEOI1_T and BNBOI1_T (Nov 14, 2026, activity seats 2 and 3): the 90th percentile of the open interest rise over 1,587 windows of KXHYPE15M and KXBNB15M, 20 trading days 2026-10-21 to 2026-11-12, EVENT830's listed 13:30Z closes cut;
// two independent builds matched exactly (the Head of R&D, Nov 14, 2026). Frozen: never from stored data or the page.
module.exports = Object.freeze({ SPXOI1_T: 5463.9, HYPEOI1_T: 6796.75, BNBOI1_T: 4351.84 });

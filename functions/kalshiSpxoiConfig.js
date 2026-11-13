"use strict";
// SPXOI1 trial seat: the ONE number that is not known yet (Nov 13, 2026).
//
// SPXOI1_T is the open interest rise (contracts, the candle ending 180 s before the close minus the candle ending 360 s before it) a KXINX15M window must show before the seat may buy.
// It is the 90th percentile of that rise over the KXINX15M windows of Nov 5 to Nov 13, 2026, computed from the candles the manual data pull jobs SPXOI1_LISTS and SPXOI1_CANDLES fetch.
// Nobody may guess it. It is null until that computation exists and Auditor B has checked it; the seat is NOT in the registry while it is null (the slot library), so a null here places nothing.
// Setting it is a one-line reviewed edit of this file, together with the page and registry rows listed in CLAUDE.md "SPXOI1 trial seat (Nov 13, 2026)" (gate SX9 fails if the page is left behind).
// Pure data: no network, no clock, no Firestore, nothing else imported.
module.exports = Object.freeze({ SPXOI1_T: null });

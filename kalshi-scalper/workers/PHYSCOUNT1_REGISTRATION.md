# PHYSCOUNT1 registration (2026-11-05): physical-event and count-by-date markets resolved from a public catalog (census first)

Registered before any price, candle or outcome was read. The census prints listing counts only (series, event, close time, volume), events closing before the frozen cut 2026-10-03T16:00Z.

**Ledger check.** EQUAKE1 (earthquakes, NOT_ENOUGH_DATA), WXOTHER1 (storms, hurricanes, space weather 1 to 12 events, air quality, tornadoes), COUNT2 (tornadoes) already cover those. No SpaceX, launch, asteroid or Rocket Lab entry exists in the ledger (grep for launch, spacex, starship, asteroid, flare found none). Full public series list (all categories) searched by title for launch, rocket, Starship, SpaceX, flare, solar, geomagnetic, volcano, wildfire, asteroid, meteor, satellite, NASA, tsunami, aurora, eclipse.

**Candidate series:** KXSPACEXCOUNT, KXSPACEX, KXRKLBCOUNT, KXSPACEXREUSE, KXASTEROID, KXSPACEXLAND, KXSTARSHIPDOCK, KXSTARSHIP25, KXRKLBORBIT, KXHURCAT, KXHURCTOTMAJ.

**Counterparty.** Retail takers who price a count-by-date strike without the launch manifest or the partial count so far. **Outside fact.** The catalog's own partial count at the look (launches so far in the window against the strike), not a model fit to the quote.

**Rule if runnable (not run).** Look 24 h before close; cheap side only (ask 3c to 30c), held to settlement, fee 7% x C x p x (1-p) rounded up, C = 10, taker at the ask; buy only when the partial count makes the strike reachable at a rate at least 3 x the ask; at most 2 per event; control = every cheap strike. Halves D1/D2, event clustering. No favourite-side result computed.

**Gate.** A series is scored only with at least 100 settled events before the cut. **Prediction:** every series fails the gate (NOT_ENOUGH_DATA), about 90%. **Kill if scored:** mean net not above 0 in both halves, PF under 1.5, or z under 5.27 is FALSIFIED. N +1 (census), running count about 730,447, z bar about 5.27. Nothing fetched beyond listings.

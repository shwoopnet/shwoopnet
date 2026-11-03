# EARN1: Kalshi company metric / earnings-style markets, cheap side vs consensus surprise (2026-11-03)

Status: `NOT_RUNNABLE` (census failed before any scoring). Registered first; no outcome joined, no candle fetched, no price looked at.

**Duplicate check.** Earnings-CALL WORD markets (KXEARNINGSMENTION*) were tested as MENT1 (FALSIFIED, rerun PF 0.86) and NEWS1 was withdrawn. No earlier worker tested EPS/revenue/company-metric markets against consensus (grep earnings, EARN, EVENT1, CALIB1, FEDIMPL1: only STRADDLE1, which is options, and MENT1). So not a duplicate; the census decides.

**Rule as it would have run.** Series: company metric series on the public series list (TESLA deliveries, NETFLIXSUBS, SPOTIFYSUBS, FBDAU, METADAP, CBVOLUME, SOFIMEMBERS, the "Annual KPI" series KXTSLAA, KXMETAA, KXSBUXA and the other KX..A series). Reference: consensus/guidance (EDGAR 8-K, company releases), published before the look. Look: 24 h before the release. Surprise (actual minus consensus, scaled) distribution from the first two thirds of events only; model probability per far bracket; buy the CHEAP side only (ask 3c to 30c, model probability at least 3x the ask), hold to settlement, max 2 per event, event-clustered. Frozen cut 2026-10-03T16:00Z (last third never fetched). Prediction: PF about 0.9, FALSIFIED about 80% if it could run. Kill: FALSIFIED if mean net after fees not above 0 in both halves or PF under 1.5; NOT_ENOUGH_DATA under 150 trades with months to go. Bar: at least 25 events and 150 scoreable markets before the cut.

**Census (public series list and market list, status only, no prices).** 216 Companies series, mostly non-numeric one-offs (CEO changes, launches). The numeric ones:
- TESLA, NETFLIXSUBS, SPOTIFYSUBS, FBDAU, METADAP, CBVOLUME, SOFIMEMBERS, TESLAPROD: 0 markets, live or historical (retired series).
- Annual KPI series (KXTSLAA, KXMETAA, KXUBERA, KXSPOTA and 20 more): 0 settled; their markets are active with close dates in 2027 to 2028 (3 events each).
- KXSBUXA: 14 settled markets, 2 events, all closing after the frozen cut.
Settled events before the cut with a numeric company reference: **0** (bar 25), scoreable markets **0** (bar 150). Consensus for what exists also has no free keyless historical source.

**Verdict: `NOT_RUNNABLE`.** Nothing scored; no PF; no try counted beyond the registration. **Forward plan:** the KPI series settle from 2027 (annual, 3 events per company at most), so re-census on 2027-04-30 for settled count; run only if at least 25 settled events with an EDGAR-obtainable reference, otherwise stay closed. The earnings-call word family is already MENT1.

N: +2 (one rule registered, never scored).

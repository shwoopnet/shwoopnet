# MMSIM1 build 2 on DEVELOPMENT events (Idea Desk B, 20:02Z). Script mmsim_build2.py sha256 3671bc82. Data: quote-data folders 2026-10-29 to 2026-11-07 (159 files), read directly; events closing at or after 2026-11-07T15:00:00Z dropped at load (10 events, counted, never simulated); no folder after Nov 8 opened. Counts and PFs on development only; defaults were NOT chosen to match anything.
## Defaults (G1 to G9 as in BUILD2_SPEC_AND_GAPS.md)
Development events 171, quotable 168, strikes in the books 1,197, strikes with an order 1,176, orders 2,289.
**Rule Q:** fills 797 (34.8% of orders), pairs 175, singles 447. 1 contract, fee unrounded: PF **1.42** at maker 0 (net +8.90, mean +5.30c an event, 8 of 10 days positive) and **1.30** at the 0.0175 bound (+6.61). Fee rounded per leg: PF 1.27 and **0.93**.
**Rule P:** fills 2,027 (88.6% of orders; 608 from trades, 1,419 from the book condition), pairs 908, singles 211. PF **0.18** at maker 0 (mean -17.6c an event, 1 of 10 days positive), **0.07** at the bound. Rounded: 0.18 and 0.00.
## Does each gap move a Rule Q number? (each alternative alone, everything else default)
| Gap | Alternative | Rule Q fills / pairs / singles | Rule Q PF maker 0 / bound | Rule P PF maker 0 |
|---|---|---|---|---|
| default | | 797 / 175 / 447 | 1.42 / 1.30 | 0.18 |
| G1 strike set | only strikes of the event's first poll | no change | no change | no change |
| G2 clock | local poll ms instead of the Date header | 793 / 174 / 445 | 1.42 / 1.30 | about 0.18 |
| G3 no bid at the first poll | post at the next poll with a bid | 800 / 175 / 450 (orders 2,294) | 1.43 / 1.31 | about 0.18 |
| G4 same second | inclusive | no change | no change | no change |
| G5 fill time | the trade's own poll instead of created_time | 856 / 190 / 476 | **1.34 / 1.23** | about 0.18 |
| G6 sale poll | last poll before T-15 instead of first at or after | 797 / 175 / 447 | 1.40 / 1.28 | about 0.18 |
| G7 no bid at the sale poll | latest earlier best bid instead of 0 | same counts | 1.44 / 1.31 | 0.20 |
| G8 (Rule P "absent") | not tested: the recorder drops empty books, so "absent" only exists as an empty level 1 on a kept row | n/a | n/a | not run |
| G9 rounding | per leg is the default; rounding a pair as one fee was not run | n/a | rounded rows reported above | n/a |
G7 detail: at the T-15 poll 35 of 447 Rule Q singles and **126 of 211 Rule P singles** had no bid on the filled side, so the default sale price 0 matters most for Rule P; the latest earlier bid is a cent or so, so the PF moves little. G5 is the gap that moves Rule Q most.
## Counts compared with the registered text (information only; not matched)
The protocol reports 168 quotable events, 1,113 strikes, 400 and 391 fills (791), 174 pairs, 443 singles, PF 1.41 and 1.28; Amendment 3 reports Rule P quotes filled 85% to 91%, PF at maker 0 between 0.16 and 0.29, mean about -18c an event, 1 positive day of 10. Build 2 under the defaults gives 168, 1,176 strikes with an order (1,197 in the books), 797 fills (the YES and NO split is not printed), 175 pairs, 447 singles, PF 1.42 and 1.30; Rule P 88.6%, 0.18, -17.6c, 1 of 10 days. I cannot tell from the text why the strike count differs by 63.
G10 (10 contracts) left out as ordered.

# MMSIM1 build 2 under Amendment 4, development events only (Idea Desk B, 20:07Z). Frozen script mmsim_build2.py sha256 83cdc79a61d7e6e7. Fixture v2 generator make_fixture_v2.py; hand case EXPECTED_hand_build2_am4.md committed before the code change, every figure matched (OUTPUT_hand_build2_am4.txt).
Data: quote-data folders 2026-10-29 to 2026-11-07 (159 files); events closing at or after 2026-11-07T15:00:00Z dropped at load (10, counted, never simulated); no folder after Nov 8 opened.
Development events 171, strikes in the books 1,197.
| | Rule Q | Rule P |
|---|---|---|
| events with an order | 171 | 171 |
| strikes with an order / orders | 1,123 / 2,246 | 1,123 / 2,246 |
| fills (yes / no) | 791 (400 / 391) | 2,020 (988 / 1,032) |
| trade fills (fractional filling trades) / book fills | 791 (380) / 0 | 679 (348) / 1,341 |
| pairs / singles | 174 / 443 | 907 / 206 |
| PF unrounded, maker 0 / bound | 1.41 / 1.28 | 0.18 / 0.07 |
| net unrounded, maker 0 / bound | +8.513293 / +6.238708 | -29.464062 / -34.925191 |
| PF rounded per order, maker 0 / bound | 1.26 / 0.92 | 0.18 / 0.00 |
| positive days of 10 (maker 0) | 8 | 1 |
Item 7 (sales at 0 for a blank or zero bid): Rule Q 33, Rule P 124. **Item 8 (blank and zero cells examined by the Rule P book condition, until each order's first qualifying row): blank 35, zero 0.**
Mean per event over the events with an order (171): Rule Q +4.98c (maker 0), Rule P -17.2c. **Over 168 events the means are +5.07c and +3.71c at the bound for Rule Q and -17.5c for Rule P, which is what the registered text reports.**
## One difference from the registered text (item 10, "quotable")
Counts that match the text exactly: Rule Q fills 791 (400 and 391), pairs 174, singles 443, PF 1.41 and 1.28. The text also says 168 quotable events and 1,113 strikes; under item 10 ("at least one posted order") build 2 has 171 events and 1,123 strikes. The three missing events (2026-10-31T03:00Z, 2026-10-31T10:00Z, 2026-11-02T21:00Z; 10 strikes with an order) are exactly the events in which NO order fills even under Rule P (13 events have no fill under Rule Q). So the original's "quotable" appears to exclude events where nothing can fill; the text's means per event divide by 168. I did not tune to this: it is an observation for an amendment of item 10 (the figure that matters for PF is unaffected, since those events add 0).

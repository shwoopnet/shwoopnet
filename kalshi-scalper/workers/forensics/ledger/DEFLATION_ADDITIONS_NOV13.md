# Deflation ledger: tries to add for Nov 13, 2026, with a hash for each (Forensics desk, for the Head of R&D to commit to `DEFLATION_LEDGER.md` on `rnd-queue`)

Ordered by the Head of R&D at 19:50Z. Each row was checked against its card file. Hashes are the first 8 hex digits of the sha256 of the card file at the named commit (checked here; they match the ids in the Head's list). Research counts on public data only; no live account figure. [research]

## Rows (format of the "Tries added since the compiled table" section)

| Test | Desk | N | State |
|---|---|---|---|
| SPXFV1 (KXINX15M, S&P 500 futures-implied fair value, cheap side; a port of CFRTI-K) | Desk A | 1 | REGISTERED Nov 13 before any read; card `DESK_A_SPX_CARDS_NOV13.md` at 5ed61f6b (sha256 35f590c0), dated lines D1 to D8 at 94c4dfbc (sha256 bb7e1e4a); CLOSED UNREAD Nov 13 (family declined under the 3-falsified rule); 0 scored. The card states no N of its own; its toolkit variants (resting limit, target, stop, time exit) are tries "only if used" and none was used, so 1. |
| SPXOI1 (OICORE's rule on KXINX15M; research threshold and wheel threshold) | Desk A | 2 | REGISTERED Nov 13 in the same card (D6: "TWO counted tries ... research threshold: the pre-2026-12-01 90th percentile; wheel threshold: the rolling previous 20 trading days"); same file hashes as above (35f590c0, bb7e1e4a); a VERSION of OICORE (7g), no research slot. |
| SPXEVENT1 (EVENT830's rule on KXINX15M; two frozen windows) | Desk A | 1 | REGISTERED Nov 13, `DESK_A_SPXEVENT1_NOV13.md` at 2d426ec8 (sha256 88f7e93c); "N +1 per registered parameter set; this card has one set"; a VERSION of EVENT830, wheel spec only; paused. |
| WITHDRAW1 (book levels 2 to 5 withdrawing with no print) | Desk B | 1 | REGISTERED Nov 13 before any read, `bookfield/BOOKFIELD_CARDS_NOV13.md` at 50b2d209 (sha256 115ff02e); CLOSED AT INTAKE as not unique (dated line at 14d9fac0, sha256 7ed7ac1a: DEPTH1 f6 and a second try of BOOKCH1); counts as a try for the book-shape family; no scorer, no read. |
| AIRGAP1 (a hole between the favourite's best and second bids) | Desk B | 1 | Same file and hashes as WITHDRAW1 (115ff02e, 7ed7ac1a); closed at intake (DEPTH1 f8 and f9); counts as a try; no scorer, no read. |
| SPOTFLOW1 (pooled spot trade flow against a Kalshi quote that has not moved) | Desk B | 1 | REGISTERED Nov 13, `bookfield/SPOTFLOW_CARD_NOV13.md` at a40ac58f (sha256 3d3c830c); CLOSED AT INTAKE (dated line at a00339e5, sha256 dbd6dea0): inside the declined outside-reference family, dates cross CFRTI1-BTC and CFRTI-B; "counts as a try"; no read. |
| LIQREV, also named OKXLIQ1 (OKX liquidation reversal on KXBTC15M; forward only, paper and shadow) | Idea Desk C | 1 | REGISTERED Nov 13, `idea_desk_c/LIQREV_CARD.md` at 822f9ce1 (sha256 04c6680a); Amendment 2 at a16c8e3c (sha256 507a7326): family status, held-out to Dec 31; "OKXLIQ1 and LIQREV are one card, one try"; paused as written, later unpaused; no read. |
| OIVER-SPREAD (OICORE plus a spread skip of over 3c) | Desk A | 1 | WRITTEN Nov 13, `DESK_A_OICORE_VERSIONS_NOV13.md` at 741092a7 (sha256 e7b918b0); "N +1 per version"; a 7g VERSION of OICORE; not scored. |
| OIVER-CAP30 (OICORE plus a cap at 30c) | Desk A | 1 | Same file and hash (741092a7, e7b918b0); written, not scored. |
| OIVER-DEPTH (OICORE plus a touch-depth floor of twice the order size) | Desk A | 1 | Same file and hash (741092a7, e7b918b0); written, not scored; a forward shadow is the real test. |
| CFRTI-K three-label amendment (the held-out read prints PASS, FAIL and NO CALL; the EA's relay) | Desk A | 0 | Dated lines of Nov 13 (17:04Z and the EA's relay) in `CFRTI_K_REGISTRATION.md`; labels only, no new rule or cell scored. |

Total added today: 1 + 2 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 = **11**.

## Recomputed strict N and bar

One-sided normal quantile at 1 minus 0.05 / N (the ledger's convention; two-sided in brackets):

| N | One-sided z | Two-sided z | Which |
|---|---|---|---|
| 2,113,000 | 5.4611 | 5.5828 | the ruling of Nov 12 |
| 2,113,011 | 5.4611 | 5.5828 | plus today's 11 (a floor: it assumes every row added since the ruling was already in the 2,113,000) |
| 2,113,449 | 5.4611 | 5.5829 | plus today's 11 and all 438 explicit tries in the ledger's "added since" table (a ceiling: it assumes none of them was in the 2,113,000; PERPBIN1 and CFRTI-K each appear twice in that table and are counted once) |

**The bar does NOT move off 5.46.** Rounded to two decimals the one-sided bar stays 5.46 until N passes about 2,161,000, which is 48,000 more tries than the ruling's figure; today adds 11. Two-sided stays 5.58.

## What this check did and did not do

- Each card file was opened at its commit (text only, no data) and its own statement of tries read: SPXOI1 (D6, two), SPXEVENT1 (one set), LIQREV (one card, one try), the OICORE versions (N +1 each), WITHDRAW1, AIRGAP1 and SPOTFLOW1 ("count as tries"). The SPXFV1 card gives no N of its own, so its 1 is the Head's count under the rule "a scored or registered rule is one try"; if the toolkit variants (resting limit, target, stop, time exit) are ever used, each adds one.
- It did not re-derive the 2,113,000 (the Verification Analyst matched it on Nov 12) or the rows already in the ledger since. Whether the 12,600 hand-registered cells include Refinement's 409 itemised cells of Nov 11 to 12 is unresolved in the ledger; that choice moves N by at most 409 and the bar by under 0.0001.
- SPXFV1's builder and Databento cost query (Forensics) scored nothing and add 0.

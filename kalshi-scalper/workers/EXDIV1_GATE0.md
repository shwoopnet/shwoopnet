# EXDIV1 gate 0 (docs only, no data, zero Kalshi API calls), 2026-11-12

Protocol: P1 in IDEA_DESK_A_PROTOCOLS.md (branch claude/idea-desk-a).

## Verdict: CLOSED, 0 tries

Question (a) is answered by the page: dividends are passed through as a cash adjustment. The claim "the perp is not adjusted for the dividend" is false by Kalshi's own help text. Gate 1 is not run.

## (a) Corporate actions and dividends: PASSED THROUGH
Page: https://help.kalshi.com/en/articles/18183683-single-stock-perpetual-futures-on-kalshi
- "When a company takes an action that affects its stock, Kalshi adjusts stock perp positions to match."
- "When a company pays a dividend, long positions receive cash and short positions pay it."
- "Cash is added to long positions and deducted from short positions." / "The notice lists the amount per contract."
- "Kalshi publishes a notice for each corporate action with the details."
So a short pays the dividend; the short-before-ex trade earns about zero before costs.

## (b) reference_price definition: NOT ANSWERED by the pages read
The help page has no reference or index price definition (closest: Underlying row, "The price of an individual company's stock in USD."). The two CFTC fee-rebate filings do not define it either. Not needed once (a) closes the card.

## (c) Launch fee waiver on perps: NO waiver; a rebate program exists (separate cost input)
Pages: https://www.cftc.gov/filings/orgrules/rules0625267305.pdf and https://www.cftc.gov/filings/orgrules/rules09022622952.pdf (Temporary Perpetual Fee Rebate Program, and its Sept 2 2026 update, effective no earlier than Sept 16 2026, until the earlier of Dec 31 2026 or termination).
- Rebates go to "Self-Clearing Members" (not retail), "monthly rebate adjustments".
- The Sept update narrows "Eligible Markets" to perps referencing "cryptocurrencies and metals". Equity perps are not listed there. (The July filing said "all Perps markets".)
- Help page fee section mentions no rebate or waiver.
Effect for this project: no fee holiday should be assumed on equity perps.

## Other facts from the help page (not asked)
- "Funding is calculated once a day at 4:00 PM ET."
- "Trading can pause around a corporate action."

## URLs read
1. https://help.kalshi.com/en/articles/18183683-single-stock-perpetual-futures-on-kalshi
2. https://www.cftc.gov/filings/orgrules/rules0625267305.pdf
3. https://www.cftc.gov/filings/orgrules/rules09022622952.pdf
Failed: https://help.kalshi.com/en/articles/perpetual-futures (404, not retried). A web search was also run to locate pages. Page text came through a summarising fetch tool for page 1; the PDFs were read locally with pdftotext.

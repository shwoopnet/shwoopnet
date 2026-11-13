# SETTLEMENT-WINDOW card check, Idea Desk A, Nov 13, 2026 (the Head's order, 21:18Z; the owner: "find new strategies"). Written only; no data read, no Kalshi call.
**Verdict: NOT NEW. It is a version of CFRTI-K where it can be entered, and favourite class (banned) or unreachable for the bot everywhere else. Not registered.**

## 1. Settlement sources and window lengths (PUBLIC PAGES ONLY, second hand: Kalshi's own rulebook pages were not fetched by this desk; the figures below come from third-party write-ups returned by search and one Kalshi contract-terms PDF template. Each line is a claim to re-read on the live rulebook before anything rests on it.)
| Ladder | Settles on | Averaging window? |
|---|---|---|
| KXBTCD / KXETHD (hourly and daily Bitcoin and Ethereum) | CF Benchmarks real-time index, the 60 second average before expiry, one reading a second | YES, 60 s |
| KXBTC15M / KXETH15M | the 60 s average at the close against the 60 s average at the open (third-party reading; a strike-free up or down market) | YES, 60 s at each end |
| S&P daily (INX) | the official close from S&P Global (the INX terms PDF is a blank template, no averaging term in the excerpt) | NO |
| KXINX15M | the API names no source (a placeholder string); the most recent published value if none (third-party) | not stated |
| Gold and silver daily (KXGOLDD) | a 1 minute candle CLOSE at 5:00 PM ET (third party; one site says a 60 s average, the sources conflict) | a candle close is not an average; unresolved |
| Gold 15 minute | a candle close; one source says Pyth | not an average |
| WTI daily | the front-month futures settlement | NO |
So the averaging window is a CRYPTO feature of 60 seconds. The "S&P ladders" and "gold on a fix" in the card are not supported by what I could read (an official close and a candle close).

## 2. Is it CFRTI-K's model edge restated?
CFRTI-K (`CFRTI_K_REGISTRATION.md`): at close minus 120 s, a model chance of YES from an index (the Bitcoin perpetual's reference price) against the strike with a short-horizon volatility, buy the cheap side (5c to 30c) when model chance minus ask is 0.05 or more. A "narrowed fair probability inside the averaging window" is the SAME mechanism: a fair-value probability from an index against the strike, bought when it is above the ask. The only new term is that part of the 60 s average is already fixed once the window has opened (inside the last 60 s). That changes the variance input (a shorter, partly known horizon), not the entry mechanism. **Result: a version of CFRTI-K (7g: same logic, a parameter and timing change), not unique, takes no slot, counts a try.** If it is entered BEFORE the window opens (at 120 s, as CFRTI-K does) nothing of the average is fixed, so there is no narrowing at all and it is CFRTI-K exactly.

## 3. Declined list and bans
- **Inside the window, the side that the fixed part has already decided is priced at 90c or more:** buying it is a fair-value buy at 88c or above held to settlement, which is favourite-and-hold (CHARTER item 5, 7e; named exceptions XRPYES10 and KESTREL are retired). Banned without an owner exception.
- **The other side (the cheap tail):** it is the CFRTI-K cheap-side buy; an edge there needs the market to misprice a near-certain outcome in the final seconds, which is a speed and latency edge against the quote, not a fixed-window fact.
- It is not a lock or parity scan (ARB2 to ARB5), so those rows do not apply.

## 4. Could the bot enter in time?
No. The window opens at 60 s before the close. The second slot cannot enter under 120 s; L1 looks about 6 minutes out (the Closing look 9:00 into the quarter hour is about 6 minutes). At 120 s the average has no fixed part. The narrowing exists only after close minus 60 s, which neither engine can reach, and the 15 minute markets' books are thin that late. Hourly and daily ladders are not bot markets.

## 5. What survives, if anything (not registered, offered)
One honest data question, a version of CFRTI-K, no new try until a pre-registration: whether CFRTI-K's model residual is better for decisions made at 60 s, 90 s and 120 s (the same signal, a later look). It cannot be traded by the current engines (120 s floor) and would be a research read on R6 books only, after CFRTI-K's own read of 2026-11-20. I do not register it tonight: it adds a try (and a look-time sweep, row 190) to an unread rule.

## Dated line (Nov 13, 2026, Auditor B's cautions)
(a) Table row 2's reading of KXBTC15M (a strike-free "close average against open average" market) is UNVERIFIED second-hand text and conflicts with CFRTI-K's registration, which uses the market's `floor_strike`; it is not to be relied on. (b) Section 5's question (decisions at 60, 90 and 120 s) is NOT registered, counts a try if it ever is, and must not be run before CFRTI-K's read, because it would read the same KXBTC15M windows (closes from 2026-11-14).

# PERPIMB1 card (Forensics, lane 3 scalping, Nov 16, 2026; research only, nothing run)

**Question.** Does the size imbalance at the touch, (bid size minus ask size) / (bid size plus ask size), predict the next 1 to 5 minute mid move on BTC, ETH, gold, US Tech 100 and US Large Cap by more than the spread and a taker fee?

**Mechanism and counterparty.** The thin side of the touch is where the next taker order lands. A taker that follows the imbalance trades against liquidity providers who are slow to reprice (their adverse selection is the taker's edge); if the thick side is stale or spoofed, the fade is the other side of that. No claim that it survives costs: the prior is low.

**Uniqueness (checked, disclosed).** Closest: PERPDEPTH1 F1, the same feature at five levels with 5 to 60 minute holds. This one is the touch only, 1 to 5 minute holds, plus a 5 second sampling arm. It is a separate scalping lane by the Head's ruling, but the hypothesis family overlaps: a survivor of either gets a correlation check against the other (0.3 or more is a duplicate, 7d). Declined-list rows checked: second-of-minute taker clustering, fractional-size flow, lock and parity scans.

**Data and the cut.** Arm F: `book_fast.csv`, 5 second book of ten perps (five used) inside 14:30 to 21:00 UTC on weekdays, from the fast lane (first window 2026-11-17 14:30Z). Arm S: `book.csv`, 60 second book, all hours. **Files before the book fix are excluded:** PR 1013 merged at 2026-11-16T21:16:29Z; the whole 18:18 UTC job (it ran the old code to its 22:00Z boundary) holds far levels and is dropped by the loader and counted. Start: the first full UTC day after the first fixed file (provisional 2026-11-17T00:00Z). First read not before 2026-12-01T00:00Z (10 trade days) and only at n 100; one more read of short rules on 2026-12-21 (last decision, before H16).

**Rules.** 5 markets x thresholds 0.5, 0.7, 0.9 x follow or fade x holds 1, 2, 3, 5 minutes x 2 arms = 240. Episode entries, one position at a time, entry at the next quote, exit at the first quote at or after the hold.

**Costs and the maker column.** Price terms in bps after crossing the touch, fee 5 and 12 bps round trip (assumed until Kalshi's schedule is read). Maker column: entry on the own side of the touch, taker exit; fills not modelled, so a maker-only pass is flagged and NOT counted. Margin view at 10, 25 and 50 percent of the page max with a path based liquidation test.

**Gates and trades a day.** n 100, 10 trade days, 3 entries a day (per rule), PF 1.3 at 5 bps and 1.0 at 12 bps taker, BH 5% over m = carried + 240 (6,290,900 today; 7,492,724 from Nov 17), kill fast. Arm S at 60 s polling cannot see a signal that decays in seconds, so its 3 a day gate may be met and the edge absent; that is the point of running both arms.

**Prediction (numeric).** Mean mid move after |I1| >= 0.9 under 0.5 bps against a 5 bps fee: PF under 1.0 at the 5 bps taker line in at least 4 of 5 markets; about 3 percent that any rule passes; maker-only passes likely, not counted. **Kill:** PF under 1.0 at 5 bps taker in 4 of 5 markets in both arms at the first read, or no rule reaching 3 entries a day.

# DRAFT (not registered, not run): CAL-REL1, stand down L1 after Treasury bill auctions

Written 2026-10-29 by worker CAL, after counts only (no profit or loss of any window was read). It is a draft for the lead to accept, change or drop. It becomes a registration only when committed as `workers/CAL_REL1_REGISTRATION.md` before any scoring.

**Why this event type.** The brief: draft a release-window stand-down only for an event type with at least 300 L1 history entries on at least 30 event days in windows closing within 30 minutes after the event. Only Treasury bill auctions qualify (438 entries on 45 days, all series; 150 on the live 5). No macro release (CPI, jobs, PPI, retail, GDP, PCE, FOMC, claims, EIA) qualifies; they are underpowered (see `CAL_RESULT.md`).

**Disclosure (read first).** (1) Bill auctions close at 11:30 ET on most weekdays, so this rule is close to "skip the 11:45 and 12:00 ET closes on weekdays": a time-of-day rule inside the 08:00 to 12:00 Central block that MKTTIME1 (FALSIFIED, 2026-10-29) and HOURS2 already scored on the same history. It is a reworded neighbour of a tested idea, and the lead may rule it a duplicate under RULES.md. (2) Bill auctions are not volatility events for crypto, gold or currencies in any known way; the counterparty below is the brief's generic one and is weak here. (3) The 8:30 ET macro releases, where the mechanism is plausible, cannot be tested on this history.

**Rule, exactly.** L1's history entries from `scalper.tstop1.load()` (6 minute look, side price 0.88 to 0.97, held to settlement, 1 contract). An entry is SKIPPED when its market's close is after the competitive close time of any Treasury bill or CMB auction in `studies/EVENT_CALENDAR_2026.csv` (event TSY_BILL, status verified or rule) and at most 30 minutes after it (auction < close <= auction + 1800 s). All other entries are KEPT. Compare kept against all entries.

**Universe (chosen on time only).** The live 5 (KXGOLD15M, KXBTC15M, KXETH15M, KXDOGE15M, KXXRP15M) as the claim; all 26 series in the file as information only. Fixed before any look.

**Counterparty.** Quoters on Kalshi's 15 minute markets who keep pricing the last minutes of a window as calm while rates desks reprice short-dated funding after a bill auction, so a favourite in the 88c to 97c band is overpriced in the two windows that follow. (Weak; see disclosure.)

**Windows by date.** A: closes 2026-08-06 to 2026-09-03 11:30Z; B: to 2026-10-01 14:45Z; C (holdout, read once): to 2026-10-29 20:45Z (the `tstop1` close-date thirds).

**Fees.** 7% x C x p x (1 - p), rounded up to the cent per order, at C = 1 and C = 10; fees x1.2 check. Entries at the quote of the decision candle as in `tstop1` (a quote that could be hit at or after the signal candle). Zero-volume candles reported both ways.

**Numeric prediction.** Skipping does not lift the live 5's PF by 0.10 in A and B; the skipped group's mean per entry is within 1.0c of the kept group's mean; FALSIFIED with about 90% prior.

**Kill criteria.** FALSIFIED if, in any of A, B, C, skipping does not lift PF by at least 0.10 or keeps less than 70% of net (MKTTIME1's gate); or the skipped group holds fewer than 15 losses across A and B; or the day-clustered z of the per-entry gain is below 2.0. NOT_ENOUGH_DATA if fewer than 300 skipped entries or 30 auction days in the live 5 (on this file the live 5 holds 150, so as written for the live 5 it is NOT_ENOUGH_DATA before it is run; the lead must decide whether the all-series pool may be the claim).

**The bar (strategy-level).** A stand-down is scored on the kept set: PF at least 1.5 in each of A, B and C after fees, positive at fees x1.2, a named counterparty, deflated z at the bar for N about 439,000 (z about 5.17). A pass earns only a forward test registration; nothing goes live.

**Variants (N).** 1 (this rule only; no other window length, event type or offset). Running count +1 if registered.

**TOP LINE: development read PENDING (waiting on the KXBTC15M candles, `CFRTI_K_CANDLES`, PR 826). Updated the hour it lands.**

# Shadow packet: PERPBIN1 (Idea Desk A, Nov 12, 2026; no live account figure)
- **Name:** PERPBIN1 (open-interest arm, Bitcoin only, two tries A and B).
- **Rule, two sentences:** At the opening of a Bitcoin 15 minute window, when the perpetual's open interest rose over the previous quarter hour by an amount in the top third of the development sample, buy 1 contract at the ask of the candle ending 14 minutes before the close, if that side's ask is 0.40 to 0.60 (try A: YES; try B: NO). Hold to settlement.
- **Family (7f):** entry = taker at the window open on a cross-instrument field (perp open interest change); exit = none, hold to settlement.
- **Uniqueness checks for the Verification Analyst:**
  1. *Signal source:* Kalshi's Bitcoin perpetual open interest (a field, not a price or a flow); not the binary's own open interest.
  2. *Exit and management:* none; held to settlement.
  3. *Expected correlation:* gold L1 and EVENT830: none. OICORE: the same market but a different time (window open against the last 3 minutes) and price band (mid-band against 8c to 50c cheap side); measured as (a) the share of PERPBIN1 trades in windows where OICORE's trigger fired and (b) the daily-result correlation on development days; 0.3 or more is a rejected duplicate.
  4. *Declined list:* nearest rows OICORE and XOI1/MECHOI1 (open interest of the binary or of an outside venue). It differs by using the perp's own open interest; it is not taker flow (OI is not tape), not market making, not favourite-late (mid-band entry at the open).
- **Data, and is it current:** the binary side is cleared (CANDLEVSBOOK1). The perp's candle freshness is NOT measured (no perp book); stated limit, no seconds-level claim. The premium arm was dropped because the candles carry no reference price.
- **Events and N:** development = the same 5,127 windows; the top third is about 1,700 windows; each try trades the windows where its side is mid-band, perhaps 500 to 800. For the research bar (z 5.46) that needs an effect of about 6c or more a trade, which is not plausible; the lifecycle's shadow bar is the reachable one. Held-out: closes from 2026-11-05, candles pulled at the Nov 20 sitting.
- **Constants:** cutoff `2026-11-05T00:00:00Z`; the terciles are frozen from the perp candles alone before any outcome; development read once when the candles land; held-out read once, marker NOT READ.
- **Kill and return:** the lifecycle's, as for CFRTI-K (150 forward signals, cash PF 1.3, second half 1.2, 14 days, no day over 30% of net, then the owner; kill below -1c a contract after 50 signals or fewer than 40 signals in 30 days; return after 14 days and a fresh shadow run).
- **What a live version would need from Main:** a second-slot strategy reading the perp's open interest at the window open (one public candle read) and the binary candle at close minus 840 s, orders at the open held to settlement, a new reviewed registry entry, caps and kill rules, an owner popup; it can overlap OICORE in a window, so the direction lock and the shared stop apply.
- **Honest odds:** about 1 to 2% that either try clears the bar; the mechanism (a leveraged crowd on the perp and the binary's YES buyers) is weak and the perp's open interest moves slowly against a 15 minute outcome.

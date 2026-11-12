# W-CAT-ECON1 PLAN (written before any scoring, Nov 11 2026)
Data: Kalshi public API only (series list, settled markets live + historical, hourly candlesticks). No Yahoo, Open-Meteo, outside feed. No rows dropped for source reasons (none used).
UNIVERSE: Economics-category series (896 listed) minus annual/quarterly frequency (cannot reach 30 events); settled markets pulled from /markets and /historical/markets back to 2026-01-01; kept series with >=30 settled events closing on/after 2026-01-01: 66 series, 3,559 events (state gas daily KXAAAGASDxx x50, KXAAAGASD, KXAAAGASW, KXDIESELD, KXJOBLESSCLAIMS, KXSOFRD, KXTRUEV, KXTRUF* x6, KXTSAD/W, KXTXERCOTPEAKD, KXUE).
MARKETS FETCHED: per event the top 3 markets by final volume (disclosed mild post-hoc selection, chosen only to bound requests); candles hourly, 5 days before close.
LOOKS (fixed instants before close): 48h (>24h bucket), 12h (6-24h), 3h (1-6h), 30m (15-60min). Quote = last hourly candle ending at/before the look (carried), market must be open. YES buy at yes_ask close; NO buy at 1 - yes_bid close. Require 0<ask<1, ask>bid.
CELLS: side x price bucket (.05-.15,.15-.35,.35-.65,.65-.88,.88-.97) x look, minus bucket .88-.97 with looks under 6h = 36 cells. One obs per event per cell: the market nearest the money (|yes_ask-.5|).
BASIS: cash at ask, +0c and +1c, fee 0.07*a*(1-a) unrounded, hold. Wins/losses from these only.
SPLITS: chronological thirds by event close date (cut dates from the fetched events, saved in frozen.json). TRAIN, VALIDATE scored; HELD-OUT untouched here.
STATS: event-clustered bootstrap (2000) 90% interval of mean c/contract at +1c; naive z; date-clustered interval reported as extra caution.
DEFLATION: shared ~7,950 (Bonferroni z ~4.5); family exploratory cells (series family x side x bucket x look, n>=60 train) counted as extra tries and labelled exploratory.
SHORTLIST: train n>=60 and val n>=60 (events), PF@+1c >=1.3 in train and val, val clustered lo90>0; best <=2 by val lo90. Held-out read once by lead: PF>=1.2, n>=40, mean>0 = shadow candidate only.

RESULT (Nov 12): 66 series, 3,559 events; 26 cells with n 60+ in both train and validate; best cells negative; Bonferroni (deflation 9,459, z 4.55) passes 0; positive cells have validation n 9 to 10 (DATA_LIMITED). No shortlist, held-out untouched. Fed, CPI and payroll series did not reach 30 events in the window.

## AMENDMENT (2026-11-12T01:11Z, Desk A held-out audit; no rule changed)
Thirds were "cut dates from the fetched events, saved in frozen.json". Cut dates are now constants in `CUTS_W-CAT-ECON1.json` and in the script: cut1 = 1790395140 (2026-09-26T03:59Z), cut2 = 1792641540 (2026-10-22T03:59Z), tertiles of event close over the 3,175 events with candle observations. TRAIN = close before cut1, VALIDATE = cut1 up to cut2, HELD-OUT = cut2 or later. Later pulls may not move them.
HELD-OUT NOT READ as of 2026-11-12T01:11Z.

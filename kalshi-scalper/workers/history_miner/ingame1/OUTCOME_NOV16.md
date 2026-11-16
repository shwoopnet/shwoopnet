# In-game quick reads: outcome (History Miner, Nov 16, 2026)

Ran once each (prints committed blind at b1caeaeee, Auditor B CLEAN on code and both result folders). Tries: 3. Passed: 0. Figures by message only.
- IGFADE1: n = 0 (no evidence). IGUNDER1: no evidence (n under 100). IGTOTDOG1: no evidence (n under 100), well below 1.0 at 2c; dropped.

## Data finding (diagnostic after the run, recorder rows only, no result read)
- The recorder's achieved cadence is about 2 minutes, not 20 s: of NHL moneyline same-ticker gaps, most fall at 100 to 140 s; gaps of 45 s or less are about 1 percent.
- So IGFADE1's trigger (a 10c move within 45 s) never fired on NHL (0 pairs), and 'live time' (the first pair within 45 s) fires at near-random times: median entry about 1 to 1.5 days after it, i.e. live time is usually pre-game.
- Any in-game rule on this recorder needs a trigger that tolerates 2 minute gaps, or the recorder must reach its designed cadence. Not a result about the markets; a result about the data.
- Ticker coverage: of 136 NHL moneyline tickers in the rows, 42 are in the Nov 8 to Nov 12 listing (the rest close Nov 13 on, held out, or Nov 7).
- Auditor B (Nov 16 15:23Z): IGFADE1 reads NOT RUNNABLE at the recorder's cadence (a 45 s trigger cannot fire at ~2 minute polls); tried 1, passed 0. Any version with a trigger of 2 minutes or more is a new registration and a new try.

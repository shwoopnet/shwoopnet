# NFLFTD1 result (2026-11-04): NOT_ENOUGH_DATA at the census; no outcome, price or candle joined

Registration sha256 `e826dcfc4a3546281edb438f8512dc14bfeb37f155c9ca957ffa4cf2e21b8d5a` (`workers/NFLFTD1_REGISTRATION.md`). Code `src/scalper/nflftd1.py` (census plus helpers), tests `tests/test_nflftd1.py` (3 pass).
- Games: 334 settled KXNFLFIRSTTD events before the frozen cut (6,741 markets, 3 to 32 players an event, median 20); TEST third = 112 games. ESPN play-by-play reachable.
- n: 0 trades computed. Expected treated 20 to 60 in TEST (guess, stated before), under the 150 gate and 112 games under about 150.
- Win rate versus price, PF versus control: not computed (census gate stopped the run on purpose; the cheap side's prediction is win 4 to 7% against ask 7 to 10%, PF 0.5 to 0.8, unmeasured).
- Verdict: NOT_ENOUGH_DATA (months to go: about 2 months, read 2027-01-11 after the regular season; borderline even then at 60 to 150 treated trades).
- Forward plan: freeze the model fitted on the first 222 games, then run TEST plus the frozen games (2026-10-03 on) once on or after 2027-01-11; if still under 150 treated, the 2027 September season.
- N: +2. Nothing was fetched from the frozen third; no favourite side was evaluated.

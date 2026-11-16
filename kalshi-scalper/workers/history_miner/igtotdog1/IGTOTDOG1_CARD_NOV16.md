# IGTOTDOG1: buy the cheap side of an in-game total (History Miner, written Nov 16, 2026 ~13:10Z, before any read)

Shape: a "dead" total. Once a game is live, the first time either side of its totals market is priced 8c to 20c, buy that side and hold to settlement.
Counterparty and prediction: in-game bettors abandon a total that looks settled (scoring runs, late pace changes are underpriced); the cheap side wins more often than its price, PF at 2c >= 1.3.
Uniqueness: not lead-lag (one market only, no other market's price is used except the moneyline's poll TIMING for live time); not favourite-and-hold (buys the cheap side); differs from IGUNDER1 (fixed side, 35c to 65c, first row) and IGFADE1 (jump trigger). Closest existing: OICORE (cheap side 5c to 50c, crypto, open interest trigger): different market family and signal.

Data and holds exactly as INGAME_CARDS_NOV15.md Amendments 1 and 2 (Auditor B 2026-11-15 21:23Z, 21:26Z, 21:32Z): recorder rows before 2026-11-13T00:00Z only; totals of NBA, NFL and NHL; results from IG_RESULTS and IG_RESULTS_NHL (closes 1794096000 to 1794527999). Thirds by close: t1 before 1794355200, t2 to 1794528000; third 3 (from Nov 13) held out, never listed.

Rule:
- Live time = ingame1.live_time (the first pair of moneyline polls of one ticker within 45 s; the recorder's hot cadence, which can start before tip-off).
- Scan the game's totals rows with t >= live time in time order (ties: ticker order); take the FIRST two-sided row where the YES ask (yes_ask) is 0.08 to 0.20 (buy YES) or the NO ask (1 - yes_bid) is 0.08 to 0.20 (buy NO). One entry per game. Hold to settlement.
- Net as ingame1.net (per-order rounded fee, void refunds price and keeps fee). Haircut 0, 1c, 2c; primary 2c. c = 1 and 10.
- Bar: n >= 100 over t1 and t2; PF at 2c >= 1.3 pooled and >= 1.0 in t1 and in t2. Under 100: "no evidence at n = x".
- One try. Kill: PF at 2c under 1.0.

Hand case (invented): live at 120. Totals rows: t 130 (0.50, 0.52) no; t 150 (0.06, 0.08): YES ask 0.08, buy YES. Result yes, h 2c: entry 0.10, fee ceil(0.63) = 0.01, net +0.89; result no: -0.11. A row (0.85, 0.88) gives NO at 0.15. A row before live time is ignored. A one-sided row (0.00, 0.05) is skipped.

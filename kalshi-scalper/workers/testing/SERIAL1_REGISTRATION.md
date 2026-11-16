# SERIAL1: serial dependence of 15 minute outcomes on non-crypto (NC15) markets. Registered Nov 16, 2026, BEFORE any read (Testing Desk)

Mechanism (not favourite-late, open interest, lead-lag or jump-fade): a 15 minute market's strike is the underlying's price at the previous window's close, so the previous window's result is the sign of the underlying's last 15 minute move. If commodity and FX prices carry short-term momentum (or bounce), the next window's result is predictable from it, and a mid-priced quote may not price that. Prediction: continuation (variant C) or fade (variant F) has a positive net after the haircut. Both are registered as two tries.

Data: the OIREL-X extract already held (KXGOLD15M, KXSILVER15M, KXCOPPER15M, KXPLATINUM15M, KXPALLADIUM15M, KXWTI15M, KXNATGAS15M, KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M; the crypto series are excluded). Market rows and candles with end_ts after the market's close are dropped first. Window with the Aug 6 to Oct 2 close dates the extract holds; no later data.

Rule (per market M of series S, close C): the previous window P is the market of S closing at C - 900 with a result yes or no; else skip (counted). Signal side: variant C buys the side that won in P (YES if P resulted yes), variant F the other side. Entry: the candle ending exactly 600 s before C; skip if its bid or ask is missing, bid <= 0, ask >= 1 or ask <= bid. The side's ask is YES ask, or 1 - YES bid for NO. Trade only if that ask is 0.35 to 0.65 inclusive (a mid-priced bet, so no favourite effect). Hold to settlement, 10 contracts. A void result: price refunded, entry fee kept.

Haircut and cash: C1 to C11 as in the standing rules: price paid = ask + h, never past 0.99, h in {0, 0.01, 0.02}; per-order rounded fee fee_up_order(price, 10) = ceil(round(0.07 x 10 x p x (1-p) x 100, 9)) / 100; cash = 10 x (win - price) - fee. The entry candle is 10 minutes before the close (not in the last 2), but NC15 uses 2c as primary. Label "upper bound, not fill-checked".

Pass bar (lighter gate, paper): n >= 300 trades; at the 2c haircut profit factor >= 1.3 with both halves (floor(n/2) by close time) >= 1.0 and the 1c PF >= 1.3; day-clustered z >= 2.0 at 2c; both variants counted as tried 2 (the pass needs the variant's bar, not the better of two by a lower bar). Anything else is a fail, reported as "tried 2, passed 0". No other parameters will be tried; the band, look and window are fixed above.

Process: hand case before code (SERIAL1_HAND_CASE.md); one build; Auditor B sanity check of the hash and the printout; run once; commit the print sha256 before reading it. Figures by message only; no extract data in the repo.

## WITHDRAWN Nov 16, 2026, before any read (Head's order): duplicates Desk A's ADJWIN1. No read, no code run on the extract, no tries counted. serial1_second.py and its hand case stay as unused files.

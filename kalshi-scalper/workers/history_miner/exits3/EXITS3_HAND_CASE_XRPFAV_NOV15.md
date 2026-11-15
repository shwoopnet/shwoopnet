# EXITS3: hand case for XRPFAV6 and XRPFAV10 (2026-11-15 ~16:30Z, before the code and before the extract is read)

**Source of the rules:** research branch src/scalper/regime_b2.py (the REGIME-B2 history read that printed XRPFAV6 PF 1.56 and XRPFAV10 PF 1.91). The XRPFAV6 registration is main's kalshi-scalper/README.md SHADOW-WEEK2. XRPFAV10 was never registered (dropped before merge), so regime_b2.py is its only definition.

**Entry, per market (KXXRP15M):**
- The decision candle is the LAST candle with seconds left (close - end_ts) in [330, 400] (XRPFAV6) or [570, 640] (XRPFAV10).
- It must be two-sided (0 < bid < ask < 1, which is also C1). XRPFAV6 also requires a spread (ask - bid) of 0.02 or less.
- The favourite side is YES if ask >= 1 - bid, else NO, at price p = that side's ask (YES: ask; NO: 1 - bid). Trade only if 0.88 <= p <= 0.92.
- **1 contract** (the shadow rules' size). The fee per order is rounded up to the cent at c = 1 (C4). regime_b2 used an unrounded fee, so its figures were raw.
- e = p; the entry candle is the decision candle.

**Data:** Forensics' XRPFAV extract (claude/forensics-desk 31351c1b, XRPFAV_extract.sqlite.xz, xz sha256 be6bc75f...): KXXRP15M from alts2, the window and cuts in its cut log (to before 2026-10-03, XOI1). Candles after a close are dropped.

**Exits:** the engine as in EXITS3_HAND_CASE_NOV15.md, with C = 1 for these cards.
- M applies (the 180 s mark is after an entry at 330 s or more).
- **Primary haircut per variant:** hold 1c (C2, entry only); M 1c (the exit is 3 minutes before the close); T and S 2c (their exit can fall in the last 2 minutes, the Head's 15:49Z instruction and C8). 0, 1c and 2c are all printed.
- **Stated now:** with e from 0.88 to 0.92, T's target is min(2e, 0.90) = 0.90. So T sells at the first later mark whose favourite bid is 0.90 or more, often within a minute or two of entry. T on this card is close to "sell almost at once at about the entry price". That follows from the variant as fixed, and is not changed per card.

**Expected by hand (c = 1, fee = ceil(100 x 0.07 x p(1 - p)) / 100):**
- **X1 (XRPFAV6):** marks at 400, 360 and 300 s left; the last in [330, 400] is 360 s, with bid 0.88, ask 0.89 (spread 0.01). YES ask 0.89 >= NO ask 0.12, so YES at e = 0.89.
  - A mark at 240 s with bid 0.90 triggers T: sale 0.90 at h 0. fee(0.89) = ceil(0.6853) = 1c and fee(0.90) = ceil(0.63) = 1c, so net = 0.90 - 0.89 - 0.02 = -0.010.
  - M at 180 s, bid 0.93: net = 0.93 - 0.89 - 0.01 - ceil(0.4557)/100 = 0.020.
  - Hold, result yes: 1 - 0.89 - 0.01 = 0.100.
- **X2:** the same window with spread 0.03 at 360 s: XRPFAV6 no trade.
- **X3:** NO favourite: decision bid 0.10, ask 0.11, so the NO ask is 0.90 >= YES ask 0.11; NO at e = 0.90.
- **X4:** favourite price 0.93: no trade. Price 0.88: trade (inclusive).
- **X5 (XRPFAV10):** the last candle in [570, 640] chosen, with no spread cap: a spread of 0.05 still trades.
- **Code change for these cards (after the OIREL and OICORE run):**
  - exits3.py now takes the contract count per card (CONTRACTS: OIREL and OICORE 10, XRPFAV 1), the series per card, and a primary haircut per variant (PRIMARY_H).
  - Re-running OIREL and OICORE with the new code gives byte-equal variant figures, entries and not-two-sided counts to the committed prints (checked in scratch on the same, already-read extract). Only the print's "primary_h" became a per-variant map, and "contracts" was added.
- Tests X1 to X5 pass as written above.

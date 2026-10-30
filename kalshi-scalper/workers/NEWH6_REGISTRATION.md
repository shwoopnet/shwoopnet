# NEWH6 registration (Strategy Research V2 worker NEWH6, 2026-10-30, research only)

Written and pushed BEFORE any NEWH6 entry was joined to any quote after its signal or to any outcome. Code will be
`src/scalper/newh6.py`; result `workers/NEWH6_RESULT.md`. Scope (owner, 2026-10-28): no buy-the-favourite-and-hold idea and no L1
filter, exit, size, hour or throttle. **Every rule below is a round trip: bought at an ask and sold at a bid inside the window, never
held to settlement.** Markets: Kalshi KXGOLD15M and KXBTC15M only.

## Ledger check (why these are new, and what was declined)

Read before writing: `workers/RULES.md`, the README headings, the S01 to S42 and O1 to O50 catalogues, BK1 to BK7, BTC1, SCALP1 and
SCALP2, HIST1, AUTO1 to AUTO3, GEN1 (grammar), MAKER4, and the results of NEWH1 to NEWH5, GEN4 to GEN7, FALS3, FALS4, MECH1, SLOTEX,
EVT1, QUOTE1. Looked at in the data: only the candle table layout (`bid_o/h/l/c`, `ask_o/h/l/c`, `price_c`, `volume`, `oi`) and that
the first candle of every window ends 840 s before the close. No quote at or after any signal time and no result was read.

**Declined, no try spent:**
- **Momentum through 50c, bought and sold before 3 minutes left** (the brief's fourth example): HIST1's third trigger ("side whose bid
  rose 10c+ in 2 minutes with ask 20 to 70c", targets and stops, sold by 120 s) and S27 / S35 cover a side moving up through the
  middle, and GEN1's grammar (bid change plus ask level plus a 50c-cross exit) can draw it. Reworded tested idea.
- **Gold and Bitcoin as a pair in the same window** (the brief's second example): BK4 (Bitcoin YES plus gold NO, held) and BK5
  (divergence pair) were run, and O14 / S42 cover the "which series is off" story. I have no reason the PAIR is mispriced that the
  two single markets do not already carry (their outcomes are close to independent at 15 minutes), so a round-trip pair would only
  double the costs. Not spent.
- **A frozen quote that then breaks, and one-sided intra-minute churn:** S33 (compression breakout), S29 (wick), S32 (one-sided pull).

**What is new below:** (1) a counterparty that is Kalshi-internal and mechanical: stop-loss sellers who exit a FORMER favourite at
fixed lines (L1's own exit watch sells at 25c; other bots do the same), bought after the line breaks and sold two minutes later;
S27 faded any 12c jump in minutes 3 to 10, S31 held a dipped dweller to settlement; neither conditions on a favourite of 85c+ falling
through 30c late in the window. (2) Scheduled taker demand on a clock: favourite-buying bots (L1 and others) lift offers in the
minute ending 300 s before the close; front-run it with a two minute round trip, or fade the push afterwards. Nothing in the ledger
uses the clock of other bots as the signal. (3) The FIRST quote of the window (`bid_o`, `ask_o` of the first candle) against the
previous window's leader, faded as a round trip; BTC1 CONT, S39 and BK1 used closing quotes and held to settlement.

## Common to every rule (fixed now)

- **Data:** 1 minute candles, Bitcoin from `l1b`, `book`, `fresh`; gold from `l1b`, `book`, `fresh`, `five`; first file wins per close.
  Universe: every settled window in those files, chosen by date only.
- **Windows by close time (UTC):** DISCOVERY 2026-08-06 00:00 to 2026-09-21 00:00; VALIDATION 2026-09-21 00:00 to 2026-10-28 00:00.
  Nothing closing on or after 2026-10-28 00:00 is loaded. The third window is the FORWARD record: a validation survivor goes to
  `workers/candidates/` with a freeze time after its commit and is read only by the forward ledger.
- **Signal** on a candle's values (known at that candle's end). **Fill:** the bought side's closing ask on the NEXT candle (YES at
  `ask_c`, NO at 1 - `bid_c`); missing candle or ask outside the stated band or not strictly inside (0, 1): no trade (counted).
- **Sale:** at the stated exit candle's closing bid of the held side (YES `bid_c`, NO 1 - `ask_c`). **A zero bid (or a missing exit
  candle) is no sale:** the sale moves to the next candle, at most to the candle ending 120 s before the close; if there is still no
  bid above 0, the position is booked at 0 (the whole entry lost), counted as "no sale". Never held to settlement in the headline;
  the hold-to-settlement value of those rows is printed as information only.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order, on the buy AND the sell. Headline C = 10; C = 1 reported; fees
  x1.2 at C = 10 reported. Net = C x (sale - fill) - fee(fill) - fee(sale).
- **Zero volume both ways:** PF with all trades, and with trades whose fill or sale candle had volume 0 removed.
- **One trade per window per rule.** Each rule is screened per market (gold and Bitcoin separately), so every rule is 2 tries.
- **Screen (the brief):** DISCOVERY PF >= 1.5 at C = 10 on >= 100 trades and net > 0 at fees x1.2; then VALIDATION PF >= 1.3 on
  >= 50 trades and net > 0 at fees x1.2. Fewer trades than the minimum in either window: NOT_ENOUGH_DATA, never a pass. Day-clustered
  z reported; the deflated bar for N about 592,000 is z about 5.2, so a survivor earns only a forward ledger entry
  (`workers/candidates/`, evaluator `scalper.newh6:forward_eval`, with a parity check against this file's code).
- **Verdict words:** FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE.

## H1 STOPRUN: buy the fallen favourite after it breaks the stop lines, sell two minutes later (2 tries: gold, Bitcoin)

- **Signal:** scan candles ending 600 s to 300 s before the close, in order. For side X (YES bid `bid_c`; NO bid 1 - `ask_c`): X's
  bid was >= 0.85 at some earlier candle of this window (ending 840 s up to the candle before the signal), X's bid at the signal
  candle is in (0, 0.30], and X's bid at the candle before was above 0.30 (the first break of 30c). First such candle and side.
- **Trade:** buy X at the next candle's ask, ask in [0.05, 0.45]; sell at X's bid on the candle ending 120 s after the fill candle
  (the latest fill is at 240 s, so the latest sale is at 120 s left).
- **Counterparty:** stop-loss sellers on a former favourite (bots with fixed exit lines, L1's 25c exit watch among them, and people)
  who sell at the bid regardless of value when the line breaks; their selling pushes the bid below fair for a minute or two.
- **Honest alternative:** the fall is information (markets fall in jumps; the 25c line study found the bid already 11c at the first
  close below 25c), the spread is wide after a crash, and two fees on a 20c contract eat any bounce.
- **Prediction:** FALSIFIED on both markets, discovery PF about 0.7 (n gold about 100 to 200, Bitcoin about 300 to 500).

## H2 CLOCKFLOW: other bots buy favourites on a clock (4 tries: F and R, each gold and Bitcoin)

- **Mechanism:** L1 (and, by MECH1's late-minute favourite share, other takers) lifts the favourite's offers in the minute ending
  300 s before the close (L1's 6 minute look). A scheduled taker is predictable flow.
- **H2F front-run:** at the candle ending 480 s before the close, the side whose ask is in [0.88, 0.95] (YES first); buy it at the
  next candle's (420 s) ask, ask in [0.88, 0.96]; sell at its bid on the candle ending 300 s before the close (just after the 6 minute
  wave). It is a two minute round trip and never holds: the bet is on the push, not on the outcome.
  **Counterparty:** the clocked favourite buyers who pay up for the side we already hold.
- **H2R fade:** at the candle ending 300 s before the close (the wave's minute), the side whose ask is in [0.88, 0.97] (YES first);
  buy the OTHER side at the next candle's (240 s) ask, ask in [0.03, 0.15]; sell at its bid on the candle ending 180 s before the
  close. **Counterparty:** the same buyers, whose push leaves the favourite rich and the cheap side cheap for a minute.
- **Honest alternative:** the clocked flow is small against the book and makers are already priced for it; the spread and two fees
  on a 2 minute hold are about 2c to 4c on H2F and most of a 5c contract on H2R.
- **Prediction:** FALSIFIED on all four; H2F discovery PF about 0.5 to 0.8 (the bid rarely gains 2c in 2 minutes at 90c), H2R about
  0.3 to 0.6.
- **Scope note:** H2F buys a favourite but sells it at 300 s left after two minutes; it changes nothing about L1 and does not hold.
  If the lead reads it as inside the owner's 2026-10-28 ban, H2F's two rows are information only (still counted in N).

## H3 OPENLEAN: the first quote of the window leans toward the previous window's leader; fade it (2 tries: gold, Bitcoin)

- **Previous leader L:** the same series' window closing 900 s earlier; L = the side with mid above 0.5 at its last candle (ending
  at its close; if missing, the candle ending 60 s before); no previous window, no candle or a mid of exactly 0.5: no signal. Known
  before this window opens.
- **Signal:** the first candle (ending 840 s before the close) with `bid_o` > 0 and `ask_o` < 1; opening mid m = (bid_o + ask_o) / 2;
  lean = m - 0.5 signed toward L. lean >= 0.05 is the signal.
- **Trade:** buy the side OPPOSITE L at the next candle's (780 s) ask, ask in [0.20, 0.55]; sell at its bid on the candle ending
  540 s before the close (4 minutes later).
- **Counterparty:** the first quoters of a new window who anchor on who just won (a momentum belief or a carried quote) before the
  window's own price has any information.
- **Honest alternative:** for Bitcoin the strike is a lagging 60 s average (L8), so an opening lean is partly real drift; for gold
  GPRIOR found the book already prices the previous window. The lean may simply be correct.
- **Descriptive line (not counted, not screened):** mean opening lean toward L over all windows, and the share above +0.05.
- **Prediction:** FALSIFIED on both, discovery PF about 0.6 to 0.9.

## Kill criteria (each try)

Discovery PF < 1.5 on >= 100 trades, or net <= 0 at fees x1.2: FALSIFIED (no validation read for selection; validation printed for
the record). Discovery pass and validation PF < 1.3 on >= 50 trades or net <= 0 at x1.2: FALSIFIED. Fewer than 100 discovery or 50
validation trades: NOT_ENOUGH_DATA. Both passes: NOT_YET_FALSIFIED, candidate file plus parity check, forward read only.

## Count

N tried: **8** (STOPRUN 2, CLOCKFLOW 4, OPENLEAN 2). Descriptive lines and hold-to-settlement information lines are not counted.
Running count about 592,074 (after NEWH5) plus other workers' additions, plus 8.

## Amendment (2026-10-30, after a run that scored ZERO OPENLEAN entries; written before any OPENLEAN trade is scored)

The first run printed STOPRUN and CLOCKFLOW (their numbers stand as run) and no OPENLEAN entry at all: in every gold and Bitcoin
window the first candle's OPENING quote is an empty book (`bid_o` 0 to 0.011 with `ask_o` 0.989 to 1.0; e.g. in `book`, 0.0 / 0.999
in 2,077 windows and 0.001 / 1.0 in 1,739), so the registered opening mid never exists at minute resolution. As registered,
**OPENLEAN is NOT_RUNNABLE**: Kalshi's book opens empty and the first quoters arrive inside the first minute. Following the CONF1
precedent (an amendment after a zero-entry run, to the closest feasible definition), OPENLEAN is re-read ONCE with the lean taken from
the first candle's CLOSING quote (ending 840 s before the close: mid = (`bid_c` + `ask_c`) / 2, needs `bid_c` > 0 and `ask_c` < 1),
the first two-sided quote of the window that the candles carry. Everything else (previous leader, lean >= 0.05, buy the other side
at the 780 s ask in [0.20, 0.55], sell at the 540 s bid, kill criteria, prediction) is unchanged. It stays 2 tries (no variant added);
the NOT_RUNNABLE original is reported as such. Nothing about STOPRUN or CLOCKFLOW is changed or re-run.

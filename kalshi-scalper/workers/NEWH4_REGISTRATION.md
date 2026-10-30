# NEWH4 registration (V2 worker NEWH4, 2026-10-30, research only; written and pushed before any outcome is read)

New mechanisms on the LADDER markets themselves (Bitcoin hourly "above K" KXBTCD, gold hourly KXGOLDH), not on the 15 minute
contracts and not against them. **5 tries.** Gold daily and weekly ladders (KXGOLDD, KXGOLDW) are not tried (see the end). Three ideas
from the brief are declined without a try. Nothing here touches L1's code or anything live.

**Looked at before writing (no outcome, no quote at an entry time):** the README headings and the results of TAIL1, the 2026-10-23
ladder structure scan, LAD1, the 2026-10-26 ladder arbitrage snapshot, GOLD2 (card), ARB2, GEN3 (and G3H1/QUOTE2B), LADL1, CONF1,
CONF2, LOCK2H, DAILY2, INX1, NEWH2 (H4 GLADH), NEWH3 (H1 BLADX), the owner's instruction of 2026-10-28 and
`studies/SETTLEMENT_MECHANICS_2026-10-29.md`; the table layouts and row counts of `lad2`, `conf2_lad`, `newh2_goldh`, `ladders`,
`ladl1`; per file the date range, closes, strikes per close, strike grid ($100 Bitcoin, $2 gold) and which minutes have candles
(Bitcoin: candles ending 3,300 s to 60 s before each hourly close; gold: 900 s to 60 s). No quote, mid, result or trade of any
market in the universes below was read.

## Common to all

- **Data:** KXBTCD candles from `lad2` then `conf2_lad` (first file wins per ticker; universes chosen by the earlier workers from
  quotes 55 to 52 minutes before each close, so no universe look-ahead); KXGOLDH candles from `newh2_goldh` (strikes within $12 of the
  15 minute gold strike, which is set at the 15 minute window's open, before any entry time here).
- **Windows by close time (UTC), fixed now:** DISCOVERY close >= 2026-08-23 00:00Z and < 2026-09-21 00:00Z (each ladder's history
  starts Aug 23 or 24); VALIDATION close >= 2026-09-21 and < 2026-10-28 00:00Z. Nothing closing on or after 2026-10-28 is loaded. The
  third window is the FORWARD record (a validation survivor goes to `workers/candidates/` with a freeze time after its commit).
- **Quotes:** a candle's closing YES bid and ask. YES ask = ask; NO ask = 1 - YES bid. Mid = (bid + ask) / 2. A strike is "quoted"
  at a candle when 0 < bid < ask < 1 (TAIL also allows a bid of 0 for a YES buy; see TAIL).
- **Fill:** at the side's ask on the NEXT candle of the same strike (ending 60 s after the signal candle); it must be inside the
  registered fill band, else no trade (counted as a miss). Held to settlement (none of these sells). A missing candle is a data gap,
  never a trade.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order. Headline PF at C = 10; C = 1 reported; fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF with all trades and with trades whose fill candle had volume 0 removed.
- **Screen (the brief):** DISCOVERY PF >= 1.5 at C = 10 on >= 100 trades and net > 0 at fees x1.2; then VALIDATION PF >= 1.3 on >= 50
  trades and net > 0 at fees x1.2. Fewer trades than the minimum in either window = NOT_ENOUGH_DATA, never a pass. Day-clustered z
  reported; the deflated bar for N about 592,000 is z about 5.2, so a survivor earns only a forward ledger entry.
- **Owner's 2026-10-28 instruction** (no more buy-the-favourite-and-hold research): every rule here buys a side priced at most 85c
  (KINK) or at most 35c (TAIL, NARROW), never L1's 88c to 97c band.
- **Probit fit (used by KINK and NARROW).** At one candle, take the strikes whose mid is in [0.03, 0.97]; z_i = Phi^-1(mid_i);
  ordinary least squares of z on K gives z = a + b K. With b < 0 this is the normal CDF P(above K) = Phi((mu - K) / s), mu = -a / b,
  s = -1 / b. Fewer strikes than the minimum, or b >= 0, means no fit.

## H1 KINK-BTC and H2 KINK-GOLD: one strike off the ladder's own curve (2 tries)

- **Structure.** The ladder is one distribution quoted strike by strike. If one strike's quote sits well off the curve its neighbours
  draw, either that strike's quote is stale (a maker repriced the ladder and left one strike behind, or a resting retail limit sits
  there) or the curve's shape is wrong at that point (fat tails, skew).
- **Rule.** Scan candles in time order: Bitcoin ending 3,000 s to 600 s before the close; gold ending 840 s to 180 s before. For each
  quoted strike i with spread <= 0.05, fit the probit curve on the OTHER strikes (leave one out, at least 5 strikes in [0.03, 0.97]),
  fair f_i = Phi((mu - K_i) / s). Signal YES if ask_i <= f_i - 0.05; signal NO if (1 - bid_i) <= (1 - f_i) - 0.05. Side ask at the
  signal in [0.10, 0.85]. The FIRST signal candle per close is used (if several strikes signal at that candle, the largest gap); one
  trade per close. Fill band [0.10, 0.85]. Held.
- **Counterparty:** the maker or resting limit that left one strike behind a ladder move.
- **How this differs:** LAD1 priced each Bitcoin strike from spot and a volatility (outside inputs, no comparison between strikes);
  BLADX / GLADH compared the 15 minute book with a ladder interpolation; ARB2, LOCK2H and the 2026-10-23 scan looked only for riskless
  monotonicity locks. KINK uses only the ladder's own cross section and buys a non-riskless relative mispricing.
- **Prediction:** the normal curve is the wrong shape in the wings, so most residuals are shape, not staleness: discovery PF about
  0.9 on both; FALSIFIED (or NOT_ENOUGH_DATA under 100 discovery trades).
- **Kill:** as the screen.

## H3 TAIL-BTC and H4 TAIL-GOLD: the ladder's deep longshots held to settlement (2 tries)

- **Structure.** The favourite-longshot bias says the cheapest contracts are overpriced; GEN3-H1 found the opposite on the PATH of
  cheap Bitcoin ladder sides early in the hour (they touch higher more often than priced). Held to settlement, which is it on the
  ladder? TAIL1 tested 15 minute gold underdogs (4c to 10c, FALSIFIED); the ladder's far strikes are a different market.
- **Rule.** One look per close: Bitcoin the candle ending 1,800 s before the close; gold the candle ending 600 s before. A YES
  longshot is a strike whose YES ask is in [0.02, 0.06] (bid may be 0); a NO longshot is a strike whose NO ask (1 - YES bid) is in
  [0.02, 0.06] (YES ask may be 1 or missing only if the bid is present). Per close at most one YES trade (the qualifying strike with
  the LOWEST K, nearest the money) and one NO trade (the qualifying strike with the HIGHEST K). Fill band [0.01, 0.08]. Held.
- **Counterparty (if it pays):** makers who quote the far wings at a flat few cents without repricing for the hour's remaining
  volatility. **Expected instead:** the longshot buyer is the one who pays.
- **Prediction:** FALSIFIED on both, discovery PF about 0.6 at C = 10 (longshot bias plus the minimum fee tick).
- **Kill:** as the screen.

## H5 NARROW-BTC: the ladder's width against how far its own centre has been moving (1 try)

- **Structure.** The ladder implies a remaining spread s_t (probit fit). The ladder's own centre mu_t moves minute to minute; its
  realised 1 minute movement scaled to the time left is a second, ladder-only estimate of the remaining spread. If the ladder is
  much narrower than its own centre has been moving, the cheap sides one strike or two out are underpriced.
- **Rule.** Bitcoin only (gold has 15 minutes of candles, too short for the trailing window). Scan candles ending 2,100 s to 600 s
  before the close. At each candle t, fit (at least 3 strikes in [0.03, 0.97]); take the fits at the 20 candles ending t - 1,140 to
  t; with at least 15 successive pairs, sd1 = standard deviation of the 1 minute changes of mu; real = sd1 x sqrt(lead / 60); R =
  s_t / real. Signal when R <= 0.6. Then buy the cheap side (YES on a strike above mu, NO on a strike below mu) of the quoted strike
  (spread <= 0.05) whose cheap-side ask is in [0.10, 0.35] and closest to 0.20 (ties: the lower strike). First signal per close.
  Fill band [0.10, 0.35]. Held.
- **Counterparty:** ladder makers who set width from a slow volatility estimate and lag a fast hour.
- **How this differs, stated plainly:** LAD1 (realised volatility from spot bars, 30 minutes, per-strike fair value, held) is the
  nearest relative and read +0.10c (z 0.08). NARROW uses no spot price at all (the ladder's own centre path), a regime trigger on
  the whole ladder rather than a per-strike edge, and only the cheap side. Risk stated in advance: fit noise in mu inflates the
  realised figure, so R is biased low and the trigger fires more than a true narrow ladder would.
- **Prediction:** FALSIFIED, discovery PF about 0.9.
- **Kill:** as the screen.

## Declined, no try spent

- **Monotonicity violations bought as a lock** (ask of YES at K_lo below the bid of YES at K_hi): ARB2 (every open event, twelve
  scans), the 2026-10-23 and 2026-10-26 snapshots (zero) and LOCK2H (non-simultaneous candle quotes can never confirm a lock) cover
  it. KINK is the non-riskless version.
- **Far strikes near the close still trading above zero:** profiting from it means buying the 97c to 99c side and holding, which is
  buy-the-favourite-and-hold (owner's 2026-10-28 instruction) and close to LADL1 and E4.
- **NARROW's mirror (ladder too wide, buy the near favourite):** same instruction.
- **Gold daily and weekly ladders:** the only local rows are LADL1's two looks for 38 daily and 9 weekly closes (`ladl1.sqlite`), no
  path. A daily ladder gives one independent close per day, about 40 in discovery at most, below the 100 trade screen without
  pooling correlated strikes. Not tried; NOT_RUNNABLE on local data.

## Count

**N added: 5** (H1 to H5, one rule each, no parameter searched). Running count about 592,061 plus other workers' additions, plus 5.
Code: `src/scalper/newh4.py` (`PYTHONPATH=src python -m scalper.newh4 run`, run once).

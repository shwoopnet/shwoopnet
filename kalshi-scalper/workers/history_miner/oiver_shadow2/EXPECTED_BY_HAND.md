# OIVER shadow replay, build 2 (the three Bitcoin OIVER places beside OICORE), expected by hand (History Miner, Nov 13, 2026)

Written BEFORE the code, from Desk A's frozen sheet `kalshi-scalper/workers/DESK_A_FROZEN_OIVER_SHADOW_DEFINITIONS_NOV13.md` at 61fb9854 (sha256 cb45e79b; committed 2026-11-13T21:19:58Z), with the wheel sheet's section 0 where it points there. Desk A's code was not read. The Head's order of 21:22Z: R6 fill check (next poll within 4 s). The OICORE places and part (3) (the nightly OI candle source) come later; the NC15 6 s check will be a parameter of that later file. No real file is read.

## Rules as built
- **Windows:** every distinct (ticker, close_time) of series KXBTC15M in the R6 book files given. Each book.csv.gz is one run folder.
- **Count start:** a window counts only if its decision instant D = close - 180 s is after BOTH COUNT_FROM (the sheet's commit time, 1794604798) AND OI_NAMED_AT (the time the open interest source is named in a dated line; a required argument). Not yet named means the run STOPS ("no place records a signal"). Earlier windows are counted before_count_from.
- **Clock:** exchange time by the offset formula, the same code as `oiver_r6sizes` b8535332: the median over the last 120 readable-header rows of the run of (Date + 0.5 - t_recv s).
- **Decision poll:** the last poll of the window's ticker and close_time with exchange time in [D - 10 s, D]. None: no_poll.
- **Book:**
  - YES bid = yes_bid_px_1; YES ask = 1 - no_bid_px_1.
  - Rule 18: two-sided only if both exist and 0 < bid, ask < 1, bid < ask - 1e-9; otherwise not_two_sided.
  - NO ask = 1 - YES bid. The cheaper side has the lower ask; a tie goes to YES.
- **Parent trigger:** oi_rise from the OI input file (ticker -> oi_rise; the source is to be named).
  - A missing row: no_oi.
  - Under 86,300: oi_below (86,300 is inclusive).
  - Band: 0.08 <= ask <= 0.50 inclusive; under is cheap, over is out_of_band.
  - A window passing all of this is a parent SIGNAL.
- **Places**, each a condition on the decision poll only:
  - SPREAD: YES ask - YES bid <= 0.03;
  - CAP30: ask <= 0.30;
  - DEPTH: the touch size >= 40, where the touch is the best NO bid size for a YES buy and the best YES bid size for a NO buy. A blank size is size_unknown.
  - A place records pass or skip with its reason.
- **Fill check, the same for the parent and every place:**
  - The NEXT poll of the same ticker and close_time after the decision poll (by exchange time) must be at most 4 s after it. Otherwise: miss_no_second_look.
  - Both polls must offer 20 contracts at or under limit = the ask seen, on the ladder the order meets (a YES buy meets the NO bids, ask = 1 - px; a NO buy meets the YES bids), summing levels 1 to 5 with ask <= limit + 1e-9. Otherwise: miss_depth.
  - Fill price = the higher of the two polls' walked averages for 20 contracts. Since the limit equals the decision poll's best ask, this is always the limit; the walk is still computed.
- **Fee and cash:**
  - fee per order = ceil(0.07 x 20 x p x (1 - p) x 100 - 1e-9) / 100 (the sheet's fee_up_order with its own tolerance);
  - cash per contract = win - p - fee / 20.
- **Result:**
  - from the R6 coverage files' result column, or the optional list-results file;
  - a conflict between two non-blank values STOPS;
  - blank and 7 days or more after the close at the block read: VOID, booked at -fee / 20 and counted, NOT scored;
  - blank and under 7 days: the block WAITS (the run stops: "block waits").
  - A value other than yes, no or blank STOPS.
- **Block read:** refused before 2026-11-21T00:00:00Z; now is injectable.
- **Report per place and for the parent:** signals (filled and scored), wins, losses, PF, net and mean per contract, Central days, and the wheel block bar (n >= 60, >= 7 Central days, >= 10 wins and >= 10 losses, PF >= 1.3). Under 100 the label is "no evidence at n = x". Each place also gets the 7g comparison against the parent's scored trades as information: PF +0.10, net per contract-week not lower (weeks over the parent's trades, at least 1), second half not worse (floor(n/2)), 60 signals.
- **Outputs:** a log CSV, one row per window that reached the parent's signal test, plus the printed summary.

## Made-up data (test_oiver_shadow2.py)
- **Clock:** every row has skew 0 and X with fraction .5, so each term is floor(X) + 0.5 - X = 0, the offset is 0 and the exchange time is X.
- **Dates:** OI_NAMED_AT = 2026-11-13T22:00:00Z. Now = 2026-11-21T01:00:00Z. T = 2026-11-15T12:00:00Z (1794744000).
- **Polls:** unless stated, the decision poll is at X = c - 182.5 and the next poll at c - 180.5 with the same book.

| W | close c | OI | YES bids | NO bids | outcome |
|---|---|---|---|---|---|
| K1 | T | 90,000 | 0.20 x 100 | 0.78 x 50, 0.77 x 50 | YES ask 0.22, bid 0.20, spread 0.02, touch 50. All places pass. Fill 20 at <= 0.22 on both polls; p 0.22; fee 0.07 x 20 x 0.22 x 0.78 = $0.24024, so $0.25, 0.0125 a contract. Result yes: **+0.7675** |
| K2 | T+900 | 100,000 | 0.70 x 10, 0.69 x 30 | 0.25 x 200 | YES ask 0.75, NO ask 0.30, so NO at 0.30; spread 0.05; touch (YES bid size) 10. SPREAD skip, DEPTH skip, CAP30 pass (0.30 inclusive). Fill: the YES-bid ladder has asks 0.30 x 10 and 0.31 x 30, only 10 at <= 0.30: **miss_depth** (parent and CAP30) |
| K3 | T+1800 | 95,000 | 0.10 x 100 | 0.88 x 100 | YES at 0.12, spread 0.02, touch 100, all pass. The next poll is at c - 177.5, 5 s later: **miss_no_second_look** |
| K4 | T+2700 | none | 0.20 x 100 | 0.78 x 100 | **no_oi** |
| K5 | T+3600 | 50,000 | 0.20 x 100 | 0.78 x 100 | **oi_below** |
| K6 | T+4500 | 90,000 | blank | 0.78 x 100 | **not_two_sided** |
| K7 | T+5400 | 90,000 | 0.20 x 100 | 0.78 x 100 | polls only at c - 195.5 and c - 170.5: **no_poll** |
| K8 | T+6300 | 90,000 | 0.03 x 100 | 0.94 x 100 | YES ask 0.06, NO ask 0.97, so YES at 0.06: **cheap** |
| K9 | T+7200 | 90,000 | 0.42 x 100 | 0.56 x 100 | YES ask 0.44, NO 0.58, so YES 0.44; spread 0.02; touch 100. SPREAD pass, CAP30 skip, DEPTH pass. Fill p 0.44; fee 0.07 x 20 x 0.44 x 0.56 = $0.34496, so $0.35, 0.0175. Result no: **-0.4575** |
| K10 | 2026-11-13T21:15Z | 90,000 | as K1 | as K1 | D = 21:12 is before COUNT_FROM: **before_count_from** |
| K12 | 2026-11-13T23:00Z | 90,000 | as K1 | as K1 | counts (D 22:57 is after both). Fill p 0.22. Result blank, 7 d 2 h after the close: **VOID**, booked -0.0125, not scored |

Results:
- R6 coverage file: K1 yes, K9 no, K2 no, K3 yes, K12 blank.
- The others have no coverage row and need none, since they are not filled.

### Expected
- **Counts:** windows 11, before_count_from 1, no_oi 1, oi_below 1, not_two_sided 1, no_poll 1, cheap 1; signals 5 (K1, K2, K3, K9, K12); miss_no_second_look 1; miss_depth 1; filled 3; void 1; scored 2.
- **Parent:** n 2, wins 1, losses 1, PF 0.7675 / 0.4575 = 1.677596, net 0.31, mean 0.155, label "no evidence at n = 2", block bar not met.
- **SPREAD:**
  - pass K1 and K9; skip K2 (spread), plus K3 and K12, which pass but miss or are void;
  - scored n 2, PF 1.677596, net 0.31.
- **CAP30:**
  - pass K1, K2 (a miss), K3 (a miss) and K12 (void); skip K9 (cap);
  - scored n 1, PF inf, net 0.7675.
- **DEPTH:**
  - pass K1, K3 and K9 (and K12); skip K2 (depth);
  - scored n 2, PF 1.677596, net 0.31.
- **Place skip counts:** SPREAD spread_wide 1; CAP30 above_cap 1; DEPTH depth_thin 1.

### Refusals expected
- the block read at 2026-11-20T23:00Z
- OI_NAMED_AT not given
- a scored window with a blank result under 7 days old (block waits): K9's result removed and now = 2026-11-21T01:00Z, K9 closing Nov 15
- a result "maybe"
- two non-blank results that conflict
- a HELDOUT_ path

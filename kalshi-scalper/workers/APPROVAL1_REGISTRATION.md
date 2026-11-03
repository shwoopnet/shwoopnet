# APPROVAL1 registration (registered 2026-11-03, before any Kalshi candle, settled value or bracket price for the rule below was downloaded)

Worker APPROVAL1, research session "Strategy Research V2". Discovery only. No live code, no functions/, no L1, no OICORE, no promote verb. N: **+2** (one rule; the coordinator keeps the total, about 730,125 before this, z bar about 5.27).

## Duplicate check (done first)
Read: README PUB1/APP1 (2026-10-21), COUNT1, COUNT2, ELECT1, NOWCAST1, USWEEP1/2 politics rows, workers/AUDIT1_REPORT.md (politics lane: 15M contracts, 3 families, "no approval or poll-average market has been tested"; that sentence is wrong for APP1) and workers/OICORE_SHAPE_INVENTORY.md.
**Overlap, disclosed:** APP1 (README, "Results: GAS1, APP1 and CMD1") already priced `KXTRUMPAPPROVE` with a random-walk model on the previous RCP value, trading ALL sides, 97 entries on 27 days, NOT_ENOUGH_DATA, Brier model 0.0926 vs market 0.0746. APPROVAL1 is NOT that rule: it is cheap-side only (ask 3c to 30c, hard limit 0.30), requires model probability >= 3x the ask, uses a 30 day sigma, max 2 per event, and a control of all cheap sides. It reuses the idea (so the try count is honest: +2) but not the entry rule. What I saw of APP1 data: aggregate results and two settled values (38.8, 39.6) in the README; no per-bracket cheap-side outcome. The Aug 14 to Oct 20 period it covered is inside the development span below, so it is not clean out of sample; the frozen third (below) is.

## Candidate table (metadata from the public series list and one active market's rules text; no outcomes)
| Series | Settles on | Cadence | Source reachable keyless from this sandbox, same as settlement? | Verdict |
|---|---|---|---|---|
| **KXTRUMPAPPROVE** | RealClearPolitics "RCP Average" Approve column, table "President Trump Job Approval", exactly 1:00 PM ET | daily, below / between / above brackets | RCP pages return HTTP 403 (bot block) from this sandbox; I do not circumvent. The running value is instead Kalshi's own `expiration_value` of the previous daily event (the value of the same RCP cell one day earlier), which is the settlement source by construction | RUN (source = Kalshi's recorded RCP cell) |
| **KXVHGCB** | VoteHub 2026 generic ballot margin (D minus R, time-weighted), exactly 5:05 PM ET | daily brackets | VoteHub web page is Cloudflare-blocked (403); `api.votehub.com/polls` is reachable but returns individual polls, not the site's time-weighted average, so a rebuild cannot be the same source. Running value = previous event's `expiration_value` | RUN only if >= 25 scored event-days exist, else NOT_ENOUGH_DATA |
| KXAPRPOTUS / APRPOTUS | RCP approval, weekly | weekly | one event a week | alternate, not run (too few events per month; same source as KXTRUMPAPPROVE) |
| KX538APPROVE | FiveThirtyEight | weekly | 538 shut down in 2025; series stopped | NOT_RUNNABLE |
| KXNYTTRUMPAPPROVAL, KXTRUMPGALLUP50 | a single qualifying poll / Gallup | annual / one-off | too few | NOT_RUNNABLE |
| KXSILVERAPPROVALMUSK | Silver Bulletin Musk approval | custom | page reachable (HTTP 200) but series is a handful of one-off events | NOT_RUNNABLE |
| Silver Bulletin Trump average | not a settlement source of any daily series found | | reachable, but no Kalshi series settles on it | not used |

Up to 2 series are run: KXTRUMPAPPROVE and KXVHGCB.

## Source-consistency gate (run FIRST, before any model or price)
The COUNT1/COUNT2 lesson. Because the external aggregator cannot be reached, the gate is internal and weaker, and I say so: for every settled market, (a) the winning side must agree with its own `expiration_value` against its floor/cap (the bracket the value falls in wins) for >= 90% of settled markets, and (b) the previous-day value must exist for the scored day (the previous event closed 24 h +- 1 h earlier and 21 earlier consecutive daily values exist). If (a) is below 90% the series is `SOURCE_MISMATCH` and stops. This does NOT prove Kalshi's recorded value equals RCP's page at that time; it proves Kalshi's markets are internally consistent. Verdict wording must carry "source = Kalshi expiration_value, external RCP unreachable".

## Span and frozen third (by date only, fixed now)
Span = from max(first settled close of the series, 2026-05-01) to 2026-11-02 UTC. Frozen = the last third of those calendar days: not fetched for scoring, not read, not tuned on; scored once, only if the development verdict is not FALSIFIED. W1 and W2 = the first and second halves of the first two thirds by date.

## Rule (one, fixed)
- Brackets: below c (value < c - 0.05), exactly x (x - 0.05 to x + 0.05), above f (value > f + 0.05), on the 0.1 grid as APP1 (KXVHGCB: grid read from floor/cap spacing; same half-step correction = half the smallest strike gap).
- Look: the last hourly candle (ask and bid, from the one-minute batch endpoint aggregated to the last quote in each hour) ending at or before close minus 23 hours, i.e. one hour after the previous event settled (the previous value is then public). If no quote at that look, the market is not scored.
- Model: mu = V_prev (the previous event's expiration_value), no drift; sigma = population standard deviation of the last 30 daily changes of the value, floor 0.15 (KXTRUMPAPPROVE) and 0.25 (KXVHGCB), Normal. Bracket probability from the normal CDF with the half-step correction. Nothing fitted.
- Cheap side only: for each market consider YES at its ask and NO at (1 - yes bid); a side is eligible if its ask is 0.03 to 0.30 (hard limit 0.30, no price above is ever bought). Buy it if model probability of that side >= 3 x its ask. At most 2 per event (largest ratio first, ties by ticker). Held to settlement, 1 contract.
- Fee 7% x C x p x (1 - p), rounded up to the cent per contract, C = 10 (stress x1.2 reported).
- Control: every eligible cheap side at the look, with no model filter, same fee.
- No favourite-side result is computed or printed anywhere (owner rule, Nov 3).

## Numeric prediction (before any data)
Entries per series on the development span: 30 to 90 (about 0.5 a day); pooled under 150 with about 90% probability. Win rate about 5% to 9% at mean price about 0.12; mean net after fee between -4c and 0c per contract; profit factor about 0.4 to 0.9; treated not above control. FALSIFIED or NOT_ENOUGH_DATA together about 97%.

## Kill rules and verdict words
- FALSIFIED if mean net per contract after fee is not above 0 in both W1 and W2, or profit factor under 1.5, or treated mean not above control mean.
- NOT_ENOUGH_DATA if fewer than 150 trades: report trades, event-days, and days-to-go to 150 at the observed rate, and register a dated forward freeze: the same rule applied unchanged to events closing on or after 2026-11-04, read once on or after the date the observed rate gives 150 trades (and never before 2026-12-31), using recorded quotes only.
- SOURCE_MISMATCH if the consistency gate fails.
- No promote verb. Positive in both halves with a mechanism would only mean a capped-probe spec, written for the owner, not built.

## Data handling
One thread, sleeps, backoff, md5-rank stratified sample if the fetch is too heavy, cache outside the repo (research scratchpad), tracked background fetch. Code `src/scalper/approval1.py` plus tests; results to `README.md` and `workers/APPROVAL1_RESULT.md`.

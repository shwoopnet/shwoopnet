# APPROVAL1 result (2026-11-03; rule, bars and kills exactly as in workers/APPROVAL1_REGISTRATION.md, registered in commit 73756bb before any data)

**Verdict: NOT_ENOUGH_DATA** (6 trades on 5 event-days against a registered minimum of 150). Nothing was changed after seeing data. N: +2.

## What exists (the real series, found by title on the public list)
| Series | Settles on | Settled history Kalshi serves | Dev span used | Scored events |
|---|---|---|---|---|
| KXTRUMPAPPROVE | RCP Average, "Approve", 1:00 PM ET | first settled event 2026-09-02 (41 events, 369 markets; the ladder was restarted, earlier markets are not listed) | 2026-09-02 to 2026-10-12 (frozen from 2026-10-13, never requested) | 20 (needs 21 earlier consecutive daily values) |
| KXVHGCB | VoteHub time-weighted margin, 5:05 PM ET | first event 2026-09-25 (26 events, 232 markets) | 2026-09-25 to 2026-10-20 (frozen from 2026-10-21) | 0 (two 26 hour gaps break the chain; fewer than 21 values anyway) |
| KXAPRPOTUS, KX538APPROVE, KXNYTTRUMPAPPROVAL, KXTRUMPGALLUP50 | RCP weekly, 538 (closed), NYT, Gallup | weekly / one-off / ended | not run | |

## Source consistency
External sources: RCP and VoteHub web pages return 403 (bot protection) from this sandbox and were not circumvented; `api.votehub.com/polls` is reachable but returns individual polls, not the site's time-weighted average, so it cannot rebuild the settlement value. Silver Bulletin's page is reachable but no Kalshi daily series settles on it. So the external check was NOT possible. The internal gate (the winning side agrees with the market's own `expiration_value` against its floor/cap) passed: KXTRUMPAPPROVE 369 of 369, KXVHGCB 225 of 225 markets (100%). That proves Kalshi's markets are internally consistent, not that the recorded value equals RCP's page; every statement below carries "source = Kalshi expiration_value".

## Result (cheap side only; a favourite-side number is not computed anywhere)
| | n | event-days | win | mean price | net per contract | PF |
|---|---|---|---|---|---|---|
| KXTRUMPAPPROVE treated (model p >= 3 x ask, max 2 per event) | **6** | 5 | 0.0% | 0.072 | -7.67c (x1.2 fees: -7.70c) | 0.00 |
| W1 / W2 | 0 / 6 | | | | n/a / -7.67c | |
| Control: every cheap side (3c to 30c) at the look, no model | 148 | 20 | 7.4% | 0.111 | **-4.36c**, day-clustered z -3.64 | **0.59** |
| KXVHGCB | 0 | 0 | | | | |

The treated set is far too small to say anything (6 losses at 7c is just what 7% win rate predicts; z -1.9 on 5 days). The control is informative only as description: the whole cheap-side set of this ladder lost 4.4c a contract on 20 days, PF 0.59, which is the registered prediction (win 5% to 9%, price about 0.12, PF 0.4 to 0.9). Why so few treated trades: with a 30 day sigma floored at 0.15 and the price already inside a strike, a cheap bracket rarely carries model probability of 3x its ask.

## Days to go
Rate 6 treated trades per 20 scored events = 0.3 per day, so 150 trades needs about **500 days of events** (roughly early 2028) at this ladder's one event a day. KXVHGCB has no scored history yet and would add about the same rate. The registered forward freeze (same rule, events closing on or after 2026-11-04, one read on or after 2026-12-31) will not reach 150 by then; it is recorded as a dated freeze only, with no one scheduled to run it. The frozen third (KXTRUMPAPPROVE from 2026-10-13, KXVHGCB from 2026-10-21) is untouched and unscored; not unlocked because the development verdict is not a pass.

## Probe spec
None. Nothing is positive in both halves, and there are no half-results.

## Reproduce
`cd src && python -m scalper.approval1 fetch|gate|run` (cache `APPROVAL1_CACHE`, default the research scratchpad), tests `tests/test_approval1.py`. N: +2 (running about 730,127).

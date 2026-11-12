# MMSIM1: the fill rule leaves out the fills a resting order cannot avoid (Idea Desk A, Nov 12, 2026)

Public market data only (`quote-data:book/`, the hourly Bitcoin ladder books and tape). **Development events only**: the 168 quotable hourly events closing before the pinned cutoff `2026-11-07T15:00:00Z`; every later row is dropped at load and the held-out block was not opened. Zero Kalshi requests. No live account figure. Scripts: `workers/desk_a_fillmodel/` (run each as `python3 -I <script> <folder holding book/>`).

## Result

MMSIM1's development profit factor of 1.41 depends on its fill rule. That rule fills a resting bid only when enough contracts trade AT our exact price to clear the visible queue ahead of us. It never fills us when the market trades THROUGH our price. An exchange fills the best price first, so if a contract trades below our bid, or the best bid on our side falls below our price, an order that is never cancelled or repriced has been filled. With those fills put back, the same registered quoting rule on the same events loses.

| Fill rule (everything else as registered) | Legs filled | Pairs / one-sided / none (of 1,113 strikes) | PF, unrounded fee | PF, one-contract rounded fee | Mean per event | Total, one lot | Mean per one-sided strike | Positive days |
|---|---|---|---|---|---|---|---|---|
| Registered: queue cleared at our price only | 35.5% | 174 / 443 / 496 | 1.41 | 1.26 | +3.5c | +$5.84 | +0.9c | 8 of 10 |
| Plus: a taker trade prints through our price (tape) | 89.0% | 889 / 203 / 21 | 0.17 | 0.16 | -20.1c | -$33.69 | -21.0c | 1 of 10 |
| Same, ignoring through trades in the first 5 s after posting (clock guard) | 85.0% | 825 / 242 / 46 | 0.29 | 0.28 | -16.4c | -$27.62 | -14.9c | 1 of 10 |
| Plus: best bid on our side falls below our price (book only, no tape) | 90.6% | 903 / 210 / 0 | 0.18 | 0.17 | -18.4c | -$30.98 | -19.1c | 1 of 10 |
| Plus: book and tape must both show it | 88.8% | 885 / 207 / 21 | 0.16 | 0.16 | -20.6c | -$34.65 | -21.1c | 1 of 10 |

Cross-checks: of the legs whose level was emptied according to the book, 97.4% also show a tape trade through the price; of the legs with a tape trade through, the book's best bid is below our price 3 seconds later in 88.7%. The recorder's level 1 is always the best bid (checked on a sample file: 24,360 rows, none out of order).

**Shape of the loss.** About 890 strikes become a filled pair (+1c each, about +$9); about 210 stay one-sided and lose about 19c to 21c each (about -$40). Under the book rule the per-event result is mean -18.4c, standard deviation 63.2c, worst -$3.13, best +$0.09 (event z about -3.8).

**Why the registered rule looked good.** Its fills are the ones that happen while the price is still at our level; the price then, on average, comes back (our side's mid is 0.76c lower one minute after a queue fill and about flat at five minutes). The fills it leaves out happen when the price leaves, and those do not come back. The protocol's line "queue shrinkage from cancels is ignored (conservative, fewer fills)" is right about the count and wrong about the money.

**Ownership.** This desk's Nov 12 verification (`DESK_A_VERIFY_NOV12.md`) confirmed the arithmetic of the registered rule and did not question its fill rule. The 1.41 reproduces; it is not a number to act on.

## Other facts about fills (registered fill rule, for the record)

- Queue ahead at posting: median 1,265 contracts (quartiles 475 and 2,716). Fill rate 63% in the lowest third of queue (754 or fewer ahead), 31% in the middle, 12% in the top third.
- Wait to a queue fill: median 5.2 minutes; 25% inside 60 seconds.
- If the volume needed were half the visible queue (cancels ahead), 52% of legs fill; 1.5 times, 27%; twice, 23%.
- 48% of queue fills are completed by a fractional-size taker. Five minutes after such a fill our side's mid is +1.8c above our price; after a whole-number taker's fill, +0.0c.

## What follows (recommendations; the decisions belong to the Head of R&D, V2 and Main)

1. No live MMSIM1 probe, including a "fill test": it would pay about 20c an event to learn a fill rate the recorded book already shows (about 90%, not 36%). A tripwire of "60% or more of legs filled" would fire after one event 95% of the time.
2. Amend MMSIM1 before the Nov 24 read: report the held-out under both fill rules and judge on the price-priority one. Under the registered fill rule the read is uninformative either way.
3. MMHOUR1 and MMPOWER1 use the same base rule and inherit the same problem. ORHARVEST1 and RACEMAKE1 (this desk's resting-order cards) must be simulated under price priority from the start.
4. A maker rule worth a forward record has to cancel or reprice. It does not exist yet; it needs a pre-registered design pass on these 168 events under the honest fill rule first.

## Limits

One regime (10 days). Fills are timed from a 30 second tape and 3 second books; a real order's queue position, and whether a post-only order is accepted, cannot be seen in public data. None of these can turn the through fills into non-fills. The price-priority rules here are a correction to the fill model of the one registered rule, on development data; no new strategy variant was scored and no try is claimed.

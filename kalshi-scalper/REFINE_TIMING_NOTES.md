# Why Dogecoin orders go out late in the minute, and what a fix would touch (read only; Oct 30, 2026, 8:15 PM CT)

Requested by the owner via the main session. I read `functions/index.js` (`kalshiLiveArmed`, line 585 on) and `functions/kalshiLiveLib.js` (`runL1Tick`, line 842 on). I changed nothing. A trading change is its own pull request from the main session after the owner approves.

## What I measured (R5 lead, not yet a finding)

An order is stamped with `ts`, which is the moment the minute function STARTED (`const now = Date.now()`, index.js line 597), not the moment the order was sent. For a 6 minute entry, "355 seconds or more left" means the function started 0 to 5 seconds after the clock minute, and "345 to 355" means it started 5 to 15 seconds after it.

Dogecoin, 6 minute entries, report rows to Oct 30: started in the first 5 seconds, 104 orders, 21% no fill; started 5 to 15 seconds late, 73 orders, 43% no fill. Gold shows no difference (36% in both). The split was chosen after I looked, so it is a lead; R5 scores it forward (100 orders per arm, orders after Oct 30 7:30 PM UTC).

## What happens in one minute (in order)

1. Cloud Scheduler fires the function once a minute. Start time varies by seconds (scheduler jitter and, on a cold instance, startup). `now` is taken after one Firestore read (the arm document).
2. Session document read. Then `loadQuotes` reads the market lists one series after another, and the other L1 series (Dogecoin, Ethereum, XRP) are added by a second loop of one-at-a-time reads (index.js lines 614 to 621). Each is a network call, one after the next.
3. `runL1Tick` preamble, all one after the other: halted check, unresolved-order check, the last 24 hours of orders (cached), the balance call to Kalshi, the bot's risk figures, the sizing document, a probe-record transaction.
4. Candidates are tried one at a time in list order: gold first, then Dogecoin (paused markets are skipped). For EACH candidate: a fresh `GET /markets/{ticker}` (this is the price the order uses), the band check, the window cap arithmetic, a second halted check, the Firestore write that creates the order record (`createTest`), then the order POST to Kalshi, then three more writes (`updateTest`, `setSession`, the event log).
5. So when gold and Dogecoin are both in the entry window in the same minute, Dogecoin's market read does not start until gold's whole cycle has finished: gold's read, record write, POST, and three writes.

Two separate delays follow from this:
- Before any order: the start lag (step 1) plus steps 2 and 3. Every market pays this.
- Dogecoin only: it also waits for gold's cycle (step 5), and Dogecoin's price is read fresh AFTER that wait, so the price is current, but the order then sits in `createTest` and the POST while a thin book (about 100 contracts at the touch) moves.

I cannot say which step costs the 5 to 15 seconds: the order record keeps only `ts` (function start) and no send time. That is the first thing to find out.

## What a fix could change (options, smallest first)

1. **Log only, zero trading risk:** record the time each order is sent (`sentAt`) and the time its market read finished, on the order document. Then the report can show exactly where the seconds go. This reads no new data and decides nothing.
2. **Keep the function warm** (a minimum instance for `kalshiLiveArmed`). Removes cold start lag. A deploy setting, small cost per month (a warm 256 MiB instance, about a few dollars).
3. **Read the market lists in parallel** (`Promise.all`) in step 2 and the independent preamble reads in step 3. Does not change any rule, only when the first order can start. Saves seconds.
4. **Move the after-order writes** (`setSession`, the event log) to after all orders are sent. Gold's cycle then ends sooner and Dogecoin starts sooner.
5. **Send gold and Dogecoin together** (read both markets, then both orders at once). The biggest gain for Dogecoin and the one that touches the most rules (see below). Not recommended before 1 to 4 and R5.

## What each could break (the risks)

- **Order size lock and sizing:** `maxContractsFor` is checked per order and reads only code constants, so reordering reads does not change it. Size follows `cashLeft`, which subtracts what earlier orders in the same minute committed (`committed`, line 961). Options 1 to 4 keep that order intact. Option 5 breaks it unless the cash accounting is made safe first.
- **Window cap (5.5%):** `windowSpent` and `windowUsed` (lines 963, 1002) are updated order by order, so the second order sees the first. Sending both at once would let both pass the check on the same room: a possible breach of the cap by one extra order. Option 5 needs a combined check before either order goes.
- **Double-order protection:** each order has the id `L1-<ticker>` and `createTest` creates the record in a transaction, so a second send for the same market is refused ("already attempted"). That protection is per market and survives options 1 to 5. A second instance of the function running at once (a slow start overlapping the next minute) is covered by the same transaction, but a slower tick makes overlap more likely, so option 2 helps there too.
- **Halted and direction lock:** both are re-read right before the order is recorded. Any reordering must keep that read between the market read and the POST.
- **Fail-closed behaviour:** an unreadable balance, orders list or risk figure stops the tick before any order. Parallel reads must keep that: if any one fails, nothing is sent.
- **The exit watch** is a different function and is not touched by any option.
- **Quote freshness vs speed:** a faster order is based on a fresher price, which is the point. But sending earlier in the minute is also earlier in the 6 minute window; the registered rule's "6 minute look" would shift by a few seconds. The history for 6 minutes was measured on candles ending exactly 360 seconds before the close, so an order a few seconds earlier is closer to that than one a few seconds later.

## Recommendation

Do option 1 (log send time) now: zero risk, and it turns the lead into a measurement. Let R5 count to 100 per arm. If the late start is mostly scheduler start lag, option 2 is the fix. If it is mostly gold's cycle ahead of Dogecoin, options 3 and 4 first. Do not do option 5 without a combined window-cap check, and only if the owner wants it. I propose none of this as a live change; it needs the main session's pull request and the owner's approval.

Frequency note: this is the one lever I found that raises fills without paying more per contract: the 22 point no-fill gap for Dogecoin is about 8 to 12 extra fills a week if the slow starts could be made fast (73 late orders in about 10 days, about half of which might fill).

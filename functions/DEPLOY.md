# Deploying the Finnhub proxy

This replaces the hardcoded Finnhub API key that used to live in plaintext in
`index.html` (visible to anyone who read the page source or the public repo,
and shared/rate-limited across every browser that loaded the site). Market
data calls now go through these four Cloud Functions instead of straight from
the browser to Finnhub.

## One-time setup

1. **Firebase CLI**, if you don't have it:
   ```
   npm install -g firebase-tools
   firebase login
   ```

2. **Blaze plan required.** Cloud Functions (2nd gen) need billing enabled on
   the `shwoopnet` Firebase project, even though actual usage here is tiny
   (well within the free monthly quota). Enable it at
   console.firebase.google.com → shwoopnet → Upgrade, if not already on Blaze.

3. **Store the Finnhub key as a secret** (this is the same key that used to
   be hardcoded — grab it from your Finnhub dashboard or the old commit
   history if you don't have it handy):
   ```
   firebase functions:secrets:set FINNHUB_API_KEY
   ```
   Paste the key when prompted. It's stored in Google Secret Manager, not in
   this repo.

## Deploy

From the repo root:
```
firebase deploy --only functions
```

This deploys two callables: `finnhubQuote` and `finnhubCompanyNews`. Each one checks that the
caller has a real signed-in Firebase Auth token (matching firestore.rules'
own model: any account with a real `users/{uid}` document, not one specific
owner email) before it will spend the Finnhub key on a request — so the
function URLs being technically public doesn't open the key back up.
Account creation itself is invite-gated (see firestore.rules), not these
functions.

## After deploying

Nothing else to change in `index.html` — it's already wired to call these
functions via the Firebase SDK (`window.__shwoopAPI.finnhubQuote(...)` etc. in
the `<script type="module">` block). Reload the deployed page and the Brief
page / quote loop should pull data through the proxy automatically. Check the
Functions logs (`firebase functions:log`) if something doesn't load — a 403
there means the request had no signed-in token at all, not a Finnhub
problem.

## If you'd rather not deploy this yet

The old direct-to-Finnhub code path has been fully removed from `index.html`,
so until this is deployed, the Brief page's quotes/news/earnings and the
per-trade news alerts will fail closed (console errors, "Couldn't load..."
placeholders) rather than silently falling back to the old exposed key.

## Kalshi page (admin only)

- **Live books** (`kalshiBooks`, a read-only callable) requires the owner's email AND
  `isAdmin: true` on the user document. It tries `external-api.kalshi.com`, the host Kalshi's
  docs give, and falls back to `api.elections.kalshi.com`. The first works from Google Cloud
  (confirmed 2026-10-05); the second sits behind a CDN that refuses Google Cloud addresses
  (HTTP 403). If a refusal ever returns, the status line names each host and what it said.
- **Journal.** A field (`kalshiJournal`) on the admin's own user document. It needs no function:
  `firestore.rules` refuses a non-admin write to it, so it is protected only once the rules
  are deployed.
- **History for research** is fetched with `kalshi-scalper` (`python -m scalper.backfill`)
  and analysed there. Nothing on Firebase records it.

Deploy functions and rules together:
```
firebase deploy --only functions,firestore:rules
```

## Retired: the Kalshi paper bot (removed Oct 7, 2026)

The simulated bot (`kalshiBot`, `kalshiBotRun.js`, the alert module and their collections) is gone from the code. It made
SIMULATED trades from Kalshi's public prices and proved nothing about the strategy. What remains from it is the entry
signal the live test uses (`kalshiSignalLib.js`) and the halt switch (`kalshiBotMeta/control`, whose path is kept so your
saved setting survives). Cleanup on your side, once the new code is deployed:
```
firebase deploy --only functions,firestore:rules
firebase functions:delete kalshiBot --region us-central1
```
The old records (`kalshiBotPositions`, `kalshiBotEvents`, `kalshiBotMeta/status`) are no longer readable from the page. Delete
the collections in the Firebase console if you want them gone; nothing reads them.

### The outside watchdog now watches the live arm

`kalshiLiveArmed` runs every minute whether or not it is armed, and pings an outside dead-man's switch after every completed
run. A run that throws sends the failure ping instead, and still fails. The service alerts when the pings stop. Setup is the
same as before: a healthchecks.io check with period 1 minute and grace time 5 minutes, then one line in the gitignored
`functions/.env`: `KALSHI_WATCHDOG_URL=https://hc-ping.com/<uuid>`, then `firebase deploy --only functions`. Leave it unset and
nothing is sent. A failed ping never affects the arm check. The URL lets anyone ping your check, so keep it out of git and chat.
Real orders are covered in the live test sections below and in `kalshi-scalper/README.md`.

## Retired: the Kalshi demo test trader (removed Oct 7, 2026)

The website's demo trader (`kalshiDemoTrade`, its page card, `kalshiDemoLib.js` and the `kalshiDemoOrders`
collection) was removed once live testing began; it had proved signing, shards, the duplicate-order refusal and the
order shape on Kalshi's demo exchange. The research CLI (`kalshi-scalper`, `python3 -m scalper.demo`) and its README
record are kept. Cleanup that code cannot do, once, by hand:

    firebase functions:delete kalshiDemoTrade --region us-central1     # the deployed function
    firebase functions:secrets:destroy KALSHI_DEMO_KEY_ID              # then the same for KALSHI_DEMO_PRIVATE_KEY

Also delete the demo API key on Kalshi's demo site (it was pasted into a chat once), and, if you want the old rows
gone, the `kalshiDemoOrders` collection in the Firebase console.

## Kalshi LIVE test order (ONE contract, REAL money)

Step 1 of the owner's decision (2026-10-07) to put $100 to $150 of real money behind this. It proves the
live path with one contract, and it is not the bot: `kalshiLiveTrade` sends at most ONE Bitcoin or gold contract,
$2.00 cap including the fee, immediate-or-cancel, to the PRODUCTION host only. It is admin only, takes nothing
from the page, and refuses unless ALL of these hold: the switch is on, the exchange is trading, the bot is not
halted (the control document must say `halt: false` explicitly, so press Halt then release it once if the
document has never been written), no earlier live test is unresolved, fewer than 2 today and 5 ever, the
live price has not moved more than 2c since the signal, and the balance on THIS market's shard covers it
(money on another shard does not count: move it in the Kalshi app first; a signal whose shard is empty is skipped
for the next signal, and gold and Bitcoin usually sit on different shards, so fund both if you want both).

It is never retried. If Kalshi's answer is lost the record is marked `unknown`, the page says the order may or
may not exist, and further live tests are blocked until you look at the account (Portfolio, Orders) and set that
record's `status` to `resolved` by hand in the Firebase console.

To turn it on, in this order, and not before:

1. Create a Kalshi PRODUCTION API key with trading permission only (no withdrawals). Never paste it in a chat.
2. `firebase functions:secrets:set KALSHI_LIVE_KEY_ID` and
   `firebase functions:secrets:set KALSHI_LIVE_PRIVATE_KEY --data-file <path to the pem>`, then delete the file.
3. Put `KALSHI_LIVE_ENABLED=on` in `functions/.env` (gitignored). Without it the function refuses everything.
4. `firebase deploy --only functions:kalshiLiveTrade,firestore:rules`, then merge/deploy the page.
5. Press the button on the Bot tab and check the order in your Kalshi account. Set the switch back to `off` after.

### Armed live test: click once, it scans, sends ONE order, switches itself off

The page card has an "Arm automatic scan (3 hours)" button (two clicks). Arming only flips a control document
(`kalshiLiveControl/arm`, written by the `kalshiLiveArm` function with a server-set expiry; the page cannot write it).
A scheduled function, `kalshiLiveArmed`, runs every minute and does nothing at all unless that document says
armed and unexpired. When it is, it makes one ordinary live test attempt with every guard above. One arming can
place at most ONE order: it switches off as soon as an order is sent (filled or not), or refused, or its answer
was lost, on any error, and after 3 hours. A refusal before sending (no signal, price moved, shard empty) leaves
it armed to try again next minute. The last scan's result is shown on the card. The position closes by
settlement at the end of its 15 minute market; no exit order is placed.

The signal price comes from Kalshi's market list, which lags the single-market read by about 2c, so the live test
re-reads the market and requires the price it would actually pay to be inside the 40c or 50c band (and within 5c
of the signal). Deploy with `firebase deploy --only functions:kalshiLiveTrade,functions:kalshiLiveArm,functions:kalshiLiveArmed,firestore:rules`.
`kalshiLiveArmed` and `kalshiBookRecorder` are the only scheduled functions; the tests name exactly those two.

### Kalshi account panel (read only)

The Bot tab's "Kalshi account (live, read only)" card has a Refresh button. `kalshiLiveAccount` (admin only, takes
nothing from the page) reads `/portfolio/balance`, `/portfolio/positions` and `/portfolio/fills` with the live key and
shows balance per shard, open positions and recent fills. GET only, no order code (`kalshiAccountLib.js`, a test
asserts it), and it works whether or not `KALSHI_LIVE_ENABLED` is on. Each part shows its own error, and a response
shape it does not recognise is listed by field name. Deploy with
`firebase deploy --only functions:kalshiLiveAccount`. It is the quickest way to see whether your funds sit on the same
shard as the market (Bitcoin and gold were both on shard 2 when last checked) without waiting for a scan to refuse.

#### Start fresh from now (the account is shared with your own trades)

Kalshi cannot separate the owner's personal trades from the bot's on one account, and nothing on Kalshi can be erased.
"Start fresh from now (one time)" on the account card draws a permanent line instead: it records the time and the
current total balance in `kalshiLiveControl/baseline`, written once with `create()` so it can never be overwritten
(a second press just shows the existing line). From then on the account view hides fills before the line and shows
the balance as a change from the starting balance (it includes any deposit or withdrawal after the line). Press it
only after your last personal trade. To move the line, delete that one document in the Firebase console.
Deploy with `firebase deploy --only functions:kalshiLiveAccount,functions:kalshiLiveBaseline`. The bot's own journal and
the live test records were never mixed with personal trades, so only this view needed the line.

### The Bot tab now shows the live account (Oct 7, 2026)

The Bot tab used to show a simulated bot (status, totals, positions, trades, event log). It now shows the live account:
a status card (balance by shard, whether the server's order switch is on, armed or not, the last scan's result, the
halt state with its button), totals since your "start fresh" line (starting balance, now, change, how many orders the
bot sent and how many filled), open positions, recent fills labelled bot or manual (matched by the order id the bot
saved), and a log of what the live bot did. The account is read when the tab opens and once a minute while it stays
visible: three GET requests, read only. Without a starting line the totals say so instead of guessing.

- The halt button is the live kill switch: the live test and the armed scan refuse while halted. If the halt setting
  was never saved, the scan treats that as halted and the card says so: press Halt, then Resume, once.
- New collection `kalshiLiveEvents` (armed, disarmed, scan ended), written only by the server; admin read in the rules.
  Minutes with no signal are not logged (the last scan's result is on the card).
- Deploy: `firebase deploy --only functions:kalshiLiveAccount,functions:kalshiLiveArm,functions:kalshiLiveArmed,firestore:rules`.
  Do it when the scan is not armed: redeploying `kalshiLiveArmed` restarts it for a moment.


## Order-book recorder (`kalshiBookRecorder`, read only)

Scheduled once a minute; inside each run it takes about 5 snapshots, 10 seconds apart, of the real
order book of the open Bitcoin and gold 15 minute markets. No key, no order code, no secrets.
One Firestore document per minute (`kalshiBookSnaps/bk-<minute>`, admin read only), 10 days kept,
and a heartbeat at `kalshiBookMeta/status` (`lastTickMs`, `snaps`, `errs`). About 1,440 writes a day.

    firebase deploy --only functions:kalshiBookRecorder,firestore:rules

This replaces the old Firebase recorder removed on 2026-10-05, which only reached the host Kalshi's
CDN refuses from Google Cloud. `external-api.kalshi.com` works from there (the bots use it), and the
status doc shows errors per minute if that ever changes. Stop it with
`firebase functions:delete kalshiBookRecorder --region us-central1`.

## The 24 hour L1 session (Oct 7, 2026)

The owner's automatic run of strategy L1 in the live account. The terms are in `kalshi-scalper/README.md` under "Live waiver: L1 for
24 hours", written before the code. L1 failed its own bar, so this is a decision to run it, not evidence that it works.

- **What it does.** About 6 minutes before each Bitcoin or gold 15 minute close (330 to 400 seconds left), it re-reads the market and,
  if a side's fresh price is 88c to 97c, buys ONE contract at the touch, immediate-or-cancel, and holds it to settlement. One order per
  market (id `L1-<ticker>`, record created first), production host only, never retried.
- **Limits in code** (`kalshiLiveLib.js`): $2.00 per order, 24 hours, a 200 order backstop that a 24 hour session cannot reach (192 markets a day), and the session ends when the BOT's own filled trades are down $7.00
  (settled results plus every unsettled trade counted as lost, at the order's worst-case cost). Your manual trades on the same account
  neither trip it nor hide a bot loss. If the bot's trades cannot be read, nothing is sent that minute. It also ends on the first order whose answer is lost or
  refused, and while an earlier order is unresolved. The server switch, the halt switch and the shard balance all still apply.
- **Start and stop** from the Bot tab ("24 hour L1 session", two clicks to start). It cannot run beside a single armed test order, and
  each refuses to start while the other is on. The scheduled `kalshiLiveArmed` function runs it every minute and pings the watchdog.
- **Deploy:** `firebase deploy --only functions:kalshiL1Session,functions:kalshiLiveArm,functions:kalshiLiveArmed,firestore:rules`.
  `KALSHI_LIVE_ENABLED` must be `on` in `functions/.env`. Its orders appear in the same list as the test orders, so they count toward the
  one-contract test's limit of 5 ever; after a session the single test button will say the limit is reached.
- **Reading it.** Net result after fees plus the counts of fills, no fills and refusals. About 55 trades a day, so a day is noise (plus or
  minus about $2); it tests fills, fees and timing.

## Account snapshot (Oct 7, 2026)

`kalshiLiveArmed` now also stores the same read the account panel makes (balance per shard, positions, fills and
settled results) in `kalshiLiveControl/account` at minutes 1 and 10 of each quarter hour (just after a market settles and just after the entry window), or when none exists or it is 20 minutes old, after the order logic has run. The Bot tab shows it
the moment it opens, so the panel is current even if the page was closed. A failed snapshot is logged and never fails
the run, the session or the watchdog ping. Cost: one small Firestore read a minute, and about 3 Kalshi reads plus up to 20 public market reads twice per quarter hour. Deploy: `firebase deploy --only functions`. No rules change (the document is admin read, server write).

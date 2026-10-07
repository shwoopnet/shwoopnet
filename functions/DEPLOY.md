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

## The Kalshi paper bot (server side)

`kalshiBot` is a scheduled function that runs once a minute, makes SIMULATED trades
from Kalshi's public prices with $100 of paper capital, and writes its state to
Firestore. It cannot place a real order: nothing in it signs a request or calls an order
endpoint, and a test asserts that. Deploy it together with the rules, because the rules
are what keep its records readable by the admin only:
```
firebase deploy --only functions,firestore:rules
```
The first deploy of a scheduled function enables Cloud Scheduler and may ask a question
or two about APIs; answer yes. After about a minute the **Bot** tab on the Kalshi page
shows `Bot: OK`. If it still says "Not running yet" after three minutes, read the log:
```
firebase functions:log --only kalshiBot
```

- **State** lives in `kalshiBotPositions`, `kalshiBotEvents` and `kalshiBotMeta`. Only the
  function writes them (the Admin SDK bypasses the rules). The one thing the page may
  write is `kalshiBotMeta/control`, the halt switch.
- **A double fire cannot enter a market twice.** A position is created with `create()` under
  an id derived from the market, which fails if it exists; a close happens inside a
  transaction that re-checks the position is still open.
- **Cost** (a projection, not a measurement): about 43,000 invocations a month against 2
  million free, roughly 1,500 Firestore writes and 10,000 reads a day against a daily free
  allowance of 20,000 and 50,000 that the rest of the app shares. Set a budget alert and
  look at usage after a week.
- **Alerts.** The page shows the bot as OK, STALE (2.5 minutes of silence) or DOWN (5), but
  only while the page is open. For an alert that reaches a phone, the bot pings an outside
  dead-man's switch every healthy minute, and that service alerts when the pings stop.
  Setup (about five minutes):
  1. Make a free account at healthchecks.io and add a check with period 1 minute and grace
     time 5 minutes. Add a notification channel (email, or their phone app, SMS or Telegram).
  2. Copy the check's ping URL (it looks like `https://hc-ping.com/<uuid>`).
  3. Create `functions/.env` (it is gitignored) containing one line:
     `KALSHI_WATCHDOG_URL=https://hc-ping.com/<uuid>`
  4. `firebase deploy --only functions`.
  The bot sends no ping when it cannot read Kalshi's prices, so a stuck feed alerts too. It
  also sends one failure ping when the day's -5% stop is hit (expect a "back up" notice a
  minute later). Leave the URL unset and nothing is sent. A failed ping never affects the
  bot. The URL lets anyone ping your check, so keep it out of git and chat.
- **Real orders are not part of this.** They come only after a strategy passes its
  pre-registered test and 300 paper trades, and they need the API key stored as a Firebase
  secret, never in the repo. See `kalshi-scalper/README.md`.


## Kalshi demo test trader (one order, mock funds)

A button on the Kalshi page's Bot tab ("Send one test trade") that sends ONE tiny order to Kalshi's
DEMO exchange from the bot's current signal, so the whole path is proved before anything is automated.
It is admin only, takes nothing from the page (no ticker, price or size), and can only reach the demo
hosts. It is capped at $1 including the fee, immediate-or-cancel, and the order id is derived from the
market, so a double click, a retry or a second instance cannot place it twice (Kalshi also refuses a
repeated `client_order_id` with HTTP 409, measured on the demo). Each attempt is recorded in
`kalshiDemoOrders` (admin read, no client write).

The signal decides WHAT to trade; the demo's own book decides the price. The first tests were priced at the
live price and came back "no fill" because the thin demo book held nothing there. The order now meets the
demo's touch (a YES buy takes its YES ask, a NO buy takes its YES bid), only when that is within 5c of the
live price and the one-contract cost still fits the $1 cap. If the demo book is empty on that side, or too far
from the live price, nothing is sent or recorded and the page says why. Redeploy `kalshiDemoTrade` after
pulling this: `firebase deploy --only functions:kalshiDemoTrade`.

The test trades Bitcoin (`KXBTC15M`) only: the demo's gold market has too few resting orders to fill against.
The paper bot is unaffected and still watches both markets.

Set the two secrets BEFORE deploying, or the deploy fails (use a fresh demo key, not one that has been
pasted into a chat, and never commit it):

    firebase functions:secrets:set KALSHI_DEMO_KEY_ID          # the key id from the demo site
    firebase functions:secrets:set KALSHI_DEMO_PRIVATE_KEY     # paste the whole PEM, including the BEGIN and END lines
    firebase deploy --only functions,firestore:rules

Demo markets sit on exchange shards and a balance belongs to a shard. If the signal's market is on a
shard with no demo funds the button says so and sends nothing.

**If the demo is down or flaky.** Kalshi's demo exchange has gone down for stretches (HTTP 503, and
`/exchange/status` reporting `trading_active: false`). The trader checks that first and says "the demo
exchange is down" without writing a record. A transient failure (503, 429, a timeout) is retried twice
inside the call. If it never clears, the record says "unavailable" and the next press tries again with the
same order id: that is safe because Kalshi refuses a repeated `client_order_id` (HTTP 409, measured on the
demo) and, if an earlier attempt had in fact landed, the 409 makes the trader look that order up and report
it. A refusal that is the caller's fault (HTTP 4xx) is recorded and blocks that market, and a record stuck at
"sending" (the function was killed mid-flight) blocks it too, so nothing is ever sent twice. The duplicate
protection was measured on the demo; confirm it on production before any real order.

**Two demo hosts.** Kalshi documents two demo front doors, `external-api.demo.kalshi.co` (recommended) and
`demo-api.kalshi.co`. On 2026-10-06 the first returned HTTP 503 for over an hour while the second kept
trading, so a transient failure on the first is retried on the second, both on the allow list. If the
button says the demo is down, both were failing.

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
`kalshiLiveArmed` is the second scheduled function (the paper bot is the first); the tests name exactly those two.

### Kalshi account panel (read only)

The Bot tab's "Kalshi account (live, read only)" card has a Refresh button. `kalshiLiveAccount` (admin only, takes
nothing from the page) reads `/portfolio/balance`, `/portfolio/positions` and `/portfolio/fills` with the live key and
shows balance per shard, open positions and recent fills. GET only, no order code (`kalshiAccountLib.js`, a test
asserts it), and it works whether or not `KALSHI_LIVE_ENABLED` is on. Each part shows its own error, and a response
shape it does not recognise is listed by field name. Deploy with
`firebase deploy --only functions:kalshiLiveAccount`. It is the quickest way to see whether your funds sit on the same
shard as the market (Bitcoin and gold were both on shard 2 when last checked) without waiting for a scan to refuse.


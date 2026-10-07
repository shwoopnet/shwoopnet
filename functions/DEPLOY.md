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

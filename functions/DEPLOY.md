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

`kalshiBooks` is a read-only callable that feeds the Live books tab. It requires
the owner's email AND `isAdmin: true` on the user document. The journal needs no
function at all: it is a field on the admin's own user document, and
`firestore.rules` refuses a non-admin write to it. So the journal works only
once the rules are deployed:
```
firebase deploy --only functions,firestore:rules
```


`kalshiBooks` tries `external-api.kalshi.com` (the host Kalshi's docs give) first
and `api.elections.kalshi.com` second. The second sits behind a CDN that refuses
Google Cloud addresses, so Live books working at all depends on the first not
doing the same. If the status line still says refused, both hosts said no and
the error names each.

Kalshi's CDN returns 403 to requests from Google Cloud on the second host, so if both refuse, Live books will show
a plain message instead of prices. That is expected and the journal does not
depend on it. There is deliberately no scheduled recorder on Firebase: it could
only fail every minute. History is fetched with `kalshi-scalper`
(`python -m scalper.backfill`) from a connection Kalshi accepts.

The first deploy after this change asks whether to delete `kalshiRecorder` and
the old `kalshiSnapshots` data function. Answer `y`: nothing calls it.
Any `kalshiSnapshots` or `kalshiResults` documents it already wrote can be
deleted in the Firebase console; nothing reads them.

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
- **Alerts.** The page shows the bot as OK, STALE (2.5 minutes of silence) or DOWN (5). A
  phone alert when it stops is not built yet; it needs an outside watchdog and is the next
  piece.
- **Real orders are not part of this.** They come only after a strategy passes its
  pre-registered test and 300 paper trades, and they need the API key stored as a Firebase
  secret, never in the repo. See `kalshi-scalper/README.md`.

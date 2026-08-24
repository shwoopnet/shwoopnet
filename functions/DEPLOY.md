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

This deploys four callables: `finnhubQuote`, `finnhubNews`,
`finnhubEarningsCalendar`, `finnhubCompanyNews`. Each one checks that the
caller is signed in as `heiszcam@gmail.com` (matching the frontend's own
owner-only gate) before it will spend the Finnhub key on a request — so the
function URLs being technically public doesn't open the key back up.

## After deploying

Nothing else to change in `index.html` — it's already wired to call these
functions via the Firebase SDK (`window.__shwoopAPI.finnhubQuote(...)` etc. in
the `<script type="module">` block). Reload the deployed page and the Brief
page / quote loop should pull data through the proxy automatically. Check the
Functions logs (`firebase functions:log`) if something doesn't load — a 403
there means the signed-in email didn't match `OWNER_EMAIL`, not a Finnhub
problem.

## If you'd rather not deploy this yet

The old direct-to-Finnhub code path has been fully removed from `index.html`,
so until this is deployed, the Brief page's quotes/news/earnings and the
per-trade news alerts will fail closed (console errors, "Couldn't load..."
placeholders) rather than silently falling back to the old exposed key.

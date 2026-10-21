# Security review, 2026-10-08

Scope: `index.html`, `firestore.rules`, `functions/`. `shwoop-server` was not touched. Read-only review plus the fixes marked below.

## Fixed on this branch

1. **Stored script injection through news and broker text (high).** The alert toast, the History list, the Activity log, the trade
   toasts and the pause banner put third-party text (Finnhub headlines and article links, Alpaca error messages) into `innerHTML`
   without escaping, and the article link went into `href` unchecked (`javascript:` needs no metacharacters). The page holds a session
   that can read the Alpaca keys and, for the admin, call the Kalshi order functions. The article list already escaped and
   scheme-checked; these paths now do the same (`escapeHtml`, new `safeHttpHref`). Gates: `test/externalTextEscapedGates.test.js`.
2. **Dependencies (critical and high in the transitive tree).** `npm audit fix` in `functions/` (lockfile only, no `package.json` change)
   removed the critical (`proxy-addr`) and high (`@grpc/grpc-js`) findings. Nine moderate findings remain in Google client libraries,
   reachable only through `firebase-admin`; they need a major bump of that package and were left. Neither fixed package is used in a way the
   advisories describe (we read no client IP and run no gRPC server), so this is hygiene, not an exposed hole. Deploy needs
   `firebase deploy --only functions` to take effect.
3. **Finnhub callables forwarded any string (low).** Any signed-in account could pass an arbitrary symbol or date through to the vendor on
   the shared key. Symbols and dates are now shape-checked. Gates: `test/finnhubInputGates.test.js`.

## Checked and fine

- `firestore.rules`: `isAdmin` cannot be set from the client (equality on update, refused on create); a non-admin cannot write live
  credentials or `alpacaEnvironment: live` on create or update; `kalshiJournal` is admin-only; every Kalshi collection is
  read-by-admin, write-never; the halt document accepts only a boolean and two fields; there is no delete rule on user documents.
- Kalshi functions: every callable runs `assertKalshiAdmin` (email AND the `isAdmin` flag, fail closed); the order code is only in
  `kalshiLiveLib.js`, production host only (`assertLive`), never retried, create-first order record, key never logged or returned; the
  relay takes no caller-supplied path; the watchdog ping carries only a truncated error message.
- `halted()` fails closed (anything but an explicit `halt: false` is halted).

## Not changed, for the owner to decide

- **`email_verified` is not required by `assertKalshiAdmin`.** The `isAdmin` flag is the second lock and cannot be set from a client, so
  this is defence in depth. Requiring it would lock the owner out if they sign in with an unverified email and password account, so it
  was not done without asking.
- **Alpaca and live Kalshi-side secrets:** Alpaca keys live in the user's own Firestore document (readable by that signed-in user, by
  design). Anyone who can run script in the owner's session reads them, which is why item 1 mattered.
- **No Content-Security-Policy.** A CSP would add a second line behind item 1, but the page is one file with inline scripts and styles
  and Firebase, Google Fonts and chart code loaded from several origins, so a policy strict enough to matter needs a nonce build
  step this project does not have. Not attempted.
- **App Check is not enabled** on the callables, so a stolen ID token can call them from anywhere. They are all admin-gated or
  shape-checked; App Check would limit abuse of the two Finnhub callables by other invited accounts.

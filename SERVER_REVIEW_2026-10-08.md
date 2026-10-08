# shwoop-server review, 2026-10-08 (read only)

Reviewed `shwoopnet/shwoop-server` at `42366f1` (#164). Nothing in that repo was changed or pushed. `npm test` passes (90 test files, about two and a half minutes). Findings are ranked; the first one that touches money is item 3.

## Findings

1. **Secrets are compared with `!==` (low to medium).** `src/server.js` `requireSecret` and `requireOwnerSecret` compare the Authorization header to
   `Bearer <secret>` with a plain string compare, which is not constant time. Over the internet this is hard to exploit, but `/forward-test` and
   `/options/preregistration-status` return any account's trading data for any `uid` once that one secret is known, so it is worth the five lines.
   Fix: hash both sides (`crypto.createHash('sha256')`) and compare with `crypto.timingSafeEqual`.

2. **The Twelve Data proxy forwards unvalidated parameters (low).** `src/server.js` `/twelvedata/time_series` takes `symbol`, `interval`,
   `outputsize` and `end_date` from the query and forwards them. The shared secret for it is, as the file's own comment says, public in the
   frontend, so anyone can call it. The rate-limited queue bounds the damage, but `outputsize` has no upper limit (a very large value can burn
   provider credits). Fix: `interval` from a fixed list, `outputsize` an integer in a sane range, `symbol` and `end_date` shape-checked.

3. **Fallback order id is random when the bar time is missing (real money risk, cold path).** `src/autoTrade.js:228` and `:230` return
   `shwoop-<sym>-<uuid>` when `entryBarTime` is missing or unparsable. That is the exact per-call-only protection that let 15 duplicate orders
   reach a real account during a deploy overlap. Today every pick carries `entryBarTime`, so this is a path nothing reaches, but if it were ever
   reached a redeploy could double the order again. The project rule is to fail closed: skip the order with a stated reason (as the
   `duplicate_client_order_id` skip at `:659` already does for its case) instead of inventing an id.

4. **Dependency advisories (medium).** `yarn audit --groups dependencies`: 8 findings, 2 high, both via `firebase-admin`: `@grpc/grpc-js`
   (patched in 1.14.5) and `node-forge` RSA signature verification (no patched version listed). Neither is used the way the advisories
   describe (no gRPC server, no node-forge signature verification of untrusted data), so this is hygiene. Moving `firebase-admin` to its
   current major clears the grpc one. Check the release notes first: `package.json` pins `^12.0.0`.

5. **The upstream error text is returned to the caller (low).** `/twelvedata/time_series` answers `502 { message: err.message }` on a fetch
   failure. The upstream URL contains `apikey=`; Node's fetch errors do not normally include the URL, but a fixed message ("upstream fetch
   failed") removes the question.

## Checked and fine

- **Stale-document clobbering.** All 15 `updateUserDoc` call sites write server-owned status fields only (cycle status, timestamps, heartbeat,
  account summary, pause flags, last cycle summary). The journal and activity log go through `runTransaction` on the fresh document, as
  CLAUDE.md requires.
- **Order idempotency.** Equity entries use `signalOrderId` (symbol, strategy, entry bar time) with Alpaca's duplicate recovery; options,
  closes and protective orders also pass deterministic `clientOrderId`s (`optionsWeeklySpreadCycle.js`, `optionsIronCondorCycle.js`,
  `safety/*`).
- **Secrets in logs.** No console call prints a key, secret or token. Alerts go to the log with the `[alert]` prefix.
- **Server surface.** `/health` is unauthenticated by design and exposes only uptime, tick freshness and condition category names with
  durations. The other routes fail closed (503) when their secret is not configured, which fixed the old `Bearer undefined` hole.
- **No `eval`, `new Function` or `child_process`** in `src/`.
- **`profitSweep.js` moves no money.** It computes an earmark from realized P&L and returns an instruction.

## Not examined

Alpaca account-level permissions, Render environment configuration, and Firestore rules for anything other than what `shwoopnet/firestore.rules`
already says. The orchestrator's trading logic was read only where it writes or orders.

# shwoopnet

Frontend for an automated trading app (Pocket Advisor). Firebase auth +
Firestore, deployed to GitHub Pages. Its backend is a separate repo,
`shwoop-server`, which runs the actual trading cycles on Render.

## The one structural fact that governs everything

**The entire frontend is one ~13,000-line `index.html`.** No build step,
no bundler, no type checking, no framework. Nothing catches a deleted CSS
rule, a stale `getElementById`, or an unbalanced brace until a human
notices the page is broken in production.

That is why `/pre-ship` exists, and why it is not optional:

```bash
node .claude/skills/pre-ship/scripts/check-frontend.js index.html
```

Every check in it traces to a bug that **actually shipped here**. Run it
before every merge. A `note` is a judgement call — the question is never
"are there notes" but "is any note *new* in this change". `intradayToggle`
is a known, long-standing one.

## Skills in this repo

Committed under `.claude/skills/`, so they load in every session, local or
remote:

- **`pre-ship`** — the static checks above, plus the backend suite.
- **`health-check`** — the weekly strategy review, with thresholds decided
  in advance so a losing week can't be argued into looking fine.
- **`ask-the-advisors`** — six-perspective board for project decisions.

## Git workflow

`main` is squash-merged, so a long-lived branch drifts fast. Always:

```bash
git fetch origin main
git stash
git checkout -B <branch> origin/main
git stash pop
```

Push with `-u origin <branch>`. Never push to `main` directly.

## Verifying frontend work without a live account

Most of the app is behind auth and a real Alpaca connection, but almost
everything can still be verified headlessly, and should be:

- Lift a function out of `index.html` with `new Function(...)` on the file
  text and test it directly. Used for the dock columns, duplicate
  detection, the progress bar and the backtest engine.
- Load the page in Chromium with the network blocked
  (`executablePath: '/opt/pw-browsers/chromium'`), un-hide `#authGate`,
  inject fixture data, and screenshot against the real CSS.

"It renders" and "it behaves" are different claims. Say which one you
checked.

## Strategy numbers — read this before quoting any of them

The Labs page used to assert **profit factor 2.71 (equities) and 2.35
(crypto)** as fact. Both were withdrawn in Aug 2026 because the tool that
produced them could not reproduce them. Current measured figures, from the
same tool under corrected accounting:

| | Measured | Basis |
|---|---|---|
| Equities | **1.24** | 406 signals, 16 symbols, ~60 days, 5bps/leg |
| Crypto | **1.93** | 282 signals, 12 pairs, ~60 days, 25bps/leg |

Both are **upper bounds**, and both are thin:

- Equities expectancy is **+0.09%/trade against a 0.10% round-trip cost**.
  The edge is the same size as the uncertainty in the cost assumption.
- Crypto's 25bps is Alpaca's taker *fee* and **excludes spread**, which is
  widest on the alts producing most of its signals (UNI alone is 58 of
  282). It is also a single 60-day window on a long-only trend strategy —
  in crypto that measures the window as much as the strategy.

Three separate backtest errors were found in one weekend, and **every one
flattered the strategy**. Treat a backtest figure as a claim to be
re-derived, never as a fact to be quoted.

## Incidents that shaped this code

Do not undo these without understanding why they exist.

- **Duplicate orders (real money).** `submitWithRetry` keyed its Alpaca
  `client_order_id` on `randomUUID()`, so protection was per-call only.
  Two processes — the normal state for seconds during every Render
  redeploy — each generated a different key and Alpaca accepted both. 15
  duplicate orders across 10 symbols. Now keyed on `entryBarTime`, the bar
  that triggered the signal. A journal-side guard cannot fix this; by the
  time entries are written the money has moved.
- **Backtest lookahead.** The confirmation-bar option waited a bar, then
  booked the fill at the *original* breakout level — selecting for a
  favorable move and then handing the trade that move for free. Reported
  PF 13.26. Entries must always be priced at the bar you would actually
  fill on.
- **Demo page removal took `.trade-progress-*` with it**, because those
  rules sat interleaved among demo styles. The stop/target bar shipped as
  bare "StopTarget" text. This is check #3 in `pre-ship`.
- **Crypto charts loaded ~9 bars**, which froze the zoom clamp at `[8, 9]`
  and made the x-axis appear broken. Alpaca bars return **ascending from
  `start`**, so a wide window plus a `limit` cap returns the *oldest*
  bars: size the window to ~1.5x what you need, paginate to the END, then
  `slice(-limit)`.
- **Credentials arrive after auth resolves** (they live in the Firestore
  user doc), so anything firing on the auth handler must guard on
  `alpacaConnected` or it produces a burst of 401s on every page load.

## Conventions

- Comments explain **why**, not what. Several exist specifically to stop a
  future change from reintroducing a bug; keep them.
- The palette is fixed ("Ledger"). Don't introduce a second design system.
- `firestore.rules` enforces that only the admin account can ever hold
  live-trading credentials. The backend relies on that and does no admin
  check of its own.

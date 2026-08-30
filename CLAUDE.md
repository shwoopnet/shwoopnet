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
- **`unlazy`** — vendored from upstream (see its `PROVENANCE.md`). Writes
  acceptance gates before the work and re-measures them before reporting,
  so a confident "done" has to survive a check. Its `CHECK:` lines are
  shell commands — read `SECURITY.md` before running a ledger this repo
  didn't write.

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

| | 30d | 60d | 180d | 365d |
|---|---|---|---|---|
| Equities | 1.48 | **1.24** | — | 0.96 (6 of 16 symbols) |
| Crypto | — | 1.94 | **1.20** | **1.20** (1,843 signals) |

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

### The window series is the finding

**Both strategies decline as the lookback lengthens.** Equities 1.48 /
1.24 / 0.96 at 30 / 60 / 365 days, still falling. Crypto 1.94 / 1.20 / 1.20
at 60 / 180 / 365 — identical at the last two across 801 and 1,843 signals,
so that one has converged rather than merely fallen. Same universes, same
cost models, same code; only the window changes.

That is what an apparent edge living in the recent market looks like,
rather than one living in the strategy. Any single-window figure quoted
without its neighbours is close to meaningless here, and the flattering
window is always the short one.

State crypto's result in the terms that suggest what to do about it: 1.20
is a **gross edge of +0.62% a trade with 81% of it eaten by cost**, leaving
+0.12% against a 0.50% round trip that still excludes spread. The signal is
real and stable across 1,843 signals. It does not survive paying a taker
fee on both sides — so **execution cost is the binding constraint, not the
strategy logic**. Equities is not the same case: its gross edge is +0.19%
against a 0.10% cost, so cost takes only half, and it still degrades with
window length.

Neither has cleared the 1.5-across-three-windows bar that was set before
any of this was measured.

### The spread is now measured, and it closes the case (Aug 2026)

The 0.50% round trip above is Alpaca's taker **fee** and always excluded
spread. Labs' "What spread does crypto actually pay?" probe measured it:

| Cheap enough to trade | Not |
|---|---|
| BTC 0.019% · ETH 0.030% · SOL 0.066% · AVAX 0.089% | LTC 0.562% · BCH 0.575% · DOGE 0.318% · XRP 0.308% · LINK 0.201% · UNI 0.201% · AAVE 0.199% · DOT 0.188% |

Median 0.200% → **round trip 0.700% against a 0.62% gross edge, i.e.
−0.08% a trade.** Four of twelve pairs clear break-even; eight do not.

**The median understates it.** The signals concentrate in the expensive
half — UNI alone was 58 of 282 signals in a 60-day run, at a 0.701% round
trip. BTC and ETH are cheap *because* they are liquid and less volatile,
which is also why a volatility-breakout screener fires on them least. A
signal-weighted cost is higher than 0.200%; compute it properly before
quoting the equal-weight figure again.

Two caveats, and they do not cancel out:

- The 0.62% gross edge was measured **under the entry-pricing lookahead**
  fixed in #140. The honest gross edge is lower, so the true net is worse
  than −0.08%.
- The spread reading is **one Sunday-afternoon snapshot**, likely near the
  worst case. Re-sample on a weekday across several hours before treating
  0.200% as the number. This is the only correction pointing the
  strategy's way.

What this kills is **this strategy as a market-order strategy on this
universe** — a narrower claim than "crypto does not work", and the
difference is where the remaining value is. Execution cost is no longer a
hypothesis about why the edge is thin; it is a measurement with per-pair
numbers behind it.

Trimming the universe to the four cheap pairs is **legitimate**, and it is
not the thing the per-symbol-table warning below forbids. That warning is
about trimming on *returns*, which fits noise. Cost is observable before
the trade and independent of outcome, so selecting on it is not selection
bias. The open question is whether four low-volatility majors produce
enough breakout signals to be a strategy at all.

Note also that both strategies earn almost exactly **90% of their own cost
assumption** per trade (equities +0.09% against 0.10%, crypto +0.45%
against 0.50%). Crypto's profit factor looks nearly twice as good, but
relative to what it costs to trade they are the same strategy, and neither
survives being modestly wrong about fills.

### Registered before running: maker-limit entries

Recorded here **before** the experiment, so the result counts either way.

A resting limit at the breakout level *earns* the spread instead of
crossing it, and Alpaca's crypto maker fee (15bps) is below its taker fee
(25bps).

Only the **entry** leg can rest. The exit is a stop or a trend
invalidation — it takes whatever is there — so the honest model is maker
on the way in, taker on the way out:

| | Fees | Spread crossed | Round trip |
|---|---|---|---|
| Market (today) | 0.50% | 0.200% (both legs) | **0.700%** |
| Maker entry | 0.40% | ~0.100% (exit only) | **~0.50%** |

Against a 0.62% gross edge that is **+0.12% a trade, not +0.32%** — an
earlier draft of this note assumed maker fees on both legs and was wrong
in the flattering direction, which is the fifth time that has happened
here. It is a real improvement over −0.08%, and it is thin, and the gross
edge itself still has to be re-measured after the #140 entry-pricing fix.

**Predicted failure mode, stated in advance:** the breakouts that never
trade back down to the limit are disproportionately the *winners*, so fill
rate and profit factor move in opposite directions. This is the same shape
as the failed-breakout exit below, which cut average loss exactly as
intended and still lost money because it converted 37 winners into losers.

So the experiment is only meaningful if it reports **both** the profit
factor of filled trades **and** what the missed signals would have made.
A profit factor that improves while fill rate collapses is not a result,
it is the same trap with a new face.

### Registered before running: hybrid entries (limit first, market fallback)

Measured 60-day results on the same window, all three under corrected
accounting:

| | Reported PF | True net/trade |
|---|---|---|
| Market orders | 1.05 | **−0.16%** |
| Maker only | 1.29 | +0.10%, on a set that excludes the winners |

Maker-only is **selection, not execution**. The 94 skipped signals would
have averaged **+1.47%** with 51% winners, against the filled trades' 30%.
The limit catches the breakouts that come back — which is another way of
saying the ones that failed.

**The correction that matters, and it was nearly missed.** The obvious
hybrid reading is "the market strategy, with a better entry on 70% of
trades". That is wrong, and believing it would have been the sixth
flattering error here.

A hybrid cannot market-in at the bar after the signal, because it does not
yet KNOW the limit will fail — that is only known after the wait window
expires. So the fallback entry is priced at `signalIdx + waitBars + 1`,
roughly two hours later, on an asset that by definition has been running
away for those two hours. The +1.47% figure is an honest measure of what
the MARKET-ONLY strategy earns on that subset (it enters at the next bar
regardless); it is **not** what a hybrid earns, and using it as such is
lookahead wearing a different hat.

So the hybrid is not "maker plus free upside". It is **maker on the ones
that come back, and chase-the-runaway two hours late on the ones that
don't** — which is exactly what `CHASE_LIMIT_RISK_FRACTION` exists to
refuse in live trading.

**Prediction, recorded before the run:** the hybrid lands *below* maker-only
and probably below market-only, because the fallback bucket buys the
strongest moves at their worst prices. If it comes out above both, suspect
the fallback timing before believing it.

### Things that were measured and did NOT work

Keep this list. Re-running a settled experiment is a real cost, and an
option that sounds obviously good is exactly the one that gets retried.

- **Exiting when the breakout fails** (close the position when a bar closes
  back inside the opening range). Profit factor **1.24 → 1.12** on the same
  60-day window and the same 406 signals. It did what it was meant to —
  average loss 0.53% → 0.42%, average win 1.57% → 1.83% — and still lost,
  because it converted 37 winners into losers. The classic trend-following
  result: the losers it avoids are outnumbered by the winners it ends
  early. The crypto equivalent is still unmeasured.
- **The confirmation-bar delay** as originally written reported 13.26 by
  booking the fill at the pre-confirmation price. Priced honestly it is
  0.94.

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

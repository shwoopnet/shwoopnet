# shwoopnet

Frontend for a personal dashboard (Pocket Advisor): the Market Brief, the
Kalshi page and Settings, and nothing else since Oct 12, 2026 (see "The blank
slate" below). Firebase auth + Firestore, deployed to GitHub Pages. The Kalshi
bot runs from `functions/` here. `shwoop-server` is a separate repo that still
runs equities trading cycles against Alpaca on Render; this page no longer
shows or controls them.

## The one structural fact that governs everything

**The entire frontend is one ~3,800-line `index.html`** (it was ~16,700 lines before the blank slate). No build step,
no bundler, no type checking, no framework. Nothing catches a deleted CSS
rule, a stale `getElementById`, or an unbalanced brace until a human
notices the page is broken in production.

That is why `/pre-ship` exists, and why it is not optional:

```bash
node .claude/skills/pre-ship/scripts/check-frontend.js index.html
```

Every check in it traces to a bug that **actually shipped here**. Run it
before every merge. A `note` is a judgement call — the question is never
"are there notes" but "is any note *new* in this change".

As of Aug 2026 it reports **`FRONTEND: clean.`** with no notes at all, and
that is worth defending. It carried one permanent orphan (`intradayToggle`,
a guarded lookup for a button removed long ago) for months, and a check
that always prints one known failure teaches everyone to skim past the
line failures appear on. The Labs removals in the same session produced
*nineteen* orphans on that exact line.

## Skills in this repo

Committed under `.claude/skills/`, so they load in every session, local or
remote:

- **`pre-ship`** — the static checks above, plus the backend suite.
- **`health-check`** — the weekly review of the Kalshi bot (rewritten Oct 22,
  2026; it used to review the withdrawn equities strategy), with thresholds
  decided in advance so a losing week can't be argued into looking fine. The
  equities version stays in the `shwoop-server` repo.
- **`security-audit`** and the **`security` agent** (`.claude/agents/security.md`, Oct 22, 2026) — the project's security engineer. The skill runs a deterministic scan (`node .claude/skills/security-audit/scripts/scan.js`: secrets, workflows, database rules, server functions, the page, dependencies; it prints no secret value and exits 1 on a FAIL) and the agent reads what a script cannot, proves each finding, and fixes it as a small pull request with a gate in `test/`. It never merges, never deploys, never writes the details of an unfixed weakness into this PUBLIC repo, and never touches trading rules (`test/securityAgentGates.test.js`, which also proves the scan fails on a deliberately bad fake repo). Run it before merging a change to `functions/`, `firestore.rules`, sign-in code or workflows, and weekly.
- **`ask-the-advisors`** — six-perspective board for project decisions.
- **`unlazy`** — vendored from upstream (see its `PROVENANCE.md`). Writes
  acceptance gates before the work and re-measures them before reporting,
  so a confident "done" has to survive a check. Its `CHECK:` lines are
  shell commands — read `SECURITY.md` before running a ledger this repo
  didn't write.

## The blank slate (Oct 12, 2026)

At the owner's request ("an anti-degen proof website ... to prevent myself from full porting") the site was cut down to the Market Brief, the Kalshi page and Settings. Gone: the Trade Overview, Journal, Changelog, Notes and History, the ticker tape, the account dock and the trade modals; the Alpaca, Finnhub and Twelve Data integrations (and the Twelve Data proxy secret that sat in the page in plaintext); creating an account from the page, and the invite generator. `test/blankSlateGates.test.js` and `test/removedFeaturesStayRemovedGates.test.js` hold the line: three pages, a fixed list of hosts and of Firebase methods, exactly the Settings rows that exist, no sign-up. A new row, host or method has to be added to those gates on purpose; that is the point.

The Brief and the market strip make no market-data call of their own. (The Bot page's charts do read public prices in the browser, Bitcoin and PAXG candles from Coinbase and gold from gold-api.com, allowed on purpose in `test/blankSlateGates.test.js`; the footer's privacy line says so.) The Brief and the market strip read `shared/marketTape`, which the keyless scheduled function `marketTapeTick` (`functions/marketTapeLib.js`, every 5 minutes, public Yahoo chart prices and CNBC and MarketWatch RSS, no secret) writes; the Brief's movers and earnings still read `shared/marketSnapshot`, which shwoop-server writes, and an older snapshot price never replaces a newer tape price. **shwoop-server still trades Alpaca for any account with keys stored, and the page can no longer show or pause it.** One convenience was added back on Oct 20, 2026 at the owner's request: optional sound alerts on the Kalshi page (a tone for an entry, a sell, and a stop or issue, while the page is open). It is a switch in the Tools card, off by default, kept in this browser's localStorage only, never a browser Notification and never a Firestore setting (`test/kalshiSoundGates.test.js`). **Phone alerts** were added the same day (Web Push, the owner's own Cloud Functions, no third-party service): a "Phone alerts" switch in the Tools card, `sw.js` and `manifest.webmanifest` at the site root, and the functions `kalshiPushKey`, `kalshiPushSubscribe`, `kalshiPushUnsubscribe`, `kalshiPushOrder` and `kalshiPushSession` (`functions/kalshiPushLib.js`, `test/kalshiPushGates.test.js`). They only READ what the bot wrote (an order changing, the session ending), hold no Kalshi key, are imported by no trading code and catch every error. The page may ask for notification permission exactly once, from the owner's tap (`test/removedFeaturesStayRemovedGates.test.js` G1). It alerts on a buy, an early sell, a trade settling (win or loss with the amount), and a stop or issue; the owner's own Stop and Flatten are silent. On an iPhone it works only from the Home Screen app. `functions/deploy-push.sh` is the one laptop deploy for it, and keeps an existing push key (replacing it would orphan every subscribed phone). Much of what is written further down about the equities strategy, the Labs page and the account dock describes code that no longer exists; it is kept as the research record, and git history has the code.

## The Data page (Oct 21, 2026)

A fourth page, **Data**, was added at the owner's request ("start building out a data center page"): admin only like Kalshi, **read only** (no control of any kind inside it), drawn from the same settled orders the Kalshi page already loads (weekly result bars, growth line, share of trades by market, a by-market table with per-contract result). It adds no host and no Firebase method. `test/dataCenterGates.test.js` pins that it stays read only and that its numbers mean what they say (weeks on the US Central clock, per contract over contracts filled, hand-closed trades left out); `removedFeaturesStayRemovedGates` G3 now lists four pages on purpose. **Entry timing test card (Oct 22, 2026, gate D7):** a read-only table on the Data page that splits Bitcoin, XRP and natural gas by the entry time each order recorded (`entryLead`, an order with none is an older 6 minute entry), so the 10 minute live test (FWD8) can be watched without an export. It is a view, not a verdict: the two groups are not the same markets.

**Strategy numbers, live tests and a plain skip line (Oct 22, 2026, the owner: "so i dont get lost").** The Data page has a read-only card, **The strategy in numbers** (profit factor, win rate against the break-even win rate, average win and loss, deepest drawdown, longest losing run), a **Profit factor** column in By market (a market with fewer than 30 settled trades shows "too few", the health check's rule), and a **Live tests** card (windows with two filled crypto orders since the one-order-per-window rule, which should stay 0, and how many orders carry `rng5`; both start times are approximate). All plain text, no new colour, no control (gates D8 to D10). On the Bot page a minute the bot skipped is said plainly ("Skipped a minute (time): ... It looks again every minute."), and a 429 explains itself (gate D11).

**Slogan and sign-in logo (Oct 23, 2026, the owner).** The slogan is **Trade less. Live more.** (it was "We trade. You live your life."); the signed-out tab title, the link preview text and `og-image.png` carry it. The signed-out screen is one screen on the site's own background (the same ambient glow, drifting grid and ghost wordmark as the app, so the two feel like one place) (the owner: "that's a sick login page", then "playful and graffiti", "make it in our themes"): the wordmark, a small sign-in sticker in the top right (same ink border and offset shadow as the "Systematic trading" label), the big slogan in Titan One with spray-in letters and paint drips (the one deliberate exception to "Titan One is the wordmark only", `test/bubblePopGates.test.js` P1), one plain line. The longer "What is Shwoop" explanation and its note pop-up were dropped at the owner's request (Oct 23). Every colour is a theme token, so Ledger light and dark and Mono Ink all work. Motion is decoration, stopped by reduced motion and the Settings switch. It is only a layer over the same gate: every id the sign-in code uses is unchanged, it follows the theme and skin, and it says nothing about the bot's markets, size or results and makes no performance claim because it is public (`test/frontPageGates.test.js`, `test/signInWordmarkGates.test.js`). The Running panel on the Bot page's Account card is anchored to the whole card (same width, above the cards after it). The shirt and hoodie artwork is merchandise only and lives outside this repo.

**Fonts are local (Oct 22, 2026).** Public Sans, IBM Plex Mono and Titan One are served from `fonts/` (Latin subset, SIL Open Font License, see `fonts/README.md`), not from a font service, so the page makes no font request and a visitor's network address stays on this site. `test/selfHostedFontsGates.test.js` checks the files, the rules and that no font host is referenced; `blankSlateGates` no longer allows the font hosts and `motionHonestyGates` now expects zero outside resources.

**Printable statement and "as of" stamp (Oct 22, 2026, the owner: make the site feel official).** Tools, Export has a month picker and **Print statement** (this month or last month, US Central): a plain document of that month's settled trades with the same figures as the Data page (summary, by market, every trade), opened in a hidden frame so the browser's print dialog can save a PDF (`kalshiStatementHtml`, gate D13). It is an export, so its dollar figures are raw and not masked by Privacy, like Copy all orders. It is deliberately NOT on the Data page, which has no control. The Data page note starts with "As of <time> CT".

**Bubble pop (Oct 21, 2026, the owner: "more visual appeal and interactivity").** Titan One is for the WORDMARK ONLY (and its ghost behind the page): the owner said bubble text is good for the logo but not the whole site, and the black blocky headings looked like a game (Oct 21, 2026, gate P1). Page and card headings, market names and Settings titles are Public Sans bold with no bubble shadow. **Every number is in Public Sans with tabular digits** (stat tile figures, the market strip prices, chart end label, ring total and weekly values, the account total): the owner found Titan One figures like 774.14 hard to read (Oct 21, 2026, gate P1). Do not set a number in Titan One. Motion is decoration only and never moves a number: cards rise in once when a page is shown (`pageEnter`, the class comes off after 2.2 s so the minute's re-render never replays it), there is no cursor spotlight (removed Oct 21, 2026 at the owner's request; a gate keeps it out), cards and tiles lift 2px, chart lines draw in and bars pop in once, ring slices and weekly bars react to hover. Every one of these is off under the OS reduce-motion setting and the Settings switch, (`test/bubblePopGates.test.js` P1 to P6, plus `motionHonestyGates`). Do not add a count-up or any animation on a figure. **Light themes readable (Oct 21, 2026, the owner: "hard to read" in both light modes).** In the light themes the blurred blobs, the grid and the ghost wordmark are quieter (they are tinted with `--amber`, which is black in Mono Ink, so on a light page they greyed everything behind the text), secondary text and card borders are darker, Mono Ink light sits on a light grey ground so white cards stand out without shadows, and stat tiles get a white fill. Dark is unchanged. The wordmark never changes colour on hover (it turned black in Mono Ink, where `--amber` is black): the letters hop instead, off under reduce motion (gate P7).

**Bot page, second cleanup (Oct 21, 2026, the owner).** No big "Bot" title beside the updated time, no Data button in the header (the sidebar has it), the header toggle is called **Privacy** (it masks dollar amounts as ****), and the **Performance card moved off the Bot page**: "How the orders ended" and "Each settled trade" now live on the Data page, the duplicate P/L line and the all-sessions/this-session choice are gone (the Data page is read only, so it has no select).

**Bot page cleanup (Oct 21, 2026).** The Kalshi page is called **Bot** in the sidebar, the landing choice and its own title (ids and stored values still say `kalshi`). The account card is now only status and controls (stake, pool, and a "Today" line: the bot settled result for today on the US Central date, which replaced "Bot since <date>" on Oct 21, 2026; since Oct 22, 2026 it also shows a percentage of the account total at the start of the day, `kalshiTodayPct`, gate D12); the stat tiles, By market and By price paid moved to a closed "All the numbers" fold at the bottom of the Data page (same element ids, same Copy all stats). The Tools menu is grouped (Account, Export, Alerts), and the Rules and limits text lists the real markets, the gold-only size ladder, the 5.5% window limit and the 12% stop.

**Tidy-up and phone pass (Oct 21, 2026).** Removed dead CSS that no markup used (the bouncing logo cube and its flash and ring, the old Performance charts grid, the unused ticker colour variables) and moved the four review notes from the repo root to `docs/reviews/`. On a 390px phone render, every button, select and switch is now at least 40px tall (the toggle through a larger hit area), the bottom bar labels are 11px, the Tools menu is a full-width sheet, and no page scrolls sideways (`test/mobileGates.test.js` M1 to M3). `kalshiExitHtml` (the unused "Exit at 25c" stats block) was removed later the same day; `kalshiExitReport` stays for Copy all stats. The Recent trades list stacks its rows by the width of its own box (a container query on `#kalBotClosed`), not the window, so it never squeezes into four-line rows beside the account rail.

**Cost review (Oct 21, 2026).** Firebase bills about $1.3 a day (mostly Firestore reads and Functions). The Firestore read count is over the free 50K a day mostly because the bot's own minute jobs re-read the last 24 hours of orders; the page used to add about 1,200 reads on every Bot to Data switch (fixed: one set of listeners for both pages, gate D6). The paper tracker (`kalshiPaperTick`) ran every minute although its card was gone, and the old book snapshots were never pruned while the recorder was off; both are fixed in code (tracker off, recorder prunes while off) and go live with `bash functions/deploy-cost.sh`, which touches only those two keyless functions. **Third cut (Oct 21, 2026, tests CO1 to CO3).** The tick's 24 hour order read keeps orders older than 30 minutes in the function instance's memory and re-reads them every 15 minutes (`makeRecentOrderReader`), reading only the recent block each minute; the exit watch's `recentFilled` asks only for filled, unsettled orders; the hand-sold repair pass runs every 10th minute. Staleness can only show an order as unsettled or unsold, which the loss stop counts as lost, so it errs toward trading less, never more. Needs `bash functions/deploy-sizing.sh` (the armed bot) and `bash functions/deploy-push.sh` (the exit watch). Honest size: reads are $0.06 per 100K, so this is worth roughly $2 a month; the bigger line is the exit watch's 10 second loop, which is the safety feature and was left alone.

**Perps funding recorder (Oct 21, 2026, research only).** `.github/workflows/record-perps.yml` runs `scripts/record_perps.py` once an hour on GitHub Actions: one plain GET of Kalshi's public perpetual markets (no key, no account, no order), appended as CSV to the **`perp-data` branch** (never main, never published with the site; `_config.yml` excludes `.github` and `scripts`). It keeps the funding premium's inputs (price, reference price, marks, book top, open interest, funding cap and deadband) because the public market object has no funding-rate field. It exists so the research session can rerun FUND1 on a venue the owner can use. No Firebase cost; a few GitHub Actions minutes a month. `test/perpRecorderGates.test.js`.

## There is no simulation any more (one keyless paper tracker excepted)

**The paper tracker (PAPER1, Oct 20, 2026, the owner's request):** `kalshiPaperTick` (`functions/kalshiPaperLib.js`, `functions/deploy-paper.sh`, `test/kalshiPaperGates.test.js`) records what L1's rule WOULD have bought on three candidate markets (AUD/USD, USD/CAD and natural gas 15 minute markets), one contract, no money, in its own collection `kalshiPaperOrders` (admin read only), shown in its own page card and never in the live record. It meets the constraints below: keyless (no secret on the function, no signing, no `/portfolio`, no POST). Its candidates and its pass bar (300 settled entries on 10 days, read once on or after 2026-11-30, z 2.1, both halves, fees x1.2) are registered in `kalshi-scalper/README.md` before the first entry; a fourth candidate is a code edit and a README entry first. A pass only permits considering a small capped slot that cannot hold a position at the same time as L1. **The page card was removed on Oct 21, 2026 at the owner's request** (live forward testing on the same three markets replaced it, see the probe markets below); the tracker was switched off on Oct 21, 2026 (`PAPER_TRACKER_ON = false`, deployed with `functions/deploy-cost.sh`; set it to true to record again), its collection stays, and a gate (R7) keeps the page from reading the collection.

The keyless Ethereum and Solana simulation (`kalshiSimLib.js`, `kalshiSimTick`, `kalshiSimSession`, the page's simulation card) was removed on Oct 10, 2026 at the owner's request: Ethereum went live and Solana was dropped. Nothing in this repo places a simulated order. If a simulation is ever added again it must be keyless (no signing, no key, no `/portfolio` call, no POST, no secrets on its scheduled function) and, if promoted to real orders, its risk settings (one combined stop, one combined window limit) must scale with it.

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

Most of the app is behind auth and a real Kalshi connection, but almost
everything can still be verified headlessly, and should be:

- Lift a function out of `index.html` with `new Function(...)` on the file
  text and test it directly. Used for the Kalshi charts and tallies, the
  brief headline, the settings sync and `showPage`.
- Load the page in Chromium with the network blocked
  (`executablePath: '/opt/pw-browsers/chromium'`), un-hide `#authGate`,
  inject fixture data, and screenshot against the real CSS.

"It renders" and "it behaves" are different claims. Say which one you
checked.

## What this account's Alpaca plan can actually get (measured Aug 2026)

Answered by the one-shot Labs probe, now removed. Do not re-derive this.

- **SIP works.** Consolidated bars return at 2020-08-31, so there are
  **6+ years** of daily history.
- **The official closing auction print is retrievable.** SPY, 2026-08-27:
  price **771.10**, size **1,096,888**, condition `[" ","M"]` — Market
  Center Official Close.
- **The SIP daily bar close IS the auction price.** SIP's daily close was
  771.10 and the auction print was 771.10 — exact match on two
  independent paths. So a daily-close strategy needs nothing beyond the
  SIP daily bar; the trade-level print is only required for intraday
  auction work.
- **IEX is not the close.** IEX's daily close for the same day was
  **771.18**, eight cents off. That gap is the whole reason this was
  worth measuring: an IEX-based backtest of anything entering at "the
  close" would price every entry at a number no index fund ever paid.

**Nothing is eliminated by data availability.** All six strategy families
the advisor board proposed are testable on this account.

The 1,096,888-share print is worth holding on to as more than a data
point. It is the price-insensitive forced flow the auction strategies aim
to be paid for absorbing — over a million shares crossing at one price at
one instant, because index funds, ETF baskets and MOC algos must trade at
the close regardless of price. That is a measurement of the counterparty,
not a story about one, which is exactly what the current strategies could
never produce.

### How this was nearly a false negative

The first two runs reported "10,000 trades, no auction print". 10,000 was
the requested `limit`, and Alpaca returns trades **ascending from
`start`**, so a 15-minute window truncated about a minute in and never
reached 20:00. The corrected run scanned 14,361 trades across 2 pages and
found the print immediately.

Third time this project has hit that trap — it froze the crypto charts'
zoom clamp and cost the options probe two revisions. It is now asserted by
a gate rather than recorded here and forgotten, and a truncated scan
reports as a **distinct third verdict** from a genuine absence, because
those mean opposite things.

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

### The equities strategy was withdrawn (Aug 2026)

Removed from Labs entirely -- the Method card, the backtest, and the
live-vs-backtest comparison -- and `LABS_BACKTEST_PF` now carries crypto
only. 1.48 / 1.24 / 0.96 are **withdrawn figures**; do not quote them.

The reason is not that they were weak. It is that `computeORBAnalysis`
books the entry at `rangeHigh`, the level the signal bar broke through --
the identical lookahead found in the crypto backtest, which took its
60-day figure from 1.94 to 1.05 when priced honestly. The equities numbers
were never corrected for it, so their true values are unknown and lower.

The strategy is being replaced from scratch rather than repaired. Both
strategies were the same shape (opening-range breakout, volume filter,
trailing stop) and both decay with window length, which is what an edge
living in the recent market looks like rather than one living in the
strategy. The replacement should have an economic reason someone is on the
other side losing money, not a chart shape.

**A process note worth keeping.** A whole day went into four execution
variants of one crypto strategy -- market, maker, hybrid, hybrid with the
chase gate -- when the same effort could have tested four different
strategy families and reported which had anything in it. Optimising the
idea in front of you is not the same as searching. When a strategy fails
its pre-set bar, widen the search before deepening it.

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

### The backtest was simulating a different strategy than the one running

Found by comparing `simulateCryptoForward` against
`shwoop-server/src/lib/technicalAnalysisCrypto.js` directly, which is now
a standing test (`test/engineParityGates.test.js`) rather than a review
habit. **Two divergences, both flattering:**

1. **No early breakeven.** Live carries `EARLY_BREAKEVEN_RR: 0.2` -- the
   stop locks to breakeven at 0.2R, well before the 0.5R trail trigger.
   The simulation had no such concept, while its own comment claimed
   "matches technicalAnalysisCrypto.js exactly". Between 0.2R and 0.5R
   live protected the trade and the backtest let it fall to the range low.
2. **Trailing followed the intrabar HIGH.** Live runs on completed bars
   and sees closes; it cannot react to a peak the bar never closed at.
   Trailing from `bar.h` set a better stop than live could ever set.

Both are fixed to match live. The stop-HIT check still uses `bar.l`, and
that is correct rather than inconsistent: the stop is a resting order at
the broker, so it really does fill intrabar. **Updates happen on closes;
fills happen intrabar.** Both are true and they are not the same rule.

**So 1.05 is withdrawn too.** Every crypto figure ever produced here
described a strategy that has not traded since `EARLY_BREAKEVEN_RR`
landed. The sign of the correction is genuinely unknown -- early breakeven
avoids full losses but also cuts trades that would have recovered, the
same trade-off as the failed-breakout exit that improved every component
metric and still lost money. Re-run 60/180/365 before quoting anything.

That is the sixth wrong number, and the fifth in the flattering
direction. The lesson is not "check harder". It is that a comment
asserting two things match is worth nothing, and a test asserting it is
worth everything -- G1 now fails if live gains a parameter the backtest
does not have.

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

## The Kalshi bot, in four rules

The admin-only Kalshi page and `functions/` run strategy L1 on real money. Full description: `docs/PROJECT_OVERVIEW.md`.

- **It runs 24/7.** No session end time. The loss stop and the 200 order limit look at the LAST 24 HOURS, so old profits cannot hide a bad day. After a stop it stays off until restarted, on purpose.
- **Size follows the balance once a week** (`reviewSizing`, `foldSkim` in `functions/kalshiLiveLib.js`): one contract per $43 (a 2% base), one step up at most every 3 days, down at once, ceiling 40. Only NEW net profit highs are skimmed; skimming each win was tried first and is wrong (wins are 6c, losses 90c).
- **Pages publishes the repo.** Everything not in `_config.yml`'s exclude list is on the public site, and a committed symlink breaks the build. `test/pagesPublishGates.test.js` guards both. Never `git add -A` in a worktree that has a `kalshi-scalper/data` symlink.
- **Live and simulated numbers never share a column.** A research figure quoted as if it were the live record has already cost trust once.

Docs in `docs/` (overview, roadmap, career notes, mock-ups) are refreshed weekly; the checklist is in `docs/README.md`.

**Raising the size by hand (Oct 20, 2026).** After a loss stop `reviewSizing` holds the cap for 7 days (`SCALE_STOP_PAUSE_MS`), and a Stop then Start does not skip that hold. The owner may edit `cap` (a number) and `base` (the balance minus `saved`, the figure the 5% loss stop is measured from) in the Firestore document `kalshiLiveControl/sizing`; the bot reads it on its next minute. Set `base` too: a stale tiny `base` makes the loss stop end the bot at the first trade. The code is deliberately unchanged, so the hold still applies to the next stop.

**`deploy-sizing.sh` deploys only `kalshiLiveArmed` and `kalshiBooks`.** A change to the exit watch, Flatten or the alert functions needs `functions/deploy-push.sh` (or a full `firebase deploy --only functions`), and either must keep `KALSHI_LIVE_ENABLED=on` in the gitignored `functions/.env`, or the exit watch stops selling. `functions/deploy-paper.sh` deploys only the paper tracker and the Firestore rules and needs no switch.

## Conventions

- Comments explain **why**, not what. Several exist specifically to stop a
  future change from reintroducing a bug; keep them.
- The palette is "Ledger", with one optional skin, "Mono Ink" (`html[data-skin="mono"]`, chosen under Settings, Theme, added at the owner's request on 2026-10-09). A skin only re-points the existing tokens and never the gain or loss colors. Don't introduce another design system.
- **Calm view on the Kalshi page (Oct 21, 2026, the owner: it "looks like a christmas tree" shown from across a room).** Green and red are kept for the few things that carry the verdict: the "Today" line, the end label of the P/L line, the losing bars and the lost slice of the ring. Every other figure (stat tiles, By market, By price paid) is plain text with its sign; the P/L line is one plain stroke; winning bars and the Won slice are neutral; the market rows show the name, time left and YES price only. Do not add a new coloured figure without taking one away. The gain and loss tokens themselves are unchanged (gates Y8, Y14). **Presentation view** (a "Mask amounts" button in the page header and a checkbox in the Layout menu, Oct 21, 2026) shows **** in place of every dollar amount (the sign stays) and hides the Tools menu, through a page attribute and one flag (`kalshiMasked`) that are never saved (gate Y11c). Every dollar figure on the Bot and Data pages must go through `kalshiMoney`, so one flag masks them all; exports use `kalshiMoneyRaw` and are never masked. It changes no number and no control that can change the bot.
- `firestore.rules` enforces that only the admin account can ever hold
  live-trading credentials. The backend relies on that and does no admin
  check of its own.

## The page cannot choose the size (Oct 23, 2026)

The Start box used to carry a "Scale size with the account" tickbox, and `kalshiL1Session` read `sizing` from the page. The security review flagged that as a risk setting chosen from the page. Now `const sizing = on` in `functions/index.js`: starting always means the gold size ladder (every other market is one contract in code), which is what the box did while ticked, and nothing in `request.data` can change it. The page sends only `on` and `trailing`. Gates in `test/kalshiL1Gates.test.js`. `kalshiL1Session` is deployed with `bash functions/deploy-push.sh` (or a full `firebase deploy --only functions`); the page change goes live on merge.

## The exit watch only closes what the bot opened

`runExitWatch` (`functions/kalshiLiveLib.js`, run by `kalshiLiveExit`) sells a position when the side's bid falls to 25c (it was 70c, then 50c, until Oct 12, 2026, when the owner moved it to 25c). It has no mode and no setting: it always sells while the server's own live switch is on, and only records what it would have sold when that switch is off. It was 70c behind an off / log only / sell switch until Oct 12, 2026, when the owner removed the switch and moved the line; the reinvest pool was fixed to "after every win" the same day (`runL1Tick` always passes `everyWin: true`, nothing stored is read). **Do not add a callable or a page control that changes either one back.** The owner wants this to be an anti-degen site, and a risk setting that can be toggled from the page can be toggled in a bad hour. Note that `CODE_KILL_SWITCH` stops buys and Start only; the exit watch is deliberately not behind it, because it only ever reduces exposure. Its invariants are tested in `test/kalshiExitGates.test.js` and are not to be loosened: it iterates the bot's own order documents (never the account's positions), reads the live position first (a YES sell on a position that is gone would OPEN the opposite one), sells at most what the order filled, claims each sell atomically with a fixed client order id, never retries a lost answer (it ends the session instead), and its only order is an immediate-or-cancel close. **It shares a claim per market with Flatten** (`claimClose`, the `kalshiLiveClosing/{ticker}` documents, 90 second lease, no client rule): whichever of the two holds a market, the other leaves it alone, and the claim is taken BEFORE the position is read; Flatten then reads that one position again and sells exactly what the account holds now (tests E11 to E13, F6 to F8). A sell going out on a position the other closer just sold would OPEN the opposite one. A realised exit is recorded as `settled: true, result: "exit"` with `settledPnl`, which is what the loss stop and the pool read.
## The live series are a hard list in code

Only `L1_SERIES` in `functions/kalshiLiveLib.js` (Bitcoin, gold, Ethereum, XRP, Dogecoin, in that order; XRP and Dogecoin were appended on Oct 20, 2026 so they only ever take a window's second slot) can trade live under the L1 rule. A value stored in Firestore can never add a series; adding one is a deliberate code edit and review (Solana is deliberately absent). Ethereum was a separate switch until Oct 10, 2026 and is now an ordinary L1 series: the same rule, size, loss stop, pool and exit. No callable takes a ticker, price or size from the caller (test L12). Tests X1 to X8 in `test/kalshiL1Gates.test.js`.

**Gold first (Oct 21, 2026, the owner's choice, `docs/GOLD_FIRST_PROPOSAL.md` option A).** `L1_SERIES` is now gold, Bitcoin, Ethereum, XRP, Dogecoin, then the probes. **Gold is the only market that keeps the size ladder and it is sent first.** `CAPPED_SERIES` (Bitcoin, Ethereum, XRP, Dogecoin) are always one contract and never use reinvested profit, the same line as the probes. Why: in the first 302 settled bot trades gold made +$28.35 (2 losses in 98) and every other market lost slightly, the 68 day backtest agrees on gold and nothing else, and Ethereum's losses came in the same window as Bitcoin's. A capped market earns the ladder back only from its own live record (150 settled trades at one contract, a result above +0.5c a contract in both halves) and a ladder-sized market drops back if its last 100 trades are negative: either is a reviewed edit of the list in code, never a stored value. Tests GF1 to GF3. The 12% stop, 5.5% window limit and 25c exit are unchanged.

**The probe markets (Oct 21, 2026, the owner's choice: "live forward testing", no more paper trackers).** `PROBE_SERIES` (AUD/USD, USD/CAD and natural gas 15 minute markets) are the last three entries of `L1_SERIES`: L1's own rule, but ALWAYS one contract per order and never any reinvested profit, whatever the size ladder says. They come after the five series that earned their place, so they only take what a window's combined limit has left, and they count toward the same loss stop, pool, 25c exit and alerts as every other L1 order. They were chosen because history could not settle them (12 days of AUD/USD and USD/CAD, a near miss on gas), not because anything showed an edge; the same day GAS1, APP1 and CMD1 (`kalshi-scalper/README.md`) found nothing to trade. They are L1's rule on more markets, not a second strategy, so the "L1 is the only strategy" rule below still holds. Tests PR1 to PR3. Resting (maker) entries on them are a separate, not yet built, test. **Probe drop rule (Oct 21, 2026, the research session's DL1, the owner: "do it").** A probe is dropped when its last 200 settled entries net negative (`PROBE_DROP_WINDOW`, `probeRingUpdate` in `functions/kalshiLiveLib.js`, record in `kalshiLiveControl/probeRecord`, admin read only). It is an ADMISSION filter for markets that have not earned a place, not a brake: DL1 showed that on Bitcoin, Ethereum, gold, XRP and Dogecoin the same rule would have HURT (they bounce after a bad stretch), so it is never applied to them and the record only ever holds probe series. It only removes a series from what the tick may trade; a dropped probe stays dropped until the record is deleted by hand or the list is edited in code. The record is built from the 24 hours of orders the tick already reads (no extra order reads), skips hand-closed and unsettled orders, and cannot fire until it holds 200 entries (so not before about 2 to 4 days after it is deployed). Fails closed: an unreadable or unsaveable record takes the probes out for that minute and leaves the rest trading. Needs `bash functions/deploy-sizing.sh`. Tests DP1 to DP4. **Early entry probes (Oct 21, 2026, the research session's FWD7 and FWD8, the owner: "live probes at 10 minutes", then "10 minutes only").** XRP and natural gas (`EARLY_PROBE_SERIES`) are entered about 10 minutes before the close (`EARLY_WINDOW_MS`, 9.5 to 10.7 minutes left) INSTEAD of 6: they have no 6 minute window any more, so a market not in the band at 10 minutes is skipped, not tried again, and the 10 minute claim is tested on its own. Same rule otherwise: one contract, the 88c to 97c band, the same loss stop, window limit, pool, 25c exit and alerts. A market is decided once, and both entries would share the client order id `"L1-" + ticker` anyway. Every order records `entryLead` (`"10m"` or `"6m"`); XRP, natural gas and Bitcoin orders from before this change are `6m`, so read them apart (the page's per-market column mixes them). Why: on 69 days of history natural gas earned +3.19c at 10 minutes against +0.52c at 6, XRP +2.91c against +1.47c, Bitcoin +2.53c against +0.45c, but pooled over 18 series 10 minutes missed its bar (z 1.71), so this is a test, not a finding. Cost: the exit watch must run from the early window on (`EXIT_BUY_MINUTES` is now minutes 3 to 10 of each quarter hour), which gives back most of the idle minutes it used to skip, roughly $3 a month of compute. Needs `bash functions/deploy-sizing.sh` and `bash functions/deploy-push.sh`. Tests EP1 to EP3. The research session reads it as FWD8. **Rise logging (Oct 22, 2026, the research session's JUMP1 lead, the owner: "log it").** Every new order (10 minute and 6 minute) gets `rise3` (how far the bought side's mid rose over the last 3 minutes, from the public one minute candles), written AFTER every order of that minute has been sent (`logRise`, tests RL1 and RL2). Logging only: no order waits for it, it reads no key, and a failed or thin read leaves the order exactly as it was. Needs `bash functions/deploy-sizing.sh`. **rng5 (Oct 22, 2026, the research session's FLAT2 lead, the owner: "yes, log rng5")** is logged beside it, the max minus the min of the bought side's mid over the six minute marks from 5 minutes ago to now (left out if any mark is missing); same rules, logging only (test RL3). Needs `bash functions/deploy-sizing.sh`. Both order exports (Copy order diagnostics, Copy all orders) carry `entryLead`, and the full export also carries avgFill, avgFee, the book sizes, rise3 and rng5, so every forward read can split orders by entry time.

**Hand-sold check, fixed Oct 21, 2026.** `closedByHand` (#407) marked every NO order the bot bought as "sold by hand": Kalshi books a NO buy on the YES side (sent as `ask`), so the bot's own entry fill read as a sale, and those orders (losses included) were left out of the stats, the loss stop and the pool. It now ignores the entry order's own fill, does not call an order hand without its entry id, and no longer takes the exit watch's `skipped` as proof; `settleOpenOrders` re-asks every order already marked hand once and settles the wrong ones as what they were (`handRepaired`). Tests H5, H11 to H13.

## One window, one limit

Bitcoin, gold and Ethereum close in the same 15 minutes and move together, so `runL1Tick` holds the account money put into one window (matched by the ticker's time part, counting earlier ticks) to `L1_WINDOW_CAP_FRACTION` (5.5%, raised from 4.5% on Oct 20, 2026 so the last series stops getting 1 contract) of the sizing base, under the loss stop (`L1_SIZED_STOP_FRACTION`, 6% from Oct 20, 2026, **then 12% the same night**: at 6% a full open window ($8.43, counted as lost) plus $6.06 of ordinary settled losses ended the bot, because the window limit left only about $0.80 to $2.30 of room under the stop; one loss of about $3.70 was enough. Open orders are still counted as lost, so 12% of the base is the real worst case; tests W4 and W5 pin both numbers). Series are sent in `L1_SERIES` order (Bitcoin, gold, Ethereum, XRP, Dogecoin), so the later ones are the ones that go without. The add-on (profit) is not counted; the first order in a window is never cut to zero. Tests W1 to W3 in `test/kalshiL1Gates.test.js`.

## One crypto order per window (Oct 22, 2026)

Bitcoin, Ethereum, XRP and Dogecoin (`CAPPED_SERIES`) now place at most ONE order per 15 minute window (`runL1Tick`, first in `L1_SERIES` order wins; an order that did not fill does not hold the window). Why: the research session's live diagnosis found 72% of recent loss dollars came from three windows where two of them lost together. Gold and the probes are not part of the rule. History is in-sample and the rule roughly halves the expected crypto profit, so it is a test: read it on the live record, not the backtest. Test OC1. Needs `bash functions/deploy-sizing.sh`.

## A refused read is asked once more (Oct 22, 2026)

`liveRequest` (`functions/kalshiLiveLib.js`) asks a GET that Kalshi answers with 429 once more after 1.2 seconds. An order (any POST) is still never retried, which is what gate L10 protects and test RR1 proves. Why: the balance and position reads share one key with the exit watch's 10 second loop, and one refused read skipped a minute's entries and put "The account could not be read: HTTP 429" on the Bot page. Needs `bash functions/deploy-sizing.sh` and `bash functions/deploy-push.sh`.

## The quote recorder pilot (Oct 22, 2026, research only)

`.github/workflows/record-quotes.yml` and `scripts/record_quotes.py` record Kalshi's 15 minute crypto quotes (Bitcoin, Ethereum, Solana, XRP, Dogecoin; best bid, ask and sizes about twice a second in the last 150 seconds of each window) next to the public trade feeds of Coinbase, Kraken and Bitstamp (the 10 minutes before each close), plus each market's result, a per-window coverage count and an hourly clock check. It exists for the research session's RECORD1 (do Kalshi's quotes lag spot in the last two minutes). It is a ONE DAY PILOT first: its job is to show how many windows a free runner catches (late scheduled jobs, Kalshi's public read limit) before anyone commits to 14 days. It holds no key and no secret, places no order, reads only public data, and the built-in token only pushes gzipped files to the `quote-data` branch, never to main (`test/quoteRecorderGates.test.js`). Nothing about the bot changes.

## L1 is the only strategy (Oct 12, 2026)

The opening window paper recorder (`OW1`, `kalshiOpeningTick`, `kalshiOpeningLib.js`) and the page's Closing / Opening / Both switch were removed at the owner's request ("lets go back to only L1 for now"): the strategies must not overlap in mindset or position, and anything that holds to settlement overlaps L1 in both. Nothing profitable that is flat before L1 buys exists in the history: `OW2` (four variants) and `SS1` (216 cells, a train and validation search) are all `FALSIFIED` in `kalshi-scalper/README.md`, and every earlier scalp family fell to cost. `test/kalshiL1Gates.test.js` K10 and `test/kalshiLayoutGates.test.js` Y41 pin the absence. The research record (`kalshi-scalper/`, `docs/OPENING_STRATEGY.md`) stays as history; the old `kalshiOpeningOrders` and `kalshiOpeningControl` documents are untouched in Firestore and have no rule, so nothing can read them. A second strategy is a deliberate, reviewed change that must show how it cannot hold a position at the same time as L1 and why it is a different bet, not a different lane of the same one.

## How to talk to the owner (standing rules, set 2026-10-20, updated 2026-10-21)

- Keep replies short and plain. Lead with the result and the numbers. Assume the owner remembers nothing from earlier in the conversation, so say where a thing is and what it is.
- **Offer choices with the pop-up menu (the AskUserQuestion tool), not a numbered list typed into the reply** (the owner, 2026-10-21: "from now on in this project"). Put the recommended option first and mark it "(Recommended)". A closing line of text is still fine for what happens next, but the choices themselves go in the pop-up.
- Never use em dashes. Use they/them for anyone whose pronouns are not stated.
- Never ask for, or accept, credentials, keys or sign-in codes in chat.
- Merge a pull request only when the owner says so. Keep the current look: no new design system (see Conventions).

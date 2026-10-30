# shwoopnet

Frontend for a personal dashboard (Pocket Advisor): the Market Brief, the
Kalshi page and Settings, and nothing else since Oct 12, 2026 (see "The blank
slate" below). Firebase auth + Firestore, deployed to GitHub Pages. The Kalshi
bot runs from `functions/` here. `shwoop-server` is a separate repo, the old
Alpaca equities server on Render. **It was suspended on Oct 26, 2026 and is
retired** (see "Alpaca and the Render server" below); nothing on this site
depends on it.

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
- **`research-director`** and the **`research-director` agent** (`.claude/skills/research-director/`, `.claude/agents/research-director.md`, Oct 28, 2026, the owner: the research session "only continually works on the same thing over and over") — watches the research session every few days and keeps its search broad. `node .claude/skills/research-director/scripts/scoreboard.js --days 14` counts how much recent work was variants of L1 (the first read, on 2026-10-13: 25 of 36 registrations, and 5 of 5 in the last week) and lists market families never mentioned (weather, economic releases, sports, events, calibration, cross-market). The skill then drafts up to three briefs (family, counterparty, information source, numeric prediction, kill criteria) **for the owner to approve first**; it never sends one, has no Edit or Write tool, never touches trading code, never deploys and has no promote verb. Its success bar is fixed in `SKILL.md` before any result: profit factor 1.5 or better in each of three windows after the fee and after deflating for the number tried, with a named counterparty. It does not promise positive weeks. `test/researchDirectorGates.test.js`.
- **`ask-the-advisors`** — six-perspective board for project decisions.
- **`unlazy`** — vendored from upstream (see its `PROVENANCE.md`). Writes
  acceptance gates before the work and re-measures them before reporting,
  so a confident "done" has to survive a check. Its `CHECK:` lines are
  shell commands — read `SECURITY.md` before running a ledger this repo
  didn't write.

## The blank slate (Oct 12, 2026)

At the owner's request ("an anti-degen proof website ... to prevent myself from full porting") the site was cut down to the Market Brief, the Kalshi page and Settings. Gone: the Trade Overview, Journal, Changelog, Notes and History, the ticker tape, the account dock and the trade modals; the Alpaca, Finnhub and Twelve Data integrations (and the Twelve Data proxy secret that sat in the page in plaintext); creating an account from the page, and the invite generator. `test/blankSlateGates.test.js` and `test/removedFeaturesStayRemovedGates.test.js` hold the line: three pages, a fixed list of hosts and of Firebase methods, exactly the Settings rows that exist, no sign-up. A new row, host or method has to be added to those gates on purpose; that is the point.

The Brief and the market strip make no market-data call of their own. (The Bot page's price charts and their Coinbase and gold-api.com reads were removed on Oct 23, 2026 at the owner's request, so the page now calls no price feed at all; test Y16 pins it.) The Brief and the market strip read `shared/marketTape`, which the keyless scheduled function `marketTapeTick` (`functions/marketTapeLib.js`, every 5 minutes, public Yahoo chart prices and CNBC and MarketWatch RSS, no secret) writes; since Oct 23, 2026 the Brief is the market news, a risk mood (a word from the VIX, the stocks and crypto fear and greed indexes, the VIX, the 10 year yield and long bonds) and three chart pairs (Bitcoin and Ethereum, SPY and QQQ, gold and crude oil), all from the tape (`mood` from CNN's and alternative.me's public fear and greed readings, `series` the day's closes per quote). The market strip scrolls again in the header, between the logo and the clock; its Movers, Sentiment and Earnings sections were removed, so the page reads `shared/marketSnapshot` (which shwoop-server writes) only as a news fallback. **shwoop-server, which used to trade Alpaca for any account with keys stored, was suspended on Oct 26, 2026 and is retired.** One convenience was added back on Oct 20, 2026 at the owner's request: optional sound alerts on the Kalshi page (a tone for an entry, a sell, and a stop or issue, while the page is open). It is a switch in Settings, Notifications (admin only, moved there Oct 23, 2026), off by default, kept in this browser's localStorage only, never a browser Notification and never a Firestore setting (`test/kalshiSoundGates.test.js`). **Phone alerts** were added the same day (Web Push, the owner's own Cloud Functions, no third-party service): a "Phone alerts" switch in Settings, Notifications, `sw.js` and `manifest.webmanifest` at the site root, and the functions `kalshiPushKey`, `kalshiPushSubscribe`, `kalshiPushUnsubscribe`, `kalshiPushOrder` and `kalshiPushSession` (`functions/kalshiPushLib.js`, `test/kalshiPushGates.test.js`). They only READ what the bot wrote (an order changing, the session ending), hold no Kalshi key, are imported by no trading code and catch every error. The page may ask for notification permission exactly once, from the owner's tap (`test/removedFeaturesStayRemovedGates.test.js` G1). It alerts on every CLOSE (an early sell, and a trade settling as a win or a loss, with the amount) and on a stop or issue; a buy never alerts (the owner, Oct 26, 2026: "my phone gets notifications constantly", then "add in closes ... eliminate the entries"; `orderKinds`, tests P1); the owner's own Stop and Flatten are silent. Needs `bash functions/deploy-push.sh`. On an iPhone it works only from the Home Screen app. `functions/deploy-push.sh` is the one laptop deploy for it, and keeps an existing push key (replacing it would orphan every subscribed phone). Much of what is written further down about the equities strategy, the Labs page and the account dock describes code that no longer exists; it is kept as the research record, and git history has the code.

[REMOVED from the page Oct 27, 2026, see the note after this section] **Order flow (footprint), Oct 26, 2026, the owner: "build the footprint view", read only.** A closed fold on the Bot page (`data-card="footprint"`, `kalFpFold`, `kalshiFpModel`, tests F1 to F10 in `test/kalshiFootprintGates.test.js`): for one of the bot's markets, one column per minute and one row per YES price in cents, each cell the contracts takers sold (left) and bought (right), plus a delta bar and a running total, with the bot's entry, early sell and the close marked. The data is Kalshi's PUBLIC trade tape through the owner's own admin-only function `kalshiTape` (`functions/kalshiFootprintLib.js`, GET only, keyless, only series in `L1_SERIES`, at most the last 48 hours); the page names no Kalshi host and reads nothing until the fold is opened. It writes nothing and changes no trading rule; the research session found no trade-tape rule that predicts the 15 minute outcome, so this is a reading tool, not a signal. **Whole series (Oct 26, 2026, the owner: "30 minutes or 1 hour, since we work in 15 min increments").** Choosing a series (Gold, XRP, Bitcoin, Dogecoin, Ethereum; `KAL_FP_SERIES`) instead of one market shows its last 30 minutes or hour stitched across its 15 minute windows, with a line at each close (`validSeries`, `seriesWindow`, `windowsFromMarkets`, tests F11 to F14): the function lists the series' markets from Kalshi's public market list and reads each one's trades, at most 6 markets and 8,000 trades. A new deploy of `kalshiTape` is needed for it. Needs `npx firebase-tools deploy --only functions:kalshiTape --project shwoopnet` (keyless, no switch needed).

[REMOVED from the page Oct 27, 2026, see the note after this section] **Big prints (Oct 26, 2026, the owner: "do we have any flashy highlights for unusual activity? whales?").** The function also returns the 8 largest single trades of the window (`bigPrints`, tests F15 to F17), each with how many times the median trade size it is; a print of at least 5 times the median and at least 50 contracts is BIG. The fold lists them above the grid (the big ones bold with a diamond) and rings the cell of a big print in the grid. White and grey only, no animation, no alert, nothing on the phone and nothing in the bell: the owner's calm view and the phone-alert history say a whale must never buzz. A new deploy of `kalshiTape` is needed.

[REMOVED from the page Oct 27, 2026, see the note after this section] **Where the edge is (Oct 27, 2026, the owner: "build out our own formational chart ... with a REAL strategy behind it", after a mock-up of an institutional gamma surface).** A closed fold on the Bot page (`data-card="surface"`, `kalSfFold`, `kalshiEdgeModel`, `kalSurfMeshDraw`, tests S1 to S8 in `test/kalshiSurfaceGates.test.js`): every settled L1 order in a cell by the price it PAID for the side bought (88c to 97c, a NO order's fill is converted by `kalshiPricePaid`) and the US Central time of day (three hour blocks); the number is the net result in cents per contract after fees. A cell with fewer than 10 trades is blank and carries no edge, never a smoothed hill. Drawn as a wireframe mesh surface on a canvas (the owner chose it over a heatmap, columns, ridge lines, price curves and bubbles, Oct 27, 2026): a point at the centre of every readable cell, joined only to readable neighbours, so a thin cell is a HOLE and the sheet never claims a value it was not given; CAD style controls shared by both surfaces (`kalSurfAttach`, test S10): drag to orbit a full 360 degrees and over or under (tilt held to straight up or down), scroll or pinch to zoom, shift or right drag or two fingers to pan, arrow keys, Iso, Top, Front, Side and Reset buttons, double click to reset; touch or hover a point for its trades and win rate. Market and entry time (10 or 6 minutes before the close) are filters. It reads the orders the page already holds and has no server call, no storage, no timer and no animation. **It is a reading tool, not a signal:** the research record says nothing found so far predicts the outcome, so a pattern here is a question for the research session, to be pre-registered and tested forward, never a rule that changes an order or a size. Nothing to deploy; it goes live on merge.

[REMOVED from the page Oct 27, 2026, see the note after this section] **Order flow landscape (Oct 27, 2026, the owner: a surface that is "useful" for the 3D charting they wanted, "1 maybe" of three candidates).** The Order flow fold has a View choice: Grid (as before), Landscape of contracts traded, or Landscape of net buying (`kalFpLandscapeModel`, `kalSurfAttach`, test F18). The same trades as the grid, drawn as the mesh used by "Where the edge is": time one way, price the other (binned to at most 28 rows), height the contracts in that minute at that price, or bought minus sold with selling in GREY, never red (a seller or a whale must not look like a loss). A minute and price with no trade is a real zero, so the surface is filled; the height is lightly smoothed (weights 1, 2, 1) so the shape reads, and the readout always gives the raw counts. Public trades only, no new read, no order. The research session found no tape rule that predicts the 15 minute outcome, so it is for reading where the flow went, not a signal. Nothing to deploy; it needs the `kalshiTape` already deployed.

**Order flow and the 3D edge chart are off the page for now (Oct 27, 2026, the owner: "we can remove that 3d graphic, and the orderflow charts for now").** The Bot page no longer has the Order flow fold (grid and landscape views) or the "Where the edge is" mesh surface: their cards, CSS, JavaScript, the page's `kalshiTape` call and the page gates (`test/kalshiSurfaceGates.test.js`, the page model gates in `test/kalshiFootprintGates.test.js`) are gone. Left in place on purpose, so putting them back is cheap: the deployed function `kalshiTape` and `functions/kalshiFootprintLib.js` (with their server gates F1 to F6, F9, F11, F12, F15, F16), nothing on the page calls them. The code is in git history (pull requests #577 to #594, the last page version is the one before the removal in #595). Do not re-add either without the owner asking. The four paragraphs above describe what was built.

## What each page is for (Oct 23, 2026, the owner)

**Trim (Oct 24, 2026, the owner: "remove anything that doesn't NEED to be seen").** Gone from the Bot page: the shard balances and low-shard warning, the "Usual day" range bar, the "Next 7 days, as a range" chart, the loss stop card's Open orders and Fullest open window rows, and in Tools the Print statement and Copy all stats exports (`kalshiStatsText`, `kalshiStatementHtml`, `kalshiExitReport` deleted; Copy all orders and Copy order diagnostics stay). The loss stop meter is called **Stop Loss and Risk** and sits at the bottom of the Account card (it was its own card, then folded into Bot status, then moved here; the Account result card now sits beside Bot status). The Limit graphics switch is gone from Settings: the device's reduce-motion setting is the only input to the motion rules. Reinvest pool, Stake per trade and the Brief are unchanged. The gain/loss text colour is `--loss-text` (lighter than the safety red `--loss`, which bars and the banner keep).

**Notification center (Oct 25, 2026, the owner: a bell with a red bubble for unread, a Mark all as read, and a differentiator for the worst cases).** A bell in the top navigation, first, to the left of Brief (the owner, Oct 25, 2026: "up here to the left of brief", "not down by layout/privacy in bot"; admin only, on every page, a bottom bar item on a phone; until the Bot page has loaded its orders the panel says so) (`kalNotifBtn`, `renderKalshiNotifications`, tests N1 to N5) opens a panel of what the bot did, built from the event log and the orders the page already loads (no new read, nothing written to the account). Three levels: critical (the bot stopped by itself, an order or exit whose answer was lost or refused), warning (an early sell, a loss, a dropped test market), info (a buy, a win, anything else). The default tab is Important (warning and critical); Everything adds the info lines. The red bubble counts UNREAD warning and critical items only, so a busy day does not bury a problem; Mark all as read sets one number, the time of the click, kept in this browser only (`localStorage` `shwoopnet:notifRead`, never the account), and the first visit starts with nothing unread. The worst cases also raise a red banner across the top of the Bot page (`kalAlert`, `kalshiCriticalNow`): the bot stopped by itself, an order that needs checking (last 24 hours), or no check for several minutes. The banner does NOT clear when read; it stays for as long as the condition is true. Dollars go through `kalshiMoney`, so Privacy view masks them. The bell fills on every page (the owner, Oct 25, 2026: "constantly filling up, regardless of whether I have the bot panel open"): the order, event, control and halt listeners start for the admin at sign-in (`startKalshiFeed`, test N6), not when the Bot page is shown, and `kalshiFeedRender` redraws the whole Bot page when it is showing and only the bell and banner when it is not. The cost is the Bot page's first load (the last orders and events) on every admin page load, then only changes. The account read, the heartbeat strip and the ECG stay Bot page only, and sound alerts still play only on the Bot page. With the page closed the phone alerts (Web Push) are what report; a stored backend feed was not built. Phone alerts are separate and unchanged. A settlement is stamped at the market's close, worked out from the ticker's Eastern time (`kalshiCloseFromTicker`), since orders carry no settle time.

**Landing page wallpaper (Oct 25, 2026, the owner: "that same trade less live more text background" on the landing page).** The sign-in screen has its own copy of the slogan wallpaper (`.gate-slogan`, identical look to `.bg-slogan`, test BG2) because the gate is a fixed layer above the page.

**Silent-market warning (Oct 24, 2026, the owner: "make a warning in case a strategy stops running for whatever reason").** The Bot status card adds an amber "Needs a look" block (`kalshiSilentMarkets`, `KAL_WATCH`, test file `test/silentMarketGates.test.js`) when a market has sent no order, filled or not, for more than 8 times its own median gap of the last 3 days (never under 3 hours; it needs 8 orders in those 3 days). Bitcoin and Ethereum are left out because the smooth climb rule makes them quiet by design. Gold, the forex pairs and natural gas are not checked from Friday 17:00 to Sunday 18:00 Central, and their clock restarts at the reopening; XRP and Dogecoin are checked all week. It replaces the removed shard warning in spirit: a dry shard shows up as a silent market. It only reads and can warn wrongly (a holiday), never act; the bot as a whole stopping is still said by the Running pill and its reason. A new series in `L1_SERIES` must be added to `KAL_WATCH` or deliberately left out (test S7).

**Chart axes (Oct 24, 2026, the owner: "include like an x/y axis for % (y) and date (x) on the charts", then "actually built out, functional and useful").** The Account result line is a step line on a real time axis (the range start, or the first trade, to now) with round percentage ticks of the account at the start of the range on the right and Central dates (or hours, for a day) underneath, and a hover or touch scrub that shows each trade's result and time. The Brief charts have a y axis in percent against the previous close (0% is the dashed previous close) and an x axis of Central hours. The hours need `seriesT`, the unix second of each point, which `marketTapeTick` now writes beside `series` (`chartPoints` in `functions/marketTapeLib.js`); until `marketTapeTick` is redeployed (`firebase deploy --only functions:marketTapeTick --project shwoopnet`, keyless, no switch needed) the page says only "Day start" and "Now", never a made-up time. Labels are HTML laid over the chart (12px), not text in the scaled SVG. Tests PL1 to PL3, H1 to H4, T21b.

**Brief charts are a week (Oct 26, 2026, the owner: "update those to weekly and update a little bit less frequently to cut down on costs", for the Brief only).** `marketTapeTick` now runs every 15 minutes (it was every 5) and makes two Yahoo reads per symbol: today at 5 minutes for the quote (price, previous close, session state, so the header strip keeps its daily move) and 7 days at 1 hour for the chart line, marked `range: "7d"` with its own `seriesT`. The Brief chart measures a weekly line from its own first point (the header move and the dashed zero mean "since the start of the week", the x axis starts at "Week start" when it has no times); without the marker, or if the weekly read fails, it is today's line against the previous close as before. The page's stale warning is 45 minutes (three missed runs). The market strip's prices are therefore up to 15 minutes old. Tests T21d, H5. Needs `npx firebase-tools deploy --only functions:marketTapeTick --project shwoopnet`.

**Account result line (Oct 24, 2026, the owner: "bring back our account PnL line ... with a date filter").** The first card in the Bot page's main column (`data-card="pnl"`, `renderKalshiPnl`): the running settled result of the bot's orders, with Today, 1W, 1M, 3M, YTD and All buttons. It draws from the last 1,000 orders the page listens to; a range that starts before the oldest of them reads the orders from that time once (`kalshiOrdersSince`, about one read per order, kept ten minutes), so YTD, 1Y and All are real, and the card says so if the bot is younger than the range. The buttons change what is drawn and nothing else; dollar figures go through `kalshiMoney`, so Privacy view masks them (test PL1).

**Bot** is the overview and the live watch: the account strip (state, balance, stake, pool, today), Open positions and Recent trades, and the account result line (below) and nothing else (no market list; the one chart is inside Open positions, Oct 23, 2026: each position's row draws the chance of the side bought from the reads the page has made since it was opened, `kalshiPositionChartHtml`, test PC1, no price call of its own; the relay is still read in the background because Open positions takes each position's time left and price from it). There is no Data page any more (removed Oct 24, 2026, see "The Data page" below). **Brief** is the news and all market information, the broader view. A new module goes on the page whose job it is.

**Changelog (Oct 25, 2026, the owner: "i also dont see ... the changelog in the settings page"; the owner chose a changelog written from the GitHub merges and skipped a Feedback area).** A Changelog row in Settings, closed by default, static HTML grouped by day, newest first, one plain line per change with its pull request number (`changelog-list`, test B4). **Every merged pull request adds a line**, in the same pull request. It was removed with the other pages in the blank slate and is back only as this one row. A Feedback area was offered and declined.

## Alpaca and the Render server (retired Oct 26, 2026, the owner: "lets start cutting alpaca from everything on our site")

The page has named no broker or data vendor since Oct 12 (`test/removedFeaturesStayRemovedGates.test.js`). The last live piece was `shwoop-server` on Render, whose `main` still ran the old per-account scheduler (a heartbeat every minute that scanned the whole `users` collection and loaded each connected account's user document, plus the Alpaca equities and options cycles, a market snapshot every 3 minutes and an option chain recorder). Because Render is outside Google, every one of those Firestore reads was billed as **Cloud Firestore Internet Data Transfer Out**: 135.52 GiB and $15.06 in October 2026 against $0.67 for all the reads, about 5.4 GiB a day. That was the single biggest avoidable line on the bill. The owner suspended the service on Oct 26, 2026. Check Billing, Reports, grouped by SKU: that line should fall to near zero within two days. If it does not, the source is somewhere else and this section is wrong.

What stopped with it: Alpaca trading, the Brief's news fallback from `shared/marketSnapshot` (the tape has its own news) and the option chain recorder. The Kalshi bot, the tape and the phone alerts run on Cloud Functions in the same region as Firestore, which is not billed as internet transfer, and were not touched. **To finish the cut (the owner, in the consoles; nothing here can do it):** delete the Alpaca fields from the admin `users/{uid}` document (`alpacaKeyId`, `alpacaSecretKey`, `alpacaLiveKeyId`, `alpacaLiveSecretKey`, `alpacaEnvironment`, and the old `journalEntries` and other removed-page fields), revoke the keys in the Alpaca account, and delete the Render environment variables or the whole service. `firestore.rules` still keeps the admin-only guard on live credential fields; it is harmless and stays until those fields are gone.

## The Data page, and why it is gone (Oct 21 to Oct 24, 2026)

A fourth page, **Data**, was added Oct 21, 2026 ("start building out a data center page"): admin only, read only. Over three days it was rebuilt four times (a dashboard of tiles, tables and charts; six question folds with a ranked "Needs your eye" list; one screen; a headline with a dot per trade) and the owner liked none of them ("idk if i like the data page"), so on **Oct 24, 2026 the page, its nav button and its charts were removed** (`test/dataCenterGates.test.js` DS1 pins the absence; the site is Brief, Bot, Settings). What survived for a day was a small **record** card at the bottom of the Bot page (a headline and the rules on trial); the owner removed that too on Oct 24, 2026 ("lets remove this entirely"), so nothing of the Data page is left on the site. Everything else the Data page carried lives only as text: Copy all stats, Copy all orders and the printable statement in Tools (`kalshiStatsText`, `kalshiStatementHtml`). `docs/DATA_PAGE_IDEAS.md` keeps 44 ideas that were never built. Do not rebuild a Data page without the owner naming what it is for.

On the Bot page a minute the bot skipped is said plainly ("Skipped a minute (time): ... It looks again every minute."), and a 429 explains itself (gate D11).

**Slogan and sign-in logo (Oct 23, 2026, the owner).** The slogan is **Trade less. Live more.** (it was "We trade. You live your life."); the signed-out tab title, the link preview text and `og-image.png` carry it. The signed-out screen is simple and professional (the owner, Oct 23, 2026: "we have to look and be professional now that we are an LLC", "simple", "a snapshot of our account page and our market brief"): black with one accent, the wordmark, a small sign-in in the top right, the slogan in Titan One (the one deliberate exception to "Titan One is the wordmark only", `test/bubblePopGates.test.js` P1), the line "Shwoop Financials builds systematic trading tools: rules written in advance, run by software, reviewed by people.", and two window snapshots of the Account page and the Market Brief drawn in CSS with every figure and label blurred to bars (the page is public, so it shows the layout and no numbers, markets or results). It has its OWN palette on `.auth-gate` and one layout, two windows; there is no colour or layout choice any more (the owner, Oct 23, 2026: the whole site is black and white; `test/frontPageGates.test.js` pins the absence). The footer says "Shwoop Financials, LLC". It is only a layer over the same gate: every id the sign-in code uses is unchanged, it follows the theme and skin, and it says nothing about the bot's markets, size or results and makes no performance claim because it is public (`test/frontPageGates.test.js`, `test/signInWordmarkGates.test.js`). The Running panel on the Bot page's Account card is anchored to the whole card (same width, above the cards after it). The shirt and hoodie artwork is merchandise only and lives outside this repo.

**Fonts are local (Oct 22, 2026).** Public Sans, IBM Plex Mono and Titan One are served from `fonts/` (Latin subset, SIL Open Font License, see `fonts/README.md`), not from a font service, so the page makes no font request and a visitor's network address stays on this site. `test/selfHostedFontsGates.test.js` checks the files, the rules and that no font host is referenced; `blankSlateGates` no longer allows the font hosts and `motionHonestyGates` now expects zero outside resources.

**Printable statement and "as of" stamp (Oct 22, 2026, the owner: make the site feel official).** Tools, Export has a month picker and **Print statement** (this month or last month, US Central): a plain document of that month's settled trades (summary, by market, every trade), opened in a hidden frame so the browser's print dialog can save a PDF (`kalshiStatementHtml`, gate D13). It is an export, so its dollar figures are raw and not masked by Privacy, like Copy all orders. It is deliberately in Tools, not on a page that must stay read only.

**Bubble pop (Oct 21, 2026, the owner: "more visual appeal and interactivity").** Titan One is for the WORDMARK ONLY (and its ghost behind the page): the owner said bubble text is good for the logo but not the whole site, and the black blocky headings looked like a game (Oct 21, 2026, gate P1). Page and card headings, market names and Settings titles are Public Sans bold with no bubble shadow. **Every number is in Public Sans with tabular digits** (stat tile figures, the market strip prices, chart end label, ring total and weekly values, the account total): the owner found Titan One figures like 774.14 hard to read (Oct 21, 2026, gate P1). Do not set a number in Titan One. Motion is decoration only and never moves a number: cards rise in once when a page is shown (`pageEnter`, the class comes off after 2.2 s so the minute's re-render never replays it), there is no cursor spotlight (removed Oct 21, 2026 at the owner's request; a gate keeps it out), cards and tiles lift 2px, chart lines draw in and bars pop in once, ring slices and weekly bars react to hover. Every one of these is off under the OS reduce-motion setting and the Settings switch, (`test/bubblePopGates.test.js` P1 to P6, plus `motionHonestyGates`). Do not add a count-up or any animation on a figure. **Light themes readable (Oct 21, 2026, the owner: "hard to read" in both light modes).** In the light themes the blurred blobs, the grid and the ghost wordmark are quieter (they are tinted with `--amber`, which is black in Mono Ink, so on a light page they greyed everything behind the text), secondary text and card borders are darker, Mono Ink light sits on a light grey ground so white cards stand out without shadows, and stat tiles get a white fill. Dark is unchanged. The wordmark never changes colour on hover (it turned black in Mono Ink, where `--amber` is black): the letters hop instead, off under reduce motion (gate P7).

**Bot page, second cleanup (Oct 21, 2026, the owner).** No big "Bot" title beside the updated time, no Data button in the header (the sidebar has it), the header toggle is called **Privacy** (it masks dollar amounts as ****), and the **Performance card moved off the Bot page**: "How the orders ended" and "Each settled trade" now live on the Data page, the duplicate P/L line and the all-sessions/this-session choice are gone (the Data page is read only, so it has no select).

**Bot page cleanup (Oct 21, 2026).** The Kalshi page is called **Bot** in the sidebar, the landing choice and its own title (ids and stored values still say `kalshi`). The account card is now only status and controls (stake, pool, and a "Today" line: the bot settled result for today on the US Central date, which replaced "Bot since <date>" on Oct 21, 2026; since Oct 22, 2026 it also shows a percentage of the account total at the start of the day, `kalshiTodayPct`, gate D12); the stat tiles, By market and By price paid moved to a closed "All the numbers" fold at the bottom of the Data page (same element ids, same Copy all stats). The Tools menu is grouped (Account, Export), and the Rules and limits text lists the real markets, the gold-only size ladder, the 5.5% window limit and the 12% stop.

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

**Size after a loss stop (Oct 23, 2026, the owner: "i asked to have that removed").** Nothing holds the size climb after a loss stop any more: the review still steps up one contract every 3 days, and Stop then Start (the reseed) goes straight to the balance target, one contract per $43. The profit add-on hold went on Oct 13, 2026 and this cap hold was the one left behind. The 12% loss stop is what bounds a bad run. **Raising the size by hand (Oct 20, 2026).** The owner may still edit `cap` (a number) and `base` (the balance minus `saved`, the figure the 12% loss stop is measured from) in the Firestore document `kalshiLiveControl/sizing`; the bot reads it on its next minute. Set `base` too: a stale tiny `base` makes the loss stop end the bot at the first trade.

**`deploy-sizing.sh` deploys only `kalshiLiveArmed` and `kalshiBooks`.** A change to the exit watch, Flatten or the alert functions needs `functions/deploy-push.sh` (or a full `firebase deploy --only functions`), and either must keep `KALSHI_LIVE_ENABLED=on` in the gitignored `functions/.env`, or the exit watch stops selling. `functions/deploy-paper.sh` deploys only the paper tracker and the Firestore rules and needs no switch.

## Conventions

- Comments explain **why**, not what. Several exist specifically to stop a
  future change from reintroducing a bug; keep them.
- **The look is the front page (Oct 23, 2026, the owner: "we're making EVERYTHING match the front page", "except our logo").** Read `docs/DESIGN_SYSTEM.md` before touching any style: black and white palette, soft 16px windows, the rail shape, Public Sans type, the gradient ground, the motion rules and the voice. There is no Ledger, no Mono Ink, no dark-mode switch and no colour choice any more. Do not introduce another design system; change the file first if the look must change. The logo is not part of it and stays as is.
- **Calm view on the Kalshi page (Oct 21, 2026, the owner: it "looks like a christmas tree" shown from across a room).** Green and red are kept for the few things that carry the verdict: the "Today" line, the end label of the P/L line, the losing bars and the lost slice of the ring. Every other figure (stat tiles, By market, By price paid) is plain text with its sign; the P/L line is one plain stroke; winning bars and the Won slice are neutral; the market rows show the name, time left and YES price only. Do not add a new coloured figure without taking one away. The gain and loss tokens themselves are unchanged (gates Y8, Y14). **Privacy view** (the Privacy button on the Bot page, or the one switch in Settings; Oct 23, 2026 the owner tried one switch per kind of figure and went back to all or nothing) shows **** in place of raw dollar amounts only (the sign stays; percentages and chances are never masked) and hides the Tools menu, through a page attribute and one flag (`kalshiMasked`); since Oct 23, 2026 (the owner: "we don't want to accidentally leak anything") the choice is kept in this browser only (`localStorage` `shwoopnet:privacy`, never the account) and a head script restores it before first paint (gate Y11c). Every dollar figure on the Bot page must go through `kalshiMoney`, so one flag masks them all; exports use `kalshiMoneyRaw` and are never masked. It changes no number and no control that can change the bot.
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

**The probe markets (Oct 21, 2026, the owner's choice: "live forward testing", no more paper trackers).** `PROBE_SERIES` (AUD/USD, USD/CAD and natural gas 15 minute markets) are the last three entries of `L1_SERIES`: L1's own rule, but ALWAYS one contract per order and never any reinvested profit, whatever the size ladder says. They come after the five series that earned their place, so they only take what a window's combined limit has left, and they count toward the same loss stop, pool, 25c exit and alerts as every other L1 order. They were chosen because history could not settle them (12 days of AUD/USD and USD/CAD, a near miss on gas), not because anything showed an edge; the same day GAS1, APP1 and CMD1 (`kalshi-scalper/README.md`) found nothing to trade. They are L1's rule on more markets, not a second strategy, so the "L1 is the only strategy" rule below still holds. Tests PR1 to PR3. Resting (maker) entries on them are a separate, not yet built, test. **Probe drop rule (Oct 21, 2026, the research session's DL1, the owner: "do it").** A probe is dropped when its last 200 settled entries net negative (`PROBE_DROP_WINDOW`, `probeRingUpdate` in `functions/kalshiLiveLib.js`, record in `kalshiLiveControl/probeRecord`, admin read only). It is an ADMISSION filter for markets that have not earned a place, not a brake: DL1 showed that on Bitcoin, Ethereum, gold, XRP and Dogecoin the same rule would have HURT (they bounce after a bad stretch), so it is never applied to them and the record only ever holds probe series. It only removes a series from what the tick may trade; a dropped probe stays dropped until the record is deleted by hand or the list is edited in code. The record is built from the 24 hours of orders the tick already reads (no extra order reads), skips hand-closed and unsettled orders, and cannot fire until it holds 200 entries (so not before about 2 to 4 days after it is deployed). Fails closed: an unreadable or unsaveable record takes the probes out for that minute and leaves the rest trading. Needs `bash functions/deploy-sizing.sh`. Tests DP1 to DP4. **Early entry probes (Oct 21, 2026, the research session's FWD7 and FWD8, the owner: "live probes at 10 minutes", then "10 minutes only").** XRP and natural gas (`EARLY_PROBE_SERIES`) are entered about 10 minutes before the close (`EARLY_WINDOW_MS`, 9.5 to 10.7 minutes left) INSTEAD of 6: they have no 6 minute window any more, so a market not in the band at 10 minutes is skipped, not tried again, and the 10 minute claim is tested on its own. Same rule otherwise: one contract, the 88c to 97c band, the same loss stop, window limit, pool, 25c exit and alerts. A market is decided once, and both entries would share the client order id `"L1-" + ticker` anyway. Every order records `entryLead` (`"10m"` or `"6m"`); XRP, natural gas and Bitcoin orders from before this change are `6m`, so read them apart (the page's per-market column mixes them). Why: on 69 days of history natural gas earned +3.19c at 10 minutes against +0.52c at 6, XRP +2.91c against +1.47c, Bitcoin +2.53c against +0.45c, but pooled over 18 series 10 minutes missed its bar (z 1.71), so this is a test, not a finding. Cost: the exit watch must run from the early window on (`EXIT_BUY_MINUTES` is now minutes 3 to 10 of each quarter hour), which gives back most of the idle minutes it used to skip, roughly $3 a month of compute. Needs `bash functions/deploy-sizing.sh` and `bash functions/deploy-push.sh`. Tests EP1 to EP3. The research session reads it as FWD8. **Rise logging (Oct 22, 2026, the research session's JUMP1 lead, the owner: "log it").** Every new order (10 minute and 6 minute) gets `rise3` (how far the bought side's mid rose over the last 3 minutes, from the public one minute candles), written AFTER every order of that minute has been sent (`logRise`, tests RL1 and RL2). Logging only: no order waits for it, it reads no key, and a failed or thin read leaves the order exactly as it was. Needs `bash functions/deploy-sizing.sh`. **rng5 (Oct 22, 2026, the research session's FLAT2 lead, the owner: "yes, log rng5")** is logged beside it, the max minus the min of the bought side's mid over the six minute marks from 5 minutes ago to now (left out if any mark is missing); same rules, logging only (test RL3). Needs `bash functions/deploy-sizing.sh`. **flips0 (Oct 23, 2026, the research session's FLIPS0 lead, the owner: "go")** is logged beside them: `flips` (direction changes in the bought side's 1 minute mid path from the market's first candle to the decision candle, minute changes of 0.004 or less ignored), `flips0` (at least 4 earlier candles and no flip), `earlierCandles` and `askAtDecision`; same rules, logging only (tests FL1 reproduces the six parity vectors, FL2). Needs `bash functions/deploy-sizing.sh`. **Two-stage look (Oct 24, 2026, the research session's TWOSTAGE log request, the owner: "Yes, build it (log only)")** is logged beside them: `ask10`, `side10`, `inBand10`, `ask8`, `side8`, `inBand8`, `ask6`, `side6`, `inBand6` (the side whose price is inside the 0.88 to 0.97 band at the candle ending EXACTLY 600, 480 and 360 seconds before the close, its price, and whether there was one; null for a missing candle, never "not in band") and `twoStageLeft` (600, 480 or 360 for the earliest look in band, else null). Written by `logRise` after the orders are sent, public candles only; nothing that decides an order reads it (tests TS1 to TS3). An XRP or natural gas order (decided at 10 minutes) has no 8 or 6 minute candle yet, so those fields are null. NOT built: the optional small record for markets that qualified but got no order (it would need a candle read for every market, not only the ones ordered). Needs `bash functions/deploy-sizing.sh`. The full export (Copy all orders) now also carries `smooth`, `flips0` and these fields. Both order exports (Copy order diagnostics, Copy all orders) carry `entryLead`, and the full export also carries avgFill, avgFee, the book sizes, rise3 and rng5, so every forward read can split orders by entry time.

**Depth log (Oct 25, 2026, the research session's request, the owner: "2").** Every new order records `depthAtLimit` (the size resting at the touch it hits: a YES buy meets the YES ask size, a NO buy meets the YES bid size), `shareOfDepth` (its contracts over that size) and `depthLevels: "top"`, because Kalshi's market object carries only the top level of the book, so this is NOT a sum over price levels. `bidSize` and `askSize` in the export are the YES book's top sizes, so for a NO order the relevant one is `bidSize`. Written with the order record from numbers already read; nothing that decides an order reads it (test DD1). Both are columns in Copy all orders. Needs `bash functions/deploy-sizing.sh`.

**Hand-sold check, fixed Oct 21, 2026.** `closedByHand` (#407) marked every NO order the bot bought as "sold by hand": Kalshi books a NO buy on the YES side (sent as `ask`), so the bot's own entry fill read as a sale, and those orders (losses included) were left out of the stats, the loss stop and the pool. It now ignores the entry order's own fill, does not call an order hand without its entry id, and no longer takes the exit watch's `skipped` as proof; `settleOpenOrders` re-asks every order already marked hand once and settles the wrong ones as what they were (`handRepaired`). Tests H5, H11 to H13.

## XRP back to 1 contract (Oct 25, 2026, the owner, on the research session's read)

`FIXED_CONTRACTS` now has XRP at 1 (Dogecoin 3, natural gas 2 unchanged). Why: since 15:15Z on Oct 23, XRP had 24 fills, 4 losses (16.7% against 7% break-even) and -$4.87, all four losses at a price of 0.903 or lower. Order, entry time and every cap are unchanged; tests FS1, GF1 and OS1 pin the size. Needs `bash functions/deploy-sizing.sh`.

## Gold's quiet hours (Oct 29, 2026, the owner: "gold skip can go live")

`QUIET_HOURS_CT = { KXGOLD15M: [20, 24] }` in `functions/kalshiLiveLib.js`: gold places no NEW order while the US Central clock reads 20:00 to 23:59 (by the time the bot looks; follows daylight saving). Why: MKTTIME1 (V2, 2026-10-29) found this block the one place gold was weaker in all three history windows (PF 1.44 / 1.03 / 1.17 become 1.63 / 1.16 / 1.28 without it, 24 losses skipped in 315 entries) and the live block is net negative (41 orders, 3 losses, -$0.97). It is a test, not a finding. **Corrected the same evening (V2's falsifier FALS1):** the first z of +0.98 tested the wrong thing; on gold's own close-date windows the middle window lifts profit factor only +0.085 (gate 0.10), the block's permutation p is 0.025 alone and about 0.12 to 0.30 counting every market and block tried, and the corrected block-versus-rest z is 1.87 (about 3c an entry worse). The owner kept it live anyway ("keep it, review sooner"). **Interim review:** MKTTIME1-F reads it early at 100 block entries on fresh days from public candles (about Nov 24 to 26; the live bot places none in the block, so there are no live block orders to read). If the block's mean per entry is not below the rest (z under 0), delete the table entry; if it is below by z 1.5 or more, keep it; between the two, wait for the December read. It only removes orders; the exit watch still sells an open gold position. The formal MKTTIME1-F read stays in about December. The Bot page's silent-market warning says nothing about gold during the block and restarts its clock at midnight. Tests QH1, QH2. Needs `bash functions/deploy-sizing.sh`.
## Bitcoin is paused in code (Oct 29, 2026, the owner: "we can kill bitcoin i guess")

`PAUSED_SERIES` is now XRP, Bitcoin and the three probe markets. Why: live since 2026-10-07 Bitcoin is profit factor 0.72 over 155 orders (11 losses, -$22.39); 4 of its 11 losses came in the same window as an Ethereum loss, and the per-hour and per-weekday history (MKTTIME1) gave no reason to skip only some hours. Same rule as XRP: it stays in `L1_SERIES` (names, quotes and alerts work), is never a candidate, has no resume date (putting it back is a reviewed edit of the list), and the exit watch still sells anything open. Ethereum is untouched. The smooth-climb kill rules for Bitcoin (due 2026-11-12) are moot for Bitcoin; Ethereum keeps its own. Test PX1. Needs `bash functions/deploy-sizing.sh`.

## Dogecoin 3 to 5 contracts (Oct 29, 2026, the owner: "step to 5 now")

`FIXED_CONTRACTS` has Dogecoin at 5 (was 3). Why: live since Oct 20 Dogecoin has 131 settled orders, 125 won, net +$9.45, +2.66c a contract (halves +1.65c and +3.38c), profit factor 1.77, and all 6 losses were early sells at the 25c line; history holds it at PF 1.29 / 1.26 / 1.15 by third. It is ahead of the written ladder bar (150 settled, above +0.5c a contract in both halves) by about 20 orders, and 6 losses is a thin sample: the loss rate is 4.6% (95% range about 2% to 10%) against about 8% to break even, so this can still be luck. One loss at 5 contracts is about -$3.70. `MAX_FIXED_CONTRACTS` copies the new size, so the order size lock now refuses a Dogecoin order above 5. **Next step and kill rule:** review at 250 settled Dogecoin orders; go back to 3 if the last 100 settled orders at 5 net under +0.5c a contract or lose more than 8%. Tests FS1, GF1, OS1, SZ and OV pin the size. Needs `bash functions/deploy-sizing.sh`.

## Market News filter (Oct 29, 2026, the owner: "only pull equities, crypto or commodity related articles")

`isMarketNews` in `functions/marketTapeLib.js` runs on every news feed BEFORE the per feed cap: a headline is kept only when it names stocks, crypto or commodities, or the Fed, rates, inflation, yields, dollar or tariff news that moves them (`NEWS_ALLOW`), and a personal advice column or lifestyle piece is dropped even when a market word appears in it (`NEWS_DENY`: first-person starts, "my husband", Moneyist, "should I", horoscopes and the like). The two crypto desks (CoinDesk, Cointelegraph) pass on their source, but the drop list still applies. The trigger was a MarketWatch advice column about an ex-husband and a college fund. If every story in a run is filtered out, no news is written and the page keeps the last headlines. Tests NF1, NF2 (and T3 now uses a market headline). The first list was run against the live feeds the same evening and widened (price-move verbs such as "tanks" and "plunges", "free cash flow", "capex", jobless claims, and about thirty large company names) because it dropped real equity stories such as "Alphabet tanks nearly 13% for worst day ever"; of 70 live headlines it now drops 19, all politics, world news and advice columns. **Needs** `npx firebase-tools deploy --only functions:marketTapeTick --project shwoopnet` (keyless, no switch); the page changes nothing and the stored headlines refresh at the next 15 minute run after the deploy. To widen or narrow it, edit the two word lists and the tests together.

## The freshness check (Oct 29, 2026, the owner: "check for more stale modules or information ... an agent that runs after every deploy")

The Bot page's Rules and limits text, the Start confirmation, the next look label and the silent-market list say things the bot's code decides (which markets trade and which are paused, sizes, the window limit, the loss stop, the exit line, the add-on cap, gold's quiet hours). They went stale twice in one day (XRP's "10 minute look", Dogecoin's 3 contracts, Bitcoin and the probes still listed). `test/siteFreshnessGates.test.js` (SF1 to SF5) now compares each of those lines with `PAUSED_SERIES`, `L1_SERIES`, `FIXED_CONTRACTS` and the limit constants, so a code change that makes the page untrue fails in the pull request that makes it. **When you change a size, a limit, the paused list or the gold quiet hours, change the page text and this test together.** Also run: `.claude/agents/freshness.md` (read only: it runs the gate, then reads the page's visible text, the changelog and the docs for lines the gate cannot pin, and reports with proof; it never edits or deploys). `functions/deploy-sizing.sh` and `functions/deploy-push.sh` run the gate at the end of a deploy and warn, never block. A daily scheduled task runs the agent on the latest main.

## XRP is paused in code (Oct 28, 2026, the owner, on the research session's read)

`PAUSED_SERIES = ["KXXRP15M"]` in `functions/kalshiLiveLib.js`: XRP stays in `L1_SERIES` (its name, quotes and alerts keep working) but `runL1Tick` never makes it a candidate. Why: live since 2026-10-07 XRP is profit factor 0.49 over 65 fills (8 losses, -$9.51) against 1.32 in the history, which is bad luck (p about 0.07) or a live-versus-backtest gap, and the forward reads FLOOR1 and THIN1 settle it on 2026-11-12. **It fails closed: no date resumes it; putting it back is a reviewed edit of the list.** The exit watch is untouched and still sells any XRP position that is open. `args.pausedSeries` exists only so older gates can use XRP as an example market; `functions/index.js` never passes it (gate PX2). The Bot page's silent-market warning skips a market marked `paused` in `KAL_WATCH`, so XRP going quiet on purpose is not reported. The owner also declined a gold ladder cap and the half-size rule ("we need to achieve more profit % per win instead of just scaling up or down"): sizing changes what a loss costs, not the edge, so neither was built. Tests PX1, PX2, S8. Needs `bash functions/deploy-sizing.sh`.

## The probe markets are paused in code (Oct 28, 2026, the owner: "yeah we can")

`PAUSED_SERIES` is now XRP plus `PROBE_SERIES` (AUD/USD, USD/CAD, natural gas). Why: a probe buys at 97c to win 3c, and none of them had earned a place. Same rule as XRP: they stay in `L1_SERIES` (names, quotes and alerts work), are never candidates, have no resume date, and the exit watch still sells anything open. The silent-market warning skips them (`paused: true` in `KAL_WATCH`). Tests PX1, PX2. Needs `bash functions/deploy-sizing.sh`.

## The nightly order report (Oct 28, 2026, the owner: "reports at midnight (00:00 UTC)")

`kalshiNightlyReport` (`functions/kalshiReportLib.js`, `functions/deploy-report.sh`, `test/kalshiReportGates.test.js` R1 to R5) is a READ-ONLY HTTPS endpoint behind one secret token (`KALSHI_REPORT_TOKEN`, Secret Manager, at least 24 characters, compared in constant time; no token configured means closed). It returns a summary of the bot's own orders for the last N hours (default 24, at most 90 days): filled, settled, won, lost, exits, open, net, profit factor, worst loss, split by market and by entry lead, and with `?orders=1` one compact row per order. It never returns an order id, a client order id or a credential. It holds no Kalshi key, sends nothing to Kalshi, writes nothing, and only reads `kalshiLiveOrders`. It is the ONE reviewed exception to the security scan's "no open HTTP endpoint" rule (`scan.js` allows it only with `makeReportHandler` and the report token). The token goes into the Claude environment's secrets, never into a chat; a scheduled task calls it with `Authorization: Bearer <token>`. **Schedule and dates (Oct 29, 2026):** the scheduled fetch now runs at 12:04 AM US Central and the relay at 12:13 AM US Central (they were 00:00 UTC). Report days are US Central days, and every time shown to the owner is US Central. The 7 day figures still include the paused markets (XRP and the probes) until their orders age out of the window. Needs `bash functions/deploy-report.sh` (it prints a new token once, in the owner's terminal, and keeps an existing one).

## Research outcomes, Oct 29, 2026 (facts only, nothing promoted)

From `kalshi-scalper/README.md` on the research branch. No trading rule changed because of any of it.

- **GEN1, GEN1S, GEN2:** generators of full scalp strategies on the 18 fifteen minute series. 17,500 distinct strategies in all (5,000 + 5,000 + 7,500), 0 passed discovery (profit factor 1.5 at 10 contracts, per-order rounded fees). The best discovery profit factor was 1.25 (GEN1, GEN1S) and 1.14 (GEN2, at least 150 trades). N tried for deflation is about 425,000 (425,330 after GEN2), Bonferroni z bar about 5.2. Holdouts not read, nothing frozen.
- **ARB2 to ARB5:** full-set, deadline, bracket and sports totals lock scans. 0 opportunities of 1c or more that were real locks (ARB2 to ARB4 best +1.4c, +0.6c, +0.1c; the +1.4c pair was not a lock; ARB5 zero crossed ladders in 691 games). All FALSIFIED.
- **THETA1:** favourite drift sold before settlement in long-dated markets. 0 of 27 cells survived discovery (profit factor 0.03 to 0.34).
- **EXIT1: FALSIFIED.** Holding to settlement beats every exit shape. Profit factor per contract in three windows: hold 0.961 / 0.928 / 0.898, live 25c line 0.921 / 0.897 / 0.869.
- **REGIME1:** all five stand-down filters FALSIFIED. One information-only effect: entries with a spread of 2c or more do worse (removed entries 0.798 / 0.753 / 0.716). Not a pass.
- **GOLD1D:** the gold stability claim fails. Gold at the 6 minute look 1.20, at the 10 minute look 0.89.
- **G3H1 (hourly ladder) pass is VOID.** An audit found a universe look-ahead: the ladder file kept only strikes whose YES mid was between 3c and 97c 35 to 25 minutes before the close, but the rule enters 51 to 46 minutes before, so cheap strikes that later collapsed were dropped from the source file. CORR1 re-reads it on a file with strikes chosen before entry.
- **Queued, not run as of this note:** CORR1, LADL1, CONF1, MM1.

**Standing lesson:** a universe or file built after the entry time can hide the losers. Choose the strikes (or markets) from information available before entry, and say how the file was built before trusting a result from it.

## Order size lock and exit watch alarm (Oct 29, 2026)

**Why.** On Oct 28 at 6:39 PM CT a Dogecoin order for 12 contracts reached the account with no `entryLead`, while current code only sizes Dogecoin at 3 (`FIXED_CONTRACTS`) and tags every order. Nothing in code stopped a wrongly sized order. **Size lock.** `maxContractsFor(series)` (`functions/kalshiLiveLib.js`) is the most an L1 order for that series may have: the fixed size for XRP, Dogecoin and natural gas, 1 for the other capped and probe series, `L1_ORDER_CEILING` (50) for gold, the one ladder market, and 0 for a series not in `L1_SERIES`. `runL1Tick` checks it after all the sizing and window rules and BEFORE the order is recorded, so a refused count sends nothing, leaves no "sending" document, logs an `order size refused` event and the other markets carry on. The fixed sizes are copied once when the module loads, so a change in memory moves the sizing but not the lock; it reads code constants only (no session, argument, stored value or page input). It can only skip an order, never raise a count, and a valid order is unchanged. **What it cannot do:** it does not find out WHY a 12 came out (an old build running during a deploy, a manual order and a bug all look alike to it), a wrong edit to the constants moves the lock with them, and gold is bounded by the ceiling, not by its ladder. The nightly report (`kalshiReportLib.js`) has an `oversize` section (series, count, limit, time; zero is normal), which is also how a hand-placed or old-build order shows up. **Exit watch alarm.** `functions/kalshiExitAlarmLib.js`: the exit watch writes a heartbeat (`kalshiLiveControl/exitWatch`, once per minute's run, after a pass completed); the minute function `kalshiLiveArmed`, a different process, checks it when the bot is on and, if a position is open and the watch has been silent more than `EXIT_WATCH_STALE_MS` (4 minutes), writes `exitWatchAlert` on the session document once per silent spell (claimed in a transaction first); the existing `kalshiPushSession` turns that into an issue alert (`sessionKinds`, kind `exitwatch`). No new secret, endpoint or scheduled function, no Kalshi key, no order, every error swallowed. **What it cannot do:** it does not sell or restart anything, it cannot see a stall if BOTH scheduled functions are down (the dead-man's switch covers that), and an alert is lost if no phone is subscribed. Needs three deploys, IN THIS ORDER: `bash functions/deploy-push.sh` FIRST (heartbeat in `kalshiLiveExit`, alert text in `kalshiPushSession`), then `bash functions/deploy-sizing.sh` (size lock and alarm check in `kalshiLiveArmed`), then `bash functions/deploy-report.sh` (the report's `oversize` section). If the alarm check goes out before the heartbeat exists, any position open more than 4 minutes looks silent and one false alert fires; it is harmless but noisy. Gates: SZ1 to SZ6 (`test/kalshiSizeCheckGates.test.js`), OV1 to OV3 (`test/kalshiOversizeReportGates.test.js`), EA1 to EA9 (`test/kalshiExitAlarmGates.test.js`).

## The nightly report includes the second slot (Oct 30, 2026, the owner: "the report should include oicore since it's part of our strategies")

`kalshiNightlyReport` also reads `kalshiSlotOrders` (read only, one extra query) and adds `secondSlot` (total, by strategy id, by market), `allStrategies` (L1 plus slot, the Account result line's figure) and, with `?orders=1`, `slotOrders` rows (strategy, ticker, side, count, fill, result, PnL; no ids). The L1 sections (`total`, `byMarket`, `byEntryLead`, `oversize`) are unchanged. A failing slot read leaves the L1 report intact. Test R6. Needs `bash functions/deploy-report.sh`.

## The report's order rows carry depth and quote context (Oct 30, 2026, the refinement chat's R2, the owner approved the chat's request)

With `?orders=1` each row (L1 and slot) also has `orderedCount` (the intended size; `count` stays the filled size, 0 for a no-fill), `price`, `limit`, `seenBid`, `seenAsk`, `bidSize`, `askSize`, `depthAtLimit`, `shareOfDepth`, `depthLevels`, `addon`, `rise3` and `smooth`, null where the order lacks it. Numbers and short labels only; no order id, client order id or raw `seen` object. Test R7. Needs `bash functions/deploy-report.sh`.

## One deploy command (Oct 30, 2026, the owner: "build the wrapper")

`bash functions/deploy-latest.sh` updates the folder to `origin/main` (it stops if tracked files have local edits), runs the whole test suite, works out from the changed files which of `deploy-push.sh`, `deploy-sizing.sh` and `deploy-report.sh` are needed (in that order), shows the plan and asks before running anything. It only calls those three scripts, never pushes, forces or touches a secret, and records the last deployed commit in the gitignored `functions/.last-deployed` only after every selected deploy finished (a failed deploy is offered again next run). The first run has no marker and asks whether everything up to now is already deployed. `DRY_RUN=1` and `ASSUME_YES=1` exist for the test. Gates DL1 to DL4 (`test/deployLatestGates.test.js`). It does not replace the individual scripts, which still work alone.

## Profit add-on cap (Oct 29, 2026)

The owner: "i'm concerned about us losing more than we're making due to scaling". The reinvest pool buys one extra contract per $0.93 of pool with no limit but `L1_ORDER_CEILING` (50). Wins are about 6c a contract and losses about 90c, so through a win streak the add-on compounds and the next loss lands at peak size. `l1Count` now clamps the add-on to `addonCap(base)` = floor(base x `ADDON_MAX_FRACTION` 0.25), where base is the balance-driven count (base 23 allows at most +5, base 11 at most +2, base under 4 gets 0). It can only lower a count. The pool still accumulates beyond what is used, on purpose, so it reflects real profit and raising the fraction is a reviewed edit; `addonUsed` (and so `addonCost` and the loss stop's `addonAtRisk`) is the clamped count actually sent, so the unused pool is never counted as at risk. The session's `sizeAddon` is clamped by the cap-based bound and the page's pool line reads `sizePool` itself. Not changed: `SKIM_REINVEST`, `foldSkim`, the 12% stop, the window cap, the 25c exit, the ceilings, capped and probe series. Arithmetic (not predictions) at 6c a win and 90c a loss, largest order and largest single loss, before (pool unbounded) then after: base 11: 50 ($45.00) then 13 ($11.70); base 23: 50 ($45.00) then 28 ($25.20); base 40: 50 then 50 (the ceiling already binds). Tests `test/kalshiAddonCapGates.test.js`. Needs `bash functions/deploy-sizing.sh`.

## Series order (Oct 23, 2026, the owner)

`L1_SERIES` is now gold, XRP, Bitcoin, Dogecoin, Ethereum, then the probes (older sections above list the earlier order). Why: within a tick markets are tried in list order and only one capped crypto order goes out per window, and XRP and Dogecoin trade 3 contracts against Bitcoin's and Ethereum's 1, so a 1 contract order was taking the window from a 3 contract one when they tied (Bitcoin and XRP tie at the 10 minute look, Ethereum and Dogecoin at the 6 minute look). Sizes, stops, window limit, entry times and the one-crypto-order rule are unchanged. Test OS1. Needs `bash functions/deploy-sizing.sh`.

## Bitcoin and Ethereum: smooth climb only (Oct 23, 2026)

The research session's SMOOTH2 lead, the owner: "1" (confirmed in this session). Bitcoin and Ethereum (`SMOOTH_SERIES`) both decide at the 6 minute look (Bitcoin left the 10 minute list) and place their usual one contract order ONLY IF the bought side's 1 minute mid path from the market's first candle to the decision candle has at least 4 earlier candles, every minute change at or above -0.005 and a total climb of at least 0.10 (`smoothGate`, `pathShape`; plain float arithmetic, so a pullback of exactly 0.005 is NOT smooth, as in the research session's parity vectors, test SM1). A path that cannot be read, is stale or is not smooth places no order and says so in the note. The gate reads public candles only (no key) and can only REMOVE Bitcoin and Ethereum orders; size, band, stops, caps, the 25c exit and the one crypto order per window are unchanged. Every order also records `minStep`, `climb` and `smooth`. Note the list order still puts Bitcoin before Dogecoin at the 6 minute look, so a smooth Bitcoin takes the window from Dogecoin's 3 contracts. **Kill rules (README, registered before any order):** remove Bitcoin and Ethereum from live orders if 3 or more of the first 40 smooth fills lose, or their combined net is under $0 after 100 fills, or the 2026-11-12 forward read is FALSIFIED; review at the 2026-11-17 export. Tests SM1 to SM3. Needs `bash functions/deploy-sizing.sh`.

## Money across Kalshi's shards: topped up by hand (Oct 24, 2026)

Kalshi keeps each market group's money on its own exchange shard (shard 0: gold, AUD/USD, USD/CAD; shard 2: Bitcoin, Ethereum, XRP, Dogecoin, natural gas) and an order needs money on ITS shard, so a shard that ran short silently stopped a market (the forex probes sat unfunded for days). An automatic split was built on Oct 23, 2026 (Kalshi's opt-in auto-rebalance target, `kalshiShardSplit`) and **removed the next day**: Kalshi answered the key's request with HTTP 403 (the bot's key may not set that target), and the web "Advanced shard settings" page has no such setting, only the "Disable balance management" switch (leave it off) and the per-exchange balances. So the owner tops a shard up by hand, Kalshi, Transfers. The page cannot move money. It says so early instead: the Bot page's account card adds "Shard N (...) is low. Top it up in Kalshi under Transfers." and the page said so while a bot shard held under $30 (removed Oct 24, 2026). The raw account read still lists the balance per shard. Delete the deployed function with `firebase functions:delete kalshiShardSplit --project shwoopnet` (nothing calls it).

## One window, one limit

Bitcoin, gold and Ethereum close in the same 15 minutes and move together, so `runL1Tick` holds the account money put into one window (matched by the ticker's time part, counting earlier ticks) to `L1_WINDOW_CAP_FRACTION` (5.5%, raised from 4.5% on Oct 20, 2026 so the last series stops getting 1 contract) of the sizing base, under the loss stop (`L1_SIZED_STOP_FRACTION`, 6% from Oct 20, 2026, **then 12% the same night**: at 6% a full open window ($8.43, counted as lost) plus $6.06 of ordinary settled losses ended the bot, because the window limit left only about $0.80 to $2.30 of room under the stop; one loss of about $3.70 was enough. Open orders are still counted as lost, so 12% of the base is the real worst case; tests W4 and W5 pin both numbers). Series are sent in `L1_SERIES` order (Bitcoin, gold, Ethereum, XRP, Dogecoin), so the later ones are the ones that go without. The add-on (profit) is not counted; the first order in a window is never cut to zero. Tests W1 to W3 in `test/kalshiL1Gates.test.js`.

## One crypto order per window (Oct 22, 2026)

Bitcoin, Ethereum, XRP and Dogecoin (`CAPPED_SERIES`) now place at most ONE order per 15 minute window (`runL1Tick`, first in `L1_SERIES` order wins; an order that did not fill does not hold the window). Why: the research session's live diagnosis found 72% of recent loss dollars came from three windows where two of them lost together. Gold and the probes are not part of the rule. History is in-sample and the rule roughly halves the expected crypto profit, so it is a test: read it on the live record, not the backtest. Test OC1. Needs `bash functions/deploy-sizing.sh`.

## A refused read is asked once more (Oct 22, 2026)

`liveRequest` (`functions/kalshiLiveLib.js`) asks a GET that Kalshi answers with 429 once more after 1.2 seconds. An order (any POST) is still never retried, which is what gate L10 protects and test RR1 proves. Why: the balance and position reads share one key with the exit watch's 10 second loop, and one refused read skipped a minute's entries and put "The account could not be read: HTTP 429" on the Bot page. Needs `bash functions/deploy-sizing.sh` and `bash functions/deploy-push.sh`.

## The quote recorder pilot (Oct 22, 2026, research only)

`.github/workflows/record-quotes.yml` and `scripts/record_quotes.py` record Kalshi's 15 minute crypto quotes (Bitcoin, Ethereum, Solana, XRP, Dogecoin; best bid, ask and sizes about twice a second in the last 150 seconds of each window) next to the public trade feeds of Coinbase, Kraken and Bitstamp (the 10 minutes before each close), plus each market's result, a per-window coverage count and an hourly clock check. It exists for the research session's RECORD1 (do Kalshi's quotes lag spot in the last two minutes). It is a ONE DAY PILOT first: its job is to show how many windows a free runner catches (late scheduled jobs, Kalshi's public read limit) before anyone commits to 14 days. It holds no key and no secret, places no order, reads only public data, and the built-in token only pushes gzipped files to the `quote-data` branch, never to main (`test/quoteRecorderGates.test.js`). Nothing about the bot changes.

**The recorder was extended (Oct 28, 2026, the owner: "extend the recorder", for the research session's no-view brief on Bitcoin, Ethereum and gold).** `scripts/record_quotes.py` now also records gold's 15 minute market (`KXGOLD15M`, in `quotes.csv` with the others) and, in the last 150 seconds before each hourly close, the near-the-money strikes (mid between 3c and 97c, at most 40 per series, polled about every 3 seconds) of the hourly Bitcoin and Ethereum ladders (`KXBTCD`, `KXETHD`) and gold's daily and weekly ladders (`KXGOLDD`, `KXGOLDW`, which close at 21:00 UTC) into `ladder.csv` with a `close_time` column. Same schedule, same `quote-data` branch, public data only, no key, no order; a refused read backs off. Tests Q7, Q8. It goes live on merge, and data starts arriving on the next recorder run.

**The order book recorder (Oct 29, 2026, the owner approved the research session's QUOTE2B spec; research only).** `.github/workflows/record-book.yml` and `scripts/record_book.py` record the Bitcoin hourly "above K" ladder (`KXBTCD`): for the 7 strikes nearest the money of the event closing at the next top of the hour, the best 5 YES bids and 5 NO bids with sizes every 3 seconds from 55 minutes before each close, plus the public trade tape every 30 seconds (trade ids de-duplicated), with the server's Date header on every row so clock skew can be measured. Public endpoints only, no key, no order; the built-in token pushes gzipped files to the `quote-data` branch (under `book/`), never to main. Same 4 hour back to back job pattern as the quote recorder. It exists so a forward maker test (MAKER5 or QUOTE2B) can use a real queue model; about 100 MB gzipped over 14 days. Not a 15 minute series, so it cannot hold a position with L1. Tests B1 to B6 in `test/bookRecorderGates.test.js`. Goes live on merge; stop it by deleting the workflow.

**Recorder R6, the 15 minute book and tape (Oct 29, 2026, the owner approved the research session's spec `RECORDER_SPEC_R6_15MIN_BOOK_2026-10-29.md`; research only, nothing trades).** `.github/workflows/record-15m-book.yml` and `scripts/record_15m_book.py` record the whole 15 minute window of the five markets the bot trades (`KXGOLD15M`, `KXBTC15M`, `KXETH15M`, `KXDOGE15M`, `KXXRP15M`, fixed in code; XRP is paused in the bot but still recorded): every 2 seconds one batched public book read (`/markets/orderbooks?tickers=...`, falling back to one read per market after 3 failed batches in a row) keeping the best 5 YES and 5 NO bids with sizes, the server's Date header and the send and receive time; about 60 seconds after each close every public trade of that window, following the cursor until it is empty and de-duplicated by trade id (the id is not stored); a coverage row per window per market, written even for a window with no good poll (polls, 429s, fallback, largest gap, tape pages, trades, duplicates dropped, summed size next to Kalshi's volume and the result); an hourly SNTP clock check. Public endpoints only, no key, no auth header, no order; two request streams, at least 0.5 seconds between book calls and 1.5 between tape pages, a 429 waits 2 seconds and doubles up to 30. The built-in token pushes gzipped CSV to the `quote-data` branch under `book15r6/<date>/<HHMM>/`, never to main. It is triggered every 30 minutes under one concurrency group that never cancels a running job (scheduled starts run hours late), and each job records up to the next 4 hour boundary, so a dropped trigger costs at most 30 minutes; the window already open when a job starts is joined late (its tape is still complete). **It stops by itself after 14 days**: from 2026-11-13 23:59 UTC every run exits at once (checked in the workflow and in the script). Stop it sooner by deleting the workflow. Estimated (the spec's numbers): about 45 MB a day gzipped, about 630 MB over the 14 days, about 35 public reads a minute. **It replaces R2** (`record-book15.yml` and `record_book15.py`, Bitcoin, Ethereum and gold every 3 seconds under `book15/`, #610), whose files were removed in the same change, so the same markets are never read twice; what R2 recorded before the merge stays on `quote-data` under `book15/`. Tests FB1 to FB11 in `test/fifteenBookRecorderGates.test.js`.

## L1 is the only strategy (Oct 12, 2026)

The opening window paper recorder (`OW1`, `kalshiOpeningTick`, `kalshiOpeningLib.js`) and the page's Closing / Opening / Both switch were removed at the owner's request ("lets go back to only L1 for now"): the strategies must not overlap in mindset or position, and anything that holds to settlement overlaps L1 in both. Nothing profitable that is flat before L1 buys exists in the history: `OW2` (four variants) and `SS1` (216 cells, a train and validation search) are all `FALSIFIED` in `kalshi-scalper/README.md`, and every earlier scalp family fell to cost. `test/kalshiL1Gates.test.js` K10 and `test/kalshiLayoutGates.test.js` Y41 pin the absence. The research record (`kalshi-scalper/`, `docs/OPENING_STRATEGY.md`) stays as history; the old `kalshiOpeningOrders` and `kalshiOpeningControl` documents are untouched in Firestore and have no rule, so nothing can read them. A second strategy is a deliberate, reviewed change that must show how it cannot hold a position at the same time as L1 and why it is a different bet, not a different lane of the same one.

## The second strategy slot (Oct 29, 2026, phase A, inert)

The owner wants more than one live strategy, but only through a reviewed, fail-closed path, and nothing has passed the research bar yet. Phase A is the guard rails only: `functions/kalshiSlotLib.js`, `test/kalshiSlotGates.test.js`, `docs/SECOND_SLOT_DESIGN.md`. It is INERT: `SLOT_ENABLED` is `false`, `SLOT_STRATEGIES` is a frozen empty array, nothing in `functions/` or `index.html` imports the library, it has no network, Firestore, clock or signing code, and `kalshiLiveLib.js`, `index.js` and `firestore.rules` are untouched. **The owner's direction rule (Oct 29, 2026): a slot order may sit in the same market and window as an L1 order when it is on the SAME side. It would only be wrong if it were HEDGING.** So the opposite side is blocked in both directions (slot against L1 or slot, L1 against slot), fails closed on any unreadable order list, lock or position, and is decided by a lock `kalshiLiveDirection/{ticker}` read and written in the same transaction that creates the order document. A slot may send more than one contract and scale in, inside hard caps in code; the slot's dollar caps SCALE WITH THE SIZING BASE (owner, Oct 29, 2026: the gold ladder makes L1 bigger as the account grows): `SLOT_CAP_FRACTIONS` (per order 1%, per window 2%, open total 3%, daily 2%, lifetime 6%) capped by `SLOT_CAP_CEILINGS` ($25, $40, $60, $20, $60) through `slotCaps(sizingBase)`, which is all zero, so no order, for an unusable base. It shares ONE risk budget with L1: slot dollars count against the same 5.5% window cap and open slot orders count as lost in the same 12% stop (the later wiring must change `runL1Tick` and `botRisk`; this phase documents and tests the contract: `slotRiskForL1`, `slotRiskForBotRisk`, `slotWindowSpent`). Each engine sells only its own contracts, under the shared `claimClose` lease, never more than the account holds. Nothing stored can add or loosen a strategy; kill rules latch off and only a reviewed edit re-arms. Review round (Oct 29, 2026): one entry gate only (`slotOrderCheck`, no flags, needs a `lockTxn` proof), the daily and lifetime caps are checked against the new order's own cost, a stop-out is a loss in the shared stop the moment it is sold, scale-in stops after any exit, a close sells nothing for settled, hand-closed or errored orders and never L1's contracts (`othersUnsold`), kill rules are sticky and re-armed only by a later `reviewedAt`, and the window figure for L1 is the gross `windowSpent`. The wiring checklist is in the design doc. Admitting a strategy is a later, separate, reviewed pull request (phases B to H in the design doc).

**Phase B (Oct 29, 2026): wired, still off.** The slot is wired into the running bot behind constants only: entries need `slotActive` (`SLOT_ENABLED === true && SLOT_STRATEGIES.length > 0`), and everything that protects an open slot position (exits, settle sweep, the shared stop and window cap, the direction lock, L1's clamp) runs on the wider `slotWatch` (`slotActive() || SLOT_EVER_USED`), so switching the slot off or deleting a strategy never orphans a live position (`SLOT_ON` in `functions/index.js`, `slotOn(args)` in `kalshiLiveLib.js`; nothing stored, requested or typed on the page can feed either; there is no test backdoor). The exit pass also sells a slot order that ends up against another order's contracts (a hedge from an old revision during a deploy). Review round and prerequisites for the first admission: `docs/SECOND_SLOT_WIRING.md`, "Review round 2". While it is false the deployed functions make exactly the reads, writes and orders they made before: `test/kalshiSlotWiringGates.test.js` SW0 (the library) and `test/kalshiSlotIndexWiringGates.test.js` SI0 (`index.js`) replay recorded call logs, and **a change to either fixture means the off-equivalence broke: fix the code, not the fixture**. The one legitimate exception: `offEquivalenceIndex.json` was re-recorded on Oct 29, 2026 from `origin/main`'s own `index.js` (a scratch checkout with no slot code, same harness) after #613 added the exit watch heartbeat write, and the merged branch's output was required to be byte-identical to that recording; `offEquivalence.json` needed no re-record because #613 and #615 change nothing in its scenarios. A re-record is valid only from main's code and only when the branch matches it byte for byte. New files: `functions/kalshiSlotRunLib.js` (tick, exits, settle sweep, all I/O injected) and `functions/kalshiSlotStoreLib.js` (Firestore side, database injected). Slot orders live in `kalshiSlotOrders`, the direction lock in `kalshiLiveDirection/{ticker}` (written only inside the transaction that creates an order, for both engines), the kill latch in `kalshiSlotControl/killed`; the first two are admin read and no client write in `firestore.rules`, the latch has no rule. No new secret, scheduled function, callable or endpoint. The page and the alerts read only `kalshiLiveOrders`, so a slot order is never shown or alerted as an L1 order (and its fills show as unmatched account activity until the page card exists, which must come before the first admission). Deploy: `functions/deploy-sizing.sh` (minute function), `functions/deploy-push.sh` (exit watch and Flatten), `firebase deploy --only firestore:rules`; see `docs/SECOND_SLOT_WIRING.md` for the full note.

## How to talk to the owner (standing rules, set 2026-10-20, updated 2026-10-21)

- Keep replies short and plain. Lead with the result and the numbers. Assume the owner remembers nothing from earlier in the conversation, so say where a thing is and what it is.
- **Offer choices with the pop-up menu (the AskUserQuestion tool), not a numbered list typed into the reply** (the owner, 2026-10-21: "from now on in this project"). Put the recommended option first and mark it "(Recommended)". A closing line of text is still fine for what happens next, but the choices themselves go in the pop-up.
- Never use em dashes. Use they/them for anyone whose pronouns are not stated.
- Never ask for, or accept, credentials, keys or sign-in codes in chat.
- Stats to the owner in the short form (orders filled, won/lost, profit factor) unless they ask for more. Times are always US Central.
- Merge a pull request only when the owner says so. Keep the current look: no new design system (see Conventions).

## The strategy switch (Oct 29, 2026, the owner: "i like 1")

The Bot page reads `kalshiSlotOrders` (admin read, a listener with no write) next to L1's orders. With no slot order there is no switch, table or panel and every card draws what it drew before (`kalshiViewOrders` returns L1's own array). Once a probe has orders, a switch above the cards chooses Overall (a Strategies table, the Account result line summed), L1, or one probe (a probe panel replaces Open positions and Recent trades; the result line follows the choice). It reads only and cannot change a strategy; slot ids are escaped where drawn; dollars go through `kalshiMoney`. The kill-rule meters of the mock-up are not built (the latch is not browser readable). Page only, nothing to deploy. Tests ST1 to ST4 in `test/kalshiStrategiesGates.test.js`.

## The second slot, step 1 (Oct 30, 2026, the owner: "i wanna get this live", for the research session's GEN6 open interest core)

Still OFF (`SLOT_ENABLED` false, registry empty): this step only adds what the first admission needs. The page now treats slot orders as the bot's own (`kalshiAllOrders`: open positions, the fills list, and the Stop Loss and Risk meter, which counts `strategy: "SLOT"` like the server's stop). The engine can read an open interest condition (`entry.oiRiseMin`: open interest at the candle ending 180 s before the close minus the one ending 360 s before it, from the public candles; missing means no order) and a `cheap` side rule (the side with the lower price). `SLOT_HOLD_ALLOWED` is the ONE reviewed exception to "every exit is before settlement" (owner, Oct 30, 2026): only `OICORE` may declare `exit: { holdToSettle: true }`; it is still sold if it becomes a hedge. `kalshiPushSlotOrder` sends the same close alerts for slot orders (`functions/deploy-push.sh`). Admission (the registry entry, the switch, `SLOT_EVER_USED`, the pre-registration) is a separate reviewed pull request. Research view (SLOTEX, V2): held profit factor 1.85 on validation, selling at 60 s 1.52, so holding is the better exit; nothing reaches the research bar. Tests OI1 to OI5, ST5.

## The second slot is ON with one probe: OICORE (Oct 30, 2026, the owner: "i wanna get this live")

`SLOT_ENABLED` true, `SLOT_EVER_USED` true, registry exactly one strategy: OICORE (Bitcoin 15 minute, the cheaper side 5c to 50c, only when open interest rose 86,300 or more over the 3 minutes to 180 s before the close, 180 to 120 s before the close, 5 contracts, held to settlement). Full pre-registration, kill rules, size schedule and deploy order: `kalshi-scalper/README.md#SLOT-OICORE`. **Not at the research bar** (day z 4.42 against about 5.2; two history windows); the owner chose a capped live probe. The plan was 5 contracts for the first 15 fills, then a reviewed edit to 10; the owner ordered 10 before any fill (merged Oct 30, 2026; live only after `deploy-sizing.sh`). The counterparty guess in the pre-registration did not hold (V2's MECH1) and is corrected there: no counterparty is named. The streak kill is 18 (the validator now allows up to 20), because a 28% win rate makes a streak of 5 normal. Ethereum was scored by the research session and does not carry over. The shared 12% stop, 5.5% window cap and the direction lock apply. `reviewedAt` is 2026-10-30; the forward read is 2026-11-13. Needs `bash functions/deploy-push.sh` then `bash functions/deploy-sizing.sh`.

## One Overall Bot page (Oct 30, 2026, the owner: "build the entire page to be overall ... identifiers ... one module that displays the unique strategies"; replaces the strategy switch)

There is no strategy switch and no per-strategy panel. Every card shows every order the bot placed (L1's and the second slot's, `kalshiAllOrders`), a small chip (`kalshiChipHtml`, `kalshiStrategyOf`) on each open position and recent trade says which strategy it came from, and one **Strategies** module (`#kalStrategies`, `renderKalshiStrategies`) lists L1 and each registered second strategy: status, today, result, settled, win rate, open, last order. The Account result line and Stop Loss and Risk count both. `KAL_SLOT_REGISTERED` and `KAL_STRATEGY_INFO` are labels only; gate ST6 ties them to the bot's code (the registry, and the markets L1 trades). Page only. Tests ST1 to ST7.

## Strategies live in the Account card (Oct 30, 2026, the owner: "id do j, but move the all strategies text to the top")

The separate Strategies card is gone. The table (`#kalStrategies`, `renderKalshiStrategies`) is a child of the Account card (`data-card="account"`), on the right beside the balance, Today and the Loss stop, which sit on the left. **All strategies is the FIRST row** (the account figure; the strategies are its parts) and each strategy's markets are a small line under its name (`kal-strat-mk`; on a phone the table stays a stack of cards with a Markets row). It is no longer in the Layout menu (`OPTIONAL`), and the default flow is account, status, result line, positions, trades. Tests Y2, Y5, Y5b, ST14. The tiles and tallies rule (ST13) still holds: every card that counts orders reads `kalshiAllOrders()`.

## Ethereum paused, L1E removed, Dogecoin on gold's ladder (Oct 30, 2026, the owner: "we can just remove L1E altogether", then "lets allow dogecoin to follow the same gold ladder. i want these to be the same strategy entirely")

`PAUSED_SERIES` is now XRP, Bitcoin, Ethereum and the probes. Ethereum stays in `L1_SERIES` (names, quotes, alerts, exit watch still sells an open position), has no resume date, and the L1E label and row are gone (every L1 order is `L1`). Why: ETHFUNNEL showed Ethereum rarely fires because the smooth-climb step removes 95.5% of in-band windows. `CAPPED_SERIES` is Bitcoin, Ethereum, XRP; `FIXED_CONTRACTS` is XRP 1 and natural gas 2. Dogecoin left both lists, so it takes the same sizing as gold: `l1Count` with the session's `sizeCap`, the 2% base, the add-on capped at a quarter of base, the 5.5% window cap, the 12% stop and the 25c exit, up to `L1_ORDER_CEILING` (the size lock now allows Dogecoin that ceiling). It is no longer part of the one-crypto-order-per-window rule, so it can trade in the same window as gold. Risk in plain numbers: one Dogecoin early-sell loss at the gold size is the same dollars as a gold one. Review rule to set with the owner (kill: go back to 5 fixed if Dogecoin's last 100 settled orders lose more than 8% or net under +0.5c a contract). Exchange index: all live markets (gold, Bitcoin, Ethereum, XRP, Dogecoin) are on shard 2 per the owner's export Oct 30, 2026; older "shard 0: gold" text above is stale. Tests GF1, GF3, OC1, FS1 to FS3, OS1, PX1, SZ1 to SZ6, OV2, ST6, ST8, ST15, ST16, SF2. Needs `bash functions/deploy-sizing.sh`.

## Dead markets dropped from L1 (Oct 30, 2026, the owner: "yes", on "are there any dead markets we can drop from L1")

`L1_SERIES` is now gold, XRP, Bitcoin, Dogecoin, Ethereum: AUD/USD, USD/CAD and natural gas (the probe markets, paused since Oct 28 with no way back, no orders since) left it, which also removes three market reads from every bot minute. They stay in `PROBE_SERIES` and `PAUSED_SERIES`, so putting one back in the list is a reviewed edit that is still paused until it also comes off the paused list. The size check now refuses any order for them outright (`maxContractsFor` is 0 for a series off the list), which is a new safety, not a loss. An order of theirs that is still open is still sold by the exit watch and settled by the sweep (both work from the order's own ticker). The recorded off-equivalence fixture lost exactly the three market reads of those series. XRP stays until the 2026-11-12 forward read; Bitcoin stays because it is still in the list L1 reads and the second strategy needs its quotes. Needs `bash functions/deploy-sizing.sh`.

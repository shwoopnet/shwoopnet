# NEWS FADE: pre-registration (Nov 11, 2026)

Status: REGISTERED, NOT RUN. No Kalshi call, no scraping, no outside read was made to write this. Nothing below has been scored. Rules applied: `docs/RND_CHARTER.md` and `docs/STRATEGY_LIFECYCLE.md` 7d/7e (read from origin/main), `IDEA_BACKLOG.md` (owner hard rule, Nov 11), and the politics rulebook as recorded in `kalshi-scalper/REFINE_HANDOFF.md`. `docs/POLITICS_RULES.md` does not exist on this branch or on origin/main yet (V2 owns it by PR), so the politics caps below are copied from the handoff line, not from that file. The "queue item 10" label was not found in the backlog; this is written from the task text.

Classification card: `NEWSFADE | news-labelled jump reversal or continuation, days-scale time exit | win-rate class mid (10c to 90c entries, win rate near the price), loss shape up to the entry price, 1 contract, no daily dollar claim yet | Idea`

## 1. Mechanism

A Kalshi market in a news-driven category jumps at least 10c inside 15 minutes. A headline from an allowed public feed, published inside the window that ends at the jump, names the market's subject. Two arms, both registered:

- FADE: the headline moved the price too far, too fast. Buy the side that LOST ground, after a delay.
- FOLLOW: the price under-reacts to the headline. Buy the side that GAINED ground, after a delay.

Who loses: the fast reactors who traded the headline at the jump (FADE) or the slow quoters who had not yet moved (FOLLOW). The baseline question is whether a news-labelled jump behaves differently from an unlabelled jump of the same size, so every cell is also reported as kept minus the matched no-headline jump baseline, with an interval that must exclude zero.

## 2. Uniqueness (lifecycle 7d, to be scored by the Verification Analyst, not by me)

1. SIGNAL: a text event (a timestamped headline matched to a fixed keyword list per series) joined to a Kalshi price jump. The headline is a different source from price, not a price band or a clock. Honest weakness: the jump itself is a Kalshi price field, so a reviewer may call this POL-i1 with a label. The test that settles it is the kept-minus-baseline row above: if headlines add nothing, the idea collapses to POL-i1 and is rejected as its duplicate.
2. ENTRY: at jump end plus a delay of 15 minutes, 1 hour or 4 hours (three arms, all counted), on a market priced 10c to 90c at entry, one contract, either side, spread at entry 3c or less. NOT the 88c to 97c late-window logic and not a favourite: the side bought is the one the jump moved away from (FADE) or toward (FOLLOW), inside 10c to 90c.
3. MANAGEMENT: none. EXIT: a time exit 24 hours after entry at the bid, or settlement if sooner (never later than 14 days from entry, the politics cap). No hold-to-settlement as the plan, so it is not the declined favourite-and-hold family.
4. CLOSEST EXISTING: POL-i1 (politics jump fade, daily candles, 3 day exit, no headline) and row 45 (gold spot leads after a jump). DIFFERS: minute-scale jump, headline-gated, three delays, both directions, multi-category, 24 hour exit.
5. [live figure removed, ask Main]
6. CORRELATION under 0.3 with every live strategy on daily cash P&L, Pearson r, at least 20 overlapping days. This cannot be computed before any trade exists; it is checked at the first read and a value of 0.3 or more is a FAIL and a declined-list entry with the number. Prior expectation: low, because the universe excludes the 15 minute series that L1 and OICORE trade, but that is a judgment, not a measurement.

## 3. Data feasibility verdict: FORWARD ONLY

What was checked in the repo and on origin branches:

- `shared/marketTape` (written by `marketTapeTick`, `functions/marketTapeLib.js`) holds the latest headlines only. Each item carries `{headline, source, url, datetime}` with `datetime` from the feed's `pubDate` (seconds), so the TIMESTAMPS exist, but each 15 minute run overwrites the list. Feeds: CNBC (two), WSJ World, MarketWatch, CoinDesk, Cointelegraph.
- No workflow in `.github/workflows` records headlines (record-15m-book, record-book, record-oklq, record-perps, record-quotes only).
- `origin/quote-data` holds book, book15, book15r6, deribit, oklq, quotes, raincal, sportspre, wxens, daily and ref (ref/bars, ref/quotes, ref/refvals, ref/results, ref/runs, a yahoo1m_state). A path search for news, rss and headline files found only `ref/bars` and `daily/ref` (price bars, not text). No headline history exists there.
- Git history contains the tape code only (first commit `e2a6dbd1`, #393) and no stored headlines. Firestore is not readable from here, and by code it keeps no history.

So no historical headline record exists in anything this team holds. Verdict FORWARD ONLY for the allowed feeds already in the repo, because the headlines must be recorded from the day a recorder starts.

One historical route exists on paper and is NOT counted in the verdict: GDELT (`api.gdeltproject.org`, `data.gdeltproject.org`, noted PERMITTED in `POLITICS_CARDS_NOV11.md`, 15 minute file archives back to 2015; its DOC API looks back about 3 months). It was not reachable from the sandbox (reset), so reachability is unverified, and its timestamp is when GDELT first saw a story, not the publication time, which blurs a 15 minute delay arm. If a runner can reach it, a historical dry run becomes possible and this verdict is upgraded by amendment before any result is read. Until then: FORWARD ONLY.

Price side needs no recorder: Kalshi `/historical` one minute candles can be joined later by timestamp, so the recorder only has to capture headlines and a clock.

Honest sample warning: the jump count is unknown. A step 0 existence check (jump counts per category from candles only, no headlines, so it also serves POL-i1) must run before the recorder is approved. Kill the idea at step 0 if the projected count of headline-matched jumps is under 40 per third within 12 weeks of recording.

## 4. Exact event definition (frozen before any data)

- Universe: Kalshi series in the Economics, Politics, and Financials categories whose market has at least 3 days to close at the jump, excluding every series in `L1_SERIES`, `PROBE_SERIES`, all 15 minute series and the KXBTCD/KXETHD/KXGOLD ladders. The series list is written to a file and hashed BEFORE the first headline is read, chosen only from information available at that time (standing lesson on universes built after the fact).
- Jump: the market's mid (bid+ask)/2 from one minute candles moves 10c or more (arm 10c) or 15c or more (arm 15c) between two candle closes at most 15 minutes apart, with the end price between 10c and 90c. The jump end time t0 is the later candle close. One event per market per 24 hours (the first), to stop one story counting as many events.
- Headline match: an item from the allowed feeds with `datetime` in [t0 minus 15 minutes, t0] whose text contains at least one keyword from that series' fixed keyword list (written with the universe file, not edited after). Items with a `datetime` of 0 or after t0 never match. A jump with no match is a BASELINE event, recorded and not traded.
- Entry: at t0 plus delay D (15 minutes, 1 hour, 4 hours), take the ask of the chosen side; skip if the spread at that moment is above 3c or the ask is outside 10c to 90c.
- Fee: Kalshi taker fee on the unrounded formula, both legs counted; the exit sell pays the fee as well.
- Exit: bid at entry plus 24 hours, or settlement if earlier.
- Politics caps (handoff rulebook, spec caps not a live permission): 3 contracts for a live probe, up to 10 positions open, 14 day maximum hold, kill on net under -$15 after 20 fills or 5 losses in a row. For this test all results are scored as 1 contract and reported as if live against those two kills.

## 5. Cells grid and N

Axes: arm (FADE, FOLLOW) x delay (15 min, 1 h, 4 h) x jump size (10c, 15c) x category (Economics, Politics, Financials) = 2 x 3 x 2 x 3 = **36 cells**. The matched baseline rows are scored for comparison and are not additional tries.

N: the shared deflation count is about 9,459 (W-SWEEP-EXT1, Bonferroni z 4.55 at that N). Adding 36: **N = 9,495**, two-sided alpha 0.05/9,495 gives z of about 4.56. No cell may be added, dropped or redefined after the first headline is recorded; any new cell needs a new registration and a new N.

## 6. Bars (fixed now)

- Development = the first two chronological thirds of events (by t0), split into two halves for stability. Held-out = the final third, read ONCE by the lead from the frozen cell list, never by the worker.
- PASS requires ALL of: profit factor 1.5 or better on the development data AND on the held-out third, on the cash basis after the unrounded fee, with the best-cell result deflated for N = 9,495 (z about 4.56); at least 40 treated events per third in that cell; both development halves at PF 1.3 or better; kept minus baseline interval excluding zero; spread test passed (median entry spread 3c or less); correlation with every live strategy under 0.3 (20 overlapping days) at the first read.
- FALSIFIED: fails the bar on the held-out read, or cash PF under 1.0 on the development read after fees. Three FALSIFIED tests close the family for good (charter).
- NOT_ENOUGH_DATA: fewer than 40 treated events in a third at the registered read date. Two from this source close it.
- KILL early (development): PF under 1.0 in either half; or median entry spread above 3c; or 5 losses in a row or net under -$15 after 20 fills when scored as live.
- Even a PASS permits only a shadow candidate and an owner popup, never an order.

## 7. What the forward recorder needs

Two options, both need an owner popup (charter section 7: new recorder or runner minutes). Neither is built or started by this document.

A. Piggyback on `marketTapeTick` (recommended): append each run's newly seen items to a history collection (for example `tapeHeadlines/{hash(url)}`) with `first_seen`. No runner minutes, no new host, no new secret; costs a few Firestore writes and a deploy of a keyless function, and `functions/` is a trading-adjacent folder, so it needs the usual review and a gate in `test/`. Resolution is the 15 minute run, which is why the match window is [t0 minus 15 min, t0] and `pubDate` is the matching clock.

B. A GitHub Actions recorder pushing gzipped CSV to `quote-data` under `news/`. Hourly runs cost about 720 runner minutes a month, over the charter's 250, so it would need either fewer runs (about 8 a day) or an in-process loop within an existing job. Not recommended while the piggyback exists.

Host list for the allowlist PR (headline recorder only; Kalshi candles are joined later through the already-approved Kalshi public host):

| Host | Use | Terms status |
|---|---|---|
| search.cnbc.com | CNBC and CNBC Economy RSS | UNCHECKED, treat AMBIGUOUS until a human reads the terms page (RSS for display is not obviously permission to store and analyse for a business) |
| feeds.content.dowjones.io | MarketWatch and WSJ World RSS | UNCHECKED, same caution |
| www.coindesk.com | CoinDesk RSS | UNCHECKED |
| cointelegraph.com | Cointelegraph RSS | UNCHECKED |
| api.gdeltproject.org, data.gdeltproject.org | optional historical dry run | PERMITTED per its own page; reachability unverified |

No Yahoo, no Open-Meteo, no X, Reddit, Facebook, TikTok, ESPN, Polymarket or paid feed appears anywhere in this design. A human must read each RSS terms page before any recorder starts; until then the feeds are not approved for recording even though `marketTapeTick` already reads them for display.

Fields to store per headline: `source`, `headline` (title text only, or a keyword hit list plus a hash if terms disallow storing text), `url_hash`, `pubDate` (seconds, as parsed by `parseRss`), `first_seen` (our clock, seconds), `feed_run_id`, and `matched_series` (computed later from the frozen keyword file, never at record time). The frozen universe and keyword files are committed with their hash before the recorder starts.

## 8. Read plan

1. Step 0 (no headlines needed): jump counts per category and arm from candles; projected treated events per third. Kill rule above applies.
2. Terms check on the RSS hosts, then owner popup for option A.
3. Record for at least 8 weeks; development reads at 40 matched events per third; the held-out third is read once by the lead.
4. [live figure removed, ask Main]


Dated clarification Nov 13, 2026 (Head of R&D ruling): rule words restored from commit 44dda69f^ (the version before the privacy scrub); nothing re-decided. line 23 restored verbatim; lines 22 and 94 still carry a marker, to be done by hand.

# S3, combo house side: paper registration (Idea Desk B for the Head of R&D)

**Registered Nov 12, 2026, BEFORE any scoring.** No fill has been scored. It completes Refinement's skeleton (`refine_tools/SHADOW_RULES_NOV12.md`, S3 on branch `claude/refine-live`) from the fields the combo recorder actually stores.

`S3 | family: combo house side, buy NO on a high-priced combo at the posted ask, hold to settlement | risk class: high win rate, large single loss, $2 a fill, correlated across combos that share legs | stage Idea (paper only)`

**Paper only. Nothing here places, changes or cancels an order.** A live probe needs the owner's own popup with the exact spec (`docs/POLITICS_RULES.md` sections 1, 2 and 7).

## Why this is allowed at all

Buying a favourite and holding it is on the declined list. The owner wrote one exception on Nov 12, 2026 (`docs/POLITICS_RULES.md` section 7): "MEASURE ON PAPER: buy NO on high-priced combos and hold to settlement. This is a written owner exception to the Charter's buy-high-and-hold ban, for combos only." This registration uses that exception and nothing wider: combos only, paper only.

## Data

The combo book recorder (`scripts/record_combo.py`, branch `combo-data`, public Kalshi data, no key, every 30 minutes, ends 2027-01-31). Fields used: from `quotes.csv` the receive time, ticker, event ticker, close time, NO ask, YES bid size, volume and number of legs; from the daily `results.csv` the ticker and result. Scorer: `workers/combo_s3/s3_score.py`, committed with this file and carrying the same constants.

## The rule (every number is pinned)

| Item | Value |
|---|---|
| Start (date constant) | snapshots received from **2026-11-13 00:00 UTC** on. The one snapshot taken before that (Nov 12, 14:35Z) was looked at for the design only and is never scored |
| Which combos qualify | at the snapshot: 2 to 30 legs; a NO ask is posted; **price paid = NO ask + 1c, between 60c and 90c inclusive**; at least **3 contracts** resting at that ask (the YES bid size); **volume above zero**; closes between 1 hour and **14 days** after the snapshot |
| Entry | one paper buy of NO at the posted ask plus 1c, at the first snapshot where the combo qualifies |
| How many | one per combo ticker and one per event ticker, ever; at most 10 new fills per snapshot (lowest ticker first, not by price) |
| Size | 1 contract for the profit factor; dollars are shown at $2 a fill (net per contract times 2 divided by the cost per contract) |
| Fee | 0.07 x p x (1 - p) per contract, unrounded, on the price paid. The fee schedule of the combo series has not been read; if it differs, the result is restated |
| Exit | hold to settlement |
| How a result is read | the recorder's daily settled file: result "no" wins 1 minus the cost, result "yes" loses the cost. Any other result is left out and counted |
| A fill is due | 48 hours after its close time. A due fill with no row in any settled file is UNRESOLVED and counted |
| Development window | entries 2026-11-13 to 2026-11-25. **Read once, on or after 2026-11-26** (the recorder's own stop-rule date) |
| Held-out window | entries 2026-11-26 to 2026-12-09. **Read once, on or after 2026-12-12**, and only if the development read met the bar |
| Tries counted | 1 (one band, one rule) |

## Kill

1. **Paper net under -$40** at $2 a fill, running in fill order over the settled fills: killed as of that fill. (The parlay rulebook's stop.)
2. **Cash profit factor under 1.2 on the first 100 settled fills:** killed.

Kill is final for this registration. Return needs a new registration and the owner.

## The owner's bar, and how correlated legs are handled

**Bar: net of 10c or more per dollar paid, after fees and the 1c slip, over at least 100 settled combos.** Measured as total net cash divided by total cash paid (price plus fee), on EVERY settled fill of the window, not a chosen subset.

Combos are not independent bets: many share the same games. The recorder stores how many legs a combo has, not which legs, so shared legs cannot be seen directly yet. Until they can, the stand-in for "the same games" is the **close date** of the combo (UTC), and the bar also needs all of these:

- at least **10 different close dates** among the settled fills;
- **no single close date carries more than 30% of the net**;
- **both halves positive** (fills split in entry order);
- a **bootstrap that resamples whole close dates** (2,000 draws, fixed seed): its 5th percentile of net per dollar is above zero;
- **unresolved fills are 10% or less of due fills**; over that the label is NOT_ENOUGH_DATA and the figures are a description.

If Main adds the leg tickers to the recorder, a later amendment (made before the read it governs) replaces the close date with shared legs. It is not applied backwards.

**Labels.** Under 100 settled fills: "no evidence at n = x". Bar met on development: "paper edge shown (unproven)", and the held-out read is then made once on its date. Bar met on both: it goes to the Head of R&D as a candidate for a $2 probe popup, labelled unproven. Anything else: "bar not met". This is the owner's paper-first bar for the combos exception. It is NOT the research bar (cash profit factor 1.5 on development and held-out, deflated), and no result here is reported as a pass of that bar.

## What the arithmetic already says (no data used)

- **The bar cannot be met above about 90c.** A NO bought at 90.3c that wins every single time returns exactly 10c per dollar after the fee. So "high-priced" here has to mean about 60c to 90c, which is also inside the 10c to 90c entry limit of section 2. A 90c and up arm is not registered: it could not meet the bar even with no losses.
- **The bar asks for a large mispricing.** At a price paid of 80c the NO must win about 89% of the time (the price says 80%). At 60c it must win about 68%. That is 8 to 9 points of error in the YES bidder's price. The reason to think it could exist is that the YES bids here are resting limit bids by parlay buyers, on a product where the buyer usually overpays; the reason to doubt it is that anyone can lift those bids, and a bid that is still resting may be one nobody wanted.
- **The profit factor kill is strict on purpose.** A rule with no edge at 80c has a profit factor of about 0.93, and it needs about an 84% win rate to reach 1.2.
- **If the fills were independent,** a no-edge rule at 80c would reach 10c per dollar over 100 fills well under 1 time in 100. They are not independent, so the true chance is higher and unknown; that is what the close date conditions are for.

## Lock-up, stated plainly

Each paper fill is held to settlement. This rule only takes combos that close within 14 days, so the paper money is tied up for at most 14 days plus the time Kalshi takes to settle. Combos in the same collection can close as late as November 2027; this rule does not take them. A live probe on this rule would lock $2 a combo for up to 14 days, with up to the whole $2 lost on a miss.

## Rulings by the Head of R&D, added Nov 12, 2026 before any read

- **One band only, as registered: a NO price paid of 60c to 90c.** The band is not to be stretched, whatever the supply turns out to be.
- **Volume above zero at entry is known at entry.** It is read from the same snapshot row as the price, so it uses nothing from the future. It does narrow the sample to combos somebody already traded; results describe those combos and no others.
- **"Cannot be priced" closes the card.** S3 is closed with the words "cannot be priced", and no other band or rule is tried, if either of these holds:
  1. the recorder's own stop rule fires at its Nov 26 read (`docs/COMBO_RECORDER.md`: fewer than 20 distinct combos ever showed a two-sided quote with a bid on the side the paper test would buy, or fewer than 100 combo trades printed in total); or
  2. at the Nov 26 read the rate of paper fills is too low to reach 100 settled fills before the recorder ends on 2027-01-31. The test is fixed now: settled fills so far, divided by the days recorded, times the days left to 2027-01-17 (two weeks before the end, to leave time to settle), plus the settled fills so far, is under 100.
- **Try count: 1** (the owner's paper bar for the combos exception; the held-out read is the same try). It is not a try against the research bar, and no result here is reported as a pass of it.
- **The research bar, for reference (corrected Nov 12):** the shared count is about 2,113,000 tries and the bar is a one-sided z of 5.46 (`DEFLATION_LEDGER.md` on branch `rnd-queue`).

## Honest limits, stated before any read

1. **Thin supply.** In the one design snapshot, 37 of 400 recorded combos had a NO ask, and 1 met every condition above. At one or two a snapshot the first 100 settled fills may not exist by Nov 26; then the label is "no evidence at n = x".
2. **The recorder is a sample, not a census.** It lists at most 5,000 open combos a run and keeps 400 quote rows, the tightest YES spreads first, then the most traded. A combo with only a YES bid is kept only when it ranks high on volume. Results describe the combos the recorder kept.
3. **Results exist only for combos that traded.** That is why volume above zero is required at entry. The settled file is read once a day (in the 00 UTC hour, looking back 36 hours, at most 3,000 rows); a skipped run or a full list leaves fills unresolved, and they are counted, not dropped quietly.
4. **Resting bids select against us.** The only NO that can be bought is one where a YES bid is still resting. If good bids are taken at once by faster makers, what is left is the worse ones. The 1c slip does not cover that; only the settled result does.
5. **A posted ask is not a fill.** Paper assumes a fill of one contract at the ask plus 1c when at least 3 contracts rest there. Quotes on new combos may last under a minute; the recorder sees one instant every 30 minutes.
6. **Asked of Main (engineering), not assumed:** store the leg tickers, and store results for every quoted ticker, not only those that traded.

Nothing in this file authorizes a live order.

## Note for the Nov 26 read: what COMBOPRICE1 needs (added Nov 12; inventory only, nothing scored)

COMBOPRICE1 is V2's design for pricing a combo against its own legs (`workers/COMBOPRICE1_DESIGN.md` and `src/scalper/combo_price.py` on branch `claude/epic-ptolemy-0amjd9`; design only, never run). V2 has retired, so it has no owner. It is not part of S3 and not a try of S3. It can be picked up beside the Nov 26 description if these exist by then:

1. **Leg tickers AND leg sides for every recorded combo.** The combo market object lists them (`mve_selected_legs`). The recorder stores only how many there are. Main is adding them.
2. **A quote of each leg within 5 minutes of the combo's quote** (the design's staleness rule). The combo recorder does not read the legs. Two ways, neither built: the recorder reads each distinct leg once a run (more requests on the recorder), or the legs' one-minute candles at the combo's read time are pulled afterwards through kalshi-pull (no recorder change; the request count depends on how many distinct legs there are, which is not known until item 1 exists).
3. **Results for every quoted combo,** not only those that traded (the same gap S3 has).
4. **The fee field of the combo series.** The design treats the standard fee as unverified for combos until a market object or the fee schedule shows it. Neither has been read.

With item 1 alone, one thing becomes possible at zero reads: grouping S3's paper fills by shared legs in place of close dates (an amendment, made before the read it governs). COMBOPRICE1 itself needs items 1 and 2.

Also for Nov 26, description only and not a try: the recorder's printed trades where the taker bought YES show what the house side actually earned where the volume is. It is read only on or after Nov 26, with the recorder's own stop rule.

## Dated clarifying line, Nov 13, 2026, 00:20Z, before any outcome is joined (Head of R&D's ruling of 00:19Z): weather legs

The registered sample does not change. **Every S3 figure is printed twice: over all combos, and over combos with no weather leg.**
- A weather leg is a leg whose series ticker starts with one of: `KXHIGH`, `KXLOW`, `KXTEMP`, `KXRAIN`, `KXSNOW`, `KXHURR`, `KXTORN`, `KXWIND`. The list is fixed here, before any outcome; the scorer also prints every leg series it saw with its count, so a weather series the list misses can be seen and named, never silently kept.
- The recorder has stored each combo's leg tickers only since its second snapshot (Nov 12, 21:36Z). A combo with no stored legs is "leg unknown": it sits in the all-combos line only.
- The registered verdict, the kill lines and the read dates are on the all-combos line, as registered. The no-weather-leg line is information for one purpose: **any probe spec that ever goes to the owner from S3 leaves out combos with a weather leg unless the owner says otherwise** (the owner's ban on 65c to 87c weather NO legs).
- S3 stays on the paper track with its own read dates (Nov 26, Dec 12). It is NOT on the wheel list (the Head's ruling: listing it twice would pad the wheel). The optional cut at 7 or more legs is not registered.
- The scorer change (the second line and the leg-series count) is made and re-hashed before the Nov 26 read; the leg-ticker column is checked on Nov 19.

## Scorer change made, Nov 13, 2026, 01:17Z, before any outcome is joined (the change promised in the clarifying line of 00:20Z)

`combo_s3/s3_score.py` now prints, after the registered line, the same figures over combos with no weather leg, and the count of every leg series seen in paper fills. Nothing about the registered line moved: on two made-up sets of recorder files every line the old scorer printed appears unchanged in the new output (the old scorer's sha256 was 00ddac486e041a5f16af12d9d666528466a1c9e2f87a67781dd09acfd20b9b7a).

- New sha256: 1fb56ae201fa120e5b7d889c8835e31817eb8a989a212eb6997f6928b1b46157.
- A combo's legs are taken from any snapshot that stored them (a combo's legs do not change), so "leg unknown" means no snapshot ever stored them.
- The no-weather-leg lines say "would read" in place of a verdict and carry the tag "information only; the registered verdict is the all-combos line".
- **A fact the read depends on, sent to Main at 01:20Z:** the combo recorder has landed 2 snapshots since it merged (one by hand, one scheduled start of about 21). Paper fills come from snapshots. Unless the recorder is fixed, the Nov 26 read will most likely say "no evidence at n = x".

## Dated clarifying lines (Nov 15, 2026), before any outcome was read: four points, no registered number changes
Written after Auditor B's read of the scorer (CLEAN on the registered rule) and the Head's ruling of Nov 15. No result has been read for scoring; the Nov 14 feasibility count read quotes files only.
1. **Band edges, tolerance.** The price-paid band 0.60 to 0.90 is inclusive with a 1e-9 tolerance on each edge (the convention used elsewhere). On whole-cent prices this changes nothing; Auditor B's exact-cents test and mine found no cent where the plain float comparison differed.
2. **When more than 10 percent of due fills are unresolved.** The registered label is NOT_ENOUGH_DATA. Then every later line is a description: a kill line prints as "would read KILLED (description only)", never as a verdict, and the closing line reads "NOT_ENOUGH_DATA, description only". Under 100 settled fills the label stays "no evidence at n = x" as before.
3. **The bootstrap, pinned.** `random.Random(20261112)`; the close dates (UTC) of the settled fills, sorted ascending, are the clusters; one draw takes `rng.choice(sorted dates)` once per date (as many choices as there are dates, with replacement), concatenates the fills of the chosen dates (a date chosen twice counts twice), and computes net per dollar on them; 2,000 draws; the draws sorted ascending; the 5th percentile is the value at index `int(0.05 * 2000)` = 100.
4. **A daily MONITOR line (the Head, Nov 15).** A third mode of the scorer, `monitor`, prints for the development window only: paper fills, due, settled, unresolved, wins among the settled, cash PF so far and net per dollar so far, headed "MONITOR, not the registered verdict; the Nov 26 read is the verdict". It prints no label, no kill line and no bootstrap, and no rule changes because of it. The registered read stays once, on or after 2026-11-26.

## Dated lines (Nov 15, 2026, 15:00Z), before any outcome was read: answers to the Testing Desk's build 2 questions, written from what the scorer (835b06d7) does
No registered number changes. Where the scorer is the only statement of a rule, this line makes it the rule.
1. **Files.** `combo/DATE/HHMM/quotes.csv.gz` (DATE = UTC date, HHMM = UTC start of the run), a gzip CSV with a header row, read by column NAME. The real header is 19 columns: `t_send_ms,t_recv_ms,server_date_header,ticker,event_ticker,exchange_index,open_time,close_time,yes_bid,yes_ask,no_bid,no_ask,yes_bid_size,yes_ask_size,last_price,volume,open_interest,legs,leg_tickers`. Used: `t_recv_ms` (integer epoch milliseconds, UTC), `ticker`, `event_ticker`, `close_time` (ISO 8601 with Z), `no_ask` and `yes_bid_size` (dollars and contracts as decimals, e.g. 0.6500), `volume`, `legs` (integer count), `leg_tickers` (one cell, `TICKER:side` joined by `|`, may be empty or end in `|...`). A row with an unreadable or missing `no_ask`, `yes_bid_size`, `volume`, `legs` or `close_time`, or `no_ask` of 1.0 or more, does not qualify. Results: `combo/DATE/HHMM/results.csv.gz`, header with at least `ticker` and `result` (`yes` or `no`, case and spaces ignored; any other value counts as "other result", not settled). Files are read in sorted path order.
2. **Snapshot.** One quotes file is one snapshot (one run). No rounding window, no run id.
3. **Entry.** Per snapshot: keep rows that qualify and whose `t_recv_ms` is inside the window (start inclusive, end exclusive: development from 2026-11-13T00:00:00Z up to but not including 2026-11-26T00:00:00Z, by receive instant, not by file folder). Price paid p = no_ask + 0.01; band 0.60 to 0.90 inclusive with 1e-9 slack; size (`yes_bid_size`) at least 3; volume above 0; legs 2 to 30 inclusive; seconds from receive to close between 3600 and 1,209,600, both inclusive, no slack. Candidates sort by ticker ascending (plain string order). Walk them; skip a ticker already filled in ANY earlier snapshot, and skip a combo whose non-empty event ticker already has a fill in ANY earlier snapshot or earlier in this one; stop after 10 fills in the snapshot. A combo skipped only by the cap of 10 may enter at a later snapshot (it was not filled). Fills are then ordered by (receive time, ticker): this is "entry order".
4. **As-of.** The read time is an ISO instant argument. A fill is due when close time + 48 hours is at or before it. The clock is never read. `monitor` uses the development window only.
5. **Net.** Per contract: cost = p + 0.07 x p x (1 - p), unrounded; net = 1 - cost for a NO result, -cost for a YES result. Paper net at $2 is net x 2 / cost per fill (two dollars of cost, not two contracts). KILL 1: running sum over settled fills in entry order, dev read stops at the first fill where it is below -40. KILL 2: the first 100 settled fills in entry order; cash PF = sum of positive nets over absolute sum of negative nets (infinite if no loss); killed if PF is under 1.2. "Settled" = due and with a yes or no result.
6. **Bar.** All settled fills of the window, at least 100. Net per dollar = sum of net / sum of cost, at least 0.10 (no slack). Halves: first floor(n/2) by entry order and the rest, each total per dollar above 0. Close dates: UTC date of the close; at least 10; largest date's net / total net at most 0.30 (total net must be above 0). Bootstrap 5th percentile above 0 as pinned on Nov 15.
7. **Results rows.** A ticker with several rows (in one or several files): the first row in sorted file order wins; later rows are ignored, a conflict does not stop the read. A due fill with no row anywhere is unresolved.
8. **Label order.** (a) under 100 settled: "no evidence at n = x"; kill 1 is printed first when it fires, even under 100. (b) Over 10 percent unresolved of due: NOT_ENOUGH_DATA, every other line a description. (c) kill 2. (d) the bar. The label of the first failing step is the label.
9. **No-weather line.** Leg series = text before the first hyphen of each leg ticker; a combo is "weather" if ANY leg series starts with one of KXHIGH, KXLOW, KXTEMP, KXRAIN, KXSNOW, KXHURR, KXTORN, KXWIND. A combo whose legs are unknown (empty `leg_tickers` in every snapshot) is not in that line.
10. **Printed.** Aggregates only (counts, wins, PF, net per dollar, shares, percentile); no per-fill line, no ticker.

## Dated line (Nov 15, 2026), before any outcome was read: line 9 corrected (Auditor B's finding)
The recorder cuts a `leg_tickers` cell at 600 characters at a whole leg and ends it with `|...`. Rule: a cell ending in `...` is an INCOMPLETE leg list. The `...` is never a leg series. A combo with an incomplete list is "legs incomplete": it is in the all-combos line only, never in the NO WEATHER LEG line, unless some snapshot stored a complete list for it (a complete list replaces an incomplete one). A weather leg shown in a cut list still makes it a weather combo. The legs line now prints a "legs incomplete" count. Hand case 7 (tree LG) in EXPECTED_hand_s3_nov15.md. No registered number changes; the all-combos line is unaffected.

## Dated amendment (Nov 16, 2026, 16:20Z), before any outcome was read: the window is extended to Dec 5 (the owner approved; the Head's order of 16:15Z)
Why: at about 5.7 would-be fills a day (the feasibility count, 87de308b) the window to Nov 25 reaches about 74 fills and fewer settled, so the read would say "no evidence at n = x". The owner approved extending the recorder and the window to Dec 5. No registered number, price band, size, rule, kill or bar changes.
1. **Development window:** entries by receive time from 2026-11-13T00:00:00Z up to but not including 2026-12-06T00:00:00Z (receive dates Nov 13 to Dec 5 inclusive; before: Nov 13 to Nov 25).
2. **The read** is made ONCE, on or after 2026-12-12T00:00:00Z (before: Nov 26), so the last entries have a week to close and settle; the settled n is stated in the print. Fills whose close is later than the read minus 48 hours are not due and are excluded from n; fills due without a result are unresolved (over 10 percent unresolved is still NOT_ENOUGH_DATA). The excluded fills close later than the due ones, so the settled sample leans to shorter-dated combos; the print says so.
3. **The separate held-out window (entries 2026-11-26 to 2026-12-09, read on or after 2026-12-12) is WITHDRAWN.** Entries from Nov 26 to Dec 5 are now development; nothing is held out. Consequence, stated now: a development pass is read only as "paper edge shown (unproven)" and goes no further than that label; any step beyond paper needs a new forward window opened after the read, registered first.
4. **The scorer** changes only its date constants (development end, read-not-before) and its `heldout` mode refuses; the hand cases keep their expected figures with the read time moved after the new gate. The monitor keeps running on the development window.
5. **The results pull job** is built from the final combo-data tip after the recorder's last file (about Dec 5 or 6).

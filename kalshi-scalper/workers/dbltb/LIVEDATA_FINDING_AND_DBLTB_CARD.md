# A data source nobody here has used, and the one card it unlocks (Idea Desk B, Nov 13, 2026, 02:36Z)

Written under the queue-floor rule (the Head of R&D, seq 4: one new card by 08:20Z or an honest "none" with what was read). **No Kalshi API request was made for this. No price and no result was read.** What was read is listed at the end. Nothing here is registered as a try. PAPER ONLY. [research]

## 1. The finding: Kalshi's own public API carries live state, play-by-play, a temperature index and reference price series

Read from Kalshi's public documentation (docs.kalshi.com, the page index and eight pages, Nov 13). No desk's branch names any of these endpoints (searched main and six desk branches for "live_data" and "milestone": no match). They are Kalshi's own public API, which is on the permitted list.

| Endpoint | What the documentation says | What it could unlock | Not known until probed |
|---|---|---|---|
| `GET /milestones`, `GET /events?with_milestones=true` | A milestone "links Kalshi events to a real-world occurrence"; it is the key for live data | The id needed for everything below | Which sports and levels have milestones (ITF and challenger doubles?) |
| `GET /live_data/milestone/{id}`, `GET /live_data/batch` | Game status and "Scores ... in the sport-specific fields of that live data details object"; "not guaranteed to be current" | A game STATE read from Kalshi alone (a set score, a period, a map) | The fields for tennis; how stale; whether a finished match still answers |
| `GET /live_data/milestone/{id}/game_stats` | "play-by-play game statistics ... Pro Football, College Football, Pro Basketball, College Men's Basketball, College Women's Basketball, WNBA, Soccer, Pro Hockey, and Pro Baseball" | Play-by-play from a permitted source: every outside one is barred by the repo gate | Whether an event carries a wall-clock time; whether a finished game still answers (history) |
| `GET /live_data/weather/{city}` (and `/calibrations`) | "the Kalshi-computed city temperature index: the canonical minute-resolution series behind hourly temperature markets"; a `from` and `to` window; with `detailed=true` each station's reading | The settlement series of the hourly temperature markets, minute by minute, from Kalshi itself (this desk's hourly temperature measurement has no reading at all today) | How far back `from` reaches; the city ids other than `miami` |
| `GET /live_data/events/{event_ticker}` | "event-keyed live data such as crypto price charts, commodity price timeseries, and weather observations" | A reference price series for the commodity and currency 15 minute markets from a permitted source (the outside one was barred on Nov 11) | Resolution, history, which events |

**Limits, stated:** the documentation calls every `details` object "flexible JSON", so the fields are not documented; the live data "is not guaranteed to be current"; nothing says a finished game or an old minute stays available. One small probe answers these. Until it does, every "could unlock" above is a possibility, not a fact.

## 2. The probe (zero tries, 9 requests, a field probe only)

`desk_b_jobs/LIVEDATA_PROBE_A.json` (passes the check and the dry run of main's `scripts/kalshi_pull.py`; NOT dispatched; it needs the Head's order, the Chief of Staff and the owner's typed merge like every job): two milestone lists, three event lists with milestones (ITF doubles, challenger doubles, Miami hourly temperature), the Miami index for the last two hours, the same with station detail, the same for two hours on Nov 5 (does history exist), and the calibration timeline. It reads field names and time stamps. It reads no price and no result. Step B (live data and play-by-play of a handful of milestone ids, one event's live data) can only be written once step A shows the ids; about 12 requests.

## 3. The card: DBLTB, doubles at one set all

`DBLTB | family: a game-state model value in play (the deciding set's FORMAT), taker entry on the underdog pair at one set all, held to settlement | risk class: mid price (ask 15c to 45c), 1 contract | stage Idea, conditional on the probe | prior about 3%`

**This is this desk's parked idea of Nov 12** (`PARKED_NOTES_NOV12.md`; the Head of R&D, 19:13Z: "parked, correctly ... No card"). It was parked for one reason: the state "one set all" could not be read from Kalshi alone, and every score site is barred. Section 1 may remove that reason. Nothing else about the idea has changed.

**The fact.** In ITF, challenger and tour doubles the decider is a first-to-10 match tiebreak, not a set. A short tiebreak pulls the better pair toward 50%: by a per-point model (arithmetic, not measured), a pair with a 60% chance of a full set has about 55% in the tiebreak, and a pair with 75% has about 64%.

**The claim.** At one set all, a price that treats the decider like a set leaves the underdog pair about 5 to 11 points too cheap.

- **Other side:** an in-play maker or bettor using one tennis model for singles and doubles, or anchoring on the pre-match favourite.
- **Why they would lose:** the format, not the news. The error would last the whole changeover, not a second.

**Entry, management, exit (for a later registration, not registered here).** Entry: the first whole minute after the second set ends at one set all, buy the pre-match UNDERDOG pair at its ask plus 1c, only if the pre-match favourite was 65c or more, the ask is 15c to 45c and the spread is 4c or less. Management: one bet a match, 1 contract, no add. Exit: hold to settlement (the tiebreak takes about 10 to 15 minutes).

**The four uniqueness checks.**
1. **Signal:** a format fact applied at a game state read from Kalshi's own live data. Not a price pattern, a jump, a base rate or an outside feed.
2. **Entry and exit:** taker on the UNDERDOG at a mid price, held minutes to settlement. No live or shadow rule trades tennis.
3. **Correlation with live strategies:** no shared market with gold L1, OICORE or EVENT830; expected near 0, not measured.
4. **Declined list, rows compared:** favourite-and-hold (it buys the underdog at 15c to 45c); in-game lag at one minute (the claim is a wrong model for the whole changeover, not a late price); lock and parity scans (one held position); taker order-flow signals (no flow field); weather and the 15 minute grammar rows (not those markets). No row applies.

**Closest existing mechanism, said plainly:** MAPBREAK (closed tonight on its counts, not falsified) is the same FAMILY: a model value at a state change, taker, held. DBLTB differs in three ways: the value comes from the pre-match price through a format model, not from sibling market prices; the claimed error is the decider's format, which MAPBREAK had no equivalent of; it is another sport and another maker. **The Head ruled against variants of MAPBREAK tonight. If the Head reads DBLTB as a version of MAPBREAK, this desk's answer to the queue-floor rule is "none", and section 1 stands as what it found.** It is also not INPLAYJUMP (a price jump) and not TIE3 (a three-way price).

**Numeric prediction and kill lines, written before any data.**
- Define the retained edge at one set all: R = (favourite's mid at one set all minus 50c) divided by (favourite's pre-match mid minus 50c).
- The format model's fair R for a match tiebreak is about 0.55 (0.45 to 0.65); for a full third set about 0.80.
- **Stage 0 (the probe):** DEAD, back to parked, if live data shows no set score for doubles, or ITF and challenger doubles have no milestone.
- **Stage 1 (a zero-try measurement, no result read):** the median R of doubles matches at one set all, beside the same figure for tour singles (where one set all is already readable from Kalshi's set markets) as the control. **The idea lives only if the doubles median R is 0.72 or more.** CLOSED if it is 0.65 or less (the market already compresses), if fewer than 150 doubles states with a two-sided quote at a spread of 4c or less are seen in 14 days, or if the median one-way entry cost (half the spread plus the fee at the ask plus 1c) is above 4c. Between 0.65 and 0.72: not decided, no rule.
- **Stage 2 (one try, its own registration before any scored file):** cash PF 1.5 on development and on held-out, halves at 1.0, at least 150 filled bets. Arithmetic for honesty: at a pre-match favourite of 70c and a fully naive market the rule is worth about PF 1.2; it reaches 1.5 only on favourites near 85c. So a pass needs both a naive market and enough strong favourites.
- **Held-out, as date constants:** fixed in the stage 2 registration before any recorded file is read, as two whole blocks of calendar days after the recorder's first day (development days 1 to 14, held-out days 15 to 28). No date can be named today because no recorder exists.

**Events.** About 117 doubles matches a day on Nov 10 (ITF men 59, ITF women 47, challenger 7, tour 4; one day's census). Perhaps a third reach one set all (a guess). The tennis calendar thins in December and restarts in January, so 28 recorded days may straddle the gap.

**Data and terms.** Kalshi's own public API only: live data for the state, market lists and candles for prices. No outside source. **Cost:** the probe (9 requests, then about 12). Then the state has to be RECORDED forward, because nothing says a finished match's live data stays available: a batch live-data read every 20 to 30 seconds while doubles matches are live, on GitHub's runners. **That is a new recorder or an extension of the in-game recorder, which needs the owner's own popup** (runner minutes over the Charter's limit). Stage 1 for the singles control needs no recorder: about 100 list and candle requests through kalshi-pull.

**Weakness, stated.** In-play makers probably know the format; published evidence either way was not looked for. The live data may lag by tens of seconds, and a price read a minute after the set ends may already hold the tiebreak's first points.

## 4. What else section 1 could unlock, for the Head to route (none of it is this desk's card)

- **This desk's hourly temperature measurement:** the index is the settlement series the note says it cannot read. After the cost measurement, a rule on Kalshi-only data becomes possible to WRITE; nothing beyond the measurement is approved today.
- **In-game lag at seconds** (this desk closed it at one minute for want of a time-stamped play-by-play; V2 holds INGAMELAG1): only if the play-by-play carries a wall-clock time.
- **The commodity and currency 15 minute markets** (closed "without a new data source"; their outside reference feed was barred on Nov 11): a reference series from Kalshi itself, if it has history.
- **SOCDERIV's red-card state, the esports map state:** a state from live data, where MAPBREAK and REMATCH had to infer it from sibling markets.

## 5. What was read, and what was not

Read: Kalshi's documentation index and eight pages (targets and milestones; get milestones; get live data; get multiple live data; get game stats; get event live data; get weather index; get weather index calibrations). The declined list (lifecycle 7e) on main. `docs/POLITICS_RULES.md` (attention signals, nothing happens). This desk's own sixteen cards of Nov 11, its parked notes, its family table. The series titles of the Nov 12 listing already held (titles only). Every desk branch for earlier uses of Wikipedia, GDELT and live data.

Considered and NOT carded, plainly:
- **Wikipedia edits on the candidates' pages in "who will be picked" markets:** the same logic as POL-n1 and this desk's WIKIEDIT on another market. A version, not a card.
- **Today's news volume for a word in "what will the speaker say" markets (GDELT):** a new input on a family that failed twice (MENT1, card 84), from a source this sandbox could not reach on Nov 11. Not real enough to card.
- **Nothing happens:** already carded by three desks.
- **Wind and football totals from the NWS forecast:** a public forecast against a market's price, which is the declined weather row's shape, and under 52 windy games a season.
- **Cloture tallies against confirmation vote counts (Senate roll-call XML):** a real official early fact, but a handful of events a year.
- **Fading price moves inside dead-ball windows:** a filter on INPLAYJUMP, which was that idea's last look.

## 6. The Head's three conditions on the probe (seq 6), answered 02:45Z; the probe is NARROWED

The Head of R&D ruled: the probe goes ahead of the card; DBLTB is NOT a version of MAPBREAK but is a CONDITIONAL card, not registered and not counted, until the doubles state is shown to be readable from Kalshi; three conditions before the probe moves.

### (a) Terms: what could be read, and what could not

- **Kalshi's Developer Agreement and Terms of Use could NOT be read.** One request each to three kalshi.com addresses (the developer agreement page and two guessed addresses for its file and a data terms page) was answered HTTP 429 by a security checkpoint. Nothing was retried. `docs/KALSHI_PULL.md` on main already records the same: the two pages "were NOT read (HTTP 429 to every fetch, archive copy also unreachable)", the owner "waived reading" them on Nov 12 for the pull of "Kalshi's public market data", and "This is NOT a finding that automated reads are allowed."
- **What Kalshi's documentation pages say that bears on these endpoints** (docs.kalshi.com, read Nov 13; none of the nine pages carries a licence or terms statement):
  - Play-by-play: "Returns null for unsupported milestone types or milestones without a Sportradar ID." So the play-by-play is tied to a named outside provider.
  - Live data: "if the provider feed falls behind, a cached board may still be served". Scores come from a provider feed.
  - Rate limits: "Unauthenticated public requests are subject to separate limits. Authenticate requests where supported and back off on 429." And: "Publicly cacheable responses (Cache-Control: public), which include most market data".
  - The temperature index is described as "Kalshi-computed"; with `detailed=true` it adds "every member station's reported reading", which is station data from a source the page does not name.
- **This desk's reading, for the Head and the owner to overrule.** Live scores and play-by-play are a third party's data that Kalshi relays. No terms covering them have been read, the owner's waiver was given for market data, and the owner stopped a scores recorder once on terms. Under the standing rule (unsure means barred) **every sports request and the per-station detail are REMOVED from the probe**: the milestone lists, the two doubles event lists and the detailed index read. Asking for sports live data or play-by-play, even once, is a question for the owner first, with the earlier NO on a scores recorder quoted to them.
- **What stays:** the plain Kalshi-computed index for Miami (two recent hours and two hours on Nov 3), its calibration timeline, and the open Miami hourly temperature events with their milestones. These are Kalshi's own market data and settlement series, under the same owner-accepted terms risk as every kalshi-pull read. If the Head reads even these as outside that waiver, the probe stops here.
- **Effect on DBLTB:** its stage 0 (can the doubles state be read) cannot be answered by this probe any more. DBLTB stays conditional on the owner's decision about sports live data, and is not counted.

### (b) Held-out

No card, open or closed, holds out an hourly temperature series: the family was never read (the family table's row says NEVER READ; WXOTHER1 was a census only), and this desk's cost measurement has a fixed sample of Nov 5 to Nov 11 with no held-out. The probe's old window was moved to Nov 3 so it lies outside that sample. The daily temperature cards (WX1, WX3, WXDEAD1, WXDAYEND, WXENS1, WXLOW1) are on other series. With the sports requests removed, no sports, esports, politics or combo series is asked, so no held-out of INPLAYJUMP, POLGAPH, WHEEL0, S3, VOIDSNAP, COMBODONE, TIE3, MAPBREAK or REMATCH is in range. The job file's `heldout` line says the same.

### (c) The reader

`dbltb/livedata_fields.py`, written before the run exists. It opens only the files the run's manifest lists, checks each against the manifest's sha256, and prints for every field its path, its types and its count, and for time fields the first and last time. **It never prints a value.** A key is printed only if it is a plain lowercase field name; any other key (capitals, digits inside it, a dash: an id, a ticker, a station) is printed as `<key>`, and so is every key of a map (three or more keys whose values are all objects of one shape). It refuses a HELDOUT_ path, a file outside the run, a link, a manifest with no job and a file whose sha256 does not match. Tested on five made-up cases whose every value is a sentinel (77.77, 66.61, words starting SENTINEL, ids starting ZZ9): no sentinel appears in any output (`dbltb/fixture_outputs/`). **Known limit:** if Kalshi keys a small object by a lowercase word that is itself a name (a city, say) and the object is not a map of same-shaped objects, that word is printed as if it were a field name. It is a name, not a reading. The raw answers are opened by nothing else.

### What the narrowed probe can still answer

1. Whether the Miami index answers at all without a key, and which fields a point carries.
2. Whether a window ten days back still answers (is there history to measure on).
3. What a hourly temperature event's milestone looks like, and so whether the index is tied to the event.
4. How often the calibration changed.
It answers nothing about sports. Section 4's other unlocks (play-by-play, the reference price series, state reads) are NOT probed and wait for the owner.

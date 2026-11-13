# SOCDERIV, soccer extras against their own sibling markets: measurement registration

**Registered Nov 12, 2026, before any price or result of these series was read by anyone.** Written by Idea Desk B; the reader, the pull jobs and the scoring are built by the Testing Desk from this text. Card: `CENSUS_CARDS_NOV12.md`, card 19. Frozen leagues and legs: `socderiv/SOCDERIV_SERIES.json`. It runs SECOND, after TIE3.

`SOCDERIV | family: a derived contract priced away from what its liquid siblings imply, through a model that can be wrong; entry before kickoff, hold to settlement | risk class: mid price, 1 contract | stage Idea, measurement only`

**This stage is a ZERO-TRY cost and gap measurement. No result is read at all, no rule is scored, nothing is traded, and nothing here permits an order.**

## Rulings it rests on (Head of R&D, Nov 12, 17:15Z)

1. SOCDERIV is OUTSIDE the declined row "Lock and parity scans": it buys one contract that loses about half the time on a model value, not a riskless or implication-bound set.
2. **Every leg is read at the SAME minute, from minute-end candles (or books), never from a market list** (Forensics: list quotes of sibling markets are not simultaneous). Thin or one-sided minutes are counted, not filled in.
3. The model's weakness is stated, and a placebo shows what gap pure model error alone produces.
4. If small-league soccer costs more than about 5c a round trip at the measurement, it is closed there.
5. Every output carries the line: "candle freshness measured on Bitcoin 15 minute only, not on sports".

## Leagues and legs, fixed now

Two groups (file): **A, big leagues** (EPL, La Liga, Serie A, Bundesliga, Ligue 1, MLS, Liga MX, Brasileiro) and **B, smaller leagues and cups** (EFL Trophy, Copa del Rey, women's Champions League, Paraguay, Eerste Divisie, Liga Portugal, Latvia, Serie C). For each league four series: the game winner (three-way), the total-goals ladder, both-teams-to-score, and team totals. A ticker that returns no market is "no such series" and counted. Targets are both-teams-to-score and team-total markets. Corners are not covered: nothing in the siblings implies them.

**Sample:** games closing from 2026-09-12 to before 2026-11-13 (UTC), the 60 most recently settled games of each league, never extended. **Held-out:** closes from 2026-11-13 00:00 UTC, not pulled.

## The instant (one minute for every leg of a game)

1. **Kickoff** = the game-winner market's `occurrence_datetime` minus 180 minutes. **Check:** that market closed between 100 and 135 minutes after it; if not, or if the field is missing, the game is dropped and counted under "kickoff not derivable".
2. Start at kickoff minus 30 minutes and step back one minute at a time, to kickoff minus 90 minutes at most. Take the FIRST minute at which all of these are two-sided at the candle's close: the three winner markets, at least three total-goals strikes, and the target contract.
3. Every leg is read at THAT minute. If no minute qualifies, the game and target are "not filled" and counted. Nothing is carried from another minute.

## The sibling-implied value

Two goal rates, home and away, goals treated as independent counts. Fit by least squares to the mids of the three winner markets and of every two-sided total-goals strike at the instant. Then:

- both teams to score = (1 minus the chance home scores none) times (1 minus the chance away scores none);
- a team total over k and a half = the chance that team's count is above k.

**Stated weakness.** Real scores have a little more draws and low scores than independent counts give. That alone moves both-teams-to-score by about one point, in a known direction. The fit also absorbs the overround of the winner markets unevenly. So a gap of 2c to 3c means nothing.

## The placebo (what model error alone looks like)

For every game, refit the two rates with ONE sibling left out, the total-goals strike nearest 50c, and compare the model's value for that left-out strike with its own quote. That strike is a leg that should agree with the others, so its gap is model error plus quote noise and nothing else. The same statistics are reported for it as for the targets.

## What is reported, per group and per target type (counts first)

1. Games in the sample; kickoff derivable; filled at one minute; the share.
2. Median spread of the target, and its **round trip** = spread plus two fees of 0.07 x mid x (1 minus mid).
3. The gap on the cheaper side = implied value minus that side's ask: median, quartiles, 90th percentile, and the share at 8c or more with a spread of 4c or less.
4. The same four numbers for the placebo strike.
5. The residual of the fit on the fitted legs (how well two rates describe the siblings at all).

## Minimums and the kill rule, fixed now

- Under **150 filled games** in a group and target type: "no evidence at n = x".
- **A group is CLOSED on cost** if the median round trip of its targets is above 5c.
- **Closed as "not tradable"** if under half of the games with a derivable kickoff are filled.
- **Closed with "efficient, move on"** and the 90th percentile gap as the one number, unless the share of targets with a gap of 8c or more (spread 4c or less) is at least 10% AND at least twice the placebo's share at the same line. A gap the placebo also shows is the model, not the market.

## If a group survives

A separate registration before any result is read: buy the side whose ask is 8c or more under the implied value, spread 4c or less, 1 contract, hold; the measurement sample's results as development, read once; held-out from 2026-11-13, read once; **tries = the number of surviving group and target-type cells, at most 4.** Research bar as for every test (cash PF 1.5 on development and held-out, z 5.46). Near 50c that is about 950 bets for a true PF of 1.5 and about 320 for a true PF of 2.

## Requests

- **Lists job:** 16 leagues x 4 series = 64, plus 3 fee-field reads: **67 requests, about 80 pages.** The card said about 40; the count is higher because each league's series has to be asked for by name.
- **Candle stage (after TIE3 and the Head's go):** up to 960 games, about 16 contracts a game, the 61 minutes ending at kickoff minus 30; six games a request at the 100-ticker limit: **about 160 requests,** in two runs to stay under the size cap.

## Other venues are NOT in this registration

Quarter and half lines in basketball and football, tennis set markets and NBA margin markets are the same idea on other markets. Under lifecycle 7g they are this card on another venue. None is pulled or measured here; each would need its own amendment with its own sibling model.

## Honest limits

1. A gap can be my model's error. The placebo is there to say so, and a survivor still has to win a scored test.
2. An ask at one minute is not a fill, and thin contracts are quoted by few people: the size at the ask is not in a candle.
3. Team-total tickers were never seen by me; if their shape cannot be read, that target type is reported as unreadable, not guessed.
4. My probability that a group survives the measurement: about 15%. That a survivor reaches the bar: about 1 in 8.

## Dated amendment, Nov 12, 2026, 19:15Z, before any list or candle has landed (Head of R&D, 19:07Z)

1. **The cost line and the cost kill change from the round trip to the one-way entry cost.** Reported per group and target type: the median of (ask minus mid) of the target plus the entry fee as charged (0.07 x price x (1 minus price) at the ask plus 1c, rounded up to the next cent). **A group is CLOSED on cost if that median is above 4c** (it was: median round trip above 5c). Why (Head of R&D's ruling of 19:02Z, on Desk A's flag, changed before any price was read): a rule that buys and holds to settlement pays no second spread and no second fee, and with the one-contract fee rounded up to 2c a side the old round-trip line would have closed every market whose spread is above 1c before one bet was scored. It is a request-saving screen, NOT the bar: the scored profit factor pays the real ask, the 1c slip and the fee.
2. If a rule is ever registered from this measurement, the one void rule applies (Head of R&D, 19:08Z, the same for every hold-to-settlement card): a bet that fired and whose market has no yes or no result (a void, a refund, a walkover, an abandoned match, a result missing from the list) is booked as price refunded and fee kept: a fee-only loss. It is COUNTED in n, in the profit factor and in z, in the rule and in the placebo alike, and the number of such bets is printed beside n. Lists are read with status settled and the result field is read as given; no list is filtered on result.
3. **Forensics rules 4b (19:03Z) applied:** every kill line or check computed over the whole development sample (the cost line, the family start check, which titles or families are 'in') is labelled "selected on development": it can close a family, it cannot support a result; only the frozen held-out read can. The same lines are frozen, not recomputed, for the held-out. No haircut is built from a later candle.

## Second dated amendment, Nov 13, 2026, 06:21Z, text only, before any list or candle of these series has landed (the Head of R&D, seq 12, 06:22Z)

Two builds of this measurement's reader now print the same on 12 invented cases (the Testing Desk's `socderiv.py` 2993f6e1 at commit 28426619 and the History Miner's second build c679bef1: 408 figures and every verdict), after the Testing Desk moved its build to the literal text. Two readings are fixed here so the text says what both builds do. No number, no line and no kill value changes.

(a) **"The gap on the cheaper side"** (reported item 3) means the side of the target with the LOWER ASK, the YES ask against the NO ask at the look. If the two asks are equal, the side is YES. The gap is the implied value of that side minus that side's ask. **This takes the literal words:** "cheaper" is the lower price to buy, not the side with the larger gap and not the side the model favours.

(b) **The verdict lines are read in the order they are listed, and that order is their precedence, the minimum first:**
1. Under 150 filled games in a group and target type, the reading is "no evidence at n = x", whatever the cost line or the filled share would say. A cost median or a share taken on too few games cannot close a family.
2. Then the cost line, as the first amendment wrote it (the one-way entry cost).
3. Then "not tradable" (under half of the games with a derivable kickoff are filled).
4. Then "efficient, move on", unless the share at a gap of 8c or more (spread 4c or less) is at least 10% and at least twice the placebo's.

**This fixes an order the text listed but did not call a precedence.** The first reading that applies is the reading printed; the later lines' figures are still printed beside it as information.

### Clarifying line to the second amendment, Nov 13, 2026, 06:23Z, text only, before any list or candle of these series has landed (Auditor B's question; the Head of R&D, seq 13, 06:25Z)

**Two-sided, everywhere in this registration, means 0 < bid < ask < 1 at the candle's close: a bid of 0.00 is no bid and an ask of 1.00 is no ask.** Comparisons carry the 1e-9 tolerance or whole cents. It follows that at the instant (the first minute at which the target is two-sided) both sides of the target have an ask, the NO ask being 1 minus the YES bid, so the cheaper side of (a) is always defined; and a game with no such minute is not filled: counted, not priced. This is the standing reading across this desk's cards (the Head made it standing for every registration from tonight: a text that says "two-sided", "quoted" or "a side" without defining it is read this way). No number, line or kill value changes.

### Held-out line, Nov 13, 2026, 07:11Z, text only, before any list or candle of these series has landed (the Head of R&D's order of 06:53Z and ruling of 07:11Z). No rule, sample, figure or reading changes.

The sample is unchanged: the 64 series, games closing from 2026-09-12 to before 2026-11-13 (UTC), the 60 most recently settled games of each league. Every card found that ever held out any of these series, with its state:

- **W-CAT-SPORTS1 (Refinement):** five of the 64 (KXEPLGAME, KXLALIGAGAME, KXSERIEAGAME, KXBUNDESLIGAGAME, KXMLSGAME), held-out closes at or after 2026-10-30T02:53:19Z, never read. **Released by the Head of R&D 2026-11-13 06:51Z (dated line in its registration on `claude/refine-live` and in `RND_QUEUE.md`). Development here.**
- **SOCCER1 and SOCCERELO1 (the old research team, both run 2026-11-04, verdict "not enough data"):** every match starting at or after 2026-10-03T16:00Z frozen and never fetched, written as a pattern (KX + league + GAME, TOTAL, BTTS, SPREAD) over twelve leagues. EIGHT are leagues of this card (EPL, La Liga, Serie A, Bundesliga, Ligue 1, MLS, Liga MX, Liga Portugal): 24 of the 64 series (GAME, TOTAL and BTTS of those eight). Most of this card's sample for those leagues lies after that date. (Correction, same minute: I first told the Head of R&D nine leagues and 27 series, taking this card's Eerste Divisie, KXEERSTEDIV, for the Eredivisie that SOCCER1 used, KXEREDIVISIE. They are different leagues and different series. The release is by card and date, so it is not affected; the count is.) **Released by the Head of R&D 2026-11-13 07:09Z (dated line in `RND_QUEUE.md` on `rnd-queue` at 0f7bfccb, stamped 07:08Z there). Development here.** The Head's reason: their results say no forward plan is worth building and a re-run needs a new registration, their frozen third opens only if the first two windows pass, which they did not, and both rest on a score site whose terms now bar automated reads, so no read under their own registrations can ever happen.
- **USWEEP2 (the old research team, generic cheap-tail sweep, run once 2026-11-03, no lead):** 22 of the 64 series are on its frozen series list (I first counted 21; 22 is the count by name: the TOTAL series of EPL, La Liga, Serie A, Bundesliga, Ligue 1, MLS, Liga MX, Liga Portugal, Eerste Divisie, Paraguay and Serie C; the TEAMTOTAL series of EPL, La Liga, Serie A, Bundesliga, Ligue 1, MLS, Liga MX and Brasileiro; and KXMLSGAME, KXSERIECGAME, KXSERIECBTTS). For each, the last third of its anchor dates was frozen and never fetched. **Released by the Head of R&D 2026-11-13 07:09Z (the same dated line). Development here.**
- **SHARP1 (the old research team, registered 2026-11-08, no result on its branch; OPEN):** the GAME series of EPL, La Liga, Bundesliga, Serie A and Ligue 1, held-out kickoffs 2026-03-07 to 2026-09-07. This card's window starts 2026-09-12: no overlap, and nothing of SHARP1's is touched.
- **This card's own held-out:** closes from 2026-11-13T00:00Z, not pulled (as registered).
- Named soccer but hold none of the 64: TIE3 (first-half series; closed), TIE1 (two-leg advance series), XI1 (goal-scorer series).

No OPEN card holds any of the 64 series inside the sample dates.

**What was swept:** by whole-word series name, every text file of main, `rnd-queue`, the desk branches (testing, history miner, idea desks A and C, forensics, probe, stocks, research audit), `claude/refine-live` and the old research team's whole tree (`claude/epic-ptolemy-0amjd9` at 79724f00); because that team writes series as patterns, its soccer and sports registrations (SOCCER1, SOCCERELO1, SHARP1, SWING1, TIE1, SCOUT1, USWEEP2, FAMSPORTS, SERIESLAG1, ESPN1) were read by hand, which is how SOCCER1 and SOCCERELO1 were found; and Desk A's `HELDOUT_REGISTRY.md` (on `rnd-queue` at ad42ec54) was cross-checked. Not swept: the website's feature branches. A card naming these series only by a pattern in a file not read by hand could have been missed.

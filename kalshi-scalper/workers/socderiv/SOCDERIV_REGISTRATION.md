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

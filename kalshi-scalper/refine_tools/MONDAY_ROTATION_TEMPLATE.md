# Monday rotation report TEMPLATE (for Mon Nov 16, 2026, 07:43 AM CT; structure updated Nov 13)

Skeleton only. Written Nov 12, 2026 offline. It holds rules and text taken from committed files, and blanks for every live figure. PRIVACY RULE: no live account figure (P&L, profit factor, fills, wins, losses, balances, stop room, size) is ever written into this file or any file in the repo. Fill blanks in the MESSAGE to Main only. Times are US Central. No em dashes.

Sources: `kalshi-scalper/REFINE_HANDOFF.md` (Nov 12 section, standing duties), `refine_tools/GOLD_REPLACEMENT_TABLE_NOV12.md`, `refine_tools/SHADOW_RULES_NOV12.md`, `docs/GOLD_KILL_LATCH.md` and `docs/STRATEGY_LIFECYCLE.md` (sections 5, 5b, 7d, 7f) on `origin/main` (dc0057c2 at write time), `kalshi-scalper/README.md#SLOT-OICORE` and `#SLOT-EVENT830` (on `origin/main`; the local branch copy has SLOT-OICORE only).


---
## UPDATE Nov 13, 2026 (Head of R&D request; structure only, blanks stay blank; no live figure in this file)
Apply these changes to the sections below when filling Monday's message (Mon Nov 16, 07:43 AM CT):
1. **Gold (section 1 and the table).** Gold's latch state, GOLDOFF shadow and return rule: fill from Main by message. Rules to quote, from docs on main: kill = drawdown from gold's own cash peak against the fixed line, or net under the dollar line once 40 trades settled; alerts (rolling-60 PF under 0.7, rolling-100 under 1.0, 3 early sells in 40) are alerts only; RETURN = the GOLDOFF shadow's fill-checked record (60 signals, cash PF 1.3 or better) plus the owner's guard of at least 10 losses in the shadow record for an 88c or higher favourite (ROTATION_LANE.md and GOLD_KILL_LATCH.md). A shadow count is an upper bound until each row is checked against the book two or more seconds later. Blanks: ______ shadow signals so far, ______ losses so far, ______ fill-checked yet?
2. **Rotation lane (new row group).** Rules in docs/ROTATION_LANE.md on main (v1.1): a small-size slot after a recent shadow record of cash PF 1.3 or better over about 60 fillable signals replayed on real books; kills are a dollar drawdown line and net under minus 1c a contract at 50 fills; the rolling PF 0.7 line is an alert only; every shadow count fill-checked; admit list dated before its window; an 88c or higher favourite needs 150 signals and at least 10 losses; a live-versus-shadow check for the first 20 fills (fill rate and slip). Per lane strategy list IMPLEMENT, KILL, RETURN, and flag any missing.
3. **CFRTI-K probation seat 1 (new row).** Bitcoin 15 minute, cheap side at 120 seconds, 3 contracts, net floor set by the owner (the figure is in ROTATION_LANE.md, not here); it buys the same side and minutes as OICORE, so the two stack on some windows: report the overlap windows. From its first fill, cash basis, figures by message only. Rules to flag if missing: IMPLEMENT ______, KILL (net floor) ______, RETURN ______.
4. **Missing-rule flags to carry (from the Nov 13 poll).** OICORE and EVENT830 have no strategy-specific RETURN rule (general lifecycle rule only); gold's return rule needs the GOLDOFF shadow fill-checked; S-OICHEAPSKIP1 and the OICORE forward trackers wait for their own counts (dated lines on each registration); the R6 final read has a named cut (days through 2026-11-13T23:59:59Z) and waits for the Head.
5. **Research results to cite as closed (public, labels only).** POLAPPR1 read done Nov 13: 0 cells advanced, ALL_APPR and APPR_RCP NO SURVIVOR at this grid, others no evidence (POLAPPR1_RESULT.md); NOSIDE1 FAIL, closed; spread cell FAIL, closed; W-CAT weather, finance and indices, economics, politics, mentions, entertainment: no shortlist, closed; spot-lead DATA_LIMITED. Probe-ready count: ______ (0 as of Nov 13).
6. **Versions (7g) to add to section 3, none a claim of improvement; each is a candidate whose mechanical reason is stated and whose scoring needs the book and tape (rule: resting orders are scored only with a book and tape by the through-price rule; a taker exit sells at the bid and pays the fee; a stop fills at the first bid after it is crossed):**
   - **V1. OICORE resting bid on the cheap Bitcoin side** (already item A below). Mechanical reason: crossing the spread costs about the spread; a resting bid earns it. Needs trigger-window book data.
   - **V2. EVENT830 resting entry in thin markets** (silver, copper, oil, forex pairs, KXHYPE15M, KXBNB15M). Mechanical reason: these 15 minute series have wide quotes at the cheap side, so half the spread is a large share of a cheap contract's edge. Needs R6-style book and tape on these series (R6 records only the five trade markets today).
   - **V3. Closed approval and spread cells with a resting entry** (APPR_538 1 day 0.25 to 0.40 YES is the one cell that met the PF line in both thirds and failed the validation lower bound; the sports SPREAD cheap-YES cell; NOSIDE1 arm A). Mechanical reason: thin politics and sports quotes were paid at the ask in the candle model; a resting entry would pay less. Needs a recorded book for those series: none exists, so nothing can be scored now; not a reason to reopen a closed card.
   - **V4. Gold early-sell line (25c bid) versus holding or a lower stop**: NOT a version worth testing: EXIT1 (public) found holding beat every exit shape, the live 25c line among the worst, so any exit change reopens a falsified question; listed so nobody retries it without a new mechanical reason.
   - **V5. Gold favourite entry as a resting bid**: NOT a candidate: the maker replay on recorded gold books failed on adverse selection (W-MAKERREPLAY1), so the mechanical reason points the other way.
7. **Execution observations for Monday (from Forensics via the Head, Nov 13; words only, the cents figures are in the Head's message, not here; observations, not rules; any change is a 7g version for the owner):** OICORE fills land below the ask the bot saw, and the gap grows with price (smallest on the cheapest signals, largest above 15c); the ask the bot sees is the market-list quote, refreshed about every 11 seconds, so OICORE's 8c to 50c band test runs on a quote that can be several cents off at the top of the band; gold fills at its seen ask; gold orders with no price cushion no-filled more often than those with a small cushion (about 1.8 standard errors, weak), and the 0.88 to 0.90 limits filled worst; S-OICHEAPSKIP1 keeps scoring on the ask seen.
---

---

## 1. LEAD: is there a replacement for gold L1?

Owner priority (lifecycle 7f item 5, Nov 11): a gold replacement leads the report, with the candidates that pass the four uniqueness checks (7d) and how close each is to the proven bar (cash PF 1.3 or better over at least 100 fills, in 2 of 3 windows).

**Answer text (from GOLD_REPLACEMENT_TABLE_NOV12.md, re-check it is still true on Nov 16 before sending):**

> No. Nothing can replace gold L1 now, and there is no pass-ready sibling. The shared bar (Bonferroni z 4.55 over about 9,459 tries) needs about 254 independent trades at a 10c edge; no candidate has that. The fastest, W-DERIBIT1 (BTC hourly ladder vs Deribit implied probability), needs 1.5 weeks at its ceiling, has 76 usable hours against a bar of 80, leans FAIL, and Deribit data is FORBIDDEN for commercial use (card 88), so a pass could not go live on it without the owner clearing the terms. W-SPOTLEAD1 (spot-lead, BTC and ETH 15 minute) has n 58 and missed its own n 80 and both-halves bar, its R6 recorder stops itself at 2026-11-13 23:59Z unless the owner extends it, and it trades the same markets as OICORE. W-SPREAD-CELL1 (sports SPREAD cheap YES) is the only one that could return a verdict within days of a go (274 requests, about 11 hours at 25 reads an hour, expected n about 320 against a bar of 100), but it is the best of about 58 cells (lower 90 percent bound -3.6c, z 1.59) and is not started. Everything else is FAIL, FALSIFIED, UNDERPOWERED, BLOCKED on terms, or untestable on Kalshi alone; the favourite-late family is excluded by the owner rule.
>
> Next honest checkpoints: about 2026-12-01 (W-DERIBIT1 re-score, OICORE filters on ETH data, WXDAYEND weak bar if its logger starts) and the R6 extension question for W-SPOTLEAD1.

**Update since Nov 12 (fill from files; no live figures):**
- Status changes in W-DERIBIT1 / W-SPOTLEAD1 / W-SPREAD-CELL1 / shadow list S1 to S3: ______
- Did R6 get extended past Nov 13 (owner decision)? ______
- SPREADLISTS / SPREADCELL1 / NOSIDE1_CANDLES job results landed? ______

**Gold's own state (BLANKS, ask Main / fill from the report by message only):**
- Gold latch tripped? (`kalshiGoldKillCheck`, goldtrip.py since 2026-11-10 00:00Z): ______
- Drawdown from gold's own cash peak vs the fixed $58.75 line: ______
- Cash net vs the -$20 line once 40 trades settled (trades settled since re-arm): ______
- Alerts (rolling-60 PF under 0.7, rolling-100 under 1.0, 3 early sells in 40): ______
- If latched: gold's would-be orders are NOT logged (see section 3 item C and the gap in GOLD_KILL_LATCH.md "After the trip"); the return rule cannot be met yet.

---

## 2. Every live or probe strategy

Mechanism family is the entry mechanism plus the exit style (lifecycle 7f item 1). Status labels: Probe under review / Live / Latched off. Under 7f item 4 nothing is "Live" in the proven sense without cash PF 1.3 or better over 100 fills in 2 of 3 windows; the labels below follow the repo's own wording and the owner decides the final label.

| Strategy | Mechanism family | Status label (set on Nov 16) | IMPLEMENT rule (one line, source) | KILL rule (one line, source) | RETURN rule (one line, source) | Rule MISSING? | Figures (fill from the report by message only) |
|---|---|---|---|---|---|---|---|
| Gold L1 (`KXGOLD15M`) | Favourite-late buy and manage: buy the 88c to 97c side about 6 minutes (330 to 400 s) before the close, early sell at the 25c bid, no hold; the single favourite-late strategy (CLAUDE.md "FLOW1 removed / duplicates retired", lifecycle 7c, 7d) | Live, or Latched off if the latch tripped. Default text: "Live (the one favourite-late strategy)" | Gold is the only L1 market; size ladder from the 2% base, add-on capped at a quarter of base, 5.5% window cap, 25c exit, quiet hours per code (CLAUDE.md "L1 is the only strategy", "Dead markets dropped", `functions/kalshiLiveLib.js`) | Hard latch, cash basis, fees in, on gold's own settled orders since `GOLD_KILL.rearmAt` 2026-11-10 00:00Z: drawdown from own cash peak reaches fixed $58.75, or cash net under -$20 once 40 trades settled; sticky, no auto restart; alerts only for rolling-60 PF under 0.7, rolling-100 under 1.0, 3 early sells in 40 (`docs/GOLD_KILL_LATCH.md`, `functions/kalshiGoldKillLib.js`); the shared 12% loss stop also applies | Stays OFF until a shadow shows PF 1.3 or better over at least 60 trades and at least 7 days with the second half 1.3 or better, then the owner re-arms by a reviewed edit (`rearmAt` later, `rearmIsReturn: true`), first 30 trades at half size (`docs/GOLD_KILL_LATCH.md` "After the trip", lifecycle 5b) | NO for kill and return. FLAG: the return EVIDENCE is missing in practice (no gold shadow records exist; GOLDALL retired Nov 11; fix recommended, not built: one log-only `GOLDOFF` shadow rule, needs `deploy-sizing.sh`). Also: GOLD_KILL_RETURN_PROPOSAL.md says the Nov 10 numbers were a proposal; the merged note is the authority | Cash PF ____ (n ____), net ____, peak/drawdown ____, state ____ |
| OICORE (second slot, `KXBTC15M`) | Open interest flow, cheaper side, held to settlement (entry: new contracts specifically; exit: none, hold). Not favourite-late (it buys the 5c to 50c side) | Probe under review (README: "a capped live probe chosen by the owner, not a strategy that met the research bar"; no named counterparty) | In the 180 to 120 s before the close buy the CHEAPER side if its price is 5c to 50c and open interest at the candle ending 180 s before the close is at least 86,300 above its value at the candle ending 360 s before; one order per market; held to settlement; size per the current code/ladder (README#SLOT-OICORE; size schedule changed later by #699, read `functions/kalshiSlotLib.js` for the live count, do not copy a count from here) | Net below -$6 after 40 filled trades (`minNet`); 18 settled losses in a row; slot dollar caps (lifetime 6% of sizing base, at most $60; 3% open, 2% a day, 2% a window, 1% an order); a lost or refused order latches it off; 2026-11-13 forward read: FALSIFIED if PF under 1.0 on at least 100 fills or net under 0 on at least 150, or fill rate under 50% of signals, or median ask size under 10 (README#SLOT-OICORE) | Only the GENERAL rule: after a kill, 14 day cool off, then a fresh shadow of 100 to 150 fills at cash PF 1.3 or better, held-out second half 1.2 or better, at least 14 days, no day over 30% of net, owner approval by promotion packet; only a reviewed edit (moving `reviewedAt`) re-arms (lifecycle section 5, "OICORE if killed returns by the general rule above") | PARTIAL. OICORE has no return rule of its own in its README entry, only the general one. FLAG: the Nov 13 forward read (README) and any later size/ladder change are not in the sections read: check the registry and README for edits after the Oct 30 text | Fills ____, wins/losses ____, PF ____, net ____, fill rate ____, median ask size ____ |
| EVENT830 (second slot, 8 L1-free markets: KXSILVER15M, KXCOPPER15M, KXWTI15M, KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M, KXHYPE15M, KXBNB15M) | Calendar event, cheaper side on a US 8:30 AM ET release window, held to settlement (entry: 3 to 2 minutes before the close on 15 listed release windows; exit: hold). Not favourite-late | Probe under review (README: "capped live probe the owner asked for, not a strategy that met the research bar"; selected after the outcome, history is a reason to look forward, not evidence) | In the 15 minute window that CLOSES at a listed 13:30 UTC release (frozen calendar of 15 windows Nov 5 to Dec 23), 180 to 120 s before the close, if YES spread is 10c or less buy the cheaper side at 5c to 50c, IOC at that price (hard limit 50c, no slip), 1 contract, held to settlement (README#SLOT-EVENT830) | From 40 settled fills net below $0 latches it (this is PF under 1.0, NOT the owner's 1.2: the 1.0 to 1.2 band must be read by hand); 20 losses in a row; shared slot caps, 12% stop, 5.5% window cap; forward read 2026-12-07 (INTERIM per Main Nov 6: report fills, wins, net, price paid vs the registered 14c to 18c, releases left, no pass or fail unless a kill rule fired; re-read at 40 fills) (README#SLOT-EVENT830, REFINE_STATUS Nov 6 entry) | Only the GENERAL rule (lifecycle section 5); EVENT830's README entry has no return rule of its own | PARTIAL. FLAG: no EVENT830-specific RETURN rule found; the owner's 1.2 line is not in code; the registered pace (about 4.8 trades per date, 40 fills by about Dec 4) is about double the observed fills per date, so Dec 7 will probably have fewer fills than planned | Fills ____, price paid ____, wins/losses ____, net ____, releases left ____ |

Not live, listed so the table is complete: XRP, Bitcoin (L1), Ethereum, AUD/USD, USD/CAD, natural gas are PAUSED or off the L1 list in code with no resume date; Dogecoin was removed from L1 (lifecycle section 5 return table; a return is a reviewed edit plus the general rule). XRPYES10, KESTREL, FLOW1, GOLDALL, XRPFAV6, LANTERN were retired. Write one line only if Main says any of these changed.

**Strategies with a rule I could not find:** (none missing for kill; see the FLAG cells above: OICORE and EVENT830 have no strategy-specific RETURN rule, only the general lifecycle rule; no gold shadow exists to feed gold's return rule).

**Mechanism-family mix (7d item 4):** gold = favourite-late; OICORE = open interest flow (cheap side, hold); EVENT830 = calendar event (cheap side, hold). Two of the three are cheap-side-and-hold probes: say so. Correlation note: OICORE and any W-SPOTLEAD1 candidate trade the same BTC 15 minute windows.

---

## 3. VERSION candidates (not strategies, lifecycle 7g)

A version changes how an existing strategy is executed, not what it bets on. These are candidates only; none changes a rule.

**A. Resting-bid entry for OICORE's cheap Bitcoin side (Forensics desk, public R6 books).**
- Finding: a resting buy at the bid on the cheap Bitcoin side at about 178 s left filled 98.6 percent of the time and saved about 1.5c a contract against taking the ask (interval +0.6 to +2.3), over 349 windows WITHOUT OICORE's trigger.
- Caveats, state all of them: NOT yet checked by the Verification Analyst; 349 windows are non-trigger windows, so it says nothing proved for the windows that fire OICORE; needs a resting order type the bot does not send (the slot sends IOC at the touch today), so it is new order code and a new risk review, not a setting; a resting order that fills late or only on adverse moves is adverse selection (the earlier maker-limit research found missed fills were disproportionately winners, CLAUDE.md "Registered before running: maker-limit entries"); fill rate and saving must be read together.
- Also report: the no-trigger taker baseline flipped from PF 1.39 to 0.61 between adjacent weeks. That is the size of the noise in any short OICORE record; use it when judging OICORE's weekly figures. (Public R6 baseline, not an account figure.)
- Status to write on Nov 16: Verification Analyst check done? ______

**B. Gold fill measurement (Forensics GOLDHAIRCUT1, branch `claude/forensics-desk`, `kalshi-scalper/workers/forensics/GOLDHAIRCUT1_RESULT.md`, commit 870de04; 292 windows Oct 29 to Nov 11; NOT yet checked by the Verification Analyst).**
- IOC buy at the ask seen: filled 59 percent at about 2 s, 49 percent at 6 s, 46 percent at 10 s. With +1c slip: 94, 83, 73 percent. 1 and 15 contracts the same. Price trustworthy to about 0.2c a contract.
- RULE FOR THIS REPORT: any gold shadow count measured against the return rule (60 trades, PF 1.3) is stated as an UPPER BOUND on the trade count, because a fill at the touch is overstated by a quarter to a half, unless each shadow row was checked against the book 2 or more seconds later. Write: "Gold shadow count ____ is an upper bound (rows not checked 2 s later)" or "checked: ____".

**C. Gold shadow logging (the gap from GOLD_KILL_LATCH.md "After the trip").** One log-only shadow rule on gold (for example `GOLDOFF`: `KXGOLD15M`, favourite side, 0.88 to 0.97, 330 to 400 s left, 1 contract) so the return rule is computable; recommended, not built; needs a reviewed edit of `SHADOW_RULES`, `bash functions/deploy-sizing.sh`, and a written exception to the 7c cap. It models a hold at the touch, not gold's 25c early sell, so its PF is a research figure, not the live cash PF. Status: ______

**D. Other versions Main lists (SPREAD, spot-lead, shadow list S1 to S3):** ______ (S1 approval NO side, S2 sports SPREAD cell, S3 combo house side; S3's rule is a skeleton to be completed by V2 or the Head of R&D BEFORE recording.)

---

## 4. The ONE recommendation

One line, then options. Pick one; do not hedge.

**Recommendation:** ______ (write after the data pulls; default if nothing changed: "Keep gold as is, no replacement exists; keep OICORE and EVENT830 to their own kill rules, small; ask the owner for A below.")

**Decision options for the owner (to be asked by popup, recommended first):**
1. Keep the current set unchanged; next checkpoint about 2026-12-01.
2. Approve the log-only gold shadow (`GOLDOFF`) so gold's return rule can be met if the latch trips.
3. Extend the R6 recorder (stops 2026-11-13 23:59Z) so W-SPOTLEAD1 can reach n 80.
4. Start W-SPREAD-CELL1 (274 requests, one pooled block, read once; pass needs n 100 events, PF 1.5 at +1c, clustered lower bound above 0, z 3.1).
5. Ask Verification to check version candidate A before anything is built.
6. Pause or reduce a probe (only if a kill rule has fired or the Nov 13 OICORE forward read reads FALSIFIED).

Nothing is promoted by this report; a live change needs the owner's own popup.

---

## 5. Data pulls to run BEFORE sending (offline files, owner's privacy rule)

PRIVACY: figures go to Main by message only. Do not paste any output into a repo file, a commit message or a PR. Run python as `python3 -I script.py args`. Outputs stay in the scratchpad.

- [ ] `git fetch origin main` and re-read `docs/GOLD_KILL_LATCH.md`, `docs/STRATEGY_LIFECYCLE.md` 5, 5b, 7d, 7f and `kalshi-scalper/README.md` SLOT-OICORE and SLOT-EVENT830 for edits since Nov 12 (new size, ladder, kill or return rules).
- [ ] Fresh nightly report JSON, `dash_long.sh` style: the read-only report endpoint with the owner's token, 7 days with `?orders=1` (the token lives in the Claude environment's secrets, never in chat or a file). `dash_long.sh` was not found in the repo; it is a scratchpad script, so reuse the one from the current session's scratchpad or ask Main. Do this with the network ALLOWED only in the session that holds the token.
- [ ] `SIZING_BASE=<ask Main> python3 -I kalshi-scalper/refine_tools/nightly.py <report.json> [YYYY-MM-DD]` (without the base, stop room is not shown).
- [ ] `python3 -I kalshi-scalper/refine_tools/goldtrip.py <report.json> [2026-11-10T00:00:00Z]` for the gold latch lines (drawdown vs $58.75, net vs -$20 after 40).
- [ ] `python3 -I kalshi-scalper/refine_tools/scorer.py <report.json>` for the per strategy scoring (also run `shadow_read.py` or `oicheapskip.py` only if Main asks).
- [ ] Confirm the Nov 13 OICORE forward read status and the Dec 7 EVENT830 interim plan.
- [ ] Confirm the Verification Analyst status of version candidates A and B.
- [ ] Scan the draft for a live figure (any dollar amount, PF, fill count of our own strategies) and strip it from anything written to the repo; the message to Main carries the figures.
- [ ] Final check: no em dashes; times in US Central; status labels match section 2.

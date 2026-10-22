# Where things stand, 2026-10-22 (for the 2026-11-17 review)

Written by the strategy-research session. Plain numbers; nothing here changes a live trade.

## 1. Bottom line
- **Nothing meets the deployment-ready standard** (an edge that survives out of sample, with a worst case stated).
- **One strong lead (FLAT)**, two live changes still collecting evidence, and a long list of ideas that failed.
- **Money, honestly:** the entry rule earns about +0.9c per contract held to settlement. At about 26 fills a day and 1 contract each that is roughly **$0.25 a day (about $7 a month)**. Bigger size is leverage, not a better edge (SIZE1). The account cannot pay its costs on this edge alone; that needs a larger edge, which is what the hunt is for.

## 2. The live account, Oct 7 to 22 (386 settled fills, net -$11.74)
- Held to settlement, the 366 settled fills lose **5.7%** (break-even about 6.8%) and make **+0.92c** a contract. The entry rule is not the problem.
- Two sizing events (22 and 12 contract Bitcoin losses, -$20.36 and -$11.11) were two thirds of the damage; both are capped now.
- Two-fill windows lose 14.3% against 4.4% for single-fill windows (-$44.49 against +$26.20). #459 (one crypto order per window) targets this.
- The 21 exits at 25c cost about $2.20 against holding; they are not the leak.
- Orders that did not fill would have done worse than the ones that did (8.1% against 5.7% losses): the fill rule is not selecting against you.

## 3. Live changes still collecting evidence (all deployed by owner decisions)
| Change | Live since | What decides it |
|---|---|---|
| #453, 10-minute entry (Bitcoin, XRP, natural gas) | Oct 21/22 | 60 orders per series (FWD8) |
| #459, one crypto order per window | about Oct 22 02:30 to 03:00Z | thinned crypto orders, 2-loss windows per week |
| #458 `rise3` and #461 `rng5` logging, #460 read retry | `rng5` and #460 about Oct 22 17:00Z | the live FLAT record |

## 4. The one strong lead: FLAT
Rule: take an L1 favourite only if its 5-minute price range was 15c or less and it moved 5c or less in the last 3 minutes (about 15% of entries).
- History, 69 days, 24,792 entries: **+1.76c against -0.17c** (z 5.25), every month and half the same sign.
- Fresh days, 287 flat entries: +1.62c against +0.02c (z 2.63), 9 days. Replication on untouched series (mostly SOL): same direction, z 1.67, too few entries to confirm.
- Works on crypto, energy and metals at the 6-minute entry. **Does not work on gold, Dogecoin or FX.** Adds nothing at the 10-minute entry (Bitcoin, XRP, natural gas already use it).
- **Decision taken:** log only. Re-propose a filter (Ethereum only, 6-minute entry) at the review if the live data supports it. Check then: live FLAT rate should be near 15%.

## 5. Tried this session and dead
| Idea | Result |
|---|---|
| Skip the whole window when 2+ series qualify (CROWD1) | -1.40c, missed its -1.5c bar; #459 already covers the tail |
| Enter only when other crypto agree (CONC1) | FALSIFIED (reverse sign is registered as a forward claim, CONC2-F) |
| Skip entries after a recent flip (LOSSCL1) | no clustering (6.3% against 6.5% losses) |
| Best entry minute per series (ENTRY1) | overfit, +0.32c, z 0.69 |
| Size up on FLAT (SIZE1) | doubles profit and bad days together: leverage, not an edge |
| Daily-high weather markets against the official forecast (WX1) | **-4.70c, z -4.17**: the market beats the forecast |
| Equities and ETFs (24 tries on Alpaca-style data) | none cleared; the real premia are about 2% a year (cents a month at your size) |

## 6. Open paths
- **Market screen** (77 liquid hourly, daily and weekly series): running; only series flagged LEAD (150+ entries, 10+ days, +1c, z 2.5) get reported.
- **Recorder proposal** (read-only, public data, no orders): tests whether Kalshi quotes lag the spot index in the last 150 seconds. The only route I see to an edge bigger than a few cents. Needs the main session's server for 14 days. Spec: `studies/RECORDER_SPEC_2026-10-22.md`. Your decision.
- **Dated reads:** forward claims (FLAT2-F, CONC2-F, FWD7, FWD8, FEAT2-F, FEAT4-F and others) run once after 30 fresh days (about **2026-11-12**) or on 2026-12-01.

## 7. Dates
- Nov 12: forward reads. Nov 17: owner review (FLAT filter, 10-minute entry, #459 tripwires: net P/L since the deploys at or below -$15, or two windows in a week with two losing filled orders).

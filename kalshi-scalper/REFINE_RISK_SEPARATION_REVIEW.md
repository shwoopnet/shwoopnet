# Review of docs/STRATEGY_RISK_SEPARATION.md (PR 689), with the SCALE_STEP review folded in (Nov 1, 2026, 7:15 PM CT; read only, nothing live)

Requested by main at the owner's direction. Sources: nightly report `hours=2160&orders=1` (L1 orders since Oct 7, OICORE `slotOrders` since Oct 30), the draft `docs/STRATEGY_RISK_SEPARATION.md` on `origin/claude/risk-separation-doc`, and `functions/kalshiLiveLib.js`. The L1 step arithmetic is in `REFINE_SCALE_STEP_REVIEW.md` and its conclusion (keep +1, or +2 at most) is repeated at the end. Dollars are after fees. The sizing base is unknown to me: I show percentages at $540 and $779 (see the step review for why both).

## (1) Each strategy on its own, from the live record

| | L1 gold + Dogecoin | L1 all markets since Oct 7 | OICORE |
|---|---|---|---|
| Settled fills | 393 | 890 | 10 (15 orders, 5 no-fill) |
| Losses | 18 | 63 | 7 |
| Largest single loss | -$9.58 (13 contracts) | -$20.36 | -$1.70 |
| Worst rolling 24 hours | -$11.30 (Oct 26 to 27) | -$28.26 (Oct 10 to 11) | -$2.45 (Oct 30 to 31) |
| Worst UTC day | -$7.34 (Oct 27) | -$19.95 (Oct 10) | -$2.45 |
| Worst losing streak (orders in a row) | 2 (-$8.52) | 3 (-$3.49) | 3 (-$2.45) |
| Spend per order (cost of contracts) | about $12 to $15 | | median $0.70, mean $1.52, max $4.50 |

As a share of the base ($779 / $540): L1 largest loss 1.2% / 1.8%, worst 24h 1.5% / 2.1%; OICORE largest loss 0.2% / 0.3%, worst 24h 0.3% / 0.5%. The "all markets" column includes Bitcoin, XRP and the probes, now paused, and the pre-12%-stop era, so it is history, not today's L1.

**Overlap.** OICORE filled in 10 windows. L1 (gold or Dogecoin) also filled in 1 of those 10 (10%). Of the 42 windows in which gold or Dogecoin filled since OICORE started, OICORE filled in 1 (2%). In that one shared window OICORE spent $0.60 and Dogecoin $11.84. So today the coupling costs nothing in dollars: OICORE's whole gross loss so far ($6.60) is 7% to 10% of one L1 stop and its largest window use ($4.50, at a 50c entry) is 0.8% of a $540 base.

What the record can and cannot support for OICORE: 10 fills and 3 wins. The win rate 30% has a 95% range of about 11% to 60%. One 6c entry that won paid $9.36, which is 48% of the strategy's gross wins; remove it and the net is +$3.67. Profit factor is 2.97 (it was 4.1 yesterday after 8 fills: that is how fast it moves). This is enough to size a small probe, not to set a scaling rule.

## (2) Are the draft numbers sensible?

**Cost per loss to keep in mind.** OICORE entries are mostly 6c to 16c (median 9c, mean 16c, a few at 39c and 50c). A lost contract costs its price plus about 0.6c of fee: 9.6c at the median, 17c at the mean, 52c at a 50c entry.

| Draft parameter | My read | Why |
|---|---|---|
| OICORE own stop 4% of base | **Too loose to matter at 10 contracts, too tight at 30** | 4% is $21.6 ($540) to $31.2 ($779). At 10 contracts and median price that is 22 to 32 losses, so the 18 loss streak kill and the -$6 net floor always trip first; the draft's "about 10 losses at 30c" is a price OICORE rarely pays. At 30 contracts the same 4% is hit after 8 to 11 median-price losses, and a streak of 10 happens in 58% to 67% of 100-trade runs if the 28% win rate is real. The stop and the size ceiling must be set together. |
| OICORE own window cap 2% of base | **Fine for now, binds on the wrong trades at size** | 2% is $10.8 to $15.6 against a record maximum of $4.50. But the three wins came at 50c, 39c and 6c; at 25 or more contracts a 50c entry costs $12.5 and the cap would cut it first. Better as a dollar cap per order (about 1% of base) plus the window cap. |
| L1 12% stop, 5.5% window cap | **Sensible, leave** | Gold + Dogecoin worst 24h was 1.5% to 2.1% of base, worst day 1.0% to 1.4%; the stop is 6 to 8 times that. The window cap (5.5%) binds only when two orders in one window pass about 22 contracts each ($779) or 15 each ($540). |
| Account backstop 15% stop, 6.5% window cap | **Sensible, slightly loose** | Both are inside the sum of the own limits (16% and 7.5%), as the draft intends. With OICORE's real use under 1% of base the backstop is effectively L1's own 12% plus a little. Keep, but 14% would lose nothing. |
| OICORE size one per $50 of base, floor 10, ceiling 30 | **Floor and rule fine, ceiling too high** | 10 at today's base matches a base near $500 to $550, which supports reading B in the step review (cap equals target, base near $540). A 30 ceiling means an 18-loss streak costs $52 to $92 (7% to 17% of base). Ceiling 15 until 100 settled fills (see 1 below). |
| Step: up to 3 per 3 days, only after 30 settled fills net at or above zero | **Gate is too weak** | I simulated a strategy with NO edge (win chance equal to the entry price, fees paid), entries drawn from the 10 observed prices: it passes "30 fills net at or above zero" 43% of the time, 60 fills 42%, 100 fills 39%. A real +5 point edge passes 71% at 30 fills. The gate lets a no-edge probe step up about 2 times in 5 and rejects a real one 3 times in 10. 3 steps a time makes the next streak cost 30% more at once. |
| Kill rules: 18 losses in a row; floor -$0.60 a contract | **Keep both; the streak kill will fire sometimes by chance** | If the true win rate is 28%, P(18 in a row at some point) is 6% in 100 trades and 16% in 250. If it is only 20%, 28% and 60%. So it is a tripwire, and a hit is not proof the idea is dead. The floor of -$0.60 a contract is 6 median-price losses with no win (about 6 of 40 fills), a normal run at 28%. |

## (3) What a 10-loss streak costs OICORE (28% win rate, so 10 losses in a row is 3.7% from any one start; **within 100 trades it is 67%**, within 40 trades 32%, within 250 94%)

| Contracts | Median entry 9c | Mean entry 16c | A 50c entry |
|---|---|---|---|
| 10 | $9.6 | $16.9 | $51.7 |
| 20 | $19.1 | $33.9 | $103.5 |
| 30 | $28.7 | $50.8 | $155.2 |

Against the draft stop: 4% is $21.6 to $31.2, so 20 contracts at the median price reaches it after a 10 loss streak and 30 contracts does not even need ten. An 18-loss streak (the kill) costs $17 / $35 / $52 at median, $30 / $61 / $92 at mean entries. The draft's "3.7% of the time" is the per-start figure; a reader will take it as rare when over a normal 100 trade stretch it is the usual case.

## (4) Recommendation, parameter by parameter

1. **OICORE size: stay at 10** until 100 settled fills AND the Nov 13 forward read; **ceiling 15, not 30**, until then, and 20 only by a reviewed edit with 250 settled fills. Rule "one per $50 of base" is fine as the formula.
2. **OICORE own stop: keep the draft's 4% of base** ($21.6 at $540, $31.2 at $779), but tie it to the size: a 10-loss streak at the mean entry price (17c) costs $16.9 at 10 contracts, which fits under 4% at either base, and $25.4 at 15, which fits at $779 but trips the stop at $540. So at the ceiling of 15 a normal 10-loss run can end OICORE when the base is near $540. That is acceptable as a tripwire for a probe, but it should be a choice, not a surprise. 3% would trip even at 10 contracts at $540 ($16.2 against $16.9), so do not go tighter.
3. **OICORE window cap:** keep 2% and add a **per-order dollar cap of 1% of base** so a 50c entry is cut by size, not by hitting the window cap.
4. **Step rule:** at most **+2 per 3 days**, and the gate **60 settled fills, net at least +1c a contract AND at least 20% wins** (a no-edge probe then passes about one time in three). Steps down at once when either fails. Do not let any step happen before the Nov 13 read.
5. **Kill rules:** keep 18 in a row and add the net floor -$0.60 a contract, evaluated after 40 fills as drafted. Add: step back to the 10-contract floor if the last 60 settled fills net under -$1 a contract.
6. **L1:** keep 12% and 5.5%. Step: **keep +1; if the owner insists, +2**, kill rule in the step review (last 100 settled orders at the larger size lose more than 8% or net under +0.5c a contract, a day below -2% of base, no-fill share above 45%).
7. **Account backstop:** 14% to 15% stop and 6.5% window cap are both fine. Honest note: today OICORE's use is under 1% of base, so the separation changes almost nothing in dollars. It is worth building mainly so OICORE's later scaling cannot reach L1's stop, which is an argument for building the OICORE limits first and the L1 step change last (the draft's order is already that).
8. **Draft wording to fix:** "10 losses in a row happens about 3.7% of the time" should read "from any one start; in a 100-trade run it is about two chances in three." The example "10 losses at 30c" should use the observed 9c median and 16c mean.

## What this can and cannot support
- 10 OICORE fills cannot set a size, a win rate or a stop. They support a small probe with a streak tripwire, and the arithmetic of what a streak costs, which does not depend on the sample.
- The L1 numbers rest on 18 losses in 393 fills (63 in 890 fills including paused markets).
- The overlap result (1 shared window of 10) is small and may change if OICORE trades more often.

## Count for deflation
About 14 comparisons and simulations (6 stats by strategy, 4 streak and gate simulations, 4 cost tables). N about 728,705. No edge claim anywhere here.

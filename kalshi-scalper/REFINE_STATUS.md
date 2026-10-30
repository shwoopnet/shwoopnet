# Live Strategy Refinement, status (newest first; times US Central)

Scope: refine what is live (L1 on gold and Dogecoin, the OICORE second slot). New strategy families go to V2 via the main session. Read only: no trading code, no deploy, no merge.

## Entries

**2026-10-30 1:45 PM CT, first read of the live record (nightly report, 30 days, 855 settled). No kill rule has triggered. No flag for the main session.**

Live, per market (dollars after fees, settled only):

| Market | Window | Settled | Lost | Loss rate | Net | PF | Cents per contract |
|---|---|---|---|---|---|---|---|
| Gold | 30 d | 215 | 10 | 4.7% | +$42.48 | 1.66 | +2.34 |
| Gold | last 100 | 100 | 5 | 5.0% | +$20.24 | 1.45 | +1.83 |
| Dogecoin | 30 d | 143 | 7 | 4.9% | +$8.61 | 1.53 | +2.09 |
| Dogecoin | last 100 | 100 | 4 | 4.0% | +$9.63 | 1.94 | +2.93 |

All markets, 7 days: 362 settled, 30 lost, net +$8.25, PF 1.10 (paused XRP, AUD/USD, USD/CAD and natural gas are still inside it and net -$8.04 between them; gold and Dogecoin together +$16.07).

Rule checks:
- **Dogecoin at 5 contracts** (since the 21:05Z Oct 29 deploy): 12 settled at 5 contracts, 1 lost, net -$0.84 (-1.5c a contract). The kill rule (last 100 at 5 lose more than 8%, or net under +0.5c) cannot be read until 100 exist and the review is at 250 settled; nothing to report. Fill rate: 9 of 21 attempts no fill (43%) against the 60% over 20 flag in DOGEFILL, so no flag, but it is above the 26% before the deploy and worth watching.
- **Dogecoin on gold's ladder (Oct 30 change):** the newest Dogecoin order in the report is still 5 contracts, so the ladder is not visible in the record yet (or not deployed yet). Check the next report for any Dogecoin count above 5; the size lock allows up to 50.
- **Gold quiet hours (20:00 to 23:59 CT):** the last gold order in that block is Oct 29 02:54Z (Oct 28 9:54 PM CT), before the Oct 29 live date. No gold order in the block since. Interim review is still MKTTIME1-F (V2), about Nov 24 to 26. Nothing to do.
- **Oversize:** none since Oct 29 16:00 CT. (The 374 listed over 30 days are old Bitcoin, XRP and probe orders measured against today's limits.)
- **Paused markets:** no new fills on Bitcoin, Ethereum, XRP or the probes since Oct 30 00:00 UTC.

Early signs, not findings (small counts):
- Gold since the Oct 29 deposit marker: 11 settled, 1 lost, net -$0.37. Gold at 11 to 15 contracts: 9 settled, 1 lost, -$3.42 (-2.9c a contract); at 21 to 28 contracts: 2 settled, both won, +$3.05. V2's GOLDSLIP (+1.82c slippage at 16 to 20 contracts, 6 orders) is the better watch for size effects; I add nothing until that has 20 orders.
- Entry lead: 10 minute entries (XRP, now paused) were the loss: 75 settled, 12 lost, -$7.20, PF 0.55. 6 minute entries: 286 settled, 18 lost, +$14.22, PF 1.22.

**Not done yet:** OICORE (second slot) is not in the nightly report (it only reads the L1 collection `kalshiLiveOrders`). The forward read is Nov 13, and I have no read path for `kalshiSlotOrders` from this container. Needs a decision from the owner or main session: either a report extension (a reviewed code change, not mine to make) or the Bot page export of the slot orders pasted in.

**Next:** nightly read of the report each pass; check Dogecoin counts above 5 and the first Dogecoin loss at the new size; first OICORE fills when the owner shares an export. No brief drafted: no refinement idea has a hypothesis that is not already a V2 test (L1 filter, exit and sizing tests are closed by the Oct 28 instruction; STRUCT1 and EXIT1 already say the 25c exit is neutral to slightly helpful).

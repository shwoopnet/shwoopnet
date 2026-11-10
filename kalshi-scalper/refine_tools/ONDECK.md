# On-deck shadow candidates (live side), current as of 2026-11-10

Basis: cash, PF per contract, fee unrounded (matches live avgFee), hold to settlement. N tried for deflation about 770. Bonferroni z about 5.2 is unreachable at these n, so every rule below is a SHADOW candidate, never a pass. Shadow rows assume a fill at the touch (upper bound): read wouldFill. Sources: REFINE_STATUS.md Nov 9 to Nov 10 entries, SHADOW_REGISTRATIONS_WEEK1.md.

## Registry (PR 753: XRPYES10 and GOLDALL already on main, XRPFAV6 and GOLDHI6S added; needs `bash functions/deploy-latest.sh`)

| id | rule | independent-window PF (n), +0c / +1c | candle signals a week | prior |
|---|---|---|---|---|
| GOLDALL | gold, favourite 0.88-0.97, 6m look, every L1 signal logged | Aug 13 to Sep 1: 1.60 (439) / 1.36 | 126 (candle model); about 65 in live fills | low-medium |
| GOLDHI6S | gold, favourite 0.92-0.97, 6m look, spread at most 2c | Aug 13 to Sep 1: 1.68 (265) / 1.35 | 72 | low |
| XRPFAV6 | XRP, favourite 0.88-0.92, 6m look, spread at most 2c | June to early Sept: 1.645 (137) / 1.46 | 88 | low |
| XRPYES10 | XRP, YES 0.88-0.97, 10m look | June to early Sept: 1.91 (70) / 1.66 | 55 (candle model); about 13 in live fills | low |

Independent means a window not used to pick the rule (gold Aug 13 to Sep 1 covers 1,358 of 2,153 listed windows; Aug 6 to 12 and earlier not reached; XRP 12 pre-registered dates, 1,147 of 1,152 windows). Net is thin: GOLDALL +1.5c and GOLDHI6S +1.0c a contract at +1c; XRPFAV6 +3.4c at +0c. GOLDALL exploratory split by |rise3| 0.05: moving 1.78 (334) / 1.52, still 1.21 (105) / 1.03. Live XRP overall is PF 0.49 over 65 fills (paused), so the XRP priors stay low. Gold live cash PF since start 1.36 (318), tripwire cumulative 0.88 on its latest check.

## Pass and kill rules (common, from the lifecycle spec, set before any forward row)

- Pass: 150 forward shadow signals, cash PF at least 1.3 per contract, second half at least 1.2, at least 14 days, no single day above 30 percent of net. Forward read 2026-12-14.
- Kill: net under -1c per contract after 50 shadow signals, or fewer than 40 signals in 30 days (retire).
- Counterparty: none named for any rule.
- A pass only earns the incubator ($20 cap, $5 per order), then ladder step 1, owner approves.

## Retired before their first forward row

- ETHNO6: live cash 2.59 (n 53) was its only support. 4.3 weeks of Ethereum candles (2,609 windows): halves 1.04 (181) / 0.72 (189) at +0c, 0.89 / 0.61 at +1c; unseen portion 0.76 (277).
- ETHL1: candles 0.90 (361) / 0.75 (383) at +0c, 0.77 / 0.64 at +1c.
- BTCHI6: live 2.60 (n 91) had no losses in the first half. Independent Jun to Jul window 1.13 (268) at +0c, 0.91 at +1c; fails the 1.3 bar (interim 1.42 on n 137 did not hold).
- BTCHI10 (and XRPFAV10): dropped before merge. BTCHI10 independent window 1.27 (66) / 1.05 on the 78 percent pull, later 1.584 (n 83) / 1.304 on the full pull, but V2's Jun to Aug run had 0.90 (n 289) on overlapping months, so it is contested; do not re-add on this alone.

## Closed lists (do not re-run without a new reason)

- W-DECK1 (gold, Bitcoin, 40 cells each, 9.9 weeks): no cell at 1.3 in both halves. Longshot (cheap side 0.03-0.12), near-even (0.40-0.60) and late favourite (0.97-0.99, 2 to 3 minute look): below 1.0 in at least one half; fee and slip eat the edge. Best cells about 1.0 to 1.07.
- W-DECK2 and W-DECK3 (XRP, 8 days then 2.8 weeks): none qualify; the F4 0.97-0.98 infinite PF is an artifact. Ethereum had too few windows then (untested at that time, since failed in W-RERUN4).
- W-SUPPLY1: untested public series, L1 structure, 0 of 54 pass. Silver the only one above 1 (1.07; at +1c 1.19 with halves 1.28 / 1.11, 1.39 at +0c), tracked by C9. OICORE rule has n 0 outside Bitcoin (the 86,300 threshold is Bitcoin scale).
- Hourly ladders (KXGOLDH, hourly strikes): not testable with the data held. KXGOLDH ladder (25,391 strikes) not pulled; G3H1 pass is VOID (universe look-ahead).
- Ethereum smooth climb: the gate removes 95.5 percent of in-band windows; Ethereum paused in code.
- Exit shape: hold beats the 25c exit on the independent gold window (hold 1.598 vs exit 1.512 at 0c; generous bid-low trigger 1.325). Consistent with EXIT1.
- OICORE independent Jun to Jul window: 27 triggers (need 40), PF 1.59 at +0c, 1.41 at +1c; NOT_ENOUGH_DATA, swung 0.74 / 1.07 / 1.59 as n grew.

## Still hunting

Needs data, not a result: see SUNDAY_SUPPLY_DRAFT.md.

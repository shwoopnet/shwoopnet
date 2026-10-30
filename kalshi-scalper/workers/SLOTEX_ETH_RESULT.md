# SLOTEX-ETH result (2026-10-30)

Registration: `workers/SLOTEX_ETH_REGISTRATION.md` (commit 64d731d, pushed before scoring). Code: `src/scalper/slotex.py --eth`. N = 64 cells. Ethereum `KXETH15M`, windows closing 2026-08-06 to 2026-10-27; nothing on or after 2026-10-28 read. Next-candle ask fill; fees on the entry and on the sell; bid 0 or missing at 60 s = stake lost. Rows with n 0 print PF "inf" from the code: read them as no trades.

ETH windows 7869; discovery doi values 4357; ETH-P90 = 8799 contracts

| threshold | exit | cost | n disc/val | C=5 PF disc | C=5 PF val | C=10 PF disc | C=10 PF val | C=10 net $ disc/val | nonzero bid@60s disc/val |
|---|---|---|---|---|---|---|---|---|---|
| ETH-P90 | HOLD | base | 188/538 | 1.07 | 0.84 | 1.08 | 0.84 | 18.12/-98.35 | 96.8%/88.5% |
| ETH-P90 | HOLD | x1.2 | 188/538 | 1.06 | 0.83 | 1.06 | 0.83 | 14.95/-106.43 | 96.8%/88.5% |
| ETH-P90 | HOLD | +2c | 188/538 | 0.92 | 0.70 | 0.92 | 0.71 | -20.67/-210.20 | 96.8%/88.5% |
| ETH-P90 | X60 | base | 188/538 | 0.80 | 0.82 | 0.81 | 0.84 | -33.93/-75.98 | 96.8%/88.5% |
| ETH-P90 | X60 | x1.2 | 188/538 | 0.77 | 0.80 | 0.78 | 0.81 | -38.41/-87.60 | 96.8%/88.5% |
| ETH-P90 | X60 | +2c | 188/538 | 0.64 | 0.65 | 0.64 | 0.66 | -72.72/-187.83 | 96.8%/88.5% |
| ABS | HOLD | base | 0/0 | inf | inf | inf | inf | 0.00/0.00 | -/- |
| ABS | HOLD | x1.2 | 0/0 | inf | inf | inf | inf | 0.00/0.00 | -/- |
| ABS | HOLD | +2c | 0/0 | inf | inf | inf | inf | 0.00/0.00 | -/- |
| ABS | X60 | base | 0/0 | inf | inf | inf | inf | 0.00/0.00 | -/- |
| ABS | X60 | x1.2 | 0/0 | inf | inf | inf | inf | 0.00/0.00 | -/- |
| ABS | X60 | +2c | 0/0 | inf | inf | inf | inf | 0.00/0.00 | -/- |

Co-loss, C = 10 base. lost = net < 0. exp = n x pB x pE (rates within the same windows).

| pair | ETH threshold | exit | stage | n windows | BTC lost | ETH lost | both lost | exp both (indep.) | ratio | one lost | neither |
|---|---|---|---|---|---|---|---|---|---|---|---|
| both fired | ETH-P90 | HOLD | disc | 15 | 13 | 13 | 12 | 11.3 | 1.07 | 2 | 1 |
| both fired | ETH-P90 | HOLD | val | 109 | 80 | 86 | 69 | 63.1 | 1.09 | 28 | 12 |
| both fired | ETH-P90 | X60 | disc | 15 | 10 | 11 | 9 | 7.3 | 1.23 | 3 | 3 |
| both fired | ETH-P90 | X60 | val | 109 | 76 | 76 | 60 | 53.0 | 1.13 | 32 | 17 |
| BTC only, ETH same side choice | ETH-P90 | HOLD | disc | 129 | 90 | 97 | 76 | 67.7 | 1.12 | 35 | 18 |
| BTC only, ETH same side choice | ETH-P90 | HOLD | val | 116 | 80 | 90 | 66 | 62.1 | 1.06 | 38 | 12 |
| BTC only, ETH same side choice | ETH-P90 | X60 | disc | 129 | 86 | 95 | 76 | 63.3 | 1.20 | 29 | 24 |
| BTC only, ETH same side choice | ETH-P90 | X60 | val | 116 | 79 | 89 | 71 | 60.6 | 1.17 | 26 | 19 |
| both fired | ABS | HOLD | disc | 0 | | | | | | | |
| both fired | ABS | HOLD | val | 0 | | | | | | | |
| both fired | ABS | X60 | disc | 0 | | | | | | | |
| both fired | ABS | X60 | val | 0 | | | | | | | |
| BTC only, ETH same side choice | ABS | HOLD | disc | 144 | 103 | 110 | 88 | 78.7 | 1.12 | 37 | 19 |
| BTC only, ETH same side choice | ABS | HOLD | val | 225 | 160 | 176 | 135 | 125.2 | 1.08 | 66 | 24 |
| BTC only, ETH same side choice | ABS | X60 | disc | 144 | 96 | 106 | 85 | 70.7 | 1.20 | 32 | 27 |
| BTC only, ETH same side choice | ABS | X60 | val | 225 | 155 | 165 | 131 | 113.7 | 1.15 | 58 | 36 |

## Read

- **ABS (86,300) never fires on Ethereum**: n 0 in both stages. Ethereum's 3 minute open interest change never got that large (its discovery 90th percentile is 8,799).
- **ETH-P90 (doi > 8,799)**: hold PF 1.08 in discovery and 0.84 in validation. Selling at 60 s: 0.81 and 0.84. Validation loses $98 held and $76 sold at 60 s (C = 10). C = 5 is the same within 0.01. Firing rose from 188 to 538 between stages: open interest grew, so a fixed threshold from discovery fires about three times as often later.
- Nonzero bid at 60 s: 96.8% in discovery, 88.5% in validation.
- **Co-loss with Bitcoin**: when both fired, both lost 1.07 to 1.23 times as often as independence predicts (validation hold: 69 seen against 63.1 expected, in 109 windows). On the BTC-only windows, Ethereum's cheap side lost with Bitcoin 1.06 to 1.20 times independence. Mind the ceiling: cheap side loss rates are about 70% to 80%, so the ratio cannot go above about 1.3 to 1.4 even if the losses were perfectly matched. Judged against that ceiling, the losses are moderately correlated. The registered prediction (at least 1.3) was not met in any cell.
- Only 15 discovery windows had both firing (doi above Ethereum's P90 was rarer before September), so that row is thin.

## Verdicts (registered kill rule)

- ETH-P90, HOLD and X60, C = 5 and 10: **FALSIFIED** (validation PF 0.84 at base; at or under 1.0 at fees x1.2 and at +2c).
- ABS on Ethereum: **NOT_ENOUGH_DATA** (no entries).
- Co-loss cells carry no verdict (registered).

Prediction check: ABS n was under 100 (it was 0), as predicted. ETH-P90 hold validation PF was 0.84, below the predicted 1.0 to 1.6. The co-loss ratio was 1.06 to 1.23, below the predicted 1.3.

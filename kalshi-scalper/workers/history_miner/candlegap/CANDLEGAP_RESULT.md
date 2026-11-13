# CANDLEGAP result (History Miner, Nov 13, 2026): what a missing one-minute candle means on KXCS2GAME

Zero-try measurement. Frozen script `candlegap.py` (sha256 a7178688...24bd, Auditor B CLEAN on 76f233ff), run once on `wheelbook/2026-11-12/2031/` and the pull `CANDLEGAP_CS2/2026-11-13T0150Z_43347766241` (1 request, HTTP 200, 548,794 bytes, not truncated). Counts only: no result read, no price analysed. Raw output: `CANDLEGAP_RESULT_OUTPUT.json`. [research]

36 tickers, all 36 with candles; 7,436 counted market-minutes; **2,312 before the market's own close** (the headline), 5,124 after it (markets still polled after closing, the recorder fault fixed by PR 860).

## The five counts, before close (2,312 market-minutes)
| | "book changed" = any of the top 5 levels changed (as designed) | secondary: the touch (best YES bid or best NO bid) moved |
|---|---|---|
| 1. candle present, book changed | 1,286 | 872 |
| 2. candle present, book unchanged | 3 | 417 |
| 3. candle missing, book unchanged, two-sided quote standing | 446 | 767 |
| 4. candle missing, book unchanged, empty or one-sided | 239 | 256 |
| 5. candle missing although the book changed | 338 | **0** |

Candle against the recorder's last book of the minute (present candles, before close): 1,289 present, 1,151 with a bid and ask close, bid within 1c 1,130, ask within 1c 1,114, **both within 1c 1,102 (95.7%)**.

After close (5,124): 5,085 missing with an empty or one-sided book, 37 present, 2 missing with a change.

## What it supports
**On these CS2 match markets, a missing one-minute candle means the touch did not move in that minute: in 1,023 of 1,023 missing market-minutes before close the best bid and best ask were unchanged (0 exceptions); in 767 of them (75%) a two-sided quote was standing and in 256 (25%) the book was empty or one-sided.** So "carry the last quote forward" is right on the touch, but in a quarter of missing minutes there is nothing two-sided to carry. A present candle does not mean the touch moved (417 of 1,289 present candles had an unchanged touch; candles also appear for changes below the touch or trades). When present, the candle's close matches the book within 1c in 95.7% of minutes.

## Limits
One series (CS2 only, by rule (h)), one evening (3.5 h), 36 markets. "Polled every cycle" is inferred from the tier (the poll log of this run does not name tickers). Book rows are written only on change, so "unchanged" is inferred from no row. 138 present candles carried no bid or ask close and are not in the match count. Whether other series (e-soccer, Dota, tennis) behave the same is not measured here.

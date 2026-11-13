# NHLOT price measurement: the reader as it stands, Nov 13, 2026, 05:38Z

A hindsight price measurement, zero tries. No NHL candle has been pulled or read. As built it cannot produce a candidate (second amendment, point 4); its pull is at the back of the queue.

| File | sha256 |
|---|---|
| `nhlot/measure_prices.py` | `7d3b67310ba1e05653b0f725451abf55f106e475f6e1d3ba0c7f5a8266918e31` |
| `IDEA_DESK_B_WAVE3.md` (card 17 and its four dated NHLOT amendments) | `3d03e5a57a0528f08a522acbc9077ad787d7273d36e803cd0bcd3ebab9cf1820` |
| `nhlot/fixture_outputs/make_fixtures_MADE_UP_DATA.py` | `d7c4a0a928c3380d6d99b7419ed709d674a13fa31a7d4b488e97fc11deb3d475` |

Dead hashes of the reader: ff3e4811 (46 candle minutes, a folder walk), d325d328 (took a bid of 0.00 and an ask of 1.00 as sides).

**Audit:** Auditor B CLEAN on 7d3b6731 (the diff against the third amendment, then the one-place change for the fourth).

**Second build:** the History Miner, from the card's text only (`claude/history-miner`, final at 6a162f3d, `nhlot2.py` 649f8aad). It printed before comparing each time. The two builds print the same on all 14 made-up cases: every count, the median, quartiles and lowest ask, the cut counts, the detection minutes, the first-five-minutes count, both shares, the cross-check and the verdict; the two refusal cases refuse in both. The second build found the 46 against 45 minute window (which moved a registered share on one case, so the code moved to the text) and Auditor B found the empty-side reading; both are in the card as dated amendments.

**Before any figure is read:** the candle pull, then Auditor B's structure check on the landed run. Inputs for the 14 cases: `nhlot/fixture_inputs_MADE_UP_DATA/`; my printed lines: `nhlot/fixture_outputs/`.

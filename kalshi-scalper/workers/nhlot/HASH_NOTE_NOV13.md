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

## Held-out line added to the card (Nov 13, 2026, 07:07Z)

On the Head of R&D's order of 06:53Z, card 17 in `IDEA_DESK_B_WAVE3.md` gained one dated held-out line (text only; no rule, figure or reading changed). The file's sha256 is now 7d17795221691d66e4ac95ec572a8a2bb0ede2b9eb0aa7bbe68b876deca77d80 (it was 3d03e5a57a0528f08a522acbc9077ad787d7273d36e803cd0bcd3ebab9cf1820). The reader `nhlot/measure_prices.py` is unchanged at 7d3b67310ba1e05653b0f725451abf55f106e475f6e1d3ba0c7f5a8266918e31. The shared guard `deskb_guard.py` is now 14f969bc8983bff2a0696b3dcab745d748119de28fc4c5692370933cad0b1df9. W-CAT-SPORTS1 is released, so the sample stays the 150 games of `games.json`.

**07:10Z:** a registry cross-check paragraph was added under the held-out line (text only). The card file's sha256 is now efdecec293971b91c7f8e24e86c0a8af786cafe11d23f73517db136ad2d248d0. The shared guard's docstring was reworded on Auditor B's gate (code unchanged); its sha256 is now a199f946cca9da8e0a3c56f0524109629b420ef91b20e77d54fa3b6b6b0f9dcd. The reader is unchanged.

**07:11Z:** one dated line added to the card: FAMSPORTS and USWEEP2 reservations released by the Head of R&D (`RND_QUEUE.md` on `rnd-queue` at 0f7bfccb). Text only. The card file's sha256 is now 58cfad6d20cda230f0c3dd4f23eb2795d9564aa06fb313d859017aed4b141328. The Head released NHLOT_CANDLES for dispatch on commit 815e142e.

## The candle run landed and was read ONCE by the audited reader (Nov 13, 2026, 08:08Z). PROVISIONAL, ONE BUILD.

Run `pull/NHLOT_CANDLES/2026-11-13T0802Z_43390050891/` (86 answers, 1,988 tickers, 90,000 candles; the job on main byte-equal to the committed one, sha256 a019a029d1c94f0e79f794ca424b987352aa7de49cc2d72a529b6ca6e406d8d9). Auditor B's structure check PASSED before the run was opened (08:07Z). Then one command: `measure_prices.py` (7d3b6731, audited) on the run with `games.json` (2b403841). Its 15 printed lines are in `nhlot/real_read/desk_b_printed_lines_2026-11-13T0802Z.txt`, sha256 d78f2fd765779e8ccee33491818a874d30e00f0951adf0806b22f555dbc46a56.

**These figures are provisional, one build.** No verdict is recorded on the card until the History Miner's independent build (`nhlot2.py`, from the card's text only) prints the same figures on the same run, printing before comparing (rule 16b). What my build printed, in short: 150 games, all with moneyline candles; 34 detections (22.7%); the cheaper side's ask at the detection minute, median 0.49, quartiles 0.47 to 0.50, lowest 0.42; at 0.43 or lower one minute after the detection, 12% (the registered line); the reader's verdict line reads CARD CLOSED (the market already prices overtime as close to even). It is a price measurement in a hindsight window: no bet, no outcome, no try spent.

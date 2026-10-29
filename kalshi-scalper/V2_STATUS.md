# Strategy Research V2, status (newest first; times US Central)

## Now running / Next / Waiting on

- **Now running:** LADL1 download resumed from the old chat's partial files (4 shards, Bitcoin and Ethereum hourly); CONF2 ladder download for Aug 15 to Sep 25 (public, no key).
- **Next:** LADL1 run once when its shards finish and merge; CONF2 window A read once when its download finishes (window C, from Oct 27, read once later when it holds 30 kept closes).
- **Waiting on:** LOCK2 forward read (11 of 25 recorded hourly closes); RECORD1 (132 of 300 qualifying trades, 8 of 10 dates); MM1 (about 48 of 300 gold windows, about Nov 7); dated reads REV1 Nov 5, Nov 12 batch, FLIP1 Nov 14, GAS1-F Nov 22, ABSORB-F Dec 1 (scheduled tasks fire into this session); SPREAD1 (PR #611, owner).

## Entries

**2026-10-29 11:35 AM, CONF2 registered (owner approved).** CONF1's ladder filter on Bitcoin L1 entries at top-of-hour closes, with the 15 minute market's own strike. Window A (Aug to Sep 25) is new data; window B (Sep 26 to Oct 26) was seen by CONF1, reported but not a pass window; window C (from Oct 27) is a frozen forward holdout. Prediction: A kept PF under 1.5, FALSIFIED. N tried about 438,672.

**2026-10-29 11:20 AM, self-guide check, no new test (round 1 of 10 toward NO_CANDIDATE_LEFT).** Candidates checked against the ledger, none new: gold's first window after the daily COMEX break (S14 and O39, 11 trades, NOT_ENOUGH_DATA); Dogecoin and XRP following Bitcoin within a window (GEN2, LAG2, SCALP1); the previous window's outcome carrying into the next (S06); Ethereum coincident-close locks in history (same structure as LOCK2H, which was rare and unconfirmable; the recorder's LOCK2 covers Ethereum). One lead needs the owner: CONF2, CONF1's ladder filter (holdout PF 1.79 on 116 closes) on the full L1 history, which is L1 research. Not registered without the owner's yes.

**2026-10-29 11:00 AM, LOCK2H, NOT_ENOUGH_DATA.** Locks between the Bitcoin 15 minute contract and the hourly ladder at top-of-hour closes, in history (704 closes, Sep 26 to Oct 26, minute-close quotes). Locks of 1c or more after fees at 10 contracts in 4 of 704 closes (5 minutes, largest 16.8c, median best pair -4.4c), all at a ladder strike within $10 of the 15 minute strike, mostly in the last 2 minutes of fast moves where the two books' quotes are seconds apart. Not confirmable without simultaneous quotes and sizes: the forward LOCK2 read on the recorder is the test. N tried about 438,671.

**2026-10-29 10:45 AM, GOLDFV1, FALSIFIED (4 of 4 tries).** Gold 15 minute markets against the public 1 minute COMEX gold future (Yahoo GC=F; Pyth's history now needs a key). PF at 1 contract, discovery / validation (holdout not read, everything failed before it): S10 standalone 1.55 / 0.69 (n 118 / 127); S6 standalone 0.88 / 1.11; L1 gold at 10 min kept when the model agrees 1.52 / 0.76; at 6 min 1.04 / 2.64. Independent re-implementation: 0.95 / 0.70, 0.91 / 0.80, 0.77 / 1.79, 1.00 / 3.71. Plain reading: Kalshi gold already prices the latest minute of COMEX; a staler future price only adds losing trades. N tried about 438,670.

**2026-10-29 10:30 AM, takeover.** V2 took over new research. Restored the Oct 20 and Oct 29 data archives from `research-data` (checksums match; the Oct 29 `ladders.sqlite` was empty, the Oct 20 copy kept). Live record from the report endpoint since Oct 7: 821 settled, PF 1.02, net +$3.37 (gold PF 1.65 on 196, Bitcoin 0.72, XRP 0.41).

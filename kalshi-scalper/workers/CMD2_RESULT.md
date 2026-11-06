# CMD2 result (2026-11-06): NOT_ENOUGH_DATA (B1 daily break, B2 weekend; development only)

Registration `workers/CMD2_REGISTRATION.md`; code and print `workers/cmd/cmd.py`, `cmd_output.txt`. Times ET (CT one hour earlier).

**Verdict word: NOT_ENOUGH_DATA.** B1 needs 40 events on 15 break dates, B2 20 weekends.
**B1 (Mon 11-02 break, 17:00 to 18:00 ET).** Only one scoreable break exists in development (the Tue 11-03 break exits at 18:15 ET inside held-out session 11-04; Fri 10-30 is the weekend). Perp drift 17:00 to 17:59 ET: gold +4.6 bp, silver +4.1, copper -0.2 (none trigger at 10 bp), US 500 -13.3 and Tech 100 -26.7 (trigger), WTI no quote at one anchor. The two triggered trades (fade the drift, exit 18:15 ET): gross after spread +4.76 bp, net at 12 bp -19.2, at 5 bp -5.2, hit 1 of 2. n = 2 on one date.
**B2 (weekend 10-30 17:00 ET to 11-01 17:59 ET).** Only gold and silver have perp quotes at both anchors (copper, WTI, US 500 and Tech 100 have no valid quote on Sunday 17:59 ET: those perps appear not to quote while the cash market is shut). Gold drifted +28.3 bp and silver +29.2 bp over the weekend; fading it to 18:30 ET: gross after spread -57.1 bp, hit 0 of 2, net at 12 bp -81.1. The reopen confirmed the drift (information, n = 2 on one weekend, not a finding). Prediction (fewer than 6 events, net negative about -20 to -30) hit on count, missed on size.
**Enough dates:** B1 15 break dates about **2026-12-04**; B2 20 weekends **2027-03-12** (plus the held-out third about 2027-05-21).
N +2 as registered. No lead.

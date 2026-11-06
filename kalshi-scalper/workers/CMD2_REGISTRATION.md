# CMD2 registration: CME daily break and weekend gap (2026-11-06, before any score)

Shared rules: `workers/CMD_COMMON.md`. 2 tries (N +2). Times US Central in results (ET in the rules: the break is 17:00 to 18:00 ET).

**Mechanism.** While the futures are shut the perp trades on its own (thin, no reference). Its drift is part information, part noise; the reopen reconciles it. Counterparty: perp takers who chase a drift with no reference price. Honest alternative: the drift is information and the reopen confirms it.

**B1 daily break (Mon to Thu, 17:00 to 18:00 ET).** Mb = ln(perp mid at 17:59 ET / perp mid at 17:00 ET). If |Mb| at least 10 bp: enter against the drift at the 17:59 ET quote (short if Mb positive, long if negative, at bid or ask), exit at the 18:15 ET quote. Only the six pairs in the shared universe. Futures are not used for the entry (they do not exist then); the futures reopen move versus the perp is information only. Break dates in development: Mon 11-02 and Tue 11-03 (the Fri 10-30 break is the weekend); Wed and Thu 11-04, 11-05 held out.

**B2 weekend (Fri 17:00 ET to Sun 18:00 ET).** W = ln(perp mid at Sun 17:59 ET / perp mid at Fri 17:00 ET). If |W| at least 15 bp: enter against at the Sun 17:59 ET quote, exit at 18:30 ET. Development has one weekend (2026-10-30 close to 2026-11-01 reopen; the DST change on 11-01 is handled in UTC: reopen 23:00Z).

**Prediction.** B1 at most 2 break dates, fewer than 5 events; B2 one weekend, fewer than 6 events (one per pair). Direction if it ever scores: net negative at 12 bp (about -20 to -30 bp).

**Verdict bar:** B1 needs 40 events on 15 break dates and both halves 5 dates; B2 needs 20 weekends. Else NOT_ENOUGH_DATA. **Dates it becomes enough:** B1 15 dev break dates (Mon to Thu from 11-02: 11-02,03,04,05,09,10,11,12,16,17,18,19,23,24,25 minus held out third) about **2026-12-04** read (same as CMD1) at the earliest; B2 20 development weekends from 2026-10-30 is **2027-03-12**, plus the held-out third about 2027-05-21.

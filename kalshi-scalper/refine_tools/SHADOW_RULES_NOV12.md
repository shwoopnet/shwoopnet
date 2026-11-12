# Shadow list: forward records with no money (written Nov 12, 2026, BEFORE any recording starts)

Owner order: put the nearest leads on the shadow list as forward records. A shadow is a paper rule written first, recorded forward, scored once at its read point. No bar is lowered. A shadow result never places an order; a live probe needs the owner's own popup and the probe cap ($200 lifetime, small size, kill and return rules).

## S1. Approval and generic-ballot NO side (W-NO-ARM1 lead)
- Rule: for each event in KXTRUMPAPPROVE, KXVHGCB, KXAPRPOTUS, KXAPRPOTUSD, KXGENERICBALLOTVOTEHUB, KXVOTEHUBTRUMPUPDOWN, at the last hourly snapshot at least 24 h and at most 27 h before close, pick the market whose YES mid is nearest 0.5; if NO price paid (1 minus YES bid) is in [0.75, 0.90] (arm A) or [0.10, 0.25] (arm B), record one paper buy of 3 contracts of NO at that price plus 1c slip, fee 0.07*p*(1-p), hold to settlement. One per event per arm.
- Logging that makes it real: the politics forward recorder (PR 784, branch pol-data) already lists KXTRUMPAPPROVE, KXVHGCB, KXAPRPOTUS among its 26 series; it must keep hourly bid and ask for every market of those series and the settlement result. Missing: KXAPRPOTUSD, KXGENERICBALLOTVOTEHUB, KXVOTEHUBTRUMPUPDOWN (check the recorder list).
- Kill: after 20 paper fills net under -$15 at 3 contracts, or 5 losses in a row: stop recording that arm. Return: 14 day cool-off, shadow PF 1.3 or better at +1c on at least 30 fills and the owner's approval.
- Read point: the first read when each arm has 30 paper fills; live-probe graduation needs PF 1.3 or better over 100 paper fills in 2 of 3 windows (owner rule).

## S2. Sports SPREAD cell (W-SPREAD-CELL1 lead): CLOSED Nov 12, 2026: the registered read FAILED on both lines (n 172 and 173, PF about 0.6 at +1c); NOT STARTED, no forward shadow, the daily spread logging job is never built.
- Rule: for each event in the six spread series (KXMLBSPREAD, KXNBASPREAD, KXNCAAFSPREAD, KXNCAAMBSPREAD, KXNFLSPREAD, KXNHLSPREAD), at the first hourly snapshot more than 24 h before close, pick the market whose YES mid is nearest 0.5; if its YES ask is in [0.05, 0.15], record one paper buy of 1 YES at ask plus 1c, fee 0.07*p*(1-p), hold to settlement.
- Logging: a daily list of open spread markets closing in 24 to 48 h with bid and ask at the list time (about 6 to 12 reads a day through kalshi-pull), and the result from the settled list. Without this logging there is no shadow.
- Kill: after 100 shadow fills with PF below 1.2 at +1c, or lower 90 percent bound below 0 at 100: drop. Return: none (a new registration is needed).
- Read point: 100 shadow fills in the cell.

## S3. Combo house side (V2 owns combos; PR 793 recorder)
- I cannot fix a precise rule: I have not read the recorder's fields. Skeleton to be completed by V2 or the Head of R&D BEFORE recording: for each recorded combo market of 2 to 5 legs at its first quote, record one paper buy of 1 NO at the ask plus 1c, hold to settlement; one per combo; fee unrounded 0.07*p*(1-p).
- Kill: net under -$40 over the first paper fills of $2 per probe (the parlay rulebook stop), or n of 100 with PF under 1.2. Return: owner approval.
- Logging: the PR 793 recorder must store first quote time, bid, ask, number of legs and result; stop rule read Nov 26.

# Year-one edge plan (draft for the owner, Nov 17, 2026)

Goal, in the owner's words: a full-time paying job, not a hobby, that keeps earning when Claude is offline. Nothing here goes live without the owner's own popup. No live account figures are in this file.

## 1. Data others don't keep
- Recording now: the 15 minute book every 5 s for 11 non-crypto series (nc15, to Dec 31); the perps list every 60 s with the top-5 book (book-order fix PR 1013), 1 minute candles and funding for every perp, the Sunday reopen every 10 s, the 30 s open and close windows; Kalshi combos, politics, in-game sports, weather (NWS), and OKX Bitcoin liquidations.
- Gaps to close first: (a) the perps trade tape (who took, which side); (b) 5 s perps books all day, not only market hours (the fast-lane PR); (c) settlement marks at 17:00Z every day; (d) the 15 minute crypto books after R6 ends (Nov 20). Each one is public, keyless and a small recorder.
- Why: a backtest can only find what was recorded. History we keep from today is the one thing a later competitor cannot buy.

## 2. New markets to be early in (perps)
- Stock perps, gold and index perps are weeks old, thin, and priced by few makers. That is where edges are widest and shortest-lived.
- First test per lane: stock perps: relative strength and pairs (lanes 1 and 6, code done, running this week). Gold and metals: the gold move filter (V4 shadow). Indices: the funding print, already tested as SPFUND1 (development to Dec 18). Crypto perps: FUNDX2, extreme funding (runs this week).
- Honest status: 0 perps rules have passed so far (PERPSCALP2, PERPSLANE4 and POOL1 all failed). The cost of a round trip (about 24 bp, 12 bp a side as taker) is the main enemy.

## 3. The testing machine, and how it stays honest
- Every test is written down before any data is read: rule, cut dates, kill rule, expected trades a day.
- Two independent builds must agree to 1e-9. An auditor checks the code. A held-out window is read once.
- The multiple-testing count (about 7.5 million rules tried so far) is carried forward, so luck is priced in.
- Only forward shadow trading (logged, no money) can make a CANDIDATE: 100 forward trades, PF 1.3 or better at 1c, both halves. Then the owner's popup.

## 4. Cost levers
- Maker (resting) entries pay 5 bp, not 12 bp, a side on perps, and earn the spread on Kalshi. But tests so far show adverse selection: the fills we get are the bad ones. A maker pass is flagged, not counted.
- Size to the book: never more than 30% of the size resting at the touch (the bot already logs depth).
- Fee drag: on a cheap 15 minute contract the fee and spread can exceed the whole edge (the cheap-flip read, Nov 17). Rank every idea by net dollars a week after cost, not by win rate.

## 5. Earning with no Claude running
- Already automatic (Firebase): every order, the exit watch, the loss stops, the kill latches, sizing, phone alerts, the nightly report endpoint, the balance snapshots, every recorder (GitHub Actions).
- Still needs a person or Claude: merges and deploys (`bash functions/deploy-latest.sh`); re-arming a strategy after a kill (a reviewed edit, by design); topping up a shard; reading the nightly report (today a Claude routine); research.
- Can be automated next: a plain email or phone summary of the nightly report with no Claude in the loop; a deploy check that runs the tests on every merge; an alert when a recorder stops.

## 6. Runbook the owner can use alone (to write next, one page each)
1. Start, Pause, Flatten from the Bot page. 2. What each phone alert means and what to do. 3. A kill latch fired: what it means, how to re-arm. 4. A shard is low: top it up under Transfers. 5. Deploy after a merge: `bash functions/deploy-latest.sh`, type only `on` at the switch prompt. 6. The bot looks stuck: the three checks (Running pill, exit-watch heartbeat, nightly report). 7. Turn a recorder off: delete its workflow.

## Honest income math
- A full-time income of $4,000 a month needs, at a steady 3% a month, about $133,000 working; at 2% a month, $200,000; at 5% a month, $80,000. Returns of 2% to 5% a month, held for years, would be exceptional for anyone; nothing here has proven any rate yet.
- Capacity matters as much as rate: the 15 minute Kalshi books hold a few hundred to about a thousand contracts near the touch, so most Kalshi edges cap out far below $100,000. Perps scale further.
- Deposits of $250 a month alone take about 33 years to reach $100,000. With 2% a month on top, about 9 years; with 3%, about 7. So in year one the realistic aim is a proven edge with a known capacity, not an income. Income follows a proven edge plus deposits, over years.

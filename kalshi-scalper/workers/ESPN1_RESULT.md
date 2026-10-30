# ESPN1 result: ESPN in-play win probability against Kalshi game-winner asks

Registration: `ESPN1_REGISTRATION.md` (pushed before any Kalshi price was read). Check: `ESPN1_CHECK.md`. Code: `kalshi-scalper/src/scalper/espn1.py`. Data (ignored by git): `data/espn1.sqlite`.

## ESPN lag (measured live, fixed before scoring, 2026-10-30 01:00 UTC)
ESPN's probability rows carry no publication time, only the play's `wallclock`. A poller read the live summaries of 5 games on 2026-10-29/30 (2 college football from 23:30Z, NBA from 00:00Z, NFL from 00:15Z), cycling about every 15 to 25 s, and logged when each new row first appeared (rows already present at a game's first poll excluded).

| League | Rows | Median lag | p90 | Max |
|---|---|---|---|---|
| College football | 156 | 48 s | 64 s | 261 s |
| NBA | 252 | 40 s | 85 s | 368 s |
| NFL | 42 | 51 s | 62 s | 64 s |
| All | 450 | **45 s** | **77 s** | 368 s (p99 259 s) |

The lag includes up to one poll cycle, so it overstates the true lag by roughly 10 s. p90 77 s is above 60 s, so by the registered formula **D = 180 s** (p90 rounded up to the next minute, plus 60 s): the entry candle must end at least 180 s after the play's wallclock. Revisions: 6 of 445 rows (1.3%) differ by more than 0.01 between the value seen live and the stored value read at 01:00Z, so the stored history is close to what a live reader saw.

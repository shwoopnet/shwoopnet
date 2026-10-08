# Roadmap

Last refreshed: 2026-10-08 (US Central). Now / Next / Later, with the gate for each item. A date is a read date, not a promise.

## Now (this week)

| Item | Gate or check |
|---|---|
| Confirm the bot keeps trading past 8:55 PM CT (the old session end) | Bot card still shows Running and orders keep appearing after 8:55 PM |
| First weekly size review | 2026-10-15: expect the cap to step from 3 to 4 at about $344 balance |
| Look at the new page live, including a phone | Account card, Running menu, market charts, gold line, Layout arrows |
| Phone layout: the line and bar charts shrink to unreadable | Charts legible at 390 px wide |
| Confirm fee rounding on the BALANCE side | Compare the balance before and after one single-contract order |
| Merge this docs refresh and the Pages exclusion | Pages build green, site still loads |

## Next (to about 2026-10-23)

| Item | Gate or check |
|---|---|
| Forward checks F0 to F9 read | At least 300 entries on at least 5 days; z, halves and fees x1.2 as registered |
| Size ladder step 1 decision | The owner overrode the evidence gates on 2026-10-08. After the forward read, either keep or step back to 1 contract per the README |
| Use the recorder's order-book data | Book depth imbalance and locked books, pre-registered before running |
| 10 second stop test | Needs several days of recorder data |
| Remove the unused single-order path (`kalshiLiveTrade`, `kalshiLiveArm`) | Owner decision, then a deploy. Shrinks the code that can move money |
| shwoop-server fixes (separate repo, owner decides) | Timing-safe secret compare; fail closed when the bar time is missing instead of a random order id; `firebase-admin` bump; fixed error text |

## Later

- A real gold price feed that matches Kalshi's Pyth source (keyless Pyth price endpoints now need a key). The current line is gold-api.com and can sit a dollar off.
- Weekday spread measurement for crypto (the one reading was a Sunday afternoon).
- Auto-resume after a loss stop with a cooldown (today it stays off until restarted, on purpose).
- App Check on the callables, a content security policy (needs a nonce build step), and requiring a verified email for the admin check.
- Weekly digest of the bot's real results against the forward-check thresholds.

## Done recently (2026-10-07 and 2026-10-08)

- 24/7 bot, weekly size scaling, reinvest and skim, Flatten all, deposit recorder, and one Pause/Resume control in place of separate Stop and Halt buttons.
- Performance tracker, readable open positions, simplified Kalshi page, market charts, Central time.
- Exit, band, entry-side and fee studies; sizing replay; the cheap-side test, the favorite scalps and two more L1 filters (all falsified); a bug in the time-exit logic found and corrected.
- Security review fixes; hand-run mutation check of the money code.
- Pages build fixed and the repo's non-app files excluded from the public site.

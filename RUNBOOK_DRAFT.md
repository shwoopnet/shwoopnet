# Owner's runbook (DRAFT for Main to review, Nov 17, 2026)

Plain words, one page each. Written from CLAUDE.md and the code in `functions/`; nothing here is invented, and there are no live figures. Where a fact is not written down anywhere, the page says so. You never need a terminal for pages 1, 2, 3, 4 and 6. Only deploying (page 5) and a recorder switch (page 7) touch the repo.

---

## 1. Start, Pause and Flatten

All three live in one place: the **Account card** on the Bot page. Tap the **Running** pill (it says "Not running" when the bot is off). A small menu opens under it.

- **Start bot.** The page asks first ("Start it?"). The server then places REAL orders by itself, around the clock, until you pause it or a stop ends it. Starting also lifts a pause. The sizes are decided in code, not by anything you type here.
- **Pause bot.** The bot stops placing new orders. Anything already open is still watched and sold by the exit watch (the 25c early sell) or settles on its own.
- **Flatten all.** Asks twice. It pauses the bot, then SELLS every open position in the account, the bot's and any you opened by hand, at whatever the book pays right now. It takes the loss at the bid. Use it only when you want out of everything.

If a stop (the 12% loss stop) ends the bot, it stays off until you Start it again. That is on purpose.

If the Account card shows "Order switch OFF", the server will not send buys even if the bot is running. That means the server's live switch is not `on` (see page 5).

---

## 2. What each phone alert means

Alerts come from the owner's own server (Web Push). Turn them on in Settings, Notifications. On an iPhone they work only from the Home Screen app. They only report; they place and change nothing.

- **Won / Lost / Closed <market>** (with an amount): a trade finished. You get one for every close.
- **Sold <market> early**: the 25c exit sold it before the end. You will see the result in the alert.
- **A buy never alerts.** If you got used to buy alerts, they were removed on purpose.
- **"Check the bot: ..."**: something needs a look. The wording says what. Open the Bot page and read the red banner and the "Needs a look" block under Bot status.
  - "an exit ..." with a market name: an exit order's answer was lost or refused. Look at that order on the Bot page.
  - "a market cannot trade, low money on exchange N": a shard is short. Go to page 4.
  - "the exit watch is silent": a position is open and nothing has checked it for the 25c exit. Go to page 6.
- **"Bot stopped: <reason>"**: the bot ended itself (for example the loss stop). It stays off until you restart it on the Bot page. Read the reason first, then decide.
- Your own Stop and Flatten taps are silent.

---

## 3. A kill latch fired

There are two kinds of automatic stop, and they are not the same thing.

- **The loss stop (12%).** It ends the whole session and the page says so ("Bot stopped"). You can Start again when you choose.
- **A strategy kill rule or latch** (for example gold's kill latch, or a probe's streak or drawdown stop). Only that strategy stops placing NEW orders. The other strategies keep running, and the exit watch still sells anything open.

What you should know:
- A latch has **no automatic restart.** That is by design: only a reviewed code change puts a strategy back.
- On gold, a kill shows in the bell as a critical item ("gold kill"). Softer warnings ("gold alert") are only warnings.
- Do not restart the bot to "clear" a latch. Starting the bot does not re-arm a strategy.
- What to do: ask Main in the chat. A re-arm needs a dated entry from you and a reviewed pull request. For OICORE the written rule is: after its drawdown stop or any kill, never re-armed automatically.

---

## 4. A shard is low

Kalshi keeps each market group's money on its own exchange shard, and an order needs money on its own shard. If one runs short, that market silently stops trading.

- The signal: a phone alert "Check the bot: a market cannot trade, low money on exchange N", with how much is there and how much an order needs. It repeats at most once every six hours.
- The fix: in Kalshi, go to **Transfers** and move money to that exchange. **The bot and the page cannot move money.** Money on another exchange does not help.
- Which shard a market uses is on the order itself (`exchangeIndex`). Do not trust older notes about which market sits where.
- A second-slot strategy on a short shard only logs a skip; it does not send this phone alert (it is only in the nightly report's skips).

---

## 5. Deploy after a merge

A merge to `main` changes the site at once (the Pages page). The **bot** only changes when you deploy the functions.

1. Open a terminal in the project folder.
2. Run: `bash functions/deploy-latest.sh`
3. It updates to the latest `main`, runs every test, works out which of the three deploy scripts are needed (push first, then sizing, then report), shows the plan, and **asks before running anything**. Say yes only if the plan looks right.
4. If it asks for `KALSHI_LIVE_ENABLED`, type **only the word `on`**. Typing the whole line once left the order switch off after a "successful" deploy.
5. If the plan mentions `firestore.rules` changed, it prints one extra command to run (`npx firebase-tools deploy --only firestore:rules --project shwoopnet`).

If a test fails or a deploy errors, stop and show Main the last lines. The wrapper only records the last deployed commit after every selected deploy finished, so a failed one is offered again next time.

---

## 6. The bot looks stuck

Three checks, in this order:

1. **The Running pill and the red banner** (Bot page). Pill says Running? Is there a banner for "bot stopped by itself", "an order that needs checking" or "no check for several minutes"? The banner stays as long as the problem is true.
2. **The exit-watch heartbeat.** The exit watch writes a heartbeat every minute. If a position is open and it has been silent more than 4 minutes you get the phone alert "the exit watch is silent". If you get that alert, treat it as real: open the page, look at the open position, and if in doubt Pause or Flatten (page 1).
3. **The nightly report.** It lists the day's orders and, under `deploys`, which version each function is running. If the bot placed nothing for a long time, the report's `skips` section says why each market was skipped (a fixed code, such as a short shard or a stop).

Common innocent causes: a paused market (several markets are paused in code on purpose), the quiet weekend for gold and forex, or "Order switch OFF" (page 5, step 4). If all three checks are clean and you still see nothing, tell Main in the chat.

---

## 7. Turn a recorder off

The research recorders are GitHub Actions workflows in `.github/workflows/` (for example the quote, book, perps, politics, signals and in-game recorders). They only read public data and place nothing.

- **To stop one:** delete its workflow file in `.github/workflows/` on GitHub (open the file, trash icon, commit through a pull request, merge). Stopping is that simple, and the data already collected stays on its data branch.
- Each recorder also **stops by itself on a date written in its script and workflow**; nothing needs to be done at that date.
- Do not delete the website's or the bot's own workflows. If unsure which file is a recorder, ask Main before deleting.
- Turning one off does not touch the bot, the page or any trade.

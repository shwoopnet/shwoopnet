"use strict";
// One tick of the server-side Kalshi PAPER bot. It talks to two things it is handed:
//   store: where positions, events and status live (Firestore in production, a plain
//          object in tests)
//   api:   Kalshi's public read endpoints
// so every rule below can be tested without Firebase or a network.
//
// PAPER ONLY. Nothing here can place a real order: the api has no order method.
//
// Rules, each with a test that fails if it is broken:
// - Entry is idempotent. The store creates a position by a key derived from the
//   market, atomically, so two overlapping runs (Cloud Scheduler can double fire,
//   a redeploy briefly overlaps) cannot enter the same market twice.
// - Fail closed. An unreadable or partly unreadable feed, an inactive exchange, a
//   page halt, no bankroll, or a spent loss limit means NO new entry. Exits and
//   settlement carry on, because freezing an open position is the dangerous act.
// - A close is applied only if the position is still open when it is written.

const lib = require("./kalshiBotLib");

async function runTick({ store, api, now }) {
  const prev = (await store.getStatus()) || {};
  const control = (await store.getControl()) || {};
  const halted = control.halt === true;

  // ---- read the market ----
  let exchangeActive = false;
  let quotesOk = true;
  let error = null;
  const quotes = [];
  try {
    const st = await api.exchangeStatus();
    exchangeActive = Boolean(st.trading_active !== undefined ? st.trading_active : st.exchange_active);
    for (const series of lib.SERIES) {
      for (const m of await api.markets(series)) quotes.push({ series, m });
    }
  } catch (e) {
    quotesOk = false;
    error = String((e && e.message) || e).slice(0, 160);
  }
  const byTicker = new Map(quotes.map((q) => [q.m.ticker, q.m]));

  // ---- manage what is already open (always, even when halted) ----
  const open = await store.listOpen();
  const closedNow = new Set();
  for (const pos of open) {
    const m = byTicker.get(pos.ticker);
    if (!m || !lib.exitDue(pos, m, now)) continue;
    const pnl = lib.exitPnl(pos);
    const did = await store.closePosition(pos.id, {
      exit: lib.TARGET, exitFee: lib.takerFee(lib.TARGET, pos.contracts), exitAt: now, settledAt: now, pnl,
    });
    if (did) {
      closedNow.add(pos.id);
      await store.addEvent({ ts: now, kind: "exit", detail: `${pos.id} sold ${pos.contracts} at ${lib.TARGET.toFixed(2)}, net ${pnl.toFixed(2)}` });
    }
  }
  for (const pos of open) {
    if (closedNow.has(pos.id) || now < pos.closeTs + lib.SETTLE_GRACE_MS) continue;
    let result;
    try {
      result = (await api.market(pos.ticker)).result;
    } catch (e) {
      continue; // not readable now: ask again next tick
    }
    if (result !== "yes" && result !== "no") continue; // not final yet
    const pnl = lib.settlePnl(pos, result);
    const did = await store.closePosition(pos.id, {
      exit: result === pos.side ? 1 : 0, exitAt: now, settledAt: now, pnl,
    });
    if (did) await store.addEvent({ ts: now, kind: "settle", detail: `${pos.id} ${result}, net ${pnl.toFixed(2)}` });
  }

  // ---- limits, from realised profit and loss today ----
  const closed = await store.listClosedSince(lib.localDayStart(now));
  const tier = lib.tierState(closed, lib.BANKROLL, now);

  // ---- new entries ----
  let block = null;
  if (!quotesOk) block = "prices unreadable";
  else if (halted) block = "halted from the page";
  else if (!exchangeActive) block = "exchange not trading";
  else if (tier.mode === "done") block = "done for the day";
  else if (tier.mode === "break") block = "on a break";
  let entered = 0;
  if (!block) {
    for (const e of lib.planEntries(quotes, now, tier.cap)) {
      const made = await store.createPosition(lib.positionId(e.ticker), {
        ticker: e.ticker, series: e.series, side: e.side, band: e.band, contracts: e.contracts,
        entry: e.price, entryFee: e.fee, entryAt: now, closeTs: e.closeTs, status: "open",
        mode: "paper", exit: null, exitFee: null, exitAt: null, pnl: null, settledAt: null,
      });
      if (made) {
        entered++;
        await store.addEvent({ ts: now, kind: "entry", detail: `${lib.positionId(e.ticker)} bought ${e.contracts} ${e.side} at ${e.price.toFixed(2)} (band ${e.band})` });
      }
    }
  }
  // Say why entries are blocked once per change, not once per minute.
  if ((block || "") !== (prev.lastBlock || "") && block) {
    await store.addEvent({ ts: now, kind: "block", detail: block });
  }
  if (error && error !== prev.lastError) {
    await store.addEvent({ ts: now, kind: "error", detail: "quotes: " + error });
  }

  // ---- heartbeat: written every tick, even when prices were unreadable ----
  const stillOpen = (await store.listOpen()).length;
  await store.setStatus({
    lastTickMs: now, ok: quotesOk, error, mode: "paper", bankroll: lib.BANKROLL, exchangeActive,
    halted, tierMode: tier.mode, pnlToday: tier.pnlToday, perTradeCap: tier.perTradeCap,
    softLimit: tier.softLimit, hardLimit: tier.hardLimit, breakUntil: tier.breakUntil,
    openCount: stillOpen, lastBlock: block || "", lastError: error || "",
    // What the limits were computed from, so the page can show it. If this ever disagrees
    // with the trades listed, the limits are not seeing what the owner sees.
    closedCounted: tier.counted, dayStart: lib.localDayStart(now),
  });
  // ok and prevTier feed the outside watchdog (kalshiAlertLib), which lives outside this process.
  return { entered, block, tier: tier.mode, ok: quotesOk, prevTier: prev.tierMode || null };
}

module.exports = { runTick };

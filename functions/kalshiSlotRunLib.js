"use strict";
// The second slot, PHASE B step B1: the engine that would place and close slot orders (docs/SECOND_SLOT_WIRING.md section 2).
// Wired by functions/index.js only behind SLOT_ON (step B3). While SLOT_ENABLED is false or SLOT_STRATEGIES is empty every entry point below returns before it makes a single call.
//
// All I/O is injected, exactly in the style of runL1Tick and runExitWatch: a `store`, `fetchFn`, the key passed in, `now` passed in. This file has no Firestore, no environment, no clock
// of its own (the only Date.now is the signing timestamp, which liveRequest takes when no nowMs is given, as for L1's own orders), no randomness and no secret.
//
// What it will not do, by construction (each is a test in test/kalshiSlotRunGates.test.js):
//   - send anything unless a registered, valid strategy exists (slotActive), the server switch is on and the exchange is trading;
//   - create an order without the direction lock and the order document being written in ONE transaction first (no document, no send), so two instances cannot both send;
//   - ever buy the opposite side of a market the books, the lock or the account already show on the other side (a hedge);
//   - send a buy that is not immediate-or-cancel, outside the strategy's price band and time window, or above the module's caps;
//   - retry anything whose answer was lost: that ends the session and latches the strategy off;
//   - sell more than its own unsold contracts, more than the account holds beyond the other engines' contracts, or anything that could OPEN the opposite position;
//   - sell without holding the per-market close lease first (taken BEFORE the position is read), or keep that lease afterwards.

const bot = require("./kalshiSignalLib");
const slotLib = require("./kalshiSlotLib");
const live = require("./kalshiLiveLib");

const EXIT_LOOKBACK_MS = 25 * 60 * 1000;
const EXIT_SLIPPAGE = 0.15;       // how far past the bid the immediate-or-cancel sell may go; it still fills at the book's own prices (the same figure the L1 watch uses)
const EXIT_MAX_TRIES = 3;
// For a slot order whose strategy is no longer registered: a fixed stop and always out before the close. No target (the price can never reach it).
const FALLBACK_EXIT = Object.freeze({ stopBid: 0.25, targetBid: 1.01, mustExitLeftSec: 60 });
const MAX_STALE_MS = 20 * 1000;   // the longest an entry may wait between the start of the minute and the order being recorded
const BALANCE_MARGIN = 0.5;       // dollars that must remain on the shard after the order (the same figure L1 uses)
const r4 = (x) => Math.round(x * 10000) / 10000;
const num = (v) => (v === undefined || v === null || v === "" ? NaN : Number(v));
const isAmbiguous = (status) => status === 0 || status === 429 || status >= 500;
const short = (b) => (typeof b === "string" ? b : JSON.stringify(b)).slice(0, 160);
const OPEN_SHORT = ["active", "open"];

// Open interest rise to the signal candle (the one ending 180 s before the close) over the 3 minutes before it. The research read it from the candle that ENDS at those two instants; a
// missing candle, a missing value or a non-finite number is null, never a guess.
function oiRiseFromCandles(candles, closeSec) {
  if (!Array.isArray(candles) || !Number.isFinite(closeSec)) return null;
  const at = (sec) => { const c = candles.find((x) => x && Number(x.end_period_ts) === sec); const v = c ? num(c.open_interest_fp) : NaN; return Number.isFinite(v) ? v : null; };
  const a = at(closeSec - 180), b = at(closeSec - 360);
  return a === null || b === null ? null : Math.round((a - b) * 100) / 100;
}

const unsoldOf = slotLib.slotUnsoldOf;     // one definition, in the library L1's exit watch hooks also use

function makeRunners(flags) {
  const strategiesNow = () => (flags === undefined ? slotLib.activeSlotStrategies() : slotLib._testOnly.activeSlotStrategiesWith(flags));
  // Watching is wider than entering: once a slot order has ever existed, exits, settling and the hedge net keep running with entries switched off or a strategy removed.
  const watching = () => (flags === undefined ? slotLib.slotWatch() : flags.everUsed === true || strategiesNow().length > 0);
  const registryNow = () => (flags === undefined ? slotLib.SLOT_STRATEGIES : (Array.isArray(flags.registry) ? flags.registry : [])).filter((x) => slotLib.validateSlotStrategy(x).ok);
  const check = (input) => (flags === undefined ? slotLib.slotOrderCheck(input) : slotLib._testOnly.slotOrderCheckWith(flags, input));

  // ---------------------------------------------------------------------------------------------------------------------------------
  // Entries
  // ---------------------------------------------------------------------------------------------------------------------------------
  // args: { session, now, enabled, active, store, keyId, pem, fetchFn, quotes, setSession, logEvent, shared, l1Result, sessionNow }
  //   shared  the figures runL1Tick just worked out and handed over (so there is no second balance read): { sizeBase, balanceBody, risk: { worst }, floor, recentList, slotOrders, since }
  //   store   { halted(), hasUnresolved(), l1HasUnresolved(), killLatches(), allSlotOrders(), l1Recent(since), runSlotEntry({ ticker, side, decide, now }), updateSlotOrder(id, patch), killStrategy(id, info) }
  async function runSlotTick(args) {
    const strategies = strategiesNow();
    if (!strategies.length) return { skipped: "no slot strategy" };           // second line of defence for off-equivalence: not one call is made
    const { session, now, enabled, active, store, keyId, pem, fetchFn, quotes, setSession } = args;
    const log = async (kind, detail) => { if (args.logEvent) { try { await args.logEvent({ ts: now, kind, detail }); } catch (e) { /* the log is optional */ } } };
    if (!session || session.active !== true) return { skipped: "no session" };
    if (args.l1Result && args.l1Result.ended) return { skipped: "the session ended this minute" };
    if (enabled !== true) return { skipped: "switch off" };
    if (!active) return { skipped: "exchange inactive" };
    // Markets that are open and inside some strategy's entry window. Computed from the quotes already in hand: no call is made if none qualifies.
    const jobs = [];
    const early = [];
    for (const s of strategies) {
      // The entry window must open well before the exit floor: an order sent a few seconds late must still be sellable by the time rule. A strategy that does not leave that room never enters.
      if (s.exit.holdToSettle !== true && !(s.entry.leftMinSec - s.exit.mustExitLeftSec >= MAX_STALE_MS / 1000)) { early.push(s.id + ": its entry window ends too close to its exit floor, no entry"); continue; }
      for (const q of quotes || []) {
        if (!q || !q.m || !s.series.includes(q.series) || !OPEN_SHORT.includes(q.m.status)) continue;
        const left = (Date.parse(q.m.close_time) - now) / 1000;
        if (Number.isFinite(left) && left >= s.entry.leftMinSec && left <= s.entry.leftMaxSec) jobs.push({ s, ticker: q.m.ticker, series: q.series });
      }
    }
    if (!jobs.length) return { skipped: early.length ? early.join("; ") : "no market in a slot entry window" };

    const sh = args.shared;
    if (!sh || !Number.isFinite(sh.sizeBase) || !(sh.sizeBase > 0) || !sh.risk || !Number.isFinite(sh.risk.worst) || !Number.isFinite(sh.floor)) return { skipped: "no shared risk figures from the L1 tick" };
    // Ending the session must never be skipped because a write failed: each step is tried on its own.
    const end = async (why, detail) => { try { await setSession({ active: false, endedAt: now, endedBecause: why }); } catch (e) { /* the unresolved check ends it next minute */ } await log("session ended", detail); return { ended: why }; };
    const clock = typeof args.clock === "function" ? args.clock : () => now;

    // Preconditions, every one failing closed (a skip, never an order).
    let latches, slotOrders, l1Fresh;
    try {
      if (typeof args.sessionNow === "function") { const cur = await args.sessionNow(); if (!cur || cur.active !== true) return { skipped: "the session ended this minute" }; }
      if (await store.halted()) return { skipped: "halted" };
      if (await store.hasUnresolved(now)) return { skipped: "a slot order is unresolved" };
      if (await store.l1HasUnresolved()) return { skipped: "an L1 order is unresolved" };
      try { latches = await store.killLatches(); } catch (e) { latches = { unreadable: true }; }   // an unreadable latch document kills every strategy (killCheck)
      slotOrders = await store.allSlotOrders();
      const since = Number.isFinite(sh.since) ? sh.since : now - 24 * 3600 * 1000;
      l1Fresh = await store.l1Recent(since);
      if (!Array.isArray(slotOrders) || !Array.isArray(l1Fresh)) return { skipped: "orders unreadable" };
    } catch (e) { return { skipped: "the slot's preconditions could not be read" }; }

    const results = [];
    const committed = {};                          // dollars this tick has already committed on each shard
    const sinceMs = Number.isFinite(sh.since) ? sh.since : now - 24 * 3600 * 1000;
    const seenInShared = new Set((sh.recentList || []).map((t) => t.id || t.clientOrderId));
    for (const job of jobs) {
      const { s, ticker, series } = job;
      const latch = latches && !latches.unreadable && Object.prototype.hasOwnProperty.call(latches, s.id) ? latches[s.id] : (latches && latches.unreadable ? latches : null);
      const mk = await live.liveRequest({ fetchFn, method: "GET", path: "/markets/" + encodeURIComponent(ticker) });
      const m = mk.status === 200 && mk.body && mk.body.market;
      if (!m) { results.push(ticker + ": could not read the market (HTTP " + mk.status + ")"); continue; }
      const left = (Date.parse(m.close_time) - now) / 1000;
      if (!OPEN_SHORT.includes(m.status) || !(left >= s.entry.leftMinSec && left <= s.entry.leftMaxSec)) { results.push(ticker + ": not open in the entry window"); continue; }
      const bid = num(m.yes_bid_dollars), ask = num(m.yes_ask_dollars);
      if (!bot.validQuote(Number.isFinite(bid) ? bid : null, Number.isFinite(ask) ? ask : null)) { results.push(ticker + ": no two-sided quote"); continue; }
      // Which side, and the price of that side at the touch (cents).
      const yesPrice = Math.ceil(r4(ask) * 100 - 1e-9) / 100, noPrice = Math.round((1 - Math.floor(r4(bid) * 100 + 1e-9) / 100) * 100) / 100;
      const side = s.entry.sideRule === "favourite" ? (yesPrice >= noPrice ? "yes" : "no") : s.entry.sideRule === "cheap" ? (yesPrice < noPrice ? "yes" : "no") : s.entry.sideRule;
      const sidePrice = side === "yes" ? yesPrice : noPrice;
      const touch = side === "yes" ? yesPrice : Math.round((1 - noPrice) * 100) / 100;       // the YES price the order goes to, which is what Kalshi's body carries
      if (sidePrice < s.entry.priceMin - 1e-9 || sidePrice > s.entry.priceMax + 1e-9) { results.push(ticker + ": the " + side + " side is priced " + sidePrice.toFixed(2) + ", outside the band"); continue; }
      const depth = num(side === "yes" ? m.yes_ask_size_fp : m.yes_bid_size_fp);
      // The open interest condition (public candles, no key): open interest at the candle ending 180 s before the close minus the one ending 360 s before it. Any missing candle is no order.
      let oiRise = null;
      if (Object.prototype.hasOwnProperty.call(s.entry, "oiRiseMin")) {
        const closeSec = Math.round(Date.parse(m.close_time) / 1000);
        const cr = await live.liveRequest({ fetchFn, method: "GET", path: "/series/" + encodeURIComponent(series) + "/markets/" + encodeURIComponent(ticker) + "/candlesticks",
          params: { start_ts: String(closeSec - 480), end_ts: String(closeSec - 60), period_interval: "1" }, nowMs: now });
        oiRise = oiRiseFromCandles(cr.status === 200 && cr.body ? cr.body.candlesticks : null, closeSec);
        if (oiRise === null) { results.push(ticker + ": the open interest could not be read, nothing sent"); continue; }
        if (oiRise < s.entry.oiRiseMin) { results.push(ticker + ": open interest rose " + oiRise + ", under " + s.entry.oiRiseMin + ", no signal"); continue; }
      }
      // The position is read BEFORE the transaction and may be stale by the time it commits; the direction lock, not this read, is what closes that gap.
      const pos = await live.liveRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/positions", params: { ticker, limit: "20" }, nowMs: now });
      let position = NaN;
      if (pos.status === 200 && pos.body && Array.isArray(pos.body.market_positions)) {
        const row = pos.body.market_positions.find((x) => x.ticker === ticker);
        position = row ? num(row.position_fp !== undefined ? row.position_fp : row.position) : 0;
      }
      if (!Number.isFinite(position)) { results.push(ticker + ": the position could not be read, nothing sent"); continue; }
      // Lowest step not yet attempted on this market (slotOrderCheck refuses a step that is not allowed yet).
      const mine = slotOrders.filter((t) => t && t.slotId === s.id && t.ticker === ticker);
      let step = 1; while (mine.some((t) => t.step === step) && step <= s.scaleIn.maxSteps) step += 1;
      if (step > s.scaleIn.maxSteps) { results.push(ticker + ": every scale-in step was already used"); continue; }
      const shardKey = String(m.exchange_index);

      // The authoritative decision, made INSIDE the store's transaction on the lock and the order books as they are at commit time.
      const decide = (lockDoc, slotNow, l1Docs) => {
        // The window is judged on the clock at commit time, not at the start of the minute: the slow reads before this (balance, markets, candles, L1's own order) can take many seconds.
        const nowD = Number(clock());
        if (!Number.isFinite(nowD) || nowD - now > MAX_STALE_MS) return { allowed: false, reason: "too long since the minute began (" + Math.round((nowD - now) / 1000) + " s), nothing sent" };
        const leftD = (Date.parse(m.close_time) - nowD) / 1000;
        const l1Merged = new Map();
        for (const t of l1Fresh) l1Merged.set(t.id || t.clientOrderId, t);
        for (const t of l1Docs || []) l1Merged.set(t.id || t.clientOrderId, t);   // the transaction's own read of this ticker wins
        const l1All = [...l1Merged.values()];
        const c = check({ strategyId: s.id, ticker, side, limit: sidePrice, step, depthAtTouch: depth, slotOrders: slotNow, l1Orders: l1All, slotOrdersComplete: true,
          lockTxn: true, lock: lockDoc === undefined ? null : lockDoc, oiRise, position, sizingBase: sh.sizeBase, windowCapFraction: live.L1_WINDOW_CAP_FRACTION, killLatch: latch, secondsLeft: leftD, now });
        if (!c.allowed) return { allowed: false, reason: c.reasons.join("; ") };
        // The shared loss stop: the new order is treated as lost the moment it exists. L1's figure was read earlier this minute, so what has changed since is added: slot orders
        // that now exist (this tick's earlier ones) and L1 orders that were created after it was read, both counted as lost.
        const slotDelta = slotLib.slotRiskForBotRisk(slotNow, sinceMs).worst - slotLib.slotRiskForBotRisk(sh.slotOrders || [], sinceMs).worst;
        let newL1 = 0;
        for (const t of l1All) { if (!seenInShared.has(t.id || t.clientOrderId) && (num(t.fillCount) > 0 || ["filled", "sending", "unknown"].includes(String(t.status))) && !(t.settled === true)) newL1 += Math.max(0, num(t.maxCost) || 0); }
        const worstNow = sh.risk.worst + slotDelta - newL1;
        if (!(worstNow - c.cost > sh.floor + 1e-9)) return { allowed: false, reason: "the shared loss stop leaves no room for a $" + c.cost.toFixed(2) + " order" };
        // The shard must hold the money (L1's own check, with this minute's earlier L1 and slot orders taken off).
        const l1Shard = l1All.filter((t) => !seenInShared.has(t.id || t.clientOrderId) && String(t.exchangeIndex) === shardKey && t.settled !== true).reduce((a, t) => a + Math.max(0, num(t.maxCost) || 0), 0);
        const avail = live.availableFor(sh.balanceBody, m.exchange_index) - (committed[shardKey] || 0) - l1Shard;
        if (!Number.isFinite(avail)) return { allowed: false, reason: "the balance came back in a shape this code does not recognise" };
        if (avail < c.cost + BALANCE_MARGIN) return { allowed: false, reason: "only $" + avail.toFixed(2) + " on its shard" };
        const record = slotLib.slotOrderRecord({ strategyId: s.id, ticker, side, step, count: c.count, limit: touch, maxCost: Number(c.cost.toFixed(2)), ts: now });
        Object.assign(record, { accountId: live.DEFAULT_ACCOUNT_ID, series, price: sidePrice, exchangeIndex: m.exchange_index === undefined ? null : m.exchange_index, mode: "live", oiRise,
          seen: { bid: Number.isFinite(bid) ? bid : null, ask: Number.isFinite(ask) ? ask : null, bidSize: Number.isFinite(num(m.yes_bid_size_fp)) ? num(m.yes_bid_size_fp) : null, askSize: Number.isFinite(num(m.yes_ask_size_fp)) ? num(m.yes_ask_size_fp) : null } });
        return { allowed: true, record, lock: { side, by: "SLOT:" + s.id, ts: now } };
      };
      { const fresh = Number(clock()); if (!Number.isFinite(fresh) || fresh - now > MAX_STALE_MS) { results.push(ticker + ": too long since the minute began, nothing sent"); continue; } }
      // Flatten and Stop can land while this tick was reading (seconds, with timeouts). Read the halt again immediately before the order is recorded and sent.
      let halted;
      try { halted = await store.halted(); } catch (e) { halted = true; }
      if (halted) { results.push(ticker + ": the bot was halted while this minute ran, so nothing was sent"); continue; }
      let entry;
      try { entry = await store.runSlotEntry({ ticker, side, decide, now }); } catch (e) { results.push(ticker + ": the order could not be recorded, so nothing was sent"); continue; }
      if (!entry || entry.created !== true) { results.push(ticker + ": " + ((entry && entry.reason) || "not allowed")); continue; }
      const rec = entry.record, cid = rec.id;
      committed[shardKey] = (committed[shardKey] || 0) + rec.maxCost;
      slotOrders = slotOrders.concat([rec]);
      if (typeof args.onRecorded === "function") { try { args.onRecorded(rec); } catch (e) { /* observer only */ } }

      const body = live.liveOrderBody(ticker, touch, side, cid, m.exchange_index, rec.count);
      const res = await live.liveRequest({ fetchFn, keyId, pem, method: "POST", path: live.ORDERS_PATH, body });
      const d = res.body && typeof res.body === "object" ? res.body : {};
      if (res.status >= 200 && res.status < 300 && d.order_id) {
        const filledCount = Number(d.fill_count || 0);
        const patch = { status: filledCount > 0 ? "filled" : "no fill", orderId: d.order_id, fillCount: String(d.fill_count || "0"), remainingCount: String(d.remaining_count || "0"),
          averageFillPrice: d.average_fill_price || null, averageFeePaid: d.average_fee_paid || null, sentSide: body.side, sentPrice: body.price };
        await store.updateSlotOrder(cid, patch);
        Object.assign(rec, patch);
        await log("slot order", s.id + " " + side + " " + rec.count + " at " + (sidePrice * 100).toFixed(0) + "c on " + ticker + ": " + (filledCount > 0 ? "filled" : "no fill"));
        results.push(ticker + ": " + (filledCount > 0 ? "filled" : "no fill"));
        continue;
      }
      // Anything else ends the session and latches this strategy off. Nothing is ever retried. The latch and the session end come FIRST, each on its own; the order's status is written last, so a database
      // blip on that write can never leave the strategy entering and the session running after an order whose outcome nobody knows.
      const latchOff = async (reason) => { try { if (typeof store.killStrategy === "function") await store.killStrategy(s.id, { killedAt: now, reason }); } catch (e) { /* the session end below still stops L1 and the slot */ } };
      const writeLast = async (patch) => { try { await store.updateSlotOrder(cid, patch); } catch (e) { /* the order stays "sending", which the unresolved check catches */ } };
      if (res.status === 409) {
        const found = await findOrder({ fetchFn, keyId, pem, ticker, clientOrderId: cid });
        await latchOff("an order with id " + cid + " already existed");
        const out = await end("attempted", "Kalshi says a slot order with id " + cid + " already exists. Check the Kalshi account for it");
        await writeLast(found
          ? { status: Number(found.fill_count_fp || 0) > 0 ? "filled" : "no fill", orderId: found.order_id, fillCount: String(found.fill_count_fp || "0"), recovered: true, error409: true }
          : { status: "unknown", error: "HTTP 409 and the order could not be found: " + short(res.body) });
        return Object.assign(out, { results });
      }
      if (isAmbiguous(res.status)) {
        await latchOff("the answer for " + ticker + " was lost");
        const out = await end("attempted", "the answer for the slot order on " + ticker + " was lost (HTTP " + res.status + "). THE ORDER MAY OR MAY NOT EXIST. Check the Kalshi account (Portfolio, Orders) before starting again. Nothing was retried");
        await writeLast({ status: "unknown", error: "HTTP " + res.status + " " + short(res.body) });
        return Object.assign(out, { results });
      }
      await latchOff("Kalshi refused the order for " + ticker);
      const out = await end("attempted", "Kalshi refused the slot order for " + ticker + ": HTTP " + res.status + " " + short(res.body).slice(0, 80));
      await writeLast({ status: "error", error: "HTTP " + res.status + " " + short(res.body) });
      return Object.assign(out, { results });
    }
    return { ok: true, results };
  }

  // ---------------------------------------------------------------------------------------------------------------------------------
  // Exits
  // ---------------------------------------------------------------------------------------------------------------------------------
  // Exits cover EVERY unsettled filled slot order in the collection, whether or not entries are switched on and whether or not its strategy is still registered (turning the slot off must never
  // leave a live position without a stop). A registered strategy uses its own exit rules; an order whose strategy is gone gets FALLBACK_EXIT (a fixed stop, and always out before the close).
  // On top of both, a position that sits on the opposite side of another engine's unsold contracts in the same market is a HEDGE (the owner forbids it): the later slot order is sold at once and
  // its strategy latched off. This is the net under the direction lock for the deploy that first admits a strategy, when an old revision's L1 order could not read the lock.
  // args: { store, fetchFn, keyId, pem, now, enabled, setSession, logEvent }
  //   store  { slotRecentFilled(since), slotOrdersOnTicker(ticker), l1OrdersOnTicker(ticker), claimClose(ticker, who, now, ttl), releaseClose(ticker, who), claimSlotExit(id, tries, now),
  //            updateSlotOrder(id, patch), finishSlotOrder(id, patch, killEval), killStrategy(id, info) }
  async function runSlotExits(args) {
    if (!watching()) return { skipped: "no slot strategy", results: [] };    // not one call is made
    const registry = registryNow();
    const { store, fetchFn, keyId, pem, now, enabled, setSession } = args;
    const log = async (kind, detail) => { if (args.logEvent) { try { await args.logEvent({ ts: now, kind, detail }); } catch (e) { /* the log is optional */ } } };
    const selling = enabled === true;
    const results = [];
    let list;
    try {
      list = (await store.slotRecentFilled(now - EXIT_LOOKBACK_MS)).filter((t) => slotLib_isSlot(t) && t.settled !== true && Number(t.fillCount) > 0 && Number.isFinite(Number(t.maxCost)) && t.ticker
        && (t.side === "yes" || t.side === "no") && !["sold", "unknown", "sending", "skipped"].includes(t.exitStatus));
    } catch (e) { return { skipped: "slot orders unreadable", results }; }
    for (const t of list) {
      const s = registry.find((x) => x.id === t.slotId);
      const rules = s ? s.exit : FALLBACK_EXIT;
      const want = Number(t.count) > 0 ? Number(t.count) : 1, got = Math.min(Number(t.fillCount), want);
      const sold = Number(t.exitCount) > 0 ? Number(t.exitCount) : 0;
      const remaining = Math.floor(got - sold + 1e-9);
      if (remaining < 1) continue;
      const mk = await live.liveRequest({ fetchFn, method: "GET", path: "/markets/" + encodeURIComponent(t.ticker), nowMs: now });
      const m = mk.status === 200 && mk.body && mk.body.market;
      if (!m || !OPEN_SHORT.includes(m.status)) continue;
      const yb = num(m.yes_bid_dollars), ya = num(m.yes_ask_dollars);
      if (!bot.validQuote(Number.isFinite(yb) ? yb : null, Number.isFinite(ya) ? ya : null)) continue;
      const ourBid = t.side === "yes" ? r4(yb) : r4(1 - ya);
      if (!(ourBid > 0)) continue;
      const leftSec = (Date.parse(m.close_time) - now) / 1000;
      if (!Number.isFinite(leftSec) || leftSec <= 0) continue;       // closed: it settles on its own
      // What the other orders on this market still hold, by side. Unreadable means nothing is sold (and no hedge can be seen), the same fail-closed reading as before.
      let l1, sl;
      try {
        l1 = await store.l1OrdersOnTicker(t.ticker); sl = await store.slotOrdersOnTicker(t.ticker);
        if (!Array.isArray(l1) || !Array.isArray(sl)) throw new Error("unreadable");
      } catch (e) { results.push(t.ticker + ": the other orders could not be read, nothing sold"); continue; }
      const mine = (x) => x && (x.id || x.clientOrderId) === t.id;
      const sameSide = (x) => x && x.ticker === t.ticker && x.side === t.side;
      const others = l1.filter(sameSide).reduce((a, x) => a + unsoldOf(x), 0) + sl.filter((x) => sameSide(x) && !mine(x)).reduce((a, x) => a + unsoldOf(x), 0);
      // A hedge: unsold contracts of ANOTHER order on the opposite side. L1's can never be sold here, so the slot order always yields; between two slot orders the later one yields.
      const opposite = (x) => x && x.ticker === t.ticker && (x.side === "yes" || x.side === "no") && x.side !== t.side && unsoldOf(x) > 0;
      const later = (x) => !(Number(x.ts) > Number(t.ts)) && !(Number(x.ts) === Number(t.ts) && String(x.id || x.clientOrderId) > String(t.id));
      const hedge = l1.some(opposite) || sl.some((x) => opposite(x) && later(x));
      const why = hedge ? "hedge" : rules.holdToSettle === true ? null : ourBid <= rules.stopBid + 1e-9 ? "stop" : ourBid >= rules.targetBid - 1e-9 ? "target" : leftSec <= rules.mustExitLeftSec + 1e-9 ? "time" : null;
      if (!why) continue;
      const latchOff = async (reason) => { try { if (s && typeof store.killStrategy === "function") await store.killStrategy(s.id, { killedAt: now, reason }); } catch (e) { /* the session end below still stops it */ } };
      if (!selling) {
        if (t.exitShadow) continue;     // logged once per order
        await store.updateSlotOrder(t.id, { exitShadow: { at: now, bid: ourBid, left: leftSec, why, wouldSell: remaining } });
        await log("slot exit (log only)", t.ticker + ": " + why + " exit due at a bid of " + (ourBid * 100).toFixed(0) + "c; it would have sold " + remaining + " contracts. Nothing was sent, because the server's order switch is off.");
        results.push(t.ticker + ": logged");
        continue;
      }
      const tries = Number(t.exitTries) > 0 ? Number(t.exitTries) : 0;
      if (tries >= EXIT_MAX_TRIES) continue;
      if (hedge) { await latchOff("a hedge was found in " + t.ticker + " (this order is on the opposite side of another order's contracts)"); await log("slot hedge", t.ticker + ": this slot order sits against another order's contracts, which must never happen. Selling it and switching its strategy off"); }
      // The per-market close lease FIRST (shared with Flatten and the L1 watch, which take it with other holders), the position only after holding it.
      if (!(await live.claimClose(store, t.ticker, "slot", now))) { results.push(t.ticker + ": another closer holds the market (or the claim could not be made), nothing sold"); continue; }
      const release = async () => { try { if (typeof store.releaseClose === "function") await store.releaseClose(t.ticker, "slot"); } catch (e) { /* the lease lapses by itself after 90 seconds */ } };
      try {
        const pos = await live.liveRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/positions", params: { ticker: t.ticker, limit: "20" }, nowMs: now });
        let held = NaN;
        if (pos.status === 200 && pos.body && Array.isArray(pos.body.market_positions)) {
          const row = pos.body.market_positions.find((x) => x.ticker === t.ticker);
          held = row ? num(row.position_fp !== undefined ? row.position_fp : row.position) : 0;
        }
        if (!Number.isFinite(held)) { results.push(t.ticker + ": the position could not be read, nothing sold"); continue; }
        const count = slotLib.slotSellCount({ order: t, position: held, haveClaim: true, othersUnsold: others });
        if (count < 1) {
          // "Skipped" is permanent, so it is written only when the position read is clean and shows NONE of this side. A count of zero that comes from the other engines' contracts (two reads that are
          // not atomic) is a passing state: it is retried on the next pass.
          const holdsSide = t.side === "yes" ? Math.max(0, held) : Math.max(0, -held);
          if (holdsSide >= 1) { results.push(t.ticker + ": nothing of its own to sell yet (the others hold the rest), will look again"); continue; }
          await store.updateSlotOrder(t.id, { exitStatus: "skipped", exitNote: "the account holds no " + t.side.toUpperCase() + " position in this market (already closed?)" });
          results.push(t.ticker + ": nothing of its own to sell"); continue;
        }
        if (!(await store.claimSlotExit(t.id, tries, now))) continue;     // another instance has it
        const limit = t.side === "yes" ? Math.max(0.01, r4(ourBid - EXIT_SLIPPAGE)) : Math.min(0.99, r4(ya + EXIT_SLIPPAGE));
        let cid, body;
        try {
          cid = slotLib.slotExitClientOrderId(t.id, tries);
          body = live.exitBody(t.ticker, t.side, count, Math.round(limit * 100) / 100, cid, m.exchange_index);
        } catch (e) { await store.updateSlotOrder(t.id, { exitStatus: "error", exitNote: "the exit could not be built: " + String(e.message).slice(0, 80), exitTries: tries + 1 }); results.push(t.ticker + ": exit not built"); continue; }
        const res = await live.liveRequest({ fetchFn, keyId, pem, method: "POST", path: live.ORDERS_PATH, body });
        const d = res.body && typeof res.body === "object" ? res.body : {};
        if (res.status >= 200 && res.status < 300 && d.order_id) {
          const filled = Number(d.fill_count || 0);
          let p = Number(d.average_fill_price);
          if (!Number.isFinite(p) || p <= 0 || p >= 1) p = t.side === "yes" ? ourBid : r4(1 - ourBid);
          const soldPrice = t.side === "yes" ? p : r4(1 - p);
          const fee = filled > 0 ? bot.takerFee(soldPrice, filled) : 0;
          const exitCount = sold + filled, exitProceeds = Number(((Number(t.exitProceeds) || 0) + filled * soldPrice - fee).toFixed(4));
          const patch = { exitStatus: filled >= count - 1e-9 ? "sold" : (filled > 0 ? "partly sold" : "no fill"), exitCount, exitProceeds, exitAvg: filled > 0 ? soldPrice : (t.exitAvg || null), exitAt: now, exitBid: ourBid, exitWhy: why, exitOrderId: d.order_id };
          const complete = exitCount >= Math.floor(got + 1e-9) - 1e-9 && filled > 0;
          if (complete) Object.assign(patch, slotLib.slotSettledFields({ ...t, exitCount, exitProceeds }, "exit"), { settledAt: now });
          if (complete && typeof store.finishSlotOrder === "function") {
            // The order's last patch and the kill latch go in ONE transaction, so a strategy that just tripped a kill rule cannot send another order in between.
            await store.finishSlotOrder(t.id, patch, (orders) => {
              if (!s) return null;
              const k = slotLib.slotKillStatus(orders.filter((x) => x && x.slotId === s.id), s);
              return k.killed && k.latch ? { strategyId: s.id, killedAt: now, reason: k.reason } : null;
            });
          } else await store.updateSlotOrder(t.id, patch);
          await log("slot exit", t.ticker + ": " + why + " at a bid of " + (ourBid * 100).toFixed(0) + "c, " + patch.exitStatus + " " + filled + " of " + count);
          results.push(t.ticker + ": " + patch.exitStatus);
          continue;
        }
        // A lost or refused answer: switch the strategy off and end the session FIRST, each on its own, and only then write the order's status. A database blip on the status write must never leave
        // the strategy entering and the session running after a sell whose outcome nobody knows.
        const safe = async (fn) => { try { await fn(); } catch (e) { /* every step is attempted whatever the others do */ } };
        if (res.status === 409) {
          await latchOff("an exit order with id " + cid + " already existed");
          await safe(() => store.updateSlotOrder(t.id, { exitStatus: "unknown", exitNote: "HTTP 409: an order with id " + cid + " already exists" }));
          await log("slot exit", t.ticker + ": Kalshi says the exit order " + cid + " already exists. Check the Kalshi account for it");
          results.push(t.ticker + ": id already used");
          continue;
        }
        if (isAmbiguous(res.status)) {
          await latchOff("the answer for the exit on " + t.ticker + " was lost");
          if (setSession) await safe(() => setSession({ active: false, endedAt: now, endedBecause: "attempted" }));
          await safe(() => store.updateSlotOrder(t.id, { exitStatus: "unknown", exitNote: "HTTP " + res.status + " " + short(res.body) }));
          await log("session ended", "the answer for the slot exit sell on " + t.ticker + " was lost (HTTP " + res.status + "). THE SELL MAY OR MAY NOT HAVE HAPPENED. Check the Kalshi account (Portfolio, Orders) before starting again. Nothing was retried");
          return { ended: true, results };
        }
        await store.updateSlotOrder(t.id, { exitStatus: "error", exitNote: "HTTP " + res.status + " " + short(res.body), exitTries: tries + 1 });
        await log("slot exit", t.ticker + ": Kalshi refused the exit sell: HTTP " + res.status + " " + short(res.body).slice(0, 80));
        results.push(t.ticker + ": refused");
      } finally { await release(); }
    }
    return { ok: true, results };
  }

  // Idle means: there is no filled, unsettled slot order to watch (or the slot has never been used). Anything unreadable counts as NOT idle (running the watch for nothing only costs compute).
  async function slotExitIdle({ store, now }) {
    if (!watching()) return true;
    try {
      const recent = await store.slotRecentFilled(now - EXIT_LOOKBACK_MS);
      return !recent.some((t) => slotLib_isSlot(t) && t.settled !== true && Number(t.fillCount) > 0);
    } catch (e) { return false; }
  }

  // ---------------------------------------------------------------------------------------------------------------------------------
  // Settle sweep
  // ---------------------------------------------------------------------------------------------------------------------------------
  // The slot's twin of settleOpenOrders: a slot order held to the close has no exit, so without this it would stay "open" (counted as lost in the shared stop) for ever. Reads at most 12
  // public markets, places nothing. It runs whenever the slot has ever been used, so orders left behind by a removed strategy still settle. args: { store, fetchFn, keyId, pem, now }; store: { allSlotOrders(), l1Recent(since), updateSlotOrder(id, patch), finishSlotOrder(id, patch, killEval) }
  // The hand-close check ignores EVERY other order's ids (L1's and the slot's), so another engine's fill is never read as a sale by hand of this order.
  async function runSlotSettle(args) {
    if (!watching()) return { skipped: "no slot strategy", settled: 0 };      // not one call is made
    const registry = registryNow();
    const { store, fetchFn, keyId, pem, now } = args;
    let open, ignore;
    try {
      const all = await store.allSlotOrders();
      const l1 = await store.l1Recent(now - 3 * 24 * 3600 * 1000);
      if (!Array.isArray(all) || !Array.isArray(l1)) return { skipped: "orders unreadable", settled: 0 };
      ignore = slotLib.slotIgnoreSet([...all, ...l1]);
      open = all.filter((t) => slotLib_isSlot(t) && t.settled !== true && Number(t.fillCount) > 0 && Number.isFinite(Number(t.maxCost)) && t.ticker && (t.side === "yes" || t.side === "no"));
    } catch (e) { return { skipped: "orders unreadable", settled: 0 }; }
    let settled = 0;
    for (const t of open.slice(0, 12)) {
      const mk = await live.liveRequest({ fetchFn, method: "GET", path: "/markets/" + encodeURIComponent(t.ticker), nowMs: now });
      const r = mk.status === 200 && mk.body && mk.body.market ? mk.body.market.result : null;
      if (r !== "yes" && r !== "no") continue;
      const h = keyId && pem ? await live.closedByHand({ fetchFn, keyId, pem, t, nowMs: now, ignoreOrderIds: ignore }) : { unknown: true };   // no key, no settling: a loss stays counted
      if (h.unknown) continue;
      const patch = h.hand ? Object.assign({ settled: true, result: "hand", settledAt: now }, Number.isFinite(h.sold) ? { handSold: h.sold } : {}) : Object.assign(slotLib.slotSettledFields(t, r), { settledAt: now });
      const s = registry.find((x) => x.id === t.slotId);
      if (s && typeof store.finishSlotOrder === "function") {
        await store.finishSlotOrder(t.id, patch, (orders) => {
          const k = slotLib.slotKillStatus(orders.filter((x) => x && x.slotId === s.id), s);
          return k.killed && k.latch ? { strategyId: s.id, killedAt: now, reason: k.reason } : null;
        });
      } else await store.updateSlotOrder(t.id, patch);
      settled += 1;
    }
    return { ok: true, settled };
  }

  return { runSlotTick, runSlotExits, slotExitIdle, runSlotSettle };
}

const slotLib_isSlot = (t) => !!t && t.strategy === "SLOT" && typeof t.slotId === "string";

async function findOrder({ fetchFn, keyId, pem, ticker, clientOrderId }) {
  const r = await live.liveRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/orders", params: { ticker, limit: "50" } });
  const list = r.status === 200 && r.body && Array.isArray(r.body.orders) ? r.body.orders : [];
  return list.find((o) => o.client_order_id === clientOrderId) || null;
}

// The production runners take no flags, so nothing a caller passes can turn the switch on or add a strategy. The factory is exposed for tests only.
const prod = makeRunners(undefined);
module.exports = {
  runSlotTick: prod.runSlotTick, runSlotExits: prod.runSlotExits, slotExitIdle: prod.slotExitIdle, runSlotSettle: prod.runSlotSettle, unsoldOf, EXIT_LOOKBACK_MS,
  _testOnly: Object.freeze({ makeRunners, oiRiseFromCandles }),
};

"use strict";
// A SIMULATED run of L1 on other 15 minute crypto series (ETH and SOL), started by the owner on Oct 9, 2026 after the history test (README, Results: E1 and E2) found the
// rule thin but not negative there. The point is to watch it on live prices for a day or three before any real order exists.
//
// It follows the live bot's own path as closely as a keyless read can, and stops one step short of the order:
//   1. the same market list, the same 6 minute window (330 s to 400 s left), the same fresh read of the single market, the same l1Pick (88c to 97c, either side),
//   2. the same stake: l1Count with the live session's size cap and profit add-on and the account's cash, so a trade here is the size a Bitcoin or gold trade is today,
//   3. the order is replaced by a SECOND read of the market a moment later (ARRIVAL_MS, about the time a real order takes to arrive), and the fill is judged against
//      that book the way an immediate-or-cancel order at the touch would be: it fills only if the price is still inside the limit, and only up to the size resting
//      at the touch (the real bot fills about 56% of its signals because the price moves before the order arrives, so a sim that always filled would flatter it),
//   4. settlement is the same sweep the live orders use (kalshiLiveLib.settleOpenOrders), read from the public market result.
//
// Bitcoin and gold are simulated the same way, flagged `calibration`, ONLY so the sim's fill can be compared with the real bot's on the same markets (the page's fidelity line).
//
// KEYLESS by construction: this file has no signing, no key, no /portfolio call and no POST. Its scheduled function (index.js) is declared with no secrets. The only
// things it can write are its own documents (kalshiSimOrders, kalshiSimControl).

const bot = require("./kalshiSignalLib");
const live = require("./kalshiLiveLib");

const SIM_SERIES = ["KXETH15M", "KXSOL15M"];
const CALIBRATION_SERIES = ["KXBTC15M", "KXGOLD15M"];
const ALL_SERIES = SIM_SERIES.concat(CALIBRATION_SERIES);
const ARRIVAL_MS = 500;

const num = (v) => { const x = parseFloat(v); return Number.isFinite(x) ? x : NaN; };
const r4 = (x) => Math.round(x * 10000) / 10000;

// The fill an immediate-or-cancel buy at the pick's limit would get from this book. Pure.
//   YES: fills at the yes ask while it is at or under the limit, up to the size resting there.
//   NO:  a NO buy is a YES bid hit: the NO price is 1 minus the yes bid, the limit is pick.worst, the size is the yes bid's size.
// Missing quote or size, a crossed book, or a price that moved past the limit is no fill, never a guess.
function simFill(pick, count, m) {
  const bid = num(m && m.yes_bid_dollars), ask = num(m && m.yes_ask_dollars);
  if (!bot.validQuote(Number.isFinite(bid) ? bid : null, Number.isFinite(ask) ? ask : null)) return { fillCount: 0, reason: "no valid quote when the order arrived" };
  const yes = pick.side === "yes";
  const price = yes ? r4(ask) : r4(1 - bid);
  const limit = yes ? pick.limit : pick.worst;
  const size = num(yes ? m.yes_ask_size_fp : m.yes_bid_size_fp);
  if (price > limit + 1e-9) return { fillCount: 0, reason: "the price moved to " + (price * 100).toFixed(1) + "c, past the " + (limit * 100).toFixed(0) + "c limit" };
  if (!Number.isFinite(size) || size < 1) return { fillCount: 0, reason: "no size resting at the touch" };
  const fillCount = Math.min(count, Math.floor(size));
  return { fillCount, price, reason: fillCount < count ? "only " + fillCount + " of " + count + " resting at the touch" : "filled" };
}

function bookSeen(m) {
  const n = (v) => { const x = num(v); return Number.isFinite(x) ? x : null; };
  return { bid: n(m.yes_bid_dollars), ask: n(m.yes_ask_dollars), bidSize: n(m.yes_bid_size_fp), askSize: n(m.yes_ask_size_fp), at: new Date().toISOString() };
}

// One minute of the simulation. state = kalshiSimControl/state; session = the LIVE session document (only its size fields are read);
// cash = the account's total (the live bot sizes on the same figure); store = kalshiSimOrders. Never throws for a single bad market.
async function runSimTick(args) {
  const { state, session, cash, now, quotes, active, store, readMarket, sleep, setState } = args;
  if (!state || state.active !== true) return { skipped: "off" };
  const note = async (text) => { try { await setState({ lastTickAt: now, lastNote: String(text).slice(0, 300) }); } catch (e) { /* the note is optional */ } };
  if (!active) { await note("The exchange is not trading right now."); return { skipped: "exchange inactive" }; }
  const [lo, hi] = live.L1_WINDOW_MS;
  const candidates = (quotes || []).filter((q) => ALL_SERIES.includes(q.series) && ["active", "open"].includes(q.m.status)
    && Date.parse(q.m.close_time) - now >= lo && Date.parse(q.m.close_time) - now <= hi);
  const results = [];
  const sizing = Boolean(session && session.sizing === true);
  const sizeCap = session && Number.isFinite(session.sizeCap) ? session.sizeCap : 1;
  const sizeAddon = session && Number.isFinite(session.sizeAddon) ? session.sizeAddon : 0;
  const cashNow = Number.isFinite(cash) ? cash : (session && Number.isFinite(session.sizeBase) ? session.sizeBase : NaN);
  for (const c of candidates) {
    const ticker = c.m.ticker;
    try {
      const m = await readMarket(ticker);
      if (!m || !m.ticker) { results.push(ticker + ": could not read the market"); continue; }
      const left = Date.parse(m.close_time) - now;
      if (!["active", "open"].includes(m.status) || left < lo || left > hi) { results.push(ticker + ": not open in the 6 minute window"); continue; }
      const pick = live.l1Pick(m);
      if (!pick) { results.push(ticker + ": no side is priced 88c to 97c"); continue; }
      const cost1 = pick.worst + bot.takerFee(pick.worst, 1);
      if (cost1 > live.LIVE_CAP + 1e-9) { results.push(ticker + ": would cost $" + cost1.toFixed(2) + ", above the cap"); continue; }
      const count = sizing && Number.isFinite(cashNow) ? live.l1Count(cashNow, cost1, sizeCap, sizeAddon) : 1;
      const addonUsed = sizing && Number.isFinite(cashNow) ? Math.max(0, count - live.l1Count(cashNow, cost1, sizeCap, 0)) : 0;
      const cost = pick.worst * count + bot.takerFee(pick.worst, count);
      const cid = "SIM-" + ticker;
      const record = {
        ticker, series: c.series, side: pick.side, band: "88-97c", strategy: "L1", count, addon: addonUsed, addonCost: Number((cost * addonUsed / count).toFixed(4)), price: pick.price, limit: pick.limit,
        exchangeIndex: m.exchange_index === undefined ? null : m.exchange_index, clientOrderId: cid, status: "sending", ts: now, mode: "sim",
        calibration: CALIBRATION_SERIES.includes(c.series), maxCost: Number(cost.toFixed(2)), seen: bookSeen(m),
      };
      if (!(await store.createTest(cid, record))) { results.push(ticker + ": already simulated"); continue; }   // one simulated order per market, even across two instances
      await sleep(ARRIVAL_MS);
      let m2 = null;
      try { m2 = await readMarket(ticker); } catch (e) { m2 = null; }
      if (!m2 || !m2.ticker) { await store.updateTest(cid, { status: "error", error: "the market could not be read when the order would have arrived" }); results.push(ticker + ": no second read"); continue; }
      const f = simFill(pick, count, m2);
      await store.updateTest(cid, {
        status: f.fillCount > 0 ? "filled" : "no fill", fillCount: String(f.fillCount), remainingCount: String(count - f.fillCount),
        averageFillPrice: f.fillCount > 0 ? String(f.price) : null, sentSide: pick.side, sentPrice: pick.limit, reason: f.reason, seen2: bookSeen(m2),
      });
      results.push(ticker + ": " + (f.fillCount > 0 ? "simulated fill " + f.fillCount + " of " + count : "simulated no fill (" + f.reason + ")"));
    } catch (e) {
      results.push(ticker + ": " + String((e && e.message) || e).slice(0, 80));
    }
  }
  await note(results.join("; ") || "Watching. No market is 6 minutes from its close right now.");
  return { ok: true, results };
}

module.exports = { SIM_SERIES, CALIBRATION_SERIES, ALL_SERIES, ARRIVAL_MS, simFill, runSimTick };

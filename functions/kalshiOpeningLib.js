"use strict";
// The OPENING WINDOW test, OW1 (README: "Pre-registration: OW1, the opening window, two lanes"). Every minute it looks at the Bitcoin, gold and Ethereum 15 minute markets that are
// about 10 minutes from their close (five minutes after the open) and records, ON PAPER, what two simple rules would have bought there. NOTHING HERE PLACES AN ORDER, AND NOTHING HERE CAN.
//
// KEYLESS by construction, which is the rule CLAUDE.md sets for any simulation in this repo: this file has no signing, no key, no /portfolio call and no POST, and its scheduled
// function (index.js) is declared with no secrets. The only things it can write are its own documents (kalshiOpeningOrders, kalshiOpeningControl). It borrows the live library only for
// constants and the stake rule, so a paper trade is the size a live trade would be today.
//
// THERE IS NO LIVE PATH, on purpose (the owner asked for an anti-degen site, and the theory has not been read yet). Going live is a separate reviewed change under a written waiver,
// and it must carry every gate runL1Tick has: the halt switch, an unresolved order, the loss stop shared with L1, one combined limit per window shared with L1 (an OW1 order at 10 minutes
// left and an L1 order at 6 minutes left in the same market are the same window), the 24 hour order cap, $2.00 a contract, and the size ladder. It must have its own code gate that is
// NOT CODE_KILL_SWITCH: flipping that switch to restart L1 must never start this.
//
// Two lanes, one decision per market and lane, both taker at the ask and held to settlement (no exit: L1's 50c exit was set for 88c to 97c entries and means nothing at 20c to 30c):
//   F, the early favourite: the side whose fresh ask is 82c to 87c, the band just under L1's 88c floor. A win pays 13c to 18c (L1's pays 3c to 12c), against a win rate the price says is 82% to 87%.
//   U, the early underdog (the flip lane): the side whose fresh ask is 20c to 30c, the "30% flips". A win pays 70c to 80c against a win rate the price says is 20% to 30%.
// The owner's two instincts, each tested as a pre-registered rule. Their predicted outcomes and kill criteria are in the README section, written before any record existed.
// One market never gets both lanes. The two sides of a market sum to about $1, so a favourite at 82c has an underdog at about 19c, and a favourite at 80c with a 2c spread has one at 20c:
// buying both is a guaranteed small loss, not a flip. The bands are chosen so that this is rare (a 1c spread cannot do it), and when it does happen the favourite lane takes the market.

const bot = require("./kalshiSignalLib");
const live = require("./kalshiLiveLib");

const OPENING_LANES = { F: { label: "early favourite", band: [0.82, 0.87] }, U: { label: "early underdog", band: [0.20, 0.30] } };
const OPENING_SERIES = live.L1_SERIES;                  // the markets the bot trades; a series is added to the live list by a reviewed edit, and this follows it
const OPENING_WINDOW_MS = [570000, 640000];             // time left at which a market is eligible: about 10 minutes (L1's own window is 330000 to 400000, 70 s wide too)
const ARRIVAL_MS = 500;                                 // the pause before the second read, about the time a real order takes to arrive
const OPENING_MAX_ORDERS = live.L1_MAX_ORDERS;          // the live 24 hour order cap, recorded as a flag
const OPENING_WINDOW_CAP_FRACTION = live.L1_WINDOW_CAP_FRACTION;   // the live per-window cap, recorded as a flag

const num = (v) => { const x = parseFloat(v); return Number.isFinite(x) ? x : NaN; };
const r4 = (x) => Math.round(x * 10000) / 10000;

// The side a lane would buy from this market's fresh book, or null. The same rounding as the live pick (live.l1Pick), with the lane's own band: prices run in tenths of a cent
// mid-book, so the limit is rounded in the direction that can only cross (YES up to the next cent, NO down to the cent), and the band is judged on the real price, not the rounded one.
function bandPick(m, band) {
  const bid = num(m && m.yes_bid_dollars), ask = num(m && m.yes_ask_dollars);
  if (!bot.validQuote(Number.isFinite(bid) ? bid : null, Number.isFinite(ask) ? ask : null)) return null;
  const lo = band[0] - 1e-9, hi = band[1] + 1e-9;
  if (r4(ask) >= lo && r4(ask) <= hi) {
    const limit = Math.ceil(r4(ask) * 100 - 1e-9) / 100;
    return { side: "yes", price: r4(ask), limit, worst: limit };
  }
  const noPrice = r4(1 - bid);
  if (noPrice >= lo && noPrice <= hi) {
    const limit = Math.floor(r4(bid) * 100 + 1e-9) / 100;
    return { side: "no", price: noPrice, limit, worst: r4(1 - limit) };
  }
  return null;
}

// Every lane that would buy something from this book: [{ lane, side, price, limit, worst }]. Never both lanes for one market: if the favourite lane qualifies, the underdog lane is the
// opposite leg of the same market (a hedge that can only lose the fees), so the favourite takes it.
function openingPicks(m) {
  const out = [];
  for (const lane of Object.keys(OPENING_LANES)) {
    const p = bandPick(m, OPENING_LANES[lane].band);
    if (p) out.push(Object.assign({ lane }, p));
  }
  return out.length > 1 ? out.filter((p) => p.lane === "F") : out;
}

// The fill an immediate-or-cancel buy at the pick's limit would get from this book, a moment after the decision. Pure; the same model the removed simulation used.
//   YES: fills at the yes ask while it is at or under the limit, up to the size resting there.
//   NO:  a NO buy is a YES bid hit: the NO price is 1 minus the yes bid, the limit is pick.worst, the size is the yes bid's size.
// A missing quote or size, a crossed book, or a price that moved past the limit is no fill, never a guess (the real bot fills about 56% of its signals, so always filling would flatter this).
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

function bookSeen(m, nowMs) {
  const n = (v) => { const x = num(v); return Number.isFinite(x) ? x : null; };
  return { bid: n(m.yes_bid_dollars), ask: n(m.yes_ask_dollars), bidSize: n(m.yes_bid_size_fp), askSize: n(m.yes_ask_size_fp), at: new Date(nowMs).toISOString() };
}

// The two live limits that bind several orders together, worked out for a paper order and RECORDED, never enforced. Enforcing them would cut the research sample by the clock (the first
// 200 signals of a day, the first window's markets), and at paper sizes they almost never bind. They are mandatory in a live path and are computed here the way the live tick computes them,
// so the paper dollars can be read as what the live limits would have allowed. `recent` is the last 24 hours of this engine's own records.
function capFlags(recent, ticker, cost, sizeBase, nowMs) {
  const dayStart = nowMs - live.L1_WINDOW_DAY_MS;
  const inDay = (recent || []).filter((t) => t.ts >= dayStart).length;
  const wkey = live.windowKey(ticker);
  const used = (recent || []).filter((t) => live.windowKey(t.ticker) === wkey && ["filled", "sending", "unknown"].includes(t.status)).reduce((a, t) => a + (Number(t.maxCost) || 0), 0);
  const room = OPENING_WINDOW_CAP_FRACTION * (Number.isFinite(sizeBase) ? sizeBase : Infinity) - used;
  return { orderCap: inDay >= OPENING_MAX_ORDERS, windowCap: used > 0 && cost > room + 1e-9, windowUsed: Number(used.toFixed(2)) };
}

// One minute of the engine. state = kalshiOpeningControl/state (only its note is written); session = the LIVE session document (only its size fields are read);
// cash = the account's total; store = kalshiOpeningOrders. Never throws for a single bad market.
async function runOpeningTick(args) {
  const { now, quotes, active, session, cash, store, readMarket, sleep, setState } = args;
  const note = async (text) => { try { await setState({ lastTickAt: now, lastNote: String(text).slice(0, 300) }); } catch (e) { /* the note is optional */ } };
  if (!active) { await note("The exchange is not trading right now."); return { skipped: "exchange inactive" }; }
  const [lo, hi] = OPENING_WINDOW_MS;
  const candidates = (quotes || []).filter((q) => OPENING_SERIES.includes(q.series) && q.m && ["active", "open"].includes(q.m.status)
    && Date.parse(q.m.close_time) - now >= lo && Date.parse(q.m.close_time) - now <= hi)
    .sort((x, y) => OPENING_SERIES.indexOf(x.series) - OPENING_SERIES.indexOf(y.series));
  if (!candidates.length) { await note("Watching. Decisions are taken about 10 minutes before a close, and no market is at that point right now."); return { skipped: "no market in the window" }; }

  // Sized like the live bot: with its sizing on, the cap from its weekly review and the stake rule on the account's cash; otherwise one contract each.
  const sizing = Boolean(session && session.sizing === true);
  const sizeCap = session && Number.isFinite(session.sizeCap) ? session.sizeCap : 1;
  const sizeBase = session && Number.isFinite(session.sizeBase) ? session.sizeBase : (Number.isFinite(cash) ? cash : NaN);
  const cashNow = Number.isFinite(cash) ? cash : sizeBase;
  let recent = [];
  try { recent = await store.sessionTrades(now - live.L1_WINDOW_DAY_MS); } catch (e) { recent = []; }

  const results = [];
  for (const c of candidates) {
    const ticker = c.m.ticker;
    try {
      const m = await readMarket(ticker);
      if (!m || !m.ticker) { results.push(ticker + ": could not read the market"); continue; }
      const left = Date.parse(m.close_time) - now;
      if (!["active", "open"].includes(m.status) || left < lo || left > hi) { results.push(ticker + ": not open in the 10 minute window"); continue; }
      const picks = openingPicks(m);
      if (!picks.length) { results.push(ticker + ": no side is in a lane's band"); continue; }
      const made = [];
      for (const pick of picks) {
        const cost1 = pick.worst + bot.takerFee(pick.worst, 1);
        if (cost1 > live.LIVE_CAP + 1e-9) { results.push(ticker + " " + pick.lane + ": would cost $" + cost1.toFixed(2) + ", above the cap"); continue; }
        const count = sizing && Number.isFinite(cashNow) ? live.l1Count(cashNow, cost1, sizeCap, 0) : 1;
        const cost = pick.worst * count + bot.takerFee(pick.worst, count);
        const cid = "OW1-" + pick.lane + "-" + ticker;
        const record = {
          ticker, series: c.series, strategy: "OW1", lane: pick.lane, mode: "paper", side: pick.side, band: Math.round(OPENING_LANES[pick.lane].band[0] * 100) + "-" + Math.round(OPENING_LANES[pick.lane].band[1] * 100) + "c",
          count, price: pick.price, limit: pick.limit, leftMs: left, exchangeIndex: m.exchange_index === undefined ? null : m.exchange_index, clientOrderId: cid,
          status: "sending", settled: false, ts: now, maxCost: Number(cost.toFixed(2)), seen: bookSeen(m, now), caps: capFlags(recent, ticker, cost, sizeBase, now),
        };
        if (!(await store.createTest(cid, record))) { results.push(ticker + " " + pick.lane + ": already recorded"); continue; }   // one record per market and lane, even across two instances
        recent.push(record);
        made.push({ pick, count, cid });
      }
      if (!made.length) continue;
      await sleep(ARRIVAL_MS);
      let m2 = null;
      try { m2 = await readMarket(ticker); } catch (e) { m2 = null; }
      for (const t of made) {
        if (!m2 || !m2.ticker) {
          await store.updateTest(t.cid, { status: "error", error: "the market could not be read when the order would have arrived" });
          results.push(ticker + " " + t.pick.lane + ": no second read");
          continue;
        }
        const f = simFill(t.pick, t.count, m2);
        const patch = {
          status: f.fillCount > 0 ? "filled" : "no fill", fillCount: String(f.fillCount), remainingCount: String(t.count - f.fillCount),
          averageFillPrice: f.fillCount > 0 ? String(f.price) : null, reason: f.reason, seen2: bookSeen(m2, now),
        };
        await store.updateTest(t.cid, patch);
        const rec = recent.find((x) => x.clientOrderId === t.cid); if (rec) Object.assign(rec, patch);
        results.push(ticker + " " + t.pick.lane + ": " + (f.fillCount > 0 ? "paper fill " + f.fillCount + " of " + t.count : "paper no fill (" + f.reason + ")"));
      }
    } catch (e) {
      results.push(ticker + ": " + String((e && e.message) || e).slice(0, 80));
    }
  }
  await note(results.join("; ") || "Watching.");
  return { ok: true, results };
}

module.exports = { OPENING_LANES, OPENING_SERIES, OPENING_WINDOW_MS, ARRIVAL_MS, OPENING_MAX_ORDERS, OPENING_WINDOW_CAP_FRACTION, bandPick, openingPicks, simFill, capFlags, runOpeningTick };

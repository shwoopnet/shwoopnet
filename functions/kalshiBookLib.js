"use strict";
// Order-book recorder logic. READ ONLY: public market data, no key, and no order code
// anywhere in this file (kalshiBookGates asserts it). No Firebase and no network in here,
// so the repo's plain-node tests can run it; index.js supplies Firestore and Kalshi.
//
// Why it exists: Kalshi's minute candles cannot answer quoting questions (ideas L4 to L6 in
// kalshi-scalper's README ledger). The market LIST lags the real book by up to about 2c, and
// a minute candle hides everything between the bars. This keeps the real top of the book
// every ~10 seconds so those ideas can be tested on depth. It describes; it never judges.
//
// One document per minute, keyed by the minute, so two processes (a deploy overlaps old and
// new) write the SAME document and cannot double-count. A write per snapshot would be ~17,000
// a day; per minute it is 1,440.

const { KALSHI_SERIES: SERIES, kalshiNum: num } = require("./kalshiLib");

const LEVELS_KEPT = 3;
const CYCLES = 5;
const EVERY_MS = 10000;
const BUDGET_MS = 45000;          // stop starting new cycles after this, so the 58s timeout is never the thing that ends a run
const KEEP_DAYS = 10;

const round4 = (x) => Math.round(x * 10000) / 10000;

function levels(raw) {
  const out = [];
  for (const row of Array.isArray(raw) ? raw : []) {
    const p = num(row && row[0]), q = num(row && row[1]);
    if (p !== null && q !== null) out.push([p, q]);
  }
  return out.sort((a, b) => a[0] - b[0]);     // ascending, so the best bid is the LAST level
}

// Firestore refuses an array inside an array ("Property array contains an invalid nested entity"), which is what [[price, size], ...] is, so a level is a
// map {p, q}. The first version stored pairs and the recorder failed on every write for its first day; a test now checks the stored document against that rule.
const asLevels = (ls) => ls.slice(-LEVELS_KEPT).map((l) => ({ p: l[0], q: l[1] }));

// Kalshi lists resting BIDS on each side. A yes ask is what the best no bid implies: 1 - it.
// An empty side is null, never 0: zero would read as a free price.
function parseBook(raw) {
  const ob = (raw && raw.orderbook_fp) || {};
  const yes = levels(ob.yes_dollars), no = levels(ob.no_dollars);
  const yb = yes.length ? yes[yes.length - 1][0] : null;
  const nb = no.length ? no[no.length - 1][0] : null;
  const depth = (ls) => ls.slice(-LEVELS_KEPT).reduce((s, l) => s + l[1], 0);
  return {
    yb, nb,
    ya: nb === null ? null : round4(1 - nb),
    na: yb === null ? null : round4(1 - yb),
    yd: depth(yes), nd: depth(no),
    yl: asLevels(yes), nl: asLevels(no),
  };
}

async function snapshotSeries(get, series, nowMs) {
  const listed = (await get("/markets?series_ticker=" + series + "&status=open&limit=20")).markets || [];
  const rows = [];
  for (const m of listed) {
    const b = parseBook(await get("/markets/" + encodeURIComponent(m.ticker) + "/orderbook"));
    // The list's own price is kept beside the book so its staleness can be measured later.
    rows.push(Object.assign({ t: nowMs(), s: series, k: m.ticker, ly: num(m.yes_bid_dollars), la: num(m.yes_ask_dollars) }, b));
  }
  return rows;
}

async function recordMinute({ get, store, now, sleep, cycles = CYCLES, everyMs = EVERY_MS }) {
  const start = now();
  const minute = Math.floor(start / 60000) * 60000;
  const snaps = [], errs = [];
  for (let i = 0; i < cycles && now() - start < BUDGET_MS; i++) {
    const t0 = now();
    for (const s of SERIES) {
      try { snaps.push(...await snapshotSeries(get, s, now)); }
      catch (e) { errs.push({ t: now(), s, e: String((e && e.message) || e).slice(0, 160) }); }   // one bad read must not end the minute
    }
    if (i < cycles - 1) await sleep(Math.max(0, everyMs - (now() - t0)));
  }
  await store.writeMinute("bk-" + minute, { ts: minute, snaps, errs });
  await store.pruneBefore(minute - KEEP_DAYS * 86400000);
  await store.setStatus({ lastTickMs: now(), snaps: snaps.length, errs: errs.length });
  return { snaps: snaps.length, errs: errs.length };
}

module.exports = { parseBook, snapshotSeries, recordMinute, KEEP_DAYS, CYCLES };

// The opening window test, OW1 (functions/kalshiOpeningLib.js): it records on paper what two rules would have bought about 10 minutes before a close, and it can never place an order.
// Plain node, no framework. Each gate states the consequence, not the mechanism.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const opening = require('../functions/kalshiOpeningLib.js');
const live = require('../functions/kalshiLiveLib.js');
const bot = require('../functions/kalshiSignalLib.js');
const libSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiOpeningLib.js'), 'utf8');
const idxSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
const rulesSrc = fs.readFileSync(path.join(__dirname, '..', 'firestore.rules'), 'utf8');

const NOW = Date.parse('2026-10-12T15:00:00Z');
const iso = (ms) => new Date(ms).toISOString();
// A market 10 minutes from its close whose YES side is the favourite at 82c by default (lane F).
const mkt = (series, over = {}) => Object.assign({ ticker: series + '-26OCT121115-15', series, status: 'active', close_time: iso(NOW + 600000),
  yes_bid_dollars: '0.8100', yes_ask_dollars: '0.8200', yes_bid_size_fp: '500.00', yes_ask_size_fp: '500.00', exchange_index: 2 }, over);

function world({ markets, second, session = { sizing: true, sizeCap: 12, sizeBase: 553 }, cash = 553, preload = [], active = true } = {}) {
  const docs = new Map(), notes = [], reads = {};
  preload.forEach((d, i) => docs.set('pre-' + i, d));
  const store = {
    async createTest(id, d) { if (docs.has(id)) return false; docs.set(id, { ...d }); return true; },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
    async sessionTrades(since) { return [...docs.entries()].filter(([, d]) => d.ts >= since).map(([id, d]) => ({ id, ...d })); },
    async openFilled() { return [...docs.entries()].filter(([, d]) => d.status === 'filled' && d.settled === false).map(([id, d]) => ({ id, ...d })); },
  };
  return { docs, notes, store,
    args: { session, cash, now: NOW, active, quotes: markets.map((m) => ({ series: m.series, m })), store,
      readMarket: async (t) => { reads[t] = (reads[t] || 0) + 1; return reads[t] === 1 ? markets.find((m) => m.ticker === t) : (second && second[t]) || markets.find((m) => m.ticker === t); },
      sleep: async () => {}, setState: async (p) => { notes.push(p.lastNote); } } };
}

const gates = {};

// O1: it cannot place an order. Its library has no signing, no key, no portfolio call and no POST, nothing that sizes or sends a live order, and its scheduled function is declared with no
// secrets and is not behind CODE_KILL_SWITCH, so flipping that switch to restart L1 can never start it. There is no callable that switches it either (no knob to flip in a bad hour).
gates.O1 = () => {
  const code = libSrc.replace(/\/\/.*$/gm, '');
  for (const bad of ['signRequest', 'PRIVATE', 'KEY_ID', '/portfolio', 'POST', 'liveRequest', 'runL1Tick', 'runExitWatch', 'flattenAll', 'createOrder', 'exitBody', 'liveOrderBody', 'KALSHI_LIVE', 'CODE_KILL_SWITCH', 'kalshiLiveOrders']) {
    assert.ok(!code.includes(bad), 'the opening library must not contain ' + bad);
  }
  const start = idxSrc.indexOf('function firestoreOpeningStore'), end = idxSrc.indexOf('exports.kalshiLiveExit = onSchedule(');
  const block = idxSrc.slice(start, end), bcode = block.replace(/\/\/.*$/gm, '');
  assert.ok(/exports\.kalshiOpeningTick = onSchedule\(\s*\{ schedule: "every 1 minutes", timeoutSeconds: 55, retryCount: 0, memory: "256MiB" \}/.test(block), 'declared with no secrets');
  assert.ok(!/KALSHI_LIVE_KEY_ID|KALSHI_LIVE_PRIVATE_KEY|secrets:|CODE_KILL_SWITCH|KALSHI_LIVE_ENABLED/.test(bcode), 'it cannot see the live key, and neither switch has anything to do with it');
  assert.ok(!/exports\.\w+ = onCall/.test(block), 'no callable switches it on or off');
  assert.ok(idxSrc.indexOf('exports.kalshiOpeningTick') < idxSrc.indexOf('exports.kalshiBookRecorder'), 'the recorder stays last');
  assert.strictEqual((idxSrc.match(/strategy: "OW1"/g) || []).length, 0, 'nothing in the functions file writes an OW1 order: the only writer is the keyless library');
};

// O2: each lane buys the side the owner described, judged on the real price (YES at its ask, NO at one minus the yes bid), both ends of the band included, one cent outside excluded.
// The two sides of a book are complements, so each case below names both prices.
gates.O2 = () => {
  const book = (b, a) => ({ yes_bid_dollars: String(b), yes_ask_dollars: String(a) });
  const lane = (b, a) => opening.openingPicks(book(b, a)).map((p) => p.lane + ':' + p.side + ':' + p.price).join(',');
  assert.strictEqual(lane(0.81, 0.82), 'F:yes:0.82', 'YES at 82c is the favourite lane (NO is 19c, outside the underdog band)');
  assert.strictEqual(lane(0.86, 0.87), 'F:yes:0.87', '87c is still inside');
  assert.strictEqual(lane(0.87, 0.88), '', '88c belongs to L1, not to this lane');
  assert.strictEqual(lane(0.80, 0.81), 'U:no:0.2', 'YES at 81c is outside the favourite lane, and its NO side at 20c is the underdog');
  assert.strictEqual(lane(0.19, 0.20), 'U:yes:0.2', 'YES at 20c is the underdog (flip) lane');
  assert.strictEqual(lane(0.29, 0.30), 'U:yes:0.3', '30c is still inside');
  assert.strictEqual(lane(0.30, 0.31), '', '31c on YES and 70c on NO are in no lane');
  assert.strictEqual(lane(0.18, 0.19), 'F:no:0.82', 'YES at 19c is no underdog, but its NO side at 82c is a favourite');
  assert.strictEqual(lane(0.13, 0.14), 'F:no:0.87', 'a NO favourite at 87c');
  assert.strictEqual(lane(0.12, 0.13), '', 'a NO at 88c is L1\'s');
  assert.strictEqual(lane(0.73, 0.74), 'U:no:0.27', 'a NO underdog at 27c: priced off the yes bid');
  assert.strictEqual(lane(0.49, 0.51), '', 'a coin flip is in no lane');
  assert.strictEqual(lane(0.0, 1.0), '', 'an empty book is not a quote');
  assert.strictEqual(lane(0.70, 0.95), '', 'a spread wider than 10c is not a quote');
  assert.strictEqual(opening.bandPick(book(0.115, 0.12), opening.OPENING_LANES.F.band), null, 'a NO at 88.5c is outside the favourite lane');
  // A market never gets both legs: a 2c spread at the favourite lane's floor puts the other side at 20c, which would be the underdog lane. The favourite takes it.
  assert.strictEqual(lane(0.80, 0.82), 'F:yes:0.82', 'one leg only: buying both sides of a market is a guaranteed small loss, not a flip');
  // The pick rounds the way the live pick does, so a paper fill is judged the way a live order would be: the same code on L1's own band gives L1's own pick.
  for (const [b, a] of [[0.92, 0.93], [0.115, 0.12], [0.88, 0.885], [0.965, 0.97], [0.5, 0.52], [0.03, 0.04]]) {
    assert.deepStrictEqual(opening.bandPick(book(b, a), live.L1_BAND), live.l1Pick(book(b, a)), 'same pick as the live rule at ' + b + '/' + a);
  }
  assert.ok(opening.OPENING_LANES.F.band[1] < live.L1_BAND[0] && opening.OPENING_LANES.F.band[0] > 0.80, 'the favourite lane sits just under L1\'s floor, so the two never trade the same price');
};

// O3: it looks only at markets about 10 minutes from their close. Six minutes left is L1's window and 14 minutes is the first minute of the market: neither is a decision point here.
gates.O3 = async () => {
  for (const [left, expect] of [[600000, 2], [570000, 2], [640000, 2], [560000, 0], [650000, 0], [360000, 0], [840000, 0]]) {
    const w = world({ markets: [mkt('KXBTC15M', { close_time: iso(NOW + left) })] });
    await opening.runOpeningTick(w.args);
    assert.strictEqual(w.docs.size > 0 ? 1 : 0, expect ? 1 : 0, left / 1000 + ' s left');
  }
  const closed = world({ markets: [mkt('KXBTC15M', { status: 'closed' })] });
  await opening.runOpeningTick(closed.args); assert.strictEqual(closed.docs.size, 0, 'a market that is no longer open is skipped');
  const off = world({ markets: [mkt('KXBTC15M')], active: false });
  assert.deepStrictEqual(await opening.runOpeningTick(off.args), { skipped: 'exchange inactive' }); assert.strictEqual(off.docs.size, 0);
  const none = world({ markets: [mkt('KXBTC15M', { close_time: iso(NOW + 100000) })] });
  assert.deepStrictEqual(await opening.runOpeningTick(none.args), { skipped: 'no market in the window' });
  const xrp = world({ markets: [mkt('KXXRP15M')] });
  await opening.runOpeningTick(xrp.args); assert.strictEqual(xrp.docs.size, 0, 'only the bot\'s own markets: Bitcoin, gold and Ethereum, the live list');
  assert.deepStrictEqual(opening.OPENING_SERIES, live.L1_SERIES, 'and the list follows the live list');
};

// O4: a paper trade is the size a live one would be today: the live stake rule on the live session's cap and the account's cash, no profit add-on, at most $2.00 a contract; one contract when the live bot is not scaling.
gates.O4 = async () => {
  const w = world({ markets: [mkt('KXBTC15M')] });
  await opening.runOpeningTick(w.args);
  const r = w.docs.get('OW1-F-KXBTC15M-26OCT121115-15');
  const cost1 = 0.82 + bot.takerFee(0.82, 1);
  assert.strictEqual(r.count, live.l1Count(553, cost1, 12, 0), 'the same stake rule as the live bot, without its profit add-on');
  assert.deepStrictEqual([r.strategy, r.lane, r.mode, r.settled, r.status], ['OW1', 'F', 'paper', false, 'filled']);
  assert.ok(r.maxCost > 0 && Math.abs(r.maxCost - (0.82 * r.count + bot.takerFee(0.82, r.count))) < 0.006, 'carries the order cost with the fee, which settlement reads');
  assert.ok(r.seen && r.seen2 && r.leftMs === 600000, 'both books and the time left are kept so a result can be explained afterwards');
  const one = world({ markets: [mkt('KXBTC15M')], session: { sizing: false } });
  await opening.runOpeningTick(one.args);
  assert.strictEqual(one.docs.get('OW1-F-KXBTC15M-26OCT121115-15').count, 1, 'with the live bot not scaling it is one contract, as live');
  const none = world({ markets: [mkt('KXBTC15M')], session: null, cash: NaN });
  await opening.runOpeningTick(none.args);
  assert.strictEqual(none.docs.get('OW1-F-KXBTC15M-26OCT121115-15').count, 1, 'no live session to read: one contract, never a guess');
  assert.ok(live.LIVE_CAP === 2 && opening.OPENING_MAX_ORDERS === live.L1_MAX_ORDERS && opening.OPENING_WINDOW_CAP_FRACTION === live.L1_WINDOW_CAP_FRACTION, 'the limits it records are the live bot\'s own constants, not copies');
};

// O5: the fill is judged on a second read of the book, the way an immediate-or-cancel order at the touch would be. A price that runs away is a no fill, which keeps the paper fill rate honest.
gates.O5 = async () => {
  const yes = { side: 'yes', price: 0.82, limit: 0.82, worst: 0.82 };
  assert.deepStrictEqual(opening.simFill(yes, 11, mkt('KXBTC15M')), { fillCount: 11, price: 0.82, reason: 'filled' }, 'price held, plenty of size: fills in full');
  assert.strictEqual(opening.simFill(yes, 11, mkt('KXBTC15M', { yes_ask_dollars: '0.8300' })).fillCount, 0, 'one cent past the limit: no fill');
  assert.strictEqual(opening.simFill(yes, 11, mkt('KXBTC15M', { yes_ask_size_fp: '4.00' })).fillCount, 4, 'a partial fill, only what rests at the touch');
  assert.strictEqual(opening.simFill(yes, 11, mkt('KXBTC15M', { yes_ask_size_fp: undefined })).fillCount, 0, 'an unknown size is no fill, never a guess');
  assert.strictEqual(opening.simFill(yes, 11, mkt('KXBTC15M', { yes_bid_dollars: '0.9000', yes_ask_dollars: '0.8200' })).fillCount, 0, 'a crossed book is no fill');
  const w = world({ markets: [mkt('KXBTC15M')], second: { 'KXBTC15M-26OCT121115-15': mkt('KXBTC15M', { yes_bid_dollars: '0.8400', yes_ask_dollars: '0.8500' }) } });
  await opening.runOpeningTick(w.args);
  const r = w.docs.get('OW1-F-KXBTC15M-26OCT121115-15');
  assert.deepStrictEqual([r.status, r.fillCount], ['no fill', '0']); assert.ok(/moved/.test(r.reason) && r.seen2.ask === 0.85);
  const failed = world({ markets: [mkt('KXBTC15M')] });
  const rm = failed.args.readMarket; let n = 0;
  failed.args.readMarket = async (t) => { n++; if (n === 2) throw new Error('timeout'); return rm(t); };
  await opening.runOpeningTick(failed.args);
  assert.strictEqual(failed.docs.get('OW1-F-KXBTC15M-26OCT121115-15').status, 'error', 'a failed second read is an error record, not a guessed fill');
};

// O6: one record per market and lane, however often the minute runs or how many instances run it (a deploy briefly runs two); a book is only the lanes it fits; a bad market never stops the others.
gates.O6 = async () => {
  const w = world({ markets: [mkt('KXBTC15M')] });
  await opening.runOpeningTick(w.args); await opening.runOpeningTick(w.args);
  assert.strictEqual(w.docs.size, 1, 'a second run on the same market records nothing new');
  assert.ok(/already recorded/.test(w.notes[w.notes.length - 1]));
  const both = world({ markets: [mkt('KXBTC15M', { yes_bid_dollars: '0.8300', yes_ask_dollars: '0.8400' }), mkt('KXGOLD15M', { yes_bid_dollars: '0.8400', yes_ask_dollars: '0.8500' })] });
  await opening.runOpeningTick(both.args);
  assert.deepStrictEqual([...both.docs.keys()].sort(), ['OW1-F-KXBTC15M-26OCT121115-15', 'OW1-F-KXGOLD15M-26OCT121115-15'], 'one favourite record per market');
  const fav = world({ markets: [mkt('KXBTC15M', { yes_bid_dollars: '0.8200', yes_ask_dollars: '0.8300' })] });
  await opening.runOpeningTick(fav.args);
  assert.deepStrictEqual([...fav.docs.keys()], ['OW1-F-KXBTC15M-26OCT121115-15'], 'a book that is only a favourite is only lane F');
  const dog = world({ markets: [mkt('KXBTC15M', { yes_bid_dollars: '0.2500', yes_ask_dollars: '0.2600' })] });
  await opening.runOpeningTick(dog.args);
  assert.deepStrictEqual([...dog.docs.keys()], ['OW1-U-KXBTC15M-26OCT121115-15'], 'a 26c YES side is only the underdog lane');
  const hedge = world({ markets: [mkt('KXBTC15M', { yes_bid_dollars: '0.8000', yes_ask_dollars: '0.8200' })] });
  await opening.runOpeningTick(hedge.args);
  assert.deepStrictEqual([...hedge.docs.keys()], ['OW1-F-KXBTC15M-26OCT121115-15'], 'a book that fits both lanes records the favourite only: never both legs of one market');
  const bad = world({ markets: [mkt('KXBTC15M'), mkt('KXGOLD15M')] });
  const rm = bad.args.readMarket;
  bad.args.readMarket = async (t) => { if (/BTC/.test(t)) throw new Error('boom'); return rm(t); };
  const r = await opening.runOpeningTick(bad.args);
  assert.ok(r.ok && bad.docs.has('OW1-F-KXGOLD15M-26OCT121115-15') && !bad.docs.has('OW1-F-KXBTC15M-26OCT121115-15'), 'one bad read never stops the other market');
};

// O7: a paper trade settles with the same arithmetic as a live one, so the dollars are comparable; a no fill or an unfinished market is never settled, and the sweep reads only unsettled filled records.
gates.O7 = async () => {
  const w = world({ markets: [mkt('KXBTC15M'), mkt('KXGOLD15M', { yes_bid_dollars: '0.2500', yes_ask_dollars: '0.2600' })] });
  await opening.runOpeningTick(w.args);
  const results = { 'KXBTC15M-26OCT121115-15': 'yes', 'KXGOLD15M-26OCT121115-15': 'no' };
  const fetchFn = async (url) => {
    const t = decodeURIComponent(url.split('/markets/')[1].split('?')[0]);
    return { status: 200, text: async () => JSON.stringify({ market: { ticker: t, result: results[t] || '' } }) };
  };
  const out = await live.settleOpenOrders({ store: w.store, fetchFn, nowMs: NOW + 1000000 });
  assert.strictEqual(out.settled, 2);
  const fav = w.docs.get('OW1-F-KXBTC15M-26OCT121115-15'), dog = w.docs.get('OW1-U-KXGOLD15M-26OCT121115-15');
  assert.ok(fav.settled === true && fav.result === 'yes' && fav.settledPnl > 0, 'the favourite won: it paid $1 a contract less what it cost');
  assert.ok(Math.abs(fav.settledPnl - (fav.count * 1 - fav.maxCost)) < 1e-3, 'exactly count minus cost');
  assert.ok(dog.settled === true && dog.result === 'no' && dog.side === 'yes' && Math.abs(dog.settledPnl + dog.maxCost) < 1e-3, 'the 26c YES lost: a full loss costs the whole order');
  const nf = world({ markets: [mkt('KXBTC15M')], second: { 'KXBTC15M-26OCT121115-15': mkt('KXBTC15M', { yes_ask_dollars: '0.9000', yes_bid_dollars: '0.8900' }) } });
  await opening.runOpeningTick(nf.args);
  const o2 = await live.settleOpenOrders({ store: nf.store, fetchFn, nowMs: NOW }); assert.strictEqual(o2.looked, 0, 'a no fill is not an open position');
  assert.ok(/\.where\("status", "==", "filled"\)\.where\("settled", "==", false\)/.test(idxSrc), 'the sweep reads only the open filled records, not a growing history every minute');
};

// O8: the page can read the records and nothing but the server can write them.
gates.O8 = () => {
  for (const col of ['kalshiOpeningOrders', 'kalshiOpeningControl']) {
    const m = rulesSrc.match(new RegExp('match /' + col + '/\\{id\\} \\{[^}]*\\}'));
    assert.ok(m && /allow read: if isAdmin\(\);/.test(m[0]) && /allow write: if false;/.test(m[0]), col + ' is admin read, server write only');
  }
};

// O9: a Kalshi outage is a note on the heartbeat and a log line, not a failed run, and the settle sweep still happens after it.
gates.O9 = () => {
  const tick = idxSrc.slice(idxSrc.indexOf('exports.kalshiOpeningTick'), idxSrc.indexOf('exports.kalshiLiveExit'));
  assert.ok(tick.indexOf('This minute could not be read') > -1 && tick.indexOf('This minute could not be read') < tick.indexOf('live.settleOpenOrders'), 'a failed minute is a note, and the settle sweep still runs after it');
  assert.ok(/settle sweep failed/.test(tick), 'and a failed sweep is logged, never thrown');
};

// O10: it can never touch the live bot. Its records live in their own collection (a paper record stuck "sending" must never block a live order, which checks its own collection for unresolved orders),
// the live store still reads only kalshiLiveOrders, and the live tick, exit watch and pool never see a record of this engine.
gates.O10 = () => {
  const store = idxSrc.slice(idxSrc.indexOf('function firestoreOpeningStore'), idxSrc.indexOf('exports.kalshiOpeningTick'));
  assert.ok(/db\.collection\("kalshiOpeningOrders"\)/.test(store) && !/kalshiLiveOrders/.test(store), 'the paper store is its own collection');
  const liveStore = idxSrc.slice(idxSrc.indexOf('function firestoreLiveStore'), idxSrc.indexOf('function firestoreOpeningStore') > -1 ? idxSrc.indexOf('exports.kalshiLiveExit') : undefined);
  assert.ok(/db\.collection\("kalshiLiveOrders"\)/.test(liveStore), 'the live store is unchanged');
  const liveLib = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.ok(!/kalshiOpeningOrders|kalshiOpeningLib|"OW1"/.test(liveLib), 'the live library knows nothing about the paper engine');
  assert.ok(!/kalshiOpeningOrders/.test(idxSrc.slice(idxSrc.indexOf('exports.kalshiLiveExit'))), 'nothing after the paper function (the exit watch, the live tick, the recorder) reads its records');
};

// O11: the live limits that tie several orders together are worked out the live way and RECORDED, never enforced, so the research sample is not cut by the clock (the first 200 signals of a day)
// while the paper dollars can still be read as what the live limits would have allowed.
gates.O11 = async () => {
  const f = opening.capFlags;
  const base = 553, cap = live.L1_WINDOW_CAP_FRACTION * base;
  assert.strictEqual(f([], 'KXBTC15M-26OCT121115-15', 9, base, NOW).windowCap, false, 'the first order in a window is never over the cap');
  const used = [{ ts: NOW - 60000, ticker: 'KXGOLD15M-26OCT121115-15', status: 'filled', maxCost: cap - 5 }];
  assert.strictEqual(f(used, 'KXBTC15M-26OCT121115-15', 4.9, base, NOW).windowCap, false, 'it fits exactly in what is left');
  assert.strictEqual(f(used, 'KXBTC15M-26OCT121115-15', 5.1, base, NOW).windowCap, true, 'a second market in the same window that does not fit is flagged');
  assert.strictEqual(f(used, 'KXBTC15M-26OCT121130-15', 20, base, NOW).windowCap, false, 'a different window has its own room');
  const many = Array.from({ length: live.L1_MAX_ORDERS }, (_, i) => ({ ts: NOW - 1000 - i, ticker: 'T' + i + '-26OCT110000-00', status: 'no fill', maxCost: 1 }));
  assert.strictEqual(f(many, 'X-26OCT121115-15', 1, base, NOW).orderCap, true, '200 records in 24 hours: flagged');
  assert.strictEqual(f(many.slice(1), 'X-26OCT121115-15', 1, base, NOW).orderCap, false, '199 is not');
  const w = world({ markets: [mkt('KXBTC15M')], preload: many });
  await opening.runOpeningTick(w.args);
  const r = w.docs.get('OW1-F-KXBTC15M-26OCT121115-15');
  assert.ok(r && r.caps.orderCap === true && r.status === 'filled', 'past the 24 hour cap it is still recorded and settled, only flagged');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();

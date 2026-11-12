'use strict';
// CB1 to CB10: the CFRTIBTC probe candidate (Nov 12, 2026, the Probe Engineering Desk; docs/probes/PROBE_SPEC_CFRTIBTC.md). Consequence if these fail: a probe that the owner
// has not approved could trade, or an approved one could trade past one contract, past its $5 budget, on a model reading it could not make, or reach a host it should not.
// The candidate is OFF: nothing here needs, or makes, a network call.
const assert = require('assert');
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const slot = require('../functions/kalshiSlotLib');
const run = require('../functions/kalshiSlotRunLib');
const spot = require('../functions/kalshiSpotIndexLib');
const root = path.join(__dirname, '..');
const read = (f) => fs.readFileSync(path.join(root, f), 'utf8');
const C = slot.SLOT_PROBE_CANDIDATES.find((x) => x.id === 'CFRTIBTC');
const ON = { enabled: true, registry: [C], everUsed: true };           // what the registry would hold after a reviewed switch flip; a test-only view
const NOW = Date.parse('2026-11-20T16:57:02Z'), CLOSE = Date.parse('2026-11-20T17:00:00Z');
const T = 'KXBTC15M-26NOV201200-00';
const input = (extra) => Object.assign({ strategyId: 'CFRTIBTC', ticker: T, side: 'yes', limit: 0.2, step: 1, depthAtTouch: 1000, slotOrders: [], l1Orders: [], slotOrdersComplete: true,
  lockTxn: true, lock: null, position: 0, sizingBase: 800, windowCapFraction: 0.055, killLatch: null, secondsLeft: 178, now: NOW, modelEdge: 0.08, spread: 0.02 }, extra || {});
const W = (i) => slot._testOnly.slotOrderCheckWith(ON, i);
const gates = {};

gates['CB1 off by default: the switch is false and frozen, the registry and the hold list are exactly what they were, and the production gate refuses the probe'] = () => {
  assert.strictEqual(slot.SLOT_PROBE_SWITCH.CFRTIBTC, false);
  assert.ok(Object.isFrozen(slot.SLOT_PROBE_SWITCH) && Object.isFrozen(slot.SLOT_PROBE_CANDIDATES) && Object.isFrozen(slot.SLOT_PROBE_BUDGET) && Object.isFrozen(C) && Object.isFrozen(C.entry));
  assert.ok(Object.values(slot.SLOT_PROBE_SWITCH).every((v) => v === false), 'every probe switch is off');
  assert.deepStrictEqual(slot.SLOT_STRATEGIES.map((x) => x.id), ['OICORE', 'EVENT830'], 'the registry holds no probe');
  assert.deepStrictEqual(slot.SLOT_HOLD_ALLOWED, ['OICORE', 'EVENT830'], 'the hold list is unchanged');
  assert.ok(!slot.activeSlotStrategies().some((x) => x.id === 'CFRTIBTC'));
  const r = slot.slotOrderCheck(input());
  assert.ok(!r.allowed && /not in the registry/.test(r.reasons[0]), 'the production gate knows no such strategy: ' + r.reasons[0]);
  const src = read('functions/kalshiSlotLib.js');
  assert.ok(/const SLOT_PROBE_SWITCH = Object\.freeze\(\{ CFRTIBTC: false \}\);/.test(src), 'the switch is a literal false in code');
  assert.ok(/SLOT_PROBE_SWITCH\[c\.id\] === true/.test(src), 'only exactly true switches a candidate on');
  // Nothing stored, requested or in the environment can feed the switch: the library still reads no environment, database or network.
  assert.ok(!/process\.env|firestore|fetch\(|require\("(?!\.\/kalshiSignalLib")/.test(src.replace(/\/\/.*$/gm, '')), 'the slot library stays pure');
};

gates['CB2 the candidate is one contract of the cheap Bitcoin side, 5c to 30c, held, with a model line and a spread line; the validator keeps a model entry off the favourite side'] = () => {
  assert.ok(slot.validateSlotStrategy(C).ok, JSON.stringify(slot.validateSlotStrategy(C).errors));
  assert.deepStrictEqual(JSON.parse(JSON.stringify(C.entry)), { sideRule: 'cheap', priceMin: 0.05, priceMax: 0.3, leftMaxSec: 180, leftMinSec: 120, maxSpread: 0.03, modelEdgeMin: 0.05 });
  assert.deepStrictEqual(C.series, ['KXBTC15M']); assert.strictEqual(C.contractsPerOrder, 1); assert.deepStrictEqual(JSON.parse(JSON.stringify(C.exit)), { holdToSettle: true });
  assert.strictEqual(slot.SLOT_PROBE_MAX_CONTRACTS, 1); assert.strictEqual(slot.SLOT_PROBE_BUDGET.CFRTIBTC, 5); assert.ok(slot.SLOT_PROBE_BUDGET.CFRTIBTC <= slot.SLOT_PROBE_BUDGET_MAX && slot.SLOT_PROBE_BUDGET_MAX <= 20);
  assert.ok(C.reviewedAt <= slot.SLOT_LAST_REVIEWED_ON);
  const v = (patch, top) => slot.validateSlotStrategy(Object.assign(JSON.parse(JSON.stringify(C)), top || {}, { entry: Object.assign(JSON.parse(JSON.stringify(C.entry)), patch) })).ok;
  assert.ok(!v({ sideRule: 'favourite' }) && !v({ sideRule: 'yes' }), 'a model entry buys the cheap side only');
  assert.ok(!v({ priceMax: 0.6 }), 'never above 50c: that would be a favourite held to settlement');
  assert.ok(!v({ modelEdgeMin: 0.01 }) && !v({ modelEdgeMin: 0.9 }) && !v({ modelEdgeMin: 'x' }), 'the model line must be 2c to 50c');
  assert.ok(!v({}, { id: 'OTHERX' }), 'another id with the same entry may not hold to settlement');
  assert.ok(!v({}, { contractsPerOrder: 0 }));
};

gates['CB3 the gate: an edge at or over the line buys exactly one contract; a missing, impossible or small edge, a wide or missing spread, or a price outside 5c to 30c sends nothing'] = () => {
  const ok = W(input());
  assert.ok(ok.allowed && ok.count === 1 && ok.cid === 'S-CFRTIBTC-' + T + '-1', JSON.stringify(ok));
  assert.strictEqual(ok.cost, 0.22, 'cost is the 20c price plus the fee rounded up to the cent on one contract');
  assert.strictEqual(W(input({ wanted: 10 })).count, 1, 'never more than one contract, whatever is asked');
  assert.ok(W(input({ modelEdge: 0.05 })).allowed, 'exactly the line trades');
  for (const b of [undefined, null, NaN, 0.049, -0.2, 1.5, '0.2']) assert.ok(!W(input({ modelEdge: b })).allowed, 'edge ' + b + ' must not trade');
  for (const sp of [undefined, NaN, 0.04, -0.01]) assert.ok(!W(input({ spread: sp })).allowed, 'spread ' + sp + ' must not trade');
  assert.ok(!W(input({ limit: 0.31 })).allowed && !W(input({ limit: 0.04 })).allowed, 'outside the band');
  assert.ok(!W(input({ secondsLeft: 119 })).allowed && !W(input({ secondsLeft: 181 })).allowed, 'outside the time window');
  assert.ok(!W(input({ ticker: 'KXETH15M-26NOV201200-00' })).allowed, 'Bitcoin only');
  assert.ok(!W(input({ lockTxn: false })).allowed && !W(input({ position: -1 })).allowed, 'the direction lock and the hedge rule still apply');
};

// A settled probe order, net given directly (the accounting functions read settledPnl first).
const done = (n, pnl, at) => ({ id: 'S-CFRTIBTC-KXBTC15M-26NOV19' + String(1000 + n) + '-00-1', strategy: 'SLOT', slotId: 'CFRTIBTC', ticker: 'KXBTC15M-26NOV19' + String(1000 + n) + '-00', side: 'yes', step: 1, count: 1,
  limit: 0.25, maxCost: 0.27, ts: at, settledAt: at, status: 'filled', fillCount: '1', settled: true, result: pnl > 0 ? 'yes' : 'no', settledPnl: pnl, exitCount: 0, exitProceeds: 0 });
gates['CB4 the $5 budget: reached means no more orders, it is sticky after a later win, open orders count as lost, and the next order must fit in what is left'] = () => {
  const day = Date.parse('2026-11-12T00:00:00Z');
  const losses = (k) => Array.from({ length: k }, (_, j) => done(j, -0.27, day + j * 900000));
  assert.ok(W(input({ slotOrders: losses(17) })).allowed, '17 losses of 27c is $4.59: still inside');
  const spent = W(input({ slotOrders: losses(19) }));
  assert.ok(!spent.allowed && /budget/.test(spent.reasons[0]), '19 losses is $5.13: ' + spent.reasons[0]);
  const after = losses(19).concat([done(50, 0.73, day + 50 * 900000), done(51, 0.73, day + 51 * 900000)]);
  assert.ok(!W(input({ slotOrders: after })).allowed, 'two later wins do not re-arm it: the budget was reached once');
  const open = { id: 'S-CFRTIBTC-KXBTC15M-26NOV201145-00-1', strategy: 'SLOT', slotId: 'CFRTIBTC', ticker: 'KXBTC15M-26NOV201145-00', side: 'yes', step: 1, count: 1, limit: 0.3, maxCost: 0.32, ts: NOW - 900000, status: 'filled', fillCount: '1', settled: false, exitCount: 0, exitProceeds: 0 };
  assert.ok(!W(input({ slotOrders: losses(18).concat([open]) })).allowed, '$4.86 lost plus a 32c order still open counts as $5.18');
  const p = slot.probeState(C, losses(18));
  assert.ok(!p.spent && Math.abs(p.room - 0.14) < 1e-6, 'room is the budget minus what is lost: ' + JSON.stringify(p));
  const tight = W(input({ slotOrders: losses(18) }));
  assert.ok(!tight.allowed, 'a 21c order does not fit in 14c of room: ' + JSON.stringify(tight.reasons));
  assert.strictEqual(slot.probeState(slot.SLOT_STRATEGIES[0], []), null, 'a strategy that is not a candidate has no probe budget and is untouched');
  const before = losses(19).map((o) => Object.assign({}, o, { ts: Date.parse('2026-11-01T00:00:00Z'), settledAt: Date.parse('2026-11-01T00:00:00Z') }));
  assert.ok(W(input({ slotOrders: before })).allowed, 'results before reviewedAt do not count: only a reviewed edit of that date re-arms a spent probe');
};

// ---- the model -----------------------------------------------------------------------------------------------------------------------------
// A synthetic three-venue tape: one trade a second per venue for 11 minutes, prices on a slow deterministic wave.
function tape(t0, shift) {
  const out = {};
  for (const [v, off] of [['venueA', 0], ['kraken', 3], ['venueC', -2]]) {
    out[v] = [];
    for (let s = 660; s >= 0; s--) out[v].push({ t: t0 - s * 1000, p: 100000 + (shift || 0) + off + 40 * Math.sin(s / 37) + 15 * Math.cos(s / 11) });
  }
  return out;
}
gates['CB5 the model is the research rule: fresh-venue mean index, sample sd of sixty 10 s log changes, a horizon of 8 steps at 120 s, and a normal chance'] = () => {
  assert.ok(Math.abs(spot.phi(0) - 0.5) < 1e-9 && Math.abs(spot.phi(1.96) - 0.975) < 1e-4 && Math.abs(spot.phi(-1) - 0.158655) < 1e-5 && Number.isNaN(spot.phi(NaN)));
  assert.strictEqual(spot.horizonSteps(120), 8, 'the research code scales by sqrt(8) at 120 s');
  assert.ok(Math.abs(spot.horizonSteps(178) - 13.8) < 1e-9 && spot.horizonSteps(59) === null && spot.horizonSteps(NaN) === null);
  const V = tape(NOW);
  // The index: an independent recomputation of "mean of each venue's last price, venues with a trade in the last 10 s only".
  const last = (L, t) => { let x = null; for (const r of L) if (r.t <= t) x = r; return x; };
  const idx = (t) => { const ps = Object.values(V).map((L) => last(L, t)).filter((r) => r && t - r.t <= 10000).map((r) => r.p); return ps.length ? ps.reduce((a, b) => a + b, 0) / ps.length : null; };
  assert.ok(Math.abs(spot.indexAt(V, NOW) - idx(NOW)) < 1e-9 && Math.abs(spot.indexAt(V, NOW - 123456) - idx(NOW - 123456)) < 1e-9);
  const stale = { a: [{ t: NOW - 10001, p: 5 }], b: [{ t: NOW - 9000, p: 7 }] };
  assert.strictEqual(spot.indexAt(stale, NOW), 7, 'a venue silent for more than 10 s is left out');
  assert.strictEqual(spot.indexAt({ a: [{ t: NOW - 20000, p: 5 }] }, NOW), null, 'no fresh venue: no index');
  const xs = []; for (let j = 0; j <= 60; j++) xs.push(idx(NOW - 10000 * j));
  const lr = []; for (let j = 0; j < 60; j++) lr.push(Math.log(xs[j] / xs[j + 1]));
  const m = lr.reduce((a, b) => a + b, 0) / 60, sd = Math.sqrt(lr.reduce((a, b) => a + (b - m) ** 2, 0) / 59);
  assert.ok(Math.abs(spot.sigma10(V, NOW) - sd) < 1e-15, 'the sample standard deviation of the sixty changes');
  const strike = idx(NOW) * Math.exp(-0.5 * sd * Math.sqrt(8));
  const r = spot.modelYes({ venues: V, t: NOW, strike, secondsLeft: 120 });
  assert.ok(Math.abs(r.pYes - spot.phi(0.5)) < 1e-9, 'half a scaled standard deviation above the strike: ' + r.pYes);
  // Too little history, no movement or a bad strike: no reading.
  const short = {}; for (const k of Object.keys(V)) short[k] = V[k].filter((x) => x.t >= NOW - 250000);
  assert.strictEqual(spot.sigma10(short, NOW), null, 'fewer than 30 changes');
  assert.strictEqual(spot.sigma10({ a: Array.from({ length: 700 }, (_, s) => ({ t: NOW - s * 1000, p: 100 })).reverse() }, NOW), null, 'a flat index has no volatility to scale by');
  for (const bad of [0, -1, NaN, undefined]) assert.strictEqual(spot.modelYes({ venues: V, t: NOW, strike: bad, secondsLeft: 120 }), null);
};

// A fake of the one allowed venue's public trade list, in the documented shape (error array, result with the pair key and `last`, rows of [price, volume, time, ...]).
function venueFetch(V, o = {}) {
  const calls = [];
  const fn = async (url, init) => {
    calls.push({ url, init });
    const u = new URL(url), reply = (body, status, len) => ({ status: status || 200, headers: { get: (h) => (h === 'content-length' && len ? String(len) : null) }, text: async () => (typeof body === 'string' ? body : JSON.stringify(body)) });
    if (o.throws) throw new Error('network down');
    if (o.status) return reply({}, o.status);
    if (o.declared) return reply({}, 200, o.declared);
    if (u.hostname !== 'api.kraken.com') throw new Error('unexpected host ' + u.hostname);
    return reply(o.body || { error: [], result: { XXBTZUSD: V.kraken.map((x) => [String(x.p), '0.01', x.t / 1000, 'b', 'm', '', 1]), last: '1' } });
  };
  return { fn, calls };
}
const market = (extra) => Object.assign({ ticker: T, status: 'active', close_time: new Date(CLOSE).toISOString(), floor_strike: 99990, strike_type: 'greater_or_equal' }, extra || {});
gates['CB6 NOT ACTIVATABLE as built: one allowed venue against a rule that needs three, so the production reader returns null and makes no request; no other venue is named anywhere in the server code'] = async () => {
  const V = tape(NOW), f = venueFetch(V);
  assert.deepStrictEqual(spot.SPOT_HOSTS.slice(), ['api.kraken.com'], 'the only host the reader may reach');
  assert.deepStrictEqual(spot.VENUES_ALLOWED.slice(), ['kraken']); assert.strictEqual(spot.VENUES_REQUIRED, 3, 'the registered rule needs three venues');
  assert.ok(Object.isFrozen(spot.SPOT_HOSTS) && Object.isFrozen(spot.VENUES_ALLOWED));
  const r = await spot.modelForMarket({ fetchFn: f.fn, series: 'KXBTC15M', market: market(), side: 'yes', now: NOW });
  assert.strictEqual(r, null, 'no reading, so no order, even if the probe switch were flipped'); assert.strictEqual(f.calls.length, 0, 'and not one request is made');
  for (const file of ['functions/kalshiSpotIndexLib.js', 'functions/kalshiSlotLib.js', 'functions/kalshiSlotRunLib.js', 'functions/index.js']) {
    assert.ok(!/coinbase|bitstamp/i.test(read(file)), file + ' must not name a venue the owner has ruled out for live probes');
  }
  const src = read('functions/kalshiSpotIndexLib.js').replace(/\/\/.*$/gm, '');
  assert.ok(!/require\(|process\.env|setTimeout|setInterval|Date\.now|Math\.random|firestore|portfolio|\.pem|keyId/.test(src), 'no import, environment, timer, clock, randomness, database, account path or key');
  assert.ok(/const modelForMarket = \(args\) => modelWith\(VENUES_REQUIRED, args\);/.test(src), 'the production entry point cannot be handed a lower venue count');
  assert.ok(!/modelWith|_testOnly/.test(read('functions/index.js')) && !/modelWith|_testOnly\.krakenTrades/.test(read('functions/kalshiSlotRunLib.js')), 'the wiring uses only the production entry point');
  assert.ok(spot.SPOT_TIMEOUT_MS <= 2000 && spot.SPOT_TOTAL_MS <= 6000 && spot.SPOT_MAX_PAGES.kraken <= 4, 'bounded well inside the engine\'s 20 s stale limit');
};

gates['CB7 the venue reader itself: one pinned public host, GET, no credential, redirects refused, both abort timers, and null on anything it cannot read'] = async () => {
  const V = tape(NOW), K = spot._testOnly.krakenTrades, overall = AbortSignal.timeout(5000);
  const f = venueFetch(V), got = await K(f.fn, NOW - 600000, NOW, overall);
  assert.ok(got && got.complete === true && got.trades.length > 600 && got.trades[0].t < got.trades[1].t, 'the ten minutes are read, oldest first');
  assert.strictEqual(f.calls.length, 1);
  const c = f.calls[0], u = new URL(c.url);
  assert.ok(u.protocol === 'https:' && u.hostname === 'api.kraken.com' && u.pathname === '/0/public/Trades' && u.searchParams.get('pair') === 'XBTUSD', c.url);
  assert.strictEqual(c.init.method, 'GET'); assert.strictEqual(c.init.redirect, 'error'); assert.ok(c.init.signal, 'an abort timer on the request'); assert.strictEqual(c.init.body, undefined);
  assert.ok(!Object.keys(c.init.headers).some((h) => /auth|key|cookie|token|sign/i.test(h)), 'no header that could carry a credential');
  assert.ok(/since=" \+ encodeURIComponent\(since\), overall\)/.test(read('functions/kalshiSpotIndexLib.js')), 'the venue call shares the overall abort timer');
  assert.ok(got.trades.every((x) => x.t <= NOW), 'nothing after the look');
  const cut = await K(venueFetch(V).fn, NOW - 900000, NOW - 300000, overall);
  assert.ok(cut.trades.every((x) => x.t <= NOW - 300000), 'trades after the look are dropped, so the model can never see its own future');
  for (const o of [{ throws: true }, { status: 429 }, { status: 301 }, { declared: spot.SPOT_MAX_BYTES + 1 }, { body: { error: ['EGeneral:Too many requests'], result: {} } },
    { body: { error: [], result: { XXBTZUSD: [['abc', '1', 'x']], last: '1' } } }, { body: { error: [], result: { last: '1' } } }, { body: 'not json' }, { body: [] }]) {
    assert.strictEqual(await K(venueFetch(V, o).fn, NOW - 600000, NOW, overall), null, JSON.stringify(o).slice(0, 60));
  }
  assert.strictEqual(await spot.spotGet(f.fn, 'https://evil.example/0/public/Trades'), null, 'any other host is refused before a request');
  assert.strictEqual(await spot.spotGet(f.fn, 'http://api.kraken.com/0/public/Trades'), null, 'plain http is refused');
  assert.strictEqual(await spot.spotGet(f.fn, 'https://user:pw@api.kraken.com/0/public/Trades'), null, 'a URL carrying a login is refused');
  // The model on a caller-chosen venue count (test only): it reads the market and the side as documented, and still fails closed.
  const M = spot._testOnly.modelWith, go = (m, extra, o) => M(1, Object.assign({ fetchFn: venueFetch(V, o).fn, series: 'KXBTC15M', market: m || market(), side: 'yes', now: NOW }, extra || {}));
  const y = await go(), n = await go(null, { side: 'no' });
  assert.ok(y && y.venues === 1 && y.pYes > 0.5 && y.pYes < 1 && Math.abs(n.pSide - (1 - y.pYes)) < 1e-12, JSON.stringify(y));
  for (const m of [market({ strike_type: 'between' }), market({ strike_type: undefined }), market({ floor_strike: null }), market({ floor_strike: 0 }), market({ close_time: 'x' })]) assert.strictEqual(await go(m), null);
  assert.strictEqual(await go(null, { series: 'KXETH15M' }), null, 'Bitcoin only'); assert.strictEqual(await go(null, { side: 'maybe' }), null);
  assert.strictEqual(await go(null, null, { throws: true }), null); assert.strictEqual(await M(0, {}), null); assert.strictEqual(await M(2, { fetchFn: f.fn }), null, 'more venues than are allowed: null');
  assert.strictEqual(await spot.modelForMarket(null), null); assert.strictEqual(await spot.modelForMarket({}), null);
};

// ---- the engine end to end, on a fake exchange and a fake store (the same shape as test/event830SlotGates.test.js) ----
const pem = crypto.generateKeyPairSync('ed25519').privateKey.export({ type: 'pkcs8', format: 'pem' });
const iso = (ms) => new Date(ms).toISOString();
const tick = () => new Promise((r) => setImmediate(r));
function world(o = {}) {
  const db = { slot: new Map(), locks: new Map(), latches: {}, queue: Promise.resolve() };
  db.tx = (fn) => { const p = db.queue.then(fn); db.queue = p.catch(() => {}); return p; };
  const clone = (x) => JSON.parse(JSON.stringify(x));
  for (const t of o.slotOrders || []) db.slot.set(t.id, clone(t));
  const store = {
    async halted() { return false; }, async hasUnresolved() { return false; }, async l1HasUnresolved() { return false; },
    async killLatches() { return clone(db.latches); }, async allSlotOrders() { return [...db.slot.values()].map(clone); }, async l1Recent() { return []; },
    async runSlotEntry({ ticker, decide }) {
      return db.tx(async () => {
        const lock = db.locks.get(ticker) || null; await tick();
        const r = decide(lock ? clone(lock) : null, [...db.slot.values()].map(clone), []);
        if (!r.allowed) return { created: false, reason: r.reason };
        if (!lock) db.locks.set(ticker, r.lock);
        db.slot.set(r.record.id, clone(r.record));
        return { created: true, record: clone(r.record) };
      });
    },
    async updateSlotOrder(id, patch) { Object.assign(db.slot.get(id), clone(patch)); }, async killStrategy(id, info) { db.latches[id] = clone(info); },
  };
  const m = Object.assign({ ticker: T, status: 'active', close_time: iso(CLOSE), yes_bid_dollars: '0.1800', yes_ask_dollars: '0.2000', yes_bid_size_fp: '500.00', yes_ask_size_fp: '500.00', exchange_index: 2, floor_strike: 99990, strike_type: 'greater_or_equal' }, o.market || {});
  const calls = [], posts = [], skips = [], asked = [];
  const fetchFn = async (url, init) => {
    calls.push(init.method + ' ' + url.replace(/^.*\/trade-api\/v2/, '').split('?')[0]);
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [] });
    if (url.includes('/orderbook')) return reply(404, {});
    if (url.includes('/markets/')) return reply(200, { market: m });
    if (init.method === 'POST') { const b = JSON.parse(init.body); posts.push(b); return reply(201, { order_id: 'ord-1', fill_count: String(b.count), remaining_count: '0.00', average_fill_price: '0.2000' }); }
    throw new Error('unexpected ' + url);
  };
  const args = { session: { active: true }, now: NOW, enabled: true, active: true, store, keyId: 'k', pem, fetchFn, clock: () => NOW + 1500,
    quotes: [{ series: 'KXBTC15M', m: { ticker: T, status: 'active', close_time: iso(CLOSE) } }], setSession: async () => {}, logEvent: async () => {}, recordSkip: async (d) => { skips.push(d); },
    shared: { sizeBase: 800, balanceBody: { balance: 50000 }, risk: { worst: 0 }, floor: -96, recentList: [], slotOrders: [], since: NOW - 24 * 3600 * 1000 } };
  if (o.spotModel !== undefined) args.spotModel = async (q) => { asked.push(q); return typeof o.spotModel === 'function' ? o.spotModel(q) : o.spotModel; };
  return { db, calls, posts, skips, asked, args };
}
const ENG = () => run._testOnly.makeRunners(ON);
gates['CB8 end to end: a model edge buys ONE contract of the cheap side at the price seen, immediate-or-cancel, held, and the order records what the model said'] = async () => {
  const w = world({ spotModel: { pSide: 0.29, index: 100010, sigma: 0.0002, steps: 13.8, venues: 3, strike: 99990 } });
  const out = await ENG().runSlotTick(w.args);
  assert.strictEqual(w.posts.length, 1, JSON.stringify(out));
  const b = w.posts[0];
  assert.strictEqual(Number(b.count), 1); assert.strictEqual(b.side, 'bid'); assert.strictEqual(b.time_in_force, 'immediate_or_cancel'); assert.strictEqual(b.post_only, undefined);
  assert.ok(Math.abs(Number(b.price) - 0.2) < 1e-9, 'the limit is the 20c ask, no slip: ' + b.price);
  const d = [...w.db.slot.values()][0];
  assert.strictEqual(d.slotId, 'CFRTIBTC'); assert.strictEqual(d.count, 1); assert.strictEqual(d.modelEdge, 0.09); assert.strictEqual(d.model.venues, 3); assert.strictEqual(w.db.locks.get(T).by, 'SLOT:CFRTIBTC');
  assert.ok(d.maxCost <= 0.33, 'worst loss on one order is about 32c: ' + d.maxCost);
  assert.strictEqual(w.asked.length, 1); assert.strictEqual(w.asked[0].side, 'yes'); assert.strictEqual(w.asked[0].now, NOW + 1500, 'the look is the clock at the read, not the start of the minute');
  assert.ok(!('keyId' in w.asked[0]) && !('pem' in w.asked[0]), 'the model reader is never handed the key');
  // The NO side when NO is the cheap one.
  const n = world({ market: { yes_bid_dollars: '0.8300', yes_ask_dollars: '0.8500' }, spotModel: { pSide: 0.3 } });
  await ENG().runSlotTick(n.args);
  assert.strictEqual(n.posts.length, 1); assert.strictEqual(n.posts[0].side, 'ask', 'a NO buy is sent as a YES ask'); assert.strictEqual(n.asked[0].side, 'no');
  assert.ok(Math.abs(Number(n.posts[0].price) - 0.83) < 1e-9);
};

gates['CB9 end to end: no reader, an unreadable reading, a small edge, a wide spread, a dear price or a spent budget sends nothing, and each leaves a skip record'] = async () => {
  const none = async (o, code) => {
    const w = world(o); await ENG().runSlotTick(w.args);
    assert.strictEqual(w.posts.length, 0, code + ': an order went out'); assert.strictEqual(w.db.slot.size - (o.slotOrders || []).length, 0);
    assert.ok(w.skips.some((s) => s.strategy === 'CFRTIBTC' && s.reason === code), code + ' expected, got ' + JSON.stringify(w.skips.map((s) => s.reason)));
    return w;
  };
  await none({}, 'model_unreadable');                                                    // index.js handed no reader
  await none({ spotModel: null }, 'model_unreadable');
  await none({ spotModel: () => { throw new Error('boom'); } }, 'model_unreadable');
  for (const bad of [{ pSide: NaN }, { pSide: 1.2 }, { pSide: -0.1 }, { pSide: '0.4' }, {}]) await none({ spotModel: bad }, 'model_unreadable');
  await none({ spotModel: { pSide: 0.24 } }, 'model_edge_below');                         // 4c over a 20c price
  const wide = await none({ market: { yes_bid_dollars: '0.1500', yes_ask_dollars: '0.2000' }, spotModel: { pSide: 0.9 } }, 'spread_wide');
  assert.strictEqual(wide.asked.length, 0, 'a wide spread is refused before the model is even asked');
  const dear = await none({ market: { yes_bid_dollars: '0.3900', yes_ask_dollars: '0.4000' }, spotModel: { pSide: 0.9 } }, 'price_out_of_band');
  assert.strictEqual(dear.asked.length, 0);
  const day = Date.parse('2026-11-12T00:00:00Z');
  await none({ slotOrders: Array.from({ length: 19 }, (_, j) => done(j, -0.27, day + j * 900000)), spotModel: { pSide: 0.9 } }, 'killed');
};

gates['CB10 with the switch off the production engine makes no call for the probe, index.js hands the reader no key, and the docs say unproven'] = async () => {
  const w = world({ spotModel: { pSide: 0.9 } });
  w.args.quotes = [{ series: 'KXBTC15M', m: { ticker: T, status: 'active', close_time: iso(CLOSE - 60000) } }];   // 118 s left: outside OICORE's window too, so the production tick has no job
  const out = await run.runSlotTick(w.args);
  assert.strictEqual(w.calls.length, 0, JSON.stringify(out)); assert.strictEqual(w.asked.length, 0); assert.strictEqual(w.posts.length, 0);
  const idx = read('functions/index.js');
  assert.ok(/spotModel: \(q\) => spotIndexLib\.modelForMarket\(\{ \.\.\.q, fetchFn: fetch \}\),/.test(idx), 'the reader gets the public fetch and what the engine passes, nothing else');
  const runSrc = read('functions/kalshiSlotRunLib.js');
  assert.ok(/args\.spotModel\(\{ series, market: m, side, now: lookAt \}\)/.test(runSrc), 'the engine passes the market, the side and the clock: no key, no store');
  assert.ok(/hasOwnProperty\.call\(s\.entry, "modelEdgeMin"\)/.test(runSrc), 'the reader is asked only for a strategy with a model line');
  const spec = read('docs/probes/PROBE_SPEC_CFRTIBTC.md'), reg = read('kalshi-scalper/README.md');
  assert.ok(/UNPROVEN/.test(spec) && /OFF by default/i.test(spec) && /^## (\d+\. )?Kill/m.test(spec) && /^## (\d+\. )?Return/m.test(spec) && /popup/i.test(spec), 'the spec states unproven, off by default, a kill rule, a return rule and the popup text');
  assert.ok(/SLOT-CFRTIBTC/.test(reg) && /DRAFT/.test(reg.slice(reg.indexOf('SLOT-CFRTIBTC'), reg.indexOf('SLOT-CFRTIBTC') + 1500)), 'the pre-registration exists and is marked a draft');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.stack ? e.stack.split('\n').slice(0, 5).join(' | ') : e)); }
  }
  process.exit(failed ? 1 : 0);
})();

'use strict';
// Scenarios for the second slot's OFF-EQUIVALENCE proof (docs/SECOND_SLOT_WIRING.md section 0 and 9, gate SW0).
// Each scenario runs a REAL function of kalshiLiveLib against a fake store and a scripted exchange and records EVERYTHING it did: every store call (name, arguments, what it returned),
// every request to the exchange (method, url, body; headers are left out because they carry a wall-clock signature), every session write and every event, and the function's return value.
// fixtures/offEquivalence.json holds that record as produced by the library BEFORE the slot wiring was added (generated from `git show <commit before the wiring>:functions/kalshiLiveLib.js`).
// The gate replays the same scenarios against the current library with the slot off and requires the record to be identical: same reads, same writes, same orders, same order.
// `node test/fixtures/offEquivalenceScenarios.js <path to a kalshiLiveLib.js> > out.json` regenerates a record from any copy of the library.
const crypto = require('crypto');
const path = require('path');

const NOW = Date.parse('2026-10-07T14:00:00Z');
const iso = (ms) => new Date(ms).toISOString();
// A fixed key so the scenarios do not depend on randomness (signatures are not recorded anyway).
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const T = 'KXBTC15M-26OCT071415-15', GT = 'KXGOLD15M-26OCT071415-15';
const leftFor = (series) => (['KXXRP15M', 'KXNATGAS15M'].includes(series) ? 600000 : 360000);

function recorder() {
  const log = [];
  const rec = (kind, data) => log.push({ kind, ...data });
  // Wrap every function property of a store so each call and its result (or error) is logged in order.
  const wrapStore = (store) => {
    const out = {};
    for (const k of Object.keys(store)) {
      out[k] = async (...a) => {
        try { const r = await store[k](...a); rec('store', { call: k, args: a, ret: r === undefined ? null : r }); return r; }
        catch (e) { rec('store', { call: k, args: a, threw: String(e.message) }); throw e; }
      };
    }
    return out;
  };
  const wrapFetch = (fetchFn) => async (url, o) => {
    rec('fetch', { method: o.method, url, body: o.body ? JSON.parse(o.body) : null });
    return fetchFn(url, o);
  };
  return { log, rec, wrapStore, wrapFetch };
}

const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
const climb = (n) => [0.5, 0.58, 0.66, 0.74, 0.82, 0.91].map((m, i, arr) => ({ end_period_ts: Math.floor(NOW / 1000) - 60 * (arr.length - 1 - i), yes_bid: { close_dollars: String(m - 0.01) }, yes_ask: { close_dollars: String(m + 0.01) }, price: { close_dollars: String(m) } }));

function l1World(opts = {}) {
  const r = recorder();
  const docs = new Map(Object.entries(opts.docs || {}).map(([k, v]) => [k, { ...v }]));
  const sess = Object.assign({ active: true, until: NOW + 3600000, ordersSent: 0, startCash: 100 }, opts.session || {});
  const base = {
    async halted() { return opts.halted === true; },
    async hasUnresolved() { return opts.unresolved === true || [...docs.values()].some((d) => d.status === 'sending' || d.status === 'unknown'); },
    async createTest(id, data) { if (docs.has(id)) return false; docs.set(id, { ...data }); return true; },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
    async sessionTrades(since) { if (opts.tradesThrow) throw new Error('down'); return [...docs.entries()].filter(([, d]) => d.ts >= since).map(([id, d]) => ({ id, ...d })); },
  };
  // Test hooks for the slot wiring gates (never set by the recorded scenarios): extra store methods, built over the same documents.
  if (opts.extraStore) Object.assign(base, opts.extraStore(docs));
  if (opts.cached) base.sessionTradesCached = async (since, now) => base.sessionTrades(since);
  const store = r.wrapStore(base);
  const fetchFn = r.wrapFetch(async (url, o) => {
    if (url.includes('/portfolio/positions') && opts.positions) return opts.positions(url);
    if (url.includes('/candlesticks')) return reply(200, { candlesticks: opts.candles || climb() });
    if (url.includes('/markets/')) {
      const tk = decodeURIComponent(url.split('/markets/')[1].split('?')[0]);
      const over = (opts.fresh && opts.fresh[tk]) || {};
      return reply(200, { market: { status: 'active', close_time: iso(NOW + leftFor(tk.split('-')[0])), exchange_index: tk.includes('KXGOLD') ? 0 : 2, yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100', ...(opts.results && opts.results[tk] ? { result: opts.results[tk] } : {}), ...over } });
    }
    if (url.endsWith('/portfolio/balance')) return reply(200, { balance_breakdown: [{ balance: '70.0000', exchange_index: 2 }, { balance: '30.0000', exchange_index: 0 }] });
    if (url.includes('/portfolio/orders')) return reply(200, { orders: opts.existing || [] });
    if (url.includes('/portfolio/fills')) return reply(200, { fills: opts.fills || [] });
    if (o.method === 'POST') {
      if (opts.post) return reply(opts.post.status, opts.post.body);
      return reply(201, { order_id: 'ord-1', fill_count: '1.00', remaining_count: '0.00', average_fill_price: '0.9100', average_fee_paid: '0.0057' });
    }
    throw new Error('unexpected ' + o.method + ' ' + url);
  });
  const setSession = async (p) => { r.rec('session', { patch: p }); Object.assign(sess, p); };
  const logEvent = async (e) => { r.rec('event', { e }); };
  const common = { session: sess, now: NOW, setSession, logEvent, active: true, enabled: true, store, keyId: 'live-key', pem, fetchFn, pausedSeries: [] };
  return { r, docs, sess, common };
}
const q = (series, ticker, over) => ({ series, m: Object.assign({ ticker, status: 'active', close_time: iso(NOW + leftFor(series)), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' }, over || {}) });
const settledLoss = (id, over) => ({ strategy: 'L1', ticker: 'KXBTC15M-26OCT071345-15', series: 'KXBTC15M', side: 'yes', count: 1, fillCount: '1', maxCost: 0.94, price: 0.91, status: 'filled', ts: NOW - 3600000, settled: true, result: 'no', settledPnl: -0.94, ...over });

async function runScenario(name, fn, r) {
  let ret, threw = null;
  try { ret = await fn(); } catch (e) { threw = String(e.message); }
  // `at` is a wall-clock stamp the library takes itself (logRise); it is non-deterministic, so it is masked; sentAtMs and answeredAtMs (Oct 31, 2026, the send-time log) are wall-clock reads around the order POST and are masked the same way.
  const mask = (k, v) => ((k === 'at' && typeof v === 'string') || ((k === 'sentAtMs' || k === 'answeredAtMs') && typeof v === 'number') ? '<wall clock>' : v);
  return { name, ret: ret === undefined ? null : JSON.parse(JSON.stringify(ret, mask)), threw, log: JSON.parse(JSON.stringify(r.log, mask)) };
}

async function runAll(libPath) {
  const live = require(libPath);
  const out = [];
  const tickScenario = async (name, opts, tickOver, quotes) => {
    const w = l1World(opts);
    out.push(await runScenario(name, () => live.runL1Tick({ ...w.common, quotes: quotes || [q('KXBTC15M', T)], ...(tickOver || {}) }), w.r));
  };
  await tickScenario('l1 bitcoin happy', {});
  await tickScenario('l1 bitcoin happy cached reads', { cached: true });
  await tickScenario('l1 halted', { halted: true });
  await tickScenario('l1 unresolved', { unresolved: true });
  await tickScenario('l1 orders unreadable', { tradesThrow: true });
  await tickScenario('l1 no session', { session: { active: false } });
  await tickScenario('l1 loss stop', { docs: { a: settledLoss('a'), b: settledLoss('b'), c: settledLoss('c'), d: settledLoss('d'), e: settledLoss('e'), f: settledLoss('f'), g: settledLoss('g'), h: settledLoss('h'), i: settledLoss('i'), j: settledLoss('j'), k: settledLoss('k'), l: settledLoss('l'), m: settledLoss('m'), n: settledLoss('n') } });
  await tickScenario('l1 unsettled order resolved by market', { docs: { 'L1-X': settledLoss('x', { settled: false, result: undefined, settledPnl: undefined, ticker: 'KXBTC15M-26OCT071400-15' }) }, results: { 'KXBTC15M-26OCT071400-15': 'no' } });
  await tickScenario('l1 post 409', { post: { status: 409, body: { error: 'exists' } } });
  await tickScenario('l1 post 500', { post: { status: 500, body: { error: 'down' } } });
  await tickScenario('l1 post 400', { post: { status: 400, body: { error: 'bad' } } });
  await tickScenario('l1 gold sizing with window usage', {
    session: { sizing: true },
    docs: { 'L1-KXBTC15M-26OCT071415-15': { strategy: 'L1', ticker: 'KXBTC15M-26OCT071415-15', series: 'KXBTC15M', side: 'yes', count: 1, fillCount: '1', maxCost: 0.94, price: 0.91, status: 'filled', ts: NOW - 120000, settled: false } },
    results: {},
  }, {
    sizingState: { cap: 5, base: 100, saved: 0, pool: 0, cum: 0, hwm: 0, reviewedAt: NOW - 1000, appliedTs: NOW - 5000 },
    setSizingState: async (s) => { out.push({ name: 'setSizingState (gold sizing)', ret: s, threw: null, log: [] }); },
    updateProbeRecord: async (fn) => fn({}).record,
  }, [q('KXGOLD15M', GT)]);
  await tickScenario('l1 two markets one window', {}, {}, [q('KXBTC15M', T), q('KXGOLD15M', GT)]);

  // botRisk
  {
    const w = l1World({ docs: { a: settledLoss('a'), 'L1-open': settledLoss('o', { settled: false, result: undefined, settledPnl: undefined, ticker: 'KXBTC15M-26OCT071300-15' }), x: { ...settledLoss('x'), result: 'exit', settledPnl: -0.5 } }, results: { 'KXBTC15M-26OCT071300-15': 'yes' } });
    out.push(await runScenario('botRisk store read', () => live.botRisk({ store: w.common.store, since: NOW - 7200000, fetchFn: w.common.fetchFn, nowMs: NOW, keyId: 'k', pem }), w.r));
    const w2 = l1World({ results: { 'KXBTC15M-26OCT071300-15': 'no' } });
    const orders = [settledLoss('a', { id: 'a' }), settledLoss('o', { id: 'L1-o', settled: false, result: undefined, settledPnl: undefined, ticker: 'KXBTC15M-26OCT071300-15' })];
    w2.docs.set('L1-o', { ...orders[1] });
    out.push(await runScenario('botRisk shared list', () => live.botRisk({ store: w2.common.store, since: 0, fetchFn: w2.common.fetchFn, nowMs: NOW, orders, keyId: 'k', pem }), w2.r));
  }
  // closedByHand and settleOpenOrders
  {
    const fills = [{ ticker: T, action: 'sell', side: 'yes', order_id: 'other', created_time: iso(NOW - 1000), count_fp: '1.00' }, { ticker: T, action: 'sell', side: 'yes', order_id: 'o1', created_time: iso(NOW - 1000), count_fp: '1.00' }];
    const w = l1World({ fills });
    const t = { ticker: T, side: 'yes', count: 1, fillCount: '1', orderId: 'o1', ts: NOW - 60000 };
    out.push(await runScenario('closedByHand', () => live.closedByHand({ fetchFn: w.common.fetchFn, keyId: 'k', pem, t, nowMs: NOW }), w.r));
    const w2 = l1World({ fills, results: { [T]: 'yes' }, docs: { 'L1-a': { strategy: 'L1', ticker: T, side: 'yes', count: 1, fillCount: '1', maxCost: 0.94, orderId: 'o1', status: 'filled', ts: NOW - 60000, settled: false }, 'L1-h': { strategy: 'L1', ticker: T, side: 'no', count: 1, fillCount: '1', maxCost: 0.94, orderId: 'o9', status: 'filled', ts: NOW - 60000, settled: true, result: 'hand' } } });
    const base = w2.common.store;
    const store = w2.r.wrapStore({ async openFilled() { return [...w2.docs.entries()].filter(([, d]) => d.settled !== true).map(([id, d]) => ({ id, ...d })); }, async handOrders() { return [...w2.docs.entries()].filter(([, d]) => d.result === 'hand').map(([id, d]) => ({ id, ...d })); }, async updateTest(id, patch) { Object.assign(w2.docs.get(id), patch); } });
    out.push(await runScenario('settleOpenOrders', () => live.settleOpenOrders({ store, fetchFn: w2.common.fetchFn, nowMs: NOW, keyId: 'k', pem }), w2.r));
    const w3 = l1World({ results: { [T]: 'yes' }, docs: { 'L1-a': { strategy: 'L1', ticker: T, side: 'yes', count: 1, fillCount: '1', maxCost: 0.94, orderId: 'o1', status: 'filled', ts: NOW - 60000, settled: false } } });
    const store3 = w3.r.wrapStore({ async openFilled() { return [...w3.docs.entries()].filter(([, d]) => d.settled !== true).map(([id, d]) => ({ id, ...d })); }, async updateTest(id, patch) { Object.assign(w3.docs.get(id), patch); } });
    out.push(await runScenario('settleOpenOrders no key', () => live.settleOpenOrders({ store: store3, fetchFn: w3.common.fetchFn, nowMs: NOW }), w3.r));
  }
  // The exit watch
  {
    const mkExit = (o = {}) => {
      const r = recorder(), docs = new Map(), closing = new Map();
      docs.set('L1-' + T, { strategy: 'L1', ticker: T, series: 'KXBTC15M', side: 'yes', count: 20, fillCount: '20', maxCost: 18.7, addonCost: 7.5, price: 0.93, status: 'filled', ts: NOW - 300000, settled: false });
      const store = r.wrapStore({
        async recentFilled(since) { return [...docs.entries()].filter(([, d]) => d.status === 'filled' && d.ts >= since).map(([id, d]) => ({ id, ...d })); },
        async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
        async claimClose(ticker, who, now, ttl) { const c = closing.get(ticker); if (c && c.by !== who && now - c.at < ttl) return false; closing.set(ticker, { by: who, at: now }); return true; },
        async claimExit(id, tries) { const d = docs.get(id); if (d.exitStatus === 'sending' || (Number(d.exitTries) || 0) !== tries || d.settled === true) return false; d.exitStatus = 'sending'; d.exitTries = tries + 1; return true; },
      });
      const fetchFn = r.wrapFetch(async (url, init) => {
        if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [{ ticker: T, position_fp: '20.00' }] });
        if (url.includes('/markets/')) return reply(200, { market: { status: 'active', close_time: iso(NOW + 200000), yes_bid_dollars: o.bid || '0.2400', yes_ask_dollars: '0.2600', exchange_index: 2 } });
        if (init.method === 'POST') return reply(201, { order_id: 'x-1', fill_count: '20.00', remaining_count: '0.00', average_fill_price: '0.2400' });
        throw new Error('unexpected');
      });
      return { r, store, fetchFn };
    };
    const a = mkExit();
    out.push(await runScenario('exit watch sells at 24c', () => live.runExitWatch({ store: a.store, fetchFn: a.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, setSession: async (p) => a.r.rec('session', { patch: p }), logEvent: async (e) => a.r.rec('event', { e }) }), a.r));
    const b = mkExit({ bid: '0.8000' });
    out.push(await runScenario('exit watch holds at 80c', () => live.runExitWatch({ store: b.store, fetchFn: b.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, setSession: async () => {}, logEvent: async (e) => b.r.rec('event', { e }) }), b.r));
    const c = mkExit();
    out.push(await runScenario('exit watch switch off', () => live.runExitWatch({ store: c.store, fetchFn: c.fetchFn, keyId: 'k', pem, now: NOW, enabled: false, setSession: async () => {}, logEvent: async (e) => c.r.rec('event', { e }) }), c.r));
    const d = mkExit();
    out.push(await runScenario('exit idle outside buy minutes', () => live.exitWatchIdle({ store: d.store, now: Date.parse('2026-10-07T14:01:00Z') }), d.r));
    const e = mkExit();
    out.push(await runScenario('exit idle inside buy minutes', () => live.exitWatchIdle({ store: e.store, now: Date.parse('2026-10-07T14:09:00Z') }), e.r));
  }
  // Flatten
  {
    const mkFlat = (o = {}) => {
      const r = recorder(), held = new Map();
      const store = r.wrapStore({ async claimClose(ticker, who, now, ttl) { const c = held.get(ticker); if (c && c.by !== who && now - c.at < ttl) return false; held.set(ticker, { by: who, at: now }); return true; } });
      const fetchFn = r.wrapFetch(async (url, init) => {
        if (url.includes('/portfolio/positions')) {
          const tk = new URL(url).searchParams.get('ticker');
          const all = [{ ticker: T, position_fp: '3.00' }, { ticker: GT, position_fp: '-2.00' }];
          return reply(200, { market_positions: tk ? all.filter((x) => x.ticker === tk) : all });
        }
        if (url.includes('/markets/')) return reply(200, { market: { status: 'active', exchange_index: 2 } });
        if (init.method === 'POST') { const b = JSON.parse(init.body); return reply(o.postStatus || 201, o.postBody || { order_id: 'o', fill_count: b.count, remaining_count: '0.00', average_fill_price: '0.5000' }); }
        throw new Error('unexpected');
      });
      return { r, store, fetchFn };
    };
    const a = mkFlat();
    out.push(await runScenario('flatten two positions', () => live.flattenAll({ fetchFn: a.fetchFn, keyId: 'k', pem, now: NOW, store: a.store }), a.r));
    const b = mkFlat({ postStatus: 500, postBody: { e: 1 } });
    out.push(await runScenario('flatten ambiguous answer', () => live.flattenAll({ fetchFn: b.fetchFn, keyId: 'k', pem, now: NOW, store: b.store }), b.r));
  }
  return out;
}

module.exports = { runAll, NOW, T, GT, pem, q, l1World, climb, settledLoss, reply, iso, leftFor, recorder };
if (require.main === module) {
  runAll(path.resolve(process.argv[2])).then((o) => { process.stdout.write(JSON.stringify(o, null, 1) + '\n'); }).catch((e) => { console.error(e); process.exit(1); });
}

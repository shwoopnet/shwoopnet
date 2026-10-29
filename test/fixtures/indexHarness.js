'use strict';
// Harness for the second slot's OFF-EQUIVALENCE proof at the level of functions/index.js (docs/SECOND_SLOT_WIRING.md step B3).
// It loads a copy of index.js with every firebase package replaced by a stub (the scheduled and callable functions come back as plain functions), runs the three functions the slot touches
// (kalshiLiveArmed, kalshiLiveExit, kalshiFlattenAll) against an in-memory Firestore and a scripted exchange, and records EVERY database operation, every request to a Kalshi host and every
// console line, in order. test/fixtures/offEquivalenceIndex.json holds the record produced by index.js as it stood BEFORE the slot was wired; kalshiSlotIndexWiringGates.test.js replays it.
// Regenerate from any copy of index.js: `node test/fixtures/indexHarness.js <path to an index.js that sits in functions/> > out.json`.
// Nothing here talks to Firebase or Kalshi: both are fakes, and the key is a throwaway generated in memory.
const crypto = require('crypto');
const Module = require('module');
const path = require('path');

const NOW = Date.parse('2026-10-07T14:03:00Z');
const ed = crypto.generateKeyPairSync('ed25519');
const PEM = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const T = 'KXBTC15M-26OCT071415-15';

function fakeDb(seed, log) {
  const data = new Map(Object.entries(seed || {}).map(([k, v]) => [k, JSON.parse(JSON.stringify(v))]));
  const J = (x) => JSON.parse(JSON.stringify(x === undefined ? null : x));
  const snap = (id, v) => ({ id, exists: v !== undefined, data: () => J(v) });
  const docRef = (col, id) => ({
    get: async () => { log.push(['get', col + '/' + id]); return snap(id, data.get(col + '/' + id)); },
    set: async (v, o) => { log.push(['set', col + '/' + id, J(v), o || null]); data.set(col + '/' + id, o && o.merge ? { ...(data.get(col + '/' + id) || {}), ...J(v) } : J(v)); },
    update: async (v) => { log.push(['update', col + '/' + id, J(v)]); data.set(col + '/' + id, { ...(data.get(col + '/' + id) || {}), ...J(v) }); },
    create: async (v) => { log.push(['create', col + '/' + id, J(v)]); if (data.has(col + '/' + id)) { const e = new Error('ALREADY_EXISTS'); e.code = 6; throw e; } data.set(col + '/' + id, J(v)); },
    delete: async () => { log.push(['delete', col + '/' + id]); data.delete(col + '/' + id); },
  });
  const query = (col, conds, lim, ord) => ({
    where: (f, op, v) => query(col, conds.concat([[f, op, v]]), lim, ord),
    limit: (n) => query(col, conds, n, ord),
    orderBy: (f, d) => query(col, conds, lim, [f, d]),
    get: async () => {
      log.push(['query', col, conds, lim || null, ord || null]);
      let rows = [...data.entries()].filter(([k]) => k.startsWith(col + '/')).map(([k, v]) => [k.slice(col.length + 1), v]);
      for (const [f, op, v] of conds) rows = rows.filter(([, d]) => (op === '==' ? d[f] === v : op === '>=' ? d[f] >= v : op === 'in' ? v.includes(d[f]) : false));
      if (ord) rows.sort((a, b) => (ord[1] === 'desc' ? b[1][ord[0]] - a[1][ord[0]] : a[1][ord[0]] - b[1][ord[0]]));
      if (lim) rows = rows.slice(0, lim);
      return { empty: rows.length === 0, size: rows.length, docs: rows.map(([id, v]) => snap(id, v)) };
    },
  });
  return {
    collection: (col) => ({ doc: (id) => docRef(col, id), add: async (v) => { log.push(['add', col, J(v)]); }, ...query(col, [], null, null) }),
    runTransaction: async (fn) => {
      log.push(['txn']);
      const writes = [];
      const tx = {
        get: async (r) => r.get(),
        set: (r, v, o) => writes.push(() => r.set(v, o)), update: (r, v) => writes.push(() => r.update(v)),
        create: (r, v) => writes.push(() => r.create(v)), delete: (r) => writes.push(() => r.delete()),
      };
      const out = await fn(tx);
      const before = new Map([...data.entries()].map(([k, v]) => [k, JSON.parse(JSON.stringify(v))]));
      try { for (const w of writes) await w(); } catch (e) { data.clear(); for (const [k, v] of before) data.set(k, v); throw e; }   // a transaction is all or nothing
      return out;
    },
  };
}

function load(indexPath, seed) {
  const log = [];
  const db = fakeDb(seed, log);
  const stubs = {
    'firebase-functions/v2/https': { onCall: (a, b) => b || a, onRequest: (a, b) => b || a, HttpsError: class extends Error {} },
    'firebase-functions/params': { defineSecret: (n) => ({ value: () => (/PRIVATE_KEY/.test(n) ? PEM : 'key-id') }), defineString: (n, o) => ({ value: () => (n === 'KALSHI_LIVE_ENABLED' ? 'on' : (o && o.default) || '') }) },
    'firebase-functions/v2/scheduler': { onSchedule: (a, b) => b },
    'firebase-functions/v2/firestore': { onDocumentWritten: (a, b) => b },
    'firebase-admin/app': { initializeApp: () => ({}), getApps: () => [{}] },
    'firebase-admin/firestore': { getFirestore: () => db },
    'web-push': { setVapidDetails() {}, sendNotification: async () => ({}) },
  };
  const origLoad = Module._load;
  Module._load = function (request, parent, isMain) { return Object.prototype.hasOwnProperty.call(stubs, request) ? stubs[request] : origLoad.apply(this, arguments); };
  const origWarn = console.error, origLog = console.log;
  console.error = (...a) => log.push(['console.error', a.join(' ').slice(0, 160)]);
  console.log = (...a) => log.push(['console.log', a.join(' ').slice(0, 160)]);
  let mod;
  try { delete require.cache[require.resolve(indexPath)]; mod = require(indexPath); } finally { Module._load = origLoad; }
  return { mod, log, db, restore() { console.error = origWarn; console.log = origLog; } };
}

// A scripted exchange: answers every Kalshi request from the table, in the shape the library reads; unknown paths get an empty 200.
function exchange(log, over) {
  return async (url, o) => {
    const u = new URL(url);
    const method = (o && o.method) || 'GET';
    log.push(['fetch', method, u.pathname + u.search, o && o.body ? JSON.parse(o.body) : null]);
    const p = u.pathname.replace(/^\/trade-api\/v2/, '');
    const body = over && over[p] !== undefined ? over[p] : (
      /exchange\/status/.test(p) ? { trading_active: true, exchange_active: true } :
      /\/markets\/[^/]+$/.test(p) ? { market: { ticker: T, status: 'active', close_time: new Date(NOW + 420000).toISOString(), yes_bid_dollars: '0.50', yes_ask_dollars: '0.52', exchange_index: 2 } } :
      /\/markets$/.test(p) ? { markets: [] } :
      /portfolio\/positions/.test(p) ? { market_positions: [] } :
      /portfolio\/balance/.test(p) ? { balance: 10000 } : {});
    return { ok: true, status: 200, json: async () => body, text: async () => JSON.stringify(body) };
  };
}

async function run(indexPath) {
  const out = [];
  const scenarios = [
    ['armed: no arm, no session', 'kalshiLiveArmed', {}],
    ['armed: a session is running, no markets', 'kalshiLiveArmed', { 'kalshiLiveControl/session': { active: true, since: NOW - 600000 }, 'kalshiLiveControl/sizing': { cap: 2, base: 100, saved: 0, pool: 0, cum: 0, hwm: 0, reviewedAt: NOW - 1000, appliedTs: NOW - 5000 }, 'kalshiBotMeta/control': { halt: false } }],
    ['armed: an open filled order that has finished', 'kalshiLiveArmed', { ['kalshiLiveOrders/L1-' + T]: { ticker: T, side: 'yes', status: 'filled', settled: false, fillCount: '1', count: 1, maxCost: 0.9, orderId: 'o1', ts: NOW - 900000, strategy: 'L1' } }, { ['/markets/' + T]: { market: { ticker: T, status: 'finalized', result: 'yes', close_time: new Date(NOW - 60000).toISOString() } } }],
    ['exit: nothing open and nothing to buy', 'kalshiLiveExit', { 'kalshiLiveControl/session': { active: true } }],
    ['exit: an open filled order below the line', 'kalshiLiveExit', { 'kalshiLiveControl/session': { active: true }, ['kalshiLiveOrders/L1-' + T]: { ticker: T, side: 'yes', status: 'filled', settled: false, fillCount: '1', count: 1, maxCost: 0.9, orderId: 'o1', ts: NOW - 120000, strategy: 'L1' } }, { ['/markets/' + T]: { market: { ticker: T, status: 'active', close_time: new Date(NOW + 400000).toISOString(), yes_bid_dollars: '0.20', yes_ask_dollars: '0.22', exchange_index: 2 } }, '/portfolio/positions': { market_positions: [{ ticker: T, position_fp: '1' }] } }],
    ['flatten: nothing held', 'kalshiFlattenAll', { 'users/u': { isAdmin: true } }],
    ['flatten: one position held', 'kalshiFlattenAll', { 'users/u': { isAdmin: true } }, { '/portfolio/positions': { market_positions: [{ ticker: T, position_fp: '2' }] } }],
  ];
  for (const [name, fn, seed, over] of scenarios) {
    const h = load(indexPath, seed);
    const realFetch = global.fetch, realNow = Date.now, realTimeout = global.setTimeout;
    let clock = NOW;
    global.fetch = exchange(h.log, over);
    Date.now = () => clock;                                            // the clock moves only when the code sleeps, so an extra Date.now call cannot change how many times a loop runs
    global.setTimeout = (f, ms) => { clock += Number(ms) || 0; return realTimeout(f, 0); };
    let ret = null, threw = null;
    try {
      ret = fn === 'kalshiFlattenAll' ? await h.mod[fn]({ auth: { uid: 'u', token: { email: 'heiszcam@gmail.com', email_verified: true } } }) : await h.mod[fn]();
    } catch (e) { threw = String(e.message).slice(0, 120); }
    finally { global.fetch = realFetch; Date.now = realNow; global.setTimeout = realTimeout; h.restore(); }
    out.push({ name, log: JSON.parse(JSON.stringify(h.log)), ret: JSON.parse(JSON.stringify(ret === undefined ? null : ret)), threw });
  }
  return out;
}

module.exports = { run, load, fakeDb, exchange, NOW, T, PEM };
if (require.main === module) {
  run(path.resolve(process.argv[2])).then((r) => process.stdout.write(JSON.stringify(r, null, 1) + '\n'));
}

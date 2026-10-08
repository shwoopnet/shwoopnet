'use strict';
// Gates added after a hand-run mutation check of kalshiLiveLib.js: each one kills a mutant the earlier tests let live. Same fakes as kalshiL1Gates.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib');

const root = path.join(__dirname, '..');
const fnSrc = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const NOW = Date.parse('2026-10-07T14:00:00Z');
const iso = (ms) => new Date(ms).toISOString();
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const gates = {};

const T = 'KXBTC15M-26OCT071415-15';
const quote = (over = {}, series = 'KXBTC15M', ticker = T) => ({ series, m: Object.assign({
  ticker, status: 'active', close_time: iso(NOW + 360000), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' }, over) });

function world(opts = {}) {
  const calls = [], posts = [], docs = new Map(), events = [];
  const sess = Object.assign({ active: true, until: NOW + 3600000, ordersSent: 0, startCash: 100 }, opts.session || {});
  const store = {
    async halted() { return opts.halted === true; },
    async hasUnresolved() { return opts.unresolved === true || [...docs.values()].some((d) => d.status === 'sending' || d.status === 'unknown'); },
    async createTest(id, data) { if (docs.has(id)) return false; docs.set(id, { ...data }); return true; },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
    async sessionTrades(since) { if (opts.tradesThrow) throw new Error('down'); return [...docs.entries()].filter(([, d]) => d.ts >= since).map(([id, d]) => ({ id, ...d })); },
  };
  const fetchFn = async (url, o) => {
    calls.push({ url, method: o.method, headers: o.headers, body: o.body ? JSON.parse(o.body) : null });
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/markets/')) {
      const tk = decodeURIComponent(url.split('/markets/')[1].split('?')[0]);
      const over = (opts.fresh && opts.fresh[tk]) || {};
      return reply(opts.marketStatus || 200, { market: { status: 'active', close_time: iso(NOW + 360000), exchange_index: tk.includes('KXGOLD') ? 0 : 2, ...(opts.results && opts.results[tk] ? { result: opts.results[tk] } : {}), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100', ...over } });
    }
    if (url.endsWith('/portfolio/balance')) return reply(opts.balStatus || 200, opts.balance || { balance_breakdown: [{ balance: '70.0000', exchange_index: 2 }, { balance: '30.0000', exchange_index: 0 }] });
    if (url.includes('/portfolio/orders')) return reply(200, { orders: opts.existing || [] });
    if (o.method === 'POST') {
      posts.push(JSON.parse(o.body));
      if (opts.postThrows) throw new Error('timeout');
      if (opts.post) return reply(opts.post.status, opts.post.body);
      return reply(201, { order_id: 'ord-' + posts.length, fill_count: '1.00', remaining_count: '0.00', average_fill_price: '0.9100', average_fee_paid: '0.0057' });
    }
    throw new Error('unexpected ' + o.method + ' ' + url);
  };
  return { calls, posts, docs, store, fetchFn, sess, events };
}
const tick = (w, over = {}) => live.runL1Tick({
  session: w.sess, now: NOW, setSession: async (p) => { Object.assign(w.sess, p); }, logEvent: async (e) => { w.events.push(e); },
  quotes: [quote()], active: true, enabled: true, store: w.store, keyId: 'live-key', pem, fetchFn: w.fetchFn, ...over,
});


const seed = (w, id, over) => w.docs.set(id, Object.assign({ strategy: 'L1', ticker: id, side: 'yes', count: 1, fillCount: '1.00', maxCost: 0.92, ts: NOW - 60000, status: 'filled' }, over));

// Mutation survivors, each a consequence. The stop is "down $10", so being down EXACTLY $10 stops it.
gates.M1 = async () => {
  const w = world();
  seed(w, 'L1-OLD', { maxCost: 10, settled: true, result: 'no' });
  const r = await tick(w);
  assert.strictEqual(r.ended, 'loss stop', 'down exactly the stop amount ends the session');
  assert.strictEqual(w.posts.length, 0);
  const w2 = world();
  seed(w2, 'L1-OLD', { maxCost: 9.99, settled: true, result: 'no' });
  await tick(w2);
  assert.strictEqual(w2.posts.length, 1, 'one cent short of the stop keeps trading');
};

// Size is rounded DOWN: 1.7 contracts of risk budget buys one, never two.
gates.M2 = () => {
  assert.strictEqual(live.l1Count(80, 0.9157), 1, '1.75 contracts of budget is one contract');
  assert.strictEqual(live.l1Count(138, 0.9157), 3, 'three whole contracts of budget is three');
  assert.strictEqual(live.l1Count(120, 0.9157), 2, '2.62 is two');
};

// A market 329 s or 401 s out is outside the 330 to 400 s window, on the list and on the fresh read; 331 s and 399 s are inside.
gates.M3 = async () => {
  for (const [ms, expect] of [[329000, 0], [331000, 1], [399000, 1], [401000, 0]]) {
    const close_time = iso(NOW + ms);
    const w = world({ fresh: { [T]: { close_time } } });
    await tick(w, { quotes: [quote({ close_time })] });
    assert.strictEqual(w.posts.length, expect, ms + ' ms before the close');
  }
};

// With size scaling on, two markets on one shard cannot both take the full share: the second is sized on what is left.
gates.M4 = async () => {
  const G = 'KXGOLD15M-26OCT071415-15';
  const w = world({ session: { sizing: true, startCash: 300 }, balance: { balance_breakdown: [{ balance: '300.0000', exchange_index: 2 }] },
    fresh: { [G]: { exchange_index: 2, yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' } } });
  await tick(w, { quotes: [quote(), quote({}, 'KXGOLD15M', G)] });
  assert.deepStrictEqual(w.posts.map((p) => p.count), ['3', '3'], 'both are held to the cap');
  assert.ok(/l1Count\(cash - Object\.values\(committed\)/.test(fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8')), 'and the cash an earlier order in the same tick took is still taken off before sizing the next');
};

// Only the L1 session's own trades feed its stop: an older single test order on the same account does not.
gates.M5 = async () => {
  const w = world();
  seed(w, 'L-OTHER', { strategy: undefined, maxCost: 11 });
  await tick(w);
  assert.strictEqual(w.posts.length, 1, 'a non-L1 record is not the bot\'s exposure');
  assert.ok(w.sess.active, 'and it does not end the session');
};

// A balance with one unreadable row is unreadable, not "the readable rows": nothing is sent on a guess.
gates.M6 = async () => {
  const w = world({ balance: { balance_breakdown: [{ balance: 'abc', exchange_index: 0 }, { balance: '70.0000', exchange_index: 2 }] } });
  const r = await tick(w);
  assert.strictEqual(r.skipped, 'balance unrecognised');
  assert.strictEqual(w.posts.length, 0);
};

// The switch is the literal true. Anything else, including the string 'on', sends nothing.
gates.M7 = async () => {
  const w = world();
  const r = await tick(w, { enabled: 'on' });
  assert.strictEqual(r.skipped, 'switch off');
  assert.strictEqual(w.posts.length, 0);
};

// A success status with no order id is not a success: the order may exist, so it is not counted as sent and the session ends for a human to look.
gates.M8 = async () => {
  const w = world({ post: { status: 200, body: {} } });
  const r = await tick(w);
  assert.strictEqual(r.ended, 'attempted');
  assert.strictEqual(w.docs.get('L1-' + T).status, 'error');
  assert.ok(!w.sess.ordersSent, 'not counted as an order sent');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();

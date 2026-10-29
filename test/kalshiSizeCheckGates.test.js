// Order size sanity (Oct 29, 2026): a Dogecoin order for 12 contracts reached the account where current code only sends 3. maxContractsFor is a second lock behind the sizing code.
// Each gate states a consequence for the account, not a mechanism.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib');
const root = path.join(__dirname, '..');
const NOW = Date.parse('2026-10-07T14:00:00Z');
const iso = (ms) => new Date(ms).toISOString();
const pem = crypto.generateKeyPairSync('ed25519').privateKey.export({ type: 'pkcs8', format: 'pem' });
const gates = {};

const TICKER = { KXGOLD15M: 'KXGOLD15M-26OCT071415-06', KXXRP15M: 'KXXRP15M-26OCT071415-10', KXBTC15M: 'KXBTC15M-26OCT071415-06', KXDOGE15M: 'KXDOGE15M-26OCT071415-06', KXETH15M: 'KXETH15M-26OCT071415-06', KXAUDUSD15M: 'KXAUDUSD15M-26OCT071415-06', KXUSDCAD15M: 'KXUSDCAD15M-26OCT071415-06', KXNATGAS15M: 'KXNATGAS15M-26OCT071415-10' };
const leftFor = (series) => (live.EARLY_PROBE_SERIES.includes(series) ? 600000 : 360000);
const quote = (series) => ({ series, m: { ticker: TICKER[series], status: 'active', close_time: iso(NOW + leftFor(series)), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' } });
const sess = (extra) => Object.assign({ active: true, until: NOW + 3600000, ordersSent: 0, startCash: 100, sizing: true, sizeCap: 40, sizeAddon: 0, sizeBase: 1000, sizeNextReview: NOW + 86400000 }, extra || {});
const state = { cap: 40, base: 1000, reviewedAt: NOW - 1000, pool: 0, saved: 0, appliedTs: NOW - 1000, lastStopAt: null };
const rich = { balance_breakdown: [{ balance: '1000.0000', exchange_index: 2 }, { balance: '1000.0000', exchange_index: 0 }] };

function world(session) {
  const posts = [], docs = new Map(), events = [], s = session || sess();
  const store = {
    async halted() { return false; }, async hasUnresolved() { return false; },
    async createTest(id, data) { if (docs.has(id)) return false; docs.set(id, { ...data }); return true; },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
    async sessionTrades(since) { return [...docs.entries()].filter(([, d]) => d.ts >= since).map(([id, d]) => ({ id, ...d })); },
  };
  const fetchFn = async (url, o) => {
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/candlesticks')) {
      const n = Math.floor(NOW / 1000);
      return reply(200, { candlesticks: [0.5, 0.58, 0.66, 0.74, 0.82, 0.91].map((m, i, a) => ({ end_period_ts: n - 60 * (a.length - 1 - i), yes_bid_dollars: undefined, yes_bid: { close_dollars: String(m - 0.01) }, yes_ask: { close_dollars: String(m + 0.01) } })) });
    }
    if (url.includes('/markets/')) {
      const tk = decodeURIComponent(url.split('/markets/')[1].split('?')[0]);
      return reply(200, { market: { status: 'active', close_time: iso(NOW + leftFor(tk.split('-')[0])), exchange_index: tk.includes('KXGOLD') ? 0 : 2, yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' } });
    }
    if (url.endsWith('/portfolio/balance')) return reply(200, rich);
    if (url.includes('/portfolio/orders')) return reply(200, { orders: [] });
    if (url.includes('/portfolio/fills')) return reply(200, { fills: [] });
    if (o.method === 'POST') { posts.push(JSON.parse(o.body)); return reply(201, { order_id: 'ord-' + posts.length, fill_count: '1.00', remaining_count: '0.00', average_fill_price: '0.9100', average_fee_paid: '0.0057' }); }
    throw new Error('unexpected ' + o.method + ' ' + url);
  };
  return { posts, docs, store, fetchFn, sess: s, events };
}
// pausedSeries: [] unless a gate wants the real pause list (leave it out of the args entirely, as index.js does)
const tick = (w, series, extra = {}) => live.runL1Tick({
  session: w.sess, now: NOW, setSession: async (p) => { Object.assign(w.sess, p); }, logEvent: async (e) => { w.events.push(e); },
  quotes: series.map(quote), active: true, enabled: true, store: w.store, keyId: 'live-key', pem, fetchFn: w.fetchFn,
  sizingState: state, setSizingState: async () => {}, ...extra,
});
const noPause = { pausedSeries: [] };
const EXPECTED = { KXGOLD15M: null, KXXRP15M: 1, KXBTC15M: 1, KXDOGE15M: 3, KXETH15M: 1, KXAUDUSD15M: 1, KXUSDCAD15M: 1, KXNATGAS15M: 2 };

// SZ1: the incident. A 12 contract Dogecoin order is never sent, leaves no order document behind, says why, and does not stop the other markets from trading.
gates.SZ1 = async () => {
  const saved = live.FIXED_CONTRACTS.KXDOGE15M;
  live.FIXED_CONTRACTS.KXDOGE15M = 12;   // simulates the sizing code going wrong
  try {
    const w = world();
    await tick(w, ['KXDOGE15M'], noPause);
    assert.strictEqual(w.posts.filter((p) => p.ticker.includes('KXDOGE')).length, 0, 'no Dogecoin order reached the broker');
    assert.strictEqual(w.docs.size, 0, 'and none is recorded as sending');
    assert.ok(w.events.some((e) => e.kind === 'order size refused' && /KXDOGE15M/.test(e.detail) && /12/.test(e.detail)), 'the refusal is logged with the series and the count');
    const w2 = world();
    await tick(w2, ['KXDOGE15M', 'KXGOLD15M'], noPause);
    assert.deepStrictEqual(w2.posts.map((p) => p.ticker), [TICKER.KXGOLD15M], 'gold still goes out, only the bad order is skipped');
  } finally { live.FIXED_CONTRACTS.KXDOGE15M = saved; }
};

// SZ2: every valid order of every series is sent exactly as before: same count, one order, client id from the market.
gates.SZ2 = async () => {
  for (const series of live.L1_SERIES) {
    for (const sizing of [true, false]) {
      const w = world(sizing ? sess() : { active: true, until: NOW + 3600000, ordersSent: 0, startCash: 100 });
      await tick(w, [series], { ...noPause, ...(sizing ? {} : { sizingState: null }) });
      assert.strictEqual(w.posts.length, 1, series + ' (sizing ' + sizing + ') is still sent');
      const n = Number(w.posts[0].count);
      assert.ok(n >= 1 && n <= live.maxContractsFor(series), series + ' count ' + n + ' is inside its maximum');
      assert.strictEqual(w.posts[0].client_order_id, 'L1-' + TICKER[series]);
      if (EXPECTED[series] !== null) assert.strictEqual(n, sizing ? EXPECTED[series] : 1, series + ' keeps its size');
    }
  }
};

// SZ3: gold's ladder sizes still go out, up to the ceiling, and the maximum is never tighter than the ladder can legitimately produce.
gates.SZ3 = async () => {
  const w = world();
  await tick(w, ['KXGOLD15M'], noPause);
  assert.ok(w.posts.length === 1 && Number(w.posts[0].count) > 3, 'a ladder-sized gold order is sent: ' + w.posts.map((p) => p.count));
  assert.ok(live.maxContractsFor('KXGOLD15M') === live.L1_ORDER_CEILING && live.L1_ORDER_CEILING >= live.L1_SIZE_CEILING, 'gold may go to the existing single order ceiling, which is above the ladder ceiling');
  for (const cap of [1, 3, 12, 40]) for (const addon of [0, 5, 9, 100]) {
    assert.ok(live.l1Count(1e9, 0.91, cap, addon) <= live.maxContractsFor('KXGOLD15M'), 'no ladder result exceeds the maximum: cap ' + cap + ' addon ' + addon);
  }
};

// SZ4: paused series still never trade, with the real pause list (index.js never passes one).
gates.SZ4 = async () => {
  const w = world();
  await tick(w, ['KXXRP15M', 'KXAUDUSD15M', 'KXUSDCAD15M', 'KXNATGAS15M'], {});
  assert.strictEqual(w.posts.length, 0, 'XRP and the probes stay paused');
  assert.ok(live.PAUSED_SERIES.includes('KXXRP15M'));
};

// SZ5: a series that is not on the list, or no series at all, may have no contracts.
gates.SZ5 = () => {
  assert.strictEqual(live.maxContractsFor('KXSOL15M'), 0);
  assert.strictEqual(live.maxContractsFor(undefined), 0);
  assert.strictEqual(live.maxContractsFor('KXDOGE15M'), 3);
  assert.strictEqual(live.maxContractsFor('KXBTC15M'), 1);
  assert.strictEqual(live.maxContractsFor('KXNATGAS15M'), 2);
};

// SZ6: nothing from the page, the session document or Firestore can move the limit. Extra arguments are ignored and the source reads no session, argument or request.
gates.SZ6 = async () => {
  assert.strictEqual(live.maxContractsFor('KXDOGE15M', { maxContracts: 99, FIXED_CONTRACTS: { KXDOGE15M: 99 } }), 3, 'extra arguments are ignored');
  const saved = live.FIXED_CONTRACTS.KXDOGE15M;
  live.FIXED_CONTRACTS.KXDOGE15M = 12;
  try {
    assert.strictEqual(live.maxContractsFor('KXDOGE15M'), 3, 'a change to the fixed sizes in memory does not move the lock');
    const w = world(sess({ maxContracts: 99, liveExtra: { KXDOGE15M: 99 }, sizeCap: 99, count: 12 }));
    await tick(w, ['KXDOGE15M'], { ...noPause, sizingState: { ...state, cap: 99, maxContracts: 99 } });
    assert.strictEqual(w.posts.length, 0, 'stored values do not let a 12 contract order through');
  } finally { live.FIXED_CONTRACTS.KXDOGE15M = saved; }
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  const body = src.slice(src.indexOf('function maxContractsFor('), src.indexOf('}\n', src.indexOf('function maxContractsFor(')) + 2);
  assert.ok(!/args|session|request|store|process\.env/.test(body), 'the function reads code constants only');
  const idx = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
  assert.ok(!/maxContractsFor/.test(idx) && !/maxContractsFor/.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8')), 'neither a callable nor the page touches it');
  assert.ok(/count > maxContractsFor\(c\.series\)/.test(src) && src.indexOf('store.createTest(cid, record)', src.indexOf('count > maxContractsFor(c.series)')) > 0 && src.indexOf('count > maxContractsFor(c.series)') > src.indexOf('async function runL1Tick'), 'checked before the order is recorded or sent');
};

(async () => {
  for (const [name, fn] of Object.entries(gates)) { await fn(); console.log('ok   ' + name); }
})().catch((e) => { console.error(e); process.exit(1); });

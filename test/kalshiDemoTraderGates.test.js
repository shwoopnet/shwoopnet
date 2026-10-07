// The one-time Kalshi DEMO test trader. It sends one tiny order to the demo exchange (mock funds)
// from the bot's current signal. Every gate states a consequence, and runs the real code against
// a scripted Kalshi and an in-memory store.

const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const demo = require('../functions/kalshiDemoLib');

const root = path.join(__dirname, '..');
const gates = {};

const ed = crypto.generateKeyPairSync('ed25519');
const rsa = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
const pemOf = (k) => k.privateKey.export({ type: 'pkcs8', format: 'pem' });
const NOW = Date.parse('2026-10-06T18:30:00Z');
const iso = (ms) => new Date(ms).toISOString();

// ---- signing ----
// The signature must verify against the public key over timestamp + METHOD + path, query left out.
gates.D1 = () => {
  const sig = demo.signRequest(pemOf(ed), '1703123456789', 'GET', '/trade-api/v2/portfolio/balance?limit=5');
  const msg = Buffer.from('1703123456789GET/trade-api/v2/portfolio/balance');
  assert.ok(crypto.verify(null, msg, ed.publicKey, Buffer.from(sig, 'base64')), 'Ed25519 signature verifies');
  assert.ok(!crypto.verify(null, Buffer.from('1703123456789POST/trade-api/v2/portfolio/balance'), ed.publicKey, Buffer.from(sig, 'base64')), 'a different method must not verify');
  assert.ok(!crypto.verify(null, Buffer.from('1703123456790GET/trade-api/v2/portfolio/balance'), ed.publicKey, Buffer.from(sig, 'base64')), 'a different timestamp must not verify');
  const rs = demo.signRequest(pemOf(rsa), '1', 'POST', '/trade-api/v2/portfolio/events/orders');
  const pss = { key: rsa.publicKey, padding: crypto.constants.RSA_PKCS1_PSS_PADDING, saltLength: crypto.constants.RSA_PSS_SALTLEN_DIGEST };
  assert.ok(crypto.verify('sha256', Buffer.from('1POST/trade-api/v2/portfolio/events/orders'), pss, Buffer.from(rs, 'base64')), 'RSA-PSS signature verifies');
  // A secret pasted with literal \n (a common paste) still loads.
  const flat = pemOf(ed).replace(/\n/g, '\\n');
  assert.ok(crypto.verify(null, msg, ed.publicKey, Buffer.from(demo.signRequest(flat, '1703123456789', 'GET', '/trade-api/v2/portfolio/balance'), 'base64')));
};

// ---- demo only ----
gates.D2 = async () => {
  for (const bad of ['https://external-api.kalshi.com/trade-api/v2/x', 'https://api.elections.kalshi.com/trade-api/v2/x',
    'http://external-api.demo.kalshi.co/trade-api/v2/x', 'https://external-api.demo.kalshi.co.evil.com/x', 'https://evil.com/external-api.demo.kalshi.co']) {
    assert.throws(() => demo.assertDemo(bad), demo.NotDemo, 'must refuse ' + bad);
  }
  demo.assertDemo('https://demo-api.kalshi.co/trade-api/v2/x');
  const urls = [];
  const fetchFn = async (u) => { urls.push(u); return { status: 200, text: async () => '{}' }; };
  await demo.demoRequest({ fetchFn, keyId: 'k', pem: pemOf(ed), method: 'GET', path: '/portfolio/balance' });
  await demo.demoRequest({ fetchFn, method: 'GET', path: '/markets/X@evil.com' });
  assert.ok(urls.every((u) => new URL(u).hostname === 'external-api.demo.kalshi.co'), 'every request goes to the demo host: ' + urls);
};

// ---- the order ----
gates.D3 = () => {
  const yes = { ticker: 'KXGOLD15M-A', side: 'yes', price: 0.40, contracts: 2, band: '40c' };
  assert.deepStrictEqual(demo.orderBody(yes, 't-KXGOLD15M-A', 0), {
    ticker: 'KXGOLD15M-A', side: 'bid', count: '2', price: '0.40', time_in_force: 'immediate_or_cancel',
    self_trade_prevention_type: 'taker_at_cross', client_order_id: 't-KXGOLD15M-A', exchange_index: 0 });
  // Buying NO at 48c is selling YES at 52c on the YES book.
  const no = demo.orderBody({ ticker: 'T', side: 'no', price: 0.48, contracts: 2, band: '50c' }, 'c');
  assert.ok(no.side === 'ask' && no.price === '0.52' && !('exchange_index' in no), JSON.stringify(no));
  for (const c of [0, 6]) assert.throws(() => demo.orderBody({ ...yes, contracts: c }, 'c'), /1 to 5/);
  assert.throws(() => demo.orderBody({ ...yes, price: 0.52, contracts: 2 }, 'c'), /at most \$1\.00/, 'the cost cap includes the fee');
};

gates.D4 = () => {
  const f = demo.fundedShards({ balance_breakdown: [{ balance: '200.0000', exchange_index: 0 }, { balance: '0.0000', exchange_index: 2 }] });
  assert.ok(f.has(0) && !f.has(2) && f.size === 1);
  assert.strictEqual(demo.fundedShards(null).size, 0);
};

// ---- the flow, against a scripted demo exchange ----
const quote = (over = {}) => ({ series: 'KXGOLD15M', m: Object.assign({
  ticker: 'KXGOLD15M-26OCT061400-00', status: 'active', close_time: iso(NOW + 13 * 60000),
  yes_bid_dollars: '0.38', yes_ask_dollars: '0.40', yes_bid_size_fp: '50', yes_ask_size_fp: '50' }, over) });

function world(opts = {}) {
  const calls = [], posts = [], docs = new Map(), orders = new Map();
  const store = {
    async lastTestAt() { const t = [...docs.values()].map((d) => d.ts); return t.length ? Math.max(...t) : null; },
    async createTest(id, data) { if (docs.has(id)) return false; docs.set(id, { ...data }); return true; },
    async getTest(id) { return docs.has(id) ? { ...docs.get(id) } : null; },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
  };
  const seq = (opts.postSeq || []).slice();
  const fetchFn = async (url, o) => {
    calls.push({ url, method: o.method, headers: o.headers, body: o.body ? JSON.parse(o.body) : null });
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (opts.primaryDown && url.startsWith('https://external-api.demo.kalshi.co/')) return reply(503, { exchange_active: false, trading_active: false });
    if (url.endsWith('/exchange/status')) return opts.demoDown ? reply(503, { exchange_active: false, trading_active: false }) : reply(200, { exchange_active: true, trading_active: true });
    if (url.endsWith('/portfolio/balance')) return reply(200, { balance_breakdown: opts.breakdown || [{ balance: '200.0000', exchange_index: 0 }, { balance: '0.0000', exchange_index: 2 }] });
    if (url.includes('/portfolio/orders')) return reply(200, { orders: [...orders.values()] });
    if (url.includes('/markets/')) return reply(200, { market: { status: 'active', close_time: iso(NOW + 13 * 60000), exchange_index: opts.shard === undefined ? 0 : opts.shard, yes_bid_dollars: '0.38', yes_ask_dollars: '0.40', yes_bid_size_fp: '20', yes_ask_size_fp: '20', ...(opts.demoBook || {}) } });
    if (o.method === 'POST') {
      const b = JSON.parse(o.body);
      posts.push(b);
      const step = seq.length ? seq.shift() : null;
      if (opts.netDown || step === 'throw') throw new Error('network down');
      const create = () => { const ord = { order_id: 'ord-' + (orders.size + 1), client_order_id: b.client_order_id, status: 'canceled', fill_count_fp: '2.00', initial_count_fp: b.count }; orders.set(b.client_order_id, ord); return ord; };
      if (step === 'land-then-throw') { create(); throw new Error('response lost'); }
      if (step && typeof step === 'object') return reply(step.status, step.body);
      if (opts.post) return reply(opts.post.status, opts.post.body);
      if (orders.has(b.client_order_id)) return reply(409, { error: { code: 'order_already_exists', message: 'order already exists' } });
      const ord = create();
      return reply(201, { order_id: ord.order_id, client_order_id: b.client_order_id, fill_count: '2.00', remaining_count: '0.00', average_fill_price: '0.4000' });
    }
    throw new Error('unexpected ' + o.method + ' ' + url);
  };
  return { calls, posts, docs, orders, store, fetchFn };
}
const run = (w, over = {}) => demo.runDemoTest({ quotes: [quote()], active: true, store: w.store, now: NOW, keyId: 'key-id-123', pem: pemOf(ed), fetchFn: w.fetchFn, sleepFn: async () => {}, ...over });

// The happy path: one capped order from the live signal, signed, recorded, with no secret anywhere.
gates.D5 = async () => {
  const w = world();
  const r = await run(w);
  assert.ok(r.ok && r.filled && r.count === 2 && r.sentSide === 'bid' && r.sentPrice === '0.40', JSON.stringify(r));
  assert.strictEqual(w.posts.length, 1);
  assert.strictEqual(w.posts[0].client_order_id, 't-KXGOLD15M-26OCT061400-00', 'derived from the market, never random');
  assert.strictEqual(w.posts[0].exchange_index, 0);
  const rec = w.docs.get('t-KXGOLD15M-26OCT061400-00');
  assert.ok(rec.status === 'filled' && rec.orderId === 'ord-1' && rec.mode === 'demo');
  const post = w.calls.find((c) => c.method === 'POST');
  assert.ok(post.url.startsWith('https://external-api.demo.kalshi.co/'));
  const ts = post.headers['KALSHI-ACCESS-TIMESTAMP'];
  assert.ok(crypto.verify(null, Buffer.from(ts + 'POST/trade-api/v2/portfolio/events/orders'), ed.publicKey, Buffer.from(post.headers['KALSHI-ACCESS-SIGNATURE'], 'base64')), 'the order is signed over the full path');
  const everything = JSON.stringify([r, [...w.docs.values()]]);
  assert.ok(!everything.includes('key-id-123') && !everything.includes('BEGIN') && !everything.includes(post.headers['KALSHI-ACCESS-SIGNATURE']), 'no secret in the result or the record');
};

// A second test for the same market must not send a second order, and two at the same instant send exactly one.
gates.D6 = async () => {
  const w = world();
  await run(w);
  const again = await run(w, { now: NOW + 5 * 60000 });
  assert.ok(!again.ok && /already sent/.test(again.reason) && w.posts.length === 1, 'the record blocks a second order');
  const w2 = world();
  const both = await Promise.all([run(w2, { now: NOW }), run(w2, { now: NOW })]);
  assert.strictEqual(w2.posts.length, 1, 'two simultaneous clicks place one order');
  assert.strictEqual(both.filter((x) => x.ok).length, 1);
};

// Kalshi's own refusal of a repeated id (HTTP 409) is handled, not crashed on: the order that already exists is looked up.
gates.D7 = async () => {
  const w = world({ post: { status: 409, body: { error: { code: 'order_already_exists', message: 'order already exists' } } } });
  const r = await run(w);
  assert.ok(!r.ok && /already has an order/.test(r.reason), 'a 409 whose order cannot be found is reported, not crashed on');
  assert.strictEqual(w.docs.get('t-KXGOLD15M-26OCT061400-00').status, 'duplicate refused');
  const w2 = world({ post: { status: 409, body: { error: { code: 'order_already_exists' } } } });
  w2.orders.set('t-KXGOLD15M-26OCT061400-00', { order_id: 'ord-9', client_order_id: 't-KXGOLD15M-26OCT061400-00', status: 'canceled', fill_count_fp: '0.00' });
  const r2 = await run(w2);
  assert.ok(r2.ok && r2.recovered && r2.orderId === 'ord-9' && !r2.filled, 'the existing order is reported as it stands: ' + JSON.stringify(r2));
};

// Things that must stop BEFORE any order: no signal, exchange closed, cooldown, unfunded shard.
gates.D8 = async () => {
  let w = world();
  const none = await run(w, { quotes: [quote({ yes_bid_dollars: '0.68', yes_ask_dollars: '0.70' })] });
  assert.ok(!none.ok && /No signal/.test(none.reason) && w.calls.length === 0, 'no signal: nothing is called');
  w = world();
  assert.ok(!(await run(w, { active: false })).ok && w.calls.length === 0);
  w = world();
  await w.store.createTest('old', { ts: NOW - 30000 });
  const cool = await run(w);
  assert.ok(!cool.ok && /less than a minute/.test(cool.reason) && w.calls.length === 0, 'cooldown: nothing is called');
  w = world({ shard: 2 });
  const unfunded = await run(w);
  assert.ok(!unfunded.ok && /no funds/.test(unfunded.reason) && w.posts.length === 0, 'an unfunded shard gets no order: ' + unfunded.reason);
  assert.strictEqual(w.docs.size, 0, 'and no record');
};

// A refusal that is the caller's fault (HTTP 400) is recorded and blocks that market; it is not retried.
gates.D9 = async () => {
  const w = world({ post: { status: 400, body: { error: { code: 'invalid_order' } } } });
  const r = await run(w);
  assert.ok(!r.ok && /HTTP 400/.test(r.reason) && w.docs.get('t-KXGOLD15M-26OCT061400-00').status === 'error' && w.posts.length === 1, 'a 400 is not retried');
  const again = await run(w, { now: NOW + 5 * 60000 });
  assert.ok(!again.ok && /already sent/.test(again.reason) && w.posts.length === 1, 'and it blocks the market');
  // A crash after the record and before any answer leaves "sending", which blocks: nothing is sent twice.
  const w2 = world();
  await w2.store.createTest('t-KXGOLD15M-26OCT061400-00', { ts: NOW - 120000, status: 'sending' });
  const stuck = await run(w2);
  assert.ok(!stuck.ok && /already sent/.test(stuck.reason) && w2.posts.length === 0);
};

// The demo exchange went down in real use (HTTP 503, trading_active false). It must say so before anything is recorded.
gates.D12 = async () => {
  const w = world({ demoDown: true });
  const r = await run(w);
  assert.ok(!r.ok && /demo exchange is down/.test(r.reason) && w.posts.length === 0, r.reason);
  assert.strictEqual(w.docs.size, 0, 'no record is written for an order that was never sent');
  assert.ok(w.calls.every((c) => c.method === 'GET'), 'and nothing is placed');
};

// A transient failure is retried within the call; if it never clears, the record says "unavailable" and the next
// press tries again, sending the same order id. It can leave only one order.
gates.D13 = async () => {
  const w = world({ postSeq: Array.from({ length: 6 }, () => ({ status: 503, body: { error: { code: 'service_unavailable' } } })) });
  const r = await run(w);
  assert.ok(!r.ok && /not answering \(HTTP 503\)/.test(r.reason), r.reason);
  assert.strictEqual(w.posts.length, 6, 'three attempts in the one call, each tried on both demo front doors');
  assert.strictEqual(w.docs.get('t-KXGOLD15M-26OCT061400-00').status, 'unavailable');
  assert.strictEqual(w.orders.size, 0, 'nothing was placed');
  const retry = await run(w, { now: NOW + 5 * 60000 });
  assert.ok(retry.ok && w.orders.size === 1, 'the next press goes through once the exchange is back: ' + JSON.stringify(retry));
  assert.ok(new Set(w.posts.map((p) => p.client_order_id)).size === 1, 'every attempt carried the same order id');
  assert.strictEqual(w.docs.get('t-KXGOLD15M-26OCT061400-00').status, 'filled');
  // One retry inside the call is enough when the exchange recovers at once.
  const w2 = world({ postSeq: [{ status: 503, body: {} }] });
  const r2 = await run(w2);
  assert.ok(r2.ok && w2.posts.length === 2 && w2.orders.size === 1);
};

// The answer to an order can be lost AFTER Kalshi accepted it. The retry is refused as a duplicate (409), and the
// existing order is reported: exactly one order exists and the user sees the truth.
gates.D14 = async () => {
  const w = world({ postSeq: ['land-then-throw'] });
  const r = await run(w);
  assert.ok(r.ok && r.recovered && w.orders.size === 1 && w.posts.length === 2, JSON.stringify(r));
  assert.ok(r.filled && r.fillCount === '2.00');
  const w2 = world({ netDown: true });
  const down = await run(w2);
  assert.ok(!down.ok && w2.docs.get('t-KXGOLD15M-26OCT061400-00').status === 'unavailable' && w2.posts.length === 6, 'a network failure is retried on both front doors, then marked unavailable');
};

// Kalshi's recommended demo host returned 503 while the other demo host kept trading (2026-10-06). The order must go
// through the second one, once, with the same id, and only ever to the two documented demo hosts.
gates.D15 = async () => {
  const w = world({ primaryDown: true });
  const r = await run(w);
  assert.ok(r.ok && r.filled, 'the order goes through when only the recommended host is down: ' + JSON.stringify(r));
  assert.strictEqual(w.orders.size, 1, 'exactly one order exists');
  const post = w.calls.filter((c) => c.method === 'POST');
  assert.ok(post.length === 2 && post[0].url.startsWith('https://external-api.demo.kalshi.co/') && post[1].url.startsWith('https://demo-api.kalshi.co/'), 'tried the recommended host, then the alternate');
  assert.strictEqual(post[0].body.client_order_id, post[1].body.client_order_id, 'the same order id on both');
  const hosts = new Set(w.calls.map((c) => new URL(c.url).hostname));
  assert.ok([...hosts].every((h) => ['external-api.demo.kalshi.co', 'demo-api.kalshi.co'].includes(h)), 'only demo hosts: ' + [...hosts]);
  // The exchange check also fails over: one front door reporting the exchange down is not "down".
  const w2 = world({ primaryDown: true });
  assert.ok((await run(w2)).ok && !w2.calls.some((c) => c.url.startsWith('https://demo-api.kalshi.co/') && c.method === 'DELETE'));
};

// The first demo tests came back "no fill" because they were priced at the LIVE signal price, which the thin demo book
// did not hold. The order is now priced to meet the demo's own touch, within a tolerance of the live price.
gates.D16 = async () => {
  // A YES buy takes the demo's YES ask, even when it is a few cents from the live signal price.
  const w = world({ demoBook: { yes_ask_dollars: '0.43' } });
  const r = await run(w);
  assert.ok(r.ok && r.filled && r.sentSide === 'bid' && r.sentPrice === '0.43', JSON.stringify(r));
  assert.strictEqual(w.posts[0].price, '0.43', 'crosses the demo ask, not the live price');
  assert.strictEqual(w.docs.get('t-' + w.posts[0].ticker).livePrice, 0.4, 'the live signal price is kept on the record');
  // A NO buy is a YES sell: it takes the demo's YES bid.
  const q = quote({ yes_bid_dollars: '0.59', yes_ask_dollars: '0.61' });
  const w2 = world({ demoBook: { yes_bid_dollars: '0.57', yes_ask_dollars: '0.61' } });
  const r2 = await run(w2, { quotes: [q] });
  assert.ok(r2.ok && r2.sentSide === 'ask' && r2.sentPrice === '0.57', JSON.stringify(r2));
};
gates.D17 = async () => {
  // Too far from the live price: nothing is sent and nothing is recorded, so trying again is not blocked.
  const far = world({ demoBook: { yes_ask_dollars: '0.50' } });
  const r = await run(far);
  assert.ok(!r.ok && /0\.50 against the live 0\.40/.test(r.reason), JSON.stringify(r));
  assert.strictEqual(far.posts.length, 0); assert.strictEqual(far.docs.size, 0);
  // An empty side of the demo book is said plainly, not reported as "no fill".
  for (const book of [{ yes_ask_dollars: '0.00' }, { yes_ask_dollars: '1.00' }, { yes_ask_dollars: undefined }, { yes_ask_size_fp: '0' }]) {
    const w = world({ demoBook: book });
    const e = await run(w);
    assert.ok(!e.ok && /nothing on the side/.test(e.reason) && w.posts.length === 0 && w.docs.size === 0, JSON.stringify([book, e]));
  }
};
gates.D18 = () => {
  // The cap holds at the crossing price: contracts shrink to fit, and one that still does not fit is refused.
  const sig = { ticker: 'T', series: 'KXBTC15M', side: 'yes', band: '40c', price: 0.40, contracts: 2 };
  const p = demo.crossPlan(sig, { yes_ask_dollars: '0.44', yes_ask_size_fp: '10' });
  assert.ok(p.ok && p.signal.price === 0.44);
  const cost = p.signal.price * p.signal.contracts + require('../functions/kalshiBotLib').takerFee(p.signal.price, p.signal.contracts);
  assert.ok(cost <= demo.TEST_CAP + 1e-9, 'cost ' + cost);
  assert.strictEqual(demo.crossPlan({ ...sig, price: 0.99 }, { yes_ask_dollars: '0.995' }).ok, false, 'a price whose single contract plus fee breaks the cap');
  const shrunk = demo.crossPlan({ ...sig, price: 0.45, contracts: 2 }, { yes_ask_dollars: '0.49' });
  assert.ok(shrunk.ok && shrunk.signal.contracts === 1, 'two contracts at 49c break the cap, so one is sent: ' + JSON.stringify(shrunk));
  assert.strictEqual(demo.CROSS_TOLERANCE, 0.05);
  assert.ok(demo.crossPlan(sig, { yes_ask_dollars: '0.45' }).ok && !demo.crossPlan(sig, { yes_ask_dollars: '0.46' }).ok, 'the tolerance is 5c, no more');
};

// ---- wiring: where the order code may live ----
const fnSrc = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
gates.D10 = () => {
  const ORD = /portfolio\/events\/orders/;
  const offenders = fs.readdirSync(path.join(root, 'functions')).filter((f) => f.endsWith('.js') && ORD.test(fs.readFileSync(path.join(root, 'functions', f), 'utf8')));
  assert.deepStrictEqual(offenders, ['kalshiDemoLib.js'], 'order code lives in exactly one module');
  const m = /exports\.kalshiDemoTrade = onCall\(([\s\S]*?)\n\);/.exec(fnSrc);
  assert.ok(m, 'kalshiDemoTrade not found');
  assert.ok(m[1].indexOf('assertKalshiAdmin(request.auth)') > -1 && m[1].indexOf('assertKalshiAdmin') < m[1].indexOf('runDemoTest'), 'admin check comes first');
  assert.ok(!/request\.data/.test(m[1]), 'takes nothing from the caller: no ticker, price or size can be supplied');
  assert.ok(/secrets: \[KALSHI_DEMO_KEY_ID, KALSHI_DEMO_PRIVATE_KEY\]/.test(m[1]));
  const lib = fs.readFileSync(path.join(root, 'functions', 'kalshiDemoLib.js'), 'utf8').replace(/\/\/[^\n]*/g, '');
  assert.ok(!/console\.(log|info|warn|error)/.test(lib), 'the module never logs');
  assert.ok(!/kalshi\.com\/trade-api/.test(lib.replace(/demo\.kalshi\.co/g, '')), 'no production host in the module');
  // The scheduled bot and the relay stay order-free.
  const rules = fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8');
  const r = /match \/kalshiDemoOrders\/\{id\} \{([\s\S]*?)\n    \}/.exec(rules);
  assert.ok(r && /allow read: if isAdmin\(\);/.test(r[1]) && /allow write: if false;/.test(r[1]), 'demo records: admin read, nobody writes from a client');
};

// ---- the page ----
// Nothing is sent by the first click: it only asks. Only the confirm button calls the server, only for the admin, and the
// bridge sends no ticker, price or size.
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
gates.D11 = () => {
  assert.ok(/id="kalDemoSend"/.test(html) && /id="kalDemoYes"/.test(html) && /id="kalDemoNo"/.test(html) && /id="kalDemoList"/.test(html));
  const wire = /\(function\(\)\{\n    var send = document\.getElementById\('kalDemoSend'\)([\s\S]*?)\n  \}\)\(\);/.exec(html);
  assert.ok(wire, 'demo wiring not found');
  const sendClick = /send\.addEventListener\('click', function\(\)\{([^}]*)\}\);/.exec(wire[1]);
  assert.ok(sendClick && !/kalshiDemoTrade/.test(sendClick[1]) && /ask\(true\)/.test(sendClick[1]), 'the first click only asks');
  assert.ok(/yes\.addEventListener\('click'[\s\S]*?currentUserIsAdmin[\s\S]*?api\.kalshiDemoTrade\(\)/.test(wire[1]), 'only the confirm click sends, and only for the admin');
  assert.strictEqual((wire[1].match(/kalshiDemoTrade\(/g) || []).length, 1, 'one call site');
  assert.ok(/kalshiDemoTradeFn\(\{\}\)/.test(html), 'the bridge sends an empty payload');
  assert.ok(/watchKalshiDemo/.test(html) && /kalshiDemoUnsub\(\)/.test(html), 'listens only while the Bot tab is open');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();

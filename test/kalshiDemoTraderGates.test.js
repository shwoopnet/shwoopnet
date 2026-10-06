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
  const calls = [], posts = [], docs = new Map();
  const store = {
    async lastTestAt() { const t = [...docs.values()].map((d) => d.ts); return t.length ? Math.max(...t) : null; },
    async createTest(id, data) { if (docs.has(id)) return false; docs.set(id, { ...data }); return true; },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
  };
  const fetchFn = async (url, o) => {
    calls.push({ url, method: o.method, headers: o.headers, body: o.body ? JSON.parse(o.body) : null });
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.endsWith('/portfolio/balance')) return reply(200, { balance_breakdown: opts.breakdown || [{ balance: '200.0000', exchange_index: 0 }, { balance: '0.0000', exchange_index: 2 }] });
    if (url.includes('/markets/')) return reply(200, { market: { status: 'active', close_time: iso(NOW + 13 * 60000), exchange_index: opts.shard === undefined ? 0 : opts.shard } });
    if (o.method === 'POST') {
      posts.push(JSON.parse(o.body));
      if (opts.netDown) throw new Error('network down');
      if (opts.post) return reply(opts.post.status, opts.post.body);
      return reply(201, { order_id: 'ord-' + posts.length, client_order_id: JSON.parse(o.body).client_order_id, fill_count: '2.00', remaining_count: '0.00', average_fill_price: '0.4000' });
    }
    throw new Error('unexpected ' + o.method + ' ' + url);
  };
  return { calls, posts, docs, store, fetchFn };
}
const run = (w, over = {}) => demo.runDemoTest({ quotes: [quote()], active: true, store: w.store, now: NOW, keyId: 'key-id-123', pem: pemOf(ed), fetchFn: w.fetchFn, ...over });

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

// Kalshi's own refusal of a repeated id (HTTP 409) is handled, not crashed on.
gates.D7 = async () => {
  const w = world({ post: { status: 409, body: { error: { code: 'order_already_exists', message: 'order already exists' } } } });
  const r = await run(w);
  assert.ok(!r.ok && /already has an order/.test(r.reason));
  assert.strictEqual(w.docs.get('t-KXGOLD15M-26OCT061400-00').status, 'duplicate refused');
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

// Failure stops, it does not repeat: a server error is recorded, and a network failure after the record leaves
// it behind so a retry cannot send a second order.
gates.D9 = async () => {
  let w = world({ post: { status: 500, body: { error: 'boom' } } });
  const r = await run(w);
  assert.ok(!r.ok && /HTTP 500/.test(r.reason) && w.docs.get('t-KXGOLD15M-26OCT061400-00').status === 'error');
  w = world({ netDown: true });
  await assert.rejects(() => run(w), /network down/);
  assert.strictEqual(w.docs.get('t-KXGOLD15M-26OCT061400-00').status, 'sending', 'the record stays, marking an order of unknown outcome');
  const retry = await run(w, { now: NOW + 5 * 60000 });
  assert.ok(!retry.ok && /already sent/.test(retry.reason) && w.posts.length === 1, 'a retry must not send a second order');
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

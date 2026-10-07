'use strict';
// Gates for the LIVE test order (real money). Each states the consequence, not the mechanism.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib');

const root = path.join(__dirname, '..');
const NOW = Date.parse('2026-10-07T14:00:00Z');
const iso = (ms) => new Date(ms).toISOString();
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const gates = {};

const quote = (over = {}) => ({ series: 'KXBTC15M', m: Object.assign({
  ticker: 'KXBTC15M-26OCT071415-15', status: 'active', close_time: iso(NOW + 13 * 60000),
  yes_bid_dollars: '0.38', yes_ask_dollars: '0.40', yes_bid_size_fp: '50', yes_ask_size_fp: '50' }, over) });

function world(opts = {}) {
  const calls = [], posts = [], docs = new Map();
  const store = {
    async halted() { return opts.halted === true; },
    async countSince(ts) { return opts.today !== undefined ? opts.today : [...docs.values()].filter((d) => d.ts >= ts).length; },
    async countEver() { return opts.ever !== undefined ? opts.ever : docs.size; },
    async lastTestAt() { const t = [...docs.values()].map((d) => d.ts); return t.length ? Math.max(...t) : null; },
    async hasUnresolved() { return opts.unresolved === true || [...docs.values()].some((d) => d.status === 'sending' || d.status === 'unknown'); },
    async createTest(id, data) { if (docs.has(id)) return false; docs.set(id, { ...data }); return true; },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
  };
  const fetchFn = async (url, o) => {
    calls.push({ url, method: o.method, headers: o.headers, body: o.body ? JSON.parse(o.body) : null });
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/markets/')) return reply(200, { market: { status: 'active', close_time: iso(NOW + 13 * 60000), exchange_index: 2, yes_bid_dollars: '0.38', yes_ask_dollars: '0.40', ...(opts.book || {}) } });
    if (url.endsWith('/portfolio/balance')) return reply(opts.balStatus || 200, opts.balance || { balance_breakdown: [{ balance: '120.0000', exchange_index: 2 }, { balance: '30.0000', exchange_index: 0 }] });
    if (url.includes('/portfolio/orders')) return reply(200, { orders: opts.existing || [] });
    if (o.method === 'POST') {
      posts.push(JSON.parse(o.body));
      if (opts.postThrows) throw new Error('timeout');
      if (opts.post) return reply(opts.post.status, opts.post.body);
      return reply(201, { order_id: 'ord-1', fill_count: '1.00', remaining_count: '0.00', average_fill_price: '0.4000', average_fee_paid: '0.0200' });
    }
    throw new Error('unexpected ' + o.method + ' ' + url);
  };
  return { calls, posts, docs, store, fetchFn };
}
const run = (w, over = {}) => live.runLiveTest({ quotes: [quote()], active: true, enabled: true, store: w.store, now: NOW, keyId: 'live-key', pem, fetchFn: w.fetchFn, ...over });

gates.L1 = async () => {
  // The happy path: ONE contract, at the live touch, immediate-or-cancel, signed, recorded first.
  const w = world();
  const r = await run(w);
  assert.ok(r.ok && r.filled && r.count === 1 && r.sentSide === 'bid' && r.sentPrice === '0.40', JSON.stringify(r));
  assert.strictEqual(w.posts[0].count, '1');
  assert.strictEqual(w.posts[0].self_trade_prevention_type, 'taker_at_cross');
  assert.strictEqual(w.posts[0].time_in_force, 'immediate_or_cancel');
  assert.strictEqual(w.posts[0].client_order_id, 'L-KXBTC15M-26OCT071415-15', 'derived from the market, never random');
  assert.strictEqual(w.posts[0].exchange_index, 2);
  const post = w.calls.find((c) => c.method === 'POST');
  assert.ok(crypto.verify(null, Buffer.from(post.headers['KALSHI-ACCESS-TIMESTAMP'] + 'POST/trade-api/v2/portfolio/events/orders'), ed.publicKey, Buffer.from(post.headers['KALSHI-ACCESS-SIGNATURE'], 'base64')), 'signed over the full path');
  assert.ok(!JSON.stringify([...w.docs.values()]).includes('PRIVATE'), 'no key material in a record');
  assert.strictEqual(w.docs.get('L-KXBTC15M-26OCT071415-15').status, 'filled');
};

gates.L2 = async () => {
  // Production only. Anything else, including the demo host, is refused before a request is made.
  for (const u of ['https://external-api.demo.kalshi.co/trade-api/v2/x', 'https://demo-api.kalshi.co/x', 'http://external-api.kalshi.com/x', 'https://evil.example/x']) {
    assert.throws(() => live.assertLive(u), live.NotLive, u);
  }
  assert.doesNotThrow(() => live.assertLive('https://external-api.kalshi.com/trade-api/v2/portfolio/balance'));
  const w = world();
  await run(w);
  assert.ok(w.calls.every((c) => new URL(c.url).hostname === 'external-api.kalshi.com'), 'only the production host');
};

gates.L3 = async () => {
  // Off unless explicitly on, and halted, closed or unfunded all stop it with nothing sent or recorded.
  for (const [over, w, re] of [
    [{ enabled: false }, world(), /switched off/], [{ enabled: undefined }, world(), /switched off/], [{ enabled: 'on' }, world(), /switched off/],
    [{ active: false }, world(), /not trading/], [{}, world({ halted: true }), /halted/], [{}, world({ unresolved: true }), /unresolved/],
  ]) {
    const r = await run(w, over);
    assert.ok(!r.ok && re.test(r.reason), JSON.stringify([over, r]));
    assert.strictEqual(w.posts.length, 0); assert.strictEqual(w.docs.size, 0);
  }
};

gates.L4 = async () => {
  // Hard totals: 2 a day, 5 ever, one a minute. No code path raises them.
  for (const [opts, re] of [[{ today: 2 }, /a day/], [{ ever: 5 }, /limit of 5/]]) {
    const w = world(opts); const r = await run(w);
    assert.ok(!r.ok && re.test(r.reason) && w.posts.length === 0, JSON.stringify([opts, r]));
  }
  const w = world(); await w.store.createTest('x', { ts: NOW - 30000, status: 'filled' });
  assert.ok(/less than a minute/.test((await run(w)).reason));
  assert.strictEqual(live.MAX_PER_DAY, 2); assert.strictEqual(live.MAX_EVER, 5); assert.strictEqual(live.LIVE_CAP, 2.0);
};

gates.L5 = async () => {
  // Bitcoin only, and a price that moved since the signal is not chased.
  const gold = { series: 'KXGOLD15M', m: { ...quote().m, ticker: 'KXGOLD15M-26OCT071415-00' } };
  const wg = world(); const g = await run(wg, { quotes: [gold] });
  assert.ok(!g.ok && /No Bitcoin signal/.test(g.reason) && wg.posts.length === 0);
  const wm = world({ book: { yes_ask_dollars: '0.44' } }); const m = await run(wm);
  assert.ok(!m.ok && /moved from 0\.40 to 0\.44/.test(m.reason) && wm.posts.length === 0 && wm.docs.size === 0, JSON.stringify(m));
  const we = world({ book: { yes_ask_dollars: '0.00' } }); const e = await run(we);
  assert.ok(!e.ok && /nothing on the side/.test(e.reason) && we.posts.length === 0);
  // The exchange's own close time is re-checked: a market it says closes in 3 minutes is skipped even if the quote looked fine.
  const wc = world({ book: { close_time: iso(NOW + 3 * 60000) } }); const c = await run(wc);
  assert.ok(!c.ok && /closing too soon/.test(c.reason) && wc.posts.length === 0 && wc.docs.size === 0, JSON.stringify(c));
};

gates.L6 = async () => {
  // The balance must cover THIS market's shard. Money on another shard does not count, and an unreadable balance fails closed.
  const cases = [
    [{ balance: { balance_breakdown: [{ balance: '0.0000', exchange_index: 2 }, { balance: '150.0000', exchange_index: 0 }] } }, /shard 2/],
    [{ balance: { balance_breakdown: [{ balance: '0.8000', exchange_index: 2 }] } }, /needs/],
    [{ balance: { balance: 'lots' } }, /shape this code does not recognise/],
    [{ balance: {} }, /shape this code does not recognise/],
    [{ balStatus: 401 }, /could not be read \(HTTP 401\)/],
  ];
  for (const [opts, re] of cases) {
    const w = world(opts); const r = await run(w);
    assert.ok(!r.ok && re.test(r.reason) && w.posts.length === 0 && w.docs.size === 0, JSON.stringify([opts, r]));
  }
  assert.strictEqual(live.availableFor({ balance: 15000 }, 2), 150, 'the top-level balance is cents');
};

gates.L7 = async () => {
  // A lost answer is NEVER retried, is marked unknown, says to look at the account, and blocks the next test.
  for (const opts of [{ postThrows: true }, { post: { status: 503, body: { error: 'down' } } }, { post: { status: 500, body: 'x' } }, { post: { status: 429, body: 'x' } }]) {
    const w = world(opts); const r = await run(w);
    assert.ok(!r.ok && /MAY OR MAY NOT HAVE BEEN PLACED/.test(r.reason) && /Kalshi account/.test(r.reason), JSON.stringify([opts, r]));
    assert.strictEqual(w.posts.length, 1, 'exactly one attempt, never a retry');
    assert.strictEqual(w.docs.get('L-KXBTC15M-26OCT071415-15').status, 'unknown');
    const again = await run(w);
    assert.ok(!again.ok && /unresolved/.test(again.reason) && w.posts.length === 1, 'blocked until resolved by hand');
  }
};

gates.L8 = async () => {
  // A refusal (4xx) is reported with what Kalshi said and is not retried. A 409 is looked up, not re-sent.
  const w = world({ post: { status: 400, body: { error: { code: 'insufficient_balance' } } } });
  const r = await run(w);
  assert.ok(!r.ok && /HTTP 400/.test(r.reason) && w.posts.length === 1 && w.docs.get('L-KXBTC15M-26OCT071415-15').status === 'error');
  const w2 = world({ post: { status: 409, body: { error: { code: 'order_already_exists' } } }, existing: [{ order_id: 'o9', client_order_id: 'L-KXBTC15M-26OCT071415-15', fill_count_fp: '1.00' }] });
  const r2 = await run(w2);
  assert.ok(!r2.ok && /already exists/.test(r2.reason) && w2.posts.length === 1);
  assert.strictEqual(w2.docs.get('L-KXBTC15M-26OCT071415-15').status, 'filled');
  const w3 = world({ post: { status: 409, body: 'x' } });
  await run(w3);
  assert.strictEqual(w3.docs.get('L-KXBTC15M-26OCT071415-15').status, 'unknown', 'a 409 for an order that cannot be found is unresolved');
};

gates.L9 = async () => {
  // One order per market, whatever the clicks: a second attempt on the same market sends nothing.
  const w = world(); await run(w);
  const w2 = world(); await w2.store.createTest('L-KXBTC15M-26OCT071415-15', { ts: NOW - 600000, status: 'no fill' });
  const r = await run(w2);
  assert.ok(!r.ok && /already attempted/.test(r.reason) && w2.posts.length === 0, JSON.stringify(r));
};

gates.L10 = () => {
  // The cap holds at the order's own price, and the body is fixed fields only.
  // One contract can never cost more than about $1.01, so the $2 cap is a backstop that cannot bind; it is asserted anyway.
  const top = live.livePlan({ side: 'yes', price: 0.99 }, { yes_ask_dollars: '0.995' });
  assert.ok(top.ok && top.cost <= live.LIVE_CAP && top.cost < 1.02);
  const p = live.livePlan({ side: 'yes', price: 0.4 }, { yes_ask_dollars: '0.41' });
  assert.ok(p.ok && p.cost <= live.LIVE_CAP);
  const body = live.liveOrderBody('T', 0.4, 'no', 'L-T', 2);
  assert.deepStrictEqual(Object.keys(body).sort(), ['client_order_id', 'count', 'exchange_index', 'price', 'self_trade_prevention_type', 'side', 'ticker', 'time_in_force']);
  assert.strictEqual(body.count, '1'); assert.strictEqual(body.side, 'ask');
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.ok(!/postWithRetry|RETRY|setTimeout|for \(const base of/.test(src.replace(/\/\/[^\n]*/g, '')), 'no retry or failover loop in the live module');
};

// ---- wiring: who can reach it, what the page can send, who can read the records ----
const fnSrc = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const rules = fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8');

gates.L12 = () => {
  const m = /exports\.kalshiLiveTrade = onCall\(([\s\S]*?)\n\);/.exec(fnSrc);
  assert.ok(m, 'kalshiLiveTrade not found');
  const body = m[1];
  assert.ok(body.indexOf('assertKalshiAdmin(request.auth)') > -1 && body.indexOf('assertKalshiAdmin') < body.indexOf('runLiveTest'), 'the admin check comes first');
  assert.ok(!/request\.data/.test(body), 'takes nothing from the caller: no ticker, price or size can be supplied');
  assert.ok(/secrets: \[KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY\]/.test(body), 'its own secrets, never the demo ones');
  assert.ok(!/KALSHI_DEMO/.test(body), 'the demo key is never used for a live order');
  assert.ok(/enabled: KALSHI_LIVE_ENABLED\.value\(\) === "on"/.test(body), 'only the literal "on" enables it');
  assert.ok(/defineString\("KALSHI_LIVE_ENABLED", \{ default: "off" \}\)/.test(fnSrc), 'off by default: deploying alone cannot place an order');
  assert.ok(!/KALSHI_LIVE/.test(fnSrc.slice(fnSrc.indexOf('exports.kalshiBot ='))), 'the scheduled bot never sees the live key or switch');
};

gates.L13 = () => {
  // The page asks twice, only the second click calls the server, only for the admin, and a failed call says to look at the account.
  const i = html.indexOf("getElementById('kalLiveSend')");
  assert.ok(i > -1, 'live card wiring not found');
  const iife = html.slice(i, html.indexOf('})();', i));
  const firstClick = /send\.addEventListener\('click', function\(\)\{([\s\S]*?)\}\);/.exec(iife);
  assert.ok(firstClick && !/kalshiLiveTrade\(/.test(firstClick[1]) && /ask\(true\)/.test(firstClick[1]), 'the first click only asks');
  assert.ok(/yes\.addEventListener\('click'[\s\S]*currentUserIsAdmin[\s\S]*api\.kalshiLiveTrade\(\)/.test(iife), 'the confirm click calls the server, for the admin only');
  assert.strictEqual((html.match(/kalshiLiveTrade\(/g) || []).length, 1, 'one call site in the page');
  assert.ok(/may or may not have reached Kalshi/.test(iife), 'a failed call tells the owner to check the account');
  assert.ok(/kalshiLiveTradeFn\(\{\}\)/.test(html), 'the callable is sent no arguments');
  assert.ok(/REAL money/i.test(html.slice(html.indexOf('id="kalLiveConfirm"') - 200, html.indexOf('id="kalLiveConfirm"') + 400)), 'the confirmation says it is real money');
};

gates.L14 = () => {
  const m = /match \/kalshiLiveOrders\/\{id\} \{([\s\S]*?)\n    \}/.exec(rules);
  assert.ok(m, 'rule for kalshiLiveOrders not found');
  assert.ok(/allow read: if isAdmin\(\);/.test(m[1]) && /allow write: if false;/.test(m[1]), 'admin read, no client write');
};

gates.L11 = () => {
  // The scheduled bot and the demo module stay separate from the live one.
  const demoSrc = fs.readFileSync(path.join(root, 'functions', 'kalshiDemoLib.js'), 'utf8').replace(/\/\/[^\n]*/g, '');
  assert.ok(!/external-api\.kalshi\.com/.test(demoSrc), 'the demo module never names the production host');
  for (const f of ['kalshiBotLib.js', 'kalshiBotRun.js']) {
    const code = fs.readFileSync(path.join(root, 'functions', f), 'utf8').replace(/\/\/[^\n]*/g, '');
    assert.ok(!/kalshiLiveLib|portfolio\/events\/orders/.test(code), f + ' must not touch live order code');
  }
  const liveSrc = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8').replace(/\/\/[^\n]*/g, '');
  assert.ok(!/demo\.kalshi|demo-api/.test(liveSrc), 'the live module never names a demo host');
  assert.ok(!/console\.log|print\(/.test(liveSrc), 'nothing is logged from the module that holds the key');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();

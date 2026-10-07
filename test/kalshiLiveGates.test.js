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
    // As on the demo: Bitcoin trades on shard 2, gold on shard 0.
    if (url.includes('/markets/')) return reply(200, { market: { status: 'active', close_time: iso(NOW + 13 * 60000), exchange_index: url.includes('KXGOLD') ? 0 : 2, yes_bid_dollars: '0.38', yes_ask_dollars: '0.40', ...(opts.book || {}) } });
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
  // Bitcoin and gold only (nothing else is ever sent), and a price that moved since the signal is not chased.
  const gold = { series: 'KXGOLD15M', m: { ...quote().m, ticker: 'KXGOLD15M-26OCT071415-00' } };
  const wg = world(); const g = await run(wg, { quotes: [gold] });
  assert.ok(g.ok && g.ticker.startsWith('KXGOLD15M') && wg.posts[0].exchange_index === 0, 'a gold signal is sent, on gold\'s own shard: ' + JSON.stringify(g));
  const other = { series: 'KXETH15M', m: { ...quote().m, ticker: 'KXETH15M-26OCT071415-00' } };
  const wo = world(); const o = await run(wo, { quotes: [other] });
  assert.ok(!o.ok && /No Bitcoin or gold signal/.test(o.reason) && wo.posts.length === 0, 'any other series is ignored');
  assert.deepStrictEqual(live.LIVE_SERIES, ['KXBTC15M', 'KXGOLD15M']);
  const wm = world({ book: { yes_ask_dollars: '0.44' } }); const m = await run(wm);
  assert.ok(!m.ok && /moved from 0\.40 to 0\.44/.test(m.reason) && wm.posts.length === 0 && wm.docs.size === 0, JSON.stringify(m));
  const we = world({ book: { yes_ask_dollars: '0.00' } }); const e = await run(we);
  assert.ok(!e.ok && /nothing on the side/.test(e.reason) && we.posts.length === 0);
  // The exchange's own close time is re-checked: a market it says closes in 3 minutes is skipped even if the quote looked fine.
  const wc = world({ book: { close_time: iso(NOW + 3 * 60000) } }); const c = await run(wc);
  assert.ok(!c.ok && /closing too soon/.test(c.reason) && wc.posts.length === 0 && wc.docs.size === 0, JSON.stringify(c));
};

gates.L15 = async () => {
  // Funds sit on one shard each. A signal on a market whose shard is empty is skipped for the next signal; when
  // every shard is empty nothing is sent and the reason names each one.
  const btc = quote();
  const gold = { series: 'KXGOLD15M', m: { ...quote().m, ticker: 'KXGOLD15M-26OCT071415-00' } };
  const onlyGold = { balance: { balance_breakdown: [{ balance: '0.0000', exchange_index: 2 }, { balance: '30.0000', exchange_index: 0 }] } };
  const w = world(onlyGold); const r = await run(w, { quotes: [btc, gold] });
  assert.ok(r.ok && r.ticker.startsWith('KXGOLD15M') && w.posts.length === 1, 'Bitcoin is unfunded, so gold is sent: ' + JSON.stringify(r));
  const onlyBtc = { balance: { balance_breakdown: [{ balance: '30.0000', exchange_index: 2 }, { balance: '0.0000', exchange_index: 0 }] } };
  const w2 = world(onlyBtc); const r2 = await run(w2, { quotes: [gold, btc] });
  assert.ok(r2.ok && r2.ticker.startsWith('KXBTC15M') && w2.posts.length === 1, 'gold is unfunded, so Bitcoin is sent (the order of the signals does not matter)');
  const w3 = world({ balance: { balance_breakdown: [{ balance: '0.0000', exchange_index: 2 }, { balance: '0.0000', exchange_index: 0 }] } });
  const r3 = await run(w3, { quotes: [btc, gold] });
  assert.ok(!r3.ok && /KXBTC15M[^;]*shard 2/.test(r3.reason) && /KXGOLD15M[^;]*shard 0/.test(r3.reason) && w3.posts.length === 0 && w3.docs.size === 0, JSON.stringify(r3));
  // At most ONE order per press, however many markets qualify.
  const w4 = world(); await run(w4, { quotes: [btc, gold] });
  assert.strictEqual(w4.posts.length, 1);
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
  const top = live.livePlan({ side: 'yes', price: 0.52 }, { yes_ask_dollars: '0.52' });
  assert.ok(top.ok && top.cost <= live.LIVE_CAP && top.cost < 1.02);
  // The price PAID must itself be inside a 40c or 50c band: the signal comes from a list that lags the single-market
  // read by about 2c, so the fresh price decides, not the stale one. Edges count, and NO prices are rounded to cents.
  assert.ok(live.livePlan({ side: 'yes', price: 0.40 }, { yes_ask_dollars: '0.38' }).ok, 'the 38c edge is in');
  assert.ok(live.livePlan({ side: 'yes', price: 0.40 }, { yes_ask_dollars: '0.42' }).ok, 'the 42c edge is in');
  assert.ok(!live.livePlan({ side: 'yes', price: 0.40 }, { yes_ask_dollars: '0.37' }).ok, '37c is out of the band');
  assert.ok(!live.livePlan({ side: 'yes', price: 0.43 }, { yes_ask_dollars: '0.44' }).ok, '44c sits between the bands');
  const no42 = live.livePlan({ side: 'no', price: 0.42 }, { yes_bid_dollars: '0.58' });
  assert.ok(no42.ok && no42.sidePrice === 0.42, 'a NO entry at exactly 42c is taken: 1 - 0.58 must not read as 0.42000000000000004');
  assert.ok(!live.livePlan({ side: 'yes', price: 0.40 }, { yes_ask_dollars: '0.46' }).ok && !live.livePlan({ side: 'yes', price: 0.40 }, { yes_ask_dollars: '0.34' }).ok, 'more than the wide bound is refused too');
  // A jump from one band to the other is also refused (a stale signal), even though the fresh price is itself in a band.
  assert.ok(!live.livePlan({ side: 'yes', price: 0.42 }, { yes_ask_dollars: '0.49' }).ok, '42c to 49c is a 7c jump, past the 5c bound');
  assert.ok(live.livePlan({ side: 'yes', price: 0.42 }, { yes_ask_dollars: '0.48' }).ok === false, '6c is past the bound');
  assert.ok(live.livePlan({ side: 'yes', price: 0.46 }, { yes_ask_dollars: '0.50' }).ok, '4c inside a band is fine');
  assert.strictEqual(live.MOVE_TOLERANCE, 0.05);
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
  assert.ok(!/KALSHI_LIVE/.test(fnSrc.slice(fnSrc.indexOf('exports.kalshiBookRecorder ='))), 'nothing after the live arm sees the live key or switch');
};

gates.L13 = () => {
  // The one contract test button was removed from the page when the 24 hour session replaced it. The server callable stays
  // (admin only, switch off by default), but nothing in the page can call it, so no stray click can send an order.
  assert.ok(!/kalLiveSend|kalLiveConfirm/.test(html), 'the single test controls are gone from the page');
  assert.strictEqual((html.match(/kalshiLiveTrade/g) || []).length, 0, 'the page does not call kalshiLiveTrade');
};

gates.L14 = () => {
  const m = /match \/kalshiLiveOrders\/\{id\} \{([\s\S]*?)\n    \}/.exec(rules);
  assert.ok(m, 'rule for kalshiLiveOrders not found');
  assert.ok(/allow read: if isAdmin\(\);/.test(m[1]) && /allow write: if false;/.test(m[1]), 'admin read, no client write');
};

// ---- the armed scan: click once, it scans every minute, sends ONE order, then switches itself off ----
function armed(state, logThrows) {
  const log = { sets: [], lasts: [], events: [] };
  return {
    log,
    get arm() { return state; },
    setArm: async (p) => { log.sets.push(p); state = { ...state, ...p }; },
    recordLast: async (r) => { log.lasts.push(r); },
    logEvent: async (e) => { if (logThrows) throw new Error('log down'); log.events.push(e); },
  };
}
const tick = (w, a, over = {}) => live.runArmedTick({
  quotes: [quote()], active: true, enabled: true, store: w.store, now: NOW, keyId: 'live-key', pem, fetchFn: w.fetchFn,
  arm: a.arm, setArm: a.setArm, recordLast: a.recordLast, logEvent: a.logEvent, ...over,
});

gates.L16 = async () => {
  // Not armed, or past its expiry: nothing happens, and an expired arm is switched off. No request of any kind is made.
  const w0 = world(); const a0 = armed({ armed: false });
  assert.strictEqual((await tick(w0, a0)).skipped, 'not armed');
  assert.strictEqual(w0.calls.length, 0); assert.strictEqual(a0.log.sets.length, 0);
  const w1 = world(); const a1 = armed(null);
  assert.strictEqual((await tick(w1, a1, { arm: null })).skipped, 'not armed'); assert.strictEqual(w1.calls.length, 0);
  const w2 = world(); const a2 = armed({ armed: true, until: NOW - 1 });
  assert.strictEqual((await tick(w2, a2)).skipped, 'expired');
  assert.strictEqual(w2.calls.length, 0, 'an expired arm sends nothing');
  assert.deepStrictEqual([a2.log.sets[0].armed, a2.log.sets[0].endedBecause], [false, 'expired']);
};

gates.L17 = async () => {
  // Armed with no qualifying signal: it stays armed and records why, so the page can show it. Nothing is sent.
  const w = world(); const a = armed({ armed: true, until: NOW + 3600000 });
  const r = await tick(w, a, { quotes: [] });
  assert.ok(!r.ok && /No Bitcoin or gold signal/.test(r.reason));
  assert.strictEqual(a.log.sets.length, 0, 'still armed');
  assert.strictEqual(a.log.lasts.length, 1); assert.strictEqual(a.log.lasts[0].ok, false); assert.strictEqual(a.log.lasts[0].attempted, false);
  assert.strictEqual(w.posts.length, 0);
  // Refused before sending for any guard (price moved, shard empty, halted, daily limit) also stays armed.
  for (const opts of [{ book: { yes_ask_dollars: '0.46' } }, { balance: { balance_breakdown: [{ balance: '0.0000', exchange_index: 2 }] } }, { halted: true }, { today: 2 }]) {
    const wx = world(opts); const ax = armed({ armed: true, until: NOW + 3600000 });
    const rx = await tick(wx, ax);
    assert.ok(!rx.ok && !rx.attempted && ax.log.sets.length === 0 && wx.posts.length === 0, JSON.stringify([opts, rx]));
  }
};

gates.L18 = async () => {
  // One arming places at most ONE order: it switches off once an order is sent, however many minutes follow.
  const w = world(); const a = armed({ armed: true, until: NOW + 3600000 });
  const r = await tick(w, a);
  assert.ok(r.ok && w.posts.length === 1);
  assert.deepStrictEqual([a.log.sets[0].armed, a.log.sets[0].endedBecause], [false, 'sent']);
  for (let i = 1; i <= 5; i++) await tick(w, a, { now: NOW + i * 60000 });
  assert.strictEqual(w.posts.length, 1, 'five more minutes later, still exactly one order');
  // A no-fill is still a sent order, so it also disarms.
  const wn = world({ post: { status: 201, body: { order_id: 'o1', fill_count: '0.00', remaining_count: '0.00' } } });
  const an = armed({ armed: true, until: NOW + 3600000 });
  await tick(wn, an); assert.strictEqual(an.arm.armed, false);
  // A refused (4xx), lost (5xx, timeout) or duplicate (409) answer also disarms: an order may exist, so no more scanning.
  for (const opts of [{ post: { status: 400, body: { error: 'x' } } }, { post: { status: 503, body: 'x' } }, { postThrows: true }, { post: { status: 409, body: 'x' } }]) {
    const wx = world(opts); const ax = armed({ armed: true, until: NOW + 3600000 });
    const rx = await tick(wx, ax);
    assert.ok(!rx.ok && rx.attempted === true && ax.arm.armed === false && ax.arm.endedBecause === 'attempted', JSON.stringify([opts, rx]));
    for (let i = 1; i <= 3; i++) await tick(wx, ax, { now: NOW + i * 60000 });
    assert.strictEqual(wx.posts.length, 1, 'never a second send after an attempt');
  }
  // An error mid-scan switches it off and is not swallowed.
  const we = world(); we.store.halted = async () => { throw new Error('database down'); };
  const ae = armed({ armed: true, until: NOW + 3600000 });
  await assert.rejects(() => tick(we, ae), /database down/);
  assert.deepStrictEqual([ae.arm.armed, ae.arm.endedBecause], [false, 'error']);
  assert.strictEqual(live.ARM_MS, 3 * 3600 * 1000);
};

gates.L22 = async () => {
  // The event log shown on the Bot tab. A scan that ends says why, a refusal before sending logs nothing (it would
  // be one line a minute), and a log that fails to write changes nothing about what the scan does.
  const w1 = world(); const a1 = armed({ armed: true, until: NOW + 3600000 });
  await tick(w1, a1);
  assert.deepStrictEqual(a1.log.events.map((e) => [e.kind, e.detail, e.ts]), [['scan ended', 'order sent and filled', NOW]]);
  const w2 = world({ post: { status: 201, body: { order_id: 'o1', fill_count: '0.00' } } }); const a2 = armed({ armed: true, until: NOW + 3600000 });
  await tick(w2, a2);
  assert.strictEqual(a2.log.events[0].detail, 'order sent, no fill');
  const w3 = world({ post: { status: 503, body: 'x' } }); const a3 = armed({ armed: true, until: NOW + 3600000 });
  await tick(w3, a3);
  assert.ok(/needs a look/.test(a3.log.events[0].detail) && /MAY OR MAY NOT/.test(a3.log.events[0].detail));
  const w4 = world(); const a4 = armed({ armed: true, until: NOW - 1 });
  await tick(w4, a4);
  assert.deepStrictEqual(a4.log.events.map((e) => e.detail), ['expired after 3 hours with nothing sent']);
  const w5 = world(); w5.store.halted = async () => { throw new Error('database down'); }; const a5 = armed({ armed: true, until: NOW + 3600000 });
  await assert.rejects(() => tick(w5, a5), /database down/);
  assert.ok(/stopped on an error: database down/.test(a5.log.events[0].detail));
  const w6 = world(); const a6 = armed({ armed: true, until: NOW + 3600000 });
  await tick(w6, a6, { quotes: [] });
  assert.strictEqual(a6.log.events.length, 0, 'a minute with no signal logs nothing');
  const w7 = world(); const a7 = armed({ armed: true, until: NOW + 3600000 }, true);
  const r7 = await tick(w7, a7);
  assert.ok(r7.ok && w7.posts.length === 1 && a7.arm.armed === false, 'a failing log must not stop the order or the disarm');
  const w8 = world(); const a8 = armed({ armed: true, until: NOW - 1 }, true);
  assert.strictEqual((await tick(w8, a8)).skipped, 'expired');
  assert.strictEqual(a8.arm.armed, false, 'a failing log must not keep an expired arm armed');
  // No logEvent at all is fine too.
  const w9 = world(); const a9 = armed({ armed: true, until: NOW + 3600000 });
  assert.ok((await tick(w9, a9, { logEvent: undefined })).ok);
  // Wiring: the arm function logs armed and disarmed, the scan passes the log in, and only the server can write it.
  const arm = /exports\.kalshiLiveArm = onCall\(([\s\S]*?)\n\}\);/.exec(fnSrc)[1];
  assert.ok(/kind: "armed"/.test(arm) && /kind: "disarmed"/.test(arm) && /collection\("kalshiLiveEvents"\)/.test(arm), 'arming and disarming are logged');
  assert.ok(/logEvent: \(e\) => db\.collection\("kalshiLiveEvents"\)\.add\(e\)/.test(fnSrc), 'the scheduled scan writes its endings to the log');
  const ev = /match \/kalshiLiveEvents\/\{id\} \{([\s\S]*?)\n    \}/.exec(rules);
  assert.ok(ev && /allow read: if isAdmin\(\);/.test(ev[1]) && /allow write: if false;/.test(ev[1]), 'admin read, no client write');
};

gates.L19 = () => {
  // Wiring. The arm function only flips a document: no order code, no key. The scheduled one does nothing unless armed.
  const am = /exports\.kalshiLiveArm = onCall\(([\s\S]*?)\n\}\);/.exec(fnSrc);
  assert.ok(am, 'kalshiLiveArm not found');
  const a = am[1];
  assert.ok(a.indexOf('assertKalshiAdmin(request.auth)') > -1 && a.indexOf('assertKalshiAdmin') < a.indexOf('.set('), 'admin check first');
  assert.ok(!/runLiveTest|runArmedTick|KALSHI_LIVE_KEY|KALSHI_LIVE_PRIVATE|portfolio|fetch/.test(a), 'arming touches no key and sends no request');
  assert.ok(/request\.data && request\.data\.on === true/.test(a), 'the only thing read from the caller is an explicit true');
  assert.ok(/KALSHI_LIVE_ENABLED\.value\(\) !== "on"/.test(a) && /ref\.set\(\{ armed: true, since: now, until: now \+ live\.ARM_MS,/.test(a) && /return \{ armed: true, until: now \+ live\.ARM_MS \}/.test(a), 'refuses while the switch is off, and the expiry written is the server\'s own 3 hours');
  const sm = /exports\.kalshiLiveArmed = onSchedule\(([\s\S]*?)\n\);/.exec(fnSrc);
  assert.ok(sm, 'kalshiLiveArmed not found');
  const s = sm[1];
  assert.ok(/schedule: "every 1 minutes"/.test(s) && /secrets: \[KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY\]/.test(s) && !/KALSHI_DEMO/.test(s), 'its own live secrets only');
  assert.ok(/retryCount: 0/.test(s) && !/retryCount: [1-9]/.test(s), 'a failed run is never retried by the platform');
  const load = s.indexOf('live.loadQuotes'), guard = s.indexOf('arm.armed === true && arm.until > now');
  assert.ok(guard > -1 && load > guard, 'prices are loaded only inside the armed branch');
  assert.ok(/live\.runArmedTick\(args\)/.test(s) && !/live\.runLiveTest/.test(s), 'it only ever goes through runArmedTick');
  assert.ok(fnSrc.indexOf('exports.kalshiLiveArmed') < fnSrc.indexOf('exports.kalshiBookRecorder ='), 'defined before the recorder, so the no-order-code slice still covers it');
  const m = /match \/kalshiLiveControl\/\{id\} \{([\s\S]*?)\n    \}/.exec(rules);
  assert.ok(m && /allow read: if isAdmin\(\);/.test(m[1]) && /allow write: if false;/.test(m[1]), 'admin read, no client write');
  // The arm controls were removed from the page with the single test; only the 24 hour session is started from it.
  assert.ok(!/kalLiveArm|kalshiLiveArmFn/.test(html), 'the page has no arm controls');
};

gates.L20 = () => {
  // The signature must verify against the public key over timestamp + METHOD + path, query left out (kept from the
  // retired demo trader's gates: the live module now owns signing).
  const sig = live.signRequest(pem, '1703123456789', 'GET', '/trade-api/v2/portfolio/balance?limit=5');
  const msg = Buffer.from('1703123456789GET/trade-api/v2/portfolio/balance');
  assert.ok(crypto.verify(null, msg, ed.publicKey, Buffer.from(sig, 'base64')), 'Ed25519 signature verifies');
  assert.ok(!crypto.verify(null, Buffer.from('1703123456789POST/trade-api/v2/portfolio/balance'), ed.publicKey, Buffer.from(sig, 'base64')), 'a different method must not verify');
  assert.ok(!crypto.verify(null, Buffer.from('1703123456790GET/trade-api/v2/portfolio/balance'), ed.publicKey, Buffer.from(sig, 'base64')), 'a different timestamp must not verify');
  const rsa = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
  const rs = live.signRequest(rsa.privateKey.export({ type: 'pkcs8', format: 'pem' }), '1', 'POST', '/trade-api/v2/portfolio/events/orders');
  const pss = { key: rsa.publicKey, padding: crypto.constants.RSA_PKCS1_PSS_PADDING, saltLength: crypto.constants.RSA_PSS_SALTLEN_DIGEST };
  assert.ok(crypto.verify('sha256', Buffer.from('1POST/trade-api/v2/portfolio/events/orders'), pss, Buffer.from(rs, 'base64')), 'RSA-PSS signature verifies');
  const flat = pem.replace(/\n/g, '\\n');   // a secret pasted with literal \n still loads
  assert.ok(crypto.verify(null, msg, ed.publicKey, Buffer.from(live.signRequest(flat, '1703123456789', 'GET', '/trade-api/v2/portfolio/balance'), 'base64')));
  assert.throws(() => live.signRequest(crypto.generateKeyPairSync('ec', { namedCurve: 'P-256' }).privateKey.export({ type: 'pkcs8', format: 'pem' }), '1', 'GET', '/x'), /unsupported key type/);
};

gates.L21 = () => {
  // Order code lives in exactly one module, and nothing of the retired demo trader remains.
  const fnDir = path.join(root, 'functions');
  const offenders = fs.readdirSync(fnDir).filter((f) => f.endsWith('.js') && /portfolio\/events\/orders/.test(fs.readFileSync(path.join(fnDir, f), 'utf8')));
  assert.deepStrictEqual(offenders, ['kalshiLiveLib.js'], 'order code lives in exactly one module');
  assert.ok(!fs.existsSync(path.join(fnDir, 'kalshiDemoLib.js')), 'the demo module is gone');
  assert.ok(!/kalshiDemo|KALSHI_DEMO/i.test(fnSrc + html + rules), 'no demo function, secret, collection or page card is left');
};

gates.L11 = () => {
  // The signal library, the recorder and the watchdog stay separate from the live order code.
  for (const f of ['kalshiSignalLib.js', 'kalshiBookLib.js', 'kalshiWatchdogLib.js']) {
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

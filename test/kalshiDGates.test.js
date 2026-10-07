'use strict';
// Gates for the rule D forward test (real money). Each states the consequence, not the mechanism.
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
  ticker, status: 'active', close_time: iso(NOW + 120000), yes_bid_dollars: '0.0800', yes_ask_dollars: '0.0900' }, over) });

function world(opts = {}) {
  const calls = [], posts = [], docs = new Map(), events = [];
  const sess = Object.assign({ active: true, until: NOW + 3600000, ordersSent: 0, startCash: 100 }, opts.session || {});
  const store = {
    async halted() { return opts.halted === true; },
    async hasUnresolved() { return opts.unresolved === true || [...docs.values()].some((d) => d.status === 'sending' || d.status === 'unknown'); },
    async createTest(id, data) { if (docs.has(id)) return false; docs.set(id, { ...data }); return true; },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
  };
  const fetchFn = async (url, o) => {
    calls.push({ url, method: o.method, headers: o.headers, body: o.body ? JSON.parse(o.body) : null });
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/markets/')) {
      const tk = decodeURIComponent(url.split('/markets/')[1].split('?')[0]);
      const over = (opts.fresh && opts.fresh[tk]) || {};
      return reply(opts.marketStatus || 200, { market: { status: 'active', close_time: iso(NOW + 120000), exchange_index: 2, yes_bid_dollars: '0.0800', yes_ask_dollars: '0.0900', ...over } });
    }
    if (url.endsWith('/portfolio/balance')) return reply(opts.balStatus || 200, opts.balance || { balance_breakdown: [{ balance: '70.0000', exchange_index: 2 }, { balance: '30.0000', exchange_index: 0 }] });
    if (url.includes('/portfolio/orders')) return reply(200, { orders: opts.existing || [] });
    if (o.method === 'POST') {
      posts.push(JSON.parse(o.body));
      if (opts.postThrows) throw new Error('timeout');
      if (opts.post) return reply(opts.post.status, opts.post.body);
      return reply(201, { order_id: 'ord-' + posts.length, fill_count: '1.00', remaining_count: '0.00', average_fill_price: '0.0900', average_fee_paid: '0.0006' });
    }
    throw new Error('unexpected ' + o.method + ' ' + url);
  };
  return { calls, posts, docs, store, fetchFn, sess, events };
}
const tick = (w, over = {}) => live.runDTick({
  session: w.sess, now: NOW, setSession: async (p) => { Object.assign(w.sess, p); }, logEvent: async (e) => { w.events.push(e); },
  quotes: [quote()], active: true, enabled: true, store: w.store, keyId: 'live-key', pem, fetchFn: w.fetchFn, ...over,
});

// The rule is D as found: a side whose FRESH price is 3c to 20c inclusive, a real book, and a spread of 1c or less. Nothing else.
gates.D1 = () => {
  const p = (bid, ask) => live.dPick({ yes_bid_dollars: String(bid), yes_ask_dollars: String(ask) });
  assert.strictEqual(p(0.02, 0.03).side, 'yes', '3c is inside');
  assert.strictEqual(p(0.19, 0.20).side, 'yes', '20c is inside');
  assert.strictEqual(p(0.20, 0.21), null, '21c is outside');
  assert.strictEqual(p(0.01, 0.02), null, '2c is outside');
  assert.deepStrictEqual([p(0.91, 0.92).side, p(0.91, 0.92).price], ['no', 0.09], 'the NO side is priced at 1 minus the YES bid');
  assert.strictEqual(p(0.80, 0.81).side, 'no', 'a NO at exactly 20c is inside');
  assert.strictEqual(p(0.08, 0.10), null, 'a spread of 2c is refused');
  assert.ok(p(0.08, 0.09), 'a spread of exactly 1c is accepted');
  assert.strictEqual(p(0.50, 0.51), null, 'a coin flip is not D');
  assert.strictEqual(p(0.001, 1.0), null, 'an empty book is not a quote');
  const y = p(0.085, 0.0955);
  assert.strictEqual(y, null, 'tenth-cent prices count for the spread: 1.05c is refused');
  const z = p(0.0855, 0.0945);
  assert.deepStrictEqual([z.side, z.price, z.limit], ['yes', 0.0945, 0.10], 'the YES limit rounds UP to the cent so it still takes the ask');
  const n = p(0.9055, 0.9145);
  assert.deepStrictEqual([n.side, n.limit, n.worst], ['no', 0.90, 0.10], 'the NO limit rounds DOWN so it still crosses, and the worst price is bounded');
};

// Happy path: ONE contract at the touch, immediate-or-cancel, signed, recorded first, id derived from the market and kept apart from L1's.
gates.D2 = async () => {
  const w = world();
  const r = await tick(w);
  assert.ok(r.ok, JSON.stringify(r));
  assert.strictEqual(w.posts.length, 1);
  const b = w.posts[0];
  assert.deepStrictEqual([b.count, b.side, b.price, b.time_in_force, b.self_trade_prevention_type], ['1', 'bid', '0.09', 'immediate_or_cancel', 'taker_at_cross']);
  assert.strictEqual(b.client_order_id, 'D-' + T, 'derived from the market, never random, and never L1\'s id');
  assert.strictEqual(b.exchange_index, 2);
  const post = w.calls.find((c) => c.method === 'POST');
  assert.ok(crypto.verify(null, Buffer.from(post.headers['KALSHI-ACCESS-TIMESTAMP'] + 'POST/trade-api/v2/portfolio/events/orders'), ed.publicKey, Buffer.from(post.headers['KALSHI-ACCESS-SIGNATURE'], 'base64')), 'signed over the full path');
  const rec = w.docs.get('D-' + T);
  assert.ok(rec.status === 'filled' && rec.strategy === 'D' && rec.count === 1);
  assert.strictEqual(w.sess.ordersSent, 1);
  assert.ok(w.calls.every((c) => new URL(c.url).hostname === 'external-api.kalshi.com'), 'production only');
};

// A NO order sells YES at the bid.
gates.D3 = async () => {
  const w = world({ fresh: { [T]: { yes_bid_dollars: '0.9100', yes_ask_dollars: '0.9200' } } });
  await tick(w);
  assert.deepStrictEqual([w.posts[0].side, w.posts[0].price], ['ask', '0.91']);
};

// Bitcoin only, and about 2 minutes before the close: gold, a market 13 minutes out, 6 minutes out, or under 90 seconds is never ordered, on the list
// or on the fresh read.
gates.D4 = async () => {
  const gold = world();
  await tick(gold, { quotes: [quote({}, 'KXGOLD15M', 'KXGOLD15M-26OCT071415-15')] });
  assert.strictEqual(gold.posts.length, 0, 'gold is never traded by D');
  for (const ms of [13 * 60000, 6 * 60000, 60000]) {
    const w = world();
    const r = await tick(w, { quotes: [quote({ close_time: iso(NOW + ms) })] });
    assert.strictEqual(r.skipped, 'no market in the window', ms + 'ms');
    assert.strictEqual(w.posts.length, 0);
  }
  const moved = world({ fresh: { [T]: { close_time: iso(NOW + 60000) } } });     // the list said 2 minutes; the fresh read says 1
  await tick(moved);
  assert.strictEqual(moved.posts.length, 0, 'the fresh read decides');
};

// One order per market, however many ticks see it: the duplicate protection, and L1's order on the same market does not block it.
gates.D5 = async () => {
  const w = world();
  await tick(w); await tick(w); await tick(w);
  assert.strictEqual(w.posts.length, 1, 'a market is never ordered twice');
  const withL1 = world();
  withL1.docs.set('L1-' + T, { status: 'filled', strategy: 'L1' });
  await tick(withL1);
  assert.strictEqual(withL1.posts.length, 1, 'an L1 order on the same market is a different id and does not block D');
};

// A price or spread that has left D's shape on the fresh read is not bought, whatever the list said.
gates.D6 = async () => {
  for (const book of [{ yes_bid_dollars: '0.2500', yes_ask_dollars: '0.2600' }, { yes_bid_dollars: '0.0800', yes_ask_dollars: '0.1000' }, { yes_bid_dollars: '0.5000', yes_ask_dollars: '0.5100' }]) {
    const w = world({ fresh: { [T]: book } });
    await tick(w);
    assert.strictEqual(w.posts.length, 0, JSON.stringify(book));
    assert.strictEqual(w.docs.size, 0, 'and nothing was recorded');
  }
};

// Everything that must stop it, stops it, and sends nothing.
gates.D7 = async () => {
  for (const [name, over, wopts] of [
    ['switch off', { enabled: false }, {}],
    ['exchange inactive', { active: false }, {}],
    ['halted', {}, { halted: true }],
    ['balance unreadable', {}, { balStatus: 500 }],
    ['balance unrecognised', {}, { balance: { weird: true } }],
    ['market unreadable', {}, { marketStatus: 500 }],
  ]) {
    const w = world(wopts);
    await tick(w, over);
    assert.strictEqual(w.posts.length, 0, name + ' must send nothing');
    assert.strictEqual(w.sess.active, true, name + ' leaves the session running for the next minute');
  }
  const un = world({ unresolved: true });
  await tick(un);
  assert.strictEqual(un.posts.length, 0);
  assert.strictEqual(un.sess.endedBecause, 'attempted', 'an unresolved earlier order ends the session until the owner looks');
  const none = world({ session: { active: false } });
  assert.strictEqual((await tick(none)).skipped, 'no session');
  assert.strictEqual(none.posts.length, 0);
};

// The funds are per shard: a shard that cannot cover the order skips the market.
gates.D8 = async () => {
  const w = world({ balance: { balance_breakdown: [{ balance: '0.3000', exchange_index: 2 }, { balance: '90.0000', exchange_index: 0 }] }, session: { startCash: 90.3 } });
  await tick(w);
  assert.strictEqual(w.posts.length, 0, 'money on shard 0 does not pay for shard 2');
};

// THE loss stop: cash more than $4 below where it started ends the session before any order; $3.50 down does not.
gates.D9 = async () => {
  const w = world({ session: { startCash: 100 }, balance: { balance_breakdown: [{ balance: '95.9000', exchange_index: 2 }] } });
  await tick(w);
  assert.strictEqual(w.posts.length, 0);
  assert.deepStrictEqual([w.sess.active, w.sess.endedBecause], [false, 'loss stop']);
  const ok = world({ session: { startCash: 100 }, balance: { balance_breakdown: [{ balance: '96.5000', exchange_index: 2 }] } });
  await tick(ok);
  assert.strictEqual(ok.posts.length, 1, '$3.50 down is inside the allowance');
  const first = world({ session: { startCash: null } });
  await tick(first);
  assert.strictEqual(first.sess.startCash, 100, 'the first tick records the starting cash');
};

// The order limit and the 24 hour limit end the session, and the constants are what the terms say.
gates.D10 = async () => {
  const lim = world({ session: { ordersSent: 60 } });
  await tick(lim);
  assert.deepStrictEqual([lim.posts.length, lim.sess.endedBecause], [0, 'limit']);
  const exp = world({ session: { until: NOW - 1 } });
  await tick(exp);
  assert.deepStrictEqual([exp.posts.length, exp.sess.endedBecause], [0, 'expired']);
  assert.deepStrictEqual([live.D_MAX_ORDERS, live.D_SESSION_MS, live.D_LOSS_STOP, live.D_SPREAD_MAX], [60, 24 * 3600 * 1000, 4, 0.01]);
  assert.deepStrictEqual([live.D_BAND, live.D_WINDOW_MS], [[0.03, 0.20], [95000, 155000]]);
};

// An answer that is lost or refused ends the session, is recorded, and is never retried.
gates.D11 = async () => {
  for (const [name, wopts, status, said] of [
    ['lost answer', { post: { status: 503, body: 'oops' } }, 'unknown', /MAY OR MAY NOT/],
    ['network error', { postThrows: true }, 'unknown', /MAY OR MAY NOT/],
    ['refusal', { post: { status: 400, body: { error: 'bad' } } }, 'error', /refused/],
    ['duplicate id', { post: { status: 409, body: { error: 'exists' } } }, 'unknown', /already exists/],
  ]) {
    const w = world(wopts);
    await tick(w, { quotes: [quote(), quote({}, 'KXBTC15M', 'KXBTC15M-26OCT071430-30')] });
    assert.strictEqual(w.posts.length, 1, name + ': nothing is retried and the next market is not tried');
    assert.deepStrictEqual([w.sess.active, w.sess.endedBecause], [false, 'attempted'], name);
    assert.strictEqual(w.docs.get('D-' + T).status, status, name + ' is recorded for the owner to look at');
    assert.ok(said.test(w.events.map((e) => e.detail).join(' ')), name + ' tells the owner what to check');
  }
  const nofill = world({ post: { status: 201, body: { order_id: 'o', fill_count: '0.00', remaining_count: '0.00' } } });
  await tick(nofill);
  assert.strictEqual(nofill.docs.get('D-' + T).status, 'no fill');
  assert.strictEqual(nofill.sess.active, true, 'an IOC that did not fill is normal, the session carries on');
};

// Wiring: its own callable with a server-set expiry, run by the scheduled function beside the L1 session, never beside a single armed test, and the
// page asks twice. Nothing else is scheduled and the L1 session code is untouched by this feature.
gates.D12 = () => {
  assert.ok(/exports\.kalshiDSession = onCall\(async \(request\) => \{\s*await assertKalshiAdmin\(request\.auth\);/.test(fnSrc), 'admin only');
  assert.ok(/ref\.set\(\{ active: true, since: now, until: now \+ live\.D_SESSION_MS/.test(fnSrc), 'the expiry is set by the server, not the page');
  assert.ok(/KALSHI_LIVE_ENABLED\.value\(\) !== "on"/.test(fnSrc.slice(fnSrc.indexOf('exports.kalshiDSession'))), 'refuses when the server switch is off');
  const sched = fnSrc.slice(fnSrc.indexOf('exports.kalshiLiveArmed'), fnSrc.indexOf('exports.kalshiBookRecorder'));
  assert.ok(/live\.runDTick\(/.test(sched) && /live\.runL1Tick\(/.test(sched), 'both sessions run from the scheduled function');
  assert.ok(/if \(sessionDOn && !armedOn\)/.test(sched), 'never beside an armed single test');
  assert.ok(/The rule D session is running\. Stop it before arming/.test(fnSrc) && /A single test order is armed\. Disarm it before starting rule D/.test(fnSrc), 'each refuses while the other is on');
  assert.deepStrictEqual([...fnSrc.matchAll(/exports\.(\w+) = onSchedule\(/g)].map((x) => x[1]), ['kalshiLiveArmed', 'kalshiBookRecorder']);
  assert.ok(fnSrc.indexOf('exports.kalshiDSession') < fnSrc.indexOf('exports.kalshiBookRecorder'), 'defined before the recorder, which stays last');
  assert.ok(/kalDStart'\)[\s\S]{0,400}addEventListener\('click', function\(\)\{ msg\.textContent = ''; ask\(true\); \}\)/.test(html), 'the first click only asks');
  const yes = html.slice(html.indexOf("yes.addEventListener('click', function(){\n      var api = window.__shwoopAPI;\n      if(!api || !api.kalshiDSession"));
  assert.ok(/api\.kalshiDSession\(true\)/.test(yes.slice(0, 700)), 'the confirm click starts it');
  assert.ok(/id="kalDStop"/.test(html) && /api\.kalshiDSession\(false\)/.test(html), 'there is a stop button');
  assert.ok(/data-card="sessionD"/.test(html) && !/\['sessionD'/.test(html), 'the D card cannot be hidden, so its Stop button is always on screen');
  assert.ok(/httpsCallable\(functions, 'kalshiDSession'\)/.test(html));
};

// Order code still lives in exactly one module, ids are never random, and D never reads a result to choose what to buy.
gates.D13 = () => {
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  const d = src.slice(src.indexOf('const D_BAND'), src.indexOf('module.exports'));
  assert.ok(!/Math\.random|randomUUID/.test(d) && !/demo\.kalshi|demo-api/.test(d));
  assert.ok(!/res\.result|\.result\b/.test(d), 'no result is read to decide a trade');
  const offenders = fs.readdirSync(path.join(root, 'functions')).filter((f) => f.endsWith('.js') && /portfolio\/events\/orders/.test(fs.readFileSync(path.join(root, 'functions', f), 'utf8').replace(/\/\/[^\n]*/g, '')));
  assert.deepStrictEqual(offenders, ['kalshiLiveLib.js']);
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();

'use strict';
// Gates for the 24 hour L1 session (real money). Each states the consequence, not the mechanism.
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

// The rule is L1 as written: the side whose FRESH price is 88c to 97c, inclusive, either side, nothing else.
gates.N1 = () => {
  const p = (bid, ask) => live.l1Pick({ yes_bid_dollars: String(bid), yes_ask_dollars: String(ask) });
  assert.strictEqual(p(0.87, 0.88).side, 'yes', '88c is inside');
  assert.strictEqual(p(0.96, 0.97).side, 'yes', '97c is inside');
  assert.strictEqual(p(0.97, 0.98), null, '98c is outside');
  assert.strictEqual(p(0.86, 0.87), null, '87c is outside');
  assert.deepStrictEqual([p(0.03, 0.04).side, p(0.03, 0.04).price], ['no', 0.97], 'a NO at exactly 97c survives floating point');
  assert.strictEqual(p(0.12, 0.13).side, 'no', 'NO at 88c is inside');
  assert.strictEqual(p(0.50, 0.52), null, 'a coin flip is not L1');
  assert.strictEqual(p(0.001, 1.0), null, 'an empty book is not a quote');
  assert.strictEqual(p(0.80, 0.95), null, 'a spread wider than 10c is not a quote');
  // Mid-book prices come in tenths of a cent. The limit sent can only cross, and the band is judged on the real price.
  const y = p(0.88, 0.885);
  assert.deepStrictEqual([y.price, y.limit], [0.885, 0.89], 'YES limit rounds UP to the cent so it still takes the ask');
  const n = p(0.115, 0.12);
  assert.deepStrictEqual([n.side, n.limit, n.worst], ['no', 0.11, 0.89], 'NO limit rounds DOWN so it still crosses, and the worst price is bounded');
};

// The happy path: ONE contract at the touch, immediate-or-cancel, signed, recorded first, id derived from the market.
gates.N2 = async () => {
  const w = world();
  const r = await tick(w);
  assert.ok(r.ok, JSON.stringify(r));
  assert.strictEqual(w.posts.length, 1);
  const b = w.posts[0];
  assert.deepStrictEqual([b.count, b.side, b.price, b.time_in_force, b.self_trade_prevention_type], ['1', 'bid', '0.91', 'immediate_or_cancel', 'taker_at_cross']);
  assert.strictEqual(b.client_order_id, 'L1-' + T, 'derived from the market, never random');
  assert.strictEqual(b.exchange_index, 2);
  const post = w.calls.find((c) => c.method === 'POST');
  assert.ok(crypto.verify(null, Buffer.from(post.headers['KALSHI-ACCESS-TIMESTAMP'] + 'POST/trade-api/v2/portfolio/events/orders'), ed.publicKey, Buffer.from(post.headers['KALSHI-ACCESS-SIGNATURE'], 'base64')), 'signed over the full path');
  const rec = w.docs.get('L1-' + T);
  assert.ok(rec.status === 'filled' && rec.strategy === 'L1' && rec.count === 1);
  assert.strictEqual(w.sess.ordersSent, 1);
  assert.ok(w.events.some((e) => e.kind === 'order'));
  assert.ok(w.calls.every((c) => new URL(c.url).hostname === 'external-api.kalshi.com'), 'production only');
};

// A NO order sells YES at the bid.
gates.N3 = async () => {
  const w = world({ fresh: { [T]: { yes_bid_dollars: '0.0800', yes_ask_dollars: '0.0900' } } });
  await tick(w);
  assert.deepStrictEqual([w.posts[0].side, w.posts[0].price], ['ask', '0.08']);
};

// The decision is made about 6 minutes before the close: a market 13 minutes out or 2 minutes out is never ordered, on the
// list or on the fresh read.
gates.N4 = async () => {
  const far = world();
  const r1 = await tick(far, { quotes: [quote({ close_time: iso(NOW + 13 * 60000) })] });
  assert.strictEqual(r1.skipped, 'no market in the window');
  assert.strictEqual(far.posts.length, 0);
  const late = world();
  await tick(late, { quotes: [quote({ close_time: iso(NOW + 120000) })] });
  assert.strictEqual(late.posts.length, 0);
  const moved = world({ fresh: { [T]: { close_time: iso(NOW + 120000) } } });     // the list said 6 minutes; the fresh read says 2
  await tick(moved);
  assert.strictEqual(moved.posts.length, 0, 'the fresh read decides');
};

// One order per market, however many ticks see it: THE duplicate protection.
gates.N5 = async () => {
  const w = world();
  await tick(w);
  await tick(w);
  await tick(w);
  assert.strictEqual(w.posts.length, 1, 'a market is never ordered twice');
  const both = world();
  await tick(both, { quotes: [quote(), quote({}, 'KXGOLD15M', 'KXGOLD15M-26OCT071415-15')] });
  assert.strictEqual(both.posts.length, 2, 'one order per market, so both series trade');
  assert.strictEqual(both.posts[1].exchange_index, 0, 'gold is placed on its own shard');
};

// A price that has left the band on the fresh read is not bought, whatever the list said.
gates.N6 = async () => {
  const w = world({ fresh: { [T]: { yes_bid_dollars: '0.9600', yes_ask_dollars: '0.9900' } } });
  await tick(w);
  assert.strictEqual(w.posts.length, 0, '99c is outside the band');
  assert.strictEqual(w.docs.size, 0, 'and nothing was recorded');
};

// Everything that must stop it, stops it, and sends nothing.
gates.N7 = async () => {
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

// The funds are per shard: a shard that cannot cover the order skips that market, it is not paid for from another shard.
gates.N8 = async () => {
  const w = world({ balance: { balance_breakdown: [{ balance: '0.5000', exchange_index: 2 }, { balance: '90.0000', exchange_index: 0 }] }, session: { startCash: 90.5 } });
  await tick(w);
  assert.strictEqual(w.posts.length, 0, 'money on shard 0 does not pay for shard 2');
};

// THE loss stop follows the BOT's trades. Settled results count, open trades count as lost, and the account's cash does not.
const botTrade = (n, over = {}) => [`L1-OLD-${n}`, Object.assign({ strategy: 'L1', ticker: `OLD-${n}`, side: 'yes', status: 'filled', fillCount: '1.00', maxCost: 0.92, ts: NOW - 3600000 }, over)];
gates.N9 = async () => {
  // Seven lost trades (7 x 0.92 = $6.44) leave room; the eighth reaches $7.36 and stops the session before any order.
  const seed = (w, n, over) => { for (let i = 0; i < n; i++) { const [id, d] = botTrade(i, over); w.docs.set(id, d); } };
  const lost = {}; for (let i = 0; i < 8; i++) lost[`OLD-${i}`] = 'no';
  const w = world({ results: lost }); seed(w, 8);
  await tick(w);
  assert.strictEqual(w.posts.length, 0);
  assert.deepStrictEqual([w.sess.active, w.sess.endedBecause], [false, 'loss stop']);
  assert.ok([...w.docs.values()].filter((d) => d.settled === true).length === 8, 'each settled result is kept on its record, so it is read once');
  const lostSeven = {}; for (let i = 0; i < 7; i++) lostSeven[`OLD-${i}`] = 'no';
  const ok = world({ results: lostSeven }); seed(ok, 7);
  await tick(ok);
  assert.strictEqual(ok.posts.length, 1, '$6.44 down is inside the allowance');
  // Open trades are counted as lost: eight unsettled ones stop it just as eight settled losses do.
  const open = world(); seed(open, 8);
  await tick(open);
  assert.deepStrictEqual([open.posts.length, open.sess.endedBecause], [0, 'loss stop']);
  // Wins offset losses: eight settled wins are never a reason to stop.
  const wins = {}; for (let i = 0; i < 8; i++) wins[`OLD-${i}`] = 'yes';
  const won = world({ results: wins }); seed(won, 8);
  await tick(won);
  assert.strictEqual(won.posts.length, 1);
  // Cash is not the measure: the account being $50 down because of the owner's own trades changes nothing.
  const manual = world({ session: { startCash: 150 } });
  await tick(manual);
  assert.strictEqual(manual.posts.length, 1, 'manual trades moving the account do not trip the bot stop');
  // Trades from before this session are not counted, and an unreadable record fails closed.
  const before = world({ session: { since: NOW - 1000 } }); seed(before, 8);
  await tick(before);
  assert.strictEqual(before.posts.length, 1, 'earlier trades are not this session');
  const down = world({ tradesThrow: true });
  await tick(down);
  assert.deepStrictEqual([down.posts.length, down.sess.active], [0, true], 'if the bot trades cannot be read, nothing is sent and the session keeps running');
  // Orders that did not fill cost nothing.
  const nofill = world(); seed(nofill, 8, { fillCount: '0.00', status: 'no fill' });
  await tick(nofill);
  assert.strictEqual(nofill.posts.length, 1, 'no-fills are not losses');
  const first = world({ session: { startCash: null } });
  await tick(first);
  assert.strictEqual(first.sess.startCash, 100, 'the first tick still records the starting cash');
};

// The order limit and the 24 hour limit end the session.
gates.N10 = async () => {
  const lim = world({ session: { ordersSent: 200 } });
  await tick(lim);
  assert.deepStrictEqual([lim.posts.length, lim.sess.endedBecause], [0, 'limit']);
  const exp = world({ session: { until: NOW - 1 } });
  await tick(exp);
  assert.deepStrictEqual([exp.posts.length, exp.sess.endedBecause], [0, 'expired']);
  assert.ok(live.L1_MAX_ORDERS >= 2 * 96, 'the order backstop can never end a 24 hour session early');
  assert.strictEqual(live.L1_SESSION_MS, 24 * 3600 * 1000);
  assert.strictEqual(live.L1_LOSS_STOP, 7);
};

// An answer that is lost or refused ends the session, is recorded, and is never retried.
gates.N11 = async () => {
  for (const [name, wopts, status, said] of [
    ['lost answer', { post: { status: 503, body: 'oops' } }, 'unknown', /MAY OR MAY NOT/],
    ['network error', { postThrows: true }, 'unknown', /MAY OR MAY NOT/],
    ['refusal', { post: { status: 400, body: { error: 'bad' } } }, 'error', /refused/],
    ['duplicate id', { post: { status: 409, body: { error: 'exists' } } }, 'unknown', /already exists/],
  ]) {
    const w = world(wopts);
    await tick(w, { quotes: [quote(), quote({}, 'KXGOLD15M', 'KXGOLD15M-26OCT071415-15')] });
    assert.strictEqual(w.posts.length, 1, name + ': nothing is retried and the next market is not tried');
    assert.deepStrictEqual([w.sess.active, w.sess.endedBecause], [false, 'attempted'], name);
    assert.strictEqual(w.docs.get('L1-' + T).status, status, name + ' is recorded for the owner to look at');
    assert.ok(said.test(w.events.map((e) => e.detail).join(' ')), name + ' tells the owner what to check');
  }
  const nofill = world({ post: { status: 201, body: { order_id: 'o', fill_count: '0.00', remaining_count: '0.00' } } });
  await tick(nofill);
  assert.strictEqual(nofill.docs.get('L1-' + T).status, 'no fill');
  assert.strictEqual(nofill.sess.active, true, 'an IOC that did not fill is normal, the session carries on');
};

// Worst case in the cost cap: a YES limit of 97c plus its fee is far under $2, and the cap is still checked.
gates.N12 = () => {
  assert.ok(live.LIVE_CAP === 2);
  const p = live.l1Pick({ yes_bid_dollars: '0.9600', yes_ask_dollars: '0.9700' });
  assert.ok(p.worst + 0.07 * p.worst * (1 - p.worst) < live.LIVE_CAP);
};

// Wiring: the session is switched by a server callable with a server-set expiry; the scheduled arm function runs it; nothing
// else is scheduled; it refuses to run beside a single armed test order; and the page asks twice.
gates.N13 = () => {
  assert.ok(/exports\.kalshiL1Session = onCall\(async \(request\) => \{\s*await assertKalshiAdmin\(request\.auth\);/.test(fnSrc), 'admin only');
  assert.ok(/ref\.set\(\{ active: true, since: now, until: now \+ live\.L1_SESSION_MS/.test(fnSrc), 'the expiry is set by the server, not the page');
  assert.ok(/KALSHI_LIVE_ENABLED\.value\(\) !== "on"/.test(fnSrc.slice(fnSrc.indexOf('exports.kalshiL1Session'))), 'refuses when the server switch is off');
  assert.ok(/live\.runL1Tick\(/.test(fnSrc.slice(fnSrc.indexOf('exports.kalshiLiveArmed'))), 'run by the scheduled function');
  assert.ok(/if \(sessionOn && !armedOn\)/.test(fnSrc), 'never beside an armed single test');
  assert.ok(/The 24 hour L1 session is running\. Stop it before arming/.test(fnSrc), 'arming refuses while the session runs');
  assert.ok(/A single test order is armed\. Disarm it before starting/.test(fnSrc), 'starting refuses while armed');
  assert.deepStrictEqual([...fnSrc.matchAll(/exports\.(\w+) = onSchedule\(/g)].map((x) => x[1]), ['kalshiLiveArmed', 'kalshiBookRecorder']);
  assert.ok(fnSrc.indexOf('exports.kalshiL1Session') < fnSrc.indexOf('exports.kalshiBookRecorder'), 'defined before the recorder, which stays last');
  // The page: two clicks, a server call only on the confirm click, and a visible stop.
  assert.ok(/kalL1Start'\)[\s\S]{0,400}addEventListener\('click', function\(\)\{ msg\.textContent = ''; ask\(true\); \}\)/.test(html), 'the first click only asks');
  const yes = html.slice(html.indexOf("yes.addEventListener('click', function(){\n      var api = window.__shwoopAPI;\n      if(!api || !api.kalshiL1Session"));
  assert.ok(/api\.kalshiL1Session\(true\)/.test(yes.slice(0, 700)), 'the confirm click starts it');
  assert.ok(/id="kalL1Stop"/.test(html) && /api\.kalshiL1Session\(false\)/.test(html), 'there is a stop button');
  assert.ok(/httpsCallable\(functions, 'kalshiL1Session'\)/.test(html));
};

// Order code still lives in exactly one module, and the session never reads a result to choose what to buy.
gates.N14 = () => {
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  const l1 = src.slice(src.indexOf('const L1_BAND'), src.indexOf('module.exports'));
  assert.ok(!/Math\.random|randomUUID/.test(l1), 'order ids are never random');
  assert.ok(!/demo\.kalshi|demo-api/.test(l1));
  const offenders = fs.readdirSync(path.join(root, 'functions')).filter((f) => f.endsWith('.js') && /portfolio\/events\/orders/.test(fs.readFileSync(path.join(root, 'functions', f), 'utf8').replace(/\/\/[^\n]*/g, '')));
  assert.deepStrictEqual(offenders, ['kalshiLiveLib.js']);
};

// Bitcoin and gold close together and share a shard. The balance is read once per tick, so money committed to the first
// order must come off what the second may use: otherwise the second is sent without the funds and Kalshi's refusal ends the session.
gates.N15 = async () => {
  const G = 'KXGOLD15M-26OCT071415-15';
  const w = world({ session: { startCash: 2 }, balance: { balance_breakdown: [{ balance: '2.0000', exchange_index: 2 }] }, fresh: { [G]: { exchange_index: 2 } } });
  await tick(w, { quotes: [quote(), quote({}, 'KXGOLD15M', G)] });
  assert.strictEqual(w.posts.length, 1, 'the second market on the same shard is skipped, not sent without funds');
  assert.ok(w.sess.endedBecause === undefined && w.sess.active === true, 'and the session keeps running');
  const rich = world({ session: { startCash: 50 }, balance: { balance_breakdown: [{ balance: '50.0000', exchange_index: 2 }] }, fresh: { [G]: { exchange_index: 2 } } });
  await tick(rich, { quotes: [quote(), quote({}, 'KXGOLD15M', G)] });
  assert.strictEqual(rich.posts.length, 2, 'with the funds, both are sent');
};

// The order limit holds inside a single tick, not only at its start.
gates.N16 = async () => {
  const G = 'KXGOLD15M-26OCT071415-15';
  const w = world({ session: { ordersSent: 199 } });
  await tick(w, { quotes: [quote(), quote({}, 'KXGOLD15M', G)] });
  assert.strictEqual(w.posts.length, 1, '199 sent plus two candidates is stopped at 200');
  assert.strictEqual(w.sess.ordersSent, 200);
};

// A no-fill has to be explainable afterwards: the record carries the touch and size the order was decided on.
gates.N17 = async () => {
  const w = world({ fresh: { [T]: { yes_ask_size_fp: '3.00', yes_bid_size_fp: '12.00' } }, post: { status: 201, body: { order_id: 'o1', fill_count: '0.00', remaining_count: '0.00' } } });
  await tick(w);
  const rec = w.docs.get('L1-' + T);
  assert.strictEqual(rec.status, 'no fill');
  assert.deepStrictEqual([rec.seen.bid, rec.seen.ask, rec.seen.bidSize, rec.seen.askSize], [0.9, 0.91, 12, 3]);
  const bare = world(); await tick(bare);
  assert.strictEqual(bare.docs.get('L1-' + T).seen.askSize, null, 'a field Kalshi did not send is null, not a guess');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();

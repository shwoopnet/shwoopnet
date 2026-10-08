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
  // Trades of 0.92 each. The stop is live.L1_LOSS_STOP ($10): ten lost ones ($9.20) leave room, the eleventh ($10.12) stops the session before any order.
  const per = 0.92, stopN = Math.ceil(live.L1_LOSS_STOP / per), roomN = stopN - 1;
  assert.ok(roomN * per < live.L1_LOSS_STOP && stopN * per >= live.L1_LOSS_STOP, 'the counts below straddle the stop');
  const seed = (w, n, over) => { for (let i = 0; i < n; i++) { const [id, d] = botTrade(i, over); w.docs.set(id, d); } };
  const results = (n, r) => { const o = {}; for (let i = 0; i < n; i++) o[`OLD-${i}`] = r; return o; };
  const w = world({ results: results(stopN, 'no') }); seed(w, stopN);
  await tick(w);
  assert.strictEqual(w.posts.length, 0);
  assert.deepStrictEqual([w.sess.active, w.sess.endedBecause], [false, 'loss stop']);
  assert.ok([...w.docs.values()].filter((d) => d.settled === true).length === stopN, 'each settled result is kept on its record, so it is read once');
  const ok = world({ results: results(roomN, 'no') }); seed(ok, roomN);
  await tick(ok);
  assert.strictEqual(ok.posts.length, 1, 'inside the allowance');
  // Open trades are counted as lost: unsettled ones stop it just as settled losses do.
  const open = world(); seed(open, stopN);
  await tick(open);
  assert.deepStrictEqual([open.posts.length, open.sess.endedBecause], [0, 'loss stop']);
  // Wins offset losses: settled wins are never a reason to stop.
  const won = world({ results: results(stopN, 'yes') }); seed(won, stopN);
  await tick(won);
  assert.strictEqual(won.posts.length, 1);
  // Cash is not the measure: the account being $50 down because of the owner's own trades changes nothing.
  const manual = world({ session: { startCash: 150 } });
  await tick(manual);
  assert.strictEqual(manual.posts.length, 1, 'manual trades moving the account do not trip the bot stop');
  // Trades from before this session are not counted, and an unreadable record fails closed.
  const before = world({ session: { since: NOW - 1000 } }); seed(before, stopN);
  await tick(before);
  assert.strictEqual(before.posts.length, 1, 'earlier trades are not this session');
  const down = world({ tradesThrow: true });
  await tick(down);
  assert.deepStrictEqual([down.posts.length, down.sess.active], [0, true], 'if the bot trades cannot be read, nothing is sent and the session keeps running');
  // Orders that did not fill cost nothing.
  const nofill = world(); seed(nofill, stopN, { fillCount: '0.00', status: 'no fill' });
  await tick(nofill);
  assert.strictEqual(nofill.posts.length, 1, 'no-fills are not losses');
  const first = world({ session: { startCash: null } });
  await tick(first);
  assert.strictEqual(first.sess.startCash, 100, 'the first tick still records the starting cash');
};

// With scaling on, the stop is L1_SIZED_STOP_FRACTION of the starting cash and counts every contract; a partial fill counts what filled.
gates.N19 = async () => {
  const seed = (w, n, over) => { for (let i = 0; i < n; i++) { const [id, d] = botTrade(i, over); w.docs.set(id, d); } };
  const loss = (n) => { const r = {}; for (let i = 0; i < n; i++) r[`OLD-${i}`] = 'no'; return r; };
  const bal = { balance_breakdown: [{ balance: '300.0000', exchange_index: 2 }] };
  // $300 start: the stop is $30. Three-contract trades cost 2.76 each: ten lost ones are $27.60, eleven are $30.36.
  const ten = world({ session: { startCash: 300, sizing: true }, balance: bal, results: loss(10) }); seed(ten, 10, { count: 3, fillCount: '3.00', maxCost: 2.76 });
  await tick(ten);
  assert.strictEqual(ten.posts.length, 1, '$27.60 is inside a $30 stop');
  const eleven = world({ session: { startCash: 300, sizing: true }, balance: bal, results: loss(11) }); seed(eleven, 11, { count: 3, fillCount: '3.00', maxCost: 2.76 });
  await tick(eleven);
  assert.deepStrictEqual([eleven.posts.length, eleven.sess.endedBecause], [0, 'loss stop']);
  // With scaling off the flat $10 stop applies to the same trades and ends it far sooner: 3 x 2.76 = $8.28 is fine, 4 x 2.76 = $11.04 is not.
  const flat3 = world({ session: { startCash: 300 }, balance: bal, results: loss(3) }); seed(flat3, 3, { count: 3, fillCount: '3.00', maxCost: 2.76 });
  await tick(flat3);
  assert.strictEqual(flat3.posts.length, 1, 'scaling off: $8.28 is inside the flat $10 stop');
  const flat4 = world({ session: { startCash: 300 }, balance: bal, results: loss(4) }); seed(flat4, 4, { count: 3, fillCount: '3.00', maxCost: 2.76 });
  await tick(flat4);
  assert.strictEqual(flat4.sess.endedBecause, 'loss stop', 'scaling off: $11.04 reaches the flat $10 stop');
  // A partial fill: 2 of 3 filled costs two thirds and pays two contracts.
  const part = world({ session: { startCash: 300, sizing: true }, balance: bal, results: { 'OLD-0': 'yes' } }); seed(part, 1, { count: 3, fillCount: '2.00', maxCost: 2.76 });
  await live.runL1Tick({ session: part.sess, now: NOW, setSession: async (p) => { Object.assign(part.sess, p); }, logEvent: async () => {}, quotes: [], active: true, enabled: true, store: part.store, keyId: 'k', pem, fetchFn: part.fetchFn });
  const risk = await live.botRisk({ store: part.store, since: 0, fetchFn: part.fetchFn, nowMs: NOW });
  assert.ok(Math.abs(risk.net - (2 - 2.76 * 2 / 3)) < 1e-9 && risk.openCost === 0, 'two contracts won, two thirds of the cost');
};

// Only a literal true turns scaling on, and it is a choice made at the start of a session.
gates.N20 = () => {
  const cb = /exports\.kalshiL1Session = onCall\(([\s\S]*?)\n\}\);/.exec(fnSrc)[1];
  assert.ok(/const sizing = on && request\.data\.sizing === true;/.test(cb), 'only the literal true counts');
  assert.ok(/startCash: null, sizing,/.test(cb), 'kept on the session record');
  assert.ok(/id="kalL1Sizing"/.test(html) && !/id="kalL1Sizing"[^>]*checked/.test(html), 'the box starts unticked');
};

// "No market is about 6 minutes from its close" is true at 3 minutes before a close, and unhelpful: the session says when the next look is.
gates.N21 = async () => {
  const closing = quote({ close_time: iso(NOW + 180000) });                         // 3 minutes left: past its window
  const later = quote({ close_time: iso(NOW + 18 * 60000) }, 'KXBTC15M', 'KXBTC15M-26OCT071430-30');   // 18 minutes left
  const w = world();
  await tick(w, { quotes: [closing, later] });
  assert.strictEqual(w.posts.length, 0);
  assert.strictEqual(w.sess.nextLookAt, NOW + 18 * 60000 - live.L1_WINDOW_MS[1], 'the next window opens 6:40 before the later close');
  assert.ok(w.sess.botNet === 0 && w.sess.botOpen === 0, 'the bot\'s running total is kept current on every tick, not only ticks that trade');
  assert.ok(/entry|6 minutes/.test(w.sess.lastNote) && !/about 6 minutes from its close right now/.test(w.sess.lastNote), 'the note says what the window is');
  const none = world(); await tick(none, { quotes: [closing] });
  assert.strictEqual(none.sess.nextLookAt, null, 'no later market known: no time is invented');
  assert.ok(/fact\('Next look', Number\.isFinite\(s\.nextLookAt\) && s\.nextLookAt > now/.test(html), 'the page shows it only while it is still in the future');
  assert.ok(!/At most 80 orders/.test(html) && /bot's own trades are down \$10\.00/.test(html), 'the rules text matches the live limits');
};

// The page quotes the limits in three places (the start confirmation, the rules text, the status line). They must say what the server does.
gates.N22 = () => {
  const frac = Math.round(live.L1_SIZE_FRACTION * 1000) / 10, stop = Math.round(live.L1_SIZED_STOP_FRACTION * 100), flat = live.L1_LOSS_STOP;
  assert.ok(new RegExp('about ' + frac + '% of cash per order, up to ' + live.L1_SIZE_MAX + ' contracts, stop at ' + stop + '% of starting cash').test(html), 'the start confirmation');
  assert.ok(new RegExp('are down \\$' + flat.toFixed(2).replace('.', '\\.') + ' \\(' + stop + '% of the starting cash with scaling').test(html), 'the rules text');
  assert.ok(new RegExp("\\(" + (stop / 100).toFixed(2) + " \\* s\\.startCash\\)\\.toFixed\\(2\\) : '\\$" + flat.toFixed(2).replace('.', '\\.') + "'").test(html), 'the status line');
  assert.ok(new RegExp('\\(" \\+ \\(live\\.L1_SIZE_FRACTION \\* 100\\)').test(fnSrc) && /live\.L1_SIZED_STOP_FRACTION \* 100/.test(fnSrc), 'the session start log is built from the constants, not typed');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();

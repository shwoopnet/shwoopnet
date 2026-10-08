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

// No end time: a session started days ago still trades. The order limit and the loss stop look at the last 24 hours, not the whole run.
gates.N10 = async () => {
  const old = world({ session: { until: NOW - 1, since: NOW - 30 * 86400000 } });
  await tick(old);
  assert.strictEqual(old.sess.active, true, 'an old session (even one carrying a past until) is not ended by time');
  assert.strictEqual(old.posts.length, 1, 'and it still places its order');
  const lim = world();
  for (let i = 0; i < 200; i++) lim.docs.set('X' + i, { strategy: 'L1', ts: NOW - 3600000 - i, status: 'no fill', fillCount: '0.00' });
  await tick(lim);
  assert.deepStrictEqual([lim.posts.length, lim.sess.active], [0, true], 'the order limit waits, it does not end the session');
  const roll = world();
  for (let i = 0; i < 200; i++) roll.docs.set('X' + i, { strategy: 'L1', ts: NOW - 25 * 3600000 - i, status: 'no fill', fillCount: '0.00' });
  await tick(roll);
  assert.strictEqual(roll.posts.length, 1, 'orders older than 24 hours no longer count toward the limit');
  assert.ok(live.L1_MAX_ORDERS >= 2 * 96, 'the backstop can never be reached by normal trading');
  assert.strictEqual(live.L1_WINDOW_DAY_MS, 24 * 3600 * 1000);
  assert.strictEqual(live.L1_LOSS_STOP, 10);
  // Old profits cannot hide a bad day: a loss that settled in the last 24 hours trips the stop even though the whole run is up.
  const day = world({ session: { since: NOW - 30 * 86400000 } });
  for (let i = 0; i < 5; i++) day.docs.set('W' + i, { strategy: 'L1', ts: NOW - 10 * 86400000 + i, ticker: 'W' + i, side: 'yes', fillCount: '2.00', count: 2, maxCost: 1.86, settled: true, result: 'yes' });
  for (let i = 0; i < 6; i++) day.docs.set('L' + i, { strategy: 'L1', ts: NOW - 3600000 - i, ticker: 'L' + i, side: 'yes', fillCount: '2.00', count: 2, maxCost: 1.86, settled: true, result: 'no' });
  await tick(day);
  assert.deepStrictEqual([day.posts.length, day.sess.endedBecause], [0, 'loss stop'], 'six losses in the last day stop it');
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

// The review (every 3 days): the cap follows the balance down at once, up by one step at most per review, and never within a week of a loss stop.
gates.N24 = async () => {
  const seed = (w, n, over) => { for (let i = 0; i < n; i++) { const [id, d] = botTrade(i, over); w.docs.set(id, d); } };
  const DAY = 86400000, W = live.SCALE_REVIEW_MS;
  const first = live.reviewSizing(null, 341, NOW);
  assert.deepStrictEqual([first.state.cap, first.state.base], [3, 341], 'the first review starts at the 3 the owner was running');
  assert.strictEqual(live.reviewSizing(null, 150, NOW).state.cap, 1, 'a small account starts lower');
  const st = { cap: 3, base: 341, reviewedAt: NOW, lastStopAt: null };
  const early = live.reviewSizing(st, 900, NOW + 2 * DAY);
  assert.deepStrictEqual([early.state.cap, early.changed], [3, false], 'the balance more than doubled but two days is not a review');
  const later = live.reviewSizing(st, 900, NOW + W);
  assert.deepStrictEqual([later.state.cap, later.state.base, later.state.reviewedAt], [4, 900, NOW + W], 'a review later (3 days) it rises ONE step, not to the nine the balance would allow');
  assert.strictEqual(live.reviewSizing(later.state, 900, NOW + W + DAY).state.cap, 4, 'and not again the next day');
  assert.strictEqual(live.reviewSizing(later.state, 900, NOW + 2 * W).state.cap, 5, 'the next review, 3 days on, is the next step');
  assert.strictEqual(W, 3 * DAY, 'reviews are 3 days apart');
  assert.strictEqual(live.reviewSizing({ ...st, cap: 5 }, 240, NOW + DAY).state.cap, 2, 'a falling balance cuts the cap at once, mid week');
  assert.strictEqual(live.reviewSizing({ ...st, lastStopAt: NOW + 2 * DAY }, 900, NOW + 6 * DAY).state.cap, 3, 'no rise within a week of a loss stop, even though reviews come every 3 days');
  assert.strictEqual(live.reviewSizing({ cap: 10, base: 5000, reviewedAt: NOW, lastStopAt: null }, 99999, NOW + 9 * W).state.cap, 10, 'the hard ceiling holds');
  // Through a tick: the stop follows the balance at the review, and the order uses the stored cap.
  const w = world({ session: { sizing: true }, balance: { balance_breakdown: [{ balance: '900.0000', exchange_index: 2 }] } });
  const saved = [];
  await tick(w, { sizingState: { cap: 4, base: 900, reviewedAt: NOW - 1000, lastStopAt: null }, setSizingState: async (x) => { saved.push(x); } });
  assert.strictEqual(w.posts[0].count, '4', 'sized by the stored cap, not by the 2% rule');
  assert.strictEqual(w.sess.sizeCap, 4);
  assert.strictEqual(w.sess.sizeBase, 900, 'the stop base is shown on the session');
  const stopW = world({ session: { sizing: true }, balance: { balance_breakdown: [{ balance: '300.0000', exchange_index: 2 }] }, results: (() => { const r = {}; for (let i = 0; i < 11; i++) r['OLD-' + i] = 'no'; return r; })() });
  seed(stopW, 11, { count: 3, fillCount: '3.00', maxCost: 2.76 });
  const rec = [];
  await tick(stopW, { sizingState: { cap: 3, base: 300, reviewedAt: NOW - 1000, lastStopAt: null }, setSizingState: async (x) => { rec.push(x); } });
  assert.deepStrictEqual([stopW.sess.endedBecause, rec[rec.length - 1].lastStopAt], ['loss stop', NOW], 'a loss stop is remembered so the cap cannot rise for a week');
  const failSave = world({ session: { sizing: true } });
  await tick(failSave, { sizingState: null, setSizingState: async () => { throw new Error('db down'); } });
  assert.strictEqual(failSave.posts.length, 0, 'a review that cannot be saved sends nothing');
};

// Reinvest and skim: half of each win's profit buys extra contracts later, half is set aside; losses come out of the pool; nothing counts twice.
gates.N25 = async () => {
  const st = { cap: 3, base: 341, reviewedAt: 1000, pool: 0, saved: 0, cum: 0, hwm: 0, lastStopAt: null };
  const o = (id, ts, pnl, over = {}) => ({ id, strategy: 'L1', ts, fillCount: '3.00', maxCost: 2.79, settled: true, settledPnl: pnl, ...over });
  const a = live.foldSkim(st, [o('a', 2000, 0.20), o('b', 3000, 0.20)]);
  assert.deepStrictEqual([a.pool, a.saved, a.hwm, a.appliedTs], [0.2, 0.2, 0.4, 3000], 'net profit of 40c: 20c to the pool and 20c to savings');
  const again = live.foldSkim({ ...st, ...a }, [o('a', 2000, 0.20), o('b', 3000, 0.20)]);
  assert.deepStrictEqual([again.pool, again.saved, again.changed], [0.2, 0.2, false], 'the same orders are never counted twice');
  const loss = live.foldSkim({ ...st, pool: 0.5, saved: 1, cum: 2, hwm: 2 }, [o('c', 4000, -2.79)]);
  assert.deepStrictEqual([loss.pool, loss.saved], [0, 1], 'a loss comes out of the pool first, the pool stops at zero, and savings are untouched');
  // The flaw the first version had: wins of 20c and one loss of $2.79. Skimming each win banked half of every win; only net new highs are skimmed now.
  const seq = [];
  for (let i = 0; i < 10; i++) seq.push(o('w' + i, 2000 + i, 0.20));
  seq.push(o('L', 3000, -2.79));
  for (let i = 0; i < 10; i++) seq.push(o('v' + i, 4000 + i, 0.20));
  const flaw = live.foldSkim(st, seq);
  assert.ok(Math.abs(flaw.cum - (4 - 2.79)) < 1e-6 && flaw.saved <= 0.5 * flaw.hwm + 1e-9, 'savings never exceed half of the net high-water profit (here ' + flaw.saved + ' of ' + flaw.hwm + ')');
  assert.ok(flaw.saved < 1.5, 'ten recovery wins after a loss skimmed nothing while they were only winning back the loss');
  const gap = live.foldSkim(st, [o('d', 2000, 0.2, { settled: false, settledPnl: undefined }), o('e', 3000, 0.2)]);
  assert.deepStrictEqual([gap.pool, gap.appliedTs], [0, 1000], 'an unsettled older order holds everything behind it, so a late settle is not skipped');
  const hist = live.foldSkim(st, [o('old', 500, 5)]);
  assert.strictEqual(hist.pool, 0, 'orders from before the state existed are history');
  assert.deepStrictEqual([live.skimAddon({ pool: 0.5 }, 5), live.skimAddon({ pool: 0.95 }, 5), live.skimAddon({ pool: 99 }, 5)], [0, 1, 106], 'one extra contract per 93c of pool, with no fixed limit');
  assert.strictEqual(live.skimAddon({ pool: 99, lastStopAt: 1000 }, 1000 + 3 * 86400000), 0, 'off for a week after a loss stop');
  assert.ok(live.skimAddon({ pool: 99, lastStopAt: 1000 }, 1000 + 8 * 86400000) > 0);
  // Through a tick: the cap plus the add-on sets the size, and the balance the weekly review sees excludes savings.
  const w = world({ session: { sizing: true }, balance: { balance_breakdown: [{ balance: '341.0000', exchange_index: 2 }] } });
  const saved = [];
  await tick(w, { sizingState: { cap: 3, base: 341, reviewedAt: NOW - 1000, pool: 2, saved: 5, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async (x) => { saved.push(x); } });
  assert.strictEqual(w.posts[0].count, '5', 'cap 3 plus two from a $2 pool');
  assert.strictEqual(w.sess.sizeAddon, 2);
  assert.strictEqual(live.reviewSizing({ cap: 3, base: 341, reviewedAt: 0, lastStopAt: null }, 341 - 30, 8 * 86400000).state.cap, 3, 'with $30 saved the sizing balance is $311, which still supports three');
  assert.strictEqual(live.reviewSizing({ cap: 3, base: 341, reviewedAt: 0, lastStopAt: null }, 341 - 100, 8 * 86400000).state.cap, 2, 'savings are not sized on: if the rest of the balance falls under $255 the cap follows it down');
  const ceil = world({ session: { sizing: true }, balance: { balance_breakdown: [{ balance: '5000.0000', exchange_index: 2 }] } });
  await tick(ceil, { sizingState: { cap: 10, base: 5000, reviewedAt: NOW - 1000, pool: 99, saved: 0, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async () => {} });
  assert.strictEqual(ceil.posts[0].count, String(live.L1_ORDER_CEILING), 'a huge pool still stops at the order ceiling, the fat-finger guard');
};

// Wiring: the session is switched by a server callable with a server-set expiry; the scheduled arm function runs it; nothing
// else is scheduled; it refuses to run beside a single armed test order; and the page asks twice.
gates.N13 = () => {
  assert.ok(/exports\.kalshiL1Session = onCall\(async \(request\) => \{\s*await assertKalshiAdmin\(request\.auth\);/.test(fnSrc), 'admin only');
  assert.ok(/ref\.set\(\{ active: true, since: now, until: null,/.test(fnSrc), 'the session is written with no end time');
  assert.ok(/KALSHI_LIVE_ENABLED\.value\(\) !== "on"/.test(fnSrc.slice(fnSrc.indexOf('exports.kalshiL1Session'))), 'refuses when the server switch is off');
  assert.ok(/live\.runL1Tick\(/.test(fnSrc.slice(fnSrc.indexOf('exports.kalshiLiveArmed'))), 'run by the scheduled function');
  assert.ok(/if \(sessionOn && !armedOn\)/.test(fnSrc), 'never beside an armed single test');
  assert.ok(/The L1 bot is running\. Stop it before arming/.test(fnSrc), 'arming refuses while the session runs');
  assert.ok(/A single test order is armed\. Disarm it before starting/.test(fnSrc), 'starting refuses while armed');
  assert.deepStrictEqual([...fnSrc.matchAll(/exports\.(\w+) = onSchedule\(/g)].map((x) => x[1]), ['kalshiLiveArmed', 'kalshiBookRecorder']);
  assert.ok(fnSrc.indexOf('exports.kalshiL1Session') < fnSrc.indexOf('exports.kalshiBookRecorder'), 'defined before the recorder, which stays last');
  // The page: two clicks, a server call only on the confirm click, and a visible stop.
  assert.ok(/kalL1Start'\)[\s\S]{0,400}addEventListener\('click', function\(\)\{ msg\.textContent = ''; ask\(true\); \}\)/.test(html), 'the first click only asks');
  const yes = html.slice(html.indexOf("yes.addEventListener('click', function(){\n      var api = window.__shwoopAPI;\n      if(!api || !api.kalshiL1Session"));
  assert.ok(/api\.kalshiL1Session\(true, document\.getElementById\('kalL1Sizing'\)\.checked, document\.getElementById\('kalL1Trailing'\)\.checked\)/.test(yes.slice(0, 800)), 'the confirm click starts it');
  assert.ok(!/id="kalL1Stop"/.test(html) && /id="kalBotHalt"/.test(html), 'one control stops entries (Pause, which can be resumed); there is no separate stop button');
  assert.ok(/api\.setKalshiHalt\(false\)/.test(html.slice(html.indexOf("var wasPaused"))), 'starting lifts a pause left on, so Start after a Flatten is one step');
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
  const w = world();
  for (let i = 0; i < 199; i++) w.docs.set('X' + i, { strategy: 'L1', ts: NOW - 3600000 - i, status: 'no fill', fillCount: '0.00' });
  await tick(w, { quotes: [quote(), quote({}, 'KXGOLD15M', G)] });
  assert.strictEqual(w.posts.length, 1, '199 in the last day plus two candidates is stopped at 200');
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

// Size scaling: off unless the session was started with it, never fewer than one or more than three contracts, and the
// money it risks is counted in the loss stop.
gates.N18 = async () => {
  const rich = { balance_breakdown: [{ balance: '300.0000', exchange_index: 2 }] };
  const off = world({ session: { startCash: 300 }, balance: rich });
  await tick(off);
  assert.strictEqual(off.posts[0].count, '1', 'off by default, even on a large account');
  const on = world({ session: { startCash: 300, sizing: true }, balance: rich });
  await tick(on);
  assert.strictEqual(on.posts[0].count, '3', '1% of $300 buys three contracts at about 91c');
  assert.strictEqual(on.docs.get('L1-' + T).count, 3);
  assert.ok(on.docs.get('L1-' + T).maxCost > 2.7 && on.docs.get('L1-' + T).maxCost < 3, 'the record carries the cost of all three');
  const small = world({ session: { startCash: 40, sizing: true }, balance: { balance_breakdown: [{ balance: '40.0000', exchange_index: 2 }] } });
  await tick(small);
  assert.strictEqual(small.posts[0].count, '1', 'a $40 account is one contract');
  const mid = world({ session: { startCash: 106, sizing: true }, balance: { balance_breakdown: [{ balance: '106.0000', exchange_index: 2 }] } });
  await tick(mid);
  assert.strictEqual(mid.posts[0].count, '1', 'a $106 account is one contract (one per $100 of balance)');
  const two = world({ session: { startCash: 250, sizing: true }, balance: { balance_breakdown: [{ balance: '250.0000', exchange_index: 2 }] } });
  await tick(two);
  assert.strictEqual(two.posts[0].count, '2', 'a $250 account is two contracts');
  const huge = world({ session: { startCash: 5000, sizing: true }, balance: { balance_breakdown: [{ balance: '5000.0000', exchange_index: 2 }] } });
  await tick(huge);
  assert.strictEqual(huge.posts[0].count, '3', 'never more than three');
  assert.deepStrictEqual([live.l1Count(NaN, 0.9), live.l1Count(50, 0.9), live.l1Count(40, 0.9), live.l1Count(106.5, 0.92), live.l1Count(138, 0.92), live.l1Count(1e9, 0.9)], [1, 1, 1, 2, 3, 3]);
  assert.deepStrictEqual([live.L1_SIZE_FRACTION, live.L1_SIZED_STOP_FRACTION, live.L1_SIZE_MAX], [0.02, 0.05, 3], 'the share of cash per order, the scaled stop and the cap');
  assert.strictEqual(live.liveOrderBody('X', 0.9, 'yes', 'id', 2, 4).count, '4', 'the cap can rise, so four is a valid order');
  assert.throws(() => live.liveOrderBody('X', 0.9, 'yes', 'id', 2, live.L1_ORDER_CEILING + 1), /refusing/, 'but never past the order ceiling');
  assert.throws(() => live.liveOrderBody('X', 0.9, 'yes', 'id', 2, 0), /refusing/);
  assert.throws(() => live.liveOrderBody('X', 0.9, 'yes', 'id', 2, 1.5), /refusing/);
  assert.strictEqual(live.liveOrderBody('X', 0.9, 'yes', 'id', 2).count, '1', 'one contract unless told otherwise');
};

// With scaling on, the stop is L1_SIZED_STOP_FRACTION of the starting cash and counts every contract; a partial fill counts what filled.
gates.N19 = async () => {
  const seed = (w, n, over) => { for (let i = 0; i < n; i++) { const [id, d] = botTrade(i, over); w.docs.set(id, d); } };
  const loss = (n) => { const r = {}; for (let i = 0; i < n; i++) r[`OLD-${i}`] = 'no'; return r; };
  const bal = { balance_breakdown: [{ balance: '300.0000', exchange_index: 2 }] };
  // $300 start: the stop is $15 (5%). Three-contract trades cost 2.76 each: five lost ones are $13.80, six are $16.56.
  const ten = world({ session: { startCash: 300, sizing: true }, balance: bal, results: loss(5) }); seed(ten, 5, { count: 3, fillCount: '3.00', maxCost: 2.76 });
  await tick(ten);
  assert.strictEqual(ten.posts.length, 1, '$13.80 is inside a $15 stop');
  const eleven = world({ session: { startCash: 300, sizing: true }, balance: bal, results: loss(6) }); seed(eleven, 6, { count: 3, fillCount: '3.00', maxCost: 2.76 });
  await tick(eleven);
  assert.deepStrictEqual([eleven.posts.length, eleven.sess.endedBecause], [0, 'loss stop'], '$16.56 reaches the $15 stop');
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
  assert.ok(/id="kalL1Sizing"[^>]*checked/.test(html), 'the scaling box starts ticked, so a restart cannot silently drop the bot to one contract (it cannot be changed once the session runs)');
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
  assert.ok(/'Next look ' \+ \(Number\.isFinite\(s\.nextLookAt\) && s\.nextLookAt > now/.test(html), 'the page shows it only while it is still in the future');
  assert.ok(!/At most 80 orders/.test(html) && /bot's own trades over the last 24 hours are down \$10\.00/.test(html), 'the rules text matches the live limits');
};

// The page quotes the limits in three places (the start confirmation, the rules text, the status line). They must say what the server does.
gates.N22 = () => {
  const frac = Math.round(live.L1_SIZE_FRACTION * 1000) / 10, stop = Math.round(live.L1_SIZED_STOP_FRACTION * 100), flat = live.L1_LOSS_STOP;
  assert.ok(new RegExp('one contract per \\$' + live.SCALE_DOLLARS_PER_CONTRACT + ' of balance, up to ' + live.L1_SIZE_CEILING + ', raised one step every 3 days at most; stop at ' + stop + '% of the balance at the last review').test(html), 'the start confirmation');
  assert.ok(new RegExp('are down \\$' + flat.toFixed(2).replace('.', '\\.') + ' \\(' + stop + '% of the balance at the last review with scaling').test(html), 'the rules text');
  assert.ok(new RegExp("\\(" + (stop / 100).toFixed(2) + " \\* base\\)\\.toFixed\\(2\\) : '\\$" + flat.toFixed(2).replace('.', '\\.') + "'").test(html), 'the status line');
  assert.ok(/live\.SCALE_DOLLARS_PER_CONTRACT/.test(fnSrc) && /live\.L1_SIZED_STOP_FRACTION \* 100/.test(fnSrc), 'the session start log is built from the constants, not typed');
};

// The high-point stop: measured from the best settled result, only when the session was started with it, and the peak never falls.
gates.N23 = async () => {
  const seed = (w, n, over) => { for (let i = 0; i < n; i++) { const [id, d] = botTrade(i, over); w.docs.set(id, d); } };
  const lost = (n) => { const r = {}; for (let i = 0; i < n; i++) r[`OLD-${i}`] = 'no'; return r; };
  // After a high point of +$5, six losses ($5.52) are $10.52 below it: the stop is $10, so a trailing session ends; a plain session has room.
  const trail = world({ session: { trailing: true, peakNet: 5, peakAt: NOW - 1000 }, results: lost(6) }); seed(trail, 6);
  await tick(trail);
  assert.deepStrictEqual([trail.posts.length, trail.sess.endedBecause], [0, 'loss stop'], 'the stop counts from the high point');
  assert.ok(/from their best/.test(trail.events.find((e) => e.kind === 'session ended').detail), 'and says so');
  const plain = world({ session: { peakNet: 5, peakAt: NOW - 1000 }, results: lost(6) }); seed(plain, 6);
  await tick(plain);
  assert.strictEqual(plain.posts.length, 1, 'without the option the same trades are well inside the $10 stop');
  // Inside the give-back it keeps trading: peak 5, down $4.60 from it is fine.
  const ok = world({ session: { trailing: true, peakNet: 5, peakAt: NOW - 1000 }, results: lost(1) }); seed(ok, 1);
  await tick(ok);
  assert.strictEqual(ok.posts.length, 1);
  // The peak rises with settled gains and never falls with losses, and is never below zero.
  const rise = world({ session: { trailing: true }, results: (() => { const r = {}; for (let i = 0; i < 13; i++) r[`OLD-${i}`] = 'yes'; return r; })() }); seed(rise, 13);
  await tick(rise);
  assert.ok(Math.abs(rise.sess.peakNet - 13 * 0.08) < 1e-6, 'thirteen wins of 8c set the peak at +$1.04: ' + rise.sess.peakNet);
  const keep = world({ session: { trailing: true, peakNet: 3, peakAt: NOW - 1000 } });
  await tick(keep);
  assert.strictEqual(keep.sess.peakNet === undefined ? 3 : keep.sess.peakNet, 3, 'a lower result does not lower the peak');
  const neg = world({ session: { trailing: true }, results: lost(2) }); seed(neg, 2);
  await tick(neg);
  assert.ok(!(neg.sess.peakNet < 0), 'the peak is never below zero');
  // Chosen at the start only, with a literal true; the page offers it unticked and passes it on.
  const cb = /exports\.kalshiL1Session = onCall\(([\s\S]*?)\n\}\);/.exec(fnSrc)[1];
  assert.ok(/const trailing = on && request\.data\.trailing === true;/.test(cb) && /startCash: null, sizing, trailing,/.test(cb), 'only a literal true, kept on the session record');
  assert.ok(/id="kalL1Trailing"/.test(html) && !/id="kalL1Trailing"[^>]*checked/.test(html), 'the box starts unticked');
  assert.ok(/api\.kalshiL1Session\(true, document\.getElementById\('kalL1Sizing'\)\.checked, document\.getElementById\('kalL1Trailing'\)\.checked\)/.test(html) && /trailing: trailing === true/.test(html), 'and passed to the server');
};

gates.N30 = () => {
  // Profit-funded contracts have no fixed limit, but the risk stays inside the 2% of cash rule and the pool holds only profit.
  assert.strictEqual(live.skimAddon({ pool: 4.65 }, 5), 5, 'a pool of five contract costs buys five extras');
  assert.strictEqual(live.l1Count(344, 0.93, 3 + 5), 7, 'but one order never risks more than 2% of cash, however large the pool');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();

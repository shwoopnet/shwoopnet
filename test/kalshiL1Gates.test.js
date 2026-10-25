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
// How long a market has left when the bot looks at it: 10 minutes for the series that decide early (Bitcoin, XRP, natural gas), 6 for the rest, so a test about something else lands in the series' own entry window.
const leftFor = (series) => (live.EARLY_PROBE_SERIES.includes(series) ? 600000 : 360000);
const quote = (over = {}, series = 'KXBTC15M', ticker = T) => ({ series, m: Object.assign({
  ticker, status: 'active', close_time: iso(NOW + leftFor(series)), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' }, over) });

// Gold first (Oct 21, 2026): gold is the only market that keeps the size ladder, so the sizing gates tick a gold market (its own shard, 0).
const GT = 'KXGOLD15M-26OCT071415-15';
const gq = () => quote({}, 'KXGOLD15M', GT);
function world(opts = {}) {
  const calls = [], posts = [], docs = new Map(), events = [];
  let haltReads = 0;
  const sess = Object.assign({ active: true, until: NOW + 3600000, ordersSent: 0, startCash: 100 }, opts.session || {});
  const store = {
    async halted() { if (opts.haltAfterFirstRead) return haltReads++ > 0; return opts.halted === true; },
    async hasUnresolved() { return opts.unresolved === true || [...docs.values()].some((d) => d.status === 'sending' || d.status === 'unknown'); },
    async createTest(id, data) { if (docs.has(id)) return false; docs.set(id, { ...data }); return true; },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
    async sessionTrades(since) { if (opts.tradesThrow) throw new Error('down'); return [...docs.entries()].filter(([, d]) => d.ts >= since).map(([id, d]) => ({ id, ...d })); },
  };
  const fetchFn = async (url, o) => {
    calls.push({ url, method: o.method, headers: o.headers, body: o.body ? JSON.parse(o.body) : null });
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/candlesticks')) {
      if (opts.candlesThrow) throw new Error('down');
      if (opts.candles === 'none') return reply(404, {});
      // The default path is a smooth climb of the YES side (0.50 up to 0.91), so a Bitcoin or Ethereum order passes the smooth-climb gate unless a test says otherwise.
      const nowSecW = Math.floor(NOW / 1000), climb = [0.5, 0.58, 0.66, 0.74, 0.82, 0.91].map((m, i, arr) => ({ end_period_ts: nowSecW - 60 * (arr.length - 1 - i), yes_bid: { close_dollars: String(m - 0.01) }, yes_ask: { close_dollars: String(m + 0.01) } }));
      return reply(200, { candlesticks: opts.candles === undefined ? climb : opts.candles });
    }
    if (url.includes('/markets/')) {
      const tk = decodeURIComponent(url.split('/markets/')[1].split('?')[0]);
      const over = (opts.fresh && opts.fresh[tk]) || {};
      return reply(opts.marketStatus || 200, { market: { status: 'active', close_time: iso(NOW + leftFor(tk.split('-')[0])), exchange_index: tk.includes('KXGOLD') ? 0 : 2, ...(opts.results && opts.results[tk] ? { result: opts.results[tk] } : {}), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100', ...over } });
    }
    if (url.endsWith('/portfolio/balance')) return reply(opts.balStatus || 200, opts.balance || { balance_breakdown: [{ balance: '70.0000', exchange_index: 2 }, { balance: '30.0000', exchange_index: 0 }] });
    if (url.includes('/portfolio/orders')) return reply(200, { orders: opts.existing || [] });
    if (url.includes('/portfolio/fills')) return reply(200, { fills: opts.fills || [] });     // the account's own fills: nothing sold by hand unless a gate says so
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
  // Bitcoin buys NO here, so its smooth-climb path is the NO side's: a YES mid that falls from 0.50 to 0.085 is a smooth climb for NO.
  const nowS = Math.floor(NOW / 1000), noClimb = [0.5, 0.42, 0.34, 0.26, 0.18, 0.085].map((m, i, arr) => ({ end_period_ts: nowS - 60 * (arr.length - 1 - i), yes_bid_dollars: undefined, yes_bid: { close_dollars: String(m - 0.005) }, yes_ask: { close_dollars: String(m + 0.005) } }));
  const w = world({ fresh: { [T]: { yes_bid_dollars: '0.0800', yes_ask_dollars: '0.0900' } }, candles: noClimb });
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
  assert.strictEqual(both.posts.find((p) => p.ticker.includes('KXGOLD')).exchange_index, 0, 'gold is placed on its own shard');
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
    assert.strictEqual(w.docs.get('L1-KXGOLD15M-26OCT071415-15').status, status, name + ' is recorded for the owner to look at (gold is tried first)');
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

// The review (every 3 days): the cap follows the balance down at once, up by one step at most per review, and a loss stop does not hold it (the owner, Oct 23, 2026).
gates.N24 = async () => {
  const seed = (w, n, over) => { for (let i = 0; i < n; i++) { const [id, d] = botTrade(i, over); w.docs.set(id, d); } };
  const DAY = 86400000, W = live.SCALE_REVIEW_MS;
  const first = live.reviewSizing(null, 341, NOW);
  assert.deepStrictEqual([first.state.cap, first.state.base], [3, 341], 'the first review starts at the 3 the owner was running');
  assert.strictEqual(live.reviewSizing(null, 40, NOW).state.cap, 1, 'a small account starts lower');
  const st = { cap: 3, base: 341, reviewedAt: NOW, lastStopAt: null };
  const early = live.reviewSizing(st, 900, NOW + 2 * DAY);
  assert.deepStrictEqual([early.state.cap, early.changed], [3, false], 'the balance more than doubled but two days is not a review');
  const later = live.reviewSizing(st, 900, NOW + W);
  assert.deepStrictEqual([later.state.cap, later.state.base, later.state.reviewedAt], [4, 900, NOW + W], 'a review later (3 days) it rises ONE step, not to the nine the balance would allow');
  assert.strictEqual(live.reviewSizing(later.state, 900, NOW + W + DAY).state.cap, 4, 'and not again the next day');
  assert.strictEqual(live.reviewSizing(later.state, 900, NOW + 2 * W).state.cap, 5, 'the next review, 3 days on, is the next step');
  assert.strictEqual(W, 3 * DAY, 'reviews are 3 days apart');
  assert.strictEqual((() => { const a = live.reviewSizing({ ...st, cap: 5 }, 130, NOW + DAY); return live.reviewSizing(a.state, 130, NOW + DAY + live.SCALE_FALL_CONFIRM_MS).state.cap; })(), 3, 'a balance that stays low cuts the cap, mid week, without waiting for a review');
  assert.strictEqual(live.reviewSizing({ ...st, lastStopAt: NOW + 2 * DAY }, 900, NOW + 6 * DAY).state.cap, 4, 'a loss stop does not hold the climb: the next review still steps up one (the owner, Oct 23, 2026)');
  assert.strictEqual(live.reviewSizing({ cap: live.L1_SIZE_CEILING, base: 5000, reviewedAt: NOW, lastStopAt: null }, 99999, NOW + 9 * W).state.cap, live.L1_SIZE_CEILING, 'the hard ceiling holds');
  // Through a tick: the stop follows the balance at the review, and the order uses the stored cap.
  const w = world({ session: { sizing: true }, balance: { balance_breakdown: [{ balance: '900.0000', exchange_index: 0 }] } });
  const saved = [];
  await tick(w, { quotes: [gq()], sizingState: { cap: 4, base: 900, reviewedAt: NOW - 1000, lastStopAt: null }, setSizingState: async (x) => { saved.push(x); } });
  assert.strictEqual(w.posts[0].count, '4', 'sized by the stored cap, not by the 2% rule');
  assert.strictEqual(w.sess.sizeCap, 4);
  assert.strictEqual(w.sess.sizeBase, 900, 'the stop base is shown on the session');
  const stopW = world({ session: { sizing: true }, balance: { balance_breakdown: [{ balance: '300.0000', exchange_index: 0 }] }, results: (() => { const r = {}; for (let i = 0; i < 14; i++) r['OLD-' + i] = 'no'; return r; })() });
  seed(stopW, 14, { count: 3, fillCount: '3.00', maxCost: 2.76 });
  const rec = [];
  await tick(stopW, { quotes: [gq()], sizingState: { cap: 3, base: 300, reviewedAt: NOW - 1000, lastStopAt: null }, setSizingState: async (x) => { rec.push(x); } });
  assert.deepStrictEqual([stopW.sess.endedBecause, rec[rec.length - 1].lastStopAt], ['loss stop', NOW], 'a loss stop is still recorded (when it happened), though it no longer holds the cap');
  const failSave = world({ session: { sizing: true } });
  await tick(failSave, { quotes: [gq()], sizingState: null, setSizingState: async () => { throw new Error('db down'); } });
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
  assert.ok(live.skimAddon({ pool: 99, lastStopAt: 1000 }, 1000 + 3 * 86400000) > 0, 'the profit add-on is NOT held after a loss stop: a pool that has refilled buys extras at once (owner, Oct 13, 2026)');
  assert.strictEqual(live.skimAddon({ pool: 0, lastStopAt: 1000 }, 1000 + 3 * 86400000), 0, 'a stop empties the pool, so there is nothing to buy with until wins refill it');
  assert.ok(live.skimAddon({ pool: 99, lastStopAt: 1000 }, 1000 + 8 * 86400000) > 0);
  // Through a tick: the cap plus the add-on sets the size, and the balance the weekly review sees excludes savings.
  const w = world({ session: { sizing: true }, balance: { balance_breakdown: [{ balance: '600.0000', exchange_index: 0 }] } });
  const saved = [];
  await tick(w, { quotes: [gq()], sizingState: { cap: 3, base: 341, reviewedAt: NOW - 1000, pool: 2, saved: 5, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async (x) => { saved.push(x); } });
  assert.strictEqual(w.posts[0].count, '5', 'cap 3 plus two from a $2 pool');
  assert.strictEqual(w.sess.sizeAddon, 2);
  assert.strictEqual(live.reviewSizing({ cap: 3, base: 341, reviewedAt: 0, lastStopAt: null }, 341 - 30, 8 * 86400000).state.cap, 4, 'with $30 saved the sizing balance is $311, which supports seven at $43 but rises one step to four');
  assert.strictEqual((() => { const a = live.reviewSizing({ cap: 3, base: 341, reviewedAt: 0, lastStopAt: null }, 341 - 250, 8 * 86400000); return live.reviewSizing(a.state, 341 - 250, 8 * 86400000 + live.SCALE_FALL_CONFIRM_MS).state.cap; })(), 2, 'savings are not sized on: if the rest of the balance falls to $91 the cap follows it down');
  const ceil = world({ session: { sizing: true }, balance: { balance_breakdown: [{ balance: '5000.0000', exchange_index: 0 }] } });
  await tick(ceil, { quotes: [gq()], sizingState: { cap: 10, base: 5000, reviewedAt: NOW - 1000, pool: 99, saved: 0, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async () => {} });
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
  assert.ok(!/exports\.kalshiLiveArm\b/.test(fnSrc), 'there is no arm callable left to refuse');
  assert.ok(/A single test order is armed\. Disarm it before starting/.test(fnSrc), 'starting refuses while armed');
  assert.deepStrictEqual([...fnSrc.matchAll(/exports\.(\w+) = onSchedule\(/g)].map((x) => x[1]), ['marketTapeTick', 'kalshiLiveExit', 'kalshiLiveArmed', 'kalshiPaperTick', 'kalshiBookRecorder']);   // the opening window's paper recorder (no secrets, no orders: see test/kalshiOpeningGates.test.js) comes first, then the exit watch (test/kalshiExitGates.test.js)
  assert.ok(fnSrc.indexOf('exports.kalshiL1Session') < fnSrc.indexOf('exports.kalshiBookRecorder'), 'defined before the recorder, which stays last');
  // The page: two clicks, a server call only on the confirm click, and a visible stop.
  assert.ok(/kalL1Start'\)[\s\S]{0,400}addEventListener\('click', function\(\)\{ msg\.textContent = ''; ask\(true\); \}\)/.test(html), 'the first click only asks');
  const yes = html.slice(html.indexOf("yes.addEventListener('click', function(){\n      var api = window.__shwoopAPI;\n      if(!api || !api.kalshiL1Session"));
  assert.ok(/api\.kalshiL1Session\(true, document\.getElementById\('kalL1Trailing'\)\.checked\)/.test(yes.slice(0, 800)), 'the confirm click starts it');
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

// DD1: the depth log (the research session's request, the owner: "2", Oct 25, 2026). Consequence: the share of the resting size an order takes is on the record before slippage shows in P&L, and it can never change an order.
gates.DD1 = async () => {
  const w = world({ fresh: { [T]: { yes_ask_size_fp: '3.00', yes_bid_size_fp: '12.00' } }, post: { status: 201, body: { order_id: 'o1', fill_count: '1.00', remaining_count: '0.00' } } });
  await tick(w);
  const rec = w.docs.get('L1-' + T);
  assert.strictEqual(rec.side, 'yes', 'this fixture buys YES, which meets the YES ask');
  assert.deepStrictEqual([rec.depthAtLimit, rec.depthLevels], [3, 'top'], 'depth is the top level on the side being hit, and the record says it is only the top level');
  assert.strictEqual(rec.shareOfDepth, Number((rec.count / 3).toFixed(4)), 'share is count over that depth');
  const bare = world(); await tick(bare);
  const b = bare.docs.get('L1-' + T);
  assert.ok(b.depthAtLimit === null && b.shareOfDepth === null, 'a size Kalshi did not send is null, not a guess');
  const src = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.ok(/pick\.side === "yes" \? record\.seen\.askSize : record\.seen\.bidSize/.test(src), 'a NO buy meets the YES bid, so it reads the bid size');
  assert.ok(!/depthAtLimit|shareOfDepth/.test(src.replace(/record\.depthAtLimit[^;]*;|record\.shareOfDepth[^;]*;/g, '').replace(/\/\/[^\n]*/g, '')), 'nothing that decides an order reads the depth fields');
};

// Size scaling: off unless the session was started with it, never fewer than one or more than three contracts, and the
// money it risks is counted in the loss stop.
gates.N18 = async () => {
  const rich = { balance_breakdown: [{ balance: '300.0000', exchange_index: 0 }] };
  const off = world({ session: { startCash: 300 }, balance: rich });
  await tick(off, { quotes: [gq()] });
  assert.strictEqual(off.posts[0].count, '1', 'off by default, even on a large account');
  const on = world({ session: { startCash: 300, sizing: true }, balance: rich });
  await tick(on, { quotes: [gq()] });
  assert.strictEqual(on.posts[0].count, '3', '1% of $300 buys three contracts at about 91c');
  assert.strictEqual(on.docs.get('L1-' + GT).count, 3);
  assert.ok(on.docs.get('L1-' + GT).maxCost > 2.7 && on.docs.get('L1-' + GT).maxCost < 3, 'the record carries the cost of all three');
  const small = world({ session: { startCash: 40, sizing: true }, balance: { balance_breakdown: [{ balance: '40.0000', exchange_index: 0 }] } });
  await tick(small, { quotes: [gq()] });
  assert.strictEqual(small.posts[0].count, '1', 'a $40 account is one contract');
  const mid = world({ session: { startCash: 106, sizing: true }, balance: { balance_breakdown: [{ balance: '106.0000', exchange_index: 0 }] } });
  await tick(mid, { quotes: [gq()] });
  assert.strictEqual(mid.posts[0].count, '2', 'a $106 account is two contracts (2% is $2.12 at about 91c)');
  const two = world({ session: { startCash: 250, sizing: true }, balance: { balance_breakdown: [{ balance: '250.0000', exchange_index: 0 }] } });
  await tick(two, { quotes: [gq()] });
  assert.strictEqual(two.posts[0].count, '3', 'a $250 account is capped at three by the starting cap (2% would allow five)');
  const huge = world({ session: { startCash: 5000, sizing: true }, balance: { balance_breakdown: [{ balance: '5000.0000', exchange_index: 0 }] } });
  await tick(huge, { quotes: [gq()] });
  assert.strictEqual(huge.posts[0].count, '3', 'never more than three');
  assert.deepStrictEqual([live.l1Count(NaN, 0.9), live.l1Count(50, 0.9), live.l1Count(40, 0.9), live.l1Count(213, 0.92), live.l1Count(276, 0.92), live.l1Count(1e9, 0.9)], [1, 1, 1, 3, 3, 3]);
  assert.deepStrictEqual([live.L1_SIZE_FRACTION, live.L1_SIZED_STOP_FRACTION, live.L1_SIZE_MAX], [0.02, 0.12, 3], 'the share of cash per order, the scaled stop and the cap');
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
  // $300 start: the stop is $36 (12%, since Oct 20, 2026; it was 6% and ended the bot on one ordinary loss with a full window open). Three-contract trades cost 2.76 each: thirteen lost ones are $35.88, fourteen are $38.64.
  const ten = world({ session: { startCash: 300, sizing: true }, balance: bal, results: loss(13) }); seed(ten, 13, { count: 3, fillCount: '3.00', maxCost: 2.76 });
  await tick(ten);
  assert.strictEqual(ten.posts.length, 1, '$35.88 is inside a $36 stop');
  const eleven = world({ session: { startCash: 300, sizing: true }, balance: bal, results: loss(14) }); seed(eleven, 14, { count: 3, fillCount: '3.00', maxCost: 2.76 });
  await tick(eleven);
  assert.deepStrictEqual([eleven.posts.length, eleven.sess.endedBecause], [0, 'loss stop'], '$38.64 reaches the $36 stop');
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
  assert.ok(/const sizing = on;/.test(cb) && !/request\.data\.sizing/.test(cb), 'size scaling is decided in code, never by anything the page sends');
  assert.ok(/startCash: null, sizing,/.test(cb), 'kept on the session record');
  assert.ok(!/kalL1Sizing/.test(html), 'the page has no size box any more: a restart cannot drop the ladder and the page cannot raise it');
  assert.ok(!/sizing:\s*sizing === true/.test(html) && /kalshiL1Session: function\(on, trailing\)/.test(html), 'and it does not send a size choice');
};

// "No market is about 6 minutes from its close" is true at 3 minutes before a close, and unhelpful: the session says when the next look is.
gates.N21 = async () => {
  const closing = quote({ close_time: iso(NOW + 180000) });                         // 3 minutes left: past its window
  const later = quote({ close_time: iso(NOW + 18 * 60000) }, 'KXBTC15M', 'KXBTC15M-26OCT071430-30');   // 18 minutes left
  const w = world();
  await tick(w, { quotes: [closing, later] });
  assert.strictEqual(w.posts.length, 0);
  assert.strictEqual(w.sess.nextLookAt, NOW + 18 * 60000 - live.L1_WINDOW_MS[1], 'the next window opens 6:40 before the later close (Bitcoin decides at 6 minutes since Oct 23, 2026)');
  assert.ok(w.sess.botNet === 0 && w.sess.botOpen === 0, 'the bot\'s running total is kept current on every tick, not only ticks that trade');
  assert.ok(/entry|6 minutes/.test(w.sess.lastNote) && !/about 6 minutes from its close right now/.test(w.sess.lastNote), 'the note says what the window is');
  const none = world(); await tick(none, { quotes: [closing] });
  assert.strictEqual(none.sess.nextLookAt, null, 'no later market known: no time is invented');
  assert.ok(/'Next look ' \+ \(Number\.isFinite\(s\.nextLookAt\) && s\.nextLookAt > now/.test(html), 'the page shows it only while it is still in the future');
  assert.ok(!/At most 80 orders/.test(html) && /its trades over the last 24 hours are down 12% of the balance \(otherwise \$10\)/.test(html), 'the rules text matches the live limits');
};

// The page quotes the limits in three places (the start confirmation, the rules text, the status line). They must say what the server does.
gates.N22 = () => {
  const frac = Math.round(live.L1_SIZE_FRACTION * 1000) / 10, stop = Math.round(live.L1_SIZED_STOP_FRACTION * 100), flat = live.L1_LOSS_STOP;
  assert.ok(new RegExp('one contract per \\$' + live.SCALE_DOLLARS_PER_CONTRACT + ' of balance, up to ' + live.L1_SIZE_CEILING + ', raised one step every 3 days at most; stop at ' + stop + '% of the balance at the last review').test(html), 'the start confirmation');
  assert.ok(new RegExp('are down ' + stop + '% of the balance \\(otherwise \\$' + flat.toFixed(0) + '\\)').test(html), 'the rules text');
  assert.ok(new RegExp("kalshiMoney\\(" + (stop / 100).toFixed(2) + " \\* base\\) : kalshiMoney\\(" + flat.toFixed(0) + "\\)").test(html), 'the status line');
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
  assert.ok(/api\.kalshiL1Session\(true, document\.getElementById\('kalL1Trailing'\)\.checked\)/.test(html) && /trailing: trailing === true/.test(html), 'and passed to the server');
};

gates.N31 = () => {
  const H = 3600000, T0 = 1e9, st = { cap: 3, base: 344, reviewedAt: T0, lastStopAt: null };
  // The Oct 8 collapse: a manual trade of the whole account leaves the balance near $0 for a few minutes. That must not cut the cap or move the stop's base.
  const dip = live.reviewSizing(st, 0.4, T0 + H);
  assert.deepStrictEqual([dip.state.cap, dip.state.base], [3, 344], 'a dip alone changes neither the cap nor the stop base');
  const back = live.reviewSizing(dip.state, 509, T0 + H + 600000);
  assert.deepStrictEqual([back.state.cap, back.state.base, back.state.lowSince], [3, 344, null], 'money that comes back clears the wait');
  const stayed = live.reviewSizing(live.reviewSizing(st, 40, T0 + H).state, 40, T0 + H + live.SCALE_FALL_CONFIRM_MS);
  assert.strictEqual(stayed.state.cap, 1, 'a balance that stays low does cut the cap');
  // Reseed (set by Start): raises a collapsed cap to what a fresh start gives, re-bases the stop, never lowers, and a loss stop does not hold it.
  const lowSt = { cap: 1, base: 0.4, reviewedAt: T0, lastStopAt: null, reseed: true };
  const r = live.reviewSizing(lowSt, 509, T0 + H);
  assert.deepStrictEqual([r.state.cap, r.state.base, r.state.reseed], [11, 509, false], 'a collapsed cap goes straight to the balance target on Start');
  assert.strictEqual(live.reviewSizing({ ...lowSt, cap: 15 }, 509, T0 + H).state.cap, 15, 'a higher saved cap is never lowered by Start');
  assert.strictEqual(live.reviewSizing({ ...lowSt, lastStopAt: T0 }, 509, T0 + H).state.cap, 11, 'Start goes straight to the balance target (509 / 43 = 11) even right after a loss stop (the owner, Oct 23, 2026)');
};

gates.N32 = async () => {
  // The stop protects the account, not profit already made: the part of a lost (or open) order that was bought with reinvested profit does not count toward it,
  // so a big add-on cannot lock the bot out after one loss. $509 base: the stop is 12%, $61.08.
  const bal = { balance_breakdown: [{ balance: '509.0000', exchange_index: 2 }] };
  const sess = { startCash: 509, sizing: true };
  const sizing = { cap: 5, base: 509, reviewedAt: NOW - 1000, pool: 0, saved: 0, appliedTs: NOW - 1000, lastStopAt: null, cum: 0, hwm: 0 };
  const run = async (trade, result) => {
    const w = world({ session: { ...sess }, balance: bal, results: result ? { 'OLD-0': result } : {} });
    const [id, d] = botTrade(0, trade); w.docs.set(id, d);
    await tick(w, { sizingState: { ...sizing }, setSizingState: async () => {} });
    return w;
  };
  // A $70 order of which $59.50 was profit: one loss is -$70, past the plain $61.08 stop, but only $10.50 of it was the account's.
  const big = { count: 75, fillCount: '75.00', maxCost: 70, addon: 64, addonCost: 59.5 };
  const lost = await run(big, 'no');
  assert.notStrictEqual(lost.sess.endedBecause, 'loss stop', 'one loss of a profit-funded order does not lock the bot out');
  const open = await run(big, null);
  assert.notStrictEqual(open.sess.endedBecause, 'loss stop', 'nor does the same order sitting open, counted as lost');
  // The same $70 loss with NO add-on is all account money and does reach the stop.
  const plain = await run({ count: 75, fillCount: '75.00', maxCost: 70, addon: 0, addonCost: 0 }, 'no');
  assert.strictEqual(plain.sess.endedBecause, 'loss stop', 'a loss of account money past 12% still stops it');
  // And a loss that eats the allowance PLUS more than 12% of the account stops it: $59.50 of profit and $65 of account money is a $124.50 loss.
  const worse = await run({ count: 130, fillCount: '130.00', maxCost: 124.5, addon: 64, addonCost: 59.5 }, 'no');
  assert.strictEqual(worse.sess.endedBecause, 'loss stop', 'the account share of the loss is still held to the stop');
  // Old orders that carry no add-on fields behave as before.
  const risk = await live.botRisk({ store: world({ results: { 'OLD-0': 'no' } }).store, since: 0, fetchFn: world({ results: { 'OLD-0': 'no' } }).fetchFn, nowMs: NOW });
  assert.strictEqual(risk.addonAtRisk, 0);
};

gates.N30 = () => {
  assert.ok(live.L1_SIZE_CEILING < live.L1_ORDER_CEILING, 'the base ceiling leaves room under the order ceiling for the profit add-on');
  // Profit-funded contracts have no fixed limit, but the risk of the add-on is bounded by the pool, which holds only profit, and the account-funded part stays inside the 2% rule.
  assert.strictEqual(live.skimAddon({ pool: 4.65 }, 5), 5, 'a pool of five contract costs buys five extras');
  assert.strictEqual(live.l1Count(509, 0.93, 20, 0), 10, 'the account-funded part never risks more than 2% of cash');
  assert.strictEqual(live.l1Count(548, 0.93, 25, 0), 11, 'at $548 the 2% base is 11 contracts, as agreed with the owner on Oct 9');
  assert.strictEqual(live.l1Count(509, 0.93, 5, 3), 8, 'profit-funded contracts sit outside the 2% rule and are simply added');
  assert.strictEqual(live.l1Count(509, 0.93, 5, 999), live.L1_ORDER_CEILING, 'the fat-finger guard is the only fixed limit left');
};

// P1 to P5: the pool rule. "highs" is the original (half of each NEW profit high); "wins" refills the pool from half of every win, right after a loss, with savings untouched.
gates.P1 = () => {
  const st = { pool: 0, saved: 0, cum: 0, hwm: 0, appliedTs: 0 };
  const o = (id, ts, pnl) => ({ id, strategy: 'L1', ts, fillCount: '3.00', maxCost: 2.79, settled: true, settledPnl: pnl });
  const seq = [o('a', 1, 4), o('b', 2, 4), o('c', 3, -6), o('d', 4, 1), o('e', 5, 1), o('f', 6, 1)];   // +8, a loss of 6 (to +2), then three wins of 1 (back to +5, still below the high of +8)
  const highs = live.foldSkim(st, seq), wins = live.foldSkim(st, seq, { everyWin: true });
  assert.deepStrictEqual([highs.pool, highs.saved], [0, 4], 'original rule: after the loss the pool stays empty until the old high is regained (the pool took half of +8, the loss emptied it)');
  assert.ok(Math.abs(wins.pool - 1.5) < 1e-9, 'new rule: the three wins after the loss put half of each in the pool at once: ' + wins.pool);
  assert.strictEqual(wins.saved, 4, 'savings are exactly as before: half of the net high only');
};
gates.P2 = () => {
  const o = (id, ts, pnl) => ({ id, strategy: 'L1', ts, fillCount: '3.00', maxCost: 2.79, settled: true, settledPnl: pnl });
  const st = { pool: 3, saved: 3, cum: 6, hwm: 6, appliedTs: 0 };
  assert.strictEqual(live.foldSkim(st, [o('x', 1, -10)], { everyWin: true }).pool, 0, 'a loss comes out of the pool first and the pool stops at zero, under the new rule too');
  assert.strictEqual(live.foldSkim(st, [o('x', 1, -10)]).pool, 0, 'and under the original');
  assert.strictEqual(live.foldSkim(st, [o('x', 1, -1)], { everyWin: true }).pool, 2, 'a small loss takes only its size');
};
gates.P3 = () => {
  // The flaw the owner would hit with the literal restart: savings are a ratchet. Under "wins" savings stay at half the net high and never more.
  const o = (id, ts, pnl) => ({ id, strategy: 'L1', ts, fillCount: '3.00', maxCost: 2.79, settled: true, settledPnl: pnl });
  let rows = [], ts = 1, cum = 0, hi = 0, fs = { pool: 0, saved: 0, cum: 0, hwm: 0, appliedTs: 0 };
  for (let i = 0; i < 400; i++) { const pnl = (i % 17 === 16) ? -10.5 : 0.6; rows.push(o('r' + i, ts++, pnl)); cum += pnl; hi = Math.max(hi, cum); }
  const wins = live.foldSkim(fs, rows, { everyWin: true });
  assert.ok(wins.saved <= 0.5 * hi + 1e-6, 'savings never exceed half of the best net result (' + wins.saved.toFixed(2) + ' of ' + hi.toFixed(2) + ')');
  assert.ok(wins.pool >= 0, 'the pool is never negative');
};
gates.P4 = () => {
  // With no opts the function is exactly the original, so every existing order and the saved state behave as before until the owner switches the rule.
  const o = (id, ts, pnl) => ({ id, strategy: 'L1', ts, fillCount: '3.00', maxCost: 2.79, settled: true, settledPnl: pnl });
  const st = { pool: 0, saved: 0, cum: 0, hwm: 0, appliedTs: 0 };
  const a = live.foldSkim(st, [o('a', 1, 2), o('b', 2, -1), o('c', 3, 3)]);
  assert.deepStrictEqual(a, live.foldSkim(st, [o('a', 1, 2), o('b', 2, -1), o('c', 3, 3)], {}), 'no opts is the original');
  assert.deepStrictEqual(a, live.foldSkim(st, [o('a', 1, 2), o('b', 2, -1), o('c', 3, 3)], { everyWin: false }), 'everyWin false is the original');
};
gates.P5 = () => {
  // The owner removed the pool-rule switch on Oct 12, 2026: the pool always rebuilds after every win, and nothing stored or callable can bring the original rule back.
  const idx = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  const lib = fnSrcLib().replace(/\/\/.*$/gm, '');
  assert.ok(/foldSkim\(rv\.state, recentList, \{ everyWin: true \}\)/.test(lib), 'the tick always passes everyWin');
  assert.ok(!/session\.poolRule|\.poolRule\b/.test(lib) && !/poolRule|kalshiPoolRule/.test(idx.replace(/\/\/.*$/gm, '')), 'nothing reads a stored pool rule and no callable sets one');
};
gates.P6 = async () => {
  // Through a real tick: win, loss, win. After a loss the old rule waits for a new high, so it ends with an empty pool; "after every win" has refilled by half of the last win.
  // A stored poolRule of "highs" (what the removed switch used to write) must not bring the old rule back.
  const o = (id, ts, pnl) => ({ strategy: 'L1', ticker: 'KXBTC15M-OLD-' + id, series: 'KXBTC15M', side: 'yes', count: 3, fillCount: '3.00', maxCost: 2.79, ts, status: 'filled', settled: true, settledPnl: pnl, result: pnl > 0 ? 'yes' : 'no' });
  const w = world({ session: { sizing: true, poolRule: 'highs' }, balance: { balance_breakdown: [{ balance: '600.0000', exchange_index: 2 }] } });
  w.docs.set('a', o('a', NOW - 3 * 3600000, 0.6)); w.docs.set('b', o('b', NOW - 2 * 3600000, -10.5)); w.docs.set('c', o('c', NOW - 3600000, 0.6));
  const saved = [];
  await tick(w, { sizingState: { cap: 3, base: 600, reviewedAt: NOW - 1000, pool: 0, saved: 0, cum: 0, hwm: 0, appliedTs: NOW - 4 * 3600000, lastStopAt: null }, setSizingState: async (x) => { saved.push(x); } });
  assert.strictEqual(saved.length, 1, 'the folded state was saved');
  assert.ok(Math.abs(saved[0].pool - 0.3) < 1e-9, 'the pool refilled by half of the win that followed the loss (' + saved[0].pool + '), which the original rule would have left at 0');
  assert.strictEqual(w.sess.sizePoolRule, 'wins', 'and the page is told which rule is in use');
};
function fnSrcLib() { return require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8'); }
// X1 to X8: Ethereum is a regular live market (the owner folded it in, Oct 10, 2026): same rule, size, stop and exit as Bitcoin and gold, only series on the code's list, Solana never.
const ETH = 'KXETH15M-26OCT091500-00';
gates.X1 = async () => {
  const base = { sizing: true, sizeCap: 12, sizeAddon: 8, sizeBase: 500, sizePool: 7.4, sizeSaved: 5, sizeNextReview: NOW + 86400000 };
  const w = world({ session: base, balance: { balance_breakdown: [{ balance: '600.0000', exchange_index: 2 }, { balance: '400.0000', exchange_index: 2 }] } });
  await tick(w, { quotes: [quote(), quote({}, 'KXETH15M', ETH)], sizingState: { cap: 12, base: 500, reviewedAt: NOW - 1000, pool: 7.4, saved: 5, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async () => {} });
  assert.ok(w.posts.some((p) => p.ticker === ETH), 'Ethereum trades like Bitcoin and gold, with no setting to turn on');
  assert.ok(w.posts.some((p) => p.ticker === T), 'and Bitcoin still does');
};
gates.X2 = async () => {
  // Gold first (Oct 21, 2026): Ethereum is an ordinary L1 series (same rule, stop, pool and exit) but is CAPPED at one contract while gold keeps the ladder.
  const sess = { sizing: true, sizeCap: 12, sizeAddon: 8 };
  const w = world({ session: sess, balance: { balance_breakdown: [{ balance: '600.0000', exchange_index: 0 }, { balance: '400.0000', exchange_index: 0 }] }, fresh: { [ETH]: { exchange_index: 0 } } });
  await tick(w, { quotes: [gq(), quote({}, 'KXETH15M', ETH)], sizingState: { cap: 12, base: 500, reviewedAt: NOW - 1000, pool: 7.4, saved: 5, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async () => {} });
  const gold = w.posts.find((p) => p.ticker === GT), eth = w.posts.find((p) => p.ticker === ETH);
  assert.ok(gold && eth, 'both markets are traded');
  assert.ok(Number(gold.count) > 2 && Number(eth.count) === 1, 'gold gets the ladder size and Ethereum is capped at one: ' + gold.count + ' vs ' + eth.count);
  const rec = w.docs.get('L1-' + ETH);
  assert.strictEqual(rec.series, 'KXETH15M'); assert.strictEqual(rec.strategy, 'L1'); assert.ok(!('extraSeries' in rec), 'it is an ordinary L1 order, not a special kind');
};
gates.X3 = async () => {
  // Ethereum alone, at a small stake, is sized by the same cap as any other series
  const sess = { sizing: true, sizeCap: 3, sizeAddon: 0 };
  const w = world({ session: sess });
  await tick(w, { quotes: [quote({}, 'KXETH15M', ETH)], sizingState: { cap: 3, base: 300, reviewedAt: NOW - 1000, pool: 0, saved: 0, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async () => {} });
  const eth = w.posts.find((p) => p.ticker === ETH);
  assert.ok(eth && Number(eth.count) <= 3, 'a 3 contract cap holds for Ethereum too: ' + (eth && eth.count));
};
gates.X4 = () => {
  assert.deepStrictEqual(live.L1_SERIES, ['KXGOLD15M', 'KXXRP15M', 'KXBTC15M', 'KXDOGE15M', 'KXETH15M', 'KXAUDUSD15M', 'KXUSDCAD15M', 'KXNATGAS15M'], 'GOLD FIRST, then Bitcoin, Ethereum, XRP and Dogecoin, then the three probe markets LAST (the later ones yield when a window is full); Solana is not on it');
  assert.deepStrictEqual(live.LIVE_SERIES, ['KXBTC15M', 'KXGOLD15M'], 'the older single-order path is untouched');
  assert.ok(!('EXTRA_LIVE_SERIES' in live) && !('extraLiveCounts' in live), 'no separate Ethereum switch is left in the library');
};
// PR1 to PR3: the probe markets (AUD/USD, USD/CAD, natural gas; the owner's "live forward testing", Oct 21, 2026). L1's rule, ONE contract whatever the ladder says, last in line, inside the same limits.
const AUD = 'KXAUDUSD15M-26OCT091500-00';
gates.PR1 = async () => {
  const base = { sizing: true, sizeCap: 12, sizeAddon: 8, sizeBase: 500, sizePool: 7.4, sizeSaved: 5, sizeNextReview: NOW + 86400000 };
  const w = world({ session: base, balance: { balance_breakdown: [{ balance: '600.0000', exchange_index: 0 }, { balance: '400.0000', exchange_index: 0 }] }, fresh: { [AUD]: { exchange_index: 0 } } });
  await tick(w, { quotes: [gq(), quote({}, 'KXAUDUSD15M', AUD)], sizingState: { cap: 12, base: 500, reviewedAt: NOW - 1000, pool: 7.4, saved: 5, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async () => {} });
  const gold = w.posts.find((p) => p.ticker === GT), aud = w.posts.find((p) => p.ticker === AUD);
  assert.ok(gold && Number(gold.count) > 1, 'gold is sized by the ladder: ' + (gold && gold.count));
  assert.ok(aud, 'the probe market trades');
  assert.strictEqual(Number(aud.count), 1, 'but a probe market is always ONE contract, however high the ladder and the reinvested profit are: ' + aud.count);
  const rec = w.docs.get('L1-' + AUD);
  assert.ok(rec.strategy === 'L1' && rec.series === 'KXAUDUSD15M' && !rec.addon && !rec.addonCost, 'it is an ordinary L1 order with no profit money in it, so the loss stop, pool and exit read it like any other');
};
gates.PR2 = async () => {
  assert.deepStrictEqual(live.L1_SERIES.slice(0, 5), ['KXGOLD15M', 'KXXRP15M', 'KXBTC15M', 'KXDOGE15M', 'KXETH15M'], 'gold, then the four capped markets, come first');
  assert.deepStrictEqual(live.L1_SERIES.slice(5), live.PROBE_SERIES, 'the probe markets come last, so they only take what a window has left');
  // a window already at its combined limit takes no probe order
  const w = world({ session: wsess({}), balance: rich });
  w.docs.set('L1-earlier', { strategy: 'L1', ticker: BTCW.replace(/-00$/, '-99'), status: 'filled', maxCost: live.L1_WINDOW_CAP_FRACTION * 1000, addonCost: 0, ts: NOW - 60000 });
  await tick(w, { quotes: [quote({}, 'KXAUDUSD15M', AUD.replace(/-00$/, '-98'))], sizingState: wstate, setSizingState: async () => {} });
  assert.strictEqual(w.posts.length, 0, 'a full window takes no probe order (the first order in a window is the only one never cut to nothing)');
};
gates.PR3 = () => {
  const idx = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  assert.ok(/live\.L1_SERIES\.filter\(\(x\) => !live\.LIVE_SERIES\.includes\(x\)\)/.test(idx), 'the probe markets\' quotes are read by the same loop as Ethereum, XRP and Dogecoin, and a failure there never stops the rest');
  assert.ok(!/request\.data\.(ticker|price|count|side)/.test(idx), 'still no callable takes a ticker, price or size from the caller');
  const push = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'kalshiPushLib.js'), 'utf8');
  for (const s of live.PROBE_SERIES) assert.ok(push.includes(s), s + ' has a name in the alerts, not a raw ticker');
};
// DP1 to DP4: the probe drop rule (DL1, Oct 21, 2026). A probe market is dropped when its last 200 settled entries net negative; the live series never are.
const settledProbe = (series, i, pnl) => ({ id: 'o-' + series + '-' + i, series, strategy: 'L1', status: 'filled', settled: true, result: pnl > 0 ? 'yes' : 'no', settledPnl: pnl, fillCount: 1, ts: NOW - 3600000 + i * 1000 });
const memoryRecord = (initial) => {
  const box = { rec: initial || {} };
  return { box, update: async (apply) => { const r = apply(box.rec); if (r.changed) box.rec = r.record; return r.record; } };
};
gates.DP1 = async () => {
  // 200 entries netting -$0.50 drops the probe; 199 do not (too few to judge), and 200 netting +$0.50 do not.
  const mk = (n, net) => Array.from({ length: n }, (_, i) => settledProbe('KXAUDUSD15M', i, i === 0 ? net - 0.05 * (n - 1) : 0.05));
  assert.strictEqual(live.PROBE_DROP_WINDOW, 200);
  let u = live.probeRingUpdate({}, mk(199, -0.5), NOW);
  assert.ok(!live.probeDropped(u.record, 'KXAUDUSD15M') && live.probeNet(u.record.rings.KXAUDUSD15M) === null, '199 entries are too few to judge, even if they net negative');
  u = live.probeRingUpdate({}, mk(200, -0.5), NOW);
  assert.ok(live.probeDropped(u.record, 'KXAUDUSD15M') && u.newlyDropped.join() === 'KXAUDUSD15M', 'the last 200 settled entries net negative: dropped');
  u = live.probeRingUpdate({}, mk(200, 0.5), NOW);
  assert.ok(!live.probeDropped(u.record, 'KXAUDUSD15M'), 'the last 200 net positive: kept');
  // only the last 200 count: an old loss falls out of the record.
  const all = [settledProbe('KXAUDUSD15M', 0, -5)].concat(Array.from({ length: 200 }, (_, i) => settledProbe('KXAUDUSD15M', i + 1, 0.01)));
  u = live.probeRingUpdate({}, all, NOW);
  assert.ok(u.record.rings.KXAUDUSD15M.length === 200 && !live.probeDropped(u.record, 'KXAUDUSD15M'), 'the 201st oldest entry is out of the window');
  // the same order twice is one entry, a hand-closed order is not the bot's result, and an unsettled one is not a result yet.
  const dup = [settledProbe('KXUSDCAD15M', 1, -1), settledProbe('KXUSDCAD15M', 1, -1), { ...settledProbe('KXUSDCAD15M', 2, -1), result: 'hand' }, { ...settledProbe('KXUSDCAD15M', 3, -1), settled: false }];
  u = live.probeRingUpdate({}, dup, NOW);
  assert.strictEqual(u.record.rings.KXUSDCAD15M.length, 1, 'each order counts once, and only settled, non-hand ones');
  // a live series is never put in the record.
  u = live.probeRingUpdate({}, [settledProbe('KXGOLD15M', 1, -1), settledProbe('KXBTC15M', 2, -1)], NOW);
  assert.deepStrictEqual(Object.keys(u.record.rings).sort(), [...live.PROBE_SERIES].sort(), 'only probe markets have a record, so the rule can never touch gold, Bitcoin, Ethereum, XRP or Dogecoin');
};
gates.DP2 = async () => {
  // A dropped probe takes no order; the other series trade as usual; and it stays dropped on the next minute without any new entry.
  const w = world({ session: { active: true, ordersSent: 0, startCash: 100 } });
  const rec = memoryRecord({ rings: {}, droppedAt: { KXAUDUSD15M: NOW - 60000 } });
  await tick(w, { quotes: [quote(), quote({}, 'KXAUDUSD15M', AUD)], updateProbeRecord: rec.update });
  assert.ok(w.posts.some((p) => p.ticker === T), 'Bitcoin still trades');
  assert.ok(!w.posts.some((p) => p.ticker === AUD), 'the dropped probe takes no order');
  // the same market with no drop does trade (so the test above is about the rule and nothing else)
  const w2 = world({ session: { active: true, ordersSent: 0, startCash: 100 } });
  await tick(w2, { quotes: [quote({}, 'KXAUDUSD15M', AUD)], updateProbeRecord: memoryRecord().update });
  assert.ok(w2.posts.some((p) => p.ticker === AUD), 'an undropped probe trades');
};
gates.DP3 = async () => {
  // The tick builds the record from the orders it already read, drops the probe in the same minute, and says so once in the log.
  const w = world({ session: { active: true, ordersSent: 0, startCash: 100 } });
  // The 24 hour list holds at most 200 orders of every kind, so the record grows over many minutes: 199 earlier entries are already in it, and one more settled loss arrives in this minute's list.
  const earlier = Array.from({ length: 199 }, (_, i) => ({ id: 'e-' + i, ts: NOW - 86400000 * 2 + i, pnl: 0.01 }));
  { const { id, ...d } = settledProbe('KXUSDCAD15M', 1, -9); w.docs.set('L1-last', d); }
  const rec = memoryRecord({ rings: { KXUSDCAD15M: earlier }, droppedAt: {} });
  await tick(w, { quotes: [quote({}, 'KXUSDCAD15M', 'KXUSDCAD15M-26OCT071415-00')], updateProbeRecord: rec.update });
  assert.ok(live.probeDropped(rec.box.rec, 'KXUSDCAD15M'), 'the record was built from the 24 hour orders and the probe dropped');
  assert.strictEqual(w.posts.length, 0, 'and it did not trade in that same minute');
  assert.strictEqual(w.events.filter((e) => e.kind === 'probe dropped').length, 1, 'one log line');
  await tick(w, { quotes: [quote({}, 'KXUSDCAD15M', 'KXUSDCAD15M-26OCT071415-00')], updateProbeRecord: rec.update });
  assert.strictEqual(w.events.filter((e) => e.kind === 'probe dropped').length, 1, 'not logged again every minute');
};
gates.DP4 = async () => {
  // Fails closed: a record that cannot be read or saved takes the probes out for that minute, and nothing else.
  const w = world({ session: { active: true, ordersSent: 0, startCash: 100 } });
  await tick(w, { quotes: [quote(), quote({}, 'KXAUDUSD15M', AUD)], updateProbeRecord: async () => { throw new Error('down'); } });
  assert.ok(w.posts.some((p) => p.ticker === T) && !w.posts.some((p) => p.ticker === AUD), 'Bitcoin trades, the probe waits');
  // and the wiring: a transaction on the fresh document, in the one collection only the server writes.
  assert.ok(/updateProbeRecord: \(apply\) => db\.runTransaction/.test(fnSrc) && /doc\("probeRecord"\)/.test(fnSrc) && /tx\.get\(ref\)/.test(fnSrc), 'applied to the fresh document inside a transaction');
  assert.ok(/series_filter_not_used|const tradable = L1_SERIES\.filter\(\(x\) => !dropped\.includes\(x\)\)/.test(fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8')), 'the rule only removes series from the tradable list');
};
// CO1 to CO3: the cost cut (Oct 21, 2026). The 24 hour read keeps its older part in memory; the exit watch reads only unsettled orders; the repair pass runs every 10 minutes. None of it may change what the bot decides.
const MIN = 60000;
function fakeOrders(now) {
  // 120 orders over the last 24 hours, one every 12 minutes, the newest 3 minutes old.
  return Array.from({ length: 120 }, (_, i) => ({ id: 'o' + i, ts: now - 3 * MIN - i * 12 * MIN, status: 'filled', settled: i > 1 }));
}
gates.CO1 = async () => {
  const now0 = NOW; let all = fakeOrders(now0), docsRead = 0, calls = 0;
  const readSince = async (ts) => { calls++; const r = all.filter((t) => t.ts >= ts).map((t) => ({ ...t })); docsRead += r.length; return r; };
  const read = live.makeRecentOrderReader(readSince);
  const day = 24 * 60 * MIN;
  const same = (a, b) => assert.deepStrictEqual(a.map((t) => t.id).sort(), b.map((t) => t.id).sort());
  const first = await read(now0 - day, now0);
  same(first, all.filter((t) => t.ts >= now0 - day));
  const full = docsRead;
  // every following minute returns exactly what a full read would, including orders created in between (by this or another instance), while reading far fewer documents.
  docsRead = 0;
  for (let m = 1; m <= 14; m++) {
    const now = now0 + m * MIN;
    all = all.concat([{ id: 'n' + m, ts: now - 20000, status: 'filled', settled: false }]);
    const got = await read(now - day, now);
    same(got, all.filter((t) => t.ts >= now - day));
  }
  assert.ok(docsRead < full * 14 * 0.4, 'the 14 cached minutes read well under half of what 14 full reads would: ' + docsRead + ' vs ' + full * 14);
  // a change to a RECENT order (the exit watch selling, the settle sweep) is seen the next minute.
  all = all.map((t) => t.id === 'o0' ? { ...t, settled: true, result: 'yes' } : t);
  const seen = (await read(now0 + 15 * MIN - day, now0 + 14 * MIN + 1000)).find((t) => t.id === 'o0');
  assert.ok(seen, 'present');
  // after 15 minutes the older part is read again, so nothing stays stale for long.
  const before = calls;
  await read(now0 + 16 * MIN - day, now0 + 16 * MIN);
  assert.strictEqual(calls, before + 1, 'one full read at the refresh');
  // a failed read throws, as the plain read did, so the tick still sends nothing.
  const bad = live.makeRecentOrderReader(async () => { throw new Error('down'); });
  await assert.rejects(() => bad(NOW - day, NOW));
};
gates.CO2 = async () => {
  // The tick uses the cached read when the store has one, the plain read otherwise, and an unreadable list still sends nothing.
  const w = world({ session: { active: true, ordersSent: 0, startCash: 100 } });
  let cached = 0;
  w.store.sessionTradesCached = async (since, now) => { cached++; return w.store.sessionTrades(since); };
  await tick(w, { quotes: [quote()] });
  assert.strictEqual(cached, 1, 'the tick read through the cache');
  assert.ok(w.posts.length === 1, 'and still traded as before');
  const w2 = world({ session: { active: true, ordersSent: 0, startCash: 100 } });
  w2.store.sessionTradesCached = async () => { throw new Error('down'); };
  await tick(w2, { quotes: [quote()] });
  assert.strictEqual(w2.posts.length, 0, 'an unreadable list sends nothing');
};
gates.CO3 = async () => {
  const idx = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
  assert.ok(/async recentFilled\(since\) \{ return \(await col\.where\("status", "==", "filled"\)\.where\("settled", "==", false\)\.get\(\)\)/.test(idx), 'the exit watch reads only filled, unsettled orders (two equalities, no index)');
  assert.ok(/repair: Math\.floor\(now \/ 60000\) % 10 === 0/.test(idx), 'the hand-sold repair pass runs every 10 minutes');
  // the repair pass is skipped on request and the rest of the sweep still settles.
  const docs = [{ id: 'a', ticker: 'KXBTC15M-26OCT071415-15', side: 'yes', fillCount: '1', maxCost: 0.9, count: 1, settled: false, status: 'filled', result: undefined }];
  let handAsked = 0; const upd = [];
  const store = { openFilled: async () => docs, handOrders: async () => { handAsked++; return []; }, updateTest: async (id, p) => { upd.push(id); } };
  const f = async (url) => ({ status: 200, text: async () => JSON.stringify({ market: { result: 'yes' } }) });
  await live.settleOpenOrders({ store, fetchFn: f, nowMs: NOW, keyId: 'k', pem, repair: false });
  assert.strictEqual(handAsked, 0, 'no repair read when it is off');
  assert.deepStrictEqual(upd, ['a'], 'but the order still settles');
  await live.settleOpenOrders({ store, fetchFn: f, nowMs: NOW, keyId: 'k', pem });
  assert.strictEqual(handAsked, 1, 'on by default, so every other caller behaves as before');
};
// EP1 to EP3: early entry probes (FWD7 and FWD8, Oct 21, 2026). XRP and natural gas are entered about 10 minutes before the close INSTEAD of 6, one contract; a market is decided once.
const XRP10 = 'KXXRP15M-26OCT071415-10';
const q10 = (series, ticker, over = {}) => ({ series, m: Object.assign({ ticker, status: 'active', close_time: iso(NOW + 600000), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' }, over) });
gates.EP1 = async () => {
  assert.deepStrictEqual(live.EARLY_PROBE_SERIES, ['KXXRP15M', 'KXNATGAS15M'], 'exactly XRP and natural gas (Bitcoin moved to the 6 minute look on a smooth climb, Oct 23, 2026)');
  assert.strictEqual(live.entryLead('KXXRP15M', 600000), '10m');
  assert.strictEqual(live.entryLead('KXXRP15M', 360000), null, 'XRP no longer decides at 6 minutes: it is 10 minutes only');
  assert.strictEqual(live.entryLead('KXNATGAS15M', 360000), null, 'nor does natural gas');
  assert.strictEqual(live.entryLead('KXBTC15M', 360000), '6m', 'Bitcoin decides at 6 minutes (on a smooth climb only)');
  assert.strictEqual(live.entryLead('KXETH15M', 360000), '6m', 'every other series is unchanged');
  assert.strictEqual(live.entryLead('KXXRP15M', 480000), null, 'between the two windows: nothing');
  assert.strictEqual(live.entryLead('KXBTC15M', 600000), null, 'and has no 10 minute window any more');
  assert.strictEqual(live.entryLead('KXETH15M', 600000), null, 'Ethereum has no early window, nor do gold, Dogecoin or the currency probes');
  assert.strictEqual(live.entryLead('KXGOLD15M', 600000), null);
  assert.strictEqual(live.entryLead('KXDOGE15M', 600000), null);
  const w = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { [XRP10]: { close_time: iso(NOW + 600000) }, 'KXBTC15M-26OCT071430-10': { close_time: iso(NOW + 600000) } } });
  await tick(w, { quotes: [q10('KXXRP15M', XRP10), q10('KXBTC15M', 'KXBTC15M-26OCT071430-10')] });
  assert.strictEqual(w.posts.length, 1, 'XRP is entered at 10 minutes and Bitcoin is not');
  assert.ok(Number(w.posts[0].count) === 1 && w.posts[0].ticker === XRP10, 'one contract');
  const w5 = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { 'KXETH15M-26OCT071415-10': { close_time: iso(NOW + 600000) } } });
  await tick(w5, { quotes: [q10('KXETH15M', 'KXETH15M-26OCT071415-10')] });
  assert.strictEqual(w5.posts.length, 0, 'Ethereum is not entered at 10 minutes');
  const rec = w.docs.get('L1-' + XRP10);
  assert.ok(rec.entryLead === '10m' && rec.strategy === 'L1' && !rec.addon, 'recorded as an ordinary L1 order tagged with the lead it was entered at');
};
gates.EP2 = async () => {
  // A market is decided once. After its 10 minute order the 6 minute tick sends nothing on it, and a market not in the band at 10 minutes is NOT tried again at 6.
  const w = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { [XRP10]: { close_time: iso(NOW + 600000) } } });
  await tick(w, { quotes: [q10('KXXRP15M', XRP10)] });
  assert.strictEqual(w.posts.length, 1);
  await live.runL1Tick({ session: w.sess, now: NOW + 4 * 60000, setSession: async (p) => { Object.assign(w.sess, p); }, logEvent: async () => {}, quotes: [{ series: 'KXXRP15M', m: { ticker: XRP10, status: 'active', close_time: iso(NOW + 600000), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' } }], active: true, enabled: true, store: w.store, keyId: 'live-key', pem, fetchFn: w.fetchFn });
  assert.strictEqual(w.posts.length, 1, 'no second order on the same market at 6 minutes');
  const w3 = world({ session: { active: true, ordersSent: 0, startCash: 100 } });
  await tick(w3, { quotes: [quote({ close_time: iso(NOW + 360000) }, 'KXXRP15M', 'KXXRP15M-26OCT071415-06'), quote({ close_time: iso(NOW + 360000) }, 'KXNATGAS15M', 'KXNATGAS15M-26OCT071415-06')] });
  assert.strictEqual(w3.posts.length, 0, 'XRP and natural gas are not entered at 6 minutes at all');
  const w4 = world({ session: { active: true, ordersSent: 0, startCash: 100 } });
  await tick(w4, { quotes: [quote({ close_time: iso(NOW + 360000) }, 'KXETH15M', 'KXETH15M-26OCT071415-06')] });
  assert.strictEqual(w4.posts.length, 1, 'Ethereum is still entered at 6 minutes');
  const w6 = world({ session: { active: true, ordersSent: 0, startCash: 100 } });
  await tick(w6, { quotes: [quote({ close_time: iso(NOW + 360000) })] });
  assert.strictEqual(w6.posts.length, 1, 'Bitcoin is entered at 6 minutes now, on a smooth climb (default path)');
};
gates.EP3 = async () => {
  // The exit watch must be running when an early order lands: every minute from just before the 10 minute window to the end of the 6 minute window is a watch minute.
  for (const m of [3, 4, 5, 6, 7, 8, 9, 10]) assert.ok(live.EXIT_BUY_MINUTES.includes(m), 'minute ' + m + ' is watched');
  assert.ok(!live.EXIT_BUY_MINUTES.includes(1) && !live.EXIT_BUY_MINUTES.includes(13), 'but a quiet minute with nothing open is still idle');
  // and nothing else about the entry changed: no other series gained an early window, the band and the sizing are the same.
  assert.deepStrictEqual(live.L1_WINDOW_MS, [330000, 400000]);
  assert.ok(live.EARLY_PROBE_SERIES.every((x) => live.L1_SERIES.includes(x)) && live.EARLY_PROBE_SERIES.every((x) => live.CAPPED_SERIES.includes(x) || live.PROBE_SERIES.includes(x)), 'both are already one-contract series, so an early entry can never be larger than a normal one');
};
// RL1 and RL2: the 3 minute rise is LOGGED on every new order (the research session's JUMP1 lead, Oct 22, 2026). Logging only: after the order, public candles, never able to change a trade.
const candle = (endSec, bid, ask) => ({ end_period_ts: endSec, yes_bid: { close_dollars: String(bid) }, yes_ask: { close_dollars: String(ask) } });
gates.RL1 = async () => {
  const nowSec = Math.floor(NOW / 1000);
  // pure: YES side rose from 0.80 to 0.90 over 3 candles = +0.10; a NO order's side rose when the YES mid fell; thin or stale data gives nothing.
  const cs = [candle(nowSec - 180, 0.79, 0.81), candle(nowSec - 120, 0.84, 0.86), candle(nowSec - 60, 0.87, 0.89), candle(nowSec, 0.89, 0.91)];
  const yes = live.riseFromCandles(cs, 'yes', nowSec), no = live.riseFromCandles(cs, 'no', nowSec);
  assert.ok(Math.abs(yes.rise - 0.1) < 1e-9 && Math.abs(no.rise + 0.1) < 1e-9, 'the rise is for the side that was bought: ' + [yes.rise, no.rise]);
  assert.strictEqual(live.riseFromCandles(cs.slice(1), 'yes', nowSec), null, 'no candle 3 minutes earlier: nothing is logged');
  assert.strictEqual(live.riseFromCandles(cs, 'yes', nowSec + 600), null, 'a stale latest candle: nothing is logged');
  assert.strictEqual(live.riseFromCandles([], 'yes', nowSec), null);
  // in the bot: the 10 minute XRP order carries the rise, after being sent as usual.
  const w = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { [XRP10]: { close_time: iso(NOW + 600000) } }, candles: cs });
  await tick(w, { quotes: [q10('KXXRP15M', XRP10)] });
  assert.strictEqual(w.posts.length, 1, 'the order went out');
  const rec = w.docs.get('L1-' + XRP10);
  assert.ok(Math.abs(rec.rise3 - 0.1) < 1e-9 && rec.entryLead === '10m' && rec.status === 'filled', 'and carries the 3 minute rise: ' + rec.rise3);
  const order = w.calls.map((c) => c.method + ' ' + c.url.split('/').slice(-1)[0].split('?')[0]);
  assert.ok(order.indexOf('POST orders') < order.findIndex((x) => /candlesticks/.test(x)), 'the candles are read AFTER the order is sent, never before');
  // a 6 minute order carries it too (the research session reads the lead on every order).
  const w6 = world({ session: { active: true, ordersSent: 0, startCash: 100 }, candles: cs });
  await tick(w6, { quotes: [quote({}, 'KXDOGE15M', 'KXDOGE15M-26OCT071415-06')] });
  assert.strictEqual(w6.posts.length, 1);
  const rec6 = w6.docs.get('L1-KXDOGE15M-26OCT071415-06');
  assert.ok(rec6.entryLead === '6m' && Math.abs(rec6.rise3 - 0.1) < 1e-9, 'a 6 minute order carries the rise too: ' + rec6.rise3);
  // a market that was not entered (not in the band) reads no candles.
  const wn = world({ session: { active: true, ordersSent: 0, startCash: 100 }, candles: cs, fresh: { 'KXETH15M-26OCT071415-07': { yes_bid_dollars: '0.5000', yes_ask_dollars: '0.5100' } } });
  await tick(wn, { quotes: [quote({ yes_bid_dollars: '0.5000', yes_ask_dollars: '0.5100' }, 'KXETH15M', 'KXETH15M-26OCT071415-07')] });
  assert.ok(wn.posts.length === 0 && !wn.calls.some((c) => /candlesticks/.test(c.url)), 'no order, no candle read');
};
gates.RL2 = async () => {
  // Whatever goes wrong with the candles, the order is exactly what it was.
  for (const opts of [{ candlesThrow: true }, { candles: 'none' }, { candles: [] }, { candles: [{ end_period_ts: 'x' }] }]) {
    const w = world(Object.assign({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { [XRP10]: { close_time: iso(NOW + 600000) } } }, opts));
    const r = await tick(w, { quotes: [q10('KXXRP15M', XRP10)] });
    assert.ok(r && r.ok, 'the tick still completes');
    const rec = w.docs.get('L1-' + XRP10);
    assert.ok(w.posts.length === 1 && rec.status === 'filled' && rec.rise3 === undefined, 'order sent and recorded, nothing logged: ' + JSON.stringify(opts).slice(0, 40));
  }
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.ok(!/keyId|pem/.test(src.slice(src.indexOf('async function logRise'), src.indexOf('async function logRise') + 900)), 'it reads public candles with no key');
};
// FL1 and FL2: the path shape flag flips0 is LOGGED on every new order (the research session's FLIPS0 lead, Oct 23, 2026, the owner: "go"). Logging only, same rules as rise3.
// FL1 reproduces the research session's six parity vectors (flips0_parity_vectors_2026-10-23.json) exactly: a field that disagrees with them is not trusted.
gates.FL1 = () => {
  const V = [
    [[0.5, 0.58, 0.66, 0.74, 0.82, 0.91], 5, 0, true], [[0.5, 0.58, 0.52, 0.74, 0.82, 0.91], 5, 2, false], [[0.5, 0.501, 0.6, 0.7, 0.8, 0.9], 5, 0, true],
    [[0.62, 0.7, 0.69, 0.75, 0.74, 0.92], 5, 4, false], [[0.5, 0.55, 0.6, 0.8, 0.795, 0.9], 5, 2, false], [[0.9, 0.91, 0.92, 0.93], 3, 0, false],
  ];
  const nowSec = Math.floor(NOW / 1000);
  for (const [mids, earlier, flips, flips0] of V) {
    // as candles: the favourite is YES here, so the side mid is the YES mid (bid and ask 0.01 either side of it).
    const cs = mids.map((m, i) => candle(nowSec - 60 * (mids.length - 1 - i), m - 0.01, m + 0.01));
    const r = live.pathShape(cs, 'yes', nowSec);
    assert.ok(r.flips === flips && r.flips0 === flips0 && r.earlierCandles === earlier, 'vector ' + JSON.stringify(mids) + ' gave ' + JSON.stringify(r));
    assert.strictEqual(live.flipsOf(mids), flips, 'flipsOf agrees: ' + JSON.stringify(mids));
    // a NO order reads the same path from the other side: its mids are one minus the YES mids, and the same shape comes out.
    const no = live.pathShape(mids.map((m, i) => candle(nowSec - 60 * (mids.length - 1 - i), (1 - m) - 0.01, (1 - m) + 0.01)), 'no', nowSec);
    assert.ok(no.flips === flips && no.flips0 === flips0, 'a NO side gives the same shape');
  }
  assert.strictEqual(live.pathShape([], 'yes', nowSec), null);
  assert.strictEqual(live.pathShape([candle(nowSec - 600, 0.4, 0.42)], 'yes', nowSec), null, 'a stale latest candle logs nothing');
};
gates.FL2 = async () => {
  const nowSec = Math.floor(NOW / 1000), mids = [0.5, 0.58, 0.66, 0.74, 0.82, 0.91];
  const cs = mids.map((m, i) => candle(nowSec - 60 * (mids.length - 1 - i), m - 0.01, m + 0.01));
  const w = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { [XRP10]: { close_time: iso(NOW + 600000) } }, candles: cs });
  await tick(w, { quotes: [q10('KXXRP15M', XRP10)] });
  const rec = w.docs.get('L1-' + XRP10);
  assert.ok(rec.flips === 0 && rec.flips0 === true && rec.earlierCandles === 5 && Number.isFinite(rec.askAtDecision), 'the order carries the flag: ' + JSON.stringify([rec.flips, rec.flips0, rec.earlierCandles, rec.askAtDecision]));
  // logging only: the same market with no candles at all sends the identical order.
  const w0 = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { [XRP10]: { close_time: iso(NOW + 600000) } }, candles: [] });
  await tick(w0, { quotes: [q10('KXXRP15M', XRP10)] });
  assert.strictEqual(w.posts.length, 1); assert.deepStrictEqual(w.posts, w0.posts, 'the order sent does not depend on the path shape');
  const order = w.calls.map((c) => c.method + ' ' + c.url.split('/').slice(-1)[0].split('?')[0]);
  assert.ok(order.indexOf('POST orders') < order.findIndex((x) => /candlesticks/.test(x)), 'read after the order is sent');
  const src = fnSrcLib(), at = src.indexOf('function pathShape'), body = src.slice(at, src.indexOf('// Smooth climb only'));
  assert.ok(!/store\.|fetchFn|liveRequest/.test(body), 'the shape is a pure function of the candles');
};
// SM1 to SM3: Bitcoin and Ethereum order ONLY on a smooth climb (the research session's SMOOTH2 lead, Oct 23, 2026, the owner: "1"). Consequence: the change can only remove Bitcoin and Ethereum orders; anything unreadable places nothing.
// SM1 reproduces the research session's six parity vectors (smooth_parity_vectors_2026-10-23.json) to the decimal, including the two that sit exactly on and just past the -0.005 pullback line.
gates.SM1 = () => {
  const V = [
    [[0.5, 0.58, 0.66, 0.74, 0.82, 0.91], 5, 0.08, 0.41, true], [[0.5, 0.58, 0.575, 0.74, 0.82, 0.91], 5, -0.005, 0.41, false], [[0.5, 0.58, 0.574, 0.74, 0.82, 0.91], 5, -0.006, 0.41, false],
    [[0.6, 0.65, 0.7, 0.72, 0.74, 0.8], 5, 0.02, 0.2, true], [[0.5, 0.6, 0.7, 0.8, 0.9], 4, 0.1, 0.4, true], [[0.91, 0.92, 0.93, 0.92], 3, -0.01, 0.01, false],
  ];
  const nowSec = Math.floor(NOW / 1000);
  for (const [mids, earlier, minStep, climb, smooth] of V) {
    const cs = mids.map((m, i) => candle(nowSec - 60 * (mids.length - 1 - i), m - 0.01, m + 0.01));
    const r = live.pathShape(cs, 'yes', nowSec);
    assert.ok(r.earlierCandles === earlier && Math.abs(r.minStep - minStep) < 1e-9 && Math.abs(r.climb - climb) < 1e-9 && r.smooth === smooth, 'vector ' + JSON.stringify(mids) + ' gave ' + JSON.stringify(r));
  }
  assert.deepStrictEqual(live.SMOOTH_SERIES, ['KXBTC15M', 'KXETH15M'], 'exactly Bitcoin and Ethereum');
};
gates.SM2 = async () => {
  const nowSec = Math.floor(NOW / 1000), mk = (mids) => mids.map((m, i) => candle(nowSec - 60 * (mids.length - 1 - i), m - 0.01, m + 0.01));
  const run = async (series, ticker, candles, extra = {}) => { const w = world(Object.assign({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { [ticker]: { close_time: iso(NOW + 360000) } }, candles }, extra)); await tick(w, { quotes: [quote({ close_time: iso(NOW + 360000) }, series, ticker)] }); return w; };
  const smooth = mk([0.5, 0.58, 0.66, 0.74, 0.82, 0.91]), rough = mk([0.5, 0.58, 0.52, 0.74, 0.82, 0.91]), short = mk([0.8, 0.85, 0.9]);
  for (const [series, ticker] of [['KXBTC15M', 'KXBTC15M-26OCT071415-06'], ['KXETH15M', 'KXETH15M-26OCT071415-06']]) {
    const ok = await run(series, ticker, smooth);
    assert.ok(ok.posts.length === 1 && Number(ok.posts[0].count) === 1, series + ': a smooth climb is ordered, one contract');
    const rec = ok.docs.get('L1-' + ticker);
    assert.ok(rec.smooth === true && rec.entryLead === '6m' && Number.isFinite(rec.minStep) && Number.isFinite(rec.climb), series + ': the record carries smooth, minStep and climb: ' + JSON.stringify([rec.smooth, rec.minStep, rec.climb]));
    for (const [why, cs] of [['a pullback', rough], ['too few candles', short], ['no candles', []], ['an unreadable answer', 'none']]) {
      const w = await run(series, ticker, cs);
      assert.strictEqual(w.posts.length, 0, series + ' ' + why + ': no order');
      assert.ok(/no order/.test(w.sess.lastNote || ''), series + ' ' + why + ': the note says why');
    }
    const thrown = await run(series, ticker, undefined, { candlesThrow: true });
    assert.strictEqual(thrown.posts.length, 0, series + ': a failed read places nothing (fails closed)');
  }
  // Nothing else is affected: gold, XRP, Dogecoin and the probes never read the path before ordering, and still order on a rough path.
  for (const [series, ticker, close] of [['KXDOGE15M', 'KXDOGE15M-26OCT071415-06', NOW + 360000], ['KXXRP15M', XRP10, NOW + 600000]]) {
    const w = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { [ticker]: { close_time: iso(close) } }, candles: rough });
    await tick(w, { quotes: [quote({ close_time: iso(close) }, series, ticker)] });
    assert.strictEqual(w.posts.length, 1, series + ' is not gated');
    const order = w.calls.map((c) => c.method + ' ' + c.url.split('/').slice(-1)[0].split('?')[0]);
    assert.ok(order.indexOf('POST orders') < order.findIndex((x) => /candlesticks/.test(x)), series + ': its candles are read only AFTER the order, for logging');
  }
};
gates.SM3 = () => {
  const src = fnSrcLib();
  assert.ok(/const SMOOTH_MIN_STEP = 0\.005, SMOOTH_MIN_CLIMB = 0\.10;/.test(src), 'the two thresholds are constants in code, not stored values');
  assert.ok(/const EARLY_PROBE_SERIES = \["KXXRP15M", "KXNATGAS15M"\];/.test(src), 'Bitcoin is not on the 10 minute list');
  const at = src.indexOf('async function smoothGate'), body = src.slice(at, src.indexOf('async function logRise'));
  assert.ok(!/keyId|pem|method: "POST"/.test(body), 'the gate reads public candles only: no key, no POST');
  assert.ok(/return \{ ok: false/.test(body) && (body.match(/ok: false/g) || []).length >= 4, 'every unreadable or unsmooth case returns no order');
};
// GF1 to GF3: gold first (Oct 21, 2026, docs/GOLD_FIRST_PROPOSAL.md option A). Gold alone keeps the size ladder and is sent first; Bitcoin, Ethereum, XRP and Dogecoin are capped at one contract; the lists change only by a code edit.
gates.GF1 = async () => {
  assert.deepStrictEqual(live.CAPPED_SERIES, ['KXBTC15M', 'KXETH15M', 'KXXRP15M', 'KXDOGE15M'], 'exactly the four markets that have not earned the ladder');
  assert.ok(!live.CAPPED_SERIES.includes('KXGOLD15M') && !live.CAPPED_SERIES.some((x) => live.PROBE_SERIES.includes(x)), 'gold is not capped, and a market is in at most one of the two lists');
  const base = { sizing: true, sizeCap: 12, sizeAddon: 8, sizeBase: 500, sizePool: 7.4, sizeSaved: 5, sizeNextReview: NOW + 86400000 };
  const rich = { balance_breakdown: [{ balance: '600.0000', exchange_index: 0 }, { balance: '400.0000', exchange_index: 0 }] };
  const w = world({ session: base, balance: rich, fresh: { 'KXBTC15M-26OCT091500-00': { exchange_index: 0 }, 'KXXRP15M-26OCT091500-00': { exchange_index: 0 }, 'KXDOGE15M-26OCT091500-00': { exchange_index: 0 }, [ETH]: { exchange_index: 0 } } });
  await tick(w, { quotes: [quote({}, 'KXBTC15M', 'KXBTC15M-26OCT091500-00'), quote({}, 'KXETH15M', ETH), quote({}, 'KXXRP15M', 'KXXRP15M-26OCT091500-00'), quote({}, 'KXDOGE15M', 'KXDOGE15M-26OCT091500-00'), gq()],
    sizingState: { cap: 12, base: 500, reviewedAt: NOW - 1000, pool: 7.4, saved: 5, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async () => {} });
  const by = (frag) => w.posts.filter((p) => p.ticker.includes(frag));
  assert.ok(by('KXGOLD').length === 1 && Number(by('KXGOLD')[0].count) > 2, 'gold takes the ladder size: ' + by('KXGOLD').map((p) => p.count));
  // One crypto order per window: of the four capped markets sharing this window only the first in list order (XRP since Oct 23, 2026) is sent, at its fixed size.
  const crypto = w.posts.filter((p) => !p.ticker.includes('KXGOLD'));
  assert.ok(crypto.length === 1 && crypto[0].ticker.includes('KXXRP') && Number(crypto[0].count) === 1, 'one capped market per window, the first in list order (XRP since Oct 23, 2026) at its fixed size, never the ladder or the pool: ' + crypto.map((p) => p.ticker + 'x' + p.count));
  for (const p of w.posts) { const rec = w.docs.get('L1-' + p.ticker); assert.ok(rec.strategy === 'L1' && (!rec.addon || p.ticker.includes('KXGOLD')), 'a capped market never carries reinvested profit: ' + p.ticker); }
};
gates.GF2 = async () => {
  // Gold is sent first whatever order the quotes arrive in: it takes its full size even when a capped market is listed ahead of it and the window's limit is tight.
  const solo = world({ session: wsess({}), balance: rich });
  await tick(solo, { quotes: [quote({}, 'KXGOLD15M', GOLD)], sizingState: wstate, setSizingState: async () => {} });
  const w = world({ session: wsess({}), balance: rich });
  await tick(w, { quotes: [quote({}, 'KXBTC15M', BTCW), quote({}, 'KXETH15M', ETH), quote({}, 'KXGOLD15M', GOLD)], sizingState: wstate, setSizingState: async () => {} });
  const gold = w.posts.find((p) => p.ticker === GOLD);
  assert.ok(gold && gold.count === solo.posts[0].count, 'gold trades its full stake even when listed last: ' + (gold && gold.count) + ' vs ' + solo.posts[0].count);
  assert.strictEqual(w.posts[0].ticker, GOLD, 'and it is the first order sent');
};
gates.GF3 = () => {
  const src = fnSrcLib();
  assert.ok(/const CAPPED_SERIES = \["KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M"\];/.test(src) && /PROBE_SERIES\.includes\(c\.series\) \|\| CAPPED_SERIES\.includes\(c\.series\)/.test(src), 'the capped list is a hard list in code and is applied beside the probe rule');
  const idx = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  assert.ok(!/CAPPED_SERIES|request\.data\.(ticker|price|count|side)/.test(idx), 'no callable or stored value can change which markets are capped or how many contracts an order has');
};
gates.X5 = async () => {
  // Solana stored on the session is never traded, even if its quotes arrive
  const w = world({ session: { liveExtra: { KXSOL15M: 5 } } });
  await tick(w, { quotes: [quote({}, 'KXSOL15M', 'KXSOL15M-26OCT091500-00')] });
  assert.strictEqual(w.posts.length, 0, 'a series that is not on the list never trades');
};
gates.X6 = async () => {
  // Ethereum sits on a shard with too little money: skipped with the reason, Bitcoin still trades
  const sess = { liveExtra: { KXETH15M: 2 } };
  const w = world({ session: sess, fresh: { [ETH]: { exchange_index: 0 } }, balance: { balance_breakdown: [{ balance: '90.0000', exchange_index: 2 }, { balance: '0.2000', exchange_index: 0 }] } });
  await tick(w, { quotes: [quote(), quote({}, 'KXETH15M', ETH)] });
  assert.strictEqual(w.posts.filter((p) => p.ticker === T).length, 1, 'Bitcoin, with money on its own shard, still trades');
  assert.strictEqual(w.posts.filter((p) => p.ticker === ETH).length, 0, 'no money on its shard, no order');
};
gates.X7 = async () => {
  // the loss stop and the pool read Ethereum orders like any other L1 order: one stop for the whole account
  const lostEth = { id: 'L1-' + ETH, strategy: 'L1', ticker: ETH, series: 'KXETH15M', side: 'yes', count: 2, fillCount: '2.00', maxCost: 1.88, addonCost: 0, ts: NOW - 1000, settled: true, result: 'no', settledPnl: -1.88 };
  const risk = await live.botRisk({ store: { sessionTrades: async () => [lostEth], updateTest: async () => {} }, since: 0, fetchFn: async () => { throw new Error('settled records need no network'); }, nowMs: NOW });
  assert.ok(Math.abs(risk.net + 1.88) < 1e-9, 'an Ethereum loss counts toward the same stop as Bitcoin and gold');
  const fold = live.foldSkim({ pool: 3, saved: 3, cum: 6, hwm: 6, appliedTs: 0 }, [{ ...lostEth, ts: 5 }]);
  assert.ok(fold.pool < 3, 'and comes out of the same pool');
};
gates.X8 = () => {
  const idx = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  assert.ok(!/kalshiExtraSeries|liveExtra|EXTRA_LEVELS/.test(idx), 'there is no callable or stored setting for Ethereum any more');
  assert.ok(!/request\.data\.(ticker|price|count|side)/.test(idx), 'still no callable takes a ticker, price or size from the caller');
  const armed = idx.slice(idx.indexOf('exports.kalshiLiveArmed = onSchedule('));
  assert.ok(/live\.L1_SERIES\.filter\(\(x\) => !live\.LIVE_SERIES\.includes\(x\)\)/.test(armed) && /quotes skipped/.test(armed), 'Ethereum\'s quotes are added, and a failure there never stops Bitcoin and gold');
};

// W1 to W3: the combined cap per window. Bitcoin, gold and Ethereum close together and move together, so one window may put only so much of the account at risk, however many series fire.
const BTCW = 'KXBTC15M-26OCT091500-00';
const GOLD = 'KXGOLD15M-26OCT091500-00';
const wsess = (extra) => ({ sizing: true, sizeCap: 40, sizeAddon: 0, sizeBase: 1000, sizeNextReview: NOW + 86400000, liveExtra: extra });
const wstate = { cap: 40, base: 1000, reviewedAt: NOW - 1000, pool: 0, saved: 0, appliedTs: NOW - 1000, lastStopAt: null };
const rich = { balance_breakdown: [{ balance: '1000.0000', exchange_index: 2 }, { balance: '1000.0000', exchange_index: 0 }] };
gates.W1 = async () => {
  // a window's account money never exceeds the combined limit, whatever number of series fire
  const w = world({ session: wsess({ KXETH15M: 50 }), balance: rich, fresh: { [ETH]: { exchange_index: 0 }, [GOLD]: { exchange_index: 0 } } });
  await tick(w, { quotes: [quote({}, 'KXBTC15M', BTCW), quote({}, 'KXGOLD15M', GOLD), quote({}, 'KXETH15M', ETH)], sizingState: wstate, setSizingState: async () => {} });
  const spent = [...w.docs.values()].reduce((a, d) => a + d.maxCost, 0);
  assert.ok(spent <= live.L1_WINDOW_CAP_FRACTION * 1000 + 1e-9, 'three series in one window put $' + spent.toFixed(2) + ' at risk, over the limit');
  assert.ok(w.posts.length >= 1, 'and the window still trades');
};
gates.W2 = async () => {
  // Ethereum is the one that goes without when the room is used: Bitcoin is sent first, at its full size
  const w = world({ session: wsess({ KXETH15M: 50 }), balance: rich });
  const solo = world({ session: wsess({}), balance: rich });
  await tick(solo, { quotes: [quote({}, 'KXBTC15M', BTCW)], sizingState: wstate, setSizingState: async () => {} });
  await tick(w, { quotes: [quote({}, 'KXETH15M', ETH), quote({}, 'KXBTC15M', BTCW)], sizingState: wstate, setSizingState: async () => {} });
  const btc = w.posts.find((p) => p.ticker === BTCW);
  assert.ok(btc && btc.count === solo.posts[0].count, 'Bitcoin trades its full stake even when Ethereum is listed first: ' + (btc && btc.count));
};
// W4: the window limit is 5.5% and the loss stop 6% (the owner's choices, Oct 20, 2026: the limit was raised so the last series in the list stops getting 1 contract, and the stop with it). The limit stays
// UNDER the stop, so one window alone cannot reach it. Pinned so neither is moved without the other being decided.
gates.W4 = () => {
  assert.strictEqual(live.L1_WINDOW_CAP_FRACTION, 0.055, 'the window limit the owner chose');
  assert.strictEqual(live.L1_SIZED_STOP_FRACTION, 0.12, 'the loss stop the owner chose (6% on Oct 20, then 12% the same night)');
  assert.ok(live.L1_WINDOW_CAP_FRACTION < live.L1_SIZED_STOP_FRACTION, 'one window alone cannot reach the loss stop');
};

// W5: the night of Oct 20, 2026. $6.06 of SETTLED losses (two ordinary ones) with a full window ($8.43) still open ended the bot at a 6% stop, because an open order is counted as lost and the window limit (5.5%)
// left almost no room under it. At 12% the same book does not stop, and a book that is really bad still does.
gates.W5 = async () => {
  const base = 163;
  const mk = async (lost, open) => {
    const w = world({ results: Object.fromEntries(lost.map((_, i) => ['OLD-' + i, 'no'])) });
    lost.forEach((c, i) => { const [id, d] = botTrade(i, { count: 4, fillCount: '4.00', maxCost: c }); w.docs.set(id, d); });
    open.forEach((c, i) => { const [id, d] = botTrade(lost.length + i, { count: 4, fillCount: '4.00', maxCost: c }); w.docs.set(id, d); });
    return live.botRisk({ store: w.store, since: 0, fetchFn: w.fetchFn, nowMs: NOW });
  };
  const night = await mk([3.03, 3.03], [4.215, 4.215]);
  assert.ok(Math.abs(night.net + 6.06) < 1e-9 && Math.abs(night.openCost - 8.43) < 1e-9, 'the book from that night: -$6.06 settled, $8.43 open');
  assert.ok(night.worst <= -(0.06 * base + 0.92), 'at the old 6% (plus the $0.92 of reinvested profit) this book stopped the bot');
  assert.ok(night.worst > -(live.L1_SIZED_STOP_FRACTION * base + 0.92), 'at the current stop it does not');
  const bad = await mk([3.03, 3.03, 6.5], [4.215, 4.215]);
  assert.ok(bad.worst <= -(live.L1_SIZED_STOP_FRACTION * base), 'a book that is really down ($12.56 settled with a full window open) still stops it');
};

gates.W3 = async () => {
  // orders from an earlier tick in the same window count, so the next minute cannot start the window over
  const w = world({ session: wsess({}), balance: rich });
  const used = live.L1_WINDOW_CAP_FRACTION * 1000;
  w.docs.set('L1-earlier', { strategy: 'L1', ticker: BTCW.replace(/-00$/, '-99'), status: 'filled', maxCost: used, addonCost: 0, ts: NOW - 60000 });
  await tick(w, { quotes: [quote({}, 'KXBTC15M', BTCW)], sizingState: wstate, setSizingState: async () => {} });
  assert.strictEqual(w.posts.length, 0, 'a window already at the limit takes no more');
  const other = world({ session: wsess({}), balance: rich });
  other.docs.set('L1-earlier', { strategy: 'L1', ticker: 'KXBTC15M-26OCT090000-00', status: 'filled', maxCost: used, addonCost: 0, ts: NOW - 60000 });
  await tick(other, { quotes: [quote({}, 'KXBTC15M', BTCW)], sizingState: wstate, setSizingState: async () => {} });
  assert.ok(other.posts.length === 1, 'a different window is unaffected');
};

// K2: a pool that does not move must be explainable. The fold reports the order it is waiting on and the tick saves the rule in force and how far it counted (the page no longer prints either).
gates.K2 = () => {
  const st = { pool: 0, saved: 0, cum: 0, hwm: 0, appliedTs: 100 };
  const row = (ts, p, settled) => ({ id: 'o' + ts, ticker: 'T' + ts, strategy: 'L1', fillCount: '12', maxCost: 11.3, ts, settled, settledPnl: settled ? p : undefined });
  const f = live.foldSkim(st, [row(200, 0.4, true), row(300, 0.5, false), row(400, 0.6, true)], { everyWin: true });
  assert.deepStrictEqual(f.blocked, { ticker: 'T300', ts: 300 }, 'names the unsettled order that stops the count');
  assert.ok(Math.abs(f.pool - 0.2) < 1e-9 && f.appliedTs === 200, 'and counts nothing past it');
  assert.strictEqual(live.foldSkim(st, [row(200, 0.4, true)], { everyWin: true }).blocked, null, 'nothing blocked when everything settled');
  const src = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.ok(/sizePoolRule: "wins", sizePoolThrough: sizeState\.appliedTs, sizePoolBlocked: fs\.blocked \? fs\.blocked\.ticker : null/.test(src), 'the tick saves them');
  const html = require('fs').readFileSync(require('path').join(__dirname, '..', 'index.html'), 'utf8');
  // The page no longer shows them (owner's cleanup, Oct 12, 2026): the rule is fixed in the code, so "Pool rule in use" described a setting that does not exist, and "Counted through" was bookkeeping.
  assert.ok(!/Pool rule in use|Counted through|waiting on /.test(html), 'the page does not show the fixed rule or the count position');
};

// K1: pressing Start can no longer undo the owner's risk settings, because there are none to undo. It replaces the session document, and it once reset the exit to log only and the pool to "after new highs"
// while the page's menu still looked configured (Oct 10, 2026). The switches were removed on Oct 12, 2026: the exit (50c, always selling) and the pool (after every win) are fixed in the code, so a restart
// cannot leave either one in a different state, and an old exitMode or poolRule left on the document is not read by anything.
gates.K1 = () => {
  assert.strictEqual(live.ownerSettings, undefined, 'no owner switches are carried across a Start');
  assert.strictEqual(live.OWNER_SETTINGS, undefined);
  const idx = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  const start = idx.slice(idx.indexOf('exports.kalshiL1Session = onCall'), idx.indexOf('// ---- Flatten all + halt'));
  assert.ok(/await ref\.set\(\{ active: true, since: now,/.test(start) && !/ownerSettings|prior/.test(start.replace(/\/\/.*$/gm, '')), 'Start writes a fresh session document and reads nothing from the old one');
};

// K3: the code-level kill switch. While it is on, the scheduled tick is told live trading is off whatever the server switch says, and the bot cannot be started.
gates.K3 = () => {
  const idx = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  assert.ok(/const CODE_KILL_SWITCH = (true|false);/.test(idx), 'the switch is a literal boolean, so one token turns all buying off');
  assert.ok(/enabled: !CODE_KILL_SWITCH && KALSHI_LIVE_ENABLED\.value\(\) === "on"/.test(idx), 'the tick is told trading is off');
  const start = idx.slice(idx.indexOf('exports.kalshiL1Session = onCall'), idx.indexOf('// ---- Flatten all + halt'));
  assert.ok(/if \(CODE_KILL_SWITCH\) \{\n\s*throw new HttpsError\("failed-precondition"/.test(start), 'Start refuses, before anything is written');
};

// K4: a Flatten or Stop that lands while a tick is already running cannot be followed by an order from that tick. The tick read "not halted" at its start, then spent seconds on the
// balance and the markets; the halt is read again right before the order is recorded.
gates.K4 = async () => {
  const w = world({ haltAfterFirstRead: true });
  await tick(w);
  assert.strictEqual(w.posts.length, 0, 'halted mid-tick: no order is sent');
  assert.strictEqual(w.docs.size, 0, 'and no order record is created');
  const ok = world();
  await tick(ok);
  assert.strictEqual(ok.posts.length, 1, 'control: the same tick without a halt does send');
};

// K5: Start on a bot that is already running is refused before anything is written. Starting replaces the session document, and the loss stop counts from its `since`, so a stale tab
// could otherwise give a bot that is down most of its stop a fresh budget.
gates.K5 = () => {
  const idx = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  const start = idx.slice(idx.indexOf('exports.kalshiL1Session = onCall'), idx.indexOf('// ---- Flatten all + halt'));
  const guard = start.indexOf('running.data().active === true');
  assert.ok(guard > 0 && /throw new HttpsError\("failed-precondition", "The bot is already running/.test(start.slice(guard, guard + 200)), 'a running bot refuses Start');
  assert.ok(guard < start.indexOf('await ref.set({ active: true, since: now'), 'and it refuses before the session document is replaced');
};

// K6: the tick reads the last 24 hours of orders ONCE and shares them with the loss-stop sum (a read is billed, and this runs every minute), and every new order is written
// settled: false so the settle sweep can ask only for the unsettled ones.
gates.K6 = async () => {
  const w = world();
  let reads = 0; const orig = w.store.sessionTrades; w.store.sessionTrades = async (since) => { reads++; return orig(since); };
  await tick(w);
  assert.strictEqual(reads, 1, 'one read of the order history per tick, not one for the count and another for the stop');
  assert.strictEqual(w.posts.length, 1, 'control: the tick still trades');
  assert.strictEqual([...w.docs.values()][0].settled, false, 'a new order is written settled: false');
  // sharing the list must not change the number: orders older than the window are left out, as the store query would have
  const old = { id: 'A', ts: NOW - 5000, strategy: 'L1', fillCount: '1', maxCost: 1, count: 1, side: 'yes', ticker: 'X', settled: true, result: 'no' };
  const older = { ...old, id: 'B', ts: NOW - 99999999 };
  const r = await live.botRisk({ store: {}, since: NOW - 10000, fetchFn: async () => { throw new Error('no network'); }, nowMs: NOW, orders: [old, older] });
  assert.ok(r.net < 0 && r.net > -1.5, 'only the order inside the window counts (one lost $1, not two): ' + r.net);
};

// K7: the exit watch is skipped only when it truly has nothing to watch. Outside the minutes L1 buys in, with no open filled order: idle. Anything else, or anything unreadable: it runs.
gates.K7 = async () => {
  const at = (minute) => Date.UTC(2026, 9, 12, 14, 0, 0) + minute * 60000;      // 14:00 UTC is a quarter hour, so minute m is minute m of the cycle
  const empty = { recentFilled: async () => [] };
  assert.strictEqual(await live.exitWatchIdle({ store: empty, now: at(1) }), true, 'nothing open, not a buy minute: idle');
  const open = { recentFilled: async () => [{ strategy: 'L1', settled: false, fillCount: '9' }] };
  assert.strictEqual(await live.exitWatchIdle({ store: open, now: at(1) }), false, 'a filled, unsettled L1 order: it must run');
  assert.strictEqual(await live.exitWatchIdle({ store: { recentFilled: async () => [{ strategy: 'L1', settled: true, fillCount: '9' }] }, now: at(1) }), true, 'a settled order is nothing to watch');
  assert.strictEqual(await live.exitWatchIdle({ store: { recentFilled: async () => { throw new Error('down'); } }, now: at(1) }), false, 'unreadable: it runs');
  // The early entry window (about 10 minutes left, XRP and natural gas) is covered the same way, so an order placed then is watched from its first minute.
  for (let left = 570000; left <= 640000; left += 1000) {
    const t = at(15) - left;
    assert.strictEqual(await live.exitWatchIdle({ store: empty, now: t }), false, 'early window: with ' + left / 1000 + 's left the watch runs');
    assert.strictEqual(await live.exitWatchIdle({ store: empty, now: t + 60000 }), false, 'and so does the next minute');
  }
  // Every second in which L1 may place an order falls in a minute the watch runs, and so does the minute after it: an order placed late in minute 9 is watched from minute 10.
  for (let left = 330000; left <= 400000; left += 1000) {
    const t = at(15) - left;
    assert.strictEqual(await live.exitWatchIdle({ store: empty, now: t }), false, 'with ' + left / 1000 + 's left the watch runs');
    assert.strictEqual(await live.exitWatchIdle({ store: empty, now: t + 60000 }), false, 'and so does the next minute');
  }
  assert.ok(live.EXIT_BUY_MINUTES.length >= 4 && live.EXIT_BUY_MINUTES.length <= 9, 'about half of the minutes in fifteen (the 6 minute and the 10 minute entry windows), not all of them');
  const idx = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  const fn = idx.slice(idx.indexOf('exports.kalshiLiveExit = onSchedule'), idx.indexOf('exports.kalshiLiveArmed = onSchedule'));
  assert.ok(fn.indexOf('live.exitWatchIdle') > 0 && fn.indexOf('live.exitWatchIdle') < fn.indexOf('for (;;)'), 'the scheduled function asks before it loops');
};

// K8: the research book recorder is off, and nothing that trades depends on it.
gates.K8 = () => {
  const idx = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  assert.ok(/const BOOK_RECORDER_ON = false;/.test(idx), 'the recorder is off');
  const rec = idx.slice(idx.indexOf('exports.kalshiBookRecorder = onSchedule'));
  const off = rec.slice(rec.indexOf('if (!BOOK_RECORDER_ON) {'), rec.indexOf('book.recordMinute'));
  assert.ok(off.length > 0 && off.indexOf('book.recordMinute') < 0, 'while off it never reads a market or records a snapshot');
  // Oct 21, 2026 cost review: off, it only deletes snapshots older than a day (the recorder was the only thing that ever pruned them, so the ones from before Oct 12 kept billing as stored data).
  assert.ok(/\.where\("ts", "<", Date\.now\(\) - 86400000\)\.limit\(200\)/.test(off) && /\.delete\(\)/.test(off) && !/\.set\(|\.add\(|\.update\(|fetch|kalshiGetJson/.test(off), 'it only deletes old snapshots');
  assert.ok(/const PAPER_TRACKER_ON = false;/.test(idx) && idx.indexOf('if (!PAPER_TRACKER_ON) return;') > idx.indexOf('exports.kalshiPaperTick = onSchedule'), 'the paper tracker returns at once');
};

// K9: the settle sweep finds an unsettled order whether or not it carries the settled field (orders created before it existed do not).
gates.K9 = () => {
  const idx = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  const live = idx.slice(idx.indexOf('function firestoreLiveStore'), idx.indexOf('// ---- Kalshi account view'));
  assert.ok(/where\("status", "==", "filled"\)\.where\("settled", "==", false\)/.test(live), 'asks for filled and unsettled, not every filled order');
  assert.ok(/where\("ts", ">=", Date\.now\(\) - 3 \* 3600 \* 1000\)/.test(live), 'and also the last few hours, for orders written without the field');
};

// K10: L1 is the only strategy. The opening window paper recorder (OW1) was removed on Oct 12, 2026 at the owner's request: the strategies must not overlap in mindset or position, and nothing
// that holds to settlement can avoid overlapping L1. There is no recorder function, no module, no collection rule and no page code for it. The research record stays in kalshi-scalper.
gates.K10 = () => {
  const fs = require('fs'), path = require('path');
  const root = path.join(__dirname, '..');
  assert.ok(!fs.existsSync(path.join(root, 'functions', 'kalshiOpeningLib.js')), 'the recorder module is gone');
  const idx = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
  assert.ok(!/kalshiOpening|OPENING_SERIES|runOpeningTick/.test(idx), 'no recorder function, store or require in index.js');
  const rules = fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8');
  assert.ok(!/kalshiOpening/.test(rules), 'no rule for its collections: they are denied by default');
  assert.deepStrictEqual([...idx.matchAll(/exports\.(\w+) = onSchedule\(/g)].map((x) => x[1]), ['marketTapeTick', 'kalshiLiveExit', 'kalshiLiveArmed', 'kalshiPaperTick', 'kalshiBookRecorder'], 'the scheduled functions are the exit watch, the live bot, the keyless paper tracker (PAPER1, Oct 20, 2026) and the (off) recorder');
};

// OC1: only one of Bitcoin, Ethereum, XRP, Dogecoin per window (Oct 22, 2026). Consequence: two correlated crypto positions never lose together in one window, and a missed order does not block the window.
gates.OC1 = async () => {
  const w = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { 'KXBTC15M-26OCT091500-00': {}, 'KXETH15M-26OCT091500-00': {}, 'KXDOGE15M-26OCT091500-00': {} } });
  await tick(w, { quotes: [quote({}, 'KXBTC15M', 'KXBTC15M-26OCT091500-00'), quote({}, 'KXETH15M', 'KXETH15M-26OCT091500-00'), quote({}, 'KXDOGE15M', 'KXDOGE15M-26OCT091500-00')] });
  assert.strictEqual(w.posts.length, 1, 'three crypto markets in one window place one order: ' + w.posts.map((p) => p.ticker));
  assert.ok(w.posts[0].ticker.includes('KXBTC'));
  const w2 = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { 'KXBTC15M-26OCT091500-00': {}, 'KXETH15M-26OCT091515-15': {} } });
  await tick(w2, { quotes: [quote({}, 'KXBTC15M', 'KXBTC15M-26OCT091500-00'), quote({}, 'KXETH15M', 'KXETH15M-26OCT091515-15')] });
  assert.strictEqual(w2.posts.length, 2, 'different windows are independent');
};

// RR1: a read that Kalshi refuses with 429 is asked once more, an order never is. Consequence: one refused balance read no longer skips a minute's entries or blanks the account card, and a refused order is never sent twice.
gates.RR1 = async () => {
  const mk = (status) => { const calls = []; return { calls, fetchFn: async (url, o) => { calls.push(o.method); return { status: calls.length === 1 ? status : 200, text: async () => '{}' }; } }; };
  const g = mk(429);
  const r = await live.liveRequest({ fetchFn: g.fetchFn, method: 'GET', path: '/portfolio/balance' });
  assert.deepStrictEqual([g.calls.length, r.status], [2, 200], 'a refused GET is asked once more');
  const p = mk(429);
  const r2 = await live.liveRequest({ fetchFn: p.fetchFn, method: 'POST', path: '/portfolio/events/orders', body: {} });
  assert.deepStrictEqual([p.calls.length, r2.status], [1, 429], 'an order is never retried');
  const h = { calls: [], fetchFn: async (u, o) => { h.calls.push(1); return { status: 429, text: async () => '{}' }; } };
  const r3 = await live.liveRequest({ fetchFn: h.fetchFn, method: 'GET', path: '/portfolio/balance' });
  assert.deepStrictEqual([h.calls.length, r3.status], [2, 429], 'a second 429 comes back as it is, after one retry only');
};

// RL3: rng5, the 5 minute range of the bought side's mid, is logged beside rise3 (the research session's FLAT2 lead, Oct 22, 2026). Logging only. Consequence: a quiet market and a jumpy one can be told apart after the fact, and a thin read logs nothing rather than a wrong range.
gates.RL3 = async () => {
  const nowSec = Math.floor(NOW / 1000);
  const mids = [0.80, 0.86, 0.83, 0.84, 0.88, 0.90];   // oldest first, six minute marks t-300 .. t
  const cs = mids.map((m, i) => candle(nowSec - 300 + i * 60, (m - 0.01).toFixed(2), (m + 0.01).toFixed(2)));
  const yes = live.riseFromCandles(cs, 'yes', nowSec), no = live.riseFromCandles(cs, 'no', nowSec);
  assert.ok(Math.abs(yes.rng - 0.10) < 1e-9 && Math.abs(no.rng - 0.10) < 1e-9, 'the range is max minus min of the six marks, the same for either side: ' + [yes.rng, no.rng]);
  assert.ok(Math.abs(yes.rise - 0.07) < 1e-9, 'rise3 is unchanged by it: ' + yes.rise);
  const five = live.riseFromCandles(cs.slice(1), 'yes', nowSec);
  assert.ok(five && five.rng === null, 'a missing mark leaves the range out, and the rise (which has its own mark) is still read');
  const w = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { [XRP10]: { close_time: iso(NOW + 600000) } }, candles: cs });
  await tick(w, { quotes: [q10('KXXRP15M', XRP10)] });
  const rec = w.docs.get('L1-' + XRP10);
  assert.ok(w.posts.length === 1 && Math.abs(rec.rng5 - 0.10) < 1e-9, 'the order carries rng5: ' + rec.rng5);
  const w2 = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { [XRP10]: { close_time: iso(NOW + 600000) } }, candles: cs.slice(1) });
  await tick(w2, { quotes: [q10('KXXRP15M', XRP10)] });
  const rec2 = w2.docs.get('L1-' + XRP10);
  assert.ok(w2.posts.length === 1 && rec2.rng5 === undefined && rec2.rise3 !== undefined, 'a five-mark read logs the rise and no range');
};

// FS1 to FS3: fixed order sizes (Oct 23, 2026, the owner: "yeah build", on the research session's sizing proposal at a $500 balance). XRP and Dogecoin trade 3 contracts, natural gas 2; Bitcoin and Ethereum stay at 1.
// Consequence: the larger size reaches only the three markets the history supports, and never grows through the ladder, the profit add-on, a stored value or a second crypto order in the window.
gates.FS1 = async () => {
  assert.deepStrictEqual(live.FIXED_CONTRACTS, { KXXRP15M: 1, KXDOGE15M: 3, KXNATGAS15M: 2 }, 'exactly these three markets, at exactly these sizes');
  const one = async (series, ticker, closeAt) => {
    const w = world({ session: wsess({}), balance: rich, fresh: { [ticker]: { exchange_index: 0, close_time: iso(closeAt) } } });
    await tick(w, { quotes: [quote({ close_time: iso(closeAt) }, series, ticker)], sizingState: { cap: 40, base: 1000, reviewedAt: NOW - 1000, pool: 50, saved: 0, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async () => {} });
    return w;
  };
  const doge = await one('KXDOGE15M', 'KXDOGE15M-26OCT071415-06', NOW + 360000);
  assert.strictEqual(doge.posts.length === 1 && Number(doge.posts[0].count), 3, 'Dogecoin takes 3 contracts');
  const xrp = await one('KXXRP15M', XRP10, NOW + 600000);
  assert.strictEqual(xrp.posts.length === 1 && Number(xrp.posts[0].count), 1, 'XRP takes 1 contract (back from 3 on Oct 25, 2026)');
  const gas = await one('KXNATGAS15M', 'KXNATGAS15M-26OCT071415-10', NOW + 600000);
  assert.strictEqual(gas.posts.length === 1 && Number(gas.posts[0].count), 2, 'natural gas takes 2 contracts');
  const btc = await one('KXBTC15M', 'KXBTC15M-26OCT071415-06', NOW + 360000);
  assert.strictEqual(btc.posts.length === 1 && Number(btc.posts[0].count), 1, 'Bitcoin stays at 1 contract');
  const eth = await one('KXETH15M', 'KXETH15M-26OCT071415-06', NOW + 360000);
  assert.strictEqual(eth.posts.length === 1 && Number(eth.posts[0].count), 1, 'Ethereum stays at 1 contract');
  const aud = await one('KXAUDUSD15M', 'KXAUDUSD15M-26OCT071415-06', NOW + 360000);
  assert.strictEqual(aud.posts.length === 1 && Number(aud.posts[0].count), 1, 'the other probes stay at 1 contract');
  for (const w of [doge, xrp, gas]) { const rec = w.docs.get('L1-' + w.posts[0].ticker); assert.ok(!rec.addon && !rec.addonCost, 'no reinvested profit goes into a fixed size, however full the pool is'); }
};
gates.FS2 = async () => {
  // The window limit still holds: with a base too small to afford 3 Dogecoin contracts in one window the order is cut, and it is never cut below the first contract.
  const tiny = { sizing: true, sizeCap: 1, sizeAddon: 0, sizeBase: 20, sizeNextReview: NOW + 86400000 };
  const w = world({ session: tiny, balance: rich, fresh: { 'KXDOGE15M-26OCT071415-06': { exchange_index: 0 } } });
  await tick(w, { quotes: [quote({}, 'KXDOGE15M', 'KXDOGE15M-26OCT071415-06')], sizingState: { cap: 1, base: 20, reviewedAt: NOW - 1000, pool: 0, saved: 0, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async () => {} });
  const n = w.posts.length === 1 ? Number(w.posts[0].count) : 0;
  assert.ok(n >= 1 && n <= 3, 'a small base cuts the larger size down to what the window limit allows: ' + n);
  const w2 = world({ session: wsess({}), balance: rich, fresh: { 'KXDOGE15M-26OCT071415-06': { exchange_index: 0 }, 'KXXRP15M-26OCT071415-06': { exchange_index: 0 } } });
  await tick(w2, { quotes: [quote({}, 'KXDOGE15M', 'KXDOGE15M-26OCT071415-06'), quote({}, 'KXXRP15M', 'KXXRP15M-26OCT071415-06')], sizingState: wstate, setSizingState: async () => {} });
  assert.strictEqual(w2.posts.length, 1, 'still one crypto order per window, so 3 and 3 never stack');
};
gates.FS3 = () => {
  const src = fnSrcLib();
  assert.ok(/const FIXED_CONTRACTS = \{ KXXRP15M: 1, KXDOGE15M: 3, KXNATGAS15M: 2 \};/.test(src) && /count = sizing && FIXED_CONTRACTS\[c\.series\] \? FIXED_CONTRACTS\[c\.series\] : 1/.test(src), 'the sizes are a hard list in code and apply only when sizing is on');
  const idx = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  assert.ok(!/FIXED_CONTRACTS|request\.data\.(ticker|price|count|side)/.test(idx), 'no callable or stored value can change an order size');
};

// OS1: series order (Oct 23, 2026, the owner's reorder after the research session's question). Consequence: when two capped crypto markets qualify in the same tick, the 3 contract market (XRP over Bitcoin, Dogecoin over Ethereum) gets the one crypto order of the window, and nothing else about the order changes.
gates.OS1 = async () => {
  assert.deepStrictEqual(live.L1_SERIES, ['KXGOLD15M', 'KXXRP15M', 'KXBTC15M', 'KXDOGE15M', 'KXETH15M', 'KXAUDUSD15M', 'KXUSDCAD15M', 'KXNATGAS15M'], 'gold first, XRP before Bitcoin, Dogecoin before Ethereum, probes last');
  assert.deepStrictEqual(live.CAPPED_SERIES.slice().sort(), ['KXBTC15M', 'KXDOGE15M', 'KXETH15M', 'KXXRP15M'], 'the capped list is the same four markets');
  assert.deepStrictEqual(live.FIXED_CONTRACTS, { KXXRP15M: 1, KXDOGE15M: 3, KXNATGAS15M: 2 }, 'sizes unchanged');
  const run = async (list, lead) => {
    const close = NOW + (lead === '10m' ? 600000 : 360000);
    const fresh = {}, quotes = [];
    for (const [series, ticker] of list) { fresh[ticker] = { exchange_index: 0, close_time: iso(close) }; quotes.push(quote({ close_time: iso(close) }, series, ticker)); }
    const w = world({ session: wsess({}), balance: rich, fresh });
    await tick(w, { quotes, sizingState: { cap: 40, base: 1000, reviewedAt: NOW - 1000, pool: 0, saved: 0, appliedTs: NOW - 1000, lastStopAt: null }, setSizingState: async () => {} });
    return w;
  };
  // Quotes handed over in the OLD order (Bitcoin first) still resolve by list order: XRP wins at the 10 minute tick.
  const ten = await run([['KXBTC15M', 'KXBTC15M-26OCT071415-10'], ['KXXRP15M', 'KXXRP15M-26OCT071415-10']], '10m');
  assert.strictEqual(ten.posts.length, 1, 'one crypto order in the window');
  assert.ok(ten.posts[0].ticker.includes('KXXRP') && Number(ten.posts[0].count) === 1, 'XRP (1 contract) is the only one with a 10 minute look: ' + ten.posts.map((p) => p.ticker + 'x' + p.count));
  const six = await run([['KXETH15M', 'KXETH15M-26OCT071415-06'], ['KXDOGE15M', 'KXDOGE15M-26OCT071415-06']], '6m');
  assert.strictEqual(six.posts.length, 1);
  assert.ok(six.posts[0].ticker.includes('KXDOGE') && Number(six.posts[0].count) === 3, 'Dogecoin (3 contracts) takes the window from Ethereum: ' + six.posts.map((p) => p.ticker + 'x' + p.count));
  // Bitcoin and Ethereum still trade when their pair partner has no qualifying market (the order only decides ties).
  const btc = await run([['KXBTC15M', 'KXBTC15M-26OCT071415-06']], '6m');
  assert.ok(btc.posts.length === 1 && btc.posts[0].ticker.includes('KXBTC') && Number(btc.posts[0].count) === 1, 'Bitcoin alone still trades, at one contract');
  const src = fnSrcLib();
  assert.ok(/const L1_SERIES = \["KXGOLD15M", "KXXRP15M", "KXBTC15M", "KXDOGE15M", "KXETH15M", \.\.\.PROBE_SERIES\];/.test(src), 'the order is a hard list in code');
};


// TS1 to TS3: the two-stage look is LOGGED on every new order (the research session's TWOSTAGE log request, Oct 24, 2026; the owner: "Yes, build it (log only)"). Consequences: it reads exact candles only (no neighbour is
// substituted, a missing candle is no value rather than "not in band"), it records the earliest look that was in the band, and it never changes an order, a size, an entry time or a series.
const tsCandle = (endSec, bid, ask) => candle(endSec, bid, ask);
gates.TS1 = () => {
  const C = 1800000000;
  const yes = (e) => tsCandle(e, 0.89, 0.91), mid = (e) => tsCandle(e, 0.5, 0.52), noSide = (e) => tsCandle(e, 0.05, 0.07);
  const a = live.twoStageFromCandles([yes(C - 600), mid(C - 480), noSide(C - 360)], C);
  assert.deepStrictEqual([a.ask10, a.side10, a.inBand10, a.ask8, a.side8, a.inBand8, a.ask6, a.side6, a.inBand6, a.twoStageLeft],
    [0.91, 'yes', true, null, null, false, 0.95, 'no', true, 600], 'the favourite side and its price at each look, and the earliest look in band');
  const b = live.twoStageFromCandles([mid(C - 480), noSide(C - 360)], C);
  assert.deepStrictEqual([b.ask10, b.side10, b.inBand10, b.inBand8, b.inBand6, b.twoStageLeft], [null, null, null, false, true, 360], 'a missing 10 minute candle is no value (null), not "not in band", and the earliest in band is 6 minutes');
  assert.strictEqual(live.twoStageFromCandles([yes(C - 540), yes(C - 420)], C), null, 'a neighbouring candle is never substituted: no exact candle, nothing logged');
  assert.strictEqual(live.twoStageFromCandles([], C), null); assert.strictEqual(live.twoStageFromCandles([yes(C - 600)], NaN), null);
  const none = live.twoStageFromCandles([mid(C - 600), mid(C - 480), mid(C - 360)], C);
  assert.ok(none.inBand10 === false && none.inBand8 === false && none.inBand6 === false && none.twoStageLeft === null, 'candles present but never in band: twoStageLeft is null');
  const edge = live.twoStageFromCandles([tsCandle(C - 600, 0.87, 0.88), tsCandle(C - 480, 0.02, 0.03)], C);
  assert.deepStrictEqual([edge.side10, edge.ask10, edge.side8, edge.inBand8], ['yes', 0.88, null, false], 'the band is 0.88 to 0.97 inclusive, judged on the real price: a YES at 0.88 is in, a NO at 0.98 is out');
};
gates.TS2 = async () => {
  const closeSec = (NOW + 360000) / 1000;
  const cs = [candle(closeSec - 600, 0.89, 0.91), candle(closeSec - 480, 0.90, 0.92), candle(closeSec - 360, 0.91, 0.93)];
  const withLog = world({ session: { active: true, ordersSent: 0, startCash: 100 }, candles: cs });
  await tick(withLog, { quotes: [quote({}, 'KXDOGE15M', 'KXDOGE15M-26OCT071415-06')] });
  const without = world({ session: { active: true, ordersSent: 0, startCash: 100 }, candles: 'none' });
  await tick(without, { quotes: [quote({}, 'KXDOGE15M', 'KXDOGE15M-26OCT071415-06')] });
  assert.strictEqual(withLog.posts.length, 1);
  assert.deepStrictEqual(withLog.posts, without.posts, 'the order sent is byte for byte the same with or without the log');
  const rec = withLog.docs.get('L1-KXDOGE15M-26OCT071415-06');
  assert.deepStrictEqual([rec.ask10, rec.side10, rec.inBand10, rec.ask8, rec.inBand8, rec.ask6, rec.inBand6, rec.twoStageLeft], [0.91, 'yes', true, 0.92, true, 0.93, true, 600], 'the order record carries the three looks and the earliest in band');
  assert.strictEqual(without.docs.get('L1-KXDOGE15M-26OCT071415-06').twoStageLeft, undefined, 'no candles, nothing logged, the order is as it was');
};
gates.TS3 = async () => {
  // A 10 minute order (XRP) has no 8 or 6 minute candle yet: only the 10 minute look is written.
  const closeSec = (NOW + 600000) / 1000;
  const cs = [candle(closeSec - 600, 0.89, 0.91)];
  const w = world({ session: { active: true, ordersSent: 0, startCash: 100 }, fresh: { [XRP10]: { close_time: iso(NOW + 600000) } }, candles: cs });
  await tick(w, { quotes: [q10('KXXRP15M', XRP10)] });
  const rec = w.docs.get('L1-' + XRP10);
  assert.deepStrictEqual([rec.ask10, rec.inBand10, rec.ask8, rec.inBand8, rec.inBand6, rec.twoStageLeft], [0.91, true, null, null, null, 600], 'only the look that exists is written; later looks are null, not "not in band"');
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.strictEqual((src.match(/twoStageFromCandles\(/g) || []).length, 2, 'it is defined once and called once, in logRise, after the orders: nothing that decides an order reads it');
  assert.ok(!/keyId|pem/.test(src.slice(src.indexOf('function twoStageFromCandles'), src.indexOf('async function logRise'))), 'public candles only, no key');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();

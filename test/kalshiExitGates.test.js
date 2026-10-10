// The exit watch (functions/kalshiLiveLib.js, runExitWatch): it sells the bot's OWN open L1 positions when the side's bid falls to 70c, only when switched to "sell". Plain node, no framework.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib.js');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const NOW = Date.parse('2026-10-09T20:00:00Z');
const iso = (ms) => new Date(ms).toISOString();
const libSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8');
const idxSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');

// A fake exchange: markets with a yes bid and ask, a positions endpoint, an order endpoint. Every request is recorded.
function world(o = {}) {
  const docs = new Map(), events = [], calls = [], posts = [], sess = { active: true };
  const mk = (id, over) => docs.set(id, Object.assign({ strategy: 'L1', ticker: 'KXBTC15M-T1', series: 'KXBTC15M', side: 'yes', count: 20, fillCount: '20', maxCost: 18.7, addonCost: 7.5, price: 0.93, status: 'filled', ts: NOW - 300000, settled: false }, over));
  const store = {
    async recentFilled(since) { return [...docs.entries()].filter(([, d]) => d.status === 'filled' && d.ts >= since).map(([id, d]) => ({ id, ...d })); },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
    async claimExit(id, tries) { const d = docs.get(id); if (d.exitStatus === 'sending' || (Number(d.exitTries) || 0) !== tries || d.settled === true) return false; d.exitStatus = 'sending'; d.exitTries = tries + 1; return true; },
  };
  const market = Object.assign({ status: 'active', close_time: iso(NOW + 200000), yes_bid_dollars: '0.6900', yes_ask_dollars: '0.7100', exchange_index: 2 }, o.market || {});
  const fetchFn = async (url, init) => {
    calls.push({ url, method: init.method, body: init.body ? JSON.parse(init.body) : null });
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/portfolio/positions')) return reply(o.posStatus || 200, { market_positions: o.positions === undefined ? [{ ticker: 'KXBTC15M-T1', position_fp: '20.00' }] : o.positions });
    if (url.includes('/markets/')) return reply(o.marketStatus || 200, { market });
    if (init.method === 'POST') {
      posts.push(JSON.parse(init.body));
      if (o.post) return reply(o.post.status, o.post.body);
      return reply(201, { order_id: 'x-' + posts.length, fill_count: o.fill !== undefined ? o.fill : '20.00', remaining_count: '0.00', average_fill_price: o.avg || '0.6900' });
    }
    throw new Error('unexpected ' + init.method + ' ' + url);
  };
  return { docs, events, calls, posts, sess, store, fetchFn, mk,
    run: (extra = {}) => live.runExitWatch(Object.assign({ mode: 'sell', store, fetchFn, keyId: 'k', pem, now: NOW, enabled: true, setSession: async (p) => Object.assign(sess, p), logEvent: async (e) => events.push(e) }, extra)) };
}

const gates = {};

// E1: it can only ever close an existing long. Structural: its one order endpoint is the same events/orders path, its body builder takes a count of the position and a limit, and nothing in it can build a buy of a new position.
gates.E1 = () => {
  const code = libSrc.slice(libSrc.indexOf('const EXIT_THRESHOLD'), libSrc.indexOf('// ---- Flatten: the owner')).replace(/\/\/.*$/gm, '');
  assert.strictEqual((code.match(/method: "POST"/g) || []).length, 1, 'one place sends an order');
  assert.ok(/\/portfolio\/positions/.test(code) && code.indexOf('/portfolio/positions') < code.indexOf('method: "POST"'), 'the position is read before anything is sent');
  assert.ok(!/liveOrderBody|l1Count|runL1Tick/.test(code), 'it shares nothing with the buying path');
  assert.deepStrictEqual(live.EXIT_MODES, ['off', 'log', 'sell']);
  assert.strictEqual(live.EXIT_THRESHOLD, 0.70);
  const yes = live.exitBody('T', 'yes', 20, 0.54, 'X-T-1', 2), no = live.exitBody('T', 'no', 20, 0.46, 'X-T-1', 2);
  assert.deepStrictEqual([yes.side, no.side], ['ask', 'bid'], 'a long YES is closed by selling YES, a long NO by buying YES back');
  assert.deepStrictEqual([yes.time_in_force, yes.count, yes.exchange_index], ['immediate_or_cancel', '20', 2]);
  assert.throws(() => live.exitBody('T', 'yes', 0, 0.5, 'c'), /refusing/); assert.throws(() => live.exitBody('T', 'yes', 51, 0.5, 'c'), /refusing/); assert.throws(() => live.exitBody('T', 'yes', 5, 1.2, 'c'), /refusing/);
};

// E2: off does nothing; log records that it WOULD have sold, once, and sends nothing; sell without the live switch behaves as log.
gates.E2 = async () => {
  const off = world(); off.mk('L1-KXBTC15M-T1'); await off.run({ mode: 'off' });
  assert.strictEqual(off.calls.length, 0, 'off makes no request at all');
  const lg = world(); lg.mk('L1-KXBTC15M-T1'); await lg.run({ mode: 'log' }); await lg.run({ mode: 'log' });
  const d = lg.docs.get('L1-KXBTC15M-T1');
  assert.ok(d.exitShadow && d.exitShadow.bid === 0.69 && d.exitShadow.wouldSell === 20, 'it records the bid and the size it would have sold');
  assert.strictEqual(lg.posts.length, 0, 'and sends nothing');
  assert.strictEqual(lg.calls.filter((c) => c.url.includes('/portfolio/')).length, 0, 'log mode never touches the account at all');
  assert.strictEqual(lg.events.filter((e) => e.kind === 'exit (log only)').length, 1, 'logged once per order');
  const sw = world(); sw.mk('L1-KXBTC15M-T1'); await sw.run({ mode: 'sell', enabled: false });
  assert.strictEqual(sw.posts.length, 0, 'sell with the live switch off sends nothing');
  assert.ok(sw.docs.get('L1-KXBTC15M-T1').exitShadow, 'it logs instead');
};

// E3: a bid above 70c does nothing; 70c itself triggers; a closed market, a crossed book and an empty bid do nothing.
gates.E3 = async () => {
  const up = world({ market: { yes_bid_dollars: '0.7100', yes_ask_dollars: '0.7300' } }); up.mk('L1-KXBTC15M-T1'); await up.run(); assert.strictEqual(up.posts.length, 0, '71c is not a trigger');
  const at = world({ market: { yes_bid_dollars: '0.7000', yes_ask_dollars: '0.7200' } }); at.mk('L1-KXBTC15M-T1'); await at.run(); assert.strictEqual(at.posts.length, 1, '70c is');
  const closed = world({ market: { status: 'closed' } }); closed.mk('L1-KXBTC15M-T1'); await closed.run(); assert.strictEqual(closed.posts.length, 0, 'a market that is no longer open settles on its own');
  const crossed = world({ market: { yes_bid_dollars: '0.6000', yes_ask_dollars: '0.5000' } }); crossed.mk('L1-KXBTC15M-T1'); await crossed.run(); assert.strictEqual(crossed.posts.length, 0, 'a crossed book is no quote');
  const empty = world({ market: { yes_bid_dollars: '0.0000', yes_ask_dollars: '0.0100' } }); empty.mk('L1-KXBTC15M-T1'); await empty.run(); assert.strictEqual(empty.posts.length, 0, 'nothing bid is nothing to sell into');
};

// E4: the sell is the right order for the position, sized to the order, and the record shows a realised result the loss stop and the pool can use.
gates.E4 = async () => {
  const w = world(); w.mk('L1-KXBTC15M-T1'); await w.run();
  assert.strictEqual(w.posts.length, 1);
  const b = w.posts[0];
  assert.deepStrictEqual([b.side, b.count, b.time_in_force, b.client_order_id, b.ticker], ['ask', '20', 'immediate_or_cancel', 'X-KXBTC15M-T1-1', 'KXBTC15M-T1']);
  assert.strictEqual(b.price, '0.54', 'a floor 15c under the bid it saw, so a collapsing book is not sold into at 1c');
  const d = w.docs.get('L1-KXBTC15M-T1');
  assert.deepStrictEqual([d.exitStatus, d.settled, d.result, d.exitCount], ['sold', true, 'exit', 20]);
  const want = 20 * 0.69 - require('../functions/kalshiSignalLib.js').takerFee(0.69, 20) - 18.7;
  assert.ok(Math.abs(d.settledPnl - want) < 0.001, 'realised pnl = proceeds after the fee minus the order cost: ' + d.settledPnl + ' vs ' + want.toFixed(4));
  assert.ok(d.settledPnl < 0 && d.settledPnl > -18.7, 'a saved loss, smaller than holding it');
  assert.ok(w.events.some((e) => e.kind === 'exit'));
  // NO side: closed by a YES buy at a ceiling 15c over the yes ask; our NO bid is one minus the yes ask
  const n = world({ market: { yes_bid_dollars: '0.2900', yes_ask_dollars: '0.3100' }, positions: [{ ticker: 'KXBTC15M-T1', position_fp: '-20.00' }], avg: '0.3100' });
  n.mk('L1-KXBTC15M-T1', { side: 'no' }); await n.run();
  assert.deepStrictEqual([n.posts[0].side, n.posts[0].price, n.posts[0].count], ['bid', '0.46', '20'], 'NO: buy YES back, ceiling 46c');
  assert.ok(Math.abs(n.docs.get('L1-KXBTC15M-T1').exitAvg - 0.69) < 1e-9, 'the NO sale price is one minus the YES price paid');
};

// E5: never more than the account holds, never when it holds nothing, and never a position that is not the bot's own record.
gates.E5 = async () => {
  const less = world({ positions: [{ ticker: 'KXBTC15M-T1', position_fp: '12.00' }] }); less.mk('L1-KXBTC15M-T1'); await less.run();
  assert.strictEqual(less.posts[0].count, '12', 'sells only what the account holds');
  const none = world({ positions: [] }); none.mk('L1-KXBTC15M-T1'); await none.run();
  assert.strictEqual(none.posts.length, 0, 'a position that is gone is not sold (a YES sell would open the opposite one)');
  assert.strictEqual(none.docs.get('L1-KXBTC15M-T1').exitStatus, 'skipped');
  const wrongway = world({ positions: [{ ticker: 'KXBTC15M-T1', position_fp: '-20.00' }] }); wrongway.mk('L1-KXBTC15M-T1'); await wrongway.run();
  assert.strictEqual(wrongway.posts.length, 0, 'a long NO is not closed by a YES sell');
  const unread = world({ posStatus: 500 }); unread.mk('L1-KXBTC15M-T1'); await unread.run();
  assert.strictEqual(unread.posts.length, 0, 'an unreadable position is nothing sold');
  const manual = world(); manual.mk('MANUAL-1', { strategy: undefined, ticker: 'KXBTC15M-T2' }); manual.mk('L1-KXBTC15M-T3', { ticker: 'KXBTC15M-T3', strategy: 'L1', ts: NOW - 40 * 60000 });
  await manual.run();
  assert.strictEqual(manual.posts.length, 0, 'a document that is not an L1 order, or is older than the lookback, is never touched');
};

// E6: two instances never send the same sell, and an answer that came back is never sent again.
gates.E6 = async () => {
  const w = world(); w.mk('L1-KXBTC15M-T1');
  await Promise.all([w.run(), w.run()]);
  assert.strictEqual(w.posts.length, 1, 'the sell is claimed atomically: one instance sends it');
  await w.run();
  assert.strictEqual(w.posts.length, 1, 'a sold order is not sold again');
};

// E7: a lost answer is never retried and ends the bot's session; a refusal is recorded and retried at most three times; a 409 is flagged for the owner.
gates.E7 = async () => {
  const lost = world({ post: { status: 502, body: 'bad gateway' } }); lost.mk('L1-KXBTC15M-T1');
  const r = await lost.run();
  assert.strictEqual(r.ended, true); assert.strictEqual(lost.sess.active, false); assert.strictEqual(lost.sess.endedBecause, 'attempted');
  assert.strictEqual(lost.docs.get('L1-KXBTC15M-T1').exitStatus, 'unknown');
  assert.ok(lost.events.some((e) => e.kind === 'session ended' && /MAY OR MAY NOT/.test(e.detail)));
  await lost.run(); assert.strictEqual(lost.posts.length, 1, 'nothing was retried');
  const refused = world({ post: { status: 400, body: { error: 'bad' } } }); refused.mk('L1-KXBTC15M-T1');
  await refused.run(); await refused.run(); await refused.run(); await refused.run();
  assert.strictEqual(refused.posts.length, 3, 'at most three tries');
  assert.deepStrictEqual(refused.posts.map((p) => p.client_order_id), ['X-KXBTC15M-T1-1', 'X-KXBTC15M-T1-2', 'X-KXBTC15M-T1-3'], 'each try has its own id');
  const dup = world({ post: { status: 409, body: {} } }); dup.mk('L1-KXBTC15M-T1'); await dup.run();
  assert.strictEqual(dup.docs.get('L1-KXBTC15M-T1').exitStatus, 'unknown');
};

// E8: a partial fill keeps the rest held and sells it on the next look; settlement then counts the contracts still held at the close.
gates.E8 = async () => {
  const w = world({ fill: '8.00' }); w.mk('L1-KXBTC15M-T1');
  await w.run();
  let d = w.docs.get('L1-KXBTC15M-T1');
  assert.deepStrictEqual([d.exitStatus, d.exitCount, d.settled], ['partly sold', 8, false], 'a partial exit is not settled');
  assert.strictEqual(w.posts[0].count, '20');
  // the same order, settled by the market's result with 12 contracts still held: YES won
  const f = live.settledFields(d, 'yes');
  assert.ok(Math.abs(f.settledPnl - (12 + d.exitProceeds - 18.7)) < 1e-3, 'the held contracts pay $1 and the proceeds of the sale are added');
  const lostIt = live.settledFields(d, 'no');
  assert.ok(Math.abs(lostIt.settledPnl - (d.exitProceeds - 18.7)) < 1e-3);
  // an order with no exit settles exactly as it always did
  assert.strictEqual(live.settledFields({ side: 'yes', maxCost: 18.7, count: 20, fillCount: '20' }, 'yes').settledPnl, Number((20 - 18.7).toFixed(4)));
};

// E9: the loss stop and the pool read an exited order as a realised loss, not as an open order counted at its full cost.
gates.E9 = async () => {
  const w = world(); w.mk('L1-KXBTC15M-T1'); await w.run();
  const orders = [...w.docs.entries()].map(([id, d]) => ({ id, ...d }));
  const risk = await live.botRisk({ store: { sessionTrades: async () => orders, updateTest: async () => {} }, since: 0, fetchFn: async () => { throw new Error('no network needed for a settled record'); }, nowMs: NOW });
  const pnl = w.docs.get('L1-KXBTC15M-T1').settledPnl;
  assert.ok(Math.abs(risk.net - pnl) < 1e-9 && risk.openCost === 0, 'the realised loss counts, nothing is left open');
  assert.ok(risk.addonAtRisk > 0 && risk.addonAtRisk < 7.5, 'the profit-funded share of a realised loss is allowed for, in proportion');
  const fold = live.foldSkim({ pool: 9.74, saved: 9.74, cum: 19.48, hwm: 19.48, appliedTs: 0 }, [{ ...w.docs.get('L1-KXBTC15M-T1'), id: 'a', ts: NOW - 300000, fillCount: '20' }]);
  assert.ok(fold.pool < 9.74 && fold.pool >= 0, 'a realised loss comes out of the pool first');
};

// E10: the page's switch, the session and the scheduled function.
gates.E10 = () => {
  const fn = idxSrc.slice(idxSrc.indexOf('exports.kalshiLiveExit = onSchedule('), idxSrc.indexOf('exports.kalshiLiveArmed = onSchedule('));
  assert.ok(/secrets: \[KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY\]/.test(fn) && /runExitWatch/.test(fn), 'the only function that can sell is declared with the key');
  assert.ok(/exitMode/.test(fn) && /"log"/.test(fn), 'it reads the switch from the session, default log');
  const setter = idxSrc.slice(idxSrc.indexOf('exports.kalshiExitMode = onCall'), idxSrc.indexOf('exports.kalshiL1Session = onCall'));
  assert.ok(/assertKalshiAdmin/.test(setter) && /EXIT_MODES/.test(setter) && /HttpsError/.test(setter), 'admin only, and only the three named modes');
  assert.ok(idxSrc.indexOf('exports.kalshiLiveExit') < idxSrc.indexOf('exports.kalshiBookRecorder'), 'the recorder stays last');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();

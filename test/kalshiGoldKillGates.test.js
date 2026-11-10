// Gold L1 kill latch (the owner, Nov 10, 2026; docs/GOLD_KILL_LATCH.md). Each gate states a consequence for the account, not a mechanism.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib');
const gk = require('../functions/kalshiGoldKillLib');
const root = path.join(__dirname, '..');
const NOW = Date.parse('2026-11-12T14:00:00Z');
const iso = (ms) => new Date(ms).toISOString();
const pem = crypto.generateKeyPairSync('ed25519').privateKey.export({ type: 'pkcs8', format: 'pem' });
const R = gk.GOLD_KILL.rearmAt;
const BASE = 979.25, LIMIT = 0.06 * BASE;   // 58.755
const gates = {};

let n = 0;
// A settled gold order that made `pnl` dollars. A loss is an early sell with a stored settledPnl; a win settles at the close on the cash basis (0.92 fill + 0.01 fee, 10 contracts: +0.70).
const loss = (pnl, ts) => ({ id: 'o' + (++n), strategy: 'L1', series: 'KXGOLD15M', ticker: 'KXGOLD15M-26NOV121500-00', ts, fillCount: 10, count: 10, maxCost: 9.5, side: 'yes', settled: true, result: 'exit', settledPnl: pnl });
const win = (ts) => ({ id: 'o' + (++n), strategy: 'L1', series: 'KXGOLD15M', ticker: 'KXGOLD15M-26NOV121500-00', ts, fillCount: 10, count: 10, maxCost: 9.5, side: 'yes', settled: true, result: 'yes', averageFillPrice: '0.9200', averageFeePaid: '0.0100' });
const at = (i) => R + 3600000 + i * 900000;

function checker(orders, sizing) {
  const wrote = [], events = [], state = { sizing: sizing === undefined ? { base: BASE } : sizing };
  return {
    wrote, events, state,
    io: {
      now: NOW, readOrders: async () => orders, readSizing: async () => state.sizing,
      writeGoldKill: async (p) => { wrote.push(p); state.sizing = { ...(state.sizing || {}), goldKill: { ...((state.sizing && state.sizing.goldKill) || {}), ...p } }; },
      logEvent: async (e) => { events.push(e); },
    },
  };
}

// K1: a drawdown of 6% of the base from gold's own peak latches gold off; one cent short of it does not.
gates.K1 = async () => {
  const short = [win(at(0)), loss(-(LIMIT - 0.01), at(1))];   // peak +0.70 after the win, then down by just under the line from that peak
  const a = checker(short);
  const ra = await gk.runGoldKillCheck(a.io);
  assert.ok(!ra.tripped && !gk.goldKillActive(a.state.sizing, 'KXGOLD15M'), 'just under the line: still trading');
  const over = [win(at(0)), loss(-(LIMIT + 0.01), at(1))];
  const b = checker(over);
  const rb = await gk.runGoldKillCheck(b.io);
  assert.strictEqual(rb.tripped, 'drawdown');
  assert.ok(gk.goldKillActive(b.state.sizing, 'KXGOLD15M'), 'the latch is on the sizing document the tick reads');
  assert.ok(b.events.some((e) => e.kind === 'gold kill'), 'and the owner is told');
};

// K2: the net rule needs 40 trades. 39 trades down $21 trips nothing; the 40th does.
gates.K2 = async () => {
  const mk = (k) => Array.from({ length: k }, (_, i) => loss(-0.55, at(i)));   // each far inside the drawdown line, together past -$20
  const a = checker(mk(39));
  assert.ok(!(await gk.runGoldKillCheck(a.io)).tripped, '39 trades: not yet');
  const b = checker(mk(40));
  assert.strictEqual((await gk.runGoldKillCheck(b.io)).tripped, 'net');
};

// K3: a win after the trip does not un-kill, in the replay and in the stored record.
gates.K3 = async () => {
  const rows = [loss(-(LIMIT + 1), at(0))];
  for (let i = 1; i <= 120; i++) rows.push(win(at(i)));   // +84 dollars of wins afterwards: net positive, drawdown gone
  const w = checker(rows);
  const first = await gk.runGoldKillCheck(w.io);
  assert.strictEqual(first.tripped, 'drawdown');
  assert.ok(gk.evaluateGold({ orders: rows, base: BASE }).trip, 'the replay stays tripped');
  await gk.runGoldKillCheck(w.io);   // later minutes
  assert.ok(gk.goldKillActive(w.state.sizing, 'KXGOLD15M'));
  assert.ok(w.wrote.every((p) => p.tripped !== false), 'nothing ever writes the latch off');
  // even if the base later grows so the replay alone would not trip, the stored latch holds
  const w2 = checker([loss(-1, at(0))], { base: BASE, goldKill: { tripped: true, rearmAt: R } });
  await gk.runGoldKillCheck(w2.io);
  assert.ok(gk.goldKillActive(w2.state.sizing, 'KXGOLD15M'));
};

// K4: only a later re-arm date re-arms. A latch from an older generation is ignored; trades before the new date count for nothing.
gates.K4 = async () => {
  const stored = { base: BASE, goldKill: { tripped: true, rearmAt: R } };
  assert.ok(gk.goldKillActive(stored, 'KXGOLD15M'));
  const later = Object.freeze({ ...gk.GOLD_KILL, rearmAt: R + 7 * 86400000 });
  assert.ok(!gk.goldKillActive(stored, 'KXGOLD15M', later), 'a code edit that moves the date past the latch re-arms it');
  const rows = [loss(-(LIMIT + 5), at(0))];   // before the new date
  const ev = gk.evaluateGold({ orders: rows, base: BASE, cfg: later });
  assert.strictEqual(ev.trip, null, 'old trades no longer count');
  const w = checker(rows, stored);
  const r = await gk.runGoldKillCheck(w.io, later);
  assert.ok(!r.killed && w.wrote.some((p) => p.tripped === false && p.rearmAt === later.rearmAt), 'the new generation is recorded as not tripped');
  // nothing on the sizing document can set the date back: a stored date older than the code's is ignored
  assert.ok(!gk.goldKillActive({ goldKill: { tripped: true, rearmAt: R - 1 } }, 'KXGOLD15M'));
};

// K5: the tick places no gold order while latched and does when it is not; the other series are untouched by it.
const TICKER = 'KXGOLD15M-26NOV121415-06';
const sess = () => ({ active: true, until: NOW + 3600000, ordersSent: 0, startCash: 100, sizing: true, sizeCap: 15, sizeAddon: 0, sizeBase: 1000, sizeNextReview: NOW + 86400000 });
const state = { cap: 15, base: 1000, reviewedAt: NOW - 1000, pool: 0, saved: 0, appliedTs: NOW - 1000, lastStopAt: null };
function world() {
  const posts = [], docs = new Map(), notes = [], s = sess();
  const store = {
    async halted() { return false; }, async hasUnresolved() { return false; },
    async createTest(id, d) { docs.set(id, { ...d }); return true; }, async updateTest(id, p) { Object.assign(docs.get(id), p); },
    async sessionTrades(since) { return [...docs.entries()].filter(([, d]) => d.ts >= since).map(([id, d]) => ({ id, ...d })); },
  };
  const fetchFn = async (url, o) => {
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/candlesticks')) return reply(200, { candlesticks: [] });
    if (url.includes('/markets/')) return reply(200, { market: { status: 'active', close_time: iso(NOW + 360000), exchange_index: 2, yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' } });
    if (url.endsWith('/portfolio/balance')) return reply(200, { balance_breakdown: [{ balance: '1000.0000', exchange_index: 2 }, { balance: '1000.0000', exchange_index: 0 }] });
    if (url.includes('/portfolio/orders')) return reply(200, { orders: [] });
    if (url.includes('/portfolio/fills')) return reply(200, { fills: [] });
    if (o.method === 'POST') { posts.push(JSON.parse(o.body)); return reply(201, { order_id: 'x', fill_count: '1.00', remaining_count: '0.00', average_fill_price: '0.9100', average_fee_paid: '0.0057' }); }
    throw new Error('unexpected ' + url);
  };
  return { posts, docs, store, fetchFn, sess: s, notes };
}
const tick = (w, sizingState) => live.runL1Tick({
  session: w.sess, now: NOW, setSession: async (p) => { Object.assign(w.sess, p); w.notes.push(p.lastNote); }, quotes: [{ series: 'KXGOLD15M', m: { ticker: TICKER, status: 'active', close_time: iso(NOW + 360000), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' } }],
  active: true, enabled: true, store: w.store, keyId: 'k', pem, fetchFn: w.fetchFn, sizingState, setSizingState: async () => {},
});
gates.K5 = async () => {
  const free = world(); await tick(free, state);
  assert.strictEqual(free.posts.length, 1, 'unlatched gold trades');
  const latched = world(); const r = await tick(latched, { ...state, goldKill: { tripped: true, rearmAt: R } });
  assert.strictEqual(latched.posts.length, 0, 'latched gold sends nothing');
  assert.ok(/kill latch/.test(latched.notes.join(' ')), 'and the bot says why');
  assert.strictEqual(r.skipped, 'no market in the window');
  // only gold is affected: the latch does nothing for any other series name
  for (const s of live.L1_SERIES.filter((x) => x !== 'KXGOLD15M')) assert.ok(!gk.goldKillActive({ goldKill: { tripped: true, rearmAt: R } }, s));
};

// K6: alerts never block an order or write a latch.
gates.K6 = async () => {
  const rows = [];
  // Trades from the 30 days BEFORE the re-arm date: alerts read them (they only inform), the kill does not count them.
  for (let i = 0; i < 100; i++) rows.push(i % 2 === 0 ? loss(-1.2, R - 86400000 + i * 60000) : win(R - 86400000 + i * 60000));   // PF 0.58 over the last 60 and 50 early sells
  const w = checker(rows);
  const r = await gk.runGoldKillCheck(w.io);
  assert.ok(!r.tripped, 'an alert is not a kill');
  assert.ok(r.alerts.includes('pf60') && r.alerts.includes('early'), 'the weak run and the early sells both alert');
  assert.deepStrictEqual(w.events.map((e) => e.kind), r.alerts.map(() => 'gold alert'));
  assert.ok(!gk.goldKillActive(w.state.sizing, 'KXGOLD15M'));
  const again = await gk.runGoldKillCheck(w.io);
  assert.strictEqual(w.events.length, r.alerts.length, 'an alert that is still on is not repeated every minute');
  assert.ok(!again.tripped);
  const t = world(); await tick(t, { ...state, goldKill: { tripped: false, rearmAt: R, alerts: { pf60: true, pf100: true, early: true } } });
  assert.strictEqual(t.posts.length, 1, 'with every alert on, gold still trades');
};

// K7: the exit watch still sells an open gold position, whatever the latch says. It takes no sizing document and does not name the latch.
gates.K7 = async () => {
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  const code = src.slice(src.indexOf('async function runExitWatch'), src.indexOf('async function flattenAll')).replace(/\/\/.*$/gm, '');
  assert.ok(!/goldKill|sizingState/.test(code), 'the exit watch never looks at the latch');
  const docs = new Map(), posts = [];
  docs.set('g1', { strategy: 'L1', ticker: 'KXGOLD15M-T1', series: 'KXGOLD15M', side: 'yes', count: 10, fillCount: '10', maxCost: 9.3, addonCost: 0, price: 0.93, status: 'filled', ts: NOW - 300000, settled: false });
  const store = {
    async recentFilled(since) { return [...docs.entries()].filter(([, d]) => d.status === 'filled' && d.ts >= since).map(([id, d]) => ({ id, ...d })); },
    async updateTest(id, p) { Object.assign(docs.get(id), p); },
    async claimClose() { return true; },
    async claimExit(id, tries) { const d = docs.get(id); if (d.exitStatus === 'sending' || (Number(d.exitTries) || 0) !== tries || d.settled === true) return false; d.exitStatus = 'sending'; d.exitTries = tries + 1; return true; },
  };
  const fetchFn = async (url, init) => {
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [{ ticker: 'KXGOLD15M-T1', position_fp: '10.00' }] });
    if (url.includes('/markets/')) return reply(200, { market: { status: 'active', close_time: iso(NOW + 200000), yes_bid_dollars: '0.2400', yes_ask_dollars: '0.2600', exchange_index: 2 } });
    if (init.method === 'POST') { posts.push(JSON.parse(init.body)); return reply(201, { order_id: 'x', fill_count: '10.00', remaining_count: '0.00', average_fill_price: '0.2400' }); }
    throw new Error('unexpected ' + url);
  };
  await live.runExitWatch({ store, fetchFn, keyId: 'k', pem, now: NOW, enabled: true, setSession: async () => {}, logEvent: async () => {} });
  assert.strictEqual(posts.length, 1, 'the open gold position is sold at the line');
};

// K8: the verdict is cash basis. A win at the close is re-derived from the real fill and fee, not the limit booking; an early sell keeps its stored figure; other series and hand-closed orders are ignored.
gates.K8 = () => {
  const w = gk.goldResult(win(at(0)));
  assert.ok(Math.abs(w.pnl - 0.7) < 1e-9, 'cash: 10 x (1 - 0.92 - 0.01) = 0.70, not the 0.5 the 9.5 limit booking would give');
  assert.strictEqual(gk.goldResult(loss(-3.21, at(0))).pnl, -3.21);
  assert.strictEqual(gk.goldResult({ ...win(at(0)), series: 'KXBTC15M' }), null);
  assert.strictEqual(gk.goldResult({ ...win(at(0)), result: 'hand' }), null);
  assert.strictEqual(gk.goldResult({ ...win(at(0)), settled: false }), null, 'an open order is not a result');
  assert.strictEqual(gk.goldResult({ ...win(at(0)), fillCount: 0 }), null);
};

// K9: nothing stored or typed loosens it. A stored "not tripped" does not stop a replay from tripping; a failed read changes nothing; the exports offer no way to clear it.
gates.K9 = async () => {
  const w = checker([win(at(0)), loss(-(LIMIT + 1), at(1))], { base: BASE, goldKill: { tripped: false, rearmAt: R } });
  assert.strictEqual((await gk.runGoldKillCheck(w.io)).tripped, 'drawdown');
  const bad = checker([], { base: BASE });
  bad.io.readOrders = async () => { throw new Error('down'); };
  assert.deepStrictEqual(await gk.runGoldKillCheck(bad.io), { skipped: 'unreadable' });
  assert.strictEqual(bad.wrote.length, 0);
  const failW = checker([loss(-(LIMIT + 1), at(0))]);
  failW.io.writeGoldKill = async () => { throw new Error('no'); };
  const r = await gk.runGoldKillCheck(failW.io);
  assert.strictEqual(r.skipped, 'unwritten'); assert.strictEqual(failW.events.length, 0, 'no event for a latch that was not written (the next minute tries again)');
  assert.ok(Object.isFrozen(gk.GOLD_KILL), 'the thresholds are frozen constants');
  const src = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8') + fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.ok(!/goldKill[^\n]*request\.data|request\.data[^\n]*goldKill/.test(src), 'no callable takes the latch from a caller');
};

// K10: the half size period only exists after a RE-ARM, only lowers a count, and ends after halfSizeFills trades.
gates.K10 = async () => {
  assert.ok(!gk.goldHalfSize({ goldKill: { rearmAt: R } }, 'KXGOLD15M'), 'the first arming is full size');
  const ret = Object.freeze({ ...gk.GOLD_KILL, rearmAt: R + 86400000, rearmIsReturn: true });
  assert.ok(gk.goldHalfSize(null, 'KXGOLD15M', ret), 'a return starts at half size even before the record exists');
  assert.ok(!gk.goldHalfSize(null, 'KXXRP15M', ret));
  const w = checker([win(at(2000))], { base: BASE });
  await gk.runGoldKillCheck(w.io, ret);
  assert.ok(w.wrote.some((p) => p.half === true), 'records half size while under 30 trades');
  const rows = Array.from({ length: 30 }, (_, i) => win(ret.rearmAt + 1000 + i * 1000));
  const w2 = checker(rows, { base: BASE, goldKill: { tripped: false, rearmAt: ret.rearmAt, half: true } });
  await gk.runGoldKillCheck(w2.io, ret);
  assert.strictEqual(w2.state.sizing.goldKill.half, false, 'after 30 trades full size');
  assert.ok(!gk.goldHalfSize(w2.state.sizing, 'KXGOLD15M', ret));
  assert.strictEqual(gk.GOLD_KILL.rearmIsReturn, false, 'the shipped config is the first arming, so the tick sizes gold as before');
  // the tick halves only through goldHalfSize, which is false for the shipped config whatever the stored record says
  assert.ok(!gk.goldHalfSize({ goldKill: { rearmAt: R, half: true } }, 'KXGOLD15M'));
};

// K11: the checker only reads orders and writes the sizing field and an event; it has no key and sends nothing to Kalshi.
gates.K11 = () => {
  const lib = fs.readFileSync(path.join(root, 'functions', 'kalshiGoldKillLib.js'), 'utf8').replace(/\/\/.*$/gm, '');
  assert.ok(!/fetch|keyId|pem|\/portfolio|method: "POST"|runL1Tick/.test(lib));
  const idx = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
  const fn = idx.slice(idx.indexOf('exports.kalshiGoldKillCheck'), idx.indexOf('exports.kalshiPaperTick'));
  assert.ok(!/KALSHI_LIVE_KEY_ID|KALSHI_LIVE_PRIVATE_KEY|secrets/.test(fn), 'no secret on the checker');
  assert.ok(/deploy-sizing|kalshiGoldKillCheck/.test(fs.readFileSync(path.join(root, 'functions', 'deploy-sizing.sh'), 'utf8')));
};

(async () => {
  let failed = 0;
  for (const [k, f] of Object.entries(gates)) { try { await f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + '\n' + (e && e.stack || e)); } }
  process.exit(failed ? 1 : 0);
})();

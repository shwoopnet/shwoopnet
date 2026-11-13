// Hard account stop (the owner, Nov 13, 2026; docs/HARD_ACCOUNT_STOP.md). Each gate states a consequence for the account. All figures are invented round numbers.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib');
const slotRun = require('../functions/kalshiSlotRunLib');
const push = require('../functions/kalshiPushLib');
const hs = require('../functions/kalshiHardStopLib');
const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const stripC = (s) => s.replace(/\/\/.*$/gm, '');
const NOW = Date.parse('2026-11-14T14:00:00Z');
const iso = (ms) => new Date(ms).toISOString();
const pem = crypto.generateKeyPairSync('ed25519').privateKey.export({ type: 'pkcs8', format: 'pem' });
const R = hs.HARD_STOP.rearmAt;
const BASE = 1000;   // invented sizing base; the line is 40% of it, $400
const at = (i) => R + 3600000 + i * 900000;
let n = 0;
const l1 = (pnl, ts) => ({ id: 'o' + (++n), strategy: 'L1', series: 'KXGOLD15M', ticker: 'KXGOLD15M-26NOV141500-00', ts, fillCount: 10, count: 10, maxCost: 9.5, side: 'yes', settled: true, result: 'exit', settledPnl: pnl });
const sl = (pnl, ts) => ({ id: 's' + (++n), strategy: 'SLOT', slotId: 'OICORE', series: 'KXBTC15M', ticker: 'KXBTC15M-26NOV141500-00', ts, fillCount: 10, count: 10, maxCost: 3, side: 'no', settled: true, result: 'exit', settledPnl: pnl });
const gates = {};

// A checker world: the sizing document is mutable so the effect of one minute is what the next minute sees.
function world(l1Orders, slotOrders, sizing) {
  const wrote = [], events = [], alerts = [], st = { sizing: sizing === undefined ? { base: BASE } : sizing, claim: null, state: null };
  const w = { wrote, events, alerts, st, l1Orders, slotOrders,
    io: {
      now: NOW, readL1Orders: async () => w.l1Orders, readSlotOrders: async () => w.slotOrders, readSizing: async () => st.sizing, readState: async () => st.state,
      writeState: async (p) => { st.state = { ...(st.state || {}), ...p }; },
      writeHardStop: async (p) => { wrote.push(p); st.sizing = { ...(st.sizing || {}), hardStop: { ...((st.sizing && st.sizing.hardStop) || {}), ...p } }; },
      claimAlert: async (rearmAt) => { if (st.claim === rearmAt) return false; st.claim = rearmAt; return true; },
      releaseAlert: async () => { st.claim = null; },
      raiseAlert: async (a) => { alerts.push(a); },
      logEvent: async (e) => { events.push(e); },
    } };
  return w;
}
const run = (w, extra) => hs.runHardStopCheck({ ...w.io, ...(extra || {}) });

// HS1: a deposit is not a gain and a withdrawal is not a loss. The balance is never read; only the bot's own results are, and the line is frozen at the base the account had at its best.
gates.HS1 = async () => {
  const orders = [l1(100, at(0)), l1(-300, at(1))];   // peak +100, now -200: down $300 from the peak, inside the $400 line
  const w = world(orders, [], { base: BASE });
  await run(w);
  assert.strictEqual(w.st.sizing.hardStop.peakBase, BASE);
  assert.strictEqual(w.st.sizing.hardStop.line, 400);
  // The account is then topped up: the sizing base doubles. The line must NOT move, and a $50 deposit of results is not a "new high".
  w.st.sizing.base = 2 * BASE; w.l1Orders = orders.concat([l1(-50, at(2))]); w.io.now += 600000;
  const r = await run(w);
  assert.ok(!r.killed && !hs.hardStopTripped(w.st.sizing), 'a deposit does not loosen the line (a $350 drop stays inside the frozen $400)');
  assert.strictEqual(w.st.sizing.hardStop.line, 400, 'the line is still 40% of the base at the peak');
  // A withdrawal halves the base: not a loss, so no trip, and the line does not shrink under the account.
  w.st.sizing.base = BASE / 2; w.io.now += 600000;
  assert.ok(!(await run(w)).killed, 'a withdrawal is not a loss');
  assert.ok(!/balance/i.test(stripC(read('functions', 'kalshiHardStopLib.js')).replace(/"[^"]*"/g, '')), 'the library never reads or names the account balance');
};

// HS2: 39.99% of the base does not trip and 40% does. Both strategies count, together.
gates.HS2 = async () => {
  const justUnder = world([l1(100, at(0)), l1(-399.99, at(1))], [], { base: BASE });   // the result peaks at +100, then falls 399.99 below that peak
  assert.ok(!(await run(justUnder)).killed, '399.99 of 1000 is under the line');
  const exact = world([l1(100, at(0)), l1(-400, at(1))], [], { base: BASE });
  assert.strictEqual((await run(exact)).tripped, 'drawdown', '400 of 1000 trips');
  const both = world([l1(100, at(0)), l1(-200, at(1))], [sl(-200, at(2))], { base: BASE });
  assert.strictEqual((await run(both)).tripped, 'drawdown', 'L1 alone is 200 down and the second slot alone is 200 down; together they are 400 below the peak');
  const l1Only = world([l1(100, at(0)), l1(-200, at(1))], [], { base: BASE });
  assert.ok(!(await run(l1Only)).killed, 'L1 alone at 200 is under the line');
  assert.ok(l1Only.events.length === 0);
};

// HS3: a tripped stop blocks L1 buys and slot buys, but never the exit watch.
const TICKER = 'KXGOLD15M-26NOV141415-06';
const state = { cap: 15, base: 1000, reviewedAt: NOW - 1000, pool: 0, saved: 0, appliedTs: NOW - 1000, lastStopAt: null };
function l1world() {
  const posts = [], docs = new Map(), notes = [];
  const sess = { active: true, until: NOW + 3600000, ordersSent: 0, startCash: 100, sizing: true, sizeCap: 15, sizeAddon: 0, sizeBase: 1000, sizeNextReview: NOW + 86400000 };
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
  return { posts, docs, store, fetchFn, sess, notes };
}
const tick = (w, sizingState) => live.runL1Tick({
  session: w.sess, now: NOW, setSession: async (p) => { Object.assign(w.sess, p); w.notes.push(p.lastNote); }, quotes: [{ series: 'KXGOLD15M', m: { ticker: TICKER, status: 'active', close_time: iso(NOW + 360000), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' } }],
  active: true, enabled: true, store: w.store, keyId: 'k', pem, fetchFn: w.fetchFn, sizingState, setSizingState: async () => {},
});
const okRec = { rearmAt: R, status: 'ok', tripped: false, checkedAt: NOW - 60000 };
gates.HS3 = async () => {
  const free = l1world(); await tick(free, { ...state, hardStop: okRec });
  assert.strictEqual(free.posts.length, 1, 'with a healthy record gold buys as before');
  const tripped = l1world(); const r = await tick(tripped, { ...state, hardStop: { ...okRec, tripped: true } });
  assert.strictEqual(tripped.posts.length, 0, 'a tripped stop sends no L1 buy');
  assert.strictEqual(r.skipped, 'hard stop');
  assert.ok(/hard account stop/.test(tripped.notes.join(' ')), 'and the bot says why');
  // the slot: entries are refused before any store access
  const touch = new Proxy({}, { get(_, k) { throw new Error('the slot touched ' + String(k)); } });
  const skips = [];
  const out = await slotRun.runSlotTick({ session: { active: true }, now: NOW, enabled: true, active: true, store: touch, keyId: 'k', pem, fetchFn: async () => { throw new Error('no request'); },
    quotes: [{ series: 'KXBTC15M', m: { ticker: 'KXBTC15M-26NOV141415-00', status: 'active', close_time: iso(NOW + 150000), yes_bid_dollars: '0.2000', yes_ask_dollars: '0.2200' } }],
    hardStopBlocked: true, recordSkip: async (d) => { skips.push(d); }, clock: () => NOW });
  assert.deepStrictEqual(out, { skipped: 'hard account stop' });
  assert.ok(skips.length === 1 && skips[0].reason === 'hard_stop', 'the slot logs why it did not enter');
  // exits are never gated: neither exit code names the stop
  const lv = read('functions', 'kalshiLiveLib.js');
  const watch = lv.slice(lv.indexOf('async function runExitWatch'), lv.indexOf('async function flattenAll'));
  assert.ok(!/hardStop/.test(watch), 'the L1 exit watch never looks at the stop');
  const sr = read('functions', 'kalshiSlotRunLib.js');
  const exits = sr.slice(sr.indexOf('async function runSlotExits'));
  assert.ok(!/hardStop/.test(exits), 'the slot exit and settle passes never look at the stop');
  const idx = read('functions', 'index.js');
  assert.ok(!/runSlotExits\([^)]*hardStop|runExitWatch\([^)]*hardStop/.test(idx));
};

// HS4: fail closed. What cannot be read blocks; only an absent field (never evaluated) does not.
gates.HS4 = async () => {
  assert.ok(hs.hardStopBlocks({ hardStop: { ...okRec, status: 'unreadable' } }, NOW).blocked, 'a record that says it could not read blocks');
  assert.ok(hs.hardStopBlocks({ hardStop: 'x' }, NOW).blocked, 'a record that is not an object blocks');
  assert.ok(hs.hardStopBlocks({ hardStop: { ...okRec, checkedAt: NOW - hs.HARD_STOP.staleMs - 1 } }, NOW).blocked, 'a silent checker blocks');
  assert.ok(hs.hardStopBlocks({ hardStop: { rearmAt: R, status: 'ok', tripped: false } }, NOW).blocked, 'a record with no heartbeat blocks');
  assert.ok(!hs.hardStopBlocks({ hardStop: okRec }, NOW).blocked, 'a fresh healthy record does not');
  assert.ok(hs.hardStopBlocks({ base: 1 }, NOW).blocked && hs.hardStopBlocks(null, NOW).blocked && hs.hardStopBlocks({ hardStop: null }, NOW).blocked, 'never evaluated, or the sizing document gone, after the start date: no new buys');
  assert.ok(hs.hardStopBlocks({ base: 1 }, NaN).blocked, 'an unreadable clock counts as after');
  assert.ok(!hs.hardStopBlocks({ base: 1 }, R - 1).blocked && !hs.hardStopBlocks(null, R - 1).blocked, 'before the start date an absent field does not block (the recorded October replays stay identical)');
  assert.ok(hs.hardStopBlocks({ hardStop: { ...okRec, rearmAt: R - 1, tripped: true } }, NOW).blocked, 'an older generation after the start date is not a free pass: the checker has not written this generation yet');
  assert.ok(!hs.hardStopBlocks({ hardStop: { ...okRec, rearmAt: R - 1, tripped: true } }, R - 1).blocked, 'and before the start date it is ignored');
  // The checker: unreadable orders, an unreadable sizing document, no base, an order that cannot be priced: all write "unreadable" and trip nothing.
  const cases = [
    ['orders', (w) => { w.io.readL1Orders = async () => { throw new Error('down'); }; }],
    ['slot orders', (w) => { w.io.readSlotOrders = async () => { throw new Error('down'); }; }],
    ['sizing', (w) => { w.io.readSizing = async () => { throw new Error('down'); }; }],
    ['not a list', (w) => { w.io.readL1Orders = async () => null; }],
    ['no base', (w) => { w.st.sizing = {}; }],
    ['unpriceable', (w) => { w.l1Orders = [{ ...l1(0, at(0)), result: 'yes', maxCost: undefined, settledPnl: null }]; }],
  ];
  for (const [name, mut] of cases) {
    const w = world([l1(1, at(0))], [], { base: BASE }); mut(w);
    const r = await run(w);
    assert.ok(!r.tripped, name + ': nothing trips on an unreadable input');
    assert.strictEqual(w.st.sizing && w.st.sizing.hardStop && w.st.sizing.hardStop.status, 'unreadable', name + ': recorded as unreadable');
    assert.ok(hs.hardStopBlocks(w.st.sizing, NOW).blocked, name + ': and that blocks new buys');
  }
  // the next good read puts it back to ok
  const w = world([l1(1, at(0))], [], { base: BASE, hardStop: { rearmAt: R, status: 'unreadable', checkedAt: NOW - 1 } });
  await run(w);
  assert.strictEqual(w.st.sizing.hardStop.status, 'ok');
  assert.ok(!hs.hardStopBlocks(w.st.sizing, NOW).blocked);
};

// HS5: once tripped it stays tripped. Recovery above the line does not clear it; only a reviewed edit that moves rearmAt does, and then the peak starts again from zero.
gates.HS5 = async () => {
  const w = world([l1(100, at(0)), l1(-500, at(1))], [], { base: BASE });
  await run(w);
  assert.ok(hs.hardStopTripped(w.st.sizing));
  w.l1Orders = w.l1Orders.concat([l1(900, at(2))]);   // a huge recovery: the result is now above its old peak
  w.io.now += 3600000;
  const r = await run(w);
  assert.ok(r.killed && hs.hardStopTripped(w.st.sizing), 'still tripped after a full recovery');
  assert.ok(!w.wrote.some((p) => p.tripped === false), 'the checker never writes a clear');
  const later = Object.freeze({ ...hs.HARD_STOP, rearmAt: R + 7 * 86400000 });
  assert.ok(!hs.hardStopTripped(w.st.sizing, later), 'a code edit that moves rearmAt re-arms it');
  const w2 = world(w.l1Orders, [], w.st.sizing);
  const r2 = await hs.runHardStopCheck({ ...w2.io }, later);
  assert.ok(!r2.killed && w2.st.sizing.hardStop.tripped === false && w2.st.sizing.hardStop.peakEquity === 0, 'the new generation starts from zero: old trades are history');
  // a stored date older than the code's never blocks by itself
  // a latch the tick's full sizing write erased is re-derived, while the result is still below the line
  const w3 = world([l1(100, at(0)), l1(-500, at(1))], [], { base: BASE });
  await run(w3);
  assert.strictEqual(w3.alerts.length, 1);
  w3.st.sizing = { base: BASE * 3 };   // the tick's full write erased the cache, with a base that has since tripled
  assert.ok(!hs.hardStopTripped(w3.st.sizing));
  const r3 = await run(w3);
  assert.ok(r3.killed && hs.hardStopTripped(w3.st.sizing), 'the cache is restored from the authoritative record, with the original peak base (a bigger base cannot loosen it)');
  assert.strictEqual(w3.alerts.length, 1, 'and no second alert');
  // even recovery in the same minute cannot lose the latch, because it lives in its own document
  w3.l1Orders = w3.l1Orders.concat([l1(5000, at(3))]); w3.st.sizing = { base: BASE }; w3.io.now += 60000;
  assert.ok((await run(w3)).killed && hs.hardStopTripped(w3.st.sizing));
};

// HS6: the line is a constant in range, and a bad edit can only make the stop stricter.
gates.HS6 = () => {
  assert.strictEqual(hs.HARD_STOP_FRACTION, 0.4);
  assert.ok(hs.validFraction(hs.HARD_STOP.fraction) && hs.HARD_STOP.fraction <= 0.4 && hs.HARD_STOP.fraction >= 0.2);
  assert.ok(Object.isFrozen(hs.HARD_STOP));
  for (const [x, want] of [[0.55, 0.4], [1, 0.4], [0.4, 0.4], [0.3, 0.3], [0.2, 0.2], [0.19, 0.2], [0, 0.2], [-1, 0.2], [NaN, 0.2], [undefined, 0.2], ['x', 0.2]]) {
    assert.strictEqual(hs.effectiveFraction({ fraction: x }), want, 'fraction ' + String(x));
    if (want !== x) assert.ok(!hs.validFraction(x));
  }
  // an out-of-range constant never loosens the replay: a 0.9 edit still trips at 40%
  const bad = Object.freeze({ ...hs.HARD_STOP, fraction: 0.9 });
  const ev = hs.replay([l1(-400, at(0))], bad);
  assert.ok(hs.judge({ ev, base: BASE, stored: null, cfg: bad }).trip);
};

// HS7: nothing on the page, in a callable or in the database rules can clear or loosen it.
gates.HS7 = () => {
  const html = read('index.html');
  assert.ok(!/[.'"]hardStop\b/.test(html), 'the page never reads or writes the hardStop field');
  const idx = stripC(read('functions', 'index.js'));
  const lines = idx.split('\n').filter((l) => /hardStop/i.test(l));
  assert.ok(!lines.some((l) => /request\.data|req\.body|req\.query/.test(l)), 'no callable or endpoint feeds it from a caller');
  const writers = lines.filter((l) => /writeHardStop|hardStop:/.test(l));
  assert.ok(writers.every((l) => /writeHardStop: \(patch\) => sizingRef\.set\(\{ hardStop: patch \}, \{ merge: true \}\)/.test(l)), 'its only writer is the checker, a merge');
  const rules = read('firestore.rules');
  const ctl = rules.slice(rules.indexOf('kalshiLiveControl'), rules.indexOf('kalshiLiveControl') + 400);
  assert.ok(/allow write: if false|allow create, update, delete: if false/.test(ctl) || !/allow (write|create|update)[^;]*request\.auth/.test(ctl), 'kalshiLiveControl has no client write');
  // the stored record cannot lower the line: judge takes the peak and base it computes, never a stored line
  assert.ok(!/stored\.line|stored\.fraction/.test(stripC(read('functions', 'kalshiHardStopLib.js'))));
};

// HS8: the checker holds no key and sends nothing to Kalshi; it is a scheduled function in the sizing deploy.
gates.HS8 = () => {
  const lib = stripC(read('functions', 'kalshiHardStopLib.js'));
  assert.ok(!/fetch|keyId|pem|\/portfolio|method: "POST"|runL1Tick|liveRequest/.test(lib));
  const idx = read('functions', 'index.js');
  const fn = idx.slice(idx.indexOf('exports.kalshiHardStopCheck'), idx.indexOf('exports.kalshiPaperTick'));
  assert.ok(!/KALSHI_LIVE_KEY_ID|KALSHI_LIVE_PRIVATE_KEY|secrets/.test(fn), 'no secret on the checker');
  assert.ok(/schedule: "every 5 minutes"/.test(fn), 'every 5 minutes: a 5 minute trip delay is fine for a 40% line, and the 15 minute stale rule allows two missed runs');
  assert.ok(hs.HARD_STOP.staleMs >= 3 * 5 * 60 * 1000 && hs.HARD_STOP.heartbeatMs < 5 * 60 * 1000, 'every run refreshes the heartbeat and three runs fit in the stale window');
  assert.ok(/functions:kalshiHardStopCheck/.test(read('functions', 'deploy-sizing.sh')));
  assert.ok(/kalshiHardStopLib/.test(read('functions', 'deploy-latest.sh')));
};

// HS9: a trip tells the owner once: a critical bell item, a phone alert, never repeated every minute, retried if the alert write failed.
gates.HS9 = async () => {
  const w = world([l1(100, at(0)), l1(-500, at(1))], [], { base: BASE });
  const r = await run(w);
  assert.strictEqual(r.tripped, 'drawdown');
  assert.deepStrictEqual(w.events.map((e) => e.kind), ['hard stop']);
  assert.strictEqual(w.alerts.length, 1);
  w.io.now += 120000; await run(w); w.io.now += 120000; await run(w);
  assert.strictEqual(w.events.length, 1, 'not repeated');
  assert.strictEqual(w.alerts.length, 1);
  // erased by the tick's write, re-derived: still no second alert (the claim holds)
  w.st.sizing = { base: BASE }; w.io.now += 120000; await run(w);
  assert.strictEqual(w.alerts.length, 1, 'a re-derived latch does not alert again');
  // the alert write fails: the claim is put back and the next minute tries again
  const f = world([l1(100, at(0)), l1(-500, at(1))], [], { base: BASE });
  let fail = true;
  f.io.raiseAlert = async (a) => { if (fail) throw new Error('no'); f.alerts.push(a); };
  await run(f);
  assert.ok(hs.hardStopTripped(f.st.sizing), 'the latch is set even though the alert failed');
  fail = false; f.io.now += 120000; await run(f);
  assert.strictEqual(f.alerts.length, 1, 'the next minute sends it');
  // the phone: a CHANGED stamp alerts, a rewrite does not
  const base = { active: false };
  assert.deepStrictEqual(push.sessionKinds(base, { ...base, hardStopAlert: { at: 5 } }), ['hardstop']);
  assert.deepStrictEqual(push.sessionKinds({ ...base, hardStopAlert: { at: 5 } }, { ...base, hardStopAlert: { at: 5 }, lastNote: 'x' }), []);
  const m = push.message('hardstop', {});
  assert.ok(/Hard stop/.test(m.title) && m.tag === 'issue-hardstop');
  // the page builds a critical item from the event
  assert.ok(/k === 'hard stop'\)\{\s*out\.push\(\{ id: id, ts: e\.ts, level: 'critical'/.test(read('index.html')));
};

// HS10: an absent field after the start date means no buys (deleted sizing document, checker never written); nothing about the tick changes before it.
gates.HS10 = async () => {
  const w = l1world(); const r = await tick(w, state);
  assert.strictEqual(w.posts.length, 0, 'no hardStop field after the start date: nothing is sent');
  assert.strictEqual(r.skipped, 'hard stop');
  const w2 = l1world(); await tick(w2, null);
  assert.strictEqual(w2.posts.length, 0, 'a missing sizing document: nothing is sent');
  const lv = read('functions', 'kalshiLiveLib.js');
  const body = lv.slice(lv.indexOf('Hard account stop (docs'), lv.indexOf('Probe drop rule (see'));
  assert.ok(!/await (store|args)\./.test(body.replace(/await note/g, '')) && !/liveRequest|setSizingState/.test(body), 'the check makes no read and no write of its own');
};

// HS11: the base at the peak: kept while the peak stands, refreshed only by a new high.
gates.HS11 = async () => {
  const w = world([l1(50, at(0))], [], { base: 1000 });
  await run(w);
  assert.strictEqual(w.st.sizing.hardStop.peakBase, 1000);
  w.st.sizing.base = 1500; w.io.now += 600000; await run(w);
  assert.strictEqual(w.st.sizing.hardStop.peakBase, 1000, 'a bigger base without a new high changes nothing');
  w.l1Orders = [l1(50, at(0)), l1(60, at(1))]; w.io.now += 600000; await run(w);
  assert.strictEqual(w.st.sizing.hardStop.peakBase, 1500, 'a new high takes the base the account had then');
  assert.strictEqual(w.st.sizing.hardStop.peakEquity, 110);
  // a peak can never fall, even if the stored record is lost: the replay finds it again
  w.st.sizing = { base: 1500 }; w.io.now += 600000; await run(w);
  assert.strictEqual(w.st.sizing.hardStop.peakEquity, 110);
  // open orders are not results, hand-closed ones are not the bot's result, other strategies' junk is ignored
  const ev = hs.replay([{ ...l1(-999, at(0)), settled: false }, { ...l1(-999, at(1)), result: 'hand' }, { strategy: 'X' }, null, l1(-999, R - 1000)]);
  assert.strictEqual(ev.trades, 0, 'open, hand-closed and pre-rearmAt orders count for nothing');
};

// HS14: a trip ENDS THE SESSION the way the loss stop does; the Start button is refused while the latch holds; a stale-cache tick cannot reopen buys; the exit watch does not depend on the session.
gates.HS14 = async () => {
  const sess = { active: true };
  const w = world([l1(100, at(0)), l1(-500, at(1))], [], { base: BASE });
  w.io.endSession = async (why) => { if (sess.active !== true) return false; Object.assign(sess, { active: false, endedAt: NOW, endedBecause: why }); return true; };
  await run(w);
  assert.strictEqual(sess.active, false, 'the trip ended the session');
  assert.ok(/hard account stop/.test(sess.endedBecause) && /40%/.test(sess.endedBecause) && !/by the owner/i.test(sess.endedBecause), 'with a reason that says the 40% account stop and is not read as an owner stop');
  assert.deepStrictEqual(w.events.map((e) => e.kind).sort(), ['hard stop', 'session ended']);
  assert.deepStrictEqual(push.sessionKinds({ active: true }, { active: false, endedBecause: sess.endedBecause }), ['issue'], 'the existing stopped-by-itself phone alert fires too');
  // The race: the tick's stale full write puts back an untripped cache while a session is started again by hand. The next run ends it again, and the latch (in its own document) is intact.
  w.st.sizing = { base: BASE, hardStop: { ...okRec, rearmAt: R } }; sess.active = true; w.io.now += 300000;
  await run(w);
  assert.strictEqual(sess.active, false, 'a session restarted while the latch holds is ended again on the next run');
  assert.ok(hs.hardStopTripped(w.st.sizing), 'and the cache is restored from the latch');
  assert.strictEqual(w.events.filter((e) => e.kind === 'session ended').length, 2);
  // an owner stop is left alone: no running session, nothing written, no event
  const q = world([l1(100, at(0)), l1(-500, at(1))], [], { base: BASE });
  q.io.endSession = async () => false;
  await run(q);
  assert.ok(!q.events.some((e) => e.kind === 'session ended'));
  // the Start callable refuses while the latch holds, and reads the checker's own record
  const idx = read('functions', 'index.js');
  const cb = idx.slice(idx.indexOf('exports.kalshiL1Session'), idx.indexOf('const arm = await', idx.indexOf('exports.kalshiL1Session')));
  assert.ok(/doc\("hardStopState"\)\.get\(\)/.test(cb) && /hardState\.data\(\)\.tripped === true/.test(cb) && /HttpsError\("failed-precondition"/.test(cb), 'Start refuses while the latch holds');
  assert.ok(cb.indexOf('hardStopState') < cb.indexOf('.set({ active: true') || !/\.set\(\{ active: true/.test(cb), 'before it writes anything');
  // the exit watch never reads session.active (it only needs the session document to exist)
  const lv = read('functions', 'kalshiLiveLib.js');
  const watch = stripC(lv.slice(lv.indexOf('async function runExitWatch'), lv.indexOf('async function flattenAll')));
  assert.ok(!/session\.active|\.active === true/.test(watch), 'the L1 exit watch does not depend on session.active');
  assert.ok(/ends the session|endSession/.test(read('functions', 'kalshiHardStopLib.js')));
};

// HS15: the slot's entry gate: the production caller always passes the verdict, a boolean computed from the sizing document every minute. (An omitted argument stays open: failing closed there broke
// about twenty slot engine tests that call the engine directly, so it was left, as the coordinator allowed.)
gates.HS15 = async () => {
  const idx = stripC(read('functions', 'index.js'));
  assert.ok(/hardStopBlocked: hardStopLib\.hardStopBlocks\(sizingSnap\.exists \? sizingSnap\.data\(\) : null, now\)\.blocked/.test(idx), 'the production caller passes the verdict (a boolean) every time');
  assert.strictEqual(idx.split('slotRun.runSlotTick(').length - 1, 1, 'and there is one production call site');
  assert.strictEqual(hs.hardStopBlocks(null, NOW).blocked, true, 'so with the sizing document missing the value passed is true');
};

// HS13: if the base at the peak is not on record, the smallest base seen since the start is used (a tighter line); with no base at all, no buys. The worked example: an $800 account peaks at +$100 -> $900, line $360.
gates.HS13 = async () => {
  const ex = world([l1(100, at(0)), l1(-359.99, at(1))], [], { base: 900 });
  const r0 = await run(ex);
  assert.ok(!r0.killed && ex.st.sizing.hardStop.line === 360, 'worked example: the line is $360 (40% of $900)');
  ex.l1Orders = [l1(100, at(0)), l1(-360, at(1))]; ex.st.sizing.base = 5900; ex.io.now += 60000;   // $5,000 deposited afterwards
  assert.strictEqual((await run(ex)).tripped, 'drawdown', 'a $360 fall trips whatever is deposited later');
  const w = world([l1(100, at(0))], [], { base: 600 });
  await run(w);                                         // smallest base seen: 600
  w.st.sizing.base = 1000; w.io.now += 60000; await run(w);
  assert.strictEqual(w.st.state.minBase, 600);
  w.st.state = { ...w.st.state, peakBase: null };       // the base at the peak is lost from the record
  w.l1Orders = [l1(100, at(0)), l1(-250, at(1))];       // a drop of 250 from the peak: over 40% of 600 (240), under 40% of 1000 (400)
  w.io.now += 60000;
  assert.strictEqual((await run(w)).tripped, 'drawdown', 'the smallest base seen sets the line, not the larger current one');
  const none = world([l1(1, at(0))], [], {});
  await run(none);
  assert.ok(hs.hardStopBlocks(none.st.sizing, NOW).blocked, 'no base at all: no new buys');
};

// HS12: a quiet minute writes nothing until the heartbeat is due; then one tiny write.
gates.HS12 = async () => {
  const w = world([l1(5, at(0))], [], { base: BASE });
  await run(w);
  const n1 = w.wrote.length;
  w.io.now += 60000; await run(w);
  assert.strictEqual(w.wrote.length, n1, 'a quiet minute writes nothing');
  w.io.now += hs.HARD_STOP.heartbeatMs; await run(w);
  assert.strictEqual(w.wrote.length, n1 + 1, 'the heartbeat is refreshed once it is due');
  assert.strictEqual(w.wrote[n1].checkedAt, w.io.now, 'a heartbeat');
  // read cost is bounded: only orders since rearmAt are asked for
  const asked = [];
  const q = world([], [], { base: BASE }); q.io.readL1Orders = async (s) => { asked.push(s); return []; }; q.io.readSlotOrders = async (s) => { asked.push(s); return []; };
  await run(q);
  assert.deepStrictEqual(asked, [R, R]);
};

(async () => {
  let failed = 0;
  for (const [k, f] of Object.entries(gates)) { try { await f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + '\n' + (e && e.stack || e)); } }
  process.exit(failed ? 1 : 0);
})();

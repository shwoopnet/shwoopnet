'use strict';
// Gates for the second slot's wiring into functions/index.js, the Firestore side and the rules (docs/SECOND_SLOT_WIRING.md step B3). Each states the consequence, not the mechanism.
// Part A proves OFF-EQUIVALENCE at the level of the deployed functions: with the slot off, kalshiLiveArmed, kalshiLiveExit and kalshiFlattenAll make exactly the database operations, exchange
// requests and console lines they made BEFORE the slot was wired (test/fixtures/offEquivalenceIndex.json, recorded from index.js at the commit before, by test/fixtures/indexHarness.js).
// Part B proves the Firestore side with an in-memory database: one lock and one order across two instances, atomic kill latch, leases, Flatten bookkeeping.
// Part C proves the rules, the page and the alerts do not see the new collections.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const harness = require('./fixtures/indexHarness');
const slotLib = require('../functions/kalshiSlotLib');
const runLib = require('../functions/kalshiSlotRunLib');
const storeLib = require('../functions/kalshiSlotStoreLib');
const live = require('../functions/kalshiLiveLib');

const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const indexPath = path.join(root, 'functions', 'index.js');
const gates = {};
const { NOW, T } = harness;

// ---------------------------------------------------------------- A. OFF-EQUIVALENCE of the deployed functions ----------------------------------------------------------------
gates['SI0 with the slot off, kalshiLiveArmed, kalshiLiveExit and kalshiFlattenAll make the same database operations, requests and console lines as before the wiring'] = async () => {
  assert.strictEqual(slotLib.slotActive(), false, 'the shipped constants are off');
  const golden = JSON.parse(read('test', 'fixtures', 'offEquivalenceIndex.json'));
  const now = await harness.run(indexPath);
  assert.strictEqual(now.length, golden.length);
  for (let i = 0; i < golden.length; i++) assert.deepStrictEqual(now[i], golden[i], 'off-equivalence broken in "' + golden[i].name + '": the deployed function now does something different while the slot is off. Fix the code, not the fixture.');
  const touched = JSON.stringify(now).match(/kalshiSlot|kalshiLiveDirection/g);
  assert.strictEqual(touched, null, 'no slot collection and no lock document is read or written while the slot is off');
};

gates['SI1 index.js: SLOT_ON comes only from the slot library, every slot call sits under it, and there is no new secret, schedule, callable or endpoint'] = () => {
  const src = read('functions', 'index.js'), c = code(src);
  assert.deepStrictEqual([...c.matchAll(/SLOT_ON\s*=\s*([^;]*);/g)].map((m) => m[1]), ['slotLib.slotWatch()'], 'derived from the slot library\'s constants and nothing else (entries allowed, or a slot order has ever existed)');
  assert.ok(!/slotLib\.slotActive/.test(c), 'index.js never uses the narrower entry gate: watching must not stop when entries do');
  assert.deepStrictEqual([...c.matchAll(/require\("(\.\/kalshiSlot[A-Za-z]*)"\)/g)].map((m) => m[1]), ['./kalshiSlotLib', './kalshiSlotRunLib', './kalshiSlotStoreLib']);
  assert.ok(!/kalshiSlotOrders|kalshiSlotControl|kalshiLiveDirection/.test(c), 'the collection names live in the store library, not in index.js');
  // Every use of slotRun / slotStoreLib / slotLib (apart from the definition and the requires) is in a line guarded by SLOT_ON or spread under it.
  const lines = c.split('\n');
  const inGuardedBlock = (i) => {      // is line i inside an `if (SLOT_ON) {` block opened earlier and not yet closed?
    for (let j = i; j >= 0; j--) {
      if (/if \(SLOT_ON\) \{\s*$/.test(lines[j])) {
        let depth = 0;
        for (let k = j; k <= i; k++) { depth += (lines[k].match(/\{/g) || []).length - (lines[k].match(/\}/g) || []).length; if (depth <= 0 && k < i) return false; }
        return depth > 0;
      }
    }
    return false;
  };
  lines.forEach((l, i) => {
    if (!/slotRun\.|slotStoreLib\.|slotLib\./.test(l) || /^\s*const (slotLib|slotRun|slotStoreLib) = require|const SLOT_ON|^\s*createTestLocked\(id, data, o\)|^\s*releaseClose\(ticker, who\)/.test(l)) return;
    assert.ok(/SLOT_ON/.test(l) || inGuardedBlock(i), 'unguarded slot call: ' + l.trim().slice(0, 150));
  });
  // The blocks that hold more than one line of slot work are `if (SLOT_ON) {` blocks.
  assert.strictEqual((c.match(/if \(SLOT_ON\) \{/g) || []).length, 2, 'the slot tick and the slot exit pass are the two multi-line blocks (the rest are one-line guards)');
  // No new exported function, secret or parameter.
  const before = ['KALSHI_WATCHDOG_URL', 'KALSHI_STOP_ALERT_URL', 'KALSHI_LIVE_KEY_ID', 'KALSHI_LIVE_PRIVATE_KEY', 'KALSHI_LIVE_ENABLED', 'KALSHI_PUSH_VAPID_PRIVATE', 'KALSHI_REPORT_TOKEN'];
  assert.deepStrictEqual([...c.matchAll(/define(?:Secret|String)\("([A-Z_]+)"/g)].map((m) => m[1]).sort(), before.slice().sort(), 'no new secret or parameter');
  const exported = [...c.matchAll(/^exports\.(\w+)/gm)].map((m) => m[1]).sort();
  assert.deepStrictEqual(exported, ['kalshiBookRecorder', 'kalshiBooks', 'kalshiFlattenAll', 'kalshiL1Session', 'kalshiLiveAccount', 'kalshiLiveArmed', 'kalshiLiveBaseline', 'kalshiLiveExit', 'kalshiNightlyReport', 'kalshiPaperTick',
    'kalshiPushKey', 'kalshiPushOrder', 'kalshiPushSession', 'kalshiPushSubscribe', 'kalshiPushUnsubscribe', 'kalshiTape', 'marketTapeTick'].sort(), 'no new scheduled function, callable or endpoint');
  assert.ok(!/_testForce/.test(src), 'the real caller never sets the test hook');
  // The slot tick runs after L1 and cannot fail it; the slot exits run after the L1 exit watch and cannot stop it.
  assert.ok(/const l1Result = await live\.runL1Tick/.test(c) && c.indexOf('slotRun.runSlotTick') > c.indexOf('const l1Result = await live.runL1Tick'));
  assert.ok(/try \{\s*const slotResult = await slotRun\.runSlotTick[\s\S]*?\} catch \(e\) \{ console\.error\("kalshiLiveArmed: slot tick failed/.test(c));
  assert.ok(c.indexOf('slotRun.runSlotExits') > c.indexOf('live.runExitWatch(') && /try \{\s*await slotRun\.runSlotExits[\s\S]*?\} catch \(e\) \{ console\.error\("kalshiLiveExit: slot exits failed/.test(c));
  // Flatten passes the hooks only when the slot is on.
  assert.ok(/\.\.\.\(SLOT_ON \? \{ slot: slotStoreLib\.slotHooks\(db\) \} : \{\}\)/.test(c));
  assert.strictEqual((c.match(/\.\.\.\(SLOT_ON \? \{ slot: slotStoreLib\.slotHooks\(db\) \} : \{\}\)/g) || []).length, 2, 'Flatten and the L1 exit watch both get the hooks');
  assert.ok(/clock: Date\.now/.test(c), 'the slot tick is given a real clock so an entry is judged at commit time');
};

gates['SI2 with the gate forced on in memory (no strategy registered) the deployed functions run end to end, read the slot collection, write nothing slot-related and send exactly the orders they sent before'] = async () => {
  const golden = JSON.parse(read('test', 'fixtures', 'offEquivalenceIndex.json'));
  const real = slotLib.slotWatch;
  slotLib.slotWatch = () => true;     // test-only: the shipped constants stay off; this flips the gate for this process only
  let on;
  try { on = await harness.run(indexPath); } finally { slotLib.slotWatch = real; }
  assert.strictEqual(slotLib.slotWatch(), false);
  const sends = (log) => log.filter((x) => x[0] === 'fetch' && x[1] === 'POST');
  let slotReads = 0;
  for (let i = 0; i < golden.length; i++) {
    assert.deepStrictEqual(sends(on[i].log), sends(golden[i].log), golden[i].name + ': the same orders go out');
    assert.deepStrictEqual(on[i].ret, golden[i].ret, golden[i].name + ': the same answer');
    assert.strictEqual(on[i].threw, null);
    assert.ok(!on[i].log.some((x) => x[0] === 'console.error'), golden[i].name + ': no error was logged: ' + JSON.stringify(on[i].log.filter((x) => x[0] === 'console.error')));
    const writes = on[i].log.filter((x) => ['set', 'update', 'create', 'delete', 'add'].includes(x[0]) && /kalshiSlot|kalshiLiveDirection/.test(String(x[1])));
    assert.deepStrictEqual(writes, [], golden[i].name + ': nothing is written to a slot collection when no strategy is registered');
    slotReads += on[i].log.filter((x) => x[0] === 'query' && x[1] === 'kalshiSlotOrders').length;
  }
  assert.ok(slotReads >= 3, 'the slot collection is read (unresolved check, order list, ignore set, exit idle check): ' + slotReads);
  // The L1 side of every scenario is unchanged apart from the extra slot reads.
  for (let i = 0; i < golden.length; i++) {
    const strip = (log) => log.filter((x) => !(x[0] === 'query' && x[1] === 'kalshiSlotOrders'));
    assert.deepStrictEqual(strip(on[i].log).filter((x) => x[0] === 'fetch'), strip(golden[i].log).filter((x) => x[0] === 'fetch'), golden[i].name + ': the same exchange requests');
  }
};

// ---------------------------------------------------------------- B. the Firestore side ----------------------------------------------------------------
// An in-memory database whose transactions are serialised, as Firestore serialises two writers of one document.
function db(seed) {
  const log = [];
  const d = harness.fakeDb(seed, log);
  let queue = Promise.resolve();
  const inner = d.runTransaction;
  d.runTransaction = (fn) => { const p = queue.then(() => inner(async (tx) => { await new Promise((r) => setImmediate(r)); return fn(tx); })); queue = p.catch(() => {}); return p; };
  d.log = log;
  d.rows = (col) => { const out = {}; return d.collection(col).get().then((s) => { for (const x of s.docs) out[x.id] = x.data(); return out; }); };
  return d;
}
const liveStoreOf = (d) => ({ halted: async () => false, hasUnresolved: async () => false, sessionTrades: async () => [], claimClose: async () => true });
const slotRec = (o) => Object.assign(slotLib.slotOrderRecord({ strategyId: 'TESTA', ticker: T, side: 'no', step: 1, count: 2, limit: 0.8, maxCost: 1.7, ts: NOW }), o || {});
const allowIfLockOk = (side, record) => (lock) => (lock && lock.side !== side ? { allowed: false, reason: 'the lock holds the other side' } : { allowed: true, record, lock: { side, by: 'SLOT:TESTA', ts: NOW } });

gates['SI3 two instances racing, an L1 YES and a slot NO on one market, through the real store code: one lock, one order document, the loser writes nothing (both orders of arrival)'] = async () => {
  for (const l1First of [true, false]) {
    const d = db({});
    const store = storeLib.slotStore(d, liveStoreOf(d));
    const l1 = () => storeLib.createLocked(d, 'L1-' + T, { ticker: T, side: 'yes', ts: NOW, strategy: 'L1' }, { ticker: T, side: 'yes' });
    const sl = () => store.runSlotEntry({ ticker: T, side: 'no', now: NOW, decide: allowIfLockOk('no', slotRec()) });
    const [a, b] = l1First ? await Promise.all([l1(), sl()]) : (await Promise.all([sl(), l1()])).reverse();
    const locks = await d.rows('kalshiLiveDirection'), slotDocs = await d.rows('kalshiSlotOrders'), l1Docs = await d.rows('kalshiLiveOrders');
    assert.strictEqual(Object.keys(locks).length, 1, 'exactly one lock');
    assert.strictEqual(Object.keys(slotDocs).length + Object.keys(l1Docs).length, 1, 'exactly one order document (l1First=' + l1First + ')');
    if (Object.keys(l1Docs).length) { assert.strictEqual(a, true); assert.strictEqual(b.created, false); assert.strictEqual(locks[T].side, 'yes'); assert.strictEqual(locks[T].by, 'L1'); }
    else { assert.strictEqual(a, 'direction'); assert.strictEqual(b.created, true); assert.strictEqual(locks[T].side, 'no'); }
  }
};

gates['SI3b the unresolved check counts a lost exit answer and a stale sending exit, but not a sale that is mid-flight, and an exit claim is stamped'] = async () => {
  const d = db({ 'kalshiSlotOrders/a': slotRec({ id: 'a', status: 'filled', fillCount: '2', exitStatus: 'sold', settled: false }) });
  const hooks = storeLib.slotHooks(d), store = storeLib.slotStore(d, liveStoreOf(d));
  assert.strictEqual(await hooks.hasUnresolved(NOW), false, 'a clean book');
  await d.collection('kalshiSlotOrders').doc('b').set(slotRec({ id: 'b', status: 'filled', fillCount: '2', exitStatus: 'sending', exitClaimedAt: NOW - 5000, settled: false }));
  assert.strictEqual(await hooks.hasUnresolved(NOW), false, 'a sell claimed 5 seconds ago is mid-flight, not unresolved');
  assert.strictEqual(await store.hasUnresolved(NOW + 120000), true, 'a sell claimed two minutes ago that never finished is');
  await d.collection('kalshiSlotOrders').doc('b').set(slotRec({ id: 'b', status: 'filled', fillCount: '2', exitStatus: 'sending', settled: false }));
  assert.strictEqual(await hooks.hasUnresolved(NOW), true, 'a sending exit with no claim time is unresolved (fail closed)');
  await d.collection('kalshiSlotOrders').doc('b').update({ exitStatus: 'unknown' });
  assert.strictEqual(await hooks.hasUnresolved(NOW), true, 'a lost exit answer is unresolved at once');
  await d.collection('kalshiSlotOrders').doc('b').update({ exitStatus: 'sold', settled: true });
  assert.strictEqual(await hooks.hasUnresolved(NOW), false);
  await d.collection('kalshiSlotOrders').doc('c').set(slotRec({ id: 'c', status: 'filled', fillCount: '2', exitStatus: undefined, exitTries: 0, settled: false }));
  assert.strictEqual(await store.claimSlotExit('c', 0, NOW), true);
  assert.strictEqual((await d.rows('kalshiSlotOrders')).c.exitClaimedAt, NOW);
};
gates['SI3c the lease release only clears a lease its own holder took, and unsoldOn adds up the slot\'s unsold contracts on one side'] = async () => {
  const d = db({ ['kalshiLiveClosing/' + T]: { by: 'flatten', at: NOW }, 'kalshiSlotOrders/a': slotRec({ id: 'a', side: 'yes', status: 'filled', fillCount: '2', count: 2 }), 'kalshiSlotOrders/b': slotRec({ id: 'b', side: 'yes', status: 'filled', fillCount: '3', count: 3, exitCount: 1 }), 'kalshiSlotOrders/c': slotRec({ id: 'c', side: 'no', status: 'filled', fillCount: '4', count: 4 }) });
  await storeLib.releaseCloseLease(d, T, 'exit');
  assert.ok((await d.rows('kalshiLiveClosing'))[T], 'Flatten\'s lease is untouched by another holder\'s release');
  await storeLib.releaseCloseLease(d, T, 'flatten');
  assert.ok(!(await d.rows('kalshiLiveClosing'))[T], 'the holder\'s own release clears it');
  const hooks = storeLib.slotHooks(d);
  assert.strictEqual(await hooks.unsoldOn(T, 'yes'), 4); assert.strictEqual(await hooks.unsoldOn(T, 'no'), 4); assert.strictEqual(await hooks.unsoldOn('KXETH15M-26OCT071415-15', 'yes'), 0);
};

gates['SI4 the same side in one market is allowed for both engines and the lock stays as the first writer left it'] = async () => {
  const d = db({});
  const store = storeLib.slotStore(d, liveStoreOf(d));
  assert.strictEqual(await storeLib.createLocked(d, 'L1-' + T, { ticker: T, side: 'yes', ts: NOW }, { ticker: T, side: 'yes' }), true);
  const r = await store.runSlotEntry({ ticker: T, side: 'yes', now: NOW + 1, decide: allowIfLockOk('yes', slotRec({ side: 'yes' })) });
  assert.strictEqual(r.created, true);
  const locks = await d.rows('kalshiLiveDirection');
  assert.deepStrictEqual(locks[T], { side: 'yes', by: 'L1', ts: NOW }, 'the existing same-side lock is left alone');
};

gates['SI5 an order document that already exists rolls the lock back too, and is reported as already attempted (never a second order)'] = async () => {
  const d = db({ ['kalshiSlotOrders/' + slotRec().id]: slotRec({ status: 'filled' }) });
  const store = storeLib.slotStore(d, liveStoreOf(d));
  const r = await store.runSlotEntry({ ticker: T, side: 'no', now: NOW, decide: allowIfLockOk('no', slotRec()) });
  assert.deepStrictEqual(r, { created: false, reason: 'already attempted' });
  assert.deepStrictEqual(await d.rows('kalshiLiveDirection'), {}, 'no lock was left behind');
  const l1 = await storeLib.createLocked(db({ ['kalshiLiveOrders/L1-' + T]: { ticker: T } }), 'L1-' + T, { ticker: T }, { ticker: T, side: 'yes' });
  assert.strictEqual(l1, false, 'L1 sees the same answer createTest gives today');
};

gates['SI6 the decision runs on what the database holds at commit time: the slot orders and L1 orders it is handed are the fresh ones, and a refusal writes nothing'] = async () => {
  const other = slotRec({ id: 'S-TESTA-' + T + '-0', step: 0, status: 'filled', fillCount: '2' });
  const d = db({ ['kalshiSlotOrders/' + other.id]: other, ['kalshiLiveOrders/L1-' + T]: { ticker: T, side: 'no', strategy: 'L1' }, 'kalshiLiveOrders/L1-OTHER': { ticker: 'OTHER' } });
  const store = storeLib.slotStore(d, liveStoreOf(d));
  let seen;
  const r = await store.runSlotEntry({ ticker: T, side: 'no', now: NOW, decide: (lock, slotNow, l1Docs) => { seen = { lock, slotNow, l1Docs }; return { allowed: false, reason: 'no room' }; } });
  assert.deepStrictEqual(r, { created: false, reason: 'no room' });
  assert.strictEqual(seen.lock, null);
  assert.deepStrictEqual(seen.slotNow.map((x) => x.id), [other.id]);
  assert.deepStrictEqual(seen.l1Docs.map((x) => x.id), ['L1-' + T], 'only this ticker\'s L1 orders');
  assert.deepStrictEqual(await d.rows('kalshiLiveDirection'), {});
  assert.deepStrictEqual(Object.keys(await d.rows('kalshiSlotOrders')), [other.id]);
};

gates['SI7 a strategy that trips a kill rule is latched in the SAME transaction as the order\'s last patch, and only that strategy'] = async () => {
  const o = slotRec({ status: 'filled', fillCount: '2' });
  const d = db({ ['kalshiSlotOrders/' + o.id]: o });
  const store = storeLib.slotStore(d, liveStoreOf(d));
  await store.finishSlotOrder(o.id, { settled: true, result: 'exit' }, (orders) => (orders.find((x) => x.id === o.id).settled === true ? { strategyId: 'TESTA', killedAt: NOW, reason: '3 losses in a row' } : null));
  assert.strictEqual((await d.rows('kalshiSlotOrders'))[o.id].settled, true);
  assert.deepStrictEqual((await d.rows('kalshiSlotControl')).killed, { TESTA: { killedAt: NOW, reason: '3 losses in a row' } });
  assert.deepStrictEqual(await store.killLatches(), { TESTA: { killedAt: NOW, reason: '3 losses in a row' } });
  const d2 = db({ ['kalshiSlotOrders/' + o.id]: o });
  await storeLib.slotStore(d2, liveStoreOf(d2)).finishSlotOrder(o.id, { settled: true }, () => null);
  assert.deepStrictEqual(await d2.rows('kalshiSlotControl'), {}, 'no rule tripped, no latch');
  assert.deepStrictEqual(await storeLib.slotStore(d2, liveStoreOf(d2)).killLatches(), {}, 'a missing latch document means nothing is latched');
};

gates['SI8 the close lease is released only by the holder that took it, so a slot sale cannot clear L1\'s or Flatten\'s claim'] = async () => {
  const d = db({ 'kalshiLiveClosing/A': { by: 'slot', at: NOW }, 'kalshiLiveClosing/B': { by: 'flatten', at: NOW }, 'kalshiLiveClosing/C': { by: 'exit', at: NOW } });
  const store = storeLib.slotStore(d, liveStoreOf(d));
  await store.releaseClose('A', 'slot'); await store.releaseClose('B', 'slot'); await store.releaseClose('C', 'slot'); await store.releaseClose('NONE', 'slot');
  assert.deepStrictEqual(Object.keys(await d.rows('kalshiLiveClosing')).sort(), ['B', 'C']);
};

gates['SI9 Flatten bookkeeping closes only the slot orders on markets the account is now flat in, and latches every strategy off whatever the results were'] = async () => {
  const mk = (t, o) => slotRec(Object.assign({ ticker: t, id: 'S-' + t, clientOrderId: 'S-' + t, status: 'filled', fillCount: '2' }, o || {}));
  const A = 'KXBTC15M-A', B = 'KXBTC15M-B', C = 'KXBTC15M-C', D = 'KXBTC15M-D';
  const d = db({ ['kalshiSlotOrders/S-' + A]: mk(A), ['kalshiSlotOrders/S-' + B]: mk(B), ['kalshiSlotOrders/S-' + C]: mk(C), ['kalshiSlotOrders/S-' + D]: mk(D, { settled: true, result: 'yes' }) });
  const prev = slotLib.activeSlotStrategies;
  // No strategy is registered in this phase: the latch step then has nothing to write, and the closing step is what is under test here.
  const hooks = storeLib.slotHooks(d);
  await hooks.afterFlatten({ results: [{ ticker: A, status: 'sold' }, { ticker: B, status: 'skipped', detail: 'already closed' }, { ticker: C, status: 'partly sold' }, { ticker: D, status: 'sold' }], now: NOW });
  const rows = await d.rows('kalshiSlotOrders');
  assert.strictEqual(rows['S-' + A].settled, true); assert.strictEqual(rows['S-' + A].result, 'hand'); assert.strictEqual(rows['S-' + A].flattened, true);
  assert.strictEqual(rows['S-' + B].result, 'hand');
  assert.strictEqual(rows['S-' + C].settled, false, 'a partly sold market keeps its order open: the shared stop counts it as lost');
  assert.strictEqual(rows['S-' + D].result, 'yes', 'an already settled order is not touched');
  assert.strictEqual(rows['S-' + A].settledPnl, null, 'no fabricated profit figure');
  void prev;
  // With a strategy registered (test-only factory flags are not available to the store, so the registry is stubbed), every strategy is latched.
  const real = slotLib.activeSlotStrategies;
  slotLib.activeSlotStrategies = () => [{ id: 'TESTA' }, { id: 'TESTB' }];
  try { await hooks.afterFlatten({ results: [], now: NOW }); } finally { slotLib.activeSlotStrategies = real; }
  assert.deepStrictEqual((await d.rows('kalshiSlotControl')).killed, { TESTA: { killedAt: NOW, reason: 'flattened by the owner' }, TESTB: { killedAt: NOW, reason: 'flattened by the owner' } });
};

gates['SI10 the ignore set holds every slot entry and exit order id, so L1\'s sweep never reads a slot fill as a hand sale'] = async () => {
  const d = db({ 'kalshiSlotOrders/a': { orderId: 'o1', exitOrderId: 'x1' }, 'kalshiSlotOrders/b': { orderId: 'o2' }, 'kalshiSlotOrders/c': {} });
  assert.deepStrictEqual([...(await storeLib.slotIgnoreSet(d))].sort(), ['o1', 'o2', 'x1']);
};

// ---------------------------------------------------------------- the slot settle sweep ----------------------------------------------------------------
function sweepWorld(orders, l1, fills, market) {
  const patches = [], log = [];
  const store = {
    allSlotOrders: async () => orders, l1Recent: async () => l1,
    updateSlotOrder: async (id, p) => { patches.push(['update', id, p]); },
    finishSlotOrder: async (id, p, ev) => { patches.push(['finish', id, p, ev(orders.map((o) => (o.id === id ? { ...o, ...p } : o)))]); },
  };
  const fetchFn = async (url, o) => {
    const u = new URL(url); log.push(u.pathname);
    const body = /\/markets\//.test(u.pathname) ? { market: market || { result: 'yes' } } : /fills/.test(u.pathname) ? { fills } : {};
    return { status: 200, text: async () => JSON.stringify(body) };
  };
  return { store, fetchFn, patches, log };
}
const sweepArgs = (w, extra) => Object.assign({ store: w.store, fetchFn: w.fetchFn, keyId: 'k', pem: harness.PEM, now: NOW + 3600000 }, extra || {});

gates['SI11 the slot settle sweep makes no call at all while the slot is off'] = async () => {
  let calls = 0;
  const trap = new Proxy({}, { get: () => { calls += 1; throw new Error('touched'); } });
  const out = await runLib.runSlotSettle({ store: trap, fetchFn: async () => { calls += 1; throw new Error('touched'); }, keyId: 'k', pem: 'p', now: NOW });
  assert.ok(out.skipped && calls === 0);
};

const GOOD = () => ({
  id: 'TESTA', readme: 'kalshi-scalper/README.md#SLOT-TESTA', series: ['KXBTC15M', 'KXGOLD15M'],
  entry: { sideRule: 'favourite', priceMin: 0.6, priceMax: 0.9, leftMaxSec: 700, leftMinSec: 300 }, exit: { stopBid: 0.4, targetBid: 0.95, mustExitLeftSec: 90 },
  contractsPerOrder: 4, scaleIn: { maxSteps: 2, minGapSec: 60, sameSideOnly: true, requirePriorFilled: true },
  killRules: { maxConsecutiveLosses: 3, minNet: { afterFills: 20, net: -3 } }, forwardReadDate: '2026-12-01', reviewedAt: '2026-10-29',
});
const runner = () => runLib._testOnly.makeRunners({ enabled: true, registry: [GOOD()] });
const mkFill = (id, count) => ({ ticker: T, action: 'sell', side: 'yes', order_id: id, count_fp: String(count), created_time: new Date(NOW + 1000).toISOString() });

gates['SI12 the sweep settles a held-to-close slot order from the public result, and an L1 exit fill or the order\'s own entry fill is never read as a hand sale of it'] = async () => {
  const o = slotRec({ side: 'yes', status: 'filled', fillCount: '2', orderId: 'slot-o1', settled: false });
  const l1 = { id: 'L1-' + T, orderId: 'l1-o1', exitOrderId: 'l1-x1', ticker: T, side: 'yes' };
  const w = sweepWorld([o], [l1], [mkFill('l1-x1', 3), mkFill('slot-o1', 2)], { result: 'yes' });
  const out = await runner().runSlotSettle(sweepArgs(w));
  assert.strictEqual(out.settled, 1);
  const p = w.patches[0];
  assert.strictEqual(p[0], 'finish');
  assert.strictEqual(p[2].result, 'yes'); assert.strictEqual(p[2].settled, true); assert.ok(p[2].settledPnl > 0, 'booked as a win, not as a hand close');
  assert.strictEqual(p[2].settledAt, NOW + 3600000);
  assert.strictEqual(p[3], null, 'no kill rule tripped by one win');
};

gates['SI13b a genuine sale by someone else, covering the whole order, is still called a hand close (no profit figure), and an unreadable fills answer leaves the order open'] = async () => {
  const o = slotRec({ side: 'yes', status: 'filled', fillCount: '2', orderId: 'slot-o1', settled: false });
  const w = sweepWorld([o], [], [mkFill('manual-1', 2)], { result: 'no' });
  assert.strictEqual((await runner().runSlotSettle(sweepArgs(w))).settled, 1);
  assert.strictEqual(w.patches[0][2].result, 'hand'); assert.ok(!('settledPnl' in w.patches[0][2]));
  const w2 = sweepWorld([o], [], [], { result: 'no' });
  const f = w2.fetchFn; w2.fetchFn = async (u, x) => (/fills/.test(u) ? { status: 500, text: async () => '{}' } : f(u, x));
  assert.strictEqual((await runner().runSlotSettle(sweepArgs(w2))).settled, 0);
  assert.deepStrictEqual(w2.patches, [], 'it stays open, which the shared stop counts as lost');
  const w3 = sweepWorld([o], [], [], { result: null });
  assert.strictEqual((await runner().runSlotSettle(sweepArgs(w3))).settled, 0, 'a market with no result yet is left alone');
  const w4 = sweepWorld([o], [], [], { result: 'no' });
  assert.strictEqual((await runner().runSlotSettle(sweepArgs(w4, { keyId: null }))).settled, 0, 'without the key a hand close cannot be ruled out, so nothing is settled');
};

gates['SI13c a settle that completes a losing streak latches the strategy in the same write'] = async () => {
  const LATE = Date.parse('2026-11-03T15:00:00Z');       // after the strategy's reviewedAt date: only results from then on count toward its kill rules
  const lose = (n) => slotRec({ id: 'S-TESTA-' + T + '-' + n, step: n, side: 'yes', status: 'filled', fillCount: '2', orderId: 'o' + n, settled: true, result: 'no', settledPnl: -1.7, settledAt: LATE + n, ts: LATE + n });
  const o = slotRec({ side: 'yes', status: 'filled', fillCount: '2', orderId: 'slot-o3', settled: false, ts: LATE + 3 });
  const w = sweepWorld([lose(1), lose(2), o], [], [], { result: 'no' });
  await runner().runSlotSettle(sweepArgs(w, { now: LATE + 3600000 }));
  assert.deepStrictEqual(w.patches[0][3] && { id: w.patches[0][3].strategyId, why: w.patches[0][3].reason }, { id: 'TESTA', why: '3 losses in a row' });
};

// ---------------------------------------------------------------- C. rules, page and alerts ----------------------------------------------------------------
gates['SI13 the rules open the two collections to the admin for reading only, and nothing else about the slot to any browser'] = () => {
  const rules = read('firestore.rules'), c = rules.replace(/\/\/.*$/gm, '');
  for (const col of ['kalshiSlotOrders', 'kalshiLiveDirection']) {
    const m = c.match(new RegExp('match /' + col + '/\\{id\\} \\{([^}]*)\\}'));
    assert.ok(m, col + ' has a rule');
    assert.deepStrictEqual(m[1].split(';').map((x) => x.trim()).filter(Boolean), ['allow read: if isAdmin()', 'allow write: if false']);
  }
  assert.ok(!/kalshiSlotControl|kalshiLiveClosing/.test(c), 'the kill latch and the leases have no rule: closed to every browser');
  assert.ok(!/allow (read|write)[^;]*:\s*if true/.test(c) && !/allow write: if isAdmin\(\);\s*\}\s*\n\s*match \/kalshiSlot/.test(c));
};

gates['SI14 the Bot page and the alerts do not read the slot collections, so slot orders are never shown or alerted as L1 orders'] = () => {
  const page = read('index.html');
  assert.ok(!/kalshiLiveDirection/.test(page), 'the page never reads the direction lock');
  // The page card (strategy switch, Oct 29, 2026) reads kalshiSlotOrders and nothing else of the slot; it writes nothing.
  assert.ok(!/kalshiSlot(Lib|Run|Store|Control)/.test(page), 'the page names only the slot orders');
  // HARD PREREQUISITE of the pull request that flips SLOT_ENABLED (docs/SECOND_SLOT_WIRING.md, "Before the first admission"): without it the slot's fills show as manual trades on the page, its
  // dollars are missing from the Stop Loss and Risk meter, and a slot close sends no phone alert. This gate keeps SI14's absence check from locking the gap in: it must be REWRITTEN then, not deleted.
  if (slotLib.SLOT_ENABLED === true || slotLib.SLOT_STRATEGIES.length > 0) {
    assert.ok(/kalshiSlotOrders/.test(page), 'the page reads the slot orders before any strategy is admitted');
    assert.ok(/kalshiSlotOrders/.test(read('functions', 'index.js') + read('functions', 'kalshiPushLib.js') + read('functions', 'kalshiSlotStoreLib.js')) && /onDocumentWritten\(\{ document: "kalshiSlotOrders/.test(read('functions', 'index.js')), 'a slot close sends a phone alert');
  }
  assert.ok(/collection\([^)]*"kalshiLiveOrders"|kalshiLiveOrders/.test(page), 'the page still reads the L1 collection');
  const push = code(read('functions', 'kalshiPushLib.js'));
  assert.ok(!/kalshiSlot|kalshiLiveDirection|SLOT/i.test(push), 'the alert library knows nothing about the slot');
  const idx = code(read('functions', 'index.js'));
  const triggers = [...idx.matchAll(/onDocumentWritten\(\{ document: "([^"]+)"/g)].map((m) => m[1]);
  assert.deepStrictEqual(triggers.sort(), ['kalshiLiveControl/session', 'kalshiLiveOrders/{id}'], 'the only document triggers watch L1\'s orders and the session');
  const report = code(read('functions', 'kalshiReportLib.js'));
  assert.ok(!/kalshiSlot/.test(report), 'the nightly report reads only L1 orders');
};

gates['SI14b the watch constant can never be false while entries are allowed: admitting a strategy forces SLOT_EVER_USED, and nothing turns it back off'] = () => {
  assert.strictEqual(slotLib.SLOT_EVER_USED, false, 'ships false: nothing has ever been admitted');
  const src = read('functions', 'kalshiSlotLib.js').replace(/\/\/.*$/gm, '');
  assert.strictEqual((src.match(/SLOT_EVER_USED\s*=(?!=)/g) || []).length, 1, 'one definition, a constant');
  assert.ok(/const SLOT_EVER_USED = (false|true);/.test(src));
  if (slotLib.slotActive()) assert.strictEqual(slotLib.SLOT_EVER_USED, true, 'a strategy is admitted, so the watch must be permanent');
  assert.ok(/const slotWatch = \(\) => slotActive\(\) \|\| SLOT_EVER_USED === true;/.test(src));
};

gates['SI15 the store library imports no firebase package, reads no environment and has no clock or randomness'] = () => {
  const c = code(read('functions', 'kalshiSlotStoreLib.js'));
  assert.deepStrictEqual([...c.matchAll(/require\(([^)]*)\)/g)].map((m) => m[1]), ['"./kalshiSlotLib"']);
  assert.ok(!/process\.env|Date\.now|new Date|Math\.random|setTimeout|setInterval|fetch\(/.test(c));
};

gates['SI16 the docs carry the deploy note and the checklist is marked done'] = () => {
  const wiring = read('docs', 'SECOND_SLOT_WIRING.md'), design = read('docs', 'SECOND_SLOT_DESIGN.md'), claude = read('CLAUDE.md');
  assert.ok(/B3[^\n]*done/i.test(wiring) || /Deploy note/i.test(wiring));
  assert.ok(/deploy-sizing\.sh/.test(wiring) && /deploy-push\.sh/.test(wiring) && /firestore:rules/.test(wiring));
  assert.ok(/wired|Wired/.test(design));
  assert.ok(/Phase B/.test(claude) && /SLOT_ON/.test(claude));
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed += 1; console.log('FAIL ' + name + '\n     ' + (e && e.stack ? e.stack.split('\n').slice(0, 5).join('\n     ') : e)); }
  }
  if (failed) { console.log(failed + ' failed'); process.exit(1); }
  console.log('all ' + Object.keys(gates).length + ' slot index wiring gates passed');
})();

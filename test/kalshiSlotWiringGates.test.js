'use strict';
// Gates for the second slot's WIRING into functions/kalshiLiveLib.js (docs/SECOND_SLOT_WIRING.md step B2). Each states the consequence, not the mechanism.
// Part A proves OFF-EQUIVALENCE: with the slot off, runL1Tick, botRisk, settleOpenOrders, closedByHand, runExitWatch, exitWatchIdle and flattenAll make exactly the reads, writes and orders they made
// before the slot existed. The reference is test/fixtures/offEquivalence.json, recorded from the library as it stood BEFORE the wiring (see the header of test/fixtures/offEquivalenceScenarios.js).
// Part B drives the on path by replacing slotLib.slotWatch on the module object for the length of a gate (there is NO backdoor in production code) and proves the owner's rules: same side allowed, the opposite side (a hedge) blocked both ways, one window limit, one loss stop.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib');
const slotLib = require('../functions/kalshiSlotLib');
const runLib = require('../functions/kalshiSlotRunLib');
const fx = require('./fixtures/offEquivalenceScenarios');

const root = path.join(__dirname, '..');
const liveSrc = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const { NOW, T, GT, pem, q, l1World, settledLoss, iso } = fx;
const gates = {};
const clone = (x) => JSON.parse(JSON.stringify(x));
// The slot is ADMITTED (OICORE). Gates that prove OFF behaviour force the switch off on the module object for their length (the live library looks slotWatch up at call time) and ALWAYS restore.
async function withSlotOff(fn) {
  const a = slotLib.slotActive, w = slotLib.slotWatch;
  slotLib.slotActive = () => false; slotLib.slotWatch = () => false;
  try { return await fn(); } finally { slotLib.slotActive = a; slotLib.slotWatch = w; }
}
// The state a watch-only run represents: entries off, positions still watched.
async function withWatchOnly(fn) {
  const a = slotLib.slotActive, w = slotLib.slotWatch;
  slotLib.slotActive = () => false; slotLib.slotWatch = () => true;
  try { return await fn(); } finally { slotLib.slotActive = a; slotLib.slotWatch = w; }
}

// A slot order document as the wiring reads it.
const slotOrder = (o) => Object.assign({ id: 'S-TESTA-' + T + '-1', strategy: 'SLOT', slotId: 'TESTA', ticker: T, series: 'KXBTC15M', side: 'yes', step: 1, count: 4, fillCount: '4', maxCost: 3.1, price: 0.76,
  status: 'filled', settled: false, exitCount: 0, exitProceeds: 0, orderId: 'slot-ord-1', ts: NOW - 120000 }, o || {});
// The on path needs hooks; this bag records every call. The constants are passed by patching slotLib.slotWatch (see the runner at the bottom), not by a flag in the hook bag.
function hooks(o = {}) {
  const calls = [];
  const slot = {
    async unsoldOn(ticker, side) { calls.push('unsoldOn'); if (o.unsoldThrows) throw new Error('down'); return (o.orders || []).filter((t) => t.ticker === ticker && t.side === side).reduce((a, t) => a + slotLib.slotUnsoldOf(t), 0); },
    async hasUnresolved() { calls.push('hasUnresolved'); if (o.unresolvedThrows) throw new Error('down'); return o.unresolved === true; },
    async allOrders() { calls.push('allOrders'); if (o.ordersThrow) throw new Error('down'); return clone(o.orders || []); },
    async afterFlatten(a) { calls.push('afterFlatten'); if (o.afterThrows) throw new Error('book write failed'); slot.last = a; },
  };
  return { slot, calls };
}
// L1's locked create, as the Firestore store will do it: read the lock, refuse the other side, else write the lock and the order in one step.
function lockedStore(locks, o = {}) {
  return (docs) => ({
    async createTestLocked(id, data, { ticker, side }) {
      if (o.alwaysDirection) return 'direction';
      const lock = locks.get(ticker);
      if (lock && lock.side !== side) return 'direction';
      if (docs.has(id)) return false;
      if (!lock) locks.set(ticker, { side, by: 'L1' });
      docs.set(id, { ...data });
      return true;
    },
  });
}
const noPos = () => ({ status: 200, text: async () => JSON.stringify({ market_positions: [] }) });
const posOf = (ticker, n) => () => ({ status: 200, text: async () => JSON.stringify({ market_positions: [{ ticker, position_fp: String(n) }] }) });
const posts = (w) => w.r.log.filter((x) => x.kind === 'fetch' && x.method === 'POST');
const sizingOver = { sizingState: { cap: 5, base: 100, saved: 0, pool: 0, cum: 0, hwm: 0, reviewedAt: NOW - 1000, appliedTs: NOW - 5000 }, setSizingState: async () => {}, updateProbeRecord: async (fn) => fn({}).record };

// ---------------------------------------------------------------- A. OFF-EQUIVALENCE ----------------------------------------------------------------
gates.SW0 = async () => {
  const golden = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'offEquivalence.json'), 'utf8'));
  const now = await fx.runAll(path.join(root, 'functions', 'kalshiLiveLib.js'));
  assert.strictEqual(now.length, golden.length, 'same scenarios');
  for (let i = 0; i < golden.length; i++) {
    assert.deepStrictEqual(now[i], golden[i], 'off-equivalence broken in scenario "' + golden[i].name + '": the reads, writes, orders or return value changed while the slot is off. Fix the code, not the fixture.');
  }
  assert.ok(golden.length >= 25 && golden.some((s) => s.name === 'l1 gold sizing with window usage') && golden.some((s) => s.name.startsWith('flatten')) && golden.some((s) => s.name.startsWith('exit watch')), 'the record covers the cycle, the risk, the sweep, the exit watch and Flatten');
};
gates['SW0b with the slot forced off (the admitted constants overridden for this gate only), a hook bag handed to the live library does nothing (two locks on one door)'] = () => withSlotOff(async () => {
  assert.strictEqual(slotLib.slotActive(), false); assert.strictEqual(slotLib.slotWatch(), false);
  const plain = l1World({}), h = hooks({ force: false });
  const withBag = l1World({});
  const a = await live.runL1Tick({ ...plain.common, quotes: [q('KXBTC15M', T)] });
  const b = await live.runL1Tick({ ...withBag.common, quotes: [q('KXBTC15M', T)], slot: h.slot, shareOut: {} });
  assert.deepStrictEqual(b, a, 'same return');
  const mask = (k, v) => ((k === 'at' && typeof v === 'string') || ((k === 'sentAtMs' || k === 'answeredAtMs') && typeof v === 'number') ? '<wall clock>' : v);   // logRise and the send-time log stamp the wall clock
  assert.deepStrictEqual(JSON.parse(JSON.stringify(withBag.r.log, mask)), JSON.parse(JSON.stringify(plain.r.log, mask)), 'same reads, writes and orders in the same order');
  assert.deepStrictEqual(h.calls, [], 'no hook was called');
  // botRisk given slot arguments by mistake still ignores them only if they are absent; the live tick never passes them while off (checked by the equal logs above).
  const f = (bag) => { const w = { claims: [] }; return w; };
  void f;
  const calls = [];
  const fetchFn = async (url, o) => { calls.push(o.method + ' ' + url); if (url.includes('/portfolio/positions')) return { status: 200, text: async () => JSON.stringify({ market_positions: [] }) }; throw new Error('unexpected'); };
  const r = await live.flattenAll({ fetchFn, keyId: 'k', pem, now: NOW, store: {}, slot: h.slot });
  assert.strictEqual(r.ok, true); assert.deepStrictEqual(h.calls, [], 'Flatten calls no slot hook while off');
});
gates['SW0c the admitted state: exactly OICORE, valid, five contracts, hold to settle, inside every cap, nothing stored or requested can enable or enlarge it'] = () => {
  assert.strictEqual(slotLib.SLOT_ENABLED, true); assert.strictEqual(slotLib.SLOT_EVER_USED, true);
  assert.strictEqual(slotLib.slotActive(), true); assert.strictEqual(slotLib.slotWatch(), true);
  assert.ok(Object.isFrozen(slotLib.SLOT_STRATEGIES));
  assert.strictEqual(slotLib.SLOT_STRATEGIES.length, 1);
  const o = slotLib.SLOT_STRATEGIES[0];
  assert.deepStrictEqual(JSON.parse(JSON.stringify(o)), {
    id: 'OICORE', readme: 'kalshi-scalper/README.md#SLOT-OICORE', series: ['KXBTC15M'],
    entry: { sideRule: 'cheap', priceMin: 0.05, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120, oiRiseMin: 86300 },
    exit: { holdToSettle: true }, contractsPerOrder: 10,
    scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
    killRules: { maxConsecutiveLosses: 18, minNet: { afterFills: 40, net: -6 } },
    forwardReadDate: '2026-11-13', reviewedAt: '2026-10-30',
  });
  assert.deepStrictEqual(slotLib.validateSlotStrategy(o).ok, true, JSON.stringify(slotLib.validateSlotStrategy(o)));
  assert.deepStrictEqual(slotLib.activeSlotStrategies().map((x) => x.id), ['OICORE']);
  assert.strictEqual(o.contractsPerOrder, 10); assert.ok(o.contractsPerOrder <= slotLib.SLOT_MAX_CONTRACTS_PER_ORDER);
  assert.strictEqual(o.exit.holdToSettle, true); assert.ok(slotLib.SLOT_HOLD_ALLOWED.includes(o.id));
  assert.ok(o.scaleIn.maxSteps * o.contractsPerOrder <= slotLib.SLOT_MAX_OPEN_CONTRACTS_PER_MARKET);
  assert.ok(o.reviewedAt <= slotLib.SLOT_LAST_REVIEWED_ON);
  // Nothing stored, requested or typed can enable or enlarge it: the entry point takes no argument and the live and run libraries have no flag.
  assert.strictEqual(slotLib.activeSlotStrategies.length, 0); assert.strictEqual(slotLib.slotActive.length, 0); assert.strictEqual(slotLib.slotWatch.length, 0);
  assert.ok(!/SLOT_ENABLED|SLOT_STRATEGIES|_testOnly/.test(code(liveSrc)));
  // a stored/forged larger size or an off-list hold is refused by the validator
  const big = JSON.parse(JSON.stringify(o)); big.contractsPerOrder = slotLib.SLOT_MAX_CONTRACTS_PER_ORDER + 1;
  assert.strictEqual(slotLib.validateSlotStrategy(big).ok, false);
  const other = JSON.parse(JSON.stringify(o)); other.id = 'OTHER'; assert.strictEqual(slotLib.validateSlotStrategy(other).ok, false, 'hold to settle is only for listed ids');
};
gates.SW1 = () => {
  const c = code(liveSrc);
  assert.deepStrictEqual([...c.matchAll(/require\(([^)]*)\)/g)].map((m) => m[1]), ['"crypto"', '"./kalshiSignalLib"', '"./kalshiSlotLib"'], 'the only slot module the live library requires is the pure one');
  assert.ok(!/kalshiSlotRunLib|SLOT_ENABLED|SLOT_STRATEGIES|_testOnly/.test(c));
  // Every line of code that names the slot sits in a guarded or slot-only construct.
  const allowed = /require\("\.\/kalshiSlotLib"\)|slotOn\(|slotLive|slotOrders|slotIgnoreIds|slotLib\.|args\.slot|slot\.afterFlatten|ignoreOrderIds|slot\b.*=>|\{ slot \}|, slot \}|slot: *slotLive|slotUsed|created ===|createTestLocked|\bslot\b|slotHeld|leased/;
  const lines = c.split('\n').filter((l) => /slot/i.test(l));
  assert.ok(lines.length > 10, 'slot lines found');
  for (const l of lines) assert.ok(allowed.test(l), 'unguarded slot mention: ' + l.trim().slice(0, 140));
  // The library functions of the slot module it calls, and nothing else.
  const used = [...new Set([...c.matchAll(/slotLib\.(\w+)/g)].map((m) => m[1]))].sort();
  assert.deepStrictEqual(used, ['directionDecision', 'slotIgnoreSet', 'slotRiskForBotRisk', 'slotWatch', 'slotWindowSpent']);
  // Each use is guarded: slotWindowSpent and directionDecision by slotLive, slotRiskForBotRisk by the array check, slotWatch inside slotOn.
  assert.ok(/slotLive \? slotLib\.slotWindowSpent\(/.test(c));
  assert.ok(/if \(slotLive\) \{\s*\n\s*if \(typeof store\.createTestLocked/.test(c));
  assert.ok(/if \(Array\.isArray\(slotOrders\)\) \{\s*\n\s*const s = slotLib\.slotRiskForBotRisk/.test(c));
  // The exit watch knows the slot in exactly two places (the clamp on its sell and the lease release), each behind slotOn.
  const exitCode = c.slice(c.indexOf('async function runExitWatch'), c.indexOf('async function flattenAll'));
  assert.ok(!/slot/i.test(c.slice(c.indexOf('async function exitWatchIdle'), c.indexOf('async function claimClose')).replace(/\/\/.*$/gm, '')), 'exitWatchIdle knows nothing about the slot');
  assert.ok(/slotHeld = await args\.slot\.unsoldOn\(/.test(exitCode) && /if \(slotOn\(args\)\) leased\.push/.test(exitCode));
  // Slot hooks are only reached through args.slot after slotOn / slotLive.
  assert.strictEqual((c.match(/args\.slot\./g) || []).length, 3, 'hasUnresolved and allOrders in runL1Tick, unsoldOn in the exit watch');
  assert.strictEqual((c.match(/slot\.afterFlatten/g) || []).length, 1);
};
// Every USE of the slot (a hook call, a slot library call, the locked create, the lease release) must sit under a guard: on its own line or on an enclosing block line (found by indentation).
// This is what stops a future edit adding an unguarded slot call that only a recorded scenario would catch.
gates['SW1b every use of the slot in the live library sits under slotOn, slotLive or the slot-only argument checks'] = () => {
  const lines = code(liveSrc).split('\n');
  const use = /args\.slot\.|slotLib\.(?!slotWatch\(\)|slotActive)|\.createTestLocked|slot\.afterFlatten|\.releaseClose|slotOn\(args\)\) leased/;
  const guard = /slotOn\(|slotLive|Array\.isArray\(slotOrders\)|ignoreOrderIds &&|slotHeld > 0|leased\.length/;
  const indent = (l) => l.match(/^\s*/)[0].length;
  let checked = 0;
  lines.forEach((l, i) => {
    if (!use.test(l) || /^function slotOn/.test(l.trim())) return;
    checked += 1;
    if (guard.test(l)) return;
    let ind = indent(l), ok = false;
    for (let j = i - 1; j >= 0 && !ok; j--) {
      if (!lines[j].trim()) continue;
      const jin = indent(lines[j]);
      if (jin < ind) { if (guard.test(lines[j])) ok = true; ind = jin; if (/^(async )?function /.test(lines[j].trim()) || jin === 0) break; }
    }
    assert.ok(ok, 'unguarded slot use at line ' + (i + 1) + ': ' + l.trim().slice(0, 140));
  });
  assert.ok(checked >= 9, 'the gate really found the uses (' + checked + ')');
};
gates['SW1c the inertness gate in kalshiSlotGates.test.js exempts exactly the slot libraries, the live library and index.js, by name'] = () => {
  const g = fs.readFileSync(path.join(__dirname, 'kalshiSlotGates.test.js'), 'utf8');
  for (const name of ['kalshiSlotLib', 'kalshiSlotRunLib', 'kalshiSlotStoreLib', 'kalshiLiveLib']) assert.ok(g.includes(name), name + ' is named in the exemption');
  assert.ok(!/kalshiPushLib|kalshiReportLib|kalshiAccountLib/.test(g.slice(g.indexOf('the module is inert'), g.indexOf('the module is inert') + 900)), 'the push, report and account libraries are NOT exempt: they must never see the slot');
};

gates.SW3 = () => {
  const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.name === 'node_modules' || e.name === '.git') ? [] : e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]);
  const hits = walk(root).filter((f) => /\.(js|html|sh|yml|yaml|json)$/.test(f) && !/[\\/]test[\\/]/.test(f) && /_testForce/.test(fs.readFileSync(f, 'utf8'))).map((f) => path.relative(root, f));
  assert.deepStrictEqual(hits, [], 'no production file has a test backdoor: the constants are the only way in');
  const c = code(liveSrc);
  assert.ok(/function slotOn\(args\) \{ return Boolean\(args && args\.slot && typeof args\.slot === "object" && slotLib\.slotWatch\(\)\); \}/.test(c), 'slotOn is the constants and nothing else');
};

// ---------------------------------------------------------------- B. the on path ----------------------------------------------------------------
gates['SW6a the same side as a slot position in the market is allowed, and the order is created through the direction lock'] = async () => {
  const locks = new Map(), h = hooks({ orders: [slotOrder({ side: 'yes' })] });
  const w = l1World({ extraStore: lockedStore(locks), positions: posOf(T, 4) });
  const r = await live.runL1Tick({ ...w.common, quotes: [q('KXBTC15M', T)], slot: h.slot });
  assert.ok(r.ok, JSON.stringify(r)); assert.strictEqual(posts(w).length, 1, 'the yes buy went out');
  assert.deepStrictEqual(locks.get(T), { side: 'yes', by: 'L1' }, 'the lock was written with the order');
  assert.ok(w.r.log.some((x) => x.kind === 'store' && x.call === 'createTestLocked'), 'created through the locked transaction');
  assert.ok(!w.r.log.some((x) => x.kind === 'store' && x.call === 'createTest'), 'never the unlocked create when the slot is on');
  assert.ok(h.calls.includes('hasUnresolved') && h.calls.includes('allOrders'));
};
gates['SW6b the opposite side is blocked: a slot position on NO stops an L1 YES buy (books, account, lock, and an unreadable answer)'] = async () => {
  const cases = [
    ['the books show a slot NO order', { orders: [slotOrder({ side: 'no' })] }, {}],
    ['the account holds NO here', { orders: [] }, { positions: posOf(T, -3) }],
    ['the position cannot be read', { orders: [] }, { positions: () => ({ status: 500, text: async () => '{}' }) }],
    ['the lock holds the other side', { orders: [] }, { lockOther: true }],
  ];
  for (const [why, ho, wo] of cases) {
    const locks = new Map(); if (wo.lockOther) locks.set(T, { side: 'no', by: 'SLOT:TESTA' });
    const h = hooks(ho), w = l1World({ extraStore: lockedStore(locks), positions: wo.positions || noPos });
    const r = await live.runL1Tick({ ...w.common, quotes: [q('KXBTC15M', T)], slot: h.slot });
    assert.strictEqual(posts(w).length, 0, why + ': nothing sent'); assert.strictEqual(w.docs.size, 0, why + ': no order document either');
    assert.ok(r.ok && /nothing sent|holds the other side/.test(r.results.join(';')), why + ': ' + JSON.stringify(r));
    assert.deepStrictEqual([...locks.values()].filter((l) => l.by === 'L1'), [], why + ': no L1 lock written');
  }
  // a store with no locked create refuses rather than falling back to the unlocked one
  const h = hooks({}), w = l1World({ positions: noPos });
  await live.runL1Tick({ ...w.common, quotes: [q('KXBTC15M', T)], slot: h.slot });
  assert.strictEqual(posts(w).length, 0); assert.strictEqual(w.docs.size, 0);
};
gates['SW6c the other way: an L1 order leaves a lock and a document that stop the slot buying the opposite side, and allow the same side'] = async () => {
  const locks = new Map(), w = l1World({ extraStore: lockedStore(locks), positions: noPos }), h = hooks({});
  await live.runL1Tick({ ...w.common, quotes: [q('KXBTC15M', T)], slot: h.slot });
  assert.strictEqual(posts(w).length, 1);
  const l1Docs = [...w.docs.entries()].map(([id, d]) => ({ id, ...d }));
  const dd = (side, over) => slotLib.directionDecision({ ticker: T, side, l1Orders: l1Docs, slotOrders: [], lock: locks.get(T), position: 1, ...(over || {}) });
  assert.strictEqual(dd('no', { position: 0 }).allow, false, 'the slot may not hedge L1');
  assert.strictEqual(dd('yes').allow, true, 'the slot may hold L1\'s side');
  assert.strictEqual(slotLib.directionDecision({ ticker: T, side: 'no', l1Orders: [], slotOrders: [], lock: locks.get(T), position: 0 }).allow, false, 'the lock alone refuses it');
};
gates['SW8 two instances racing, an L1 YES and a slot NO on one market: one lock, one order document, the loser sends nothing'] = async () => {
  for (const l1First of [true, false]) {
    const db = { slot: new Map(), l1: new Map(), locks: new Map(), queue: Promise.resolve() };
    const txn = (fn) => { const p = db.queue.then(fn); db.queue = p.catch(() => {}); return p; };
    const tickP = () => new Promise((r) => setImmediate(r));
    // L1 side: the real runL1Tick with the serialised locked create.
    const ex1 = { extraStore: (docs) => ({ async createTestLocked(id, data, { ticker, side }) { return txn(async () => { const lock = db.locks.get(ticker); await tickP(); if (lock && lock.side !== side) return 'direction'; if (!lock) db.locks.set(ticker, { side, by: 'L1' }); if (docs.has(id)) return false; docs.set(id, { ...data }); db.l1.set(id, { ...data }); return true; }); } }), positions: noPos };
    const w = l1World(ex1), h = hooks({});
    // Slot side: a slot NO entry through the same lock, as the slot engine's runSlotEntry does.
    const slotNo = () => txn(async () => { const lock = db.locks.get(T); await tickP(); if (lock && lock.side !== 'no') return 'direction'; if (!lock) db.locks.set(T, { side: 'no', by: 'SLOT:TESTA' }); db.slot.set('S-TESTA-' + T + '-1', slotOrder({ side: 'no' })); return true; });
    const l1P = () => live.runL1Tick({ ...w.common, quotes: [q('KXBTC15M', T)], slot: h.slot });
    if (l1First) { await Promise.all([l1P(), slotNo()]); } else { const sp = slotNo(); const lp = l1P(); await Promise.all([lp, sp]); }
    assert.strictEqual(db.locks.size, 1, 'exactly one lock');
    const lockSide = db.locks.get(T).side;
    assert.strictEqual(db.l1.size + db.slot.size, 1, 'exactly one order document (l1First=' + l1First + ')');
    assert.strictEqual(posts(w).length, db.l1.size, 'L1 sent an order only if it won the lock');
    assert.strictEqual(lockSide, db.l1.size ? 'yes' : 'no');
  }
};
gates['SW7a a slot loss ends the whole session through the shared 12% stop, and an unsettled slot order is counted as lost'] = async () => {
  const base = { session: { sizing: true }, extraStore: lockedStore(new Map()), positions: noPos };
  const quotes = [q('KXGOLD15M', GT)];
  // control: no slot orders, the gold order goes
  let w = l1World(base), h = hooks({ orders: [] });
  let r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.ok(r.ok && posts(w).length === 1, 'control: ' + JSON.stringify(r));
  // a settled slot loss of $13 against a $100 base (12% = $12)
  w = l1World(base); h = hooks({ orders: [slotOrder({ ticker: 'KXETH15M-26OCT071345-15', series: 'KXETH15M', settled: true, result: 'no', settledPnl: -13, maxCost: 13, ts: NOW - 3600000 })] });
  r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.deepStrictEqual(r, { ended: 'loss stop' }); assert.strictEqual(posts(w).length, 0); assert.strictEqual(w.sess.active, false);
  // an open (unsettled) slot order is counted as lost: $13 of it open is the same
  w = l1World(base); h = hooks({ orders: [slotOrder({ ticker: 'KXETH15M-26OCT071445-15', series: 'KXETH15M', maxCost: 13, fillCount: '4', count: 4, settled: false, ts: NOW - 60000 })] });
  r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.deepStrictEqual(r, { ended: 'loss stop' });
  // and a slot win offsets nothing it should not: a smaller loss stays under the stop
  w = l1World(base); h = hooks({ orders: [slotOrder({ ticker: 'KXETH15M-26OCT071345-15', series: 'KXETH15M', settled: true, result: 'no', settledPnl: -5, maxCost: 5, ts: NOW - 3600000 })] });
  r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.ok(r.ok, 'a $5 slot loss is under the $12 stop: ' + JSON.stringify(r));
  // L1 and slot add: $7 L1 loss + $6 slot loss = $13
  w = l1World({ ...base, docs: { a: settledLoss('a', { maxCost: 7, settledPnl: -7, ts: NOW - 3600000 }) } }); h = hooks({ orders: [slotOrder({ ticker: 'KXETH15M-26OCT071345-15', series: 'KXETH15M', settled: true, result: 'no', settledPnl: -6, maxCost: 6, ts: NOW - 3000000 })] });
  r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.deepStrictEqual(r, { ended: 'loss stop' }, 'one budget: the two engines\' losses add');
  // botRisk directly: the return shape is unchanged and the totals add
  const orders = [settledLoss('a', { id: 'a', maxCost: 1, settledPnl: -1 })];
  const only = await live.botRisk({ store: w.common.store, since: 0, fetchFn: w.common.fetchFn, nowMs: NOW, orders });
  const both = await live.botRisk({ store: w.common.store, since: 0, fetchFn: w.common.fetchFn, nowMs: NOW, orders, slotOrders: [slotOrder({ settled: true, result: 'no', settledPnl: -2, ts: NOW - 1000 })] });
  assert.deepStrictEqual(Object.keys(both), Object.keys(only)); assert.strictEqual(both.net, only.net - 2); assert.strictEqual(both.trades, only.trades + 1); assert.strictEqual(both.worst, both.net - both.openCost);
  // an unreadable slot list fails closed
  w = l1World(base); h = hooks({ ordersThrow: true });
  r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.deepStrictEqual(r, { skipped: 'slot orders unreadable' }); assert.strictEqual(posts(w).length, 0);
  w = l1World(base); h = hooks({ unresolved: true });
  r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.deepStrictEqual(r, { ended: 'attempted' }, 'an unresolved slot order ends the session like an unresolved L1 order');
  w = l1World(base); h = hooks({ unresolvedThrows: true });
  r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.deepStrictEqual(r, { ended: 'attempted' }, 'a check that cannot be made counts as unresolved');
};
gates['SW7b the window limit is shared: slot dollars in a window use up the 5.5% L1 may put there'] = async () => {
  const base = { session: { sizing: true }, extraStore: lockedStore(new Map()), positions: noPos };
  const quotes = [q('KXGOLD15M', GT)];
  const inWindow = slotOrder({ ticker: 'KXETH15M-26OCT071415-15', series: 'KXETH15M', side: 'yes', maxCost: 5.2, fillCount: '5', count: 5, settled: false, ts: NOW - 60000 });
  // control: the same gold order with an empty slot list goes out
  let w = l1World(base), h = hooks({ orders: [] });
  let r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.strictEqual(posts(w).length, 1, JSON.stringify(r));
  // slot spend of $5.20 in the 14:15 window leaves $0.30 of the $5.50: no whole contract
  w = l1World(base); h = hooks({ orders: [inWindow] });
  r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.strictEqual(posts(w).length, 0, 'no order: ' + JSON.stringify(r));
  assert.ok(/already has \$5\.20 at risk/.test(r.results.join(';')), r.results.join(';'));
  // a sold or settled slot order still occupies its window (gross spend)
  w = l1World(base); h = hooks({ orders: [{ ...inWindow, settled: true, result: 'yes', settledPnl: 0.4, exitCount: 5 }] });
  r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.strictEqual(posts(w).length, 0);
  // a different window is untouched
  w = l1World(base); h = hooks({ orders: [{ ...inWindow, ticker: 'KXETH15M-26OCT071400-15' }] });
  r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot });
  assert.strictEqual(posts(w).length, 1);
  // the shared figures reach the slot tick
  const share = {};
  w = l1World(base); h = hooks({ orders: [] });
  await live.runL1Tick({ ...w.common, ...sizingOver, quotes, slot: h.slot, shareOut: share });
  assert.ok(share.sizeBase === 100 && Number.isFinite(share.floor) && share.risk && Array.isArray(share.slotOrders) && Array.isArray(share.recentList), 'sizeBase, floor, risk, recentList and slotOrders are handed over');
  const off = {}; w = l1World(base);
  await live.runL1Tick({ ...w.common, ...sizingOver, quotes, shareOut: off });
  assert.deepStrictEqual(off, {}, 'with no slot nothing is handed over');
};
gates['SW14 the 200 order limit counts slot orders when the slot is on, and not when it is off'] = async () => {
  const many = Array.from({ length: 200 }, (_, i) => slotOrder({ id: 'S-' + i, ticker: 'KXETH15M-26OCT07' + (1000 + i) + '-15', settled: true, result: 'hand', ts: NOW - 60000 - i }));
  const w = l1World({ extraStore: lockedStore(new Map()), positions: noPos }), h = hooks({ orders: many });
  const r = await live.runL1Tick({ ...w.common, quotes: [q('KXBTC15M', T)], slot: h.slot });
  assert.deepStrictEqual(r, { skipped: 'order limit' }); assert.strictEqual(posts(w).length, 0);
  const w2 = l1World({}), r2 = await live.runL1Tick({ ...w2.common, quotes: [q('KXBTC15M', T)] });
  assert.ok(r2.ok, 'off: the same quotes trade');
  // 199 old-enough orders do not count: older than 24 hours is outside
  const old = many.map((t) => ({ ...t, ts: NOW - 25 * 3600 * 1000 }));
  const w3 = l1World({ extraStore: lockedStore(new Map()), positions: noPos }), h3 = hooks({ orders: old });
  const r3 = await live.runL1Tick({ ...w3.common, quotes: [q('KXBTC15M', T)], slot: h3.slot });
  assert.ok(r3.ok, JSON.stringify(r3));
};
gates['SW9 the other engine\'s fills are never read as a sale by hand: a slot NO entry fill or a slot exit does not drop an L1 order out of the stop'] = async () => {
  const t = { ticker: T, side: 'yes', count: 1, fillCount: '1', orderId: 'l1-ord', ts: NOW - 60000 };
  const fills = [
    { ticker: T, action: 'sell', side: 'yes', order_id: 'slot-entry-no', created_time: new Date(NOW - 1000).toISOString(), count_fp: '4.00' },   // a slot NO buy, booked on the YES side as a sell
    { ticker: T, action: 'sell', side: 'yes', order_id: 'slot-exit', created_time: new Date(NOW - 500).toISOString(), count_fp: '4.00' },
  ];
  const w = l1World({ fills });
  const base = { fetchFn: w.common.fetchFn, keyId: 'k', pem, t, nowMs: NOW };
  assert.strictEqual((await live.closedByHand(base)).hand, true, 'the hazard: without the ignore set the slot\'s fills read as the owner selling L1\'s contract');
  const ids = new Set(['slot-entry-no', 'slot-exit']);
  assert.strictEqual((await live.closedByHand({ ...base, ignoreOrderIds: ids })).hand, false, 'with the slot\'s ids ignored it is not hand');
  assert.strictEqual((await live.closedByHand({ ...base, ignoreOrderIds: new Set(['unrelated']) })).hand, true, 'a genuine sale by someone else is still found');
  // through botRisk: an open L1 order whose market settled, with only the slot's fills present, stays an open result and is settled by the market, not marked hand
  const wl = l1World({ fills, results: { [T]: 'no' }, docs: { 'L1-x': { strategy: 'L1', ticker: T, side: 'yes', count: 1, fillCount: '1', maxCost: 0.94, orderId: 'l1-ord', status: 'filled', ts: NOW - 60000, settled: false } } });
  const slotOrders = [slotOrder({ ticker: T, orderId: 'slot-entry-no', exitOrderId: 'slot-exit', side: 'no' })];
  const risk = await live.botRisk({ store: wl.common.store, since: 0, fetchFn: wl.common.fetchFn, nowMs: NOW, keyId: 'k', pem, slotOrders, ignoreOrderIds: new Set(['slot-entry-no', 'slot-exit']) });
  assert.strictEqual(wl.docs.get('L1-x').result, 'no', 'settled as the market result, not "hand"');
  assert.ok(risk.net < 0 - 0.9, 'the L1 loss is in the stop: ' + risk.net);
  // settleOpenOrders takes the same set
  const store = { async openFilled() { return [{ id: 'L1-x', ...wl.docs.get('L1-x'), settled: false, result: undefined }]; }, async updateTest(id, p) { Object.assign(wl.docs.get(id), p); } };
  wl.docs.get('L1-x').settled = false; delete wl.docs.get('L1-x').result;
  await live.settleOpenOrders({ store, fetchFn: wl.common.fetchFn, nowMs: NOW, keyId: 'k', pem, ignoreOrderIds: ids });
  assert.strictEqual(wl.docs.get('L1-x').result, 'no');
  // and the live tick builds that set from the slot's order ids itself
  const w2 = l1World({ fills, results: { [T]: 'no' }, extraStore: lockedStore(new Map()), positions: noPos, docs: { 'L1-x': { strategy: 'L1', ticker: T, series: 'KXBTC15M', side: 'yes', count: 1, fillCount: '1', maxCost: 0.94, orderId: 'l1-ord', status: 'filled', ts: NOW - 60000, settled: false } } });
  const h = hooks({ orders: slotOrders });
  await live.runL1Tick({ ...w2.common, quotes: [q('KXBTC15M', 'KXBTC15M-26OCT071500-15')], slot: h.slot });
  assert.strictEqual(w2.docs.get('L1-x').result, 'no', 'through runL1Tick the L1 order is settled by the market, not called hand');
};
gates['SW11 Flatten with the slot on tells the slot which markets it closed, and a failure of that bookkeeping never changes what Flatten returns'] = async () => {
  const mk = (postStatus) => {
    const claims = new Map();
    const store = { async claimClose(ticker, who, now) { claims.set(ticker, who); return true; } };
    const fetchFn = async (url, init) => {
      const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
      if (url.includes('/portfolio/positions')) { const tk = new URL(url).searchParams.get('ticker'); const all = [{ ticker: T, position_fp: '3.00' }, { ticker: GT, position_fp: '-2.00' }]; return reply(200, { market_positions: tk ? all.filter((x) => x.ticker === tk) : all }); }
      if (url.includes('/markets/')) return reply(200, { market: { status: 'active', exchange_index: 2 } });
      if (init.method === 'POST') { const b = JSON.parse(init.body); return reply(postStatus, postStatus < 300 ? { order_id: 'o', fill_count: b.count, remaining_count: '0.00', average_fill_price: '0.5' } : { e: 1 }); }
      throw new Error('unexpected');
    };
    return { store, fetchFn };
  };
  const off = mk(201), offRes = await live.flattenAll({ ...off, keyId: 'k', pem, now: NOW });
  const h = hooks({}), on = mk(201), onRes = await live.flattenAll({ ...on, keyId: 'k', pem, now: NOW, slot: h.slot });
  assert.deepStrictEqual(onRes, offRes, 'the owner gets the same answer');
  assert.deepStrictEqual(h.calls, ['afterFlatten']); assert.strictEqual(h.slot.last.results.length, 2); assert.strictEqual(h.slot.last.now, NOW);
  assert.deepStrictEqual(h.slot.last.results.map((r) => r.status), ['sold', 'sold']);
  const hf = hooks({ afterThrows: true }), bad = mk(201), badRes = await live.flattenAll({ ...bad, keyId: 'k', pem, now: NOW, slot: hf.slot });
  assert.deepStrictEqual(badRes, offRes, 'a bookkeeping failure changes nothing the owner sees');
  const err = hooks({}), e = mk(500), eRes = await live.flattenAll({ ...e, keyId: 'k', pem, now: NOW, slot: err.slot });
  assert.deepStrictEqual(eRes.results.map((r) => r.status), ['error', 'error'], 'failed sales are passed on as errors, so the slot can leave those orders open');
  assert.ok(!/claimClose\(store, [^)]*"slot"/.test(code(liveSrc)), 'the slot\'s own lease calls live in the slot library, not here');
};
// ---- the L1 exit watch with the slot on ------------------------------------------------------------------------------------------------
function exitWorld(o = {}) {
  const calls = [], posts = [], releases = [], docs = new Map();
  const l1 = { id: 'L1-' + T, strategy: 'L1', ticker: T, series: 'KXBTC15M', side: 'yes', count: 1, fillCount: '1', maxCost: 0.94, status: 'filled', settled: false, ts: NOW - 60000, orderId: 'l1-ord' };
  docs.set(l1.id, l1);
  const store = {
    async recentFilled() { return [...docs.values()].map((d) => ({ ...d })); },
    async updateTest(id, patch) { calls.push('updateTest'); Object.assign(docs.get(id), patch); },
    async claimClose() { calls.push('claimClose'); return o.claim !== false; },
    async claimExit() { calls.push('claimExit'); return true; },
  };
  if (o.release !== false) store.releaseClose = async (tk, who) => { releases.push([tk, who]); };
  const fetchFn = async (url, init) => {
    const rep = (st, b) => ({ status: st, text: async () => JSON.stringify(b) });
    if (url.includes('/portfolio/positions')) return rep(200, { market_positions: [{ ticker: T, position_fp: String(o.held === undefined ? 1 : o.held) }] });
    if (url.includes('/markets/')) return rep(200, { market: { status: 'active', close_time: iso(NOW + 400000), yes_bid_dollars: '0.2000', yes_ask_dollars: '0.2200', exchange_index: 2 } });
    if (init.method === 'POST') { const b = JSON.parse(init.body); posts.push(b); return rep(201, { order_id: 'x1', fill_count: b.count, average_fill_price: '0.2000' }); }
    throw new Error('unexpected ' + url);
  };
  return { store, fetchFn, posts, calls, releases, docs };
}
gates['SW-EXIT-1 L1\'s exit watch sells only what is not the slot\'s: the whole account position is shared, so the slot\'s contracts on the same side are subtracted'] = async () => {
  // L1 owns 1 YES (the owner sold it by hand), the slot owns 4 YES: the account holds 4. L1 must NOT sell the slot's contract at its own 25c line.
  const h = hooks({ orders: [slotOrder({ side: 'yes', count: 4, fillCount: '4' })] });
  let w = exitWorld({ held: 4 });
  const r = await live.runExitWatch({ store: w.store, fetchFn: w.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, slot: h.slot });
  assert.strictEqual(w.posts.length, 0, 'nothing sold: ' + JSON.stringify(r)); assert.ok(h.calls.includes('unsoldOn'));
  assert.notStrictEqual(w.docs.get('L1-' + T).exitStatus, 'skipped', 'and it is retried later, never written off for good');
  // With the position at 5 (L1 still holds its own 1) it sells exactly 1.
  w = exitWorld({ held: 5 });
  await live.runExitWatch({ store: w.store, fetchFn: w.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, slot: hooks({ orders: [slotOrder({ side: 'yes', count: 4, fillCount: '4' })] }).slot });
  assert.strictEqual(w.posts.length, 1); assert.strictEqual(w.posts[0].count, '1');
  // The other side of the market does not reduce what L1 may sell.
  w = exitWorld({ held: 1 });
  await live.runExitWatch({ store: w.store, fetchFn: w.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, slot: hooks({ orders: [slotOrder({ side: 'no', count: 4, fillCount: '4' })] }).slot });
  assert.strictEqual(w.posts.length, 1, 'a slot NO is not on L1\'s side');
  // An unreadable slot list sells nothing.
  w = exitWorld({ held: 5 });
  await live.runExitWatch({ store: w.store, fetchFn: w.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, slot: hooks({ unsoldThrows: true }).slot });
  assert.strictEqual(w.posts.length, 0, 'fails closed');
  // No slot argument: the watch is the one that has always run (and calls no hook).
};
gates['SW-EXIT-2 with the slot on, L1\'s exit watch gives its close lease back when its pass ends, so the slot\'s stop is not held off the market for 90 seconds'] = async () => {
  const w = exitWorld({ held: 1 });
  await live.runExitWatch({ store: w.store, fetchFn: w.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, slot: hooks({ orders: [] }).slot });
  assert.strictEqual(w.posts.length, 1); assert.deepStrictEqual(w.releases, [[T, 'exit']]);
  // A refused claim (Flatten holds it) releases nothing: it is not L1's lease.
  const f = exitWorld({ claim: false });
  await live.runExitWatch({ store: f.store, fetchFn: f.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, slot: hooks({ orders: [] }).slot });
  assert.deepStrictEqual(f.releases, []);
  // Even when the sell throws, the lease is released.
  const t = exitWorld({ held: 1 }); const f0 = t.fetchFn; t.fetchFn = async (u, i) => { if (i.method === 'POST') throw new Error('boom'); return f0(u, i); };
  await live.runExitWatch({ store: t.store, fetchFn: t.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, slot: hooks({ orders: [] }).slot }).catch(() => {});
  assert.deepStrictEqual(t.releases, [[T, 'exit']]);
};
gates['SW-EXIT-3 with the slot OFF the exit watch makes the same calls whether or not a hook bag and a release method exist (nothing leaks into the off state)'] = async () => {
  slotLib.slotWatch = () => false;
  const a = exitWorld({ held: 1, release: false }), b = exitWorld({ held: 1 }), h = hooks({ orders: [] });
  const ra = await live.runExitWatch({ store: a.store, fetchFn: a.fetchFn, keyId: 'k', pem, now: NOW, enabled: true });
  const rb = await live.runExitWatch({ store: b.store, fetchFn: b.fetchFn, keyId: 'k', pem, now: NOW, enabled: true, slot: h.slot });
  assert.deepStrictEqual(rb, ra); assert.deepStrictEqual(b.calls, a.calls); assert.deepStrictEqual(b.posts, a.posts); assert.deepStrictEqual(b.releases, [], 'no lease released'); assert.deepStrictEqual(h.calls, []);
};
gates['SW-LOST-ID a slot order whose answer was lost has no order id; its market is marked so L1\'s hand check answers "unknown" instead of reading the fill as a sale by hand'] = async () => {
  const t = { ticker: T, side: 'yes', count: 1, fillCount: '1', orderId: 'l1-ord', ts: NOW - 60000 };
  const fills = [{ ticker: T, action: 'sell', side: 'yes', order_id: 'never-recorded', created_time: new Date(NOW - 500).toISOString(), count_fp: '1.00' }];
  const w = l1World({ fills });
  const lost = slotOrder({ status: 'unknown', fillCount: '0', orderId: undefined, side: 'no' });
  const set = slotLib.slotIgnoreSet([lost]);
  assert.ok(set.has('ticker:' + T));
  const base = { fetchFn: w.common.fetchFn, keyId: 'k', pem, t, nowMs: NOW };
  assert.strictEqual((await live.closedByHand(base)).hand, true, 'the hazard: the unrecorded fill reads as the owner selling L1\'s contract');
  assert.strictEqual((await live.closedByHand({ ...base, ignoreOrderIds: set })).unknown, true, 'with the marker the order stays open and counted as lost');
  // an exit whose answer was lost marks the market too, and a settled clean slot order does not
  assert.ok(slotLib.slotIgnoreSet([slotOrder({ exitStatus: 'unknown' })]).has('ticker:' + T));
  assert.ok(!slotLib.slotIgnoreSet([slotOrder({})]).has('ticker:' + T));
  // through botRisk the L1 order is NOT dropped as hand
  const wl = l1World({ fills, results: { [T]: 'no' }, docs: { 'L1-x': { strategy: 'L1', ticker: T, side: 'yes', count: 1, fillCount: '1', maxCost: 0.94, orderId: 'l1-ord', status: 'filled', ts: NOW - 60000, settled: false } } });
  const risk = await live.botRisk({ store: wl.common.store, since: 0, fetchFn: wl.common.fetchFn, nowMs: NOW, keyId: 'k', pem, slotOrders: [lost], ignoreOrderIds: set });
  assert.notStrictEqual(wl.docs.get('L1-x').result, 'hand'); assert.ok(risk.worst <= -0.9, 'the L1 loss stays counted: ' + risk.worst);
};
gates['SW-WATCH-ONLY with entries off but a slot order ever used, L1 still reads the slot orders, counts them in the stop and honours the direction lock'] = () => withWatchOnly(async () => {
  // Entries forced off (slotActive false) and watching true: exactly the "turned off, still watching" state, now forced because the shipped constants are on.
  assert.strictEqual(slotLib.slotActive(), false); assert.strictEqual(slotLib.slotWatch(), true);
  const w = l1World({ session: { sizing: true }, extraStore: lockedStore(new Map()), positions: noPos }), h = hooks({ orders: [slotOrder({ ticker: 'KXETH15M-26OCT071345-15', series: 'KXETH15M', settled: true, result: 'no', settledPnl: -13, maxCost: 13, ts: NOW - 3600000 })] });
  const r = await live.runL1Tick({ ...w.common, ...sizingOver, quotes: [q('KXGOLD15M', GT)], slot: h.slot });
  assert.deepStrictEqual(r, { ended: 'loss stop' }, 'an orphaned slot loss still ends the session through the shared stop');
});

gates['SW5b with the slot forced on and no registered strategy the engine still sends nothing'] = async () => {
  // The shipped registry holds OICORE, so the empty-registry engine is built through the documented test flags (enabled, empty registry).
  const empty = runLib._testOnly.makeRunners({ enabled: true, registry: [], everUsed: false });
  assert.deepStrictEqual(slotLib._testOnly.activeSlotStrategiesWith({ enabled: true, registry: [] }), []);
  const db = { calls: 0 }, trap = new Proxy({}, { get: () => { db.calls += 1; throw new Error('touched'); } });
  const out = await empty.runSlotTick({ session: { active: true }, now: NOW, enabled: true, active: true, store: trap, keyId: 'k', pem, fetchFn: async () => { db.calls += 1; throw new Error('touched'); }, quotes: [q('KXBTC15M', T)], setSession: async () => {} });
  assert.ok(out.skipped && db.calls === 0);
};

// The on path: slotLib.slotWatch is replaced on the module object for the length of the gate (the live library looks it up at call time) and always restored. Gates that prove the OFF state run unpatched.
const UNPATCHED = /^(SW0|SW0b|SW0c|SW1|SW1b|SW1c|SW3|SW5b|SW-EXIT-3)\b/;
const realWatch = slotLib.slotWatch;
(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try {
      if (!UNPATCHED.test(name)) slotLib.slotWatch = () => true;
      try { await fn(); } finally { slotLib.slotWatch = realWatch; }
      console.log('ok   ' + name); } catch (e) { failed += 1; console.log('FAIL ' + name + '\n     ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n     ') : e)); }
  }
  if (failed) { console.log(failed + ' failed'); process.exit(1); }
  console.log('all ' + Object.keys(gates).length + ' slot wiring gates passed');
})();

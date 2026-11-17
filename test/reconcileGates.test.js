const fs = require('fs'), assert = require('assert');
const lib = require('../functions/kalshiReconcileLib');
const probe = require('../functions/kalshiPerpsProbeLib');
const push = require('../functions/kalshiPushLib');
const report = require('../functions/kalshiReportLib');
const slot = require('../functions/kalshiSlotLib');

const NOV17 = Date.parse('2026-11-17T12:00:00Z'), OCT20 = Date.parse('2026-10-20T12:00:00Z');
const gold = (ts, count) => ({ ts, ticker: 'KXGOLD15M-26NOV171300-30', count, fillCount: count });

// RC1: check 4, contracts against the cap in force at the order's own time (the gold trial seat is 3 contracts from its start, the ceiling before)
let r = lib.checkContracts([gold(NOV17, 3), gold(NOV17, 4), gold(OCT20, 4)], []);
assert.strictEqual(r.findings.length, 1, 'only the order above the trial cap is a finding');
assert.deepStrictEqual([r.findings[0].who, r.findings[0].count, r.findings[0].max], ['L1 KXGOLD15M', 4, 3]);
assert.strictEqual(r.checked, 3);
// a series off the list is skipped (not a finding), and a Dogecoin order before its removal date is history
r = lib.checkContracts([{ ts: NOV17, ticker: 'KXFOO15M-X', count: 99 }, { ts: Date.parse('2026-11-01T00:00:00Z'), ticker: 'KXDOGE15M-26NOV011300-30', count: 20 }, { ts: NOV17, ticker: 'KXDOGE15M-26NOV171300-30', count: 1 }], []);
assert.deepStrictEqual([r.findings.length, r.skipped, r.checked], [1, 2, 1], 'a Dogecoin order after Nov 9 is oversize (the lock is 0); the older one and the unknown series are skipped');

// RC2: slot orders: a laddered strategy is held to the ladder ceiling, the others to their registry size; an id the registry no longer has is skipped, never a finding
const ids = slot.SLOT_STRATEGIES.map((s) => s.id);
assert(ids.includes('OICORE'));
assert.strictEqual(lib.slotCeiling('OICORE'), slot.SLOT_LADDER_MAX_CONTRACTS);
const plain = slot.SLOT_STRATEGIES.find((s) => !slot.SLOT_LADDERS[s.id]);
assert.strictEqual(lib.slotCeiling(plain.id), Math.min(plain.contractsPerOrder, slot.SLOT_MAX_CONTRACTS_PER_ORDER));
// RC2b: the library keeps a COPY of the slot ceilings (a gate stops it importing the slot library); it must equal the registry's, strategy for strategy, or this fails
const expected = {}; for (const s of slot.SLOT_STRATEGIES) expected[s.id] = slot.SLOT_LADDERS[s.id] ? slot.SLOT_LADDER_MAX_CONTRACTS : Math.min(s.contractsPerOrder, slot.SLOT_MAX_CONTRACTS_PER_ORDER);
assert.deepStrictEqual(Object.assign({}, lib.SLOT_CEILINGS), expected, 'RC2b the ceiling table matches the slot registry');
assert.strictEqual(lib.slotCeiling('GONE1'), null);
r = lib.checkContracts([], [{ ts: NOV17, slotId: 'OICORE', count: 20 }, { ts: NOV17, slotId: 'OICORE', count: 31 }, { ts: NOV17, slotId: plain.id, count: lib.slotCeiling(plain.id) + 1 }, { ts: NOV17, slotId: 'GONE1', count: 99 }]);
assert.deepStrictEqual(r.findings.map((f) => f.who).sort(), ['OICORE', plain.id].sort());
assert.strictEqual(r.skipped, 1);

// RC3: check 3, perps. The account read is Kalshi's own; an open position must agree with the last event of its market
const T = 1700000000000, M = 60000;
const doc = (rows, ok = true, at = T) => ({ at, positionsOk: ok, rows });
const row = (market, size, up = true) => ({ market, size, up });
const ev = (market, kind, size, up = true, at = T - M) => ({ market, kind, size, up, at });
let p = lib.checkPerps(doc([row('KXA', 2)]), [ev('KXA', 'opened', 2)], T);
assert.deepStrictEqual([p.findings.length, p.checked], [0, 1], 'agreeing is clean');
p = lib.checkPerps(doc([row('KXA', 3)]), [ev('KXA', 'opened', 2)], T);
assert.strictEqual(p.findings.length, 1, 'size differs');
p = lib.checkPerps(doc([row('KXA', 2, false)]), [ev('KXA', 'opened', 2, true)], T);
assert.strictEqual(p.findings.length, 1, 'direction differs');
p = lib.checkPerps(doc([row('KXA', 2)]), [ev('KXA', 'opened', 2, true, T - 3 * M), ev('KXA', 'closed', 0, true, T - M)], T);
assert.strictEqual(p.findings.length, 1, 'the newest event is a close but the account still holds it');
p = lib.checkPerps(doc([]), [ev('KXB', 'opened', 5)], T);
assert.strictEqual(p.findings.length, 1, 'an open event with no position in the account read');
p = lib.checkPerps(doc([]), [ev('KXB', 'opened', 5, true, T - 3 * M), ev('KXB', 'closed', 0, true, T - M)], T);
assert.strictEqual(p.findings.length, 0, 'closed then gone is clean');
// an event AFTER the read is not the read's business; a position with no event at all is "not checked", not a mismatch
p = lib.checkPerps(doc([row('KXA', 2)]), [ev('KXA', 'closed', 0, true, T + M)], T);
assert.strictEqual(p.findings.length, 0);
p = lib.checkPerps(doc([row('KXOLD', 4)]), [], T);
assert.deepStrictEqual([p.findings.length, p.checked, p.notChecked.length], [0, 0, 1]);
// a missing, answer-less or old read is "not checked", never a finding
for (const bad of [null, {}, doc([row('KXA', 2)], false), doc([row('KXA', 2)], true, T - 31 * M)]) { p = lib.checkPerps(bad, [ev('KXA', 'closed', 0)], T); assert.strictEqual(p.findings.length, 0); assert.strictEqual(p.notChecked.length, 1); }

// RC4: the verdict and its first line. The two checks that need Kalshi's own records are ALWAYS listed as not checked
let rec = lib.reconcile({ now: T, l1Orders: [gold(NOV17, 3)], slotOrders: [], perpsDoc: doc([row('KXA', 2)]), events: [ev('KXA', 'opened', 2)] });
assert.strictEqual(rec.ok, true);
assert(/^RECONCILE OK/.test(rec.line) && /NOT checked: P&L and balance/.test(rec.line));
assert(rec.notChecked.length >= 2 && rec.notChecked.some((s) => /fills and settlements/.test(s)) && rec.notChecked.some((s) => /transfer/.test(s)));
rec = lib.reconcile({ now: NOV17, l1Orders: [gold(NOV17, 9)], slotOrders: [], perpsDoc: null, events: [] });
assert.strictEqual(rec.ok, false);
assert(/^RECONCILE MISMATCH: 1 finding/.test(rec.line) && /L1 KXGOLD15M 9 contracts, cap 3/.test(rec.line));
const many = []; for (let i = 0; i < 50; i++) many.push(gold(NOV17 + i, 9));
assert.strictEqual(lib.reconcile({ now: NOV17, l1Orders: many, slotOrders: [], perpsDoc: null, events: [] }).findings.length, lib.MAX_FINDINGS, 'the stored list is bounded');

(async () => {
  // RC5: one alert at most a day; a clean or missing result sends nothing and claims nothing; a failed raise puts the old time back; errors are swallowed
  const calls = [];
  const io = (prev) => ({ claim: async (...a) => { calls.push(['claim', ...a]); return prev; }, release: async (...a) => calls.push(['release', ...a]), raise: async (a) => calls.push(['raise', a]) });
  assert.strictEqual(await lib.runReconcileAlert({ now: 1, rec: { ok: true }, ...io(null) }), 'none');
  assert.strictEqual(await lib.runReconcileAlert({ now: 1, rec: null, ...io(null) }), 'none');
  assert.deepStrictEqual(calls, []);
  const bad = lib.reconcile({ now: NOV17, l1Orders: [gold(NOV17, 9)], slotOrders: [], perpsDoc: null, events: [] });
  assert.strictEqual(await lib.runReconcileAlert({ now: 5000, rec: bad, ...io(null) }), 'alerted');
  assert.deepStrictEqual(calls[1], ['raise', { at: 5000, count: 1, first: 'L1 KXGOLD15M', check: 'contracts' }]);
  calls.length = 0;
  assert.strictEqual(await lib.runReconcileAlert({ now: 5000, rec: bad, ...io(false) }), 'already alerted');
  assert.deepStrictEqual(calls.map((c) => c[0]), ['claim']);
  calls.length = 0;
  assert.strictEqual(await lib.runReconcileAlert({ now: 5000, rec: bad, claim: async () => 777, release: io().release, raise: async () => { throw new Error('x'); } }), 'alert failed');
  assert.deepStrictEqual(calls, [['release', 777]]);
  assert.ok(/^error/.test(await lib.runReconcileAlert({ now: 1, rec: bad, claim: async () => { throw new Error('boom'); }, release: io().release, raise: io().raise })));
  assert.strictEqual(lib.ALERT_COOLDOWN_MS, 20 * 3600000);

  // RC6: the phone alert fires only on a CHANGED stamp, with no session needed, and its words say nothing was changed
  assert.deepStrictEqual(push.sessionKinds({ active: false }, { active: false, reconcileAlert: { at: 5 } }), ['reconcile']);
  assert.deepStrictEqual(push.sessionKinds({ reconcileAlert: { at: 5 } }, { reconcileAlert: { at: 5 } }), []);
  const m = push.message('reconcile', { reconcileAlert: { count: 2, first: 'L1 KXGOLD15M' } });
  assert(/reconciliation found a mismatch \(2\)/.test(m.title) && /First: L1 KXGOLD15M/.test(m.body) && /only reports/.test(m.body) && m.tag === 'issue-reconcile');

  // RC7: the report prints the stored line FIRST; a missing result says so; an old one never reads as OK
  const mk = (rc) => { let out; const h = report.makeReportHandler({ getToken: () => 'x'.repeat(30), now: () => NOV17, readOrders: async () => [], readReconcile: async () => rc, readPortfolioProbe: async () => ({ at: 1, results: { '/portfolio/fills': { status: 200, fields: ['fills[].count'] } } }) }); return h({ method: 'GET', headers: { authorization: 'Bearer ' + 'x'.repeat(30) }, query: {} }, { set() {}, status() { return this; }, json(o) { out = o; } }).then(() => out); };
  let o = await mk(null);
  assert.strictEqual(Object.keys(o)[0], 'reconcileLine'); assert(/^RECONCILE NOT RUN/.test(o.reconcileLine)); assert.strictEqual(o.reconcile, undefined);
  o = await mk(rec);   // rec was computed at NOV17 time T above? use a fresh one below
  o = await mk(Object.assign({}, bad, { at: NOV17 - 60000 }));
  assert(/^RECONCILE MISMATCH/.test(o.reconcileLine) && o.reconcile.findingCount === 1 && o.reconcile.findings[0].who === 'L1 KXGOLD15M');
  o = await mk(Object.assign({}, bad, { ok: true, line: 'RECONCILE OK, all fine', at: NOV17 - 37 * 3600000 }));
  assert(/^RECONCILE STALE/.test(o.reconcileLine), 'an old OK is stale, never OK');
  assert.strictEqual(o.portfolioProbe.results['/portfolio/fills'].status, 200);

  // RC8: the portfolio probe keeps status and field NAMES only: GET, no retry, no value, every route answered or not
  assert(probe.PORTFOLIO_PROBES.length >= 8 && probe.PORTFOLIO_PROBES.every((x) => /^\/(portfolio|margin)\//.test(x.path)));
  const seen = [];
  const out = await probe.runPortfolioProbe({ now: 9, liveRequest: async (a) => { seen.push(a); return a.path === '/portfolio/fills' ? { status: 200, body: { fills: [{ count: 7, price: '0.5', trade_id: 'SECRET' }], cursor: 'abc' } } : { status: 404, body: { error: 'nope' } }; } });
  assert(seen.every((a) => a.method === 'GET' && a.noRetry === true));
  assert.deepStrictEqual(out.results['/portfolio/fills'].fields.sort(), ['cursor', 'fills', 'fills[].count', 'fills[].price', 'fills[].trade_id'].sort());
  assert(!JSON.stringify(out).includes('SECRET') && !JSON.stringify(out).includes('"7"') && !/0\.5/.test(JSON.stringify(out)), 'no value is ever stored');
  assert.strictEqual(out.results['/portfolio/deposits'].status, 404);
  const thrown = await probe.runPortfolioProbe({ now: 9, liveRequest: async () => { throw new Error('boom'); } });
  assert(Object.values(thrown.results).every((x) => x.status === 0 && x.fields.length === 0), 'a throwing route is a 0, never a crash');

  // RC9: wiring. The library is pure; the server block runs inside the existing hourly snapshot function in one fenced try, reads only, and makes no Kalshi request
  const src = fs.readFileSync(__dirname + '/../functions/kalshiReconcileLib.js', 'utf8').split('\n').filter((l) => !/^\s*\/\//.test(l)).join('\n');
  assert(!/fetch|liveRequest|getFirestore|signature|POST|setTimeout|Date\.now|Math\.random/.test(src), 'RC9 pure: no I/O, clock or randomness');
  const idx = fs.readFileSync(__dirname + '/../functions/index.js', 'utf8');
  const a = idx.indexOf('exports.kalshiBalanceSnapshot'), b = idx.indexOf('exports.kalshiPerpsProbe');
  const block = idx.slice(a, b);
  assert(/getUTCHours\(\) === reconcileLib\.RECONCILE_HOUR_UTC/.test(block) && /reconcileRun\.runReconcileNightly\(/.test(block) && /try \{/.test(block) && /reconcile failed/.test(block), 'RC9 once a day, fenced');
  assert(block.indexOf('runBalanceSnapshot') < block.indexOf('reconcileRun.runReconcileNightly('), 'RC9 after the balance snapshot, so it can never delay it');
  const runSrc = fs.readFileSync(__dirname + '/../functions/kalshiReconcileRunLib.js', 'utf8').split('\n').filter((l) => !/^\s*\/\//.test(l)).join('\n');
  assert(!/fetch|liveRequest|signature|POST|\.delete\(|\.update\(/.test(runSrc), 'RC9 the Firestore side makes no Kalshi request and deletes nothing');

  // RC10: the Firestore side, on a fake database: it reads, stores the result, and alerts once on a mismatch
  const store = {}, sets = [];
  const docRef = (path) => ({ get: async () => ({ exists: path in store, data: () => store[path] }), set: async (v, o) => { sets.push([path, v]); store[path] = Object.assign(o && o.merge ? store[path] || {} : {}, v); } });
  const data = { kalshiLiveOrders: [{ ts: NOV17 - 1000, ticker: 'KXGOLD15M-26NOV171300-30', count: 9, fillCount: 9 }], kalshiSlotOrders: [], kalshiPerpsEvents: [] };
  const fakeDb = { collection: (n) => ({ where: () => ({ limit: () => ({ get: async () => ({ docs: (data[n] || []).map((x) => ({ data: () => x })) }) }) }), orderBy: () => ({ limit: () => ({ get: async () => ({ docs: [] }) }) }), doc: (id) => docRef(n + '/' + id) }), runTransaction: async (fn) => fn({ get: async (ref) => ref.get(), set: (ref, v) => ref.set(v, { merge: true }) }) };
  const perpsRef = { get: async () => ({ exists: false }) };
  const run = require('../functions/kalshiReconcileRunLib');
  let note = await run.runReconcileNightly({ db: fakeDb, now: NOV17, perpsRef });
  assert(/reconcile 1 finding\(s\); alert alerted/.test(note), note);
  assert(store['kalshiLiveControl/reconcile'].findingCount === 1 && store['kalshiLiveControl/session'].reconcileAlert.count === 1);
  note = await run.runReconcileNightly({ db: fakeDb, now: NOV17 + 3600000, perpsRef });
  assert(/alert already alerted/.test(note), 'a second run the same day does not alert again: ' + note);
  data.kalshiLiveOrders = [];
  note = await run.runReconcileNightly({ db: fakeDb, now: NOV17 + 25 * 3600000, perpsRef });
  assert(/reconcile ok; alert none/.test(note), note);
  assert(/^reconcile failed/.test(await run.runReconcileNightly({ db: { collection: () => { throw new Error('boom'); } }, now: 1, perpsRef })));
  const rb = block.slice(block.indexOf('reconcileLib.RECONCILE_HOUR_UTC'));
  assert(!/liveRequest|fetchFn|fetch\(/.test(rb), 'RC9 no Kalshi request in the reconciliation block');
  assert(!/exports\.kalshiReconcile/.test(idx), 'RC9 no new function');
  assert.strictEqual(lib.RECONCILE_HOUR_UTC, 5);
  // nothing that decides a trade reads the reconciliation or its probe
  for (const f of ['kalshiLiveLib', 'kalshiSlotLib', 'kalshiSlotRunLib', 'kalshiRiskCoreLib', 'kalshiHardStopLib', 'kalshiGoldKillLib', 'kalshiShadowLib']) {
    const t = fs.readFileSync(__dirname + '/../functions/' + f + '.js', 'utf8');
    assert(!/kalshiReconcileLib|reconcileAlert|portfolioProbe/.test(t), 'RC9 ' + f + ' does not read the reconciliation');
  }
  console.log('reconcileGates ok');
})().catch((e) => { console.error(e); process.exit(1); });

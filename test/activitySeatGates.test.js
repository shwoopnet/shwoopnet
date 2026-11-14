'use strict';
// Gates for activity seats, built INERT (functions/kalshiActivityLib.js, docs/ACTIVITY_SEATS.md). Each states the consequence: with no seat registered nothing changes,
// and once a seat exists no order can pass a weekly, daily or profit factor stop. All money figures are INVENTED, test only.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const act = require('../functions/kalshiActivityLib');
const slot = require('../functions/kalshiSlotLib');
const bot = require('../functions/kalshiSignalLib');

const root = path.join(__dirname, '..');
const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? (e.name === 'node_modules' ? [] : walk(path.join(d, e.name))) : [path.join(d, e.name)]);
const read = slot.accountOrder;
const gates = {};

const seat = (o) => Object.assign({ id: 'ACTA', familyId: 'cheap-side-demo', readme: 'docs/ACTIVITY_SEATS.md#acta', series: ['KXBTC15M'],
  entry: { priceMin: 0.05, priceMax: 0.5 }, contractsPerOrder: 3, ioc: true, reviewedAt: '2026-11-14' }, o || {});
const SEATS = [seat(), seat({ id: 'ACTB' }), seat({ id: 'ACTC' })];
const T = 'KXBTC15M-26NOV161015-15';
// A settled slot order with an invented cash result.
let n = 0;
const ord = (id, ts, net, extra) => Object.assign({ strategy: 'SLOT', slotId: id, ticker: T, side: 'yes', count: 3, fillCount: 3, status: 'filled', maxCost: 1, ts, settledAt: ts + 900e3,
  settled: true, result: net > 0 ? 'yes' : 'no', settledPnl: net, step: 1, cid: 'o' + (n++) }, extra || {});
const chk = (o) => act.activityOrderCheck(Object.assign({ seatId: 'ACTA', count: 3, limit: 0.8, slotOrders: [], now: Date.parse('2026-11-18T18:00:00Z'), read, seats: SEATS }, o));

gates['AS1 with no seat registered the check does nothing and the empty list stays empty and frozen'] = () => {
  assert.deepStrictEqual(act.ACTIVITY_SEATS, []);
  assert.ok(Object.isFrozen(act.ACTIVITY_SEATS));
  assert.deepStrictEqual(act.activeActivitySeats(), []);
  const r = act.activityOrderCheck({ seatId: 'ACTA', count: 3, limit: 0.3, slotOrders: [], now: 1, read });
  assert.deepStrictEqual(r, { applies: false, allowed: true, reason: '' });
  assert.deepStrictEqual(slot.SLOT_STRATEGIES.map((s) => s.id), ['OICORE', 'EVENT830', 'CFRTIK'], 'no seat was added to the slot registry');
};

gates['AS2 the shared $40 weekly cap binds across seats and every seat resumes Monday 00:00 Central, DST included'] = () => {
  const wed = Date.parse('2026-11-18T18:00:00Z');
  const monCST = Date.parse('2026-11-16T06:00:00Z');                       // Monday 00:00 CST (UTC-6)
  assert.strictEqual(act.centralWeekStart(wed), monCST);
  // two seats lose $19 each earlier in the week (each under its own $20 cap): the third seat's order would pass $40 in total
  const orders = [ord('ACTA', monCST + 3600e3, -19), ord('ACTB', monCST + 7200e3, -19)];
  assert.strictEqual(chk({ seatId: 'ACTC', slotOrders: orders }).allowed, false, 'a third seat is stopped by the shared cap');
  assert.ok(/shared weekly/.test(chk({ seatId: 'ACTC', slotOrders: orders }).reason));
  assert.strictEqual(chk({ seatId: 'ACTC', slotOrders: [orders[0]] }).allowed, true, 'under the shared cap the same order passes');
  // one second after Monday 00:00 Central the whole week is forgotten, on its own
  const nextMon = Date.parse('2026-11-23T06:00:00Z') + 1000;
  assert.strictEqual(act.centralWeekStart(nextMon), Date.parse('2026-11-23T06:00:00Z'));
  assert.strictEqual(chk({ seatId: 'ACTC', slotOrders: orders, now: nextMon }).allowed, true, 'resets Monday 00:00 Central');
  assert.strictEqual(chk({ seatId: 'ACTC', slotOrders: orders, now: Date.parse('2026-11-23T05:59:59Z') }).allowed, false, 'still the old week one second before');
  // across the DST change (2027-03-14): the week of Mon Mar 8 starts 06:00Z (CST), the week of Mon Mar 15 starts 05:00Z (CDT)
  assert.strictEqual(act.centralWeekStart(Date.parse('2027-03-14T12:00:00Z')), Date.parse('2027-03-08T06:00:00Z'));
  assert.strictEqual(act.centralWeekStart(Date.parse('2027-03-16T12:00:00Z')), Date.parse('2027-03-15T05:00:00Z'));
  assert.strictEqual(act.centralWeekStart(Date.parse('2027-03-15T04:59:59Z')), Date.parse('2027-03-08T06:00:00Z'));
  // and the autumn change (2026-11-01): Monday Oct 26 00:00 CDT = 05:00Z; Monday Nov 2 00:00 CST = 06:00Z
  assert.strictEqual(act.centralWeekStart(Date.parse('2026-11-01T12:00:00Z')), Date.parse('2026-10-26T05:00:00Z'));
  assert.strictEqual(act.centralWeekStart(Date.parse('2026-11-02T06:00:00Z')), Date.parse('2026-11-02T06:00:00Z'));
};

gates['AS3 one seat stops at $20 a week and $6 a day, counting a loss still open as lost'] = () => {
  const mon = Date.parse('2026-11-16T06:00:00Z'), now = Date.parse('2026-11-18T18:00:00Z');
  const wk = [ord('ACTA', mon + 3600e3, -10), ord('ACTA', mon + 7200e3, -9)];
  assert.strictEqual(chk({ slotOrders: wk }).allowed, false, 'losses of $19 leave no room for a $2.5 order under $20');
  assert.ok(/weekly/.test(chk({ slotOrders: wk }).reason));
  assert.strictEqual(chk({ slotOrders: [wk[0]] }).allowed, true);
  const day = [ord('ACTA', now - 3600e3, -4)];
  assert.strictEqual(chk({ slotOrders: day }).allowed, false, 'a $4 loss today leaves under the cost of a $2.5 order inside $6? 4 + 2.5 > 6');
  assert.ok(/daily/.test(chk({ slotOrders: day }).reason));
  assert.strictEqual(chk({ slotOrders: [ord('ACTA', now - 3600e3, -3)] }).allowed, true);
  assert.strictEqual(chk({ slotOrders: [ord('ACTA', now - 30 * 3600e3, -5)] }).allowed, true, 'yesterday does not count against today');
  const open = { strategy: 'SLOT', slotId: 'ACTA', ticker: T, side: 'yes', count: 3, fillCount: 3, status: 'filled', maxCost: 3, ts: now - 600e3, settled: false };
  assert.strictEqual(chk({ slotOrders: [open, Object.assign({}, open, { cid: 'x2' })] }).allowed, false, 'two open $3 orders count as $6 lost today');
  // another seat's loss never counts against this seat's own caps
  assert.strictEqual(chk({ slotOrders: [ord('ACTB', now - 3600e3, -5.5)] }).allowed, true);
};

gates['AS4 no entry at 88c or above, never more than 3 contracts or $3 an order'] = () => {
  assert.strictEqual(chk({ limit: 0.88 }).allowed, false);
  assert.strictEqual(chk({ limit: 0.95 }).allowed, false);
  assert.strictEqual(chk({ limit: 0.87 }).allowed, true);
  assert.strictEqual(chk({ count: 4 }).allowed, false);
  assert.strictEqual(chk({ count: 0 }).allowed, false);
  assert.ok(0.87 * 3 + bot.takerFee(0.87, 3) <= 3, 'the top price of a valid seat fits $3');
  for (const p of [0.05, 0.3, 0.5, 0.87]) for (const c of [1, 2, 3]) assert.strictEqual(chk({ limit: p, count: c }).allowed, true, 'valid at ' + p + ' x ' + c);
  for (let c = 1; c <= 3; c++) for (let p = 1; p < 100; p++) assert.strictEqual(act.fee(p / 100, c), bot.takerFee(p / 100, c), 'the copied fee equals the slot fee at ' + p + 'c x ' + c);
  const v = (o) => act.validateActivitySeat(seat(o));
  assert.strictEqual(v().ok, true, JSON.stringify(v().errors));
  for (const o of [{ entry: { priceMin: 0.05, priceMax: 0.88 } }, { contractsPerOrder: 4 }, { contractsPerOrder: 10 }, { ioc: false }, { familyId: 'favourite-late' }, { familyId: 'market-making' }, { id: 'a' }, { reviewedAt: 'soon' }, { series: [] }, { extra: 1 }]) assert.strictEqual(v(o).ok, false, JSON.stringify(o));
  assert.strictEqual(act.validateActivitySeat(null).ok, false);
  // the whole list or nothing; a fourth seat or a repeated id refuses every seat
  assert.strictEqual(act.activeActivitySeats(SEATS).length, 3);
  assert.strictEqual(act.activeActivitySeats([...SEATS, seat({ id: 'ACTD' })]).length, 0);
  assert.strictEqual(act.activeActivitySeats([seat(), seat()]).length, 0);
  assert.strictEqual(act.activeActivitySeats([seat(), seat({ id: 'ACTB', ioc: false })]).length, 0);
  assert.strictEqual(act.ACTIVITY_LABEL, 'Activity seat: no edge expected, data only');
};

gates['AS5 the profit factor cut needs 100 settled fills, then cuts a seat under 0.8 until a reviewed edit'] = () => {
  const base = Date.parse('2026-11-15T12:00:00Z');
  const mk = (k, wins, win, loss) => Array.from({ length: k }, (_, j) => ord('ACTA', base + j * 60e3, j < wins ? win : -loss));
  // 99 fills at PF far under 0.8: not enough fills, not cut (and ts spread so no daily/weekly cap interferes in act.activityCut)
  assert.strictEqual(act.activityCut(seat(), mk(99, 10, 1, 1), read).cut, false);
  const bad = mk(100, 10, 1, 1), good = mk(100, 50, 1, 0.9);
  assert.strictEqual(act.activityCut(seat(), bad, read).cut, true);
  assert.strictEqual(act.activityCut(seat(), good, read).cut, false, 'PF above 0.8 stays');
  const c = act.activityCut(seat(), bad, read);
  assert.strictEqual(c.fills, 100);
  assert.ok(c.pf < 0.8);
  // only the LAST 100 count: 40 old bad results then 100 good ones is not cut
  assert.strictEqual(act.activityCut(seat(), [...mk(40, 0, 1, 1).map((t) => Object.assign(t, { ts: base - 9e6, settledAt: base - 9e6 })), ...good], read).cut, false);
  // the gate refuses a cut seat even with every cap clear (orders are old, so no day or week cap binds), only a moved reviewedAt returns it
  const oldBad = bad.map((t, j) => Object.assign(t, { ts: Date.parse('2026-11-14T12:00:00Z') + j * 1000, settledAt: Date.parse('2026-11-14T12:00:00Z') + j * 1000 }));
  assert.strictEqual(act.activityOrderCheck({ seatId: 'ACTA', count: 3, limit: 0.3, slotOrders: oldBad, now: Date.parse('2026-11-30T18:00:00Z'), read, seats: SEATS }).allowed, false);
  assert.ok(/cut/.test(act.activityOrderCheck({ seatId: 'ACTA', count: 3, limit: 0.3, slotOrders: oldBad, now: Date.parse('2026-11-30T18:00:00Z'), read, seats: SEATS }).reason));
  const reviewed = [seat({ reviewedAt: '2026-11-29' }), seat({ id: 'ACTB' }), seat({ id: 'ACTC' })];
  assert.strictEqual(act.activityOrderCheck({ seatId: 'ACTA', count: 3, limit: 0.3, slotOrders: oldBad, now: Date.parse('2026-11-30T18:00:00Z'), read, seats: reviewed }).allowed, true, 'a reviewed edit (reviewedAt moved past the record) returns it');
  // zero net fills (no wins and no losses) are not a cut
  assert.strictEqual(act.activityCut(seat(), mk(100, 0, 0, 0).map((t) => Object.assign(t, { result: 'yes', settledPnl: 0 })), read).cut, false);
};

gates['AS6 fired today counts a seat\'s own filled orders on the Central day, for a minimum-activity check'] = () => {
  const now = Date.parse('2026-11-18T18:00:00Z');
  const o = [ord('ACTA', now - 3600e3, 1), ord('ACTA', now - 30 * 3600e3, 1), ord('ACTB', now - 3600e3, 1), ord('ACTA', now - 7200e3, -1, { fillCount: 0, status: 'no fill', settled: false })];
  assert.strictEqual(act.activityFiredToday('ACTA', o, now), 1);
  assert.strictEqual(act.activityFiredToday('ACTB', o, now), 1);
  assert.strictEqual(act.activityFiredToday('ACTC', o, now), 0);
  assert.strictEqual(act.activityFiredToday('ACTA', null, now), 0);
  assert.strictEqual(act.activityFiredToday('ACTA', o, NaN), 0);
};

gates['AS7 fail closed: a missing reader, clock or order list refuses a registered seat'] = () => {
  for (const o of [{ read: null }, { slotOrders: null }, { now: NaN }]) assert.strictEqual(chk(o).allowed, false, JSON.stringify(Object.keys(o)));
  // an order with no readable time counts in every window
  const noTs = ord('ACTA', NaN, -19);
  assert.strictEqual(chk({ slotOrders: [noTs] }).allowed, false);
};

gates['AS8 the slot engine refuses a registered seat at its caps and nobody else; with no seat nothing changes'] = () => {
  const strat = { id: 'ACTA', readme: 'docs/ACTIVITY_SEATS.md#acta', series: ['KXBTC15M'],
    entry: { sideRule: 'cheap', priceMin: 0.05, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120 }, exit: { stopBid: 0.02, targetBid: 0.9, mustExitLeftSec: 60 }, contractsPerOrder: 3,
    scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true }, killRules: { maxConsecutiveLosses: 30, minNet: { afterFills: 100, net: -60 } },
    forwardReadDate: '2026-12-20', reviewedAt: '2026-11-13' };
  assert.ok(slot.validateSlotStrategy(strat).ok, JSON.stringify(slot.validateSlotStrategy(strat).errors));
  const now = Date.parse('2026-11-18T18:00:00Z');
  const input = (orders) => ({ strategyId: 'ACTA', ticker: 'KXBTC15M-26NOV181315-15', side: 'yes', limit: 0.3, step: 1, depthAtTouch: 500, slotOrders: orders, l1Orders: [], slotOrdersComplete: true, lockTxn: true,
    lock: null, position: 0, sizingBase: 1000, windowCapFraction: 0.055, secondsLeft: 150, now, oiRise: 0 });
  const W = slot._testOnly.slotOrderCheckWith;
  const plain = { enabled: true, registry: [strat] };
  const withSeat = { enabled: true, registry: [strat], activitySeats: [seat()] };
  const loser = [ord('ACTA', now - 3600e3, -5.5, { ticker: 'KXBTC15M-26NOV181200-15' })];
  assert.strictEqual(W(plain, input(loser)).allowed, true, 'without an activity seat registered the engine behaves as before');
  const a = W(withSeat, input(loser));
  assert.strictEqual(a.allowed, false);
  assert.ok(/daily loss cap/.test(a.reasons[0]), a.reasons[0]);
  assert.strictEqual(W(withSeat, input([])).allowed, true, 'a clear seat passes');
  assert.strictEqual(W(withSeat, input([])).count, 3);
  // another strategy's id in the same registry is untouched by the seat list
  assert.strictEqual(W({ enabled: true, registry: [Object.assign({}, strat, { id: 'ACTZ' })], activitySeats: [seat()] }, Object.assign(input(loser), { strategyId: 'ACTZ' })).allowed, true);
};

gates['AS9 the library imports nothing, nothing in functions or the page names it but the slot library, and the label is ready'] = () => {
  const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
  const src = code(fs.readFileSync(path.join(root, 'functions/kalshiActivityLib.js'), 'utf8'));
  assert.deepStrictEqual([...src.matchAll(/require\(/g)], [], 'imports nothing');
  assert.ok(!/fetch|firestore|Date\.now|Math\.random|signing|crypto/.test(src), 'no network, store, clock, randomness or signing');
  const users = walk(path.join(root, 'functions')).filter((f) => /\.js$/.test(f) && !/node_modules/.test(f) && f !== path.join(root, 'functions/kalshiActivityLib.js'))
    .filter((f) => /kalshiActivityLib/.test(code(fs.readFileSync(f, 'utf8')))).map((f) => path.basename(f));
  assert.deepStrictEqual(users, ['kalshiSlotLib.js']);
  assert.ok(!/kalshiActivityLib|ACTIVITY_SEATS/.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8')), 'the page does not name it');
};

(async () => {
  for (const [k, f] of Object.entries(gates)) { try { await f(); console.log('ok  ' + k); } catch (e) { console.error('FAIL ' + k + '\n' + (e.stack || e)); process.exit(1); } }
})();

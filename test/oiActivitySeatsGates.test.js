'use strict';
// HB1 to HB6: activity seats 2 and 3, HYPEOI1 and BNBOI1 (Nov 14, 2026): the open interest mechanism of SPXOI1 and OICORE on the HYPE and BNB 15 minute markets,
// with fixed thresholds from the Head of R&D (two builds matched). Each gate states the consequence. No live figures.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib');
const run = require('../functions/kalshiSlotRunLib');
const cfg = require('../functions/kalshiSpxoiConfig');
const act = require('../functions/kalshiActivityLib');
const root = path.join(__dirname, '..');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const iso = (ms) => new Date(ms).toISOString();
const tick = () => new Promise((r) => setImmediate(r));
const SEATS = [['HYPEOI1', 'KXHYPE15M', 6796.75], ['BNBOI1', 'KXBNB15M', 4351.84]];
const seat = (id) => slot.SLOT_STRATEGIES.find((s) => s.id === id);
const gates = {};

gates.HB1 = () => {
  // Consequence: the thresholds are the Head's frozen numbers, in code only, and the seats are exactly the specified ones.
  assert.strictEqual(cfg.HYPEOI1_T, 6796.75); assert.strictEqual(cfg.BNBOI1_T, 4351.84); assert.ok(Object.isFrozen(cfg));
  for (const [id, series, T] of SEATS) {
    const s = seat(id); assert.ok(s, id + ' is registered');
    assert.deepStrictEqual(JSON.parse(JSON.stringify(s)), {
      id, readme: 'kalshi-scalper/README.md#SLOT-' + id, series: [series],
      entry: { sideRule: 'cheap', priceMin: 0.08, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120, oiRiseMin: T, skipCalendar: 'EVENT830' },
      exit: { holdToSettle: true }, contractsPerOrder: 3, scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
      killRules: { maxConsecutiveLosses: 30, minNet: { afterFills: 5, net: -18 } }, forwardReadDate: '2026-12-01', reviewedAt: '2026-11-14' });
    assert.ok(Object.isFrozen(s) && Object.isFrozen(s.entry));
    assert.ok(slot.validateSlotStrategy(s).ok, JSON.stringify(slot.validateSlotStrategy(s).errors));
    assert.ok(slot.SLOT_HOLD_ALLOWED.includes(id) && slot.SLOT_TIE_YES.includes(id));
    assert.deepStrictEqual(JSON.parse(JSON.stringify(slot.SLOT_SEAT_CAPS[id])), { perOrder: 3, daily: 9 });
    const a = act.ACTIVITY_SEATS.find((x) => x.id === id);
    assert.ok(a && a.familyId === 'cheap-side-open-interest' && a.series[0] === series && a.contractsPerOrder === 3 && a.ioc === true && a.reviewedAt === s.reviewedAt, 'activity seat ' + id);
  }
  assert.deepStrictEqual(act.activeActivitySeats().map((x) => x.id), ['SPXOI1', 'HYPEOI1', 'BNBOI1'], 'three activity seats, the most allowed');
  assert.strictEqual(act.ACTIVITY_MAX_SEATS, 3);
  assert.strictEqual(act.activeActivitySeats(act.ACTIVITY_SEATS.concat([act.ACTIVITY_SEATS[0]])).length, 0, 'a fourth seat refuses the whole list');
  // The threshold is not read from anything stored: the entry builder takes only the config module's number.
  assert.strictEqual(slot.oiSeatEntry('HYPEOI1', 'KXHYPE15M', null), null);
  assert.strictEqual(slot.oiSeatEntry('HYPEOI1', 'KXHYPE15M', 500) && slot.validateSlotStrategy(slot.oiSeatEntry('HYPEOI1', 'KXHYPE15M', 500)).ok, false, 'under the validator line of 1,000 it would not register');
};

gates.HB2 = () => {
  // Consequence: HYPE and BNB stay EVENT830's reserved markets: no other id may list them, only these two seats may share them, and EVENT830 itself is unchanged.
  assert.strictEqual(slot.SLOT_SERIES_RESERVED.KXHYPE15M, 'EVENT830'); assert.strictEqual(slot.SLOT_SERIES_RESERVED.KXBNB15M, 'EVENT830');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(slot.SLOT_SERIES_ALSO)), { KXHYPE15M: ['HYPEOI1'], KXBNB15M: ['BNBOI1'] }, 'exactly one extra id per market');
  const base = JSON.parse(JSON.stringify(seat('HYPEOI1')));
  for (const [id, series] of [['OICORE', 'KXHYPE15M'], ['BNBOI1', 'KXHYPE15M'], ['HYPEOI1', 'KXBNB15M'], ['CFRTIK', 'KXBNB15M'], ['XYZ', 'KXBNB15M']]) {
    const e = slot.validateSlotStrategy(Object.assign({}, base, { id, series: [series] }));
    assert.ok(e.errors.some((m) => /is reserved for EVENT830/.test(m)), id + ' on ' + series + ' is refused: ' + JSON.stringify(e.errors));
  }
  const ev = slot.SLOT_STRATEGIES.find((s) => s.id === 'EVENT830');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(ev)).entry, { sideRule: 'cheap', priceMin: 0.05, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120, maxSpread: 0.1, calendar: 'EVENT830' }, 'EVENT830 is unchanged');
  assert.strictEqual(ev.contractsPerOrder, 1);
  // skipCalendar only validates for EVENT830's calendar, on another id, with an open interest line.
  const withSkip = (x) => slot.validateSlotStrategy(Object.assign({}, base, { entry: Object.assign({}, base.entry, x) })).ok;
  assert.strictEqual(withSkip({}), true); assert.strictEqual(withSkip({ skipCalendar: 'OTHER' }), false);
  const noOi = JSON.parse(JSON.stringify(base)); delete noOi.entry.oiRiseMin; assert.strictEqual(slot.validateSlotStrategy(noOi).ok, false);
};

gates.HB3 = () => {
  // Consequence: a window that closes at one of EVENT830's listed instants is refused by the gate itself too, so no path can send it; an ordinary window passes.
  const s = seat('HYPEOI1');
  const REL = Date.parse('2026-11-17T13:30:00Z'), TKR = 'KXHYPE15M-26NOV170830-30';
  assert.ok(slot.slotSkipCalendarRow(s, TKR, REL), 'a listed release window is found');
  assert.strictEqual(slot.slotSkipCalendarRow(s, 'KXHYPE15M-26NOV170845-30', Date.parse('2026-11-17T13:45:00Z')), null, 'the window after it is ordinary');
  assert.strictEqual(slot.slotSkipCalendarRow(s, TKR, REL + 900000), null, 'the close and the ticker code must both match one row');
  assert.strictEqual(slot.slotSkipCalendarRow(seat('OICORE'), TKR, REL), null, 'a strategy without skipCalendar is never skipped');
  const input = (o) => Object.assign({ strategyId: 'HYPEOI1', ticker: TKR, side: 'yes', limit: 0.3, step: 1, depthAtTouch: 100, slotOrders: [], l1Orders: [], slotOrdersComplete: true, lockTxn: true, lock: null,
    position: 0, sizingBase: 500, windowCapFraction: 0.055, secondsLeft: 150, now: REL - 150000, closeTime: REL, oiRise: 7000 }, o || {});
  const chk = (o) => slot._testOnly.slotOrderCheckWith({ enabled: true, registry: [s], everUsed: true, activitySeats: [] }, input(o));
  const bad = chk(); assert.strictEqual(bad.allowed, false); assert.ok(bad.reasons.some((r) => /never trades/.test(r)), JSON.stringify(bad.reasons));
  const ok = chk({ ticker: 'KXHYPE15M-26NOV170900-30', closeTime: Date.parse('2026-11-17T14:00:00Z'), now: Date.parse('2026-11-17T14:00:00Z') - 150000 });
  assert.strictEqual(ok.allowed, true, JSON.stringify(ok.reasons)); assert.strictEqual(ok.count, 3);
  // the same seat's entry numbers: below T, above the band, never 88c
  assert.strictEqual(chk({ ticker: 'KXHYPE15M-26NOV170900-30', closeTime: Date.parse('2026-11-17T14:00:00Z'), oiRise: 6796.75 - 1 }).allowed, false);
  for (const limit of [0.07, 0.51, 0.88, 0.95]) assert.strictEqual(chk({ ticker: 'KXHYPE15M-26NOV170900-30', closeTime: Date.parse('2026-11-17T14:00:00Z'), limit }).allowed, false, 'refused at ' + limit);
};

function world(id, series, T, closeIso, opts = {}) {
  const s = seat(id), CLOSE = Date.parse(closeIso), NOW = CLOSE - 150000, CS = Math.round(CLOSE / 1000);
  const dd = closeIso.slice(2, 4); void dd;
  const mon = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'][Number(closeIso.slice(5, 7)) - 1];
  const et = new Date(CLOSE - 5 * 3600000);   // November: Eastern standard time
  const code = '26' + mon + closeIso.slice(8, 10) + String(et.getUTCHours()).padStart(2, '0') + String(et.getUTCMinutes()).padStart(2, '0');
  const TK = series + '-' + code + '-30';
  const db = { slot: new Map(), locks: new Map(), queue: Promise.resolve() };
  db.tx = (fn) => { const p = db.queue.then(fn); db.queue = p.catch(() => {}); return p; };
  const clone = (x) => JSON.parse(JSON.stringify(x));
  const store = {
    async halted() { return false; }, async hasUnresolved() { return false; }, async l1HasUnresolved() { return false; }, async killLatches() { return {}; },
    async allSlotOrders() { return [...db.slot.values()].map(clone); }, async l1Recent() { return []; },
    async runSlotEntry({ ticker, decide }) {
      return db.tx(async () => {
        const lock = db.locks.get(ticker) || null; await tick();
        const r = decide(lock ? clone(lock) : null, [...db.slot.values()].map(clone), []);
        if (!r.allowed) return { created: false, reason: r.reason };
        if (!lock) db.locks.set(ticker, r.lock);
        db.slot.set(r.record.id, clone(r.record));
        return { created: true, record: clone(r.record) };
      });
    },
    async updateSlotOrder(i, patch) { Object.assign(db.slot.get(i), clone(patch)); }, async killStrategy() {},
  };
  const market = { ticker: TK, status: 'active', close_time: iso(CLOSE), yes_bid_dollars: '0.4000', yes_ask_dollars: '0.4200', yes_bid_size_fp: '100.00', yes_ask_size_fp: '100.00', exchange_index: 0 };
  const posts = [], gets = [];
  const candles = [{ end_period_ts: CS - 360, open_interest_fp: '1000' }, { end_period_ts: CS - 180, open_interest_fp: String(1000 + T + 100) }];
  const fetchFn = async (url, init) => {
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    gets.push(init.method + ' ' + url);
    if (url.includes('/candlesticks')) return reply(200, { candlesticks: candles });
    if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [] });
    if (url.includes('/portfolio/orders') && init.method === 'GET') return reply(200, { orders: [] });
    if (url.includes('/markets/')) return reply(200, { market });
    if (init.method === 'POST') { const b = JSON.parse(init.body); posts.push(b); return reply(201, { order_id: 'ord-1', fill_count: String(b.count), remaining_count: '0.00', average_fill_price: b.price }); }
    throw new Error('unexpected ' + init.method + ' ' + url);
  };
  const skips = [], sess = { active: true };
  const args = { session: sess, now: NOW, enabled: true, active: true, store, keyId: 'k', pem, fetchFn, quotes: [{ series, m: { ticker: TK, status: 'active', close_time: iso(CLOSE) } }],
    setSession: async (p) => Object.assign(sess, p), logEvent: async () => {}, clock: () => NOW, recordSkip: async (d) => { skips.push(d); },
    shared: { sizeBase: 500, balanceBody: { balance: 50000 }, risk: { worst: 0 }, floor: -60, recentList: [], slotOrders: [], since: NOW - 86400000 } };
  const runner = run._testOnly.makeRunners({ enabled: true, registry: [s], everUsed: true });
  return { db, posts, gets, skips, TK, go: () => runner.runSlotTick(args) };
}

gates.HB4 = async () => {
  // Consequence, through the real engine: on EVENT830's listed 13:30Z window the seat sends nothing and says event830_window, with no market read at all; an ordinary window buys the cheaper side, 3 contracts, immediate-or-cancel, held.
  for (const [id, series, T] of SEATS) {
    let w = world(id, series, T, '2026-11-17T13:30:00Z'); await w.go();
    assert.strictEqual(w.posts.length, 0, id + ' skipped the release window: ' + JSON.stringify(w.skips));
    assert.ok(w.skips.some((s) => s.reason === 'event830_window' && s.strategy === id), JSON.stringify(w.skips));
    assert.strictEqual(w.gets.filter((g) => /candlesticks|\/markets\//.test(g)).length, 0, 'no read is spent on a skipped window');
    w = world(id, series, T, '2026-11-17T14:00:00Z'); await w.go();
    assert.strictEqual(w.posts.length, 1, id + ' trades an ordinary window: ' + JSON.stringify(w.skips));
    assert.strictEqual(w.posts[0].side, 'bid'); assert.strictEqual(Number(w.posts[0].count), 3); assert.strictEqual(w.posts[0].time_in_force, 'immediate_or_cancel');
    assert.ok(Math.abs(Number(w.posts[0].price) - 0.42) < 1e-9, 'the ask seen, no slip');
    assert.strictEqual([...w.db.slot.values()][0].slotId, id);
    // the same minute on a Saturday still trades: these are every-day markets
    w = world(id, series, T, '2026-11-21T14:00:00Z'); await w.go();
    assert.strictEqual(w.posts.length, 1, id + ' on a Saturday: ' + JSON.stringify(w.skips));
  }
  // every listed EVENT830 close is skipped, none of the ordinary ones around it
  const rows = slot.SLOT_CALENDARS.EVENT830, s = seat('BNBOI1');
  for (const r of rows) {
    const c = Date.parse(r.closeUtc);
    assert.ok(slot.slotSkipCalendarRow(s, 'KXBNB15M-' + r.window + '-30', c), r.window + ' is skipped');
    assert.strictEqual(slot.slotSkipCalendarRow(s, 'KXBNB15M-' + r.window + '-30', c - 900000), null);
  }
};

gates.HB5 = () => {
  // Consequence: the quotes arrive every day around the entry span (and the weekday-only S&P seat is unchanged); an EVENT830 window is read for EVENT830 by its own calendar rule only.
  const sat = Date.parse('2026-11-21T16:57:30Z'), sun = Date.parse('2026-11-22T03:12:30Z');
  const hb = slot.SLOT_STRATEGIES.filter((x) => x.id === 'HYPEOI1' || x.id === 'BNBOI1');
  assert.deepStrictEqual(slot.slotSessionSeriesDue(hb, sat).sort(), ['KXBNB15M', 'KXHYPE15M']);
  assert.deepStrictEqual(slot.slotSessionSeriesDue(hb, sun).sort(), ['KXBNB15M', 'KXHYPE15M']);
  assert.deepStrictEqual(slot.slotSessionSeriesDue(hb, Date.parse('2026-11-21T16:50:00Z')), [], 'nothing outside the minute or two before the span');
  assert.deepStrictEqual(slot.slotSessionSeriesDue(slot.SLOT_STRATEGIES.filter((x) => x.id === 'SPXOI1'), sat), [], 'the S&P seat is still weekday only');
  assert.deepStrictEqual(slot.slotSessionSeriesDue(slot.SLOT_STRATEGIES.filter((x) => !['SPXOI1', 'HYPEOI1', 'BNBOI1'].includes(x.id)), sat), [], 'OICORE, EVENT830 and CFRTIK add no session read');
  assert.ok(/KXHYPE15M/.test(fs.readFileSync(path.join(root, 'functions', 'kalshiLib.js'), 'utf8')) && /KXBNB15M/.test(fs.readFileSync(path.join(root, 'functions', 'kalshiLib.js'), 'utf8')), 'the relay lists both markets');
};

gates.HB6 = () => {
  // Consequence: the page, the registry and the pre-registration carry both seats, with the Head's thresholds.
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.ok(/KAL_SLOT_REGISTERED = \[[^\]]*'HYPEOI1', 'BNBOI1'\]/.test(html));
  for (const id of ['HYPEOI1', 'BNBOI1']) assert.ok(new RegExp(id + ': \\{ name:').test(html) && new RegExp("id: '" + id + "'").test(html), id + ' on the page');
  assert.ok(/6,796\.75/.test(html) && /4,351\.84/.test(html) && /Activity seat: unproven, for live data/.test(html));
  const reg = JSON.parse(fs.readFileSync(path.join(root, 'strategies-registry.json'), 'utf8'));
  for (const id of ['HYPEOI1', 'BNBOI1']) { const r = reg.strategies.find((x) => x.id === id); assert.ok(r && r.code.slot === id && r.code.live === id && r.stage === 'Probe', id + ' registry row'); }
  const readme = fs.readFileSync(path.join(root, 'kalshi-scalper', 'README.md'), 'utf8');
  assert.ok(/## SLOT-HYPEOI1/.test(readme) && /SLOT-BNBOI1/.test(readme) && /6796\.75/.test(readme) && /4351\.84/.test(readme));
  assert.ok(/HYPEOI1/.test(fs.readFileSync(path.join(root, 'docs', 'ACTIVITY_SEATS.md'), 'utf8')));
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) { try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.stack || e.message).split('\n').slice(0, 4).join(' | ')); } }
  process.exit(failed ? 1 : 0);
})();

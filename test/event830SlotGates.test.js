'use strict';
// EV1 to EV9: EVENT830, the release day probe in the second slot (Nov 3, 2026; kalshi-scalper/README.md#SLOT-EVENT830). Each gate states the consequence:
// it trades ONLY the window closing at a listed US 8:30 AM ET release, only its eight L1-free markets, only the cheaper side at 5c to 50c with a hard 50c limit and a 10c spread rule,
// 1 contract, held to settlement; on any other minute it reads nothing and sends nothing, and nothing stored can add a date or lend its permissions to another strategy.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib');
const run = require('../functions/kalshiSlotRunLib');
const live = require('../functions/kalshiLiveLib');

const root = path.join(__dirname, '..');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const ev = slot.SLOT_STRATEGIES.find((s) => s.id === 'EVENT830');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const iso = (ms) => new Date(ms).toISOString();
const tick = () => new Promise((r) => setImmediate(r));
const CLOSE = Date.parse('2026-11-05T13:30:00Z');            // the first listed release window (weekly jobless claims)
const T = 'KXEURUSD15M-26NOV050830-30';
const SERIES = ['KXSILVER15M', 'KXCOPPER15M', 'KXWTI15M', 'KXEURUSD15M', 'KXGBPUSD15M', 'KXUSDJPY15M', 'KXHYPE15M', 'KXBNB15M'];
// The registration's frozen list (workers/EVENT830_CALENDAR.md on the research branch), written out here so a change to the code's list has to change this too.
const DATES = ['2026-11-05', '2026-11-06', '2026-11-10', '2026-11-12', '2026-11-13', '2026-11-17', '2026-11-19', '2026-11-25',
  '2026-12-03', '2026-12-04', '2026-12-10', '2026-12-15', '2026-12-16', '2026-12-17', '2026-12-23'];
const gates = {};

gates['EV1 the registry entry is exactly the registered probe: eight L1-free markets, cheaper side 5c to 50c, 10c spread, its own calendar, 1 contract, held, kill rules in code'] = () => {
  assert.ok(ev, 'EVENT830 is registered');
  assert.ok(Object.isFrozen(ev) && Object.isFrozen(ev.entry) && Object.isFrozen(ev.exit) && Object.isFrozen(ev.killRules) && Object.isFrozen(ev.killRules.minNet) && Object.isFrozen(ev.series), 'every level is frozen');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(ev)), {
    id: 'EVENT830', readme: 'kalshi-scalper/README.md#SLOT-EVENT830', series: SERIES,
    entry: { sideRule: 'cheap', priceMin: 0.05, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120, maxSpread: 0.1, calendar: 'EVENT830' },
    exit: { holdToSettle: true }, contractsPerOrder: 1,
    scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
    killRules: { maxConsecutiveLosses: 20, minNet: { afterFills: 40, net: 0 } },
    forwardReadDate: '2026-12-07', reviewedAt: '2026-11-05',
  });
  assert.ok(slot.validateSlotStrategy(ev).ok, JSON.stringify(slot.validateSlotStrategy(ev).errors));
  assert.strictEqual(slot.SLOT_LAST_REVIEWED_ON, '2026-11-10');
  assert.ok(SERIES.every((s) => !live.L1_SERIES.includes(s)), 'none of its markets is an L1 market, so it can never sit against an L1 position');
  assert.ok(!(slot.SLOT_LIMIT_SLIP && Object.prototype.hasOwnProperty.call(slot.SLOT_LIMIT_SLIP, 'EVENT830')), 'no slip: the limit is the price it sees, never above 50c');
  const readme = fs.readFileSync(path.join(root, 'kalshi-scalper', 'README.md'), 'utf8');
  assert.ok(/^## SLOT-EVENT830/m.test(readme), 'the pre-registration anchor exists');
  const sec = readme.slice(readme.indexOf('## SLOT-EVENT830'));
  assert.ok(sec.indexOf('deploy-push.sh') > -1 && sec.indexOf('deploy-push.sh') < sec.indexOf('deploy-sizing.sh'), 'the exit watch is deployed first: an older one would sell an unknown slot order at the 25c fallback stop');
};

gates['EV2 the calendar is the registration\'s fifteen Nov and Dec 2026 release windows, each closing at 8:30 AM New York time on a weekday, and nothing later'] = () => {
  const rows = slot.SLOT_CALENDARS.EVENT830;
  assert.ok(Object.isFrozen(slot.SLOT_CALENDARS) && Object.isFrozen(rows) && rows.every((r) => Object.isFrozen(r)), 'frozen at every level');
  assert.deepStrictEqual(Object.keys(slot.SLOT_CALENDARS), ['EVENT830'], 'one calendar, its own');
  assert.deepStrictEqual(rows.map((r) => r.closeUtc.slice(0, 10)), DATES);
  const MON = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
  for (const r of rows) {
    const ms = Date.parse(r.closeUtc);
    const ny = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false, weekday: 'short' }).formatToParts(new Date(ms));
    const p = Object.fromEntries(ny.map((x) => [x.type, x.value]));
    assert.strictEqual(p.hour + ':' + p.minute, '08:30', r.closeUtc + ' closes at 8:30 AM New York time');
    assert.ok(!['Sat', 'Sun'].includes(p.weekday), r.closeUtc + ' is a weekday');
    assert.strictEqual(r.window, p.year + MON[Number(p.month) - 1] + p.day + '0830', 'the ticker window code is the same instant in Eastern time');
    assert.ok(/^(CLAIMS|JOBS|CPI|PPI|RETAIL|GDP_PCE|CPI_CLAIMS)$/.test(r.kind));
  }
  assert.ok(!rows.some((r) => ['2026-11-26', '2026-12-24', '2026-12-31'].includes(r.closeUtc.slice(0, 10))), 'the unconfirmed holiday-week claims are left out');
  assert.ok(rows.every((r) => r.closeUtc < '2027-01-01'), 'no date after Dec 31, 2026 is guessed');
};

// The gate's input for a valid EVENT830 order in the first release window; each test changes one thing.
const input = (o) => Object.assign({
  strategyId: 'EVENT830', ticker: T, side: 'yes', limit: 0.3, step: 1, depthAtTouch: 100, slotOrders: [], l1Orders: [], slotOrdersComplete: true,
  lockTxn: true, lock: null, position: 0, sizingBase: 500, windowCapFraction: 0.055, secondsLeft: 177, now: CLOSE - 177000, spread: 0.02, closeTime: CLOSE,
}, o || {});

gates['EV3 the gate allows the listed window and refuses any other close, a mislabelled ticker, a missing close or a date not in code'] = () => {
  assert.strictEqual(slot.slotOrderCheck(input()).allowed, true, JSON.stringify(slot.slotOrderCheck(input()).reasons));
  const day = 24 * 3600 * 1000;
  const refused = [
    input({ closeTime: CLOSE - day, ticker: 'KXEURUSD15M-26NOV040830-30', now: CLOSE - day - 177000 }),     // Nov 4: no release
    input({ closeTime: CLOSE + 15 * 60000, ticker: 'KXEURUSD15M-26NOV050845-30', now: CLOSE + 15 * 60000 - 177000 }),   // the next window, after the release
    input({ ticker: 'KXEURUSD15M-26NOV050845-30' }),                                                       // the right close, a ticker of another window
    input({ ticker: 'KXEURUSD15M-26NOV060830-30' }),                                                       // a listed window code, the close of a different listed window
    input({ closeTime: undefined }), input({ closeTime: NaN }), input({ closeTime: String(CLOSE) }),
    input({ closeTime: Date.parse('2027-01-08T13:30:00Z'), ticker: 'KXEURUSD15M-27JAN080830-30' }),         // a plausible jobs day that is not in code
  ];
  // A second real listed window (Nov 6, jobs) is allowed, which proves the refusals are about the calendar and nothing else.
  assert.strictEqual(slot.slotOrderCheck(input({ closeTime: CLOSE + day, ticker: 'KXEURUSD15M-26NOV060830-30', now: CLOSE + day - 177000 })).allowed, true, 'Nov 6 (jobs) is allowed');
  for (const x of refused) {
    const r = slot.slotOrderCheck(x);
    assert.strictEqual(r.allowed, false, JSON.stringify({ t: x.ticker, c: x.closeTime }));
  }
  assert.ok(/not a listed release window/.test(slot.slotOrderCheck(refused[0]).reasons[0]));
};

gates['EV4 the band, the hard 50c limit and the spread rule: 5c to 50c only, never above 50c, no order with a spread over 10c or an unknown one'] = () => {
  assert.strictEqual(slot.slotOrderCheck(input({ limit: 0.5 })).allowed, true, '50c is the edge and is allowed');
  assert.strictEqual(slot.slotOrderCheck(input({ limit: 0.05 })).allowed, true, '5c is the other edge');
  for (const limit of [0.51, 0.04, 0.6, 0.97]) assert.strictEqual(slot.slotOrderCheck(input({ limit })).allowed, false, 'refused at ' + limit);
  assert.strictEqual(slot.slotOrderCheck(input({ spread: 0.1 })).allowed, true, 'a 10c spread is allowed');
  for (const spread of [0.11, 0.3, undefined, NaN, -0.01]) assert.strictEqual(slot.slotOrderCheck(input({ spread })).allowed, false, 'refused with spread ' + spread);
  assert.strictEqual(slot.slotLimitFor(ev, 0.5), 0.5, 'the limit sent is the price seen: no slip past 50c');
  assert.strictEqual(slot.slotLimitFor(ev, 0.31), 0.31);
  for (const secondsLeft of [181, 119, 600]) assert.strictEqual(slot.slotOrderCheck(input({ secondsLeft })).allowed, false, 'only 3 to 2 minutes before the close');
};

gates['EV5 one contract: whatever is asked for, one contract is the most the gate allows'] = () => {
  for (const wanted of [1, 2, 5, 10]) { const r = slot.slotOrderCheck(input({ wanted })); assert.strictEqual(r.allowed, true); assert.strictEqual(r.count, 1, 'asked ' + wanted); }
  assert.ok(slot.slotOrderCheck(input()).cost <= 0.52 + 1e-9, 'the worst single loss is about $0.52 (50c plus the fee)');
  assert.strictEqual(slot.slotOrderCheck(input({ limit: 0.5 })).cost, 0.52);
};

gates['EV6 holding to settlement and the eight markets are this id\'s alone: another strategy copying them is refused'] = () => {
  assert.deepStrictEqual([...slot.SLOT_HOLD_ALLOWED], ['OICORE', 'EVENT830', 'XRPYES10', 'KESTREL']);
  const copy = (o) => Object.assign(JSON.parse(JSON.stringify(ev)), o);
  assert.ok(slot.validateSlotStrategy(copy({})).ok);
  assert.ok(!slot.validateSlotStrategy(copy({ id: 'EVENT831' })).ok, 'another id may not hold, use the eight markets or the calendar');
  assert.ok(!slot.validateSlotStrategy(copy({ id: 'EVENT831', exit: { stopBid: 0.02, targetBid: 0.99, mustExitLeftSec: 60 }, entry: Object.assign({}, ev.entry, { calendar: undefined }) })).ok, 'still refused for the markets');
  const btc = copy({ id: 'TESTZ', series: ['KXBTC15M'], exit: { stopBid: 0.02, targetBid: 0.99, mustExitLeftSec: 60 } });
  assert.ok(!slot.validateSlotStrategy(btc).ok && slot.validateSlotStrategy(btc).errors.some((e) => /calendar/.test(e)), 'a calendar may only be the strategy\'s own');
  const errs = slot.validateSlotStrategy(copy({ id: 'OTHERX', series: ['KXSILVER15M'] })).errors;
  assert.ok(errs.some((e) => /reserved for EVENT830/.test(e)) && errs.some((e) => /may hold to settlement/.test(e)));
  assert.ok(!slot.validateSlotStrategy(copy({ entry: Object.assign({}, ev.entry, { maxSpread: 0.5 }) })).ok, 'a spread rule is at most 20c');
  assert.ok(!slot.validateSlotStrategy(copy({ entry: Object.assign({}, ev.entry, { calendar: 'OICORE' }) })).ok, 'an unknown calendar is refused');
};

gates['EV7 nothing stored can add a date: the calendar is a frozen constant, read only by the pure library, and no caller passes one'] = () => {
  'use strict';
  assert.throws(() => { slot.SLOT_CALENDARS.EVENT830.push({ closeUtc: '2027-01-08T13:30:00Z', window: '27JAN080830', kind: 'JOBS' }); }, TypeError);
  assert.throws(() => { slot.SLOT_CALENDARS.EXTRA = []; }, TypeError);
  assert.throws(() => { slot.SLOT_CALENDARS.EVENT830[0].closeUtc = '2027-01-08T13:30:00Z'; }, TypeError);
  assert.strictEqual(slot.SLOT_CALENDARS.EVENT830.length, 15);
  // The production gate takes the strategy from the frozen registry: a calendar (or a date) in the caller's input is ignored, never read.
  const extra = input({ calendar: [{ closeUtc: '2027-01-08T13:30:00Z', window: '27JAN080830' }], closeTime: Date.parse('2027-01-08T13:30:00Z'), ticker: 'KXEURUSD15M-27JAN080830-30' });
  assert.strictEqual(slot.slotOrderCheck(extra).allowed, false);
  for (const f of ['index.js', 'kalshiSlotRunLib.js', 'kalshiSlotStoreLib.js', 'kalshiLiveLib.js']) {
    const c = code(fs.readFileSync(path.join(root, 'functions', f), 'utf8'));
    assert.ok(!/SLOT_CALENDARS/.test(c), f + ' never touches the calendar table');
  }
  const idx = code(fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8'));
  assert.ok(/slotLib\.slotCalendarSeriesDue\(slotLib\.activeSlotStrategies\(\), now\)/.test(idx), 'the minute function asks only the library, with the registry and its own clock');
  assert.ok(/quotes: market\.quotes, active: market\.active, enabled: !CODE_KILL_SWITCH/.test(idx) && /quotes: slotQuotes/.test(idx), 'L1 reads its own quotes; the extra markets go only to the slot tick');
};

gates['EV8 the extra markets are read only around a listed window: zero reads on any other minute of Nov and Dec 2026, eight series in the two minutes before each release'] = () => {
  const strategies = slot.activeSlotStrategies();
  let dueMinutes = 0;
  for (let t = Date.parse('2026-11-03T00:00:00Z'); t < Date.parse('2027-01-02T00:00:00Z'); t += 60000) {
    const due = slot.slotCalendarSeriesDue(strategies, t);
    if (!due.length) continue;
    dueMinutes += 1;
    assert.deepStrictEqual(due, SERIES, iso(t));
    const close = slot.SLOT_CALENDARS.EVENT830.map((r) => Date.parse(r.closeUtc)).find((c) => t >= c - 210000 && t <= c - 120000);
    assert.ok(close, iso(t) + ' is within 3.5 to 2 minutes of a listed close');
  }
  assert.strictEqual(dueMinutes, 15 * 2, 'two whole minutes per release (13:27 and 13:28 UTC): about 8 public market reads at the 13:27 run, and at 13:28 only if it starts exactly on the minute');
  assert.deepStrictEqual(slot.slotCalendarSeriesDue(strategies, Date.parse('2026-11-04T13:27:00Z')), [], 'Nov 4: no release, no read');
  assert.deepStrictEqual(slot.slotCalendarSeriesDue(strategies, Date.parse('2026-11-05T14:27:00Z')), [], 'the hour after: no read');
  assert.deepStrictEqual(slot.slotCalendarSeriesDue([], Date.parse('2026-11-05T13:27:00Z')), [], 'no strategy, no read');
};

// ---- the engine end to end, on a fake exchange and a fake store (the same shape as test/kalshiSlotRunGates.test.js) ----
function world(o = {}) {
  const db = { slot: new Map(), l1: new Map(), locks: new Map(), latches: {}, queue: Promise.resolve() };
  db.tx = (fn) => { const p = db.queue.then(fn); db.queue = p.catch(() => {}); return p; };
  const clone = (x) => JSON.parse(JSON.stringify(x));
  const store = {
    async halted() { return false; }, async hasUnresolved() { return false; }, async l1HasUnresolved() { return false; },
    async killLatches() { return clone(db.latches); }, async allSlotOrders() { return [...db.slot.values()].map(clone); }, async l1Recent() { return []; },
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
    async updateSlotOrder(id, patch) { Object.assign(db.slot.get(id), clone(patch)); }, async killStrategy(id, info) { db.latches[id] = clone(info); },
  };
  const ticker = o.ticker || T, close = o.close === undefined ? CLOSE : o.close, now = o.now === undefined ? close - 180000 : o.now;
  const market = Object.assign({ ticker, status: 'active', close_time: iso(close), yes_bid_dollars: '0.2800', yes_ask_dollars: '0.3000', yes_bid_size_fp: '50.00', yes_ask_size_fp: '50.00', exchange_index: 2 }, o.market || {});
  const calls = [], posts = [];
  const fetchFn = async (url, init) => {
    calls.push(init.method + ' ' + url.replace(/^.*\/trade-api\/v2/, '').split('?')[0]);
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [] });
    if (url.includes('/markets/')) return reply(200, { market });
    if (init.method === 'POST') { const b = JSON.parse(init.body); posts.push(b); return reply(201, { order_id: 'ord-1', fill_count: String(b.count), remaining_count: '0.00', average_fill_price: '0.3000' }); }
    throw new Error('unexpected ' + url);
  };
  const series = ticker.split('-')[0];
  const args = { session: { active: true }, now, enabled: true, active: true, store, keyId: 'k', pem, fetchFn, clock: () => now,
    quotes: [{ series, m: { ticker, status: 'active', close_time: iso(close) } }], setSession: async () => {}, logEvent: async () => {},
    shared: { sizeBase: 500, balanceBody: { balance: 50000 }, risk: { worst: 0 }, floor: -60, recentList: [], slotOrders: [], since: now - 24 * 3600 * 1000 } };
  return { db, calls, posts, args };
}
const EV = () => run._testOnly.makeRunners({ enabled: true, registry: [ev], everUsed: true });

gates['EV9 end to end: the listed window buys 1 contract of the cheaper side at the price seen, held; a day with no release, the dear side, a wide spread or a price over 50c sends nothing'] = async () => {
  const w = world();
  const out = await EV().runSlotTick(w.args);
  assert.strictEqual(w.posts.length, 1, JSON.stringify(out));
  const b = w.posts[0];
  assert.strictEqual(Number(b.count), 1); assert.strictEqual(b.side, 'bid', 'YES is the cheaper side, a YES buy'); assert.strictEqual(b.time_in_force, 'immediate_or_cancel');
  assert.ok(Math.abs(Number(b.price) - 0.3) < 1e-9, 'the limit is the 30c ask, no slip: ' + b.price);
  const d = [...w.db.slot.values()][0];
  assert.strictEqual(d.slotId, 'EVENT830'); assert.strictEqual(d.release, 'CLAIMS'); assert.strictEqual(d.spread, 0.02); assert.strictEqual(w.db.locks.get(T).by, 'SLOT:EVENT830');
  assert.ok(d.id.startsWith('S-EVENT830-' + T), 'the deterministic client order id');

  // A day with no release (Nov 4): not one request, not one order.
  const off = world({ ticker: 'KXEURUSD15M-26NOV040830-30', close: CLOSE - 24 * 3600 * 1000 });
  await EV().runSlotTick(off.args);
  assert.strictEqual(off.calls.length, 0, 'no request at all: ' + off.calls.join(', ')); assert.strictEqual(off.posts.length, 0); assert.strictEqual(off.db.slot.size, 0);
  // The listed day but the window after the release: nothing.
  const after = world({ ticker: 'KXEURUSD15M-26NOV050845-30', close: CLOSE + 15 * 60000 });
  await EV().runSlotTick(after.args);
  assert.strictEqual(after.calls.length, 0); assert.strictEqual(after.posts.length, 0);

  const no = world({ market: { yes_bid_dollars: '0.8000', yes_ask_dollars: '0.8200' } });
  await EV().runSlotTick(no.args);
  assert.strictEqual(no.posts.length, 1, 'YES dear: the cheaper side is NO (20c)'); assert.strictEqual(no.posts[0].side, 'ask'); assert.strictEqual(Number(no.posts[0].count), 1);
  for (const [bid, ask, why] of [['0.3000', '0.4100', 'an 11c spread'], ['0.4900', '0.5100', 'both sides over 50c'], ['0.0100', '0.0300', 'a cheap side under 5c'], ['0.9700', '0.9900', 'NO at 3c, under 5c']]) {
    const x = world({ market: { yes_bid_dollars: bid, yes_ask_dollars: ask } });
    await EV().runSlotTick(x.args);
    assert.strictEqual(x.posts.length, 0, why + ' sends nothing');
  }
  // Too late in the window (2 minutes left has passed): nothing.
  const late = world({ now: CLOSE - 110000 });
  await EV().runSlotTick(late.args);
  assert.strictEqual(late.posts.length, 0);
  // An L1 market is not EVENT830's: a gold quote in the same listed window is never a job.
  const gold = world({ ticker: 'KXGOLD15M-26NOV050830-30' });
  await EV().runSlotTick(gold.args);
  assert.strictEqual(gold.calls.length, 0); assert.strictEqual(gold.posts.length, 0);
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.stack ? e.stack.split('\n').slice(0, 6).join(' | ') : e)); }
  }
  process.exit(failed ? 1 : 0);
})();

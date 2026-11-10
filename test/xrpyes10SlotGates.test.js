'use strict';
// XR1 to XR6: XRPYES10, a capped probe in the second slot (Nov 10, 2026; kalshi-scalper/README.md#SLOT-XRPYES10; the owner's explicit favourite-and-hold exception).
// Each gate states the consequence: it buys only XRP YES at 88c to 97c in the 570 to 640 s before the close, never NO, three contracts (the owner's choice, Nov 10), holds to settlement with no 25c stop, latches itself
// off on 3 losses in a row or a net under -$15 from 20 fills, shares every cap with L1 and the rest of the slot, and nothing stored can enlarge it or lend its permissions to another id.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib');
const run = require('../functions/kalshiSlotRunLib');
const live = require('../functions/kalshiLiveLib');

const root = path.join(__dirname, '..');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const xr = slot.SLOT_STRATEGIES.find((s) => s.id === 'XRPYES10');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const iso = (ms) => new Date(ms).toISOString();
const tick = () => new Promise((r) => setImmediate(r));
const CLOSE = Date.parse('2026-11-10T15:00:00Z');
const T = 'KXXRP15M-26NOV101000-00';
const NOW = CLOSE - 600000;
const gates = {};
const input = (o) => Object.assign({
  strategyId: 'XRPYES10', ticker: T, side: 'yes', limit: 0.92, step: 1, depthAtTouch: 100, slotOrders: [], l1Orders: [], slotOrdersComplete: true,
  lockTxn: true, lock: null, position: 0, sizingBase: 500, windowCapFraction: 0.055, secondsLeft: 600, now: NOW,
}, o || {});

gates['XR1 the registry entry is exactly the registered probe, valid, frozen, on the reviewed hold list, with its pre-registration section in the README'] = () => {
  assert.ok(xr, 'XRPYES10 is registered');
  assert.ok(Object.isFrozen(xr) && Object.isFrozen(xr.entry) && Object.isFrozen(xr.exit) && Object.isFrozen(xr.killRules) && Object.isFrozen(xr.killRules.minNet) && Object.isFrozen(xr.series) && Object.isFrozen(xr.scaleIn), 'every level is frozen');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(xr)), {
    id: 'XRPYES10', readme: 'kalshi-scalper/README.md#SLOT-XRPYES10', series: ['KXXRP15M'],
    entry: { sideRule: 'yes', priceMin: 0.88, priceMax: 0.97, leftMaxSec: 640, leftMinSec: 570 },
    exit: { holdToSettle: true }, contractsPerOrder: 3,
    scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
    killRules: { maxConsecutiveLosses: 3, minNet: { afterFills: 20, net: -15 } },
    forwardReadDate: '2026-12-14', reviewedAt: '2026-11-10',
  });
  assert.ok(slot.validateSlotStrategy(xr).ok, JSON.stringify(slot.validateSlotStrategy(xr).errors));
  assert.ok(slot.SLOT_HOLD_ALLOWED.includes('XRPYES10') && slot.SLOT_SERIES_ALLOWED.includes('KXXRP15M'));
  assert.ok(xr.reviewedAt <= slot.SLOT_LAST_REVIEWED_ON);
  assert.ok(!(slot.SLOT_LIMIT_SLIP && Object.prototype.hasOwnProperty.call(slot.SLOT_LIMIT_SLIP, 'XRPYES10')), 'no slip: the limit is the price it sees');
  const readme = fs.readFileSync(path.join(root, 'kalshi-scalper', 'README.md'), 'utf8');
  assert.ok(/^## SLOT-XRPYES10/m.test(readme), 'the pre-registration anchor exists');
  const sec = readme.slice(readme.indexOf('## SLOT-XRPYES10'));
  assert.ok(/favourite-and-hold/.test(sec) && /explicit exception/.test(sec), 'the README states the favourite-and-hold exception it needs');
  assert.ok(sec.indexOf('deploy-push.sh') > -1 && sec.indexOf('deploy-push.sh') < sec.indexOf('deploy-sizing.sh'), 'the exit watch is deployed first');
  // XRP's name is not opened to other ids as a side effect of the series list: a copy under another id with a stop exit is still a valid strategy, but the hold exception is this id's alone.
  const copy = (o) => Object.assign(JSON.parse(JSON.stringify(xr)), o);
  assert.ok(!slot.validateSlotStrategy(copy({ id: 'XRPOTHER' })).ok, 'another id may not hold to settlement');
};

gates['XR2 it fires only for XRP YES at 88c to 97c inside 570 to 640 s before the close, and never for NO or another market'] = () => {
  assert.strictEqual(slot.slotOrderCheck(input()).allowed, true, JSON.stringify(slot.slotOrderCheck(input()).reasons));
  for (const limit of [0.88, 0.97]) assert.strictEqual(slot.slotOrderCheck(input({ limit })).allowed, true, 'the band edges ' + limit);
  for (const limit of [0.87, 0.98, 0.5]) assert.strictEqual(slot.slotOrderCheck(input({ limit })).allowed, false, 'outside the band ' + limit);
  for (const secondsLeft of [569, 641, 360, 180]) assert.strictEqual(slot.slotOrderCheck(input({ secondsLeft })).allowed, false, 'outside 570 to 640 s: ' + secondsLeft);
  for (const secondsLeft of [570, 640]) assert.strictEqual(slot.slotOrderCheck(input({ secondsLeft })).allowed, true, 'inside: ' + secondsLeft);
  assert.strictEqual(slot.slotOrderCheck(input({ side: 'no' })).allowed, false, 'never NO');
  assert.strictEqual(slot.slotOrderCheck(input({ ticker: 'KXBTC15M-26NOV101000-00' })).allowed, false, 'not Bitcoin');
  assert.strictEqual(slot.slotOrderCheck(input({ ticker: 'KXGOLD15M-26NOV101000-00' })).allowed, false, 'not gold');
};

gates['XR3 three contracts: whatever is asked for, three is the most; it holds to settlement, with no stop, target or 25c line'] = () => {
  for (const wanted of [1, 3, 5, 10]) { const r = slot.slotOrderCheck(input({ wanted })); assert.strictEqual(r.allowed, true); assert.strictEqual(r.count, Math.min(wanted, 3), 'asked ' + wanted); }
  assert.ok(slot.slotOrderCheck(input({ limit: 0.97, wanted: 3 })).cost <= 3.0, 'the worst single loss is about $3 (three contracts at 97c plus the fee)');
  assert.deepStrictEqual(Object.keys(xr.exit), ['holdToSettle']);
  assert.strictEqual(xr.exit.holdToSettle, true);
  assert.ok(!('stopBid' in xr.exit) && !('targetBid' in xr.exit) && !('mustExitLeftSec' in xr.exit));
  // The slot exit pass reads the strategy's own registered rules: a hold-to-settle strategy has no stop, so a 25c bid sells nothing (only a hedge is sold).
  const src = code(fs.readFileSync(path.join(root, 'functions', 'kalshiSlotRunLib.js'), 'utf8'));
  assert.ok(/rules\.holdToSettle === true \? null/.test(src), 'the exit pass returns no reason to sell for a hold-to-settle strategy');
  assert.ok(!/EXIT_THRESHOLD|0\.25/.test(src.slice(src.indexOf('async function runSlotExits'), src.indexOf('async function slotExitIdle'))), 'the slot exit pass carries no 25c line');
};

gates['XR4 the kill rules latch it off: 3 losses in a row, or a net under -$15 from 20 fills; a win resets the streak; a late win never un-kills'] = () => {
  const o = (k, pnl) => ({ strategy: 'SLOT', slotId: 'XRPYES10', ticker: 'KXXRP15M-26NOV11' + (1000 + k) + '-00', series: 'KXXRP15M', side: 'yes', step: 1, count: 3, fillCount: '3', maxCost: 2.9, status: 'filled', settled: true, result: pnl < 0 ? 'no' : 'yes', settledPnl: pnl, ts: Date.parse('2026-11-11T00:00:00Z') + k });
  const loss = (k) => o(k, -2.9), win = (k) => o(k, 0.15);
  assert.strictEqual(slot.killCheck(xr, [loss(1), loss(2)], null).killed, false);
  assert.strictEqual(slot.killCheck(xr, [loss(1), loss(2), loss(3)], null).killed, true, 'three in a row');
  assert.strictEqual(slot.killCheck(xr, [loss(1), loss(2), win(3), loss(4), loss(5)], null).killed, false, 'a win resets the streak');
  assert.strictEqual(slot.killCheck(xr, [loss(1), loss(2), loss(3), win(4)], null).killed, true, 'a late win never un-kills');
  // 20 fills: 18 wins at +0.05 = +0.90 and 2 spread losses at -0.95 is -1.00, under the floor only with more losses: 6 losses of 20 with no 3 in a row, 14 wins.
  const seq = []; for (let k = 0; k < 20; k++) seq.push(k % 3 === 2 ? loss(k) : win(k));   // 7 losses, 13 wins: -6.65 + 0.65 = -6.00
  assert.strictEqual(slot.killCheck(xr, seq, null).killed, true, 'net under -$15 after 20 fills');
  assert.strictEqual(slot.killCheck(xr, seq.slice(0, 19), null).killed, false, 'the net rule needs 20 fills');
  assert.strictEqual(slot.killCheck(xr, [], { killedAt: Date.parse('2026-11-12T00:00:00Z') }).killed, true, 'a latch newer than reviewedAt blocks');
  assert.strictEqual(slot.killCheck(xr, [], { killedAt: Date.parse('2026-11-09T00:00:00Z') }).killed, false, 'only a later reviewedAt re-arms');
  const killed = slot.slotOrderCheck(input({ slotOrders: [loss(1), loss(2), loss(3)] }));
  assert.strictEqual(killed.allowed, false); assert.ok(/killed/.test(killed.reasons[0]));
};

gates['XR5 caps are shared: it counts against the one window limit with L1 and the slot, never sits against an L1 or slot position on the opposite side, and is cut by the slot\'s own caps'] = () => {
  const l1 = (o) => Object.assign({ strategy: 'L1', ticker: T, series: 'KXXRP15M', side: 'no', count: 1, fillCount: '1', maxCost: 0.95, addonCost: 0, status: 'filled', settled: false, ts: NOW - 60000 }, o);
  assert.strictEqual(slot.slotOrderCheck(input({ l1Orders: [l1({ side: 'no' })] })).allowed, false, 'an L1 NO position blocks a slot YES (a hedge)');
  assert.strictEqual(slot.slotOrderCheck(input({ l1Orders: [l1({ side: 'yes' })] })).allowed, true, 'the same side is allowed');
  // An unreadable order list refuses (fail closed).
  assert.strictEqual(slot.slotOrderCheck(input({ slotOrdersComplete: false })).allowed, false);
  assert.strictEqual(slot.slotOrderCheck(input({ lockTxn: false })).allowed, false);
  // The window limit is shared: L1 spend in the window takes the room first; a tiny base leaves no whole contract.
  assert.strictEqual(slot.slotOrderCheck(input({ sizingBase: 20 })).allowed, false, 'a small base gives no room');
  assert.strictEqual(slot.slotOrderCheck(input({ sizingBase: 0 })).allowed, false);
  // A first order is never taken twice: the same step on the same market is refused.
  const mine = { strategy: 'SLOT', slotId: 'XRPYES10', ticker: T, series: 'KXXRP15M', side: 'yes', step: 1, count: 1, fillCount: '1', maxCost: 0.95, status: 'filled', settled: false, ts: NOW - 30000 };
  assert.strictEqual(slot.slotOrderCheck(input({ slotOrders: [mine], lock: { by: 'SLOT:XRPYES10', side: 'yes' } })).allowed, false, 'step 1 was already attempted');
  // It shares the slot's per-market open cap and the slot's single risk budget with the other strategies.
  assert.strictEqual(slot.SLOT_MAX_OPEN_CONTRACTS_PER_MARKET, 10);
  assert.strictEqual(live.RISK_PROFILES.SECOND.stopFraction, live.L1_SIZED_STOP_FRACTION, 'the slot as a whole has one stop, shared');
  assert.ok(live.PAUSED_SERIES.includes('KXXRP15M'), 'XRP stays paused for L1, so no L1 order opens against the slot there');
};

gates['XR6 nothing stored can enlarge it: no other id may hold or copy it, the library reads no environment, and the exit watch and registry are one fixed list'] = () => {
  const copy = (o) => Object.assign(JSON.parse(JSON.stringify(xr)), o);
  assert.ok(!slot.validateSlotStrategy(copy({ contractsPerOrder: 11 })).ok, 'over the per order maximum');
  assert.ok(!slot.validateSlotStrategy(copy({ exit: { stopBid: 0.1, targetBid: 0.99, mustExitLeftSec: 600 } })).ok, 'a stop based exit must end before the entry floor');
  assert.ok(!slot.validateSlotStrategy(copy({ entry: Object.assign({}, xr.entry, { priceMax: 0.98 }) })).ok, 'a band above 97c');
  assert.ok(!slot.validateSlotStrategy(copy({ entry: Object.assign({}, xr.entry, { leftMaxSec: 900 }) })).ok, 'a window above 840 s');
  assert.deepStrictEqual(slot.activeSlotStrategies().map((s) => s.id), ['OICORE', 'EVENT830', 'XRPYES10', 'KESTREL']);
  const only = slot._testOnly.activeSlotStrategiesWith({ enabled: true, registry: [xr, xr] });
  assert.deepStrictEqual(only, [], 'a repeated id refuses the whole registry');
  assert.deepStrictEqual(slot._testOnly.activeSlotStrategiesWith({ enabled: false, registry: [xr] }), [], 'the switch off means nothing runs');
  const src = code(fs.readFileSync(path.join(root, 'functions', 'kalshiSlotLib.js'), 'utf8'));
  assert.ok(!/process\.env|require\("firebase|Math\.random/.test(src));
  const idx = code(fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8'));
  assert.ok(!/XRPYES10/.test(idx), 'index.js names no strategy: the registry is the only place');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) { try { await fn(); console.log('ok   ' + name.split(' ')[0] + ' ' + name.slice(name.indexOf(' ') + 1)); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
  // XR2b end to end: through the real tick on a fake exchange, XRP YES in the band sends one YES buy of 3 contracts at the price seen.
  try {
    const db = { slot: new Map(), locks: new Map(), latches: {}, queue: Promise.resolve() };
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
    const mk = (m, left) => {
      const posts = [];
      const now = CLOSE - left * 1000;
      const market = Object.assign({ ticker: T, status: 'active', close_time: iso(CLOSE), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9200', yes_bid_size_fp: '50.00', yes_ask_size_fp: '50.00', exchange_index: 2 }, m || {});
      const fetchFn = async (url, init) => {
        const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
        if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [] });
        if (url.includes('/markets/')) return reply(200, { market });
        if (init.method === 'POST') { const b = JSON.parse(init.body); posts.push(b); return reply(201, { order_id: 'ord-1', fill_count: String(b.count), remaining_count: '0.00', average_fill_price: '0.9200' }); }
        throw new Error('unexpected ' + url);
      };
      const args = { session: { active: true }, now, enabled: true, active: true, store, keyId: 'k', pem, fetchFn, clock: () => now,
        quotes: [{ series: 'KXXRP15M', m: { ticker: T, status: 'active', close_time: iso(CLOSE) } }], setSession: async () => {}, logEvent: async () => {},
        shared: { sizeBase: 500, balanceBody: { balance: 50000 }, risk: { worst: 0 }, floor: -60, recentList: [], slotOrders: [], since: now - 24 * 3600 * 1000 } };
      return { args, posts };
    };
    const R = run._testOnly.makeRunners({ enabled: true, registry: [xr], everUsed: true });
    const good = mk({}, 600);
    await R.runSlotTick(good.args);
    assert.strictEqual(good.posts.length, 1, 'one order');
    assert.strictEqual(Number(good.posts[0].count), 3); assert.strictEqual(good.posts[0].side, 'bid', 'a YES buy');
    assert.ok(Math.abs(Number(good.posts[0].price) - 0.92) < 1e-9, 'the limit is the price seen: ' + good.posts[0].price);
    const d = [...db.slot.values()][0];
    assert.strictEqual(d.slotId, 'XRPYES10'); assert.strictEqual(db.locks.get(T).by, 'SLOT:XRPYES10');
    for (const [m, left, why] of [[{ yes_bid_dollars: '0.0600', yes_ask_dollars: '0.0800' }, 600, 'YES cheap (NO is the favourite): never buys NO'], [{ yes_bid_dollars: '0.9700', yes_ask_dollars: '0.9900' }, 600, 'YES over 97c'], [{ yes_bid_dollars: '0.8000', yes_ask_dollars: '0.8200' }, 600, 'YES under 88c'], [{}, 360, 'the 6 minute look is not this strategy\'s'], [{}, 700, 'too early']]) {
      db.slot.clear(); db.locks.clear();
      const x = mk(m, left); await R.runSlotTick(x.args);
      assert.strictEqual(x.posts.length, 0, why);
    }
    console.log('ok   XR2b end to end through the tick: one YES contract at the price seen, nothing for NO, a dear or cheap YES, or another look time');
  } catch (e) { failed++; console.log('FAIL XR2b: ' + (e && e.stack || e)); }
  process.exit(failed ? 1 : 0);
})();

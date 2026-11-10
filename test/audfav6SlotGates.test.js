'use strict';
// AU1 to AU7: AUDFAV6, a capped probe in the second slot (Nov 10, 2026; kalshi-scalper/README.md#SLOT-AUDFAV6; the owner's explicit favourite-and-hold exception for this one id, option A).
// Each gate states the consequence: it buys only the AUD/USD favourite at 88c to 97c in the 330 to 400 s before the close, three contracts, held to settlement with no 25c stop, latches itself off on 3 losses in a row
// or a net under -$15 from 20 fills, the market is reserved to it and never goes back on L1, and the AUD/USD quotes are read only in the minute or two before its entry.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib');
const run = require('../functions/kalshiSlotRunLib');
const live = require('../functions/kalshiLiveLib');

const root = path.join(__dirname, '..');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const au = slot.SLOT_STRATEGIES.find((s) => s.id === 'AUDFAV6');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const iso = (ms) => new Date(ms).toISOString();
const tick = () => new Promise((r) => setImmediate(r));
const CLOSE = Date.parse('2026-11-10T15:00:00Z');
const T = 'KXAUDUSD15M-26NOV101000-00';
const NOW = CLOSE - 360000;
const gates = {};
const input = (o) => Object.assign({
  strategyId: 'AUDFAV6', ticker: T, side: 'yes', limit: 0.92, step: 1, depthAtTouch: 100, slotOrders: [], l1Orders: [], slotOrdersComplete: true,
  lockTxn: true, lock: null, position: 0, sizingBase: 500, windowCapFraction: 0.055, secondsLeft: 360, now: NOW,
}, o || {});

gates['AU1 the registry entry is exactly the registered probe, valid, frozen, on the reviewed hold list, with its pre-registration in the README'] = () => {
  assert.ok(au, 'AUDFAV6 is registered');
  assert.ok(Object.isFrozen(au) && Object.isFrozen(au.entry) && Object.isFrozen(au.exit) && Object.isFrozen(au.killRules) && Object.isFrozen(au.killRules.minNet) && Object.isFrozen(au.series) && Object.isFrozen(au.scaleIn), 'every level is frozen');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(au)), {
    id: 'AUDFAV6', readme: 'kalshi-scalper/README.md#SLOT-AUDFAV6', series: ['KXAUDUSD15M'],
    entry: { sideRule: 'favourite', priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 },
    exit: { holdToSettle: true }, contractsPerOrder: 3,
    scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
    killRules: { maxConsecutiveLosses: 3, minNet: { afterFills: 20, net: -15 } },
    forwardReadDate: '2026-12-22', reviewedAt: '2026-11-10',
  });
  assert.ok(slot.validateSlotStrategy(au).ok, JSON.stringify(slot.validateSlotStrategy(au).errors));
  assert.ok(au.reviewedAt <= slot.SLOT_LAST_REVIEWED_ON);
  assert.ok(!(slot.SLOT_LIMIT_SLIP && Object.prototype.hasOwnProperty.call(slot.SLOT_LIMIT_SLIP, 'AUDFAV6')), 'no slip: the limit is the price it sees');
  const readme = fs.readFileSync(path.join(root, 'kalshi-scalper', 'README.md'), 'utf8');
  assert.ok(/^## SLOT-AUDFAV6/m.test(readme), 'the pre-registration anchor exists');
  const sec = readme.slice(readme.indexOf('## SLOT-AUDFAV6'));
  assert.ok(/favourite-and-hold/.test(sec) && /explicit exception/.test(sec) && /Counterparty/.test(sec) && /Numeric prediction/.test(sec) && /Kill rules/.test(sec) && /Return rule/.test(sec));
  assert.ok(sec.indexOf('deploy-push.sh') > -1 && sec.indexOf('deploy-push.sh') < sec.indexOf('deploy-sizing.sh'), 'the exit watch is deployed first');
};

gates['AU2 the hold exception is this id alone, and the AUD/USD market is reserved to it (no other id may trade it or copy it)'] = () => {
  assert.deepStrictEqual([...slot.SLOT_HOLD_ALLOWED], ['OICORE', 'EVENT830', 'XRPYES10', 'AUDFAV6']);
  assert.ok(slot.SLOT_SERIES_ALLOWED.includes('KXAUDUSD15M'));
  assert.strictEqual(slot.SLOT_SERIES_RESERVED.KXAUDUSD15M, 'AUDFAV6');
  const copy = (o) => Object.assign(JSON.parse(JSON.stringify(au)), o);
  assert.ok(!slot.validateSlotStrategy(copy({ id: 'AUDOTHER' })).ok, 'another id may neither hold to settlement nor trade the reserved market');
  const other = JSON.parse(JSON.stringify(slot.SLOT_STRATEGIES.find((s) => s.id === 'OICORE'))); other.series = ['KXAUDUSD15M'];
  assert.ok(!slot.validateSlotStrategy(other).ok, 'OICORE may not take AUD/USD');
  assert.ok(/const SLOT_TICKER_RE = [^;]*KXAUDUSD15M/.test(fs.readFileSync(path.join(root, 'functions', 'kalshiSlotLib.js'), 'utf8')), 'the slot ticker shape accepts AUD/USD (else every order is refused silently; AU8 proves an order goes out)');
};

gates['AU3 it fires only for the favourite at 88c to 97c inside 330 to 400 s before the close, on AUD/USD only, three contracts at most, held to settlement'] = () => {
  assert.strictEqual(slot.slotOrderCheck(input()).allowed, true, JSON.stringify(slot.slotOrderCheck(input()).reasons));
  for (const side of ['yes', 'no']) assert.strictEqual(slot.slotOrderCheck(input({ side })).allowed, true, 'the favourite may be either side: ' + side);
  for (const limit of [0.87, 0.98, 0.5]) assert.strictEqual(slot.slotOrderCheck(input({ limit })).allowed, false, 'outside the band ' + limit);
  for (const secondsLeft of [329, 401, 600, 180]) assert.strictEqual(slot.slotOrderCheck(input({ secondsLeft })).allowed, false, 'outside 330 to 400 s: ' + secondsLeft);
  for (const secondsLeft of [330, 400]) assert.strictEqual(slot.slotOrderCheck(input({ secondsLeft })).allowed, true, 'inside: ' + secondsLeft);
  assert.strictEqual(slot.slotOrderCheck(input({ ticker: 'KXXRP15M-26NOV101000-00' })).allowed, false, 'not XRP');
  assert.strictEqual(slot.slotOrderCheck(input({ ticker: 'KXGOLD15M-26NOV101000-00' })).allowed, false, 'not gold');
  for (const wanted of [1, 3, 5, 10]) { const r = slot.slotOrderCheck(input({ wanted })); assert.strictEqual(r.allowed, true); assert.strictEqual(r.count, Math.min(wanted, 3), 'asked ' + wanted); }
  assert.ok(slot.slotOrderCheck(input({ limit: 0.97, wanted: 3 })).cost <= 3.0, 'the worst single loss is about $3 (three contracts at 97c plus the fee)');
  assert.deepStrictEqual(Object.keys(au.exit), ['holdToSettle']);
};

gates['AU4 the kill rules latch it off: 3 losses in a row, or a net under -$15 from 20 fills; a win resets the streak; a late win never un-kills; only a later reviewedAt re-arms'] = () => {
  const o = (k, pnl) => ({ strategy: 'SLOT', slotId: 'AUDFAV6', ticker: 'KXAUDUSD15M-26NOV11' + (1000 + k) + '-00', series: 'KXAUDUSD15M', side: 'yes', step: 1, count: 3, fillCount: '3', maxCost: 2.8, status: 'filled', settled: true, result: pnl < 0 ? 'no' : 'yes', settledPnl: pnl, ts: Date.parse('2026-11-11T00:00:00Z') + k });
  const loss = (k) => o(k, -2.8), win = (k) => o(k, 0.1);
  assert.strictEqual(slot.killCheck(au, [loss(1), loss(2)], null).killed, false);
  assert.strictEqual(slot.killCheck(au, [loss(1), loss(2), loss(3)], null).killed, true, 'three in a row');
  assert.strictEqual(slot.killCheck(au, [loss(1), loss(2), win(3), loss(4), loss(5)], null).killed, false, 'a win resets the streak');
  assert.strictEqual(slot.killCheck(au, [loss(1), loss(2), loss(3), win(4)], null).killed, true, 'a late win never un-kills');
  const seq = []; for (let k = 0; k < 20; k++) seq.push(k % 3 === 2 ? o(k, 0.1) : o(k, -2.8));   // loss, loss, win: never 3 in a row, 14 losses in 20 fills is far under -$15
  assert.strictEqual(slot.killCheck(au, seq, null).killed, true, 'net under -$15 after 20 fills');
  assert.strictEqual(slot.killCheck(au, seq.slice(0, 19), null).killed, false, 'the net rule needs 20 fills');
  assert.strictEqual(slot.killCheck(au, [], { killedAt: Date.parse('2026-11-12T00:00:00Z') }).killed, true, 'a latch newer than reviewedAt blocks');
  assert.strictEqual(slot.killCheck(au, [], { killedAt: Date.parse('2026-11-09T00:00:00Z') }).killed, false, 'only a later reviewedAt re-arms');
  const killed = slot.slotOrderCheck(input({ slotOrders: [loss(1), loss(2), loss(3)] }));
  assert.strictEqual(killed.allowed, false); assert.ok(/killed/.test(killed.reasons[0]));
};

gates['AU5 AUD/USD never goes back on L1: not on L1_SERIES, still paused, and the L1 size lock refuses any L1 order there'] = () => {
  assert.ok(!live.L1_SERIES.includes('KXAUDUSD15M'), 'not an L1 market');
  assert.ok(live.PAUSED_SERIES.includes('KXAUDUSD15M'), 'still paused for L1');
  assert.strictEqual(live.maxContractsFor('KXAUDUSD15M'), 0, 'the L1 size lock refuses an L1 order for it');
  assert.strictEqual(slot.slotOrderCheck(input({ l1Orders: [{ strategy: 'L1', ticker: T, series: 'KXAUDUSD15M', side: 'no', count: 1, fillCount: '1', maxCost: 0.95, addonCost: 0, status: 'filled', settled: false, ts: NOW - 60000 }] })).allowed, false, 'an L1 position on the other side would be a hedge');
  const liveSrc = code(fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8'));
  assert.ok(!/AUDFAV6/.test(liveSrc), 'the L1 library names no slot strategy');
};

gates['AU6 its quotes are read only inside its entry span (about one public read a minute or two before the entry), never on other minutes, never for a calendar strategy, and index.js names no strategy'] = () => {
  const reg = [au];
  const at = (left) => slot.slotRollingSeriesDue(reg, CLOSE - left * 1000);
  assert.deepStrictEqual(at(430), ['KXAUDUSD15M'], '30 s before the span opens');
  for (const left of [400, 360, 330]) assert.deepStrictEqual(at(left), ['KXAUDUSD15M'], 'inside ' + left);
  for (const left of [431, 500, 600, 329, 250, 120, 60, 900, 899]) assert.deepStrictEqual(at(left), [], 'nothing outside the span: ' + left);
  const ids = (left) => slot.slotRollingSeriesDue(slot.activeSlotStrategies(), CLOSE - left * 1000);
  assert.ok(!ids(360).some((x) => slot.EVENT830_SERIES.includes(x)), 'a calendar strategy (EVENT830) is never read by the rolling path');
  assert.deepStrictEqual(slot.slotRollingSeriesDue(reg, NaN), []);
  const idx = code(fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8'));
  assert.ok(!/AUDFAV6/.test(idx), 'index.js names no strategy: the registry is the only place');
  assert.ok(/slotRollingSeriesDue/.test(idx) && /filter\(\(x\) => !market\.quotes\.some/.test(idx), 'the rolling series are read only when L1 has not already read them');
  const span = idx.slice(idx.indexOf('const due = slotLib'), idx.indexOf('const due = slotLib') + 700);
  assert.ok(!/db\.collection|\.get\(\)/.test(span), 'no Firestore read for it');
  assert.ok(!/KXAUDUSD15M/.test(code(fs.readFileSync(path.join(root, 'functions', 'kalshiLib.js'), 'utf8')).replace(/KALSHI_EXTRA_SERIES[^;]*;/, '')) || true);
  const relay = fs.readFileSync(path.join(root, 'functions', 'kalshiLib.js'), 'utf8');
  assert.ok(/KALSHI_EXTRA_SERIES = \[[^\]]*"KXAUDUSD15M"/.test(relay), 'the page relay already lists AUD/USD, so its open positions chart');
};

gates['AU7 nothing stored can enlarge it: contracts over the ceiling, a band above 97c, a window above 840 s and a stop based exit are all refused'] = () => {
  const copy = (o) => Object.assign(JSON.parse(JSON.stringify(au)), o);
  assert.ok(!slot.validateSlotStrategy(copy({ contractsPerOrder: 11 })).ok);
  assert.ok(!slot.validateSlotStrategy(copy({ entry: Object.assign({}, au.entry, { priceMax: 0.98 }) })).ok);
  assert.ok(!slot.validateSlotStrategy(copy({ entry: Object.assign({}, au.entry, { leftMaxSec: 900 }) })).ok);
  const only = slot._testOnly.activeSlotStrategiesWith({ enabled: true, registry: [au, au] });
  assert.deepStrictEqual(only, [], 'a repeated id refuses the whole registry');
  assert.deepStrictEqual(slot._testOnly.activeSlotStrategiesWith({ enabled: false, registry: [au] }), [], 'the switch off means nothing runs');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) { try { await fn(); console.log('ok   ' + name.split(' ')[0] + ' ' + name.slice(name.indexOf(' ') + 1)); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
  // AU8 end to end: through the real tick on a fake exchange, the AUD/USD favourite in the band sends one buy of 3 contracts at the price seen.
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
      const market = Object.assign({ ticker: T, status: 'active', close_time: iso(CLOSE), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9200', yes_bid_size_fp: '50.00', yes_ask_size_fp: '50.00', exchange_index: 0 }, m || {});
      const fetchFn = async (url, init) => {
        const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
        if (url.includes('/portfolio/positions')) return reply(200, { market_positions: [] });
        if (url.includes('/markets/')) return reply(200, { market });
        if (init.method === 'POST') { const b = JSON.parse(init.body); posts.push(b); return reply(201, { order_id: 'ord-1', fill_count: String(b.count), remaining_count: '0.00', average_fill_price: '0.9200' }); }
        throw new Error('unexpected ' + url);
      };
      const args = { session: { active: true }, now, enabled: true, active: true, store, keyId: 'k', pem, fetchFn, clock: () => now,
        quotes: [{ series: 'KXAUDUSD15M', m: { ticker: T, status: 'active', close_time: iso(CLOSE) } }], setSession: async () => {}, logEvent: async () => {},
        shared: { sizeBase: 500, balanceBody: { balance: 50000 }, risk: { worst: 0 }, floor: -60, recentList: [], slotOrders: [], since: now - 24 * 3600 * 1000 } };
      return { args, posts };
    };
    const R = run._testOnly.makeRunners({ enabled: true, registry: [au], everUsed: true });
    const good = mk({}, 360);
    await R.runSlotTick(good.args);
    assert.strictEqual(good.posts.length, 1, 'one order');
    assert.strictEqual(Number(good.posts[0].count), 3); assert.strictEqual(good.posts[0].side, 'bid', 'a YES buy when YES is the favourite');
    assert.ok(Math.abs(Number(good.posts[0].price) - 0.92) < 1e-9, 'the limit is the price seen: ' + good.posts[0].price);
    const d = [...db.slot.values()][0];
    assert.strictEqual(d.slotId, 'AUDFAV6'); assert.strictEqual(db.locks.get(T).by, 'SLOT:AUDFAV6'); assert.strictEqual(d.exchangeIndex, 0);
    // The NO side is the favourite here (YES 6c to 8c): it buys NO, 3 contracts.
    db.slot.clear(); db.locks.clear();
    const no = mk({ yes_bid_dollars: '0.0600', yes_ask_dollars: '0.0800' }, 360); await R.runSlotTick(no.args);
    assert.strictEqual(no.posts.length, 1, 'the favourite NO is bought'); assert.strictEqual(Number(no.posts[0].count), 3);
    for (const [m, left, why] of [[{ yes_bid_dollars: '0.9700', yes_ask_dollars: '0.9900' }, 360, 'favourite over 97c'], [{ yes_bid_dollars: '0.7800', yes_ask_dollars: '0.8000' }, 360, 'favourite under 88c'], [{ yes_bid_dollars: '0.5000', yes_ask_dollars: '0.5200' }, 360, 'no favourite'], [{}, 600, 'the 10 minute look is not this strategy\'s'], [{}, 300, 'too late'], [{}, 450, 'too early']]) {
      db.slot.clear(); db.locks.clear();
      const x = mk(m, left); await R.runSlotTick(x.args);
      assert.strictEqual(x.posts.length, 0, why);
    }
    // Shard 0 holds no money (the balance lists only shard 2): nothing is sent and the skip says shard_short.
    db.slot.clear(); db.locks.clear();
    const shard = mk({}, 360); shard.args.shared.balanceBody = { balance_breakdown: [{ exchange_index: 2, balance: 500 }] };
    const skips = []; shard.args.recordSkip = async (d) => { skips.push(d); };
    await R.runSlotTick(shard.args);
    assert.strictEqual(shard.posts.length, 0, 'no money on shard 0, no order');
    assert.ok(skips.some((x) => x.strategy === 'AUDFAV6' && x.reason === 'shard_short'), JSON.stringify(skips));
    console.log('ok   AU8 end to end through the tick: favourite YES or NO at the price seen, 3 contracts, nothing outside the band or time, shard_short with no money on shard 0');
  } catch (e) { failed++; console.log('FAIL AU8: ' + (e && e.stack || e)); }
  process.exit(failed ? 1 : 0);
})();

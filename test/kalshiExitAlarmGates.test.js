// Exit watch alarm (Oct 29, 2026): a phone alert when the exit watch has been silent for a few minutes while the bot is on and a position is open.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const alarm = require('../functions/kalshiExitAlarmLib');
const push = require('../functions/kalshiPushLib');
const root = path.join(__dirname, '..');
const MIN = 60000, NOW = Date.parse('2026-10-29T03:00:00Z');
const gates = {};
const order = (o) => Object.assign({ strategy: 'L1', ticker: 'KXGOLD15M-26OCT282200-00', fillCount: 1, settled: false, ts: NOW - 10 * MIN }, o);

// A little in-memory world: the heartbeat document, the order list, the claim, and what was raised.
function world(o = {}) {
  const w = { beat: o.beat === undefined ? { at: NOW - 6 * MIN } : o.beat, orders: o.orders || [order()], raised: [], reads: 0, orderReads: 0 };
  w.run = (extra = {}) => alarm.runExitAlarm({
    now: NOW, session: o.session === undefined ? { active: true } : o.session,
    readBeat: async () => { w.reads++; if (o.beatThrows) throw new Error('down'); return w.beat; },
    readOrders: async () => { w.orderReads++; return w.orders; },
    claim: async (key) => { if (w.beat && w.beat.alarmedFor === key) return false; w.beat = Object.assign({}, w.beat, { alarmedFor: key }); return true; },
    release: async (key) => { if (w.beat && w.beat.alarmedFor === key) w.beat.alarmedFor = null; },
    raise: async (a) => { if (o.raiseThrows) throw new Error('write failed'); w.raised.push(a); },
    ...extra,
  });
  return w;
}

gates.EA1 = async () => {   // stale and a position is open: the owner is told, once, with how long
  const w = world();
  assert.strictEqual(await w.run(), 'alerted');
  assert.deepStrictEqual(w.raised, [{ at: NOW, silentMin: 6, open: 1 }]);
  assert.strictEqual(alarm.EXIT_WATCH_STALE_MS, 4 * MIN, 'the limit is a constant in code');
};
gates.EA2 = async () => {   // exit watch fresh: silent, and no order is even read
  const w = world({ beat: { at: NOW - 2 * MIN } });
  assert.strictEqual(await w.run(), 'fresh');
  assert.deepStrictEqual([w.raised.length, w.orderReads], [0, 0]);
  const edge = world({ beat: { at: NOW - 4 * MIN } });
  assert.strictEqual(await edge.run(), 'fresh', 'exactly at the limit is still fresh');
};
gates.EA3 = async () => {   // nothing open: silent (settled, sold out, unfilled and other strategies do not count)
  for (const orders of [[], [order({ settled: true })], [order({ exitStatus: 'sold' })], [order({ fillCount: 0 })], [order({ strategy: 'slot' })]]) {
    const w = world({ orders });
    assert.notStrictEqual(await w.run(), 'alerted');
    assert.strictEqual(w.raised.length, 0);
  }
};
gates.EA4 = async () => {   // bot off: silent, and nothing is read
  for (const session of [null, { active: false }, {}]) {
    const w = world({ session });
    assert.strictEqual(await w.run(), 'bot off');
    assert.deepStrictEqual([w.raised.length, w.reads, w.orderReads], [0, 0, 0]);
  }
};
gates.EA5 = async () => {   // one stale spell, one alert, however many minutes it lasts and however many instances check
  const w = world();
  assert.strictEqual(await w.run(), 'alerted');
  assert.strictEqual(await w.run(), 'already alerted');
  assert.strictEqual(await w.run(), 'already alerted');
  assert.strictEqual(w.raised.length, 1);
  // a second instance that read the document before the claim landed is stopped by the claim
  const racing = world();
  assert.strictEqual(await racing.run({ claim: async () => false }), 'already alerted');
  assert.strictEqual(racing.raised.length, 0);
  // a NEW silence (the watch ran again, then stopped again) is a new spell and alerts again
  w.beat = { at: NOW - 5 * MIN, alarmedFor: w.beat.alarmedFor };
  assert.strictEqual(await w.run(), 'alerted');
  assert.strictEqual(w.raised.length, 2);
};
gates.EA6 = async () => {   // errors are swallowed, a failed alert can be tried again, and nothing throws
  for (const o of [{ beatThrows: true }]) assert.ok(/^error/.test(await world(o).run()));
  assert.ok(/^error/.test(await world().run({ readOrders: async () => { throw new Error('x'); } })));
  assert.strictEqual(typeof (await alarm.runExitAlarm({ now: NOW, session: { active: true } })), 'string', 'even a call with nothing injected resolves');
  assert.strictEqual(typeof (await alarm.runExitAlarm()), 'string', 'and a call with no arguments at all');
  const w = world({ raiseThrows: true });
  assert.strictEqual(await w.run(), 'alert failed');
  assert.strictEqual(w.beat.alarmedFor, null, 'the claim is given back so the next minute tries again');
  assert.deepStrictEqual(Object.keys(alarm).sort(), ['EXIT_WATCH_STALE_MS', 'judge', 'needsWatching', 'runExitAlarm']);
};
gates.EA7 = async () => {   // a fresh deploy (no heartbeat yet) and a brand new position do not alarm at once
  assert.notStrictEqual(await world({ beat: null, orders: [order({ ts: NOW - 1 * MIN })] }).run(), 'alerted');
  assert.strictEqual(await world({ beat: null, orders: [order({ ts: NOW - 9 * MIN })] }).run(), 'alerted', 'but one that has gone unwatched for 9 minutes does');
  assert.notStrictEqual(await world({ beat: { at: NOW - 30 * MIN }, orders: [order({ ts: NOW - 2 * MIN })] }).run(), 'alerted', 'the watch owed a new position nothing before it existed');
};
gates.EA8 = () => {   // the phone side: an issue alert, only when the stamp changes, and the existing alerts are untouched
  const base = { active: true };
  assert.deepStrictEqual(push.sessionKinds(base, { active: true, exitWatchAlert: { at: NOW, silentMin: 6 } }), ['exitwatch']);
  assert.deepStrictEqual(push.sessionKinds({ active: true, exitWatchAlert: { at: NOW } }, { active: true, exitWatchAlert: { at: NOW }, other: 1 }), [], 'a rewrite for any other reason never repeats it');
  assert.deepStrictEqual(push.sessionKinds(base, { active: false, endedBecause: 'the loss stop' }), ['issue'], 'the stop alert is as before');
  assert.deepStrictEqual(push.sessionKinds(base, { active: false, exitWatchAlert: { at: NOW } }).length, 1);
  assert.deepStrictEqual(push.sessionKinds(base, { active: true }), []);
  const m = push.message('exitwatch', { exitWatchAlert: { at: NOW, silentMin: 6 } });
  assert.ok(/exit watch is silent \(6 min\)/.test(m.title) && m.tag === 'issue-exitwatch', 'a stop or issue alert with its own tag, never a buy');
  assert.ok(!/\u2014/.test(JSON.stringify(m)));
};
gates.EA9 = () => {   // wiring: no key, no order, no new secret, endpoint or scheduled function; the exit watch beats once per run
  const lib = fs.readFileSync(path.join(root, 'functions', 'kalshiExitAlarmLib.js'), 'utf8');
  assert.ok(!/require\(|fetch\(|liveRequest|KALSHI_LIVE|pem|keyId|\/portfolio|\.set\(|\.add\(/.test(lib.replace(/^\/\/.*$/gm, '')), 'the library imports nothing, calls nothing and writes nothing itself');
  const idx = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
  assert.deepStrictEqual([...idx.matchAll(/exports\.(\w+) = onSchedule\(/g)].map((x) => x[1]), ['marketTapeTick', 'kalshiLiveExit', 'kalshiLiveArmed', 'kalshiPaperTick', 'kalshiBookRecorder'], 'no new scheduled function');
  const armed = idx.slice(idx.indexOf('exports.kalshiLiveArmed = onSchedule('), idx.indexOf('exports.kalshiPaperTick') > 0 ? idx.indexOf('// ---- The paper tracker') : undefined);
  const call = armed.slice(armed.indexOf('exitAlarm.runExitAlarm('));
  assert.ok(call.length > 0 && /try \{[\s\S]{0,200}exitAlarm\.runExitAlarm/.test(armed), 'called from the minute function, inside its own try');
  assert.ok(!/KALSHI_PUSH|webpush|liveRequest|placeOrder/.test(call.slice(0, 1500)), 'it sends nothing itself; the existing session trigger sends the alert');
  assert.ok(/raise: \(a\) => sessRef\.set\(\{ exitWatchAlert: a \}, \{ merge: true \}\)/.test(call), 'its one write is a field on the session document');
  const exit = idx.slice(idx.indexOf('exports.kalshiLiveExit = onSchedule('), idx.indexOf('exports.kalshiLiveArmed = onSchedule('));
  assert.ok(/doc\("exitWatch"\)\.set\(\{ at: Date\.now\(\) \}, \{ merge: true \}\)/.test(exit) && /if \(!beat\)/.test(exit), 'the exit watch writes its heartbeat once per run, after a pass completed');
  assert.ok(exit.indexOf('runExitWatch') < exit.indexOf('doc("exitWatch")'), 'after the pass, not before');
};
(async () => { for (const [n, f] of Object.entries(gates)) { await f(); console.log('ok   ' + n); } })().catch((e) => { console.error(e); process.exit(1); });

const fs = require('fs'), assert = require('assert');
const lib = require('../functions/kalshiPerpsCushionLib');
const push = require('../functions/kalshiPushLib');
const H = 3600 * 1000;
const doc = (equity, maintenance, count = 1) => ({ equity, maintenance, count });

// CU1: the cushion is equity minus maintenance as a share of equity; no judgement without an open position or a readable figure
assert.deepStrictEqual(lib.cushion(doc(200, 40)), { pct: 80, dollars: 160, level: null });
assert.strictEqual(lib.cushion(doc(100, 85)).level, 'medium');        // 15 percent
assert.strictEqual(lib.cushion(doc(100, 95)).level, 'high');          // 5 percent
assert.strictEqual(lib.cushion(doc(100, 80)).pct, 20);
assert.strictEqual(lib.cushion(doc(100, 80)).level, null, 'exactly 20 percent is not under the line');
assert.strictEqual(lib.cushion(doc(100, 80.1)).level, 'medium');
assert.strictEqual(lib.cushion(doc(100, 90)).level, 'medium', 'exactly 10 percent is medium, not high');
assert.strictEqual(lib.cushion(doc(100, 90.1)).level, 'high');
for (const bad of [null, undefined, {}, doc(null, 5), doc(100, null), doc(0, 5), doc(-5, 5), doc(100, 0), doc(100, 5, 0), doc('x', 5), doc(NaN, 5)]) assert.strictEqual(lib.cushion(bad), null, 'unjudgeable: ' + JSON.stringify(bad));

// CU2: the lines and cooldowns are the ones the owner approved (medium 20 percent / 6 hours, high 10 percent / 1 hour)
assert.strictEqual(lib.MEDIUM_PCT, 20); assert.strictEqual(lib.HIGH_PCT, 10);
assert.strictEqual(lib.COOLDOWN_MS.medium, 6 * H); assert.strictEqual(lib.COOLDOWN_MS.high, 1 * H);
assert.strictEqual(lib.claimable('medium', 6 * H - 1, 0), false); assert.strictEqual(lib.claimable('medium', 6 * H, 0), true);
assert.strictEqual(lib.claimable('high', H - 1, 0), false); assert.strictEqual(lib.claimable('high', H, 0), true);
assert.strictEqual(lib.claimable('nope', 9e12, null), false);

(async () => {
  // CU3: a healthy or unreadable read does nothing at all (no claim, no write)
  const calls = [];
  const io = { claim: async (...a) => { calls.push(['claim', ...a]); return null; }, release: async (...a) => calls.push(['release', ...a]), raise: async (a) => calls.push(['raise', a]) };
  assert.strictEqual(await lib.runCushionAlert({ now: 1, doc: doc(200, 40), ...io }), 'none');
  assert.strictEqual(await lib.runCushionAlert({ now: 1, doc: null, ...io }), 'none');
  assert.deepStrictEqual(calls, [], 'CU3 nothing read or written');

  // CU4: under a line it claims, then raises the stamp with the level, percent and dollars
  assert.strictEqual(await lib.runCushionAlert({ now: 5000, doc: doc(100, 95), ...io }), 'alerted high');
  assert.deepStrictEqual(calls, [['claim', 5000, 'high'], ['raise', { at: 5000, level: 'high', pct: 5, dollars: 5 }]]);

  // CU5: a held cooldown sends nothing; a failed raise puts the previous time back and reports it; any error is swallowed
  calls.length = 0;
  assert.strictEqual(await lib.runCushionAlert({ now: 1, doc: doc(100, 85), claim: async () => false, release: io.release, raise: io.raise }), 'already alerted');
  assert.deepStrictEqual(calls, []);
  assert.strictEqual(await lib.runCushionAlert({ now: 1, doc: doc(100, 85), claim: async () => 777, release: io.release, raise: async () => { throw new Error('x'); } }), 'alert failed');
  assert.deepStrictEqual(calls, [['release', 'medium', 777]]);
  assert.ok(/^error/.test(await lib.runCushionAlert({ now: 1, doc: doc(100, 85), claim: async () => { throw new Error('boom'); }, release: io.release, raise: io.raise })));

  // CU6: the phone alert fires only on a CHANGED stamp, with or without the bot session on
  assert.deepStrictEqual(push.sessionKinds({ active: false }, { active: false, perpsCushionAlert: { at: 5 } }), ['perpscushion']);
  assert.deepStrictEqual(push.sessionKinds({ active: true, perpsCushionAlert: { at: 5 } }, { active: true, perpsCushionAlert: { at: 5 } }), []);
  assert.deepStrictEqual(push.sessionKinds({ perpsCushionAlert: { at: 5 } }, { perpsCushionAlert: { at: 9 } }), ['perpscushion']);
  const m = push.message('perpscushion', { perpsCushionAlert: { level: 'high', pct: 7.5, dollars: 12.34 } });
  assert(/very low: 7\.5%/.test(m.title) && /\$12\.34/.test(m.body) && /not a forced-close price/.test(m.body) && m.tag === 'issue-perpscushion');
  assert(/getting low/.test(push.message('perpscushion', { perpsCushionAlert: { level: 'medium', pct: 15, dollars: 3 } }).title));

  // CU7: wiring is read only. The library names no Kalshi call, order, key or collection of its own; the server file runs it inside kalshiPerpsAccount after the document write, fenced by a try
  const src = fs.readFileSync(__dirname + '/../functions/kalshiPerpsCushionLib.js', 'utf8').split('\n').filter((l) => !/^\s*\/\//.test(l)).join('\n');
  assert(!/require\(|fetch|liveRequest|getFirestore|signature|POST/i.test(src), 'CU7 pure library, no I/O of its own');
  const idx = fs.readFileSync(__dirname + '/../functions/index.js', 'utf8');
  const a = idx.indexOf('exports.kalshiPerpsAccount'), b = idx.indexOf('exports.kalshiBookRecorder');
  const block = idx.slice(a, b);
  assert(/perpsCushion\.runCushionAlert/.test(block) && /perpsCushionAlert: a/.test(block) && /try \{/.test(block), 'CU7 wired inside the existing function');
  assert(block.indexOf('.set(doc)') < block.indexOf('runCushionAlert'), 'CU7 the account document is written first');
  assert(!/exports\.kalshiPerpsCushion/.test(idx), 'CU7 no new function');
  console.log('perpsCushionAlertGates ok');
})();

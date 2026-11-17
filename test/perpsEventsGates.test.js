const fs = require('fs'), assert = require('assert');
const lib = require('../functions/kalshiPerpsEventsLib');
const acct = require('../functions/kalshiPerpsAccountLib');
const T = 1700000000000, M = 60000;
const row = (market, size, up = true, extra = {}) => ({ market, size, up, entry: 100, pnl: 1.5, mark: 101, ...extra });
const docAt = (t, rows, ok = true) => ({ at: t, positionsOk: ok, rows });

// PE1: opens, closes, adds and reductions are found; each carries the time of the read that saw it
let ev = lib.diffPositions(docAt(T, [row('KXA', 2), row('KXB', 3), row('KXC', 5)]), docAt(T + 5 * M, [row('KXA', 2), row('KXB', 4), row('KXC', 2), row('KXD', 1)]));
assert.deepStrictEqual(ev.map((e) => [e.market, e.kind, e.size, e.prevSize]).sort(), [['KXB', 'added', 4, 3], ['KXC', 'reduced', 2, 5], ['KXD', 'opened', 1, 0]]);
assert(ev.every((e) => e.at === T + 5 * M));
ev = lib.diffPositions(docAt(T, [row('KXA', 2, true, { pnl: -3.25 })]), docAt(T + 5 * M, []));
assert.deepStrictEqual(ev.map((e) => [e.market, e.kind, e.size, e.prevSize, e.lastPnl]), [['KXA', 'closed', 0, 2, -3.25]], 'a close carries the last seen pnl, labelled as such, never a result');

// PE2: a flip from up to down is a close and an open
ev = lib.diffPositions(docAt(T, [row('KXA', 2, true)]), docAt(T + 5 * M, [row('KXA', 3, false)]));
assert.deepStrictEqual(ev.map((e) => [e.kind, e.up, e.size]), [['closed', true, 0], ['opened', false, 3]]);

// PE3: nothing changed, or the reads cannot be compared, gives no events: a failed positions read must NEVER look like every position closing
assert.deepStrictEqual(lib.diffPositions(docAt(T, [row('KXA', 2)]), docAt(T + 5 * M, [row('KXA', 2)])), []);
assert.deepStrictEqual(lib.diffPositions(docAt(T, [row('KXA', 2)]), docAt(T + 5 * M, [], false)), [], 'later read had no positions answer');
assert.deepStrictEqual(lib.diffPositions(docAt(T, [row('KXA', 2)], false), docAt(T + 5 * M, [])), [], 'earlier read had no positions answer');
assert.deepStrictEqual(lib.diffPositions({ at: T, rows: [row('KXA', 2)] }, docAt(T + 5 * M, [])), [], 'an older document with no positionsOk');
assert.deepStrictEqual(lib.diffPositions(docAt(T, [row('KXA', 2)]), docAt(T + 13 * M, [])), [], 'a gap over 12 minutes hides several changes');
assert.deepStrictEqual(lib.diffPositions(docAt(T + 5 * M, [row('KXA', 2)]), docAt(T, [])), [], 'time must move forward');
for (const bad of [null, undefined, {}, 'x']) assert.deepStrictEqual(lib.diffPositions(bad, docAt(T, [])), []);
// rows with a bad ticker or no size are ignored, never an event
assert.deepStrictEqual(lib.diffPositions(docAt(T, []), docAt(T + 5 * M, [row('bad ticker', 1), row('KXA', 0), row('KXB', null)])), []);

// PE4: shapePerps says whether the positions answer itself was read; an empty list of positions is a real answer
assert.strictEqual(acct.shapePerps({ subaccount_balances: [] }, { positions: [] }, null, T).positionsOk, true);
assert.strictEqual(acct.shapePerps({ subaccount_balances: [] }, null, null, T).positionsOk, false);
assert.strictEqual(acct.shapePerps({ subaccount_balances: [] }, { nope: 1 }, null, T).positionsOk, false);

(async () => {
  // PE5: recordEvents writes each event under a stable id (two instances writing the same change write one document), and swallows every error
  const wrote = [];
  const prev = docAt(T, [row('KXA', 2)]), next = docAt(T + 5 * M, [row('KXA', 2), row('KXB', 1)]);
  assert.strictEqual(await lib.recordEvents({ prev, next, write: async (id, e) => wrote.push([id, e.kind]) }), 'events 1');
  assert.deepStrictEqual(wrote, [[(T + 5 * M) + '-KXB-opened', 'opened']]);
  assert.strictEqual(await lib.recordEvents({ prev: docAt(T, []), next: docAt(T + 5 * M, []), write: async () => { throw new Error('never called'); } }), 'none');
  assert.ok(/^error/.test(await lib.recordEvents({ prev, next, write: async () => { throw new Error('boom'); } })));

  // PE6: the library is pure; the server file reads the earlier document first, then writes the new one, then the events, all fenced; the rule is admin read and no client write; the doc has no order or key
  const src = fs.readFileSync(__dirname + '/../functions/kalshiPerpsEventsLib.js', 'utf8').split('\n').filter((l) => !/^\s*\/\//.test(l)).join('\n');
  assert(!/require\(|fetch|liveRequest|getFirestore|signature|POST/i.test(src), 'PE6 pure library, no I/O of its own');
  const idx = fs.readFileSync(__dirname + '/../functions/index.js', 'utf8');
  const block = idx.slice(idx.indexOf('exports.kalshiPerpsAccount'), idx.indexOf('exports.kalshiBookRecorder'));
  assert(block.indexOf('accRef.get()') > 0 && block.indexOf('accRef.get()') < block.indexOf('accRef.set(doc)') && block.indexOf('accRef.set(doc)') < block.indexOf('perpsEvents.recordEvents'), 'PE6 read, write, then events');
  assert(!/exports\.kalshiPerpsEvents/.test(idx), 'PE6 no new function');
  const rules = fs.readFileSync(__dirname + '/../firestore.rules', 'utf8');
  const m = /match \/kalshiPerpsEvents\/\{id\} \{([^}]*)\}/.exec(rules);
  assert(m && /allow read: if isAdmin\(\);/.test(m[1]) && /allow write: if false;/.test(m[1]), 'PE6 admin read, no client write');
  console.log('perpsEventsGates ok');
})().catch((e) => { console.error(e); process.exit(1); });

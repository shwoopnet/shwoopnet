// One strategy, one row, in one lane (Nov 13, 2026, the owner: "i believe we have some duplicates that slipped through between shadow/live/retired btw... gold return & closing buy seem AWFUL similar").
// A strategy is the same strategy when it has the same id, the same rule on the same market, or it is a strategy's own return record. The Strategies page draws each once.
const fs = require('fs'), path = require('path'), assert = require('assert');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const reg = JSON.parse(fs.readFileSync(path.join(root, 'strategies-registry.json'), 'utf8'));
const list = Array.isArray(reg) ? reg : reg.strategies;
const fn = (name) => { const i = html.indexOf('  function ' + name + '('); assert.ok(i >= 0, name); const j = html.indexOf('\n  }\n', i); return html.slice(i, j + 4); };
const liveBlock = html.slice(html.indexOf('  var KAL_BOARD_LIVE = ['), html.indexOf('\n  ];', html.indexOf('  var KAL_BOARD_LIVE = [')));
const liveIds = [...liveBlock.matchAll(/^\s+\{ id: '([A-Z0-9]+)', name: '([^']+)'/gm)].map((m) => m[1]);
const oneRow = new Function('return ' + /var KAL_ONE_ROW = (\{[^\n]*\});/.exec(html)[1])();
const info = new Function('return ' + html.slice(html.indexOf('{', html.indexOf('var KAL_STRATEGY_INFO = ')), html.indexOf('\n  };', html.indexOf('var KAL_STRATEGY_INFO = ')) + 4))();
const split = new Function(fn('kalshiRegistrySplit') + '; return kalshiRegistrySplit;')();
const drawn = () => split(list, [].concat(liveIds, Object.keys(oneRow)), []);
const gates = {};

// OR1: every fold points at a strategy drawn in Live, and every folded id is a registry row.
gates.OR1 = () => {
  assert.ok(liveIds.length >= 4, 'live strategies read from the page');
  for (const [from, to] of Object.entries(oneRow)) {
    assert.ok(liveIds.includes(to), from + ' folds into a live strategy');
    assert.ok(list.some((x) => x.id === from), from + ' is a registry row');
  }
  assert.ok(/KAL_BOARD_LIVE\.map\(function\(r\)\{ return r\.id; \}\)\)\.concat\(Object\.keys\(KAL_ONE_ROW\)\)/.test(html), 'the page leaves folded rows out of the pipeline');
};
// OR2: no id is drawn twice, and no pipeline row repeats a live strategy's id or name.
gates.OR2 = () => {
  const pipe = drawn().pipeline;
  const ids = liveIds.concat(pipe.map((x) => x.id));
  assert.deepStrictEqual(ids.filter((v, i) => ids.indexOf(v) !== i), [], 'an id in two lanes');
  const liveNames = liveIds.map((id) => ((list.find((x) => x.id === id) || {}).name || '').toLowerCase());
  const names = liveNames.concat(pipe.map((x) => x.name.toLowerCase()));
  assert.deepStrictEqual(names.filter((v, i) => v && names.indexOf(v) !== i), [], 'a name in two lanes');
};
// OR3: the same rule on the same market is the same strategy: a place named "<live strategy>, wheel place (<market>)" on a market that strategy already trades must be folded.
gates.OR3 = () => {
  for (const x of drawn().pipeline) {
    const m = /^(.+), wheel place \((.+)\)$/.exec(x.name);
    if (!m) continue;
    for (const id of liveIds) {
      const lv = list.find((r) => r.id === id);
      if (!lv || lv.name.toLowerCase() !== m[1].toLowerCase()) continue;
      const mk = String((info[id] || {}).markets || '').toLowerCase().split(/,\s*/);
      assert.ok(!mk.includes(m[2].toLowerCase()), x.id + ' is ' + id + ' on the same market, drawn twice');
    }
  }
  assert.ok(!drawn().pipeline.some((x) => x.id === 'WH-CFRTIK-BTC'), 'the Bitcoin wheel place is CFRTIK');
};
// OR4: a strategy's own return record is never a row of its own; gold's (GOLDOFF) shows inside the Closing buy pop-up.
gates.OR4 = () => {
  for (const x of drawn().pipeline) assert.ok(!(x.code && x.code.shadow && oneRow[x.code.shadow]), x.id + ' is a live strategy\'s own record');
  assert.ok(!drawn().pipeline.some((x) => x.id === 'GOLDOFF'), 'no Gold return record row');
  assert.ok(/label: bk === 'off' \? 'Return record' : 'Paper record while off'/.test(html) && /bar\(c\.back\.label \|\| 'Return record'/.test(html), 'the Closing buy pop-up carries the paper record while off');
  assert.ok(/ret: goldCard \? kalshiGoldReturnStats\(kalshiShadowCache\.rows, now\) : null/.test(html), 'fed from the GOLDOFF rows the page already reads');
};

let failed = 0;
for (const [k, f] of Object.entries(gates)) { try { f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + '\n' + (e && e.stack || e)); } }
process.exit(failed ? 1 : 0);

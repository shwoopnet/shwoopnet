'use strict';
// WR: the Wheel section on the Strategies page was removed (Nov 13, 2026, the owner: "this section can probably get removed").
// Consequence: no wheel place disappears from the site; every registry row the Wheel view used to draw (ids starting WH-) is placed by
// kalshiRegistrySplit in the Shadow box (pipeline) or the Retired list, like every other registry row.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>')).replace(/\/\*[\s\S]*?\*\//g, '');
const reg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'strategies-registry.json'), 'utf8')).strategies;
const gates = {};
const from = html.indexOf('  function kalshiRegistrySplit('), to = html.indexOf('\n  }\n', from) + 4;
const split = new Function(html.slice(from, to) + '; return kalshiRegistrySplit;')();
const wh = reg.filter((r) => r.id.indexOf('WH-') === 0);

// WR1: the section, its builder, its seat counts and its styles are gone.
gates.WR1 = () => {
  assert.ok(!/kalshiWheelHtml|kalshiWheelStatus|kalshiWheelDay|KAL_WHEEL_SEATS|id="wheel"/.test(html), 'no Wheel view code or markup');
  assert.ok(!/\.wh(-[a-z]+)?\s*\{/.test(css), 'no Wheel view styles');
};
// WR2: every wheel place lands in Shadow (standing places) or Retired (withdrawn ones), so nothing drops off the page.
gates.WR2 = () => {
  assert.ok(wh.length > 0, 'the registry still holds wheel places');
  const s = split(reg, [], []);
  for (const r of wh) {
    const inPipe = s.pipeline.some((x) => x.id === r.id), inRet = s.retired.some((x) => x.id === r.id);
    assert.ok(inPipe !== inRet, r.id + ' is in exactly one of Shadow and Retired');
    assert.strictEqual(inRet, r.stage === 'Retired', r.id + ' sits in the lane its stage names');
  }
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

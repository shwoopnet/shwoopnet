'use strict';
// SR1 to SR5: every strategy card says when it goes live, when it stops and when it comes back, and shows its settings (Nov 13, 2026, the owner: "all strategies should have their own
// return criteria, nothing should be dependent on me with rotating strategies" and "make sure each strategy card ... displays the rules and parameters").
// Consequence: a strategy added to the bot without its three lines or settings fails here; a size, band, stop or floor changed in code without the page fails here; and no rotation line
// may say the owner approves or re-arms (the account safety stop is the one owner step, and it is said as such).
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const slot = require('../functions/kalshiSlotLib.js');
const live = require('../functions/kalshiLiveLib.js');
const gold = require('../functions/kalshiGoldKillLib.js');
const gates = {};

const varLine = (name) => { const m = new RegExp('  var ' + name + ' = .*\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const varBlock = (name) => { const m = new RegExp('  var ' + name + ' = [\\[{][\\s\\S]*?\\n  [\\] }]+;\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const P = new Function(varBlock('KAL_BOARD_LIVE') + varLine('KAL_RULES_BUILDING') + varLine('KAL_ACCOUNT_STOP') + varLine('KAL_BOARD_SHADOW_RULES') + varBlock('KAL_STAGES') + varBlock('KAL_BOARD_RETIRED') +
  'return { KAL_BOARD_LIVE, KAL_RULES_BUILDING, KAL_ACCOUNT_STOP, KAL_BOARD_SHADOW_RULES, KAL_STAGES, KAL_BOARD_RETIRED };')();
const reg = JSON.parse(fs.readFileSync(path.join(root, 'strategies-registry.json'), 'utf8')).strategies;
const OWNER = /owner (approv|decid|re-arm|turns)|owner'?s? approval|reviewed (code )?(edit|change)|then the owner/i;
const param = (s, k) => { const p = (s.params || []).find((x) => x[0] === k); return p ? p[1] : ''; };
const cents = (x) => Math.round(x * 100) + 'c';

gates.SR1 = () => {
  // every live strategy, and every strategy the bot's second slot can trade, has the three lines and its settings
  const ids = P.KAL_BOARD_LIVE.map((s) => s.id);
  for (const s of slot.SLOT_STRATEGIES) assert.ok(ids.includes(s.id), s.id + ' (in the bot) has a card on the page');
  for (const s of P.KAL_BOARD_LIVE) {
    assert.ok(Array.isArray(s.rules) && s.rules.length === 3 && s.rules.every((t) => typeof t === 'string' && t.length > 20), s.id + ': Goes live when, Stops when and Comes back when are written');
    for (const k of ['Market', 'Entry', 'Price band', 'Contracts', 'Streak stop', 'Net floor']) assert.ok(param(s, k).length > 0, s.id + ' shows ' + k);
    assert.ok(param(s, 'Daily loss cap') || param(s, 'Window cap'), s.id + ' shows a loss cap');
    assert.ok(param(s, 'Drawdown stop') || param(s, 'Lifetime loss cap'), s.id + ' shows its drawdown or lifetime stop');
    assert.ok(!s.rules.some((t) => OWNER.test(t)), s.id + ': no rotation line depends on the owner');
    assert.ok(!/undefined|NaN|null/.test(JSON.stringify(s)), s.id + ': nothing blank or undefined');
  }
};
gates.SR2 = () => {
  // the second slot's numbers are the code's
  for (const s of slot.SLOT_STRATEGIES) {
    const c = P.KAL_BOARD_LIVE.find((x) => x.id === s.id), e = s.entry, k = s.killRules;
    const lo = slot.SLOT_SKIP_BELOW[s.id] || e.priceMin;
    assert.ok(param(c, 'Price band').startsWith(cents(lo) + ' to ' + cents(e.priceMax)), s.id + ' band ' + param(c, 'Price band'));
    const L = slot.SLOT_LADDERS[s.id];
    if (L) {
      assert.ok(param(c, 'Contracts').includes(L.steps.join(', ')) && param(c, 'Contracts').startsWith(L.steps[0] + ' '), s.id + ' ladder ' + param(c, 'Contracts'));
      assert.ok(param(c, 'Daily loss cap').startsWith('$' + L.dailyPerContract.toFixed(2) + ' a contract') && param(c, 'Daily loss cap').includes(Math.round(L.dailyMaxFraction * 100) + '%'), s.id + ' daily cap');
      assert.ok(param(c, 'Drawdown stop').startsWith('$' + L.stopPerContract + ' a contract') && param(c, 'Drawdown stop').includes('($' + L.stopPerContract * L.steps[0] + ' at ' + L.steps[0] + ')') && param(c, 'Drawdown stop').includes(Math.round(L.stopMaxFraction * 100) + '%'), s.id + ' drawdown stop');
      assert.ok(c.rules[0].includes('Starts at ' + L.steps[0] + ' contracts') && c.rules[0].includes(L.steps.slice(1, -1).join(', ') + ' and ' + L.steps[L.steps.length - 1]), s.id + ' goes live line follows the ladder');
    } else {
      assert.ok(param(c, 'Contracts').startsWith(String(s.contractsPerOrder)), s.id + ' contracts');
      assert.ok(param(c, 'Daily loss cap') === 'Its own: ' + (slot.SLOT_CAP_FRACTIONS.daily * 100) + '% of the account, at most $' + slot.SLOT_CAP_CEILINGS.daily, s.id + ' daily cap ' + param(c, 'Daily loss cap'));
      assert.ok(param(c, 'Lifetime loss cap') === 'Its own: ' + (slot.SLOT_CAP_FRACTIONS.lifetime * 100) + '% of the account, at most $' + slot.SLOT_CAP_CEILINGS.lifetime, s.id + ' lifetime cap');
    }
    assert.strictEqual(param(c, 'Streak stop'), k.maxConsecutiveLosses + ' losses in a row', s.id + ' streak');
    const floor = (k.minNet.net < 0 ? '-$' + Math.abs(k.minNet.net) : '$' + k.minNet.net) + ' after ' + k.minNet.afterFills + ' trades';
    assert.strictEqual(param(c, 'Net floor'), floor, s.id + ' net floor');
    assert.ok(c.rules[1].includes(k.maxConsecutiveLosses + ' losses in a row'), s.id + ': the Stops when line names the streak');
    assert.ok(param(c, 'Exit') === 'Held until the market closes' && s.exit.holdToSettle === true, s.id + ' holds to settlement');
  }
};
gates.SR3 = () => {
  // gold's numbers are the code's
  const c = P.KAL_BOARD_LIVE.find((x) => x.id === 'L1'), g = gold.GOLD_KILL;
  assert.ok(param(c, 'Contracts').includes('$' + live.SCALE_DOLLARS_PER_CONTRACT) && param(c, 'Contracts').includes('up to ' + live.L1_SIZE_CEILING), 'gold size: ' + param(c, 'Contracts'));
  assert.ok(param(c, 'Window cap').startsWith('At most ' + live.L1_WINDOW_CAP_FRACTION * 100 + '%'), 'window cap');
  assert.strictEqual(param(c, 'Drawdown stop'), '$' + g.drawdownDollars.toFixed(2) + ' below its best point');
  assert.strictEqual(param(c, 'Net floor'), '-$' + Math.abs(g.netFloor) + ' after ' + g.netAfterTrades + ' trades');
  assert.ok(param(c, 'Price band').startsWith(cents(live.L1_BAND[0]) + ' to ' + cents(live.L1_BAND[1])), 'band ' + param(c, 'Price band'));
  assert.ok(param(c, 'Entry').includes('(' + (live.L1_WINDOW_MS[0] / 60000).toFixed(1) + ' to ' + (live.L1_WINDOW_MS[1] / 60000).toFixed(1) + ' minutes left)'), 'entry window');
  assert.ok(c.rules[1].includes('$' + g.drawdownDollars.toFixed(2)) && c.rules[1].includes('-$' + Math.abs(g.netFloor) + ' after ' + g.netAfterTrades), 'the Stops when line is the kill latch');
  assert.ok(c.rules[0].includes('half size for ' + g.halfSizeFills + ' trades'), 'the half size return is the code\'s');
};
gates.SR4 = () => {
  // the shared lines: shadow, the stage flow, retired, and every registry row that is not retired
  assert.ok(P.KAL_BOARD_SHADOW_RULES.length === 3 && !P.KAL_BOARD_SHADOW_RULES.some((t) => OWNER.test(t)), 'the shadow rules depend on nobody');
  assert.ok(!P.KAL_STAGES.some((s) => OWNER.test(s.then) || OWNER.test(s.head)), 'the stage flow says no owner approves');
  assert.ok(!OWNER.test(P.KAL_BOARD_RETIRED.back) && P.KAL_BOARD_RETIRED.rows.every((r) => !OWNER.test(r.note || '')), 'the retired lines depend on nobody');
  assert.ok(/restarts by itself 24 hours later \(at most once in 7 days\)/.test(P.KAL_ACCOUNT_STOP) && /a second 12% stop within 7 days stays off until the owner restarts it/.test(P.KAL_ACCOUNT_STOP) && /12% of the account/.test(P.KAL_ACCOUNT_STOP) && live.L1_SIZED_STOP_FRACTION === 0.12, 'the one owner step, the account safety stop, is said plainly and matches the code');
  // the 40% hard stop (Main's pull request): once a code constant names it, the page must say it (the Risk Analyst, Nov 13, 2026)
  const hard = [live, slot, gold].map((m) => m.HARD_STOP_FRACTION).find((x) => typeof x === 'number');
  if (hard !== undefined) assert.ok(new RegExp(Math.round(hard * 100) + '%').test(P.KAL_ACCOUNT_STOP), 'the account stop line names the ' + Math.round(hard * 100) + '% hard stop now that the code has it');
  assert.ok(/being built/.test(P.KAL_RULES_BUILDING), 'until the rotation code is live the page says these are the written rules being built');
  for (const r of reg) {
    if (r.stage === 'Retired') { assert.ok(!OWNER.test(r['return'] || ''), r.id + ': a retired row\'s comeback line depends on nobody'); continue; }
    if (r.id === 'S3') continue;   // politics: the owner's own politics rulebook (docs/POLITICS_RULES.md) still asks for a popup before any politics probe; not a rotation rule
    for (const k of ['goesLive', 'kill', 'return']) assert.ok(typeof r[k] === 'string' && r[k].length > 10, r.id + ' has ' + k);
    assert.ok(!OWNER.test(r.goesLive) && !OWNER.test(r['return']), r.id + ': its rotation lines depend on nobody');
  }
  for (const s of P.KAL_BOARD_LIVE) {
    const r = reg.find((x) => x.id === s.id);
    assert.ok(r && r.goesLive === s.rules[0] && r.kill === s.rules[1] && r['return'] === s.rules[2], s.id + ': the registry row and the page say the same three lines');
  }
};
gates.SR5 = () => {
  // the pop-ups draw them: the chart sheet shows Goes live when, Stops when, Comes back when and a Settings panel; the registry pop-up shows Stage and Goes live when
  assert.ok(/line\('Goes live when', c\.goes\) \+ line\('Stops when', c\.kill\) \+ line\('Comes back when', c\.ret\)/.test(html), 'the chart sheet shows the three lines');
  assert.ok(/<h5>Settings<\/h5>/.test(html) && /line\('Stage', c\.stage\)/.test(html), 'the chart sheet shows the settings and the stage');
  assert.ok(/f\('Stage', x\.stage\) \+ \(x\.stage === 'Retired' \? '' : f\('Goes live when', x\.goes \|\| x\.goesLive\)\) \+ f\('Stops when', x\.kill\)/.test(html), 'the registry pop-up shows the stage and the three lines');
  assert.ok(/params: s\.params/.test(html), 'the live cards carry their settings to the sheet');
};

gates.SR6 = () => {
  // the glossary panel is gone (Nov 13, 2026, the owner: "this can get removed"), and Off / Retired groups are Live rows (the owner: "this card doesnt match")
  assert.ok(!/KAL_GLOSSARY|sp-gloss|<summary>What the words on this page mean/.test(html), 'no glossary panel');
  assert.ok(/<details class="sp-rgrp rw" data-k="ret:/.test(html) && /<summary class="rw-h"><i class="chev"><\/i><span class="rw-ring" aria-hidden="true"><\/span><b class="rw-n sp-rgt">/.test(html), 'a retired group uses the Live row markup');
  assert.ok(/\.sp-b-off\{ border-color:var\(--paper\); \}/.test(html), 'the Off badge is the same solid badge as the Live rows');
};
let failed = 0;
for (const [name, g] of Object.entries(gates)) { try { g(); console.log('ok ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
if (failed) process.exit(1);

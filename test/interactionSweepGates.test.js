// Interaction sweep and pop-up trim (Nov 13, 2026, the owner: "interaction bugs", "lets remove some info from the pop-up strategy card").
// Each gate pins a fix found by driving the page in a browser (desktop click and phone tap), or a trim the owner asked for.
const fs = require('fs'), path = require('path'), assert = require('assert');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const gold = require('../functions/kalshiGoldKillLib.js');
const gates = {};
const fn = (name) => { const i = html.indexOf('  function ' + name + '('); assert.ok(i >= 0, name); const j = html.indexOf('\n  }\n', i); return html.slice(i, j + 4); };

// IX1: Back closes a strategy pop-up instead of leaving the site. Opening pushes one history entry; Back (popstate) closes; X, Escape or a tap outside steps back over the entry.
gates.IX1 = () => {
  assert.ok(/function kalshiPopPush\(\)\{ try\{ if\(!\(history\.state && history\.state\.spPop\)\)\{ history\.pushState\(\{ spPop: true \}, '', location\.href\); \} \}catch\(e\)\{\} \}/.test(html), 'opening pushes one entry with the same address');
  assert.ok(/window\.addEventListener\('popstate', function\(\)\{ kalshiStratChart\.close\(true\); kalshiStratPop\.close\(true\); \}\);/.test(html), 'Back closes whichever pop-up is open');
  assert.strictEqual((html.match(/if\(!fromBack\)\{ kalshiPopPop\(\); \}/g) || []).length, 2, 'both pop-ups step back over their entry when closed another way');
  assert.strictEqual((html.match(/if\(pop\.hidden\)\{ kalshiPopPush\(\); \}/g) || []).length, 2, 'both pop-ups push only when they open, not on a redraw');
};
// IX2: the page behind stays still while a pop-up is open.
gates.IX2 = () => {
  assert.ok(/html:has\(\.sp-cpop:not\(\[hidden\]\)\)\{ overflow:hidden; \}/.test(html) && /\.sp-csheet\{ overscroll-behavior:contain; \}/.test(html));
};
// IX3: leaving the Strategies page closes its pop-ups.
gates.IX3 = () => {
  assert.ok(/if\(name !== 'strategies' && typeof kalshiStratChart === 'object'\)\{ kalshiStratChart\.close\(true\); kalshiStratPop\.close\(true\); \}/.test(fn('showPage')));
};
// IX4: the Tools and Layout menus close on a tap outside and on Escape, like the Running menu.
gates.IX4 = () => {
  assert.ok(/var KAL_MENUS = \['kalTools', 'kalLayout'\];/.test(html));
  assert.ok(/KAL_MENUS\.forEach\(function\(id\)\{ var m = document\.getElementById\(id\); if\(m && m\.open && !m\.contains\(e\.target\)\)\{ m\.open = false; \} \}\)/.test(html), 'outside tap');
  assert.ok(/if\(e\.key === 'Escape'\)\{ KAL_MENUS\.forEach/.test(html), 'Escape');
};
// IX5: a tapped readout stays until the next touch on every chart (a lifted finger fires pointerleave and pointerup, which used to clear it at once).
gates.IX5 = () => {
  assert.ok(!/addEventListener\('pointerup', function\(e\)\{ if\(e\.pointerType !== 'mouse'\)\{ clear\(\); \} \}\)/.test(html), 'no clear on a lifted finger');
  assert.ok(!/addEventListener\('pointerleave', clear\)/.test(html), 'pointerleave clears for the mouse only');
  assert.strictEqual((html.match(/addEventListener\('pointerleave', function\(e\)\{ if\(e\.pointerType === 'mouse'\)\{ clear\(\); \} \}\)/g) || []).length, 3, 'the Strategies, Account result and Brief charts');
};
// PT1: the pop-up keeps the essentials only: one chart (money over time with its range), no daily or win/loss chart, no "being built" note, and a Settings list without what is already said above.
gates.PT1 = () => {
  const c = fn('kalshiStratChartsHtml');
  assert.ok(/Money made over time/.test(c) && /kalshiStratRangeHtml/.test(c), 'the money chart with its range');
  assert.ok(!/Last 14 days/.test(c) && !/Win\/loss ratio, last 30 trades/.test(c) && !/KAL_RULES_BUILDING/.test(c), 'no second chart, no third chart, no being-built note');
  assert.ok(/var KAL_SETTINGS_KEEP = \/\^\(Contracts\|Daily loss cap\|Lifetime loss cap\|Window cap\|Started\|Next read\|Size if it goes live\)\$\/;/.test(html), 'settings keep only what is not shown above');
  for (const k of ['Market', 'Entry', 'Price band', 'Drawdown stop', 'Streak stop', 'Net floor', 'Exit', 'What it does']) assert.ok(!new RegExp('\\|' + k + '\\|').test('|Contracts|Daily loss cap|Lifetime loss cap|Window cap|Started|Next read|Size if it goes live|'), k + ' is dropped');
};
// PT2: gold is a trial seat on the page from the code's state: the trial start, size, floor and drawdown line copy the bot's GOLD_TRIAL and GOLD_KILL.
gates.PT2 = () => {
  const t = /var KAL_GOLD_TRIAL = \{ startedAt: Date\.UTC\((\d+), (\d+), (\d+)\), contracts: (\d+) \};/.exec(html);
  assert.ok(t, 'KAL_GOLD_TRIAL is on the page');
  assert.strictEqual(Date.UTC(+t[1], +t[2], +t[3]), gold.GOLD_TRIAL.startedAt); assert.strictEqual(+t[4], gold.GOLD_TRIAL.contracts);
  const k = /L1: \{ trialNet: (-?\d+), trialAfter: (\d+), drawdown: ([\d.]+) \}/.exec(html);
  assert.ok(k && +k[1] === gold.GOLD_TRIAL.floorNet && +k[2] === gold.GOLD_TRIAL.floorAfterFills && +k[3] === gold.GOLD_KILL.drawdownDollars, 'the stop bar uses the code\'s floor and line');
  assert.ok(/s\.id === 'L1' && typeof KAL_GOLD_TRIAL === 'object'/.test(html), 'gold is tagged as a trial seat (Trial N of 90), not Under review');
  assert.ok(/money\(-GK\.trialNet\) \+ ' trial floor', cap: money\(kill\.floorRoom\) \+ ' of room'/.test(fn('kalshiStratGauge')) && /' drawdown line', cap: money\(kill\.ddRoom\) \+ ' of room'/.test(fn('kalshiStratGauge')), 'the nearest stop is said in plain words with its room');
};
// PT3: every rule line is one short sentence, with no dates or internal notes.
gates.PT3 = () => {
  const block = html.slice(html.indexOf('  var KAL_BOARD_LIVE = ['), html.indexOf('  var KAL_RULES_BUILDING'));
  const lines = [...block.matchAll(/rules: \[('(?:[^'\\]|\\.)*'), ('(?:[^'\\]|\\.)*'), ('(?:[^'\\]|\\.)*')\]/g)].flatMap((m) => [m[1], m[2], m[3]]);
  const shadow = /var KAL_BOARD_SHADOW_RULES = \[('(?:[^'\\]|\\.)*'), ('(?:[^'\\]|\\.)*'), ('(?:[^'\\]|\\.)*')\];/.exec(html);
  assert.ok(lines.length === 15 && shadow, 'five live strategies and the shadow lines');
  for (const l of lines.concat(shadow.slice(1))) {
    assert.ok(l.length < 150 && !/\.\s+[A-Z]/.test(l) && !/Nov \d+|checkpoint|exception|rows\b/.test(l), 'one short plain sentence: ' + l);
  }
};
// PT4: the small ring shows a glyph for "no losses" and "n/a" (the words overflowed the circle); no box draws a progress line under its header.
gates.PT4 = () => {
  assert.ok(/esc\(kalshiStratRingText\(pf\)\.glyph\) \+ '<\/span><\/span>'/.test(html), 'the small ring uses the fitted glyph');
  assert.ok(!/class="lp-prog"/.test(fn('kalshiBoardHtml')), 'no box progress line');
};

(async () => {
  let failed = 0;
  for (const [k, f] of Object.entries(gates)) { try { await f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + '\n' + (e && e.stack || e)); } }
  process.exit(failed ? 1 : 0);
})();

'use strict';
// The strategy registry (Nov 12, 2026, the owner: the Strategies page should be "a constant rotating thing whenever we add or remove strategies").
// strategies-registry.json at the site root is the ONE list of every strategy and its stage. It is public (Pages serves it), so it holds no live figures.
// The consequence these gates protect: adding a shadow rule or a slot strategy to the bot's code without a row here fails, so the Strategies page cannot show "Shadow 0" while rules are logging.
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const root = path.join(__dirname, '..');
const reg = JSON.parse(fs.readFileSync(path.join(root, 'strategies-registry.json'), 'utf8'));
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const gates = {};
const KEYS = ['id', 'name', 'stage', 'rule', 'label', 'startDate', 'nextRead', 'nextReadText', 'n', 'nBasis', 'kill', 'return', 'retiredOn', 'reason', 'notes', 'code', 'roomTarget', 'roomWhat', 'cause', 'figures'];
const isDate = (s) => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s) && Number.isFinite(Date.parse(s + 'T00:00:00Z'));
const nonEmpty = (s) => typeof s === 'string' && s.trim().length > 0;

gates.RG1 = () => {
  // Consequence: a malformed row cannot reach the page. Every entry has exactly the known fields, a valid stage and a unique id.
  assert.deepStrictEqual(reg.stages, ['Idea', 'Shadow', 'Paper', 'Probe', 'Live', 'Retired']);
  assert.ok(Array.isArray(reg.strategies) && reg.strategies.length > 10);
  const ids = new Set();
  for (const x of reg.strategies) {
    assert.deepStrictEqual(Object.keys(x).sort(), KEYS.slice().sort(), x.id + ' has exactly the registry fields');
    assert.ok(reg.stages.includes(x.stage), x.id + ' has a valid stage');
    assert.ok(nonEmpty(x.id) && nonEmpty(x.name) && !ids.has(x.id), 'unique id and a name: ' + x.id);
    ids.add(x.id);
    assert.ok(Array.isArray(x.notes) && x.notes.every(nonEmpty), x.id + ' notes are text');
    for (const k of ['startDate', 'nextRead', 'retiredOn']) assert.ok(x[k] === null || isDate(x[k]), x.id + '.' + k + ' is a date or null');
    assert.ok(x.roomTarget === null || (Number.isInteger(x.roomTarget) && x.roomTarget > 0 && nonEmpty(x.roomWhat)), x.id + ': room left needs a target count and words for it');
    assert.ok(x.n === null || Number.isInteger(x.n), x.id + '.n is a whole number or null');
    // A retired row files under exactly one cause; any other stage has none; figures are public research text only and only on a retired row.
    if (x.stage === 'Retired') assert.ok(['failed the bar', 'killed while live', 'family closed', 'superseded'].includes(x.cause), x.id + ' has a known cause');
    else assert.strictEqual(x.cause, null, x.id + ' has no cause unless retired');
    assert.ok(x.figures === null || (x.stage === 'Retired' && nonEmpty(x.figures) && /\bn \d/.test(x.figures) && !/\$/.test(x.figures)), x.id + ': figures are a public n and PF, never dollars');
    if (x.n !== null) assert.ok(nonEmpty(x.nBasis), x.id + ': an n must say what it counts (public data only)');
  }
};

gates.RG2 = () => {
  // Consequence: an unproven strategy never looks proven. Shadow and Paper rows carry the UNPROVEN label, a rule, when the next read is, and kill and return rules in words (or an explicit "to confirm").
  for (const x of reg.strategies) {
    if (x.stage === 'Idea') { assert.strictEqual(x.label, 'UNPROVEN', x.id + ' is labelled UNPROVEN'); for (const k of ['rule', 'nextReadText']) assert.ok(nonEmpty(x[k]), x.id + ' states ' + k); }
    else if (x.stage === 'Shadow' || x.stage === 'Paper') {
      assert.strictEqual(x.label, 'UNPROVEN', x.id + ' is labelled UNPROVEN');
      for (const k of ['rule', 'nextReadText', 'kill', 'return', 'nBasis']) assert.ok(nonEmpty(x[k]), x.id + ' states ' + k);
      for (const k of ['kill', 'return']) if (/to confirm/i.test(x[k])) assert.ok(x.notes.some((t) => /to confirm/i.test(t)), x.id + ': an unwritten ' + k + ' rule is listed in notes');
    } else if (x.stage === 'Probe' && !(x.code && x.code.live)) assert.strictEqual(x.label, 'UNPROVEN', x.id + ' is approved but not built, and still unproven');
    else assert.strictEqual(x.label, null, x.id + ' only shadow and paper rows carry the label');
    if ((x.stage === 'Live' || x.stage === 'Probe')) for (const k of ['rule', 'kill', 'return']) assert.ok(nonEmpty(x[k]), x.id + ' states ' + k);
    if (x.stage === 'Retired') assert.ok(nonEmpty(x.reason) && nonEmpty(x['return']), x.id + ' states why it ended and the return rule');
  }
};

gates.RG3 = () => {
  // Consequence: the list rotates by itself. Every rule in the bot's SHADOW_RULES and every strategy in SLOT_STRATEGIES must have a registry row that names it in code{}, and every code{} name must exist.
  const shadow = require('../functions/kalshiShadowLib.js').SHADOW_RULES.map((r) => r.id);
  const slot = require('../functions/kalshiSlotLib.js').SLOT_STRATEGIES.map((r) => r.id);
  const claims = (kind) => reg.strategies.filter((x) => x.code && x.code[kind]).map((x) => x.code[kind]);
  for (const id of shadow) assert.ok(claims('shadow').includes(id), 'shadow rule ' + id + ' has no registry row (add one to strategies-registry.json)');
  for (const id of slot) assert.ok(claims('slot').includes(id), 'slot strategy ' + id + ' has no registry row (add one to strategies-registry.json)');
  for (const id of claims('shadow')) assert.ok(shadow.includes(id), 'registry names shadow rule ' + id + ' which the bot does not have');
  for (const id of claims('slot')) assert.ok(slot.includes(id), 'registry names slot strategy ' + id + ' which the bot does not have');
  // A registry row that claims a stage must agree with the code: a coded shadow rule is Shadow, a coded slot strategy is Live or Probe.
  for (const x of reg.strategies) {
    if (x.code && x.code.shadow) assert.strictEqual(x.stage, 'Shadow', x.id + ' is coded as a shadow rule');
    if (x.code && x.code.slot) assert.ok(['Live', 'Probe'].includes(x.stage), x.id + ' is coded as a slot strategy');
  }
  // The page's own live cards must be registered Live.
  const live = [...html.matchAll(/KAL_BOARD_LIVE = \[([\s\S]*?)\n  \];/g)][0][1];
  for (const m of live.matchAll(/\{ id: '(\w+)'/g)) assert.ok(reg.strategies.some((x) => ['Live', 'Probe'].includes(x.stage) && x.id === m[1]), m[1] + ' is on the page as Live and must be a Live or Probe registry row');
};

gates.RG4 = () => {
  // Consequence: nothing from the real account reaches the public site through this file. The registry is scanned with the same phrasings as test/noLiveFiguresGates.test.js, and carries no dollar result.
  const text = fs.readFileSync(path.join(root, 'strategies-registry.json'), 'utf8');
  const src = fs.readFileSync(path.join(__dirname, 'noLiveFiguresGates.test.js'), 'utf8');
  const block = src.slice(src.indexOf('const PATTERNS = ['), src.indexOf('const OPT_OUT'));
  const PATTERNS = new Function(block + '; return PATTERNS;')();
  const hits = [];
  for (const [what, re] of PATTERNS) for (const t of JSON.stringify(reg, null, 1).split('\n')) if (re.test(t)) hits.push(what + ': ' + t.trim());
  assert.deepStrictEqual(hits, [], 'live-figure phrasing in the registry');
  assert.ok(!/profit factor\s+\d|\bPF\s+\d|net\s+[-+]\$\d|win rate|balance/i.test(text.replace(/profit factor 1\.3\+?|PF 1\.3\+?|cash PF 1\.[23]\+/gi, '')), 'no result figure (bars written as 1.3+ are rules, not results)');
};

gates.RG5 = () => {
  // Consequence: the page reads the one list with one same-origin GET, merges it without replacing a computed card, and escapes every field.
  assert.ok(/fetch\('strategies-registry\.json', \{ cache: 'no-cache' \}\)/.test(html), 'one GET of the committed list');
  assert.strictEqual((html.match(/strategies-registry\.json/g) || []).length >= 1, true);
  const card = html.slice(html.indexOf('regSplit.pipeline.forEach'), html.indexOf('// ---- The nearest kill'));
  assert.ok(!/innerHTML/.test(card));
  assert.ok(/name: x\.name/.test(card) && /<b class="rw-n">' \+ esc\(o\.name\)/.test(html) && /kalshiRegistrySheetHtml\(x, d, esc\)/.test(card), 'a registry row draws its escaped name and the escaped sheet (rule, kill, return, room left, chart)');
  assert.ok(/data-reg-details=/.test(html.slice(html.indexOf('var quietHtml'), html.indexOf('var shadowEmpty'))) && /Details<\/button>/.test(html.slice(html.indexOf('var quietHtml'), html.indexOf('var shadowEmpty'))), 'Paper and idea rows keep the Details button (option A, the owner: "i like. A")');
  assert.ok(/id = 'spPop'/.test(html) && /pop\.hidden = true/.test(html) && /e\.key === 'Escape'/.test(html), 'the popup closes by Close, outside tap and Escape, and lives outside #stratBody so a redraw never closes it');
  // Behaviour: lift the pure helpers and render the seeded registry.
  const fn = (name) => { const i = html.indexOf('function ' + name + '('); let d = 0, j = html.indexOf('{', i); for (let k = j; k < html.length; k++) { if (html[k] === '{') d++; else if (html[k] === '}' && --d === 0) return html.slice(i, k + 1); } };
  const code = ['kalshiRegistryNorm', 'kalshiRegistrySplit', 'kalshiRegBuilding', 'kalshiRegistrySheetHtml', 'kalshiStratSpark', 'kalshiHoverAttr', 'kalshiHoverWhen', 'kalshiStratOneLine'].map(fn).join('\n');
  const P = new Function("var KAL_REG_STAGES = ['Idea', 'Shadow', 'Paper', 'Probe', 'Live', 'Retired'];\n" + code + '; return { kalshiRegistryNorm, kalshiRegistrySplit, kalshiRegistrySheetHtml };')();
  const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const list = P.kalshiRegistryNorm(reg);
  assert.strictEqual(list.length, reg.strategies.length);
  assert.strictEqual(P.kalshiRegistryNorm({ nope: 1 }), null, 'a wrong shape is refused');
  const split = P.kalshiRegistrySplit(list, ['OICORE', 'EVENT830', 'CFRTIK'], ['XRP', 'Bitcoin', 'Ethereum', 'Dogecoin', 'AUD/USD', 'USD/CAD', 'Natural gas']);
  assert.deepStrictEqual(split.pipeline.filter((x) => !x.id.startsWith('WH-')).map((x) => x.id).sort(), ['GOLDOFF', 'S3', 'W-SPOTLEAD1'], 'the Head of R&D list (the WH- wheel places are generated by scripts/sync_registry.py and are checked in test/registrySyncGates.test.js): the research rows still standing and the shadow rule, not Shadow 0 (the spread cell is Retired after its FAIL; NC15DEPTH1 is Retired as superseded by the wheel NC15 places, Nov 13, 2026; CFRTI-K became the live probation seat CFRTIK on Nov 12, 2026, so it is a Live-lane card now, not a pipeline row)');
  assert.ok(split.retired.some((x) => x.id === 'MMSIM1') && split.retired.some((x) => x.id === 'W-SPREAD-CELL1') && !split.retired.some((x) => x.name === 'XRP'), 'only retired rows not already listed are added');
  const out = split.pipeline.filter((x) => !x.id.startsWith('WH-')).map((x) => P.kalshiRegistrySheetHtml(x, null, esc)).join('');
  assert.strictEqual((out.match(/>UNPROVEN</g) || []).length, 3, 'every unproven card says UNPROVEN');
  // The Details sheet shows ONLY: what it does, kill, return, room left, one chart.
  const g = list.find((x) => x.id === 'GOLDOFF');
  const sheet = P.kalshiRegistrySheetHtml(g, { n: 14, spark: [0.5, 0.8, 1.1, 1.2] }, esc);
  for (const w of ['What it does', 'Stops when', 'Comes back when', 'Room left before a stop', '<svg']) assert.ok(sheet.includes(w), 'sheet has ' + w);
  assert.ok(!/Started|Next read|To confirm|>n</.test(sheet) && (sheet.match(/<svg/g) || []).length === 1, 'and nothing else: one chart');
  assert.ok(/46 to go/.test(sheet), 'room left counts toward the target in the file');
  const empty = P.kalshiRegistrySheetHtml(g, null, esc);
  assert.ok(/not measured yet/.test(empty) && /no trades to draw yet/.test(empty) && !/<svg/.test(empty), 'no data draws no made-up figure');
  const evil = P.kalshiRegistrySheetHtml({ id: 'X', name: '<img onerror=1>', stage: 'Shadow', label: 'UNPROVEN', rule: '"><script>', notes: [], n: null }, null, esc);
  assert.ok(!/<img|<script/.test(evil), 'registry text is escaped');
};

gates.RG6 = () => {
  // Consequence (the owner, Nov 12, 2026: "you didnt apply it to the LIVE side"): every Live and Probe card has the Details button and the same popup, with the same five things and nothing else; the popup is masked when Privacy is on, escapes registry text, and a strategy with no private read says so and draws no chart.
  const fn = (name) => { const i = html.indexOf('function ' + name + '('); let d = 0, j = html.indexOf('{', i); for (let k = j; k < html.length; k++) { if (html[k] === '{') d++; else if (html[k] === '}' && --d === 0) return html.slice(i, k + 1); } };
  const varLine = (n) => new RegExp('  var ' + n + ' = .*\\n').exec(html)[0];
  const varBlock = (n) => new RegExp('  var ' + n + ' = [\\[{][\\s\\S]*?\\n  [\\] }]+;\\n').exec(html)[0];
  const names = ['kalshiStratSheetRow', 'kalshiStratSheetData', 'kalshiStratGauge', 'kalshiRegistrySheetHtml', 'kalshiStratSpark', 'kalshiHoverAttr', 'kalshiHoverWhen', 'kalshiStratOneLine'];
  const P = new Function(varLine('KAL_BOARD_TRIPWIRE') + varLine('KAL_BOARD_KILL') + varBlock('KAL_BOARD_LIVE') + names.map(fn).join('\n') + '; return { ' + names.join(', ') + ', KAL_BOARD_LIVE };')();
  const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const mask = (x) => (x < 0 ? '-' : '') + '****', money = (x) => (x < 0 ? '-' : '') + '$' + Math.abs(x).toFixed(2);
  // the card side: the computed Live tile renders the button, and the click handler finds a row for every live id
  assert.ok(/data-row="' \+ esc\(o\.key\)/.test(html) && /key: s\.id, name: s\.name, stage: bk === 'off'/.test(html), 'every computed Live or Probe strategy is a row that opens its chart sheet (L1, OICORE, EVENT830 and any added to the list); the popup now serves the Retired list and the Paper and Ideas rows');
  assert.ok(/kalshiStratSheets\[openId\] \|\| kalshiStratSheetRow\(openId, kalshiRegistry\.list, KAL_BOARD_LIVE\)/.test(html) && /kalshiRegistrySheetHtml\(x, kalshiStratSheetData\(/.test(html), 'the popup reuses the one sheet builder, with its data built when it opens');
  assert.ok(/kalshiStratPop\.refresh\(\)/.test(fn('renderStrategiesPage')), 'a redraw or the Privacy switch re-masks an open popup');
  const list = reg.strategies;
  for (const id of ['L1', 'OICORE', 'EVENT830', 'CFRTIK']) {
    assert.ok(P.KAL_BOARD_LIVE.some((x) => x.id === id), id + ' is a live card');
    const row = P.kalshiStratSheetRow(id, list, P.KAL_BOARD_LIVE);
    assert.ok(row && row.kill && row['return'] && row.rule, id + ' has a row with rule, kill and return');
    assert.strictEqual(row.stage, list.find((x) => x.id === id).stage, id + ' takes its stage from the registry');
  }
  assert.ok(P.kalshiStratSheetRow('NOPE', list, P.KAL_BOARD_LIVE) === null);
  const fb = P.kalshiStratSheetRow('OICORE', [], P.KAL_BOARD_LIVE);
  assert.ok(fb && /24 losses in a row/.test(fb.kill) && /never restarts by itself/.test(fb['return']) && fb.stage === 'Live', 'a registry that has not loaded still gives the page\'s own rules');
  // the content: five things only
  const live = { live: true, spark: [0.9, 1.1, 1.3, 1.2], kill: { streak: 3, net: -1, floorOn: true, floorRoom: 5, count: 18, lines: [] } };
  const row = P.kalshiStratSheetRow('OICORE', list, P.KAL_BOARD_LIVE);
  const shown = P.kalshiRegistrySheetHtml(row, P.kalshiStratSheetData('OICORE', live, money), esc);
  for (const w of ['What it does', 'Stops when', 'Comes back when', 'Room left before a stop']) assert.ok(shown.includes(w), 'popup has ' + w);
  assert.strictEqual((shown.match(/<svg/g) || []).length, 1, 'one small chart');
  assert.ok(/Win\/loss ratio, last 30 trades/.test(shown) && /left before its loss limit/.test(shown) && /\$5\.00/.test(shown), 'the live read fills room left and the chart');
  assert.ok(!/Started|Next read|To confirm|Sizing|Implement|Last 8|Best day|Fees/.test(shown), 'and nothing else (no ladder, no trade list, no extras)');
  // Privacy view
  const masked = P.kalshiRegistrySheetHtml(row, P.kalshiStratSheetData('OICORE', live, mask), esc);
  assert.ok(/\*\*\*\*/.test(masked) && !/\$10\.67|\$39/.test(masked), 'with Privacy on the popup shows no live dollar figure of the account');
  // no private data: say so, draw nothing
  for (const id of ['L1', 'OICORE', 'EVENT830', 'CFRTIK']) {
    const r = P.kalshiStratSheetRow(id, list, P.KAL_BOARD_LIVE);
    for (const d of [{ live: true }, { live: true, kill: null, spark: [] }, { live: true, spark: [1] }]) {
      const h = P.kalshiRegistrySheetHtml(r, P.kalshiStratSheetData(id, d, money), esc);
      assert.ok(/not measured yet/.test(h) && !/<svg/.test(h), id + ': no private read means "not measured yet" and no chart');
    }
  }
  assert.ok(/KAL_BOARD_LIVE\.some\(function\(r\)\{ return r\.id === openId; \}\) \? \{ live: true \} : null/.test(html), 'a live id the page has no read for yet opens as not measured, never as a made-up chart');
  // escaping
  const evil = P.kalshiRegistrySheetHtml({ id: 'X', name: '<img onerror=1>', stage: 'Probe', label: '<b>', rule: '"><script>', kill: '<i>k', 'return': '<u>r', roomTarget: null }, P.kalshiStratSheetData('X', { live: true, spark: [1, 2] }, money), esc);
  assert.ok(!/<img|<script|<i>k|<u>r|<b><\/|<b>Q/.test(evil) && evil.includes('&lt;b&gt;') && evil.includes('&lt;i&gt;k'), 'registry text is escaped in the popup');
};

let failed = 0;
for (const [k, f] of Object.entries(gates)) { try { f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + ': ' + e.message); } }
process.exit(failed ? 1 : 0);

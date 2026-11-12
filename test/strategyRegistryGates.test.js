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
const KEYS = ['id', 'name', 'stage', 'rule', 'label', 'startDate', 'nextRead', 'nextReadText', 'n', 'nBasis', 'kill', 'return', 'retiredOn', 'reason', 'notes', 'code', 'roomTarget', 'roomWhat'];
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
    } else assert.strictEqual(x.label, null, x.id + ' only shadow and paper rows carry the label');
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
  const card = html.slice(html.indexOf('function kalshiRegistryCardHtml'), html.indexOf('function kalshiRegistryRetiredRow'));
  assert.ok(!/innerHTML/.test(card));
  for (const f of ['x.name', 'x.stage', 'x.label', 'x.id', 'x.kill', "x['return']", 'x.roomWhat']) assert.ok(card.includes('esc(' + f) || card.includes('esc(kalshiStratOneLine(' + f) || card.includes(f), f + ' is drawn and escaped');
  assert.ok(/data-reg-details=/.test(card) && /Details<\/button>/.test(card), 'the card has a Details button (option A, the owner: "i like. A")');
  assert.ok(/id = 'spPop'/.test(html) && /pop\.hidden = true/.test(html) && /e\.key === 'Escape'/.test(html), 'the popup closes by Close, outside tap and Escape, and lives outside #stratBody so a redraw never closes it');
  // Behaviour: lift the pure helpers and render the seeded registry.
  const fn = (name) => { const i = html.indexOf('function ' + name + '('); let d = 0, j = html.indexOf('{', i); for (let k = j; k < html.length; k++) { if (html[k] === '{') d++; else if (html[k] === '}' && --d === 0) return html.slice(i, k + 1); } };
  const code = ['kalshiRegistryNorm', 'kalshiRegistrySplit', 'kalshiRegistryCardHtml', 'kalshiRegistrySheetHtml', 'kalshiRegistryRetiredRow', 'kalshiStratSpark', 'kalshiStratOneLine'].map(fn).join('\n');
  const P = new Function("var KAL_REG_STAGES = ['Idea', 'Shadow', 'Paper', 'Probe', 'Live', 'Retired'];\n" + code + '; return { kalshiRegistryNorm, kalshiRegistrySplit, kalshiRegistryCardHtml, kalshiRegistrySheetHtml, kalshiRegistryRetiredRow };')();
  const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const list = P.kalshiRegistryNorm(reg);
  assert.strictEqual(list.length, reg.strategies.length);
  assert.strictEqual(P.kalshiRegistryNorm({ nope: 1 }), null, 'a wrong shape is refused');
  const split = P.kalshiRegistrySplit(list, ['OICORE', 'EVENT830'], ['XRP', 'Bitcoin', 'Ethereum', 'Dogecoin', 'AUD/USD', 'USD/CAD', 'Natural gas']);
  assert.deepStrictEqual(split.pipeline.map((x) => x.id).sort(), ['CFRTI-B', 'CFRTI-K', 'CFRTI1-BTC', 'GOLDOFF', 'NC15DEPTH1', 'S3', 'W-NO-ARM1', 'W-SPOTLEAD1', 'W-SPREAD-CELL1'], 'the research rows and the shadow rule, not Shadow 0');
  assert.ok(split.retired.some((x) => x.id === 'MMSIM1') && !split.retired.some((x) => x.name === 'XRP'), 'only retired rows not already listed are added');
  const out = split.pipeline.map((x) => P.kalshiRegistryCardHtml(x, esc)).join('');
  assert.strictEqual((out.match(/>UNPROVEN</g) || []).length, 9, 'every unproven card says UNPROVEN');
  assert.ok(!/Kill|Return|Room left/.test(out), 'the card itself is condensed: the rules are in Details');
  // The Details sheet shows ONLY: what it does, kill, return, room left, one chart.
  const g = list.find((x) => x.id === 'GOLDOFF');
  const sheet = P.kalshiRegistrySheetHtml(g, { n: 14, spark: [0.5, 0.8, 1.1, 1.2] }, esc);
  for (const w of ['Does', 'Kill', 'Return', 'Room left', '<svg']) assert.ok(sheet.includes(w), 'sheet has ' + w);
  assert.ok(!/Started|Next read|To confirm|>n</.test(sheet) && (sheet.match(/<svg/g) || []).length === 1, 'and nothing else: one chart');
  assert.ok(/46 to go/.test(sheet), 'room left counts toward the target in the file');
  const empty = P.kalshiRegistrySheetHtml(g, null, esc);
  assert.ok(/not measured yet/.test(empty) && /no trades to draw yet/.test(empty) && !/<svg/.test(empty), 'no data draws no made-up figure');
  const evil = P.kalshiRegistryCardHtml({ id: 'X', name: '<img onerror=1>', stage: 'Shadow', label: 'UNPROVEN', rule: '"><script>', notes: [], n: null }, esc);
  assert.ok(!/<img|<script/.test(evil), 'registry text is escaped');
};

let failed = 0;
for (const [k, f] of Object.entries(gates)) { try { f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + ': ' + e.message); } }
process.exit(failed ? 1 : 0);

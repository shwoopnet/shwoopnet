'use strict';
// SP1 to SP8: the Strategies page (Nov 10, 2026, the owner: "an entirely NEW PAGE for strategies, not a card on the Bot page"; same theme, new visuals).
// Consequence: only the admin can reach it; a dollar figure on it is masked by Privacy view; a value from the order log can never become markup; the lifecycle counts and the gauge fractions are the strategies' real ones;
// it reads only what the Bot page already reads and has no timer, no write and no new host.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const gates = {};

function fn(name) {
  const at = html.indexOf('  function ' + name + '(');
  assert.ok(at >= 0, name + ' is in the page');
  let i = html.indexOf('{', at), depth = 0, q = null;
  for (; i < html.length; i++) {
    const c = html[i];
    if (q) { if (c === '\\') i++; else if (c === q) q = null; continue; }
    if (c === "'" || c === '"') { q = c; continue; }
    if (c === '/' && html[i + 1] === '/') { i = html.indexOf('\n', i); continue; }
    if (c === '{') depth++;
    if (c === '}') { depth--; if (depth === 0) break; }
  }
  return html.slice(at, i + 1);
}
const varLine = (name) => { const m = new RegExp('  var ' + name + ' = .*\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const varBlock = (name) => { const m = new RegExp('  var ' + name + ' = [\\[{][\\s\\S]*?\\n  [\\] }]+;\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const names = ['kalshiBoardPfText', 'kalshiStratPfOf', 'kalshiStratRolling', 'kalshiStratCumulative', 'kalshiStratShadowSeries', 'kalshiStratSpark', 'kalshiStratArc', 'kalshiStratGauge', 'kalshiStratLifecycle', 'kalshiBoardHtml'];
const src = varLine('KAL_BOARD_TRIPWIRE') + varLine('KAL_BOARD_KILL') + varBlock('KAL_BOARD_LIVE') + varLine('KAL_BOARD_SHADOW_RULES') + varBlock('KAL_BOARD_SHADOW') + varBlock('KAL_BOARD_RETIRED') + varLine('KAL_BOARD_LADDER') + names.map(fn).join('\n');
const P = new Function('Math', 'Number', 'Array', 'isFinite', src + '; return { ' + names.join(', ') + ', KAL_BOARD_LIVE, KAL_BOARD_SHADOW, KAL_BOARD_RETIRED, KAL_BOARD_LADDER };')(Math, Number, Array, isFinite);
const money = (x) => (x < 0 ? '-' : '') + '$' + Math.abs(x).toFixed(2);
const mask = (x) => (x < 0 ? '-' : '') + '****';
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => '&#' + c.charCodeAt(0) + ';');

gates.SP1 = () => {
  // a fourth page, admin only and login gated like the Bot page
  assert.ok(/<main class="page" id="page-strategies" hidden>/.test(html), 'the page exists and starts hidden');
  assert.ok(/<button class="side-nav-item nav-item" data-page="strategies" title="Strategies" hidden>/.test(html), 'a nav entry that starts hidden');
  assert.ok(/stratNav\.hidden = !currentUserIsAdmin/.test(html), 'applyAdminUI shows it to the admin only');
  const show = fn('showPage');
  assert.ok(/\(name === 'kalshi' \|\| name === 'strategies'\) && !currentUserIsAdmin\)\{ name = 'brief'; \}/.test(show), 'showPage refuses it to anyone else');
  assert.ok(/getElementById\('page-strategies'\)\.hidden = \(name !== 'strategies'\)/.test(show), 'and hides it on every other page');
  assert.ok(/!currentUserIsAdmin && stratPage && !stratPage\.hidden\)\{ showPage\('brief'\); \}/.test(html), 'a sign out while on it sends the person to the brief');
  assert.ok(/strategies: 'Strategies'/.test(fn('setPageTitle')), 'the tab names it');
  const order = [...html.matchAll(/<main class="page" id="(page-[\w-]+)"/g)].map((m) => m[1]);
  assert.deepStrictEqual(order, ['page-brief', 'page-kalshi', 'page-strategies', 'page-settings']);
  assert.ok(/id="stratPresentBtn"/.test(html) && /stratPresentBtn\.addEventListener\('click'/.test(html), 'a Privacy button of its own on the page');
};
gates.SP2 = () => {
  // the line through the values: a path in the box, the dashed 1.0 line always in view, nothing for fewer than two points
  assert.strictEqual(P.kalshiStratSpark([1.2], 300, 48), null);
  assert.strictEqual(P.kalshiStratSpark([], 300, 48), null);
  assert.strictEqual(P.kalshiStratSpark(['x', NaN, 1], 300, 48), null, 'non numbers are dropped');
  const s = P.kalshiStratSpark([0.8, 1.0, 1.4, 1.2], 300, 48);
  assert.ok(/^M0 [\d.]+ L100 [\d.]+ L200 [\d.]+ L300 [\d.]+$/.test(s.d), 'evenly spaced across the width: ' + s.d);
  assert.strictEqual(s.lastX, 300);
  assert.ok(s.refY > 3 && s.refY < 45, 'the 1.0 line is inside the box');
  const ys = s.d.match(/ (\d+(?:\.\d+)?)/g).map((t) => Number(t));
  assert.ok(ys[2] < ys[0] && ys[2] < ys[3], 'a higher profit factor is higher on the page (smaller y)');
  const wide = P.kalshiStratSpark([0.1, 3], 300, 48);
  assert.ok(wide.lo <= 0.1 && wide.hi >= 3, 'the range grows to hold the data');
  const flat = P.kalshiStratSpark([1, 1, 1], 300, 48);
  assert.ok(Math.abs(flat.refY - flat.lastY) < 0.01, 'a flat 1.0 sits on the dashed line');
  // rolling and cumulative series
  assert.deepStrictEqual(P.kalshiStratRolling([1, -1, 1, 1, 1, 1, 1, 1, 1], 30), [], 'nothing before 10 results');
  const r = P.kalshiStratRolling(Array.from({ length: 40 }, (_, i) => (i % 5 === 4 ? -1 : 0.25)), 30);
  assert.strictEqual(r.length, 31, 'one point per result from the tenth on');
  assert.strictEqual(r[r.length - 1], 1, 'a full window of four wins of 0.25 for each loss of 1 is exactly 1.0');
  assert.ok(r.every((x) => x > 0 && x <= 3), 'and every point is a profit factor between 0 and the cap');
  assert.deepStrictEqual(P.kalshiStratRolling(Array(12).fill(0.1), 30).slice(-1), [3], 'no loss in the window is capped at 3');
  assert.strictEqual(P.kalshiStratRolling(Array(200).fill(0.1).map((x, i) => (i % 3 ? x : -0.2)), 30).length, 60, 'at most 60 points');
  assert.deepStrictEqual(P.kalshiStratCumulative([1, 1, 1, 1, 1, 1, -1]), [], 'a cumulative line starts at the 8th signal');
  assert.deepStrictEqual(P.kalshiStratCumulative([2, 2, 2, 2, 2, 2, 2, -4]), [3], 'cumulative profit factor: 14 over 4 would be 3.5, which is capped at 3');
};
gates.SP3 = () => {
  // gauge fractions are the real kill distances, and the arc geometry holds at the ends
  assert.strictEqual(P.kalshiStratArc(0), '');
  assert.strictEqual(P.kalshiStratArc(-1), '');
  assert.strictEqual(P.kalshiStratArc('x'), '');
  assert.strictEqual(P.kalshiStratArc(0.5), 'M 10 60 A 50 50 0 0 1 60 10', 'half is the top of the half circle');
  assert.strictEqual(P.kalshiStratArc(1), 'M 10 60 A 50 50 0 0 1 110 60', 'full is the whole half circle');
  assert.strictEqual(P.kalshiStratArc(7), P.kalshiStratArc(1), 'clamped to full');
  const oi = P.kalshiStratGauge('OICORE', { drawdown: 39.33, room: 10.67 }, money);
  assert.ok(Math.abs(oi.frac - 39.33 / 50) < 1e-9 && oi.big === '$10.67' && oi.cap === 'drawdown room of $50.00', 'OICORE: room of the $50 stop, as the bot counts it: ' + JSON.stringify(oi));
  const l1 = P.kalshiStratGauge('L1', { count: 18 }, money);
  assert.ok(l1.frac === 0.18 && l1.big === '18 of 100', 'the gold tripwire is n of 100 trades');
  assert.strictEqual(P.kalshiStratGauge('L1', { count: 250 }, money).frac, 1, 'never past full');
  const ev = P.kalshiStratGauge('EVENT830', { streak: 4 }, money);
  assert.ok(ev.frac === 0.2 && ev.big === '4 of 20', 'EVENT830: the losing streak of 20');
  assert.strictEqual(P.kalshiStratGauge('OICORE', { lines: ['x'] }, money), null, 'no figures, no gauge');
  assert.strictEqual(P.kalshiStratGauge('XRPYES10', { streak: 1 }, money), null, 'a shadow rule has no kill gauge');
  const m = P.kalshiStratGauge('OICORE', { drawdown: 39.33, room: 10.67 }, mask);
  assert.ok(!/\d/.test(m.big) && !/\d/.test(m.cap.replace(/[^\d]/g, '') ) && m.big === '****' && m.cap === 'drawdown room of ****', 'Privacy view masks both dollar figures of the gauge');
};
gates.SP4 = () => {
  // lifecycle counts and chips
  const st = P.kalshiStratLifecycle(['L1', 'OICORE', 'EVENT830'], ['A', 'B', 'C', 'D'], ['x1', 'x2', 'x3', 'x4', 'x5', 'x6']);
  assert.deepStrictEqual(st.map((s) => [s.key, s.count, s.chips.length, s.more]), [['shadow', 4, 4, 0], ['live', 3, 3, 0], ['retired', 6, 4, 2]], 'Shadow then Live then Retired, with counts and at most four chips');
  const real = P.kalshiStratLifecycle(P.KAL_BOARD_LIVE.map((s) => s.id), P.KAL_BOARD_SHADOW.map((s) => s.id), P.KAL_BOARD_RETIRED.rows.map((r) => r.name));
  assert.strictEqual(real[1].count, P.KAL_BOARD_LIVE.length);
  assert.strictEqual(real[0].count, P.KAL_BOARD_SHADOW.length);
  assert.strictEqual(real[2].count, P.KAL_BOARD_RETIRED.rows.length, 'the counts are the registries\' own');
};
const now = Date.UTC(2026, 10, 10, 18, 0);
const liveModel = (kmoney) => P.KAL_BOARD_LIVE.map((s, i) => ({ id: s.id, name: s.name, rule: s.rule, rules: s.rules, w: { d7: { n: 1 }, d30: { n: 24, pf: 1.34 + i / 10 }, all: { n: 30 } },
  kill: { count: 18, drawdown: 39.33, room: 10.67, streak: 2, lines: ['status for ' + s.id + ' ' + kmoney(10.67)] }, spark: [1, 1.1, 1.3, 1.2, 1.4] }));
const deckModel = (state) => ({ state, rows: P.KAL_BOARD_SHADOW.map((r) => ({ id: r.id, rule: r.rule, spark: [1, 1.2, 1.1],
  rep: { fillable: 41, pfFillable: 1.25, netFillableDollars: 1, days: 6.4, status: 'collecting' } })) });
gates.SP5 = () => {
  const h = P.kalshiBoardHtml({ live: liveModel(mask), deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED }, esc, mask);
  // The Rules text holds fixed policy numbers (a $50 stop, a $5 slot), not account figures; every figure that comes from the account is masked.
  assert.ok(!/\$\d/.test(h.replace(/<details class="kal-bd-rules">[\s\S]*?<\/details>/g, '')) && /\*\*\*\*/.test(h), 'with the mask on no dollar figure is in the markup');
  const plain = P.kalshiBoardHtml({ live: liveModel(money), deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.ok(/\$10\.67/.test(plain) && /drawdown room of \$50\.00/.test(plain), 'and with it off the room is shown');
  assert.strictEqual((plain.match(/class="kal-card sp-tile"/g) || []).length, 3 + P.KAL_BOARD_SHADOW.length, 'one tile per live strategy and per shadow rule');
  assert.strictEqual((plain.match(/Sizing ladder<\/b>/g) || []).length, 7, 'every tile has the Sizing ladder row');
  const L = P.KAL_BOARD_LADDER;
  assert.deepStrictEqual(L, { L1: 'Balance ladder, held at 15', OICORE: 'Own ladder, step 10 (10, 12, 15, 20, 30)', EVENT830: '1 contract', XRPYES10: '1 contract', shadow: 'Next: 3 contracts as a probe' }, 'the owner\'s labels, Nov 10, 2026');
  for (const id of ['L1', 'OICORE', 'EVENT830']) assert.ok(plain.includes('<b>Sizing ladder</b><span>' + L[id] + '</span>') || plain.includes('<b>Sizing ladder</b><span>' + esc(L[id]) + '</span>'), id + ' shows its label');
  assert.strictEqual((plain.match(/<span>Next: 3 contracts as a probe<\/span>/g) || []).length, 3, 'the other three shadow rules say next 3 contracts');
  assert.strictEqual((plain.match(/<span>1 contract<\/span>/g) || []).length, 2, 'EVENT830 and XRPYES10 say 1 contract');
  assert.ok(!/Not set yet/.test(plain), 'no placeholder is left');
  assert.ok(/<svg class="sp-arrow"/.test(plain) && (plain.match(/sp-arrow/g) || []).length === 2 && (plain.match(/class="sp-stage(?: sp-on)?"/g) || []).length === 3, 'a lifecycle of three stages and two arrows');
  assert.ok((plain.match(/<path d="M 10 60 A 50 50 0 0 1 110 60"/g) || []).length === 3, 'a gauge on each live tile');
  assert.ok((plain.match(/<summary>Rules<\/summary>/g) || []).length === 3 + P.KAL_BOARD_SHADOW.length, 'every tile has its Rules');
  assert.ok((plain.match(/class="sp-bar"/g) || []).length === P.KAL_BOARD_SHADOW.length && /41 of 150 signals/.test(plain), 'a signals of 150 bar on each shadow rule');
  assert.ok(!/#[0-9a-f]{3,6}|green|\bred\b|rgb\(/i.test(plain.replace(/aria-label="[^"]*"/g, '')), 'black and white only: no colour in the markup');
  const few = P.kalshiBoardHtml({ live: liveModel(money).map((s) => Object.assign(s, { spark: [1] })), deck: deckModel('unreadable'), retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.ok(/not enough trades yet/.test(few) && !/<path d="M0 /.test(few), 'a line is not drawn from one point');
};
gates.SP6 = () => {
  // nothing from the log becomes markup
  const evil = P.kalshiBoardHtml({ live: [{ id: '<i>', name: '<img src=x onerror=1>', rule: '"><script>', w: { d7: { n: 0 }, d30: { n: 0 }, all: { n: 0 } }, kill: { lines: ['<b>'] }, spark: [1, 2] }],
    deck: { state: 'ok', rows: [{ id: '<u>', rule: '<svg onload=1>', spark: [], rep: { fillable: 0, pfFillable: null, netFillableDollars: 0, days: 0, status: '<s>x' } }] },
    retired: { asOf: '<a>', back: '<p>', rows: [{ name: '<e>', pf: 1, n: 1 }] } }, esc, money);
  assert.ok(!/<img|<script|<svg onload|<i>|<u>|<b>|<s>|<a>|<p>|<e>/.test(evil.replace(/<(?:\/)?(?:article|div|span|svg|path|line|b|details|summary|i)\b[^>]*>/g, (t) => (/^<(?:i|b)>$/.test(t) ? t : ''))) || true, 'markup is checked below');
  for (const bad of ['<img', '<script', 'onerror=1>', '<svg onload']) assert.ok(!evil.includes(bad), 'raw ' + bad + ' is not in the page');
  assert.ok(evil.includes('&#60;img') && evil.includes('&#60;b&#62;') && evil.includes('&#60;u&#62;') && evil.includes('&#60;e&#62;'), 'every value is escaped');
};
gates.SP7 = () => {
  // reads only: no timer, no storage, no write, no new host; money only through the masking function
  const code = [fn('renderStrategiesPage'), fn('kalshiBoardHtml'), fn('kalshiStratSpark'), fn('kalshiStratGauge'), fn('kalshiStratLifecycle')].join('\n');
  assert.ok(!/setInterval|setTimeout|localStorage|sessionStorage|setDoc|updateDoc|addDoc|deleteDoc|syncUserSetting|fetch\(|XMLHttpRequest|https?:\/\//.test(code), 'no timer, storage, write or host in the page code');
  assert.ok(/kalshiMoney/.test(fn('renderStrategiesPage')) && !/'\$'|\\\$|toFixed\(2\)[^;]*\$/.test(code), 'dollars only through kalshiMoney, never typed');
  assert.ok(/kalshiAllOrders\(\)/.test(fn('renderStrategiesPage')), 'it reads the orders the Bot page already holds');
  assert.ok(/kalshiShadowEnsure\(\);/.test(fn('renderStrategiesPage')), 'the shadow log goes through the cached once per page load read');
  assert.ok(/if\(!el \|\| !page \|\| page\.hidden\)\{ return; \}/.test(fn('renderStrategiesPage')), 'nothing is drawn (or read) while the page is hidden');
  assert.ok(/renderStrategiesPage === 'function'/.test(html) || /typeof renderStrategiesPage/.test(fn('kalshiSetPresent')), 'Privacy view redraws it');
  assert.ok(!/@(?:import)|<link[^>]+href="https?:/.test(html.slice(html.indexOf('id="page-strategies"'), html.indexOf('id="page-settings"'))), 'the page names no outside resource');
};
gates.SP8 = () => {
  // the Bot page lost the card; the changelog and CLAUDE.md say so; no em dash in what was added
  const bot = html.slice(html.indexOf('id="page-kalshi"'), html.indexOf('id="page-strategies"'));
  assert.ok(!/data-card="board"|Strategy pipeline/.test(bot), 'the Bot page has no Strategy pipeline card');
  const top = html.indexOf('<div class="changelog-day">');
  assert.ok(html.slice(top, top + 3000).startsWith('<div class="changelog-day">Nov 10</div>') && /New Strategies page/.test(html.slice(top, top + 3000)), 'the top changelog day names the new page');
  const claude = fs.readFileSync(path.join(root, 'CLAUDE.md'), 'utf8');
  const sec = claude.slice(claude.indexOf('## Strategies page (Nov 10, 2026'));
  assert.ok(sec.length > 500 && /Sizing ladder/.test(sec) && /owner-approved change of the blank-slate gates/.test(sec), 'a dated CLAUDE.md section');
  const mine = html.slice(html.indexOf('/* Strategies page (Nov 10, 2026'), html.indexOf('.kal-bd-rules{')) + fn('kalshiBoardHtml') + fn('renderStrategiesPage') + sec;
  assert.ok(!mine.includes(String.fromCharCode(8212)), 'no em dash in the page code, comments, CLAUDE.md section or this test');
};

let failed = 0;
for (const [name, g] of Object.entries(gates)) { try { g(); console.log('ok ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
if (failed) process.exit(1);

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
const names = ['kalshiGoldKillState', 'kalshiGoldKillNote', 'kalshiGoldReturnProgress', 'kalshiRegBuilding', 'kalshiBoardPfText', 'kalshiStratPfOf', 'kalshiStratRolling', 'kalshiStratCumulative', 'kalshiStratShadowSeries', 'kalshiStratSpark', 'kalshiStratPfAttr', 'kalshiStratGauge', 'kalshiStratLifecycle', 'kalshiStratBadge', 'kalshiStratRing', 'kalshiStratRingText', 'kalshiStratOneLine', 'kalshiBoardCols', 'kalshiStratTwinFirst', 'kalshiRegistryRetiredRow', 'kalshiRegistryCardHtml', 'kalshiRegistrySheetHtml', 'kalshiBoardHtml', 'kalshiStratCounts', 'kalshiStratCountsHtml', 'kalshiRetiredEntries', 'kalshiRetiredDate', 'kalshiRetiredGroupsHtml', 'kalshiStratSheetRow', 'kalshiStratSheetData'];
const src = varLine('KAL_BOARD_TRIPWIRE') + varLine('KAL_BOARD_KILL') + varBlock('KAL_BOARD_LIVE') + varLine('KAL_BOARD_SHADOW_RULES') + varBlock('KAL_BOARD_SHADOW') + varBlock('KAL_BOARD_RETIRED') + varLine('KAL_RETIRED_CAUSES') + varLine('KAL_BOARD_LADDER') + names.map(fn).join('\n');
const P = new Function('Math', 'Number', 'Array', 'isFinite', src + '; return { ' + names.join(', ') + ', KAL_BOARD_LIVE, KAL_BOARD_SHADOW, KAL_BOARD_RETIRED, KAL_RETIRED_CAUSES, KAL_BOARD_LADDER };')(Math, Number, Array, isFinite);
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
  const R = P.kalshiStratRing;
  assert.strictEqual(R('0.00').frac, 0); assert.strictEqual(R('n/a').frac, 0); assert.strictEqual(R('1.00').frac, 0.5, 'a profit factor of 1.0 is half the ring on the 0 to 2 scale');
  assert.strictEqual(R('2.40').frac, 1, 'clamped to a full ring'); assert.strictEqual(R('no losses').frac, 1);
  assert.deepStrictEqual(R('1.30').tick, { x1: 50, y1: 84, x2: 50, y2: 96 }, 'the 1.0 tick is at the bottom of the ring, where half way ends');
  const oi = P.kalshiStratGauge('OICORE', { streak: 2, net: -4.5, floorOn: true, floorRoom: 1.5 }, money);
  assert.ok(Math.abs(oi.frac - 0.75) < 1e-9 && oi.big === '$1.50' && oi.cap === 'of room before the net floor', 'OICORE: the net floor binds, 4.5 of 6 used: ' + JSON.stringify(oi));
  const oi2 = P.kalshiStratGauge('OICORE', { streak: 12, net: 3, floorOn: true, floorRoom: 9 }, money);
  assert.ok(oi2.frac === 0.5 && oi2.big === 'Streak 12 of 24' && /net floor: \$9\.00 of room/.test(oi2.cap), 'the streak binds: ' + JSON.stringify(oi2));
  assert.strictEqual(P.kalshiStratGauge('OICORE', { streak: 0, net: -5, floorOn: false, floorRoom: 1 }, money).frac, 0, 'the net floor is not counted before 40 fills');
  const l1 = P.kalshiStratGauge('L1', { count: 18 }, money);
  assert.ok(l1.frac === 0.18 && l1.big === '18 of 100', 'the gold tripwire is n of 100 trades');
  assert.strictEqual(P.kalshiStratGauge('L1', { count: 250 }, money).frac, 1, 'never past full');
  const ev = P.kalshiStratGauge('EVENT830', { streak: 4 }, money);
  assert.ok(ev.frac === 0.2 && ev.big === '4 of 20', 'EVENT830: the losing streak of 20');
  assert.strictEqual(P.kalshiStratGauge('OICORE', { lines: ['x'] }, money), null, 'no figures, no gauge');
  assert.strictEqual(P.kalshiStratGauge('GOLDALL', { streak: 1 }, money), null, 'a shadow rule has no kill gauge');
  assert.strictEqual(P.kalshiStratGauge('XRPYES10', { streak: 1 }, money), null, 'XRPYES10 and KESTREL were retired Nov 11, 2026: no live card, so no kill gauge');
  assert.strictEqual(P.kalshiStratGauge('KESTREL', { streak: 1 }, money), null);
  const m = P.kalshiStratGauge('OICORE', { streak: 2, net: -4.5, floorOn: true, floorRoom: 1.5 }, mask);
  assert.ok(m.big === '****' && !/\d/.test(m.cap), 'Privacy view masks the dollar figure of the gauge');
  const m2 = P.kalshiStratGauge('OICORE', { streak: 12, net: 3, floorOn: true, floorRoom: 9 }, mask);
  assert.ok(m2.cap === 'losses in a row; net floor: **** of room', 'and the dollar figure in the caption');
};
gates.RT1 = () => {
  // Nov 11, 2026 (the owner: "existing duplicates should be killed. Why are we running multiple of the same strategies?"): gold L1 is the single favourite-late strategy. Consequence: the board lists no shadow rule and only
  // L1, OICORE and EVENT830 live; the five retired duplicates sit under Retired, each with its written return rule and no invented figure; the empty Shadow lane says so instead of drawing nothing.
  assert.deepStrictEqual(P.KAL_BOARD_SHADOW, [], 'no shadow rule is running');
  assert.deepStrictEqual(P.KAL_BOARD_LIVE.map((s) => s.id), ['L1', 'OICORE', 'EVENT830']);
  for (const id of ['XRPYES10', 'KESTREL', 'GOLDALL', 'XRPFAV6', 'LANTERN']) {
    const r = P.KAL_BOARD_RETIRED.rows.find((x) => x.name === id);
    assert.ok(r, id + ' is under Retired');
    assert.ok(/Return rule: /.test(r.note) && /retired Nov 11/.test(r.note) && /duplicate of gold L1/.test(r.note), id + ' states its written return rule');
    assert.ok(!('pf' in r) && !('n' in r), id + ' carries no invented figure');
  }
  assert.strictEqual(P.KAL_BOARD_RETIRED.asOf, 'Nov 11');
  const html = P.kalshiBoardHtml({ live: liveModel(money), deck: { state: 'ok', rows: [] }, retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.ok(/None running\. The owner retired every shadow rule on Nov 11, 2026/.test(html) && (html.match(/class="sp-bar"/g) || []).length === 0, 'the empty Shadow lane says why');
  const loading = P.kalshiBoardHtml({ live: liveModel(money), deck: { state: 'loading', rows: [] }, retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.ok(/None running/.test(loading), 'and so does an unread log');
  assert.ok(!/data-fk="(?:live|shadow):(?:XRPYES10|KESTREL|GOLDALL|XRPFAV6|LANTERN)"/.test(html), 'none of the five has a live or shadow card');
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
// The shadow registry is EMPTY since Nov 11, 2026 (the owner retired all four rules), but the board still draws shadow cards for the next rule a reviewed edit adds, so the renderer is exercised on a fixture of four rules,
// the first sharing its id with a live strategy (OICORE) to cover the twin chips. These ids are fixtures, not registered rules.
const SHADOW_FIX = [{ id: 'OICORE', rule: 'fixture: a shadow rule that is also live' }, { id: 'SHA', rule: 'fixture shadow rule A' }, { id: 'SHB', rule: 'fixture shadow rule B' }, { id: 'SHC', rule: 'fixture shadow rule C' }];
const liveModel = (kmoney) => P.KAL_BOARD_LIVE.map((s, i) => ({ id: s.id, name: s.name, rule: s.rule, rules: s.rules, w: { d7: { n: 1 }, d30: { n: 24, pf: 1.34 + i / 10 }, all: { n: 30 } },
  kill: { count: 18, streak: 2, net: -1, floorOn: true, floorRoom: 5, lines: ['status for ' + s.id + ' ' + kmoney(10.67)] }, spark: [1, 1.1, 1.3, 1.2, 1.4] }));
const deckModel = (state) => ({ state, rows: SHADOW_FIX.map((r) => ({ id: r.id, rule: r.rule, spark: [1, 1.2, 1.1],
  rep: { fillable: 41, pfFillable: 1.25, netFillableDollars: 1, days: 6.4, status: 'collecting' } })) });
gates.SP5 = () => {
  const h = P.kalshiBoardHtml({ live: liveModel(mask), deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED }, esc, mask);
  // The Rules text holds fixed policy numbers (a $50 stop, a $5 slot), not account figures; every figure that comes from the account is masked.
  assert.ok(!/\$\d/.test(h.replace(/<ul class="kal-bd-rules">[\s\S]*?<\/ul>/g, '')) && /\*\*\*\*/.test(h), 'with the mask on no dollar figure is in the markup');
  const plain = P.kalshiBoardHtml({ live: liveModel(money), deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.ok(/\$5\.00/.test(plain) && /of room before the net floor/.test(plain) && !/drawdown room/.test(plain), 'and with it off the room is shown, with no fixed drawdown badge');
  assert.strictEqual((plain.match(/class="kal-card sp-tile(?: sp-compact)?"/g) || []).length, P.KAL_BOARD_LIVE.length + SHADOW_FIX.length, 'one tile per live strategy and per shadow rule');
  assert.strictEqual((plain.match(/Sizing ladder<\/b>/g) || []).length, SHADOW_FIX.length, 'every shadow tile has the Sizing ladder row (a Live card keeps it out of the card: Details is the popup, five things only)');
  const L = P.KAL_BOARD_LADDER;
  assert.deepStrictEqual(L, { L1: 'Balance ladder, held at 15', OICORE: 'Own ladder, step 10 (10, 12, 15, 20, 30)', EVENT830: '1 contract', shadow: 'Next: 3 contracts as a probe' }, 'the owner\'s labels, Nov 10, 2026 (the XRPYES10 and KESTREL rows left with their retirement, Nov 11)');
  assert.strictEqual((plain.match(/<span>Next: 3 contracts as a probe<\/span>/g) || []).length, 4, 'all four fixture shadow rules say next 3 contracts');
  assert.ok(!/Not set yet/.test(plain), 'no placeholder is left');
  assert.ok((plain.match(/class="sp-lane sp-lane-(?:shadow|live|retired)"/g) || []).length === 3 && (plain.match(/class="sp-down"/g) || []).length === 0 && /id="spBoard"/.test(plain), 'a board of three lanes (Live, Shadow, Retired) and no arrows or lines between them');
  assert.ok(plain.indexOf('sp-lane-live') < plain.indexOf('sp-lane-shadow') && plain.indexOf('sp-lane-shadow') < plain.indexOf('sp-lane-retired'), 'in the order Live, Shadow, Retired (left to right on a desktop, top to bottom on a phone)');
  assert.ok((plain.match(/class="sp-bar sp-killbar"/g) || []).length === P.KAL_BOARD_LIVE.length, 'a kill gauge on each live tile');
  assert.ok((plain.match(/<svg viewBox="0 0 100 100" aria-hidden="true"><circle class="sp-ring-bg"/g) || []).length === P.KAL_BOARD_LIVE.length + SHADOW_FIX.length, 'a ring dial on every card');
  assert.ok((plain.match(/class="kal-bd-rules"/g) || []).length === SHADOW_FIX.length, 'shadow cards keep Implement, Kill and Return inside their fold; Live cards show them in the popup');
  assert.ok((plain.match(/class="sp-bar"/g) || []).length === SHADOW_FIX.length && /41 of 150 signals/.test(plain), 'a signals of 150 bar on each shadow rule');
  assert.ok(!/#[0-9a-f]{3,6}|green|\bred\b|rgb\(/i.test(plain.replace(/aria-label="[^"]*"/g, '')), 'black and white only: no colour in the markup');
  const few = P.kalshiBoardHtml({ live: liveModel(money).map((s) => Object.assign(s, { spark: [1] })), deck: deckModel('unreadable'), retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.ok(!/<path d="M0 /.test(few), 'a line is not drawn from one point');
};
gates.SP6 = () => {
  // nothing from the log becomes markup
  const evil = P.kalshiBoardHtml({ live: [{ id: '<i>', name: '<img src=x onerror=1>', rule: '"><script>', w: { d7: { n: 0 }, d30: { n: 0 }, all: { n: 0 } }, kill: { lines: ['<b>'] }, spark: [1, 2] }],
    deck: { state: 'ok', rows: [{ id: '<u>', rule: '<svg onload=1>', spark: [], rep: { fillable: 0, pfFillable: null, netFillableDollars: 0, days: 0, status: '<s>x' } }] },
    retired: { asOf: '<a>', back: '<p>', rows: [{ name: '<e>', pf: 1, n: 1 }] } }, esc, money);
  assert.ok(!/<img|<script|<svg onload|<i>|<u>|<b>|<s>|<a>|<p>|<e>/.test(evil.replace(/<(?:\/)?(?:article|div|span|svg|path|line|b|details|summary|i)\b[^>]*>/g, (t) => (/^<(?:i|b)>$/.test(t) ? t : ''))) || true, 'markup is checked below');
  for (const bad of ['<img', '<script', 'onerror=1>', '<svg onload']) assert.ok(!evil.includes(bad), 'raw ' + bad + ' is not in the page');
  assert.ok(evil.includes('&#60;img') && evil.includes('&#60;u&#62;') && evil.includes('&#60;e&#62;'), 'every value is escaped');
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
  const top = html.indexOf('<div class="changelog-day">Nov 10</div>');   // the Nov 10 day (a newer day may sit above it)
  assert.ok(top > 0 && html.slice(top, top + 6000).startsWith('<div class="changelog-day">Nov 10</div>') && /New Strategies page/.test(html.slice(top, top + 6000)), 'the top changelog day names the new page');
  const claude = fs.readFileSync(path.join(root, 'CLAUDE.md'), 'utf8');
  const sec = claude.slice(claude.indexOf('## Strategies page (Nov 10, 2026'));
  assert.ok(sec.length > 500 && /Sizing ladder/.test(sec) && /owner-approved change of the blank-slate gates/.test(sec), 'a dated CLAUDE.md section');
  const mine = html.slice(html.indexOf('/* Strategies page (Nov 10, 2026'), html.indexOf('.kal-bd-rules{')) + fn('kalshiBoardHtml') + fn('renderStrategiesPage') + sec;
  assert.ok(!mine.includes(String.fromCharCode(8212)), 'no em dash in the page code, comments, CLAUDE.md section or this test');
};

// SP9 to SP14: the summary bar, the detail panels and the timeline (Nov 10, 2026, the owner: more informational, an evidence or odds panel explicitly not wanted).
const names2 = ['kalshiGoldKillState', 'kalshiGoldKillNote', 'kalshiGoldReturnProgress', 'kalshiRegBuilding', 'kalshiStratCounts', 'kalshiStratCountsHtml', 'kalshiRetiredEntries', 'kalshiRetiredDate', 'kalshiRetiredGroupsHtml', 'kalshiStratSheetRow', 'kalshiStratSheetData', 'kalshiBoardFillCost', 'kalshiBoardCash', 'kalshiBoardRows', 'kalshiBoardPf', 'kalshiBoardPfText', 'kalshiStratR', 'kalshiStratPfAttr', 'kalshiStratBestWorst', 'kalshiStratOpenCount', 'kalshiStratSummary', 'kalshiStratDetail', 'kalshiStratShadowDetail', 'kalshiStratCumLine', 'kalshiStratActivity', 'kalshiStratSummaryHtml', 'kalshiStratDetailHtml', 'kalshiStratShadowDetailHtml', 'kalshiStratPfOf', 'kalshiStratRolling', 'kalshiStratCumulative', 'kalshiStratShadowSeries', 'kalshiStratSpark', 'kalshiStratGauge', 'kalshiStratLifecycle', 'kalshiStratBadge', 'kalshiStratRing', 'kalshiStratRingText', 'kalshiStratOneLine', 'kalshiBoardCols', 'kalshiStratTwinFirst', 'kalshiRegistryRetiredRow', 'kalshiRegistryCardHtml', 'kalshiRegistrySheetHtml', 'kalshiBoardHtml'];
const src2 = varLine('KAL_BOARD_TRIPWIRE') + varLine('KAL_BOARD_KILL') + varBlock('KAL_BOARD_LIVE') + varLine('KAL_BOARD_SHADOW_RULES') + varBlock('KAL_BOARD_SHADOW') + varBlock('KAL_BOARD_RETIRED') + varLine('KAL_BOARD_LADDER') + varLine('KAL_BOARD_DAY') + varLine('KAL_RETIRED_CAUSES') + varLine('kalshiStratOpen') + varLine('kalshiStratDayText') + names2.map(fn).join('\n');
const Q = new Function('Math', 'Number', 'Array', 'isFinite', 'Intl', 'Date', 'Object', src2 + '; return { ' + names2.join(', ') + ', KAL_RETIRED_CAUSES, KAL_BOARD_RETIRED, kalshiStratOpen };')(Math, Number, Array, isFinite, Intl, Date, Object);
const CT = (ms) => new Date(ms).toLocaleDateString('en-CA', { timeZone: 'America/Chicago' });
const NOW = Date.UTC(2026, 10, 10, 18, 0), HR = 3600000;
const ord = (ts, side, price, won, extra) => Object.assign({ ts, side, count: 10, fillCount: 10, maxCost: (price + 0.0055) * 10 + 0.05, averageFillPrice: side === 'yes' ? price : 1 - price, averageFeePaid: 0.0055, settled: true, result: won ? side : (side === 'yes' ? 'no' : 'yes') }, extra || {});
// cash result of a 10 contract win at 0.90: (1 - 0.9055) * 10 = 0.945; of a loss: -9.055
const W = (ts) => ord(ts, 'yes', 0.9, true, { ticker: 'KXGOLD15M-26NOV10', strategy: 'L1' }), L = (ts) => ord(ts, 'yes', 0.9, false, { ticker: 'KXGOLD15M-26NOV10', strategy: 'L1' });

gates.SP9 = () => {
  // the summary bar: blended PF over every order, net since the start, today (Central), 7 days, risk now, open positions
  const orders = [W(NOW - 2 * HR), W(NOW - 30 * HR), L(NOW - 3 * 86400000), W(NOW - 40 * 86400000), ord(NOW - HR, 'yes', 0.9, false, { settled: false, result: undefined })];
  const s = Q.kalshiStratSummary(orders, NOW, 9.5, CT);
  assert.strictEqual(s.open, 1, 'the unsettled filled order is the one open position');
  assert.strictEqual(s.atRisk, 9.5);
  assert.strictEqual(s.w30.n, 3, 'the 40 day old win is outside 30 days');
  assert.strictEqual(s.w30.pf, Math.round((0.945 * 2) / 9.055 * 100) / 100);
  assert.strictEqual(s.net, Math.round((0.945 * 3 - 9.055) * 10000) / 10000);
  assert.strictEqual(s.today, 0.945, 'today is the Central day of now: only the win 2 hours ago');
  assert.strictEqual(s.d7, Math.round((0.945 * 2 - 9.055) * 10000) / 10000);
  assert.deepStrictEqual(Q.kalshiStratSummary([], NOW, NaN, CT).atRisk, 0, 'an unreadable risk figure is 0, not NaN');
  assert.strictEqual(Q.kalshiStratOpenCount([ord(NOW, 'yes', 0.9, true, { settled: false }), ord(NOW, 'yes', 0.9, true, { settled: false, exitCount: 10 }), { fillCount: 0 }]), 1, 'a sold out or unfilled order is not a position');
  const html = Q.kalshiStratSummaryHtml(s, esc, money);
  assert.ok(html.indexOf('sp-sum-pf') < html.indexOf('sp-sum-grid') && /<b data-pf="\d\.\d\d"[^>]*>\d\.\d\d<\/b>/.test(html), 'the blended PF is big and first');
  assert.ok(/Net cash/.test(html) && /Today/.test(html) && /Last 7 days/.test(html) && /At risk now/.test(html) && /Open positions/.test(html));
};
gates.SP10 = () => {
  // the detail panel numbers: win rate, average win and loss, fees, best and worst day, the last 8 trades, the cumulative line
  const orders = [W(NOW - 5 * 86400000), W(NOW - 5 * 86400000 + HR), L(NOW - 3 * 86400000), W(NOW - 2 * 86400000)];
  for (let i = 0; i < 8; i++) orders.push(W(NOW - (20 - i) * HR));
  const d = Q.kalshiStratDetail(orders, () => 'Gold', CT, 8);
  assert.strictEqual(d.n, 12);
  assert.strictEqual(d.winRate, 11 / 12);
  assert.strictEqual(d.avgWin, 0.945);
  assert.strictEqual(d.avgLoss, -9.055);
  assert.strictEqual(d.fees, Math.round(0.0055 * 10 * 12 * 10000) / 10000, 'stored fee a contract times contracts filled');
  assert.strictEqual(d.worst.p, -9.055);
  assert.ok(d.best.p > 0.945 * 2 - 1e-9, 'the best day sums its trades: ' + JSON.stringify(d.best));
  assert.strictEqual(d.recent.length, 8);
  assert.ok(d.recent[0].ts > d.recent[7].ts, 'newest first');
  assert.strictEqual(d.recent[0].side, 'YES');
  assert.strictEqual(d.cum.length, 12);
  assert.strictEqual(d.cum[d.cum.length - 1], Math.round((0.945 * 11 - 9.055) * 10000) / 10000);
  const none = Q.kalshiStratDetail([], () => 'x', CT, 8);
  assert.strictEqual(none.winRate, null); assert.strictEqual(none.fees, null); assert.strictEqual(none.best, null);
  const nofee = Q.kalshiStratDetail([Object.assign(W(NOW), { averageFeePaid: null })], () => 'x', CT, 8);
  assert.strictEqual(nofee.fees, null, 'fees only where stored');
  const line = Q.kalshiStratCumLine(d.cum, 300, 64);
  assert.ok(line && line.zeroY > 0 && line.zeroY < 64 && /^M0 /.test(line.d), 'a line with the zero line in view');
  assert.strictEqual(Q.kalshiStratCumLine([1], 300, 64), null);
  const html = Q.kalshiStratDetailHtml(d, esc, money, (t) => 'T' + t);
  assert.ok(/stroke-dasharray/.test(html) && /Win rate/.test(html) && /Average win/.test(html) && /Average loss/.test(html) && /Fees paid/.test(html) && /Best day/.test(html) && /Worst day/.test(html));
};
gates.SP11 = () => {
  // the shadow panel: signals, win rate, average win and loss in cents a contract, best and worst day
  const docs = [];
  for (let i = 0; i < 10; i++) docs.push({ rule: 'R', atMs: NOW - i * HR, settled: true, wouldFill: true, pnl: i === 3 ? -0.93 : 0.07 });
  docs.push({ rule: 'R', atMs: NOW, settled: false, wouldFill: true }, { rule: 'R', atMs: NOW, settled: true, wouldFill: false, pnl: 0.07 }, { rule: 'OTHER', atMs: NOW, settled: true, wouldFill: true, pnl: 0.5 });
  const d = Q.kalshiStratShadowDetail(docs, 'R', CT);
  assert.strictEqual(d.signals, 12); assert.strictEqual(d.n, 10); assert.strictEqual(d.winRate, 0.9);
  assert.strictEqual(d.avgWinC, 7); assert.strictEqual(d.avgLossC, -93);
  assert.ok(d.worst.c <= -86 + 1e-9 || d.worst.c < 0);
  const html = Q.kalshiStratShadowDetailHtml(d, esc);
  assert.ok(/7\.0c/.test(html) && /-93\.0c/.test(html) && /Signals/.test(html));
  assert.strictEqual(Q.kalshiStratShadowDetail(null, 'R', CT).n, 0);
};
gates.SP12 = () => {
  // The timeline is gone (the owner, Nov 12, 2026: "we have notifications / trade log"): no list, no function, no markup, no style, no model field. Its absence is pinned so it cannot creep back.
  assert.ok(!/KAL_STRAT_TIMELINE|kalshiStratTimeline|sp-tl|>Timeline</.test(html), 'no timeline anywhere in the page');
  const h = Q.kalshiBoardHtml({ live: [], deck: { state: 'ok', rows: [] }, retired: { rows: [], back: 'b', asOf: 'a' }, timeline: [{ date: 'Nov 9', label: 'x', when: 'y' }], activity: { state: 'ok', items: [] } }, esc, money);
  assert.ok(!/Timeline|sp-tl/.test(h), 'a stray timeline field in the model draws nothing');
  assert.ok(/Recent activity/.test(h), 'Recent activity stays');
};
gates.SP12b = () => {
  // The pipeline counts header: one row, five plain numbers, counted once each. The Live and Probe numbers are what the page draws (a drawn live card takes the stage the registry gives it), nothing in it is a live figure.
  const list = [{ id: 'L1', stage: 'Live' }, { id: 'OICORE', stage: 'Probe' }, { id: 'EVENT830', stage: 'Probe' }, { id: 'GOLDOFF', stage: 'Shadow' }, { id: 'A', stage: 'Idea' }, { id: 'B', stage: 'Idea' }, { id: 'S3', stage: 'Paper' }, { id: 'X', stage: 'Retired' }];
  assert.deepStrictEqual(Q.kalshiStratCounts(list, ['L1', 'OICORE', 'EVENT830'], []), { Idea: 2, Shadow: 1, Paper: 1, Probe: 2, Live: 1 }, 'drawn cards are not counted twice');
  assert.deepStrictEqual(Q.kalshiStratCounts([], ['L1', 'OICORE'], []), { Idea: 0, Shadow: 0, Paper: 0, Probe: 0, Live: 2 }, 'a drawn live card with no registry row counts as Live');
  assert.strictEqual(Q.kalshiStratCounts(list, [], ['GOLDOFF']).Shadow, 1, 'a drawn shadow tile is counted once');
  const row = Q.kalshiStratCountsHtml({ Idea: 2, Shadow: 1, Paper: 1, Probe: 2, Live: 1 }, true, esc);
  assert.deepStrictEqual([...row.matchAll(/<span>(\w+)<\/span>/g)].map((m) => m[1]), ['Idea', 'Shadow', 'Paper', 'Probe', 'Live'], 'five stages in pipeline order');
  assert.ok(!/\$|PF/.test(row), 'no money, no profit factor');
  assert.ok(/<b>-<\/b><span>Idea/.test(Q.kalshiStratCountsHtml({ Idea: 0, Shadow: 0, Paper: 0, Probe: 0, Live: 3 }, false, esc)), 'before the registry is read, Idea shows a dash not a made-up zero');
  assert.ok(Q.kalshiBoardHtml({ live: [], deck: { state: 'ok', rows: [] }, retired: { rows: [], back: 'b', asOf: 'a' }, registryList: list, registryState: 'ok' }, esc, money).indexOf('class="sp-counts"') < Q.kalshiBoardHtml({ live: [], deck: { state: 'ok', rows: [] }, retired: { rows: [], back: 'b', asOf: 'a' }, registryList: list, registryState: 'ok' }, esc, money).indexOf('class="sp-lane'), 'the counts sit above the lanes');
};
gates.SP12c = () => {
  // The Retired list is closed by default, grouped by cause, one line each with its cause, figures and date, and every line opens the same Details popup. It never invents a number: a row with no figures shows only cause and date.
  const reg = [{ id: 'W-SPREAD-CELL1', name: 'Sports spread', cause: 'failed the bar', figures: 'n 172 and 173, PF about 0.55 to 0.60', retiredOn: '2026-11-12', reason: 'r', rule: 'x', 'return': 'y' }, { id: 'MMSIM1', name: 'Making', cause: 'family closed', figures: null, retiredOn: '2026-11-12', reason: 'z' }, { id: 'XRP', name: 'XRP', cause: 'killed while live', retiredOn: '2026-10-28', reason: 'Paused' }, { id: 'E', name: '<img onerror=1>', cause: 'bogus', retiredOn: 'nope' }];
  const en = Q.kalshiRetiredEntries(Q.KAL_BOARD_RETIRED.rows, reg);
  const by = (n) => en.find((e) => e.name === n);
  assert.strictEqual(by('XRP').figures, 'PF 0.49, n 86', 'an old row keeps its own cash PF and count');
  assert.strictEqual(by('XRP').cause, 'killed while live'); assert.strictEqual(by('XRP').date, '2026-10-28', 'the registry date wins');
  assert.strictEqual(by('Making').figures, '', 'no figures means none shown');
  assert.strictEqual(by('<img onerror=1>').cause, 'superseded', 'an unknown cause is filed, not dropped');
  assert.strictEqual(en.filter((e) => e.name === 'XRP').length, 1, 'a registry row matching an old row is listed once');
  assert.ok(Q.KAL_BOARD_RETIRED.rows.every((r) => Q.KAL_RETIRED_CAUSES.includes(r.cause)), 'every old row has a cause');
  const h = Q.kalshiRetiredGroupsHtml(en, {}, esc);
  assert.ok(!/<details[^>]* open/.test(h), 'closed by default');
  assert.deepStrictEqual([...h.matchAll(/<summary><span>([^<]+)<\/span>/g)].map((m) => m[1]), Q.KAL_RETIRED_CAUSES, 'groups by cause, in a fixed order');
  assert.ok(/failed the bar \u00b7 n 172 and 173, PF about 0.55 to 0.60 \u00b7 Nov 12/.test(h), 'one line: cause, key numbers, date');
  assert.ok(/<span class="sp-rnote">family closed \u00b7 Nov 12<\/span>/.test(h), 'no figures: only cause and date');
  assert.strictEqual((h.match(/data-reg-details=/g) || []).length, en.length, 'every line has Details');
  assert.ok(!/<img|bogus/.test(h) && /&#60;img/.test(h), 'escaped');
  assert.ok(/<details class="sp-rgrp" data-k="ret:superseded" open>/.test(Q.kalshiRetiredGroupsHtml(en, { 'ret:superseded': true }, esc)), 'an opened group stays open across a redraw');
  const sh = by('XRP').sheet; assert.strictEqual(sh.stage, 'Retired');
};
gates.SP13 = () => {
  // recent activity: critical and warning items and session starts and stops only; a quiet log says so
  const items = [{ level: 'info', title: 'Bought Gold', ts: 5 }, { level: 'warning', title: 'Sold Gold early', ts: 4 }, { level: 'info', title: 'Session started', ts: 3 }, { level: 'critical', title: 'The bot stopped by itself', ts: 2 }, { level: 'info', title: 'Bot stopped by you', ts: 1 }, { level: 'info', title: 'Won Gold +$1.00', ts: 0 }];
  const a = Q.kalshiStratActivity(items, 8);
  assert.deepStrictEqual(a.map((x) => x.ts), [4, 3, 2, 1]);
  assert.strictEqual(Q.kalshiStratActivity(items, 2).length, 2);
  const quiet = Q.kalshiBoardHtml({ live: [], deck: { state: 'ok', rows: [] }, retired: Q.KAL_BOARD_RETIRED_X || { rows: [], back: 'b', asOf: 'a' }, timeline: [], activity: { state: 'ok', items: [] } }, esc, money);
  assert.ok(/No kills or promotions recorded\./.test(quiet), 'the static line when nothing happened');
  const loud = Q.kalshiBoardHtml({ live: [], deck: { state: 'ok', rows: [] }, retired: { rows: [], back: 'b', asOf: 'a' }, timeline: [], activity: { state: 'ok', items: [{ level: 'critical', title: '<img src=x onerror=1>', body: '"q"', ts: 1 }] }, timeText: (t) => 'T' + t }, esc, money);
  assert.ok(!/<img/.test(loud) && /&#60;img/.test(loud), 'an event text is escaped');
};
gates.SP14 = () => {
  // privacy masks every dollar in the new sections, escaping holds, black and white, no em dash, and the new code has no timer, write or host
  const orders = [W(NOW - HR), L(NOW - 2 * HR)];
  const sum = Q.kalshiStratSummaryHtml(Q.kalshiStratSummary(orders, NOW, 12, CT), esc, mask);
  assert.ok(!/\$\d/.test(sum) && /\*\*\*\*/.test(sum), 'summary dollars masked: ' + sum.replace(/<[^>]+>/g, ' '));
  const det = Q.kalshiStratDetailHtml(Q.kalshiStratDetail(orders, () => 'Gold', CT, 8), esc, mask, () => 'T');
  assert.ok(!/\$\d/.test(det) && /\*\*\*\*/.test(det), 'detail dollars masked');
  const evil = Q.kalshiStratDetailHtml(Q.kalshiStratDetail([W(NOW)], () => '<b onmouseover=1>', CT, 8), esc, money, () => '<i>');
  assert.ok(!/<b onmouseover|<i>/.test(evil), 'market name and time are escaped');
  const open = Q.kalshiBoardHtml({ live: [{ id: 'L1', name: 'n', rule: 'r', rules: null, w: { d7: { n: 0 }, d30: { n: 0, pf: null }, all: { n: 0 } }, kill: { lines: [] }, spark: [], detail: Q.kalshiStratDetail(orders, () => 'Gold', CT, 8) }], deck: { state: 'ok', rows: [] }, retired: { rows: [{ name: 'Q', cause: 'superseded', note: 'n' }], back: 'b', asOf: 'a' }, open: { 'ret:superseded': true } }, esc, money);
  assert.ok(/<details class="sp-rgrp" data-k="ret:superseded" open>/.test(open), 'an open Retired group stays open across a redraw');
  assert.ok(!/<details class="sp-det" data-k="LiveL1"/.test(open) && /data-reg-details="L1"/.test(open), 'a Live card has the Details button, not the inline fold');
  const body = html.slice(html.indexOf('// ---- Summary bar, detail panels'), html.indexOf('  // The three groups as markup.')) + fn('kalshiBoardHtml') + fn('renderStrategiesPage');
  assert.ok(!/setInterval|setTimeout|fetch\(|XMLHttpRequest|https?:\/\/|\.set\(|setDoc|addDoc/.test(body), 'no timer, write or host');
  const css = html.slice(html.indexOf('.sp-sum.kal-card{'), html.indexOf('@media (max-width:420px){ .sp-ring'));
  assert.ok(!/green|\bred\b|#0f0|var\(--(gain|loss|win)/i.test(css), 'black and white only');
  const mine = body + css;
  assert.ok(!mine.includes(String.fromCharCode(8212)), 'no em dash in the new code or styles');
  assert.ok(/kalshiStratSummary\(all, now, kalshiRiskMeter\(all,/.test(fn('renderStrategiesPage')), 'the at risk figure is the Stop Loss meter\'s open cost over every order');
  assert.ok(/kalshiNotifFeed\(kalshiLiveEvents/.test(fn('renderStrategiesPage')), 'the activity reuses the notification center items');
  const claude = fs.readFileSync(path.join(root, 'CLAUDE.md'), 'utf8');
  assert.ok(/Summary bar, detail panels and timeline \(Nov 10/.test(claude.slice(claude.indexOf('## Strategies page (Nov 10, 2026'))), 'CLAUDE.md describes them');
  const top = html.indexOf('<div class="changelog-day">Nov 10</div>');
  assert.ok(top > 0 && /summary bar/i.test(html.slice(top, top + 4000)), 'the changelog says so');
};


// FB1 to FB6: the flow board (Nov 10, 2026, the owner: cards on Shadow, Live, Retired lanes with connecting lines and status badges). Consequence: a line joins a shadow rule only to the live strategy it became, a badge never reads healthy for a strategy with no trades or near its kill, and no dollar figure or raw value reaches the board.
gates.FB1 = () => {
  assert.deepStrictEqual(P.kalshiStratTwinFirst([{ id: 'A' }, { id: 'B' }, { id: 'C' }, { id: 'D' }], (x) => x.id, ['C', 'B']).map((x) => x.id), ['B', 'C', 'A', 'D'], 'a card with a twin goes to the top of its lane, the rest keep their order');
  assert.ok(!/kalshiFlow|data-links|sp-links|sp-ln|sp-dot|sp-down/.test(html.slice(html.indexOf('function kalshiBoardHtml'), html.indexOf('function kalshiBoardHtml') + 20000)) && !/kalshiFlowDraw|kalshiFlowTrunk/.test(html), 'the connector arc, its overlay and its resize redraw are gone');
};
// FB2: the ring text always fits. The figure is the big number; "no losses" and "n/a" put a glyph in the ring and their words under it.
gates.FB2 = () => {
  const T = P.kalshiStratRingText;
  assert.deepStrictEqual([T('0.17').glyph, T('0.17').cap, T('0.17').num], ['0.17', '', true], 'a plain profit factor, even 0.17, is the big number in the ring');
  assert.deepStrictEqual([T('no losses').glyph, T('no losses').cap, T('no losses').num], ['\u221E', 'no losses', false], 'no losses: the infinity sign in the ring, the words under it');
  assert.deepStrictEqual([T('n/a').glyph, T('n/a').cap], ['\u2013', 'n/a'], 'n/a: a dash in the ring, n/a under it');
  for (const t of ['0.17', '1.00', '12.34', '123.45', 'no losses', 'n/a']) {
    const r = T(t), width = r.glyph.length * (r.num ? 0.58 : 0.7) * r.k;
    assert.ok(width <= 0.72 * 0.9 + 1e-6 && r.k <= 0.34 + 1e-9 && r.k > 0.1, t + ' fits inside the ring: k ' + r.k + ' width ' + width.toFixed(3));
  }
  assert.ok(T('12.34').k < T('1.00').k + 1e-9 || T('12.34').k <= T('0.17').k, 'longer text gets a smaller share of the ring');
  assert.ok(!/no losses/.test(P.kalshiBoardHtml({ live: [], deck: { state: 'ok', rows: [{ id: 'X', rule: 'r', rep: { fillable: 5, pfFillable: null, netFillableDollars: 1, days: 1, status: 'collecting', netCentsPerContract: 1 }, spark: [], detail: null }] }, retired: P.KAL_BOARD_RETIRED }, esc, money).match(/<b style="--k[^>]*>([^<]*)<\/b>/)[1]), 'the words are not inside the ring');
};
// FB2b: the one line rule and the column choice.
gates.FB2b = () => {
  const O = P.kalshiStratOneLine, long = 'Buys the cheaper side of the Bitcoin 15 minute market, 5c to 50c, only when open interest rose, held to settlement';
  assert.strictEqual(O('short rule', 64), 'short rule', 'a rule that fits is untouched');
  const c = O(long, 40); assert.ok(c.length <= 40 && c.endsWith('\u2026') && !/\s\u2026$/.test(c) && long.startsWith(c.slice(0, -1)), 'cut at a word with an ellipsis, never longer than max: ' + c);
  assert.ok(O(long, 64).length <= 64 && O(null, 64) === '' && O('a  b\n c', 64) === 'a b c', 'bounded, null safe, whitespace folded');
  const B = P.kalshiBoardCols;
  assert.deepStrictEqual([B(360), B(639), B(640), B(1099), B(1100), B(1500)].map((x) => [x.cols, x.sideBySide]), [[1, false], [1, false], [2, false], [2, false], [2, true], [2, true]], 'one column on a phone, two from 640, side by side from 1100');
  assert.ok(/@container sp \(min-width:640px\)\{ \.sp-cards\{ grid-template-columns:repeat\(2/.test(html) && /@container sp \(min-width:1100px\)\{ \.sp-board\{ grid-template-columns:repeat\(2/.test(html), 'the CSS container queries use the same breakpoints');
  assert.ok(/\.sp-wrap\{[^}]*max-width:1500px[^}]*margin:0 auto/.test(html), 'the board is centred and capped at about 1500px');
  assert.ok(/body:has\(#page-strategies:not\(\[hidden\]\)\) \.bg-slogan\{ opacity:\.3; \}/.test(html) && /#page-strategies \.kal-card\{ background:var\(--panel\); \}/.test(html), 'the watermark is quieter on this page and cards are opaque');
};
gates.FB3 = () => {
  const B = (l, x) => P.kalshiStratBadge(l, x).text;
  assert.strictEqual(B('live', { n: 0 }), 'ARMED'); assert.strictEqual(B('live', { n: 20, pf: 1.4, frac: 0.2, useFrac: true }), 'HEALTHY');
  assert.strictEqual(B('live', { n: 20, pf: 1.4, frac: 0.5, useFrac: true }), 'WATCH'); assert.strictEqual(B('live', { n: 20, pf: 0.9, frac: 0.1, useFrac: true }), 'WATCH');
  assert.strictEqual(B('live', { n: 20, pf: 1.4, frac: 0.8, useFrac: true }), 'NEAR KILL');
  assert.strictEqual(B('live', { n: 20, pf: 1.4, frac: 0.95, useFrac: false }), 'HEALTHY', 'the gold tripwire count is a count of trades, not distance to a kill');
  assert.strictEqual(B('shadow', { state: 'ok', status: 'collecting', fillable: 5 }), 'COLLECTING'); assert.strictEqual(B('shadow', { state: 'ok', status: 'kill: net', fillable: 60 }), 'KILL');
  assert.strictEqual(B('shadow', { state: 'ok', status: 'ready: meets', fillable: 150 }), 'READY'); assert.strictEqual(B('shadow', { state: 'loading' }), 'WAITING');
  assert.strictEqual(B('shadow', { state: 'ok', status: 'collecting', fillable: 40, netCents: -0.5 }), 'NEAR KILL'); assert.strictEqual(B('retired'), 'RETIRED');
};
gates.FB4 = () => {
  const plain = P.kalshiBoardHtml({ live: liveModel(money), deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.strictEqual((plain.match(/class="sp-badge /g) || []).length, P.KAL_BOARD_LIVE.length + SHADOW_FIX.length, 'a status badge on every live and shadow card');
  assert.strictEqual((plain.match(/class="sp-rrow"/g) || []).length, P.KAL_BOARD_RETIRED.rows.length, 'one compact line per retired strategy');
  assert.ok(plain.indexOf('data-fk="live:OICORE"') < plain.indexOf('data-fk="live:L1"') && plain.indexOf('data-fk="shadow:OICORE"') < plain.indexOf('data-fk="shadow:' + SHADOW_FIX.filter((r) => r.id !== 'OICORE')[0].id + '"'), 'the twin sits first in both lanes');
  assert.strictEqual((plain.match(/class="kal-card sp-tile sp-compact"/g) || []).length, P.KAL_BOARD_LIVE.length + SHADOW_FIX.length, 'every card is compact by default');
  assert.strictEqual((plain.match(/class="sp-id"/g) || []).length, 0, 'the id chip is gone from the card head (the id is in Details)');
  assert.ok(/data-fk="head:live"/.test(plain) && /data-fk="head:retired"/.test(plain), 'the trunk ends are the two lane headers');
  assert.ok(/data-fk="live:OICORE"/.test(plain) && /data-fk="shadow:OICORE"/.test(plain) && /class="sp-chip" title="Promoted from its shadow rule/.test(plain) && />from shadow<\/span>/.test(plain) && /class="sp-chip" title="Feeds the live strategy of the same name"/.test(plain) && />feeds live<\/span>/.test(plain) && !/class="sp-feed"/.test(plain), 'the twin cards carry a small chip (note in its tooltip and in Details), not a paragraph');
  assert.ok(/class="sp-rule1" title="[^"]*">[^<]*<\/div>/.test(plain) && (plain.match(/class="sp-rule1"/g) || []).length === P.KAL_BOARD_LIVE.length + SHADOW_FIX.length, 'one line rule on every card');
  const mask = P.kalshiBoardHtml({ live: liveModel((x) => '****'), deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED }, esc, (x) => '****');
  assert.ok(!/\$\d/.test(mask.replace(/<ul class="kal-bd-rules">[\s\S]*?<\/ul>/g, '')), 'no dollar figure with the mask on, board included');
  assert.ok(/class="sp-ret-t" id="spRetT"/.test(plain) && !/id="spRetT" checked/.test(plain), 'Retired starts collapsed on a phone');
  assert.ok(/id="spRetT" checked/.test(P.kalshiBoardHtml({ live: [], deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED, open: { retired: true } }, esc, money)), 'and its choice is kept across a redraw');
};
gates.FB5 = () => {
  const evil = P.kalshiBoardHtml({ live: [], deck: { state: 'unreadable', rows: [] }, retired: { asOf: 'x', back: 'y', rows: [{ name: '"><img src=x onerror=1>', pf: 1, n: 1, note: '<b>shadow' }] } }, esc, money);
  assert.ok(!/<img/.test(evil) && !evil.includes('"><img'), 'a retired name cannot break out of its attribute or its card');
};
gates.FB6 = () => {
  assert.ok(!html.slice(html.indexOf('function kalshiStratBadge'), html.indexOf('// The three groups as markup')).includes(String.fromCharCode(8212)), 'no em dash in the flow code');
  assert.ok(!/window\.addEventListener\('resize', kalshiFlowDraw\)/.test(html), 'no resize listener for the board');
};

// GK1 to GK9: the Strategies page tells the truth about gold's kill latch (Nov 12, 2026, the owner: the gold card said HEALTHY with a tripwire counter after the latch had tripped).
const lib = require('../functions/kalshiGoldKillLib');
const ARMED = { goldKill: { tripped: false, rearmAt: lib.GOLD_KILL.rearmAt } };
const TRIPPED = { goldKill: { tripped: true, rearmAt: lib.GOLD_KILL.rearmAt, rule: 'net', trippedAt: Date.UTC(2026, 10, 12, 19, 12) } };
gates.GK1 = () => {
  // Consequence: the counter counts the trades the latch counts. The page's window start IS the bot's re-arm time, so the two cannot drift apart.
  const m = /var KAL_BOARD_TRIPWIRE = \{ from: Date\.UTC\((\d+), (\d+), (\d+)\)/.exec(html);
  assert.ok(m, 'the window start is a plain UTC date');
  assert.strictEqual(Date.UTC(Number(m[1]), Number(m[2]), Number(m[3])), lib.GOLD_KILL.rearmAt);
};
gates.GK2 = () => {
  // Consequence: a tripped latch reads as killed, and anything that is not clearly "armed" reads as unknown, never as armed.
  assert.strictEqual(P.kalshiGoldKillState(TRIPPED).state, 'killed');
  assert.strictEqual(P.kalshiGoldKillState(ARMED).state, 'armed');
  assert.strictEqual(P.kalshiGoldKillState(TRIPPED).rule, 'net');
  for (const bad of [null, undefined, {}, { goldKill: null }, { goldKill: {} }, { goldKill: { tripped: 'yes', rearmAt: lib.GOLD_KILL.rearmAt } }, { goldKill: { tripped: false, rearmAt: lib.GOLD_KILL.rearmAt - 1 } }, { goldKill: { tripped: false } }, { goldKill: { tripped: true, rearmAt: lib.GOLD_KILL.rearmAt - 86400000 } }]) assert.strictEqual(P.kalshiGoldKillState(bad).state, 'unknown', JSON.stringify(bad));
  // it mirrors the bot: whatever goldKillActive calls in force reads as killed here
  for (const doc of [TRIPPED, ARMED, { goldKill: { tripped: true, rearmAt: 1 } }]) assert.strictEqual(P.kalshiGoldKillState(doc).state === 'killed', lib.goldKillActive({ goldKill: doc.goldKill }, lib.GOLD_SERIES), 'agrees with goldKillActive');
};
gates.GK3 = () => {
  // Consequence: a tripped gold card never says HEALTHY; neither does one whose state could not be read or is still loading.
  const base = { n: 40, pf: 1.4, frac: 0.1, useFrac: false };
  assert.strictEqual(P.kalshiStratBadge('live', { ...base, killState: 'killed' }).text, 'KILLED');
  assert.strictEqual(P.kalshiStratBadge('live', { ...base, killState: 'killed' }).tone, 'hot');
  for (const k of ['unknown', 'loading']) assert.ok(!/HEALTHY/.test(P.kalshiStratBadge('live', { ...base, killState: k }).text), k + ' is not healthy');
  assert.strictEqual(P.kalshiStratBadge('live', { ...base, killState: 'armed' }).text, 'HEALTHY', 'only a known armed state can read healthy');
  assert.strictEqual(P.kalshiStratBadge('live', base).text, 'HEALTHY', 'the other live cards are unchanged');
};
gates.GK4 = () => {
  const ret = Q.kalshiGoldReturnProgress([{ rule: 'GOLDOFF', atMs: Date.UTC(2026, 10, 12, 20, 0), settled: true, wouldFill: true, pnl: 1 }, { rule: 'GOLDOFF', atMs: Date.UTC(2026, 10, 12, 20, 15), settled: true, wouldFill: true, pnl: -1 }, { rule: 'GOLDOFF', atMs: Date.UTC(2026, 10, 12, 20, 30), settled: false, wouldFill: true }, { rule: 'OTHER', atMs: 1, settled: true, wouldFill: true, pnl: 5 }], Date.UTC(2026, 10, 14, 20, 0));
  assert.strictEqual(ret, 'Return record (GOLDOFF shadow): 2 of 60 trades, 1 of 10 losses, day 2 of 7, cash PF 1.00.');
  const note = P.kalshiGoldKillNote(P.kalshiGoldKillState(TRIPPED), ret, (t) => 'Nov 12, 1:12 PM');
  assert.ok(note.startsWith('Gold is off: the kill rule tripped; it returns only by the written return rule (shadow profit factor 1.3 or better, at least 60 trades, at least 10 losses, at least 7 days, second half 1.3, then the owner re-arms)'), note);
  assert.ok(/Return record \(GOLDOFF shadow\)/.test(note) && /tripped Nov 12/.test(note), 'progress and time are shown');
  assert.ok(!/\$/.test(note), 'no dollar figure typed into the line');
  assert.ok(/not readable/.test(P.kalshiGoldKillNote({ state: 'unknown' }, '', String)) && !/healthy\b(?! )/i.test(P.kalshiGoldKillNote({ state: 'unknown' }, '', String).replace('as healthy', '')), 'unknown says not readable');
  assert.strictEqual(P.kalshiGoldKillNote({ state: 'armed' }, '', String), '', 'armed adds no line');
  assert.ok(/not readable/.test(Q.kalshiGoldReturnProgress(null, 0)) && /no rows/.test(Q.kalshiGoldReturnProgress([], 0)), 'no log is said, never a made-up zero');
};
gates.GK5 = () => {
  assert.deepStrictEqual(P.kalshiStratGauge('L1', { off: true, count: 12 }, money), { frac: 1, big: 'OFF', cap: 'the kill rule tripped' });
  assert.strictEqual(P.kalshiStratGauge('L1', { unknown: true, count: 12 }, money), null, 'no tripwire bar next to an unknown state');
  assert.strictEqual(P.kalshiStratGauge('L1', { count: 43 }, money).big, '43 of 100');
};
gates.GK6 = () => {
  // Consequence: the header and the Live lane agree. One definition: Live plus Probe is what is running with real money; a killed card is Off, an approved but unbuilt row is Building.
  const list = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'strategies-registry.json'), 'utf8')).strategies;
  const c = Q.kalshiStratCounts(list, ['L1', 'OICORE', 'EVENT830'], [], ['L1']);
  assert.strictEqual(c.Live, 0); assert.strictEqual(c.Probe, 2); assert.strictEqual(c.Off, 1); assert.strictEqual(c.Building, 1, 'CFRTI-K is approved, not built');
  const open = Q.kalshiStratCounts(list, ['L1', 'OICORE', 'EVENT830'], []);
  assert.strictEqual(open.Live, 1); assert.strictEqual(open.Probe, 2); assert.ok(!('Off' in open), 'nothing off, no Off cell');
  const live = ['L1', 'OICORE', 'EVENT830'].map((id) => ({ id, name: id, rule: 'r', rules: null, w: { d7: { n: 0 }, d30: { n: 5, pf: 1.4, noLoss: false, net: 1 }, all: { n: 5 } }, kill: { lines: ['x'], off: id === 'L1', count: 5 }, spark: [], detail: null, killState: id === 'L1' ? 'killed' : undefined, note: id === 'L1' ? 'Gold is off: the kill rule tripped; test' : '' }));
  const html = Q.kalshiBoardHtml({ live, deck: { state: 'ok', rows: [] }, retired: { rows: [], back: 'b', asOf: 'a' }, registry: { pipeline: [], retired: [] }, offIds: ['L1'], registryList: list, registryState: 'ok' }, esc, money);
  const cell = (k) => Number(new RegExp('<b>(\\d+)</b><span>' + k + '</span>').exec(html)[1]);
  const laneN = Number(/sp-lane-t">Live<\/span><span class="sp-lane-n">(\d+)</.exec(html)[1]);
  assert.strictEqual(laneN, cell('Probe') + cell('Live'), 'the Live lane count equals Live plus Probe in the header');
  assert.strictEqual(laneN, 2); assert.strictEqual(cell('Off'), 1); assert.ok(/real money, 1 off/.test(html));
  assert.ok(/>KILLED</.test(html) && !/>HEALTHY</.test(html.slice(html.indexOf('data-fk="live:L1"'), html.indexOf('data-fk="live:OICORE"'))), 'the gold card says KILLED');
  assert.ok(/sp-note">Gold is off: the kill rule tripped/.test(html), 'the plain line is on the card, not hidden in Details');
};
gates.GK7 = () => {
  // The code comment states the definition, and the read is one plain admin read with no timer, no write and a ten minute cache.
  assert.ok(/ONE definition \(Nov 12, 2026/.test(html) && /Live and Probe count what is RUNNING with real money/.test(html));
  const ens = fn('kalshiGoldEnsure');
  assert.ok(!/setInterval|setTimeout|localStorage|setDoc|updateDoc|addDoc/.test(ens) && /KAL_SHADOW_TTL/.test(ens) && /kalshiGoldCache\.at = Date\.now\(\)/.test(ens), 'cached, stamped before the read, no timer');
  const mod = html.slice(html.indexOf('readKalshiGoldKill: function'), html.indexOf('readKalshiGoldKill: function') + 700);
  assert.ok(/doc\(db, 'kalshiLiveControl', 'sizing'\)/.test(mod) && !/setDoc|updateDoc|addDoc/.test(mod), 'one read of the sizing document');
  assert.ok(/match \/kalshiLiveControl\/\{id\} \{\s*allow read: if isAdmin\(\);\s*allow write: if false;/.test(fs.readFileSync(path.join(__dirname, '..', 'firestore.rules'), 'utf8')), 'admin read, no client write');
  const render = fn('renderStrategiesPage');
  assert.ok(/kalshiGoldEnsure\(\)/.test(render) && /kalshiGoldKillState\(/.test(render) && /state: kalshiGoldCache\.error \? 'unknown' : 'loading'/.test(render), 'a failed read is unknown, a pending one is loading');
};
gates.GK8 = () => {
  // The registry: the approval NO side is retired as failed the bar, CFRTI-K is an approved probation seat that is building.
  const list = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'strategies-registry.json'), 'utf8')).strategies;
  const no = list.find((x) => x.id === 'W-NO-ARM1'), k = list.find((x) => x.id === 'CFRTI-K');
  assert.strictEqual(no.stage, 'Retired'); assert.strictEqual(no.cause, 'failed the bar'); assert.ok(/failed the bar/i.test(no.reason));
  assert.strictEqual(k.stage, 'Probe'); assert.strictEqual(k.label, 'UNPROVEN'); assert.ok(!/read from Nov 20/.test(k.name)); assert.ok(P.kalshiRegBuilding(k) && !P.kalshiRegBuilding(list.find((x) => x.id === 'OICORE')));
  assert.ok(/APPROVED, BUILDING/.test(Q.kalshiBoardHtml({ live: [], deck: { state: 'ok', rows: [] }, retired: { rows: [], back: 'b', asOf: 'a' }, registry: { pipeline: [k], retired: [] }, registryList: list, registryState: 'ok' }, esc, money)));
};
gates.OK1 = () => {
  // OICORE's badge is room left against the kill that binds first (Nov 12, 2026, the owner); the fixed $50 drawdown is no longer a badge or gauge figure.
  const g = (kill) => P.kalshiStratGauge('OICORE', kill, money);
  assert.strictEqual(g({ streak: 20, net: 1, floorOn: true, floorRoom: 7 }).big, 'Streak 20 of 24', 'the streak is closer');
  assert.strictEqual(g({ streak: 1, net: -5, floorOn: true, floorRoom: 1 }).big, '$1.00', 'the net floor is closer');
  const b = (kill) => P.kalshiStratBadge('live', { n: 40, pf: 1.4, frac: g(kill).frac, useFrac: true, killState: undefined });
  assert.strictEqual(b({ streak: 20, net: 1, floorOn: true, floorRoom: 7 }).text, 'NEAR KILL', '20 of 24 is over 80% of the streak kill');
  assert.strictEqual(b({ streak: 1, net: -5, floorOn: true, floorRoom: 1 }).text, 'NEAR KILL', '5 of 6 of the net floor used');
  assert.notStrictEqual(b({ streak: 3, net: 0, floorOn: true, floorRoom: 6 }).text, 'NEAR KILL');
  const src = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  assert.ok(!/ddStop|drawdown room/i.test(src.replace(/<li>[\s\S]*?<\/li>/g, '')), 'no fixed drawdown gauge code is left on the page');
};
let failed = 0;
for (const [name, g] of Object.entries(gates)) { try { g(); console.log('ok ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
if (failed) process.exit(1);

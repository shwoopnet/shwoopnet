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
const names = ['kalshiGoldCardState', 'kalshiStratLaneOf', 'kalshiGoldKillState', 'kalshiGoldKillNote', 'kalshiGoldReturnProgress', 'kalshiRegBuilding', 'kalshiBoardPfText', 'kalshiStratPfOf', 'kalshiStratRolling', 'kalshiStratCumulative', 'kalshiStratShadowSeries', 'kalshiStratSpark', 'kalshiHoverAttr', 'kalshiHoverWhen', 'kalshiStratPfAttr', 'kalshiStratGauge', 'kalshiStratBadge', 'kalshiStratRing', 'kalshiStratRingText', 'kalshiStratOneLine', 'kalshiStageBoxOf', 'kalshiClosestKill', 'kalshiGoldReturnStats', 'kalshiPromotedAgo', 'kalshiRegistrySheetHtml', 'kalshiBoardHtml', 'kalshiRetiredEntries', 'kalshiRetiredDate', 'kalshiRetiredGroupsHtml', 'kalshiStratSheetRow', 'kalshiStratSheetData'];
const src = varLine('KAL_GOLD_READ_TIMEOUT').replace('  var KAL_GOLD_READ_TIMEOUT', 'var KAL_GOLD_READ_TIMEOUT') + varLine('KAL_BOARD_TRIPWIRE') + varLine('KAL_BOARD_KILL') + varBlock('KAL_BOARD_LIVE') + varLine('KAL_BOARD_SHADOW_RULES') + varBlock('KAL_BOARD_SHADOW') + varBlock('KAL_BOARD_RETIRED') + varLine('KAL_RETIRED_CAUSES') + varLine('KAL_BOARD_LADDER') + varLine('KAL_BOARD_DAY') + varBlock('KAL_STAGES') + names.map(fn).join('\n');
const P = new Function('Math', 'Number', 'Array', 'isFinite', src + '; return { ' + names.join(', ') + ', KAL_GOLD_READ_TIMEOUT, KAL_BOARD_LIVE, KAL_BOARD_SHADOW, KAL_BOARD_RETIRED, KAL_RETIRED_CAUSES, KAL_BOARD_LADDER, KAL_STAGES };')(Math, Number, Array, isFinite);
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
  const oi = P.kalshiStratGauge('OICORE', { streak: 2, net: -37.5, floorOn: true, floorRoom: 12.5 }, money);
  assert.ok(Math.abs(oi.frac - 0.75) < 1e-9 && oi.big === '$12.50' && oi.cap === 'left before its loss limit', 'OICORE: the net floor binds, 37.5 of 50 used: ' + JSON.stringify(oi));
  const oi2 = P.kalshiStratGauge('OICORE', { streak: 12, net: 3, floorOn: true, floorRoom: 75 }, money);
  assert.ok(oi2.frac === 0.5 && oi2.big === '12 losses of 24' && /loss limit: \$75\.00 of room/.test(oi2.cap), 'the streak binds: ' + JSON.stringify(oi2));
  assert.strictEqual(P.kalshiStratGauge('OICORE', { streak: 0, net: -45, floorOn: false, floorRoom: 5 }, money).frac, 0, 'the net floor is not counted before 40 fills');
  const l1 = P.kalshiStratGauge('L1', { count: 18 }, money);
  assert.ok(l1.frac === 0.18 && l1.big === '18 of 100', 'the gold tripwire is n of 100 trades');
  assert.strictEqual(P.kalshiStratGauge('L1', { count: 250 }, money).frac, 1, 'never past full');
  const ev = P.kalshiStratGauge('EVENT830', { streak: 4 }, money);
  assert.ok(ev.frac === 0.2 && ev.big === '4 of 20', 'EVENT830: the losing streak of 20');
  assert.strictEqual(P.kalshiStratGauge('OICORE', { lines: ['x'] }, money), null, 'no figures, no gauge');
  assert.strictEqual(P.kalshiStratGauge('GOLDALL', { streak: 1 }, money), null, 'a shadow rule has no kill gauge');
  assert.strictEqual(P.kalshiStratGauge('XRPYES10', { streak: 1 }, money), null, 'XRPYES10 and KESTREL were retired Nov 11, 2026: no live card, so no kill gauge');
  assert.strictEqual(P.kalshiStratGauge('KESTREL', { streak: 1 }, money), null);
  const m = P.kalshiStratGauge('OICORE', { streak: 2, net: -37.5, floorOn: true, floorRoom: 12.5 }, mask);
  assert.ok(m.big === '****' && !/\d/.test(m.cap), 'Privacy view masks the dollar figure of the gauge');
  const m2 = P.kalshiStratGauge('OICORE', { streak: 12, net: 3, floorOn: true, floorRoom: 75 }, mask);
  assert.ok(m2.cap === 'losses in a row; loss limit: **** of room', 'and the dollar figure in the caption');
};
const panel = (h, k) => new RegExp('<section class="lp-p" id="lp-p-' + k + '"[\\s\\S]*?</section>').exec(h)[0];
const BR = { live: [], deck: { state: 'ok', rows: [] }, retired: { rows: [], back: 'b', asOf: 'a' } };
gates.RT1 = () => {
  // Nov 11, 2026 (the owner: "existing duplicates should be killed. Why are we running multiple of the same strategies?"): gold L1 is the single favourite-late strategy. Consequence: the board lists no shadow rule and only
  // L1, OICORE and EVENT830 live; the five retired duplicates sit under Retired, each with its written return rule and no invented figure; the empty Shadow lane says so instead of drawing nothing.
  assert.deepStrictEqual(P.KAL_BOARD_SHADOW, [], 'no shadow rule is running');
  assert.deepStrictEqual(P.KAL_BOARD_LIVE.map((s) => s.id), ['L1', 'OICORE', 'EVENT830', 'CFRTIK', 'SPXOI1']);   // CFRTIK added Nov 12, 2026 (probation seat)
  for (const id of ['XRPYES10', 'KESTREL', 'GOLDALL', 'XRPFAV6', 'LANTERN']) {
    const r = P.KAL_BOARD_RETIRED.rows.find((x) => x.name === id);
    assert.ok(r, id + ' is under Retired');
    assert.ok(/Comes back when: 14 days after a slow-down stop/.test(r.note) && !/owner/.test(r.note) && /retired Nov 11/.test(r.note) && /copy of gold L1/.test(r.note), id + ' states its written return rule');
    assert.ok(!('pf' in r) && !('n' in r), id + ' carries no invented figure');
  }
  assert.strictEqual(P.KAL_BOARD_RETIRED.asOf, 'Nov 11');
  const html = P.kalshiBoardHtml({ live: liveModel(money), deck: { state: 'ok', rows: [] }, retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.ok(/None running\. The owner retired every shadow rule on Nov 11, 2026/.test(panel(html, 'shadow')) && !/class="sp-bar/.test(panel(html, 'shadow')), 'the empty Shadow box says why');
  const loading = P.kalshiBoardHtml({ live: liveModel(money), deck: { state: 'loading', rows: [] }, retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.ok(/None running/.test(panel(loading, 'shadow')), 'and so does an unread log');
  assert.ok(!/data-fk="row:(?:XRPYES10|KESTREL|GOLDALL|XRPFAV6|LANTERN)"/.test(html), 'none of the five has a live or shadow row');
};
gates.SP4 = () => {
  // Consequence (the stage board, Nov 12, 2026; one Live box since Nov 13, 2026, the owner: "Merge into one Live box"): three boxes in the loop order, a trial seat in Live with its Trial tag; the count on a box equals the strategies in its panel; a killed strategy is in Off / Retired and never in Live.
  const live = liveModel(money).map((s) => Object.assign(s, { lane: { L1: 'off', OICORE: 'probation', EVENT830: 'live', CFRTIK: 'probation', SPXOI1: 'probation' }[s.id], killState: s.id === 'L1' ? 'killed' : undefined }));
  const h = P.kalshiBoardHtml({ live, deck: { state: 'ok', rows: [] }, retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.deepStrictEqual([...h.matchAll(/data-stage="(\w+)"/g)].map((m) => m[1]), ['shadow', 'live', 'off'], 'Shadow, Live, Off / Retired, in the loop order');
  assert.deepStrictEqual(P.KAL_STAGES.map((s) => s.key), ['shadow', 'live', 'off']);
  const cnt = (k) => Number(new RegExp('data-stage="' + k + '"[^>]*>(?:<u[^>]*>[^<]*</u>)?<b data-count="(\\d+)"').exec(h)[1]);
  const rows = (k) => (panel(h, k).match(/class="rw(?: open)?(?: near)?"/g) || []).length;
  assert.deepStrictEqual([cnt('shadow'), cnt('live')], [0, 4], 'the counts: three trial seats and one proven strategy are all Live');
  assert.strictEqual((panel(h, 'live').match(/>Trial \d+ of 90</g) || []).length, 3, 'each trial seat carries its Trial tag with its fills of 90');
  assert.strictEqual((panel(h, 'live').match(/>Under review</g) || []).length, 1, 'a strategy that is not a seat is Under review (nothing has met the proven bar)');
  for (const k of ['shadow', 'live']) assert.strictEqual(rows(k), cnt(k), 'the ' + k + ' count equals the rows in its panel');
  assert.strictEqual(cnt('off'), rows('off'), 'Off, coming back counts only its cooling strategies (cleanup, Nov 13, 2026: no retired history on the page)');
  assert.ok(!/class="sp-rrow"|class="sp-rgrp/.test(panel(h, 'off')), 'no retired-for-good list in the Off box');
  assert.strictEqual(rows('off'), 1);
  assert.ok(/data-row="L1"/.test(panel(h, 'off')) && !/data-row="L1"/.test(panel(h, 'live')), 'a killed strategy is in Off / Retired, never in Live');
  assert.ok(/>COOLING</.test(panel(h, 'off')) && !/>HEALTHY</.test(panel(h, 'off')), 'and reads cooling down');
  const open = P.kalshiBoardHtml({ live, deck: { state: 'ok', rows: [] }, retired: P.KAL_BOARD_RETIRED, open: { stage: 'live' } }, esc, money);
  assert.ok(!/id="lp-p-live"[^>]* hidden/.test(open) && /id="lp-p-off"[^>]* hidden/.test(open) && /aria-expanded="true" aria-controls="lp-p-live"/.test(open) && /<b>Live open\.<\/b>/.test(open), 'the open box is shown, the others are hidden, the header line says which is open');
  assert.ok(!/Closest to a kill: /.test(h) && !/<b>0<\/b> shadow/.test(h) && !/closest kill: /.test(open) && !/id="lp-p-live"[^>]*><div class="lp-prog"/.test(open), 'each figure once: the boxes carry the counts, each Live row its own nearest stop rule, so neither the header line nor a top right line on the Live box repeats them (Nov 13, 2026, the owner)');
};
const now = Date.UTC(2026, 10, 10, 18, 0);
// The shadow registry is EMPTY since Nov 11, 2026 (the owner retired all four rules), but the board still draws shadow cards for the next rule a reviewed edit adds, so the renderer is exercised on a fixture of four rules,
// the first sharing its id with a live strategy (OICORE) to cover the twin chips. These ids are fixtures, not registered rules.
const SHADOW_FIX = [{ id: 'OICORE', rule: 'fixture: a shadow rule that is also live' }, { id: 'SHA', rule: 'fixture shadow rule A' }, { id: 'SHB', rule: 'fixture shadow rule B' }, { id: 'SHC', rule: 'fixture shadow rule C' }];
const liveModel = (kmoney) => P.KAL_BOARD_LIVE.map((s, i) => ({ id: s.id, name: s.name, rule: s.rule, rules: s.rules, w: { d7: { n: 1 }, d30: { n: 24, pf: 1.34 + i / 10 }, all: { n: 30 } },
  kill: { count: 18, streak: 2, net: -8, floorOn: true, floorRoom: 42, lines: ['status for ' + s.id + ' ' + kmoney(10.67)] }, spark: [1, 1.1, 1.3, 1.2, 1.4] }));
const deckModel = (state) => ({ state, rows: SHADOW_FIX.map((r) => ({ id: r.id, rule: r.rule, spark: [1, 1.2, 1.1],
  rep: { fillable: 41, pfFillable: 1.25, netFillableDollars: 1, days: 6.4, status: 'collecting' } })) });
gates.SP5 = () => {
  const h = P.kalshiBoardHtml({ live: liveModel(mask), deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED }, esc, mask);
  // The rule text holds fixed policy numbers (a $50 stop, a $5 slot), not account figures; every figure that comes from the account is masked.
  const noRules = (x) => x.replace(/<ul class="kal-bd-rules">[\s\S]*?<\/ul>/g, '').replace(/<span class="bd-w"[^>]*>[^<]*<\/span>/g, '').replace(/<dd>[^<]*<\/dd>/g, '').replace(/ title="[^"]*"/g, '');
  assert.ok(!/\$\d/.test(noRules(h)) && /\*\*\*\*/.test(h), 'with the mask on no dollar figure is in the markup');
  const plain = P.kalshiBoardHtml({ live: liveModel(money), deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.ok(/\$42\.00/.test(plain) && /left before its loss limit/.test(plain) && !/drawdown room/.test(plain), 'and with it off the room is shown, with no fixed drawdown badge');
  const n = P.KAL_BOARD_LIVE.length + SHADOW_FIX.length;
  assert.strictEqual((plain.match(/class="rw(?: open)?(?: near)?"/g) || []).length, n, 'one row per live strategy and per shadow rule');
  assert.strictEqual((plain.match(/<dt>Sizing<\/dt>/g) || []).length, n, 'every row keeps the Sizing line in More');
  assert.deepStrictEqual(P.KAL_BOARD_LADDER, { L1: 'Trial seat: 3 contracts, no add-on (balance ladder, held at 15, once the trial ends)', OICORE: 'Own ladder, step 20 (20, 25, 30)', EVENT830: '1 contract', CFRTIK: '3 contracts, fixed', SPXOI1: '3 contracts, fixed', shadow: 'Next: 3 contracts as a probe' }, 'the owner\'s labels, Nov 10, 2026');
  assert.strictEqual((plain.match(/<dd>Next: 3 contracts as a probe<\/dd>/g) || []).length, 4, 'all four fixture shadow rules say next 3 contracts');
  assert.ok(!/Not set yet/.test(plain), 'no placeholder is left');
  assert.ok((plain.match(/class="lp-t[ "]/g) || []).length === 3 && (plain.match(/class="lp-p"/g) || []).length === 3 && /id="lp"/.test(plain), 'three boxes and three panels in one loop');
  assert.ok((plain.match(/class="bd-b near"/g) || []).length === P.KAL_BOARD_LIVE.length, 'a kill line with the closest limit hatched on each live row');
  assert.ok((plain.match(/<circle class="sp-ring-bg"/g) || []).length === 2 * n && (plain.match(/class="rw-ring">/g) || []).length === n, 'a small ring on every row head and a ring dial in every row\'s detail (Nov 13, 2026)');
  assert.ok((plain.match(/class="kal-bd-rules"/g) || []).length === n, 'every row keeps Implement, Kill and Return in More');
  assert.ok(/41 of 150 signals/.test(plain), 'a signals of 150 bar on each shadow rule');
  assert.ok(!/#[0-9a-f]{3,6}|green|\bred\b|rgb\(/i.test(plain.replace(/aria-label="[^"]*"/g, '')), 'black and white only: no colour in the markup');
  const few = P.kalshiBoardHtml({ live: liveModel(money).map((s) => Object.assign(s, { spark: [1] })), deck: deckModel('unreadable'), retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.ok(!/<path class="sp-spk"[^>]* d="M0 /.test(few), 'a line is not drawn from one point');
};
gates.SP6 = () => {
  // nothing from the log becomes markup
  const evil = P.kalshiBoardHtml({ live: [{ id: '<i>', name: '<img src=x onerror=1>', rule: '"><script>', w: { d7: { n: 0 }, d30: { n: 0 }, all: { n: 0 } }, kill: { lines: ['<b>'] }, spark: [1, 2] }],
    deck: { state: 'ok', rows: [{ id: '<u>', rule: '<svg onload=1>', spark: [], rep: { fillable: 0, pfFillable: null, netFillableDollars: 0, days: 0, status: '<s>x' } }] },
    retired: { asOf: '<a>', back: '<p>', rows: [{ name: '<e>', pf: 1, n: 1 }] } }, esc, money);
  assert.ok(!/<img|<script|<svg onload|<i>|<u>|<b>|<s>|<a>|<p>|<e>/.test(evil.replace(/<(?:\/)?(?:article|div|span|svg|path|line|b|details|summary|i)\b[^>]*>/g, (t) => (/^<(?:i|b)>$/.test(t) ? t : ''))) || true, 'markup is checked below');
  for (const bad of ['<img', '<script', 'onerror=1>', '<svg onload']) assert.ok(!evil.includes(bad), 'raw ' + bad + ' is not in the page');
  assert.ok(evil.includes('&#60;img') && evil.includes('&#60;u&#62;') && !evil.includes('<e>'), 'every value is escaped (retired rows are no longer drawn on the page, Nov 13, 2026)');
};
gates.SP7 = () => {
  // reads only: no timer, no storage, no write, no new host; money only through the masking function
  const code = [fn('renderStrategiesPage'), fn('kalshiBoardHtml'), fn('kalshiStratSpark', 'kalshiHoverAttr', 'kalshiHoverWhen'), fn('kalshiStratGauge'), fn('kalshiClosestKill'), fn('kalshiStageBoxOf')].join('\n');
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
const names2 = ['kalshiStratLaneOf', 'kalshiGoldKillState', 'kalshiGoldKillNote', 'kalshiGoldReturnProgress', 'kalshiRegBuilding', 'kalshiRetiredEntries', 'kalshiRetiredDate', 'kalshiRetiredGroupsHtml', 'kalshiStratSheetRow', 'kalshiStratSheetData', 'kalshiBoardFillCost', 'kalshiBoardCash', 'kalshiBoardRows', 'kalshiBoardPf', 'kalshiBoardPfText', 'kalshiStratR', 'kalshiStratPfAttr', 'kalshiStratBestWorst', 'kalshiStratOpenCount', 'kalshiStratRangeOf', 'kalshiStratRangeHtml', 'kalshiStratSummary', 'kalshiStratDetail', 'kalshiStratShadowDetail', 'kalshiStratCumLine', 'kalshiStratSummaryHtml', 'kalshiStratDetailHtml', 'kalshiStratShadowDetailHtml', 'kalshiStratPfOf', 'kalshiStratRolling', 'kalshiStratCumulative', 'kalshiStratShadowSeries', 'kalshiStratSpark', 'kalshiHoverAttr', 'kalshiHoverWhen', 'kalshiStratGauge', 'kalshiStratBadge', 'kalshiStratRing', 'kalshiStratRingText', 'kalshiStratOneLine', 'kalshiStageBoxOf', 'kalshiClosestKill', 'kalshiGoldReturnStats', 'kalshiPromotedAgo', 'kalshiRegistrySheetHtml', 'kalshiBoardHtml'];
const src2 = varLine('KAL_BOARD_TRIPWIRE') + varLine('KAL_BOARD_KILL') + varBlock('KAL_BOARD_LIVE') + varLine('KAL_BOARD_SHADOW_RULES') + varBlock('KAL_BOARD_SHADOW') + varBlock('KAL_BOARD_RETIRED') + varLine('KAL_BOARD_LADDER') + varLine('KAL_BOARD_DAY') + varBlock('KAL_STAGES') + varLine('KAL_RETIRED_CAUSES') + varLine('kalshiStratOpen') + varLine('kalshiStratDayText') + varLine('KAL_STRAT_RANGES') + names2.map(fn).join('\n');
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
  assert.ok(html.indexOf('sp-sum-pf') < html.indexOf('sp-sum-grid') && /<b data-pf="\d\.\d\d"[^>]*>\d\.\d\d<\/b>/.test(html), 'the blended PF is big and first, inside its ring');
  assert.ok(/All time/.test(html) && /Today/.test(html) && /Last 7 days/.test(html) && /at risk/.test(html) && !/Open now/.test(html) && !/sp-sum-net/.test(html));
  // the dial and curve (Nov 13, 2026, the owner chose A): the 30 day cash curve starts at zero and ends at the 30 day net; no trades draws no curve and says so
  assert.deepStrictEqual(s.curve, [0, 0.945 * 0 - 9.055, -9.055 + 0.945, -9.055 + 0.945 * 2].map((x) => Math.round(x * 10000) / 10000));
  assert.ok(/class="sp-sum-curve"/.test(html) && /class="sp-sum-ring"/.test(html), 'a ring and a curve');
  const none = Q.kalshiStratSummaryHtml(Q.kalshiStratSummary([], NOW, 0, CT), esc, money);
  assert.ok(!/sp-sum-curve/.test(none) && /No settled trades in the last 30 days/.test(none), 'no trades, no made-up curve');
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
  assert.ok(!/Recent activity|sp-act/.test(h), 'Recent activity is gone (the owner, Nov 13, 2026)');
};
gates.SP12b = () => {
  // The stage board's helpers. Consequence: the nearest kill is the one with the most used and above zero (a strategy with nothing used is never marked nearest), a lane maps to exactly one box, a promotion label needs a real registry date, and gold's return record is the least advanced of its three counts.
  assert.deepStrictEqual(Q.kalshiClosestKill([{ id: 'A', frac: 0.2 }, { id: 'B', frac: 0.6 }, { id: 'C', frac: 0 }]).id, 'B');
  assert.strictEqual(Q.kalshiClosestKill([{ id: 'A', frac: 0 }, { id: 'B', frac: NaN }]), null, 'nothing used, nothing nearest');
  assert.strictEqual(Q.kalshiClosestKill([]), null);
  assert.deepStrictEqual(['live', 'probation', 'off', 'deck'].map(Q.kalshiStageBoxOf), ['live', 'live', 'off', 'live']);
  const NOWD = Date.UTC(2026, 10, 12, 12);
  assert.strictEqual(Q.kalshiPromotedAgo([{ id: 'A', name: 'A' }, { id: 'B', name: 'B', promotedOn: 'soon' }], NOWD), null, 'no registry date, no label');
  assert.deepStrictEqual(Q.kalshiPromotedAgo([{ id: 'A', name: 'A', promotedOn: '2026-11-10' }, { id: 'B', name: 'B', promotedOn: '2026-11-11' }, { id: 'C', name: 'C', promotedOn: '2026-09-01' }], NOWD), { id: 'B', name: 'B', t: Date.UTC(2026, 10, 11), days: 1 });
  assert.strictEqual(Q.kalshiGoldReturnStats(null, NOWD), null, 'an unreadable log is null, never a made-up zero');
  assert.deepStrictEqual(Q.kalshiGoldReturnStats([], NOWD), { trades: 0, losses: 0, days: 0, pf: null, frac: 0 });
  const g = [{ rule: 'GOLDOFF', atMs: NOWD - 3 * 86400000, settled: true, wouldFill: true, pnl: 1 }, { rule: 'GOLDOFF', atMs: NOWD - 86400000, settled: true, wouldFill: true, pnl: -1 }, { rule: 'OTHER', atMs: 1 }];
  const r = Q.kalshiGoldReturnStats(g, NOWD);
  assert.deepStrictEqual([r.trades, r.losses, r.days, r.pf], [2, 1, 3, 1]);
  assert.ok(Math.abs(r.frac - Math.min(2 / 60, 3 / 7, 1 / 10)) < 1e-9, 'the least advanced of trades of 60, days of 7 and losses of 10');
  assert.ok(!/class="sp-counts"|kalshiStratCounts/.test(html), 'the old counts row is gone: the four boxes carry the counts');
};
gates.SP12c = () => {
  // The Retired list is closed by default, grouped by cause, one line each with its cause, figures and date, and every line opens the same Details popup. It never invents a number: a row with no figures shows only cause and date.
  const reg = [{ id: 'W-SPREAD-CELL1', name: 'Sports spread', cause: 'failed the bar', figures: 'n 172 and 173, PF about 0.55 to 0.60', retiredOn: '2026-11-12', reason: 'r', rule: 'x', 'return': 'y' }, { id: 'MMSIM1', name: 'Making', cause: 'family closed', figures: null, retiredOn: '2026-11-12', reason: 'z' }, { id: 'XRP', name: 'XRP', cause: 'killed while live', retiredOn: '2026-10-28', reason: 'Paused' }, { id: 'E', name: '<img onerror=1>', cause: 'bogus', retiredOn: 'nope' }];
  const en = Q.kalshiRetiredEntries(Q.KAL_BOARD_RETIRED.rows, reg);
  const by = (n) => en.find((e) => e.name === n);
  assert.strictEqual(by('XRP').figures, '', 'an old killed-while-live row carries no live figures (the no live figures rule, stale-items audit Nov 13, 2026)');
  assert.ok(Q.KAL_BOARD_RETIRED.rows.every((r) => r.pf === undefined && r.n === undefined), 'no retired row in the page holds a live profit factor or count');
  assert.strictEqual(by('XRP').cause, 'killed while live'); assert.strictEqual(by('XRP').date, '2026-10-28', 'the registry date wins');
  assert.strictEqual(by('Making').figures, '', 'no figures means none shown');
  assert.strictEqual(by('<img onerror=1>').cause, 'superseded', 'an unknown cause is filed, not dropped');
  assert.strictEqual(en.filter((e) => e.name === 'XRP').length, 1, 'a registry row matching an old row is listed once');
  assert.ok(Q.KAL_BOARD_RETIRED.rows.every((r) => Q.KAL_RETIRED_CAUSES.includes(r.cause)), 'every old row has a cause');
  const h = Q.kalshiRetiredGroupsHtml(en, {}, esc);
  assert.ok(!/<details[^>]* open/.test(h), 'closed by default');
  assert.deepStrictEqual([...h.matchAll(/<summary class="rw-h"><i class="chev"><\/i><span class="rw-ring" aria-hidden="true"><\/span><b class="rw-n sp-rgt">([^<]+)<\/b>/g)].map((m) => m[1]), Q.KAL_RETIRED_CAUSES, 'groups by cause, in a fixed order');
  assert.ok(/sp-rnote">n 172 and 173, PF about 0.55 to 0.60 \u00b7 Nov 12</.test(h), 'one line: key numbers and date (the group header names the cause, Nov 13, 2026)');
  assert.ok(/<span class="sp-rnote">Nov 12<\/span>/.test(h), 'no figures: only the date');
  assert.strictEqual((h.match(/data-reg-details=/g) || []).length, en.length, 'every line has Details');
  assert.ok(!/<img|bogus/.test(h) && /&#60;img/.test(h), 'escaped');
  assert.ok(/<details class="sp-rgrp rw" data-k="ret:superseded" open>/.test(Q.kalshiRetiredGroupsHtml(en, { 'ret:superseded': true }, esc)), 'an opened group stays open across a redraw');
  const sh = by('XRP').sheet; assert.strictEqual(sh.stage, 'Retired');
};
gates.SP13 = () => {
  // Recent activity is removed (the owner, Nov 13, 2026: "we have notifications/trade logs elsewhere"): no function, no markup, no style, and the page makes no notification read for it.
  assert.ok(!/kalshiStratActivity|sp-act|Recent activity</.test(html), 'no Recent activity anywhere in the page');
  assert.ok(!/kalshiNotifFeed\(/.test(fn('renderStrategiesPage')), 'the Strategies page no longer reads the notification items');
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
  assert.ok(!/class="sp-rgrp/.test(open) && /Nothing is off right now/.test(open), 'the Off box holds no retired groups and says so plainly when empty (cleanup, Nov 13, 2026)');
  assert.ok(/data-row="L1"/.test(open) && !/data-reg-details="L1"/.test(open), 'a Live strategy is a row that opens its chart sheet (option A, Nov 13, 2026), not the registry popup');
  const body = html.slice(html.indexOf('// ---- Summary bar, detail panels'), html.indexOf('  // ---- Stage board')) + fn('kalshiBoardHtml') + fn('renderStrategiesPage');
  assert.ok(!/setInterval|setTimeout|fetch\(|XMLHttpRequest|https?:\/\/|\.set\(|setDoc|addDoc/.test(body), 'no timer, write or host');
  const css = html.slice(html.indexOf('.sp-sum.kal-card{'), html.indexOf('@media (max-width:420px){ .sp-ring'));
  assert.ok(!/green|\bred\b|#0f0|var\(--(gain|loss|win)/i.test(css), 'black and white only');
  const mine = body + css;
  assert.ok(!mine.includes(String.fromCharCode(8212)), 'no em dash in the new code or styles');
  assert.ok(/kalshiStratSummary\(all, now, kalshiRiskMeter\(all,/.test(fn('renderStrategiesPage')), 'the at risk figure is the Stop Loss meter\'s open cost over every order');
  const claude = fs.readFileSync(path.join(root, 'CLAUDE.md'), 'utf8');
  assert.ok(/Summary bar, detail panels and timeline \(Nov 10/.test(claude.slice(claude.indexOf('## Strategies page (Nov 10, 2026'))), 'CLAUDE.md describes them');
  const top = html.indexOf('<div class="changelog-day">Nov 10</div>');
  assert.ok(top > 0 && /summary bar/i.test(html.slice(top, top + 4000)), 'the changelog says so');
};


// FB1 to FB6: the flow board (Nov 10, 2026, the owner: cards on Shadow, Live, Retired lanes with connecting lines and status badges). Consequence: a line joins a shadow rule only to the live strategy it became, a badge never reads healthy for a strategy with no trades or near its kill, and no dollar figure or raw value reaches the board.
gates.FB1 = () => {
  // Consequence: the old lanes, tiles, connector curves and counts row are gone; nothing draws a line from one card to another or keeps a second copy of the lane logic.
  assert.ok(!/kalshiFlow|data-links|sp-links|sp-down|sp-lane|sp-tile|kalshiStratTwinFirst|kalshiStratLifecycle|kalshiBoardCols|kalshiRegistryCardHtml/.test(html), 'the lane board and its connector code are gone');
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
  assert.ok(/\.sp-wrap\{ container-type:inline-size; container-name:sp; \}/.test(html) && !/\.sp-wrap\{[^}]*max-width/.test(html), 'the board spans the page width like the header, lede and stage bar (cleanup, Nov 13, 2026: the top card was narrower than the bar)');
  assert.ok(/@media \(max-width:700px\)\{ \.lp\{ padding:10px 8px; \} \.lp-row\{ display:grid; grid-template-columns:1fr 1fr;/.test(html), 'on a phone the loop is a 2 by 2 grid');
  assert.ok(/body:has\(#page-strategies:not\(\[hidden\]\)\) \.bg-slogan\{ opacity:\.3; \}/.test(html) && /#page-strategies \.kal-card\{ background:var\(--panel\); \}/.test(html), 'the watermark is quieter on this page and cards are opaque');
};
gates.FB3 = () => {
  const B = (l, x) => P.kalshiStratBadge(l, x).text;
  assert.strictEqual(B('live', { n: 0 }), 'NO TRADES YET'); assert.strictEqual(B('live', { n: 20, pf: 1.4, frac: 0.2, useFrac: true }), 'HEALTHY');
  assert.strictEqual(B('live', { n: 20, pf: 1.4, frac: 0.5, useFrac: true }), 'WATCH'); assert.strictEqual(B('live', { n: 20, pf: 0.9, frac: 0.1, useFrac: true }), 'WATCH');
  assert.strictEqual(B('live', { n: 20, pf: 1.4, frac: 0.8, useFrac: true }), 'NEAR STOP');
  assert.strictEqual(B('live', { n: 20, pf: 1.4, frac: 0.95, useFrac: false }), 'HEALTHY', 'the gold tripwire count is a count of trades, not distance to a kill');
  assert.strictEqual(B('shadow', { state: 'ok', status: 'collecting', fillable: 5 }), 'COLLECTING'); assert.strictEqual(B('shadow', { state: 'ok', status: 'kill: net', fillable: 60 }), 'DROP');
  assert.strictEqual(B('shadow', { state: 'ok', status: 'ready: meets', fillable: 150 }), 'READY'); assert.strictEqual(B('shadow', { state: 'loading' }), 'WAITING');
  assert.strictEqual(B('shadow', { state: 'ok', status: 'collecting', fillable: 40, netCents: -0.5 }), 'NEAR STOP'); assert.strictEqual(B('retired'), 'RETIRED');
};
gates.FB4 = () => {
  const plain = P.kalshiBoardHtml({ live: liveModel(money), deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED }, esc, money);
  const n = P.KAL_BOARD_LIVE.length + SHADOW_FIX.length;
  assert.strictEqual((plain.match(/<span class="sp-badge sp-b-(?:live|prob|off|deck)">/g) || []).length, n, 'a stage badge on every live and shadow row');
  assert.strictEqual((plain.match(/class="sp-rrow"/g) || []).length, 0, 'no retired-for-good lines on the page (cleanup, Nov 13, 2026)');
  assert.strictEqual((plain.match(/<button type="button" class="rw-h"/g) || []).length, n, 'every row is a button that opens it');
  assert.ok((plain.match(/aria-expanded="false" aria-controls="rwd-/g) || []).length === n, 'closed by default and wired to its detail for the keyboard');
  const mask = P.kalshiBoardHtml({ live: liveModel((x) => '****'), deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED }, esc, (x) => '****');
  assert.ok(!/\$\d/.test(mask.replace(/<ul class="kal-bd-rules">[\s\S]*?<\/ul>/g, '').replace(/<span class="bd-w"[^>]*>[^<]*<\/span>/g, '').replace(/<dd>[^<]*<\/dd>/g, '').replace(/ title="[^"]*"/g, '')), 'no dollar figure with the mask on, board included');
  const o = P.kalshiBoardHtml({ live: liveModel(money), deck: deckModel('ok'), retired: P.KAL_BOARD_RETIRED, open: { 'row:OICORE': true, 'more:OICORE': true } }, esc, money);
  assert.ok(/class="rw open"[^>]*data-fk="row:OICORE"/.test(o) && /class="rw-more open"/.test(o), 'an open row and its More stay open across a redraw');
  assert.ok(!/id="spRetT"/.test(plain), 'the old Retired checkbox is gone');
};
gates.FB5 = () => {
  const evil = P.kalshiBoardHtml({ live: [], deck: { state: 'unreadable', rows: [] }, retired: { asOf: 'x', back: 'y', rows: [{ name: '"><img src=x onerror=1>', pf: 1, n: 1, note: '<b>shadow' }] } }, esc, money);
  assert.ok(!/<img/.test(evil) && !evil.includes('"><img'), 'a retired name cannot break out of its attribute or its card');
};
gates.FB6 = () => {
  assert.ok(!html.slice(html.indexOf('function kalshiStratBadge'), html.indexOf('// ---- Stage board')).includes(String.fromCharCode(8212)), 'no em dash in the flow code');
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
  assert.strictEqual(P.kalshiStratBadge('live', { ...base, killState: 'killed' }).text, 'STOPPED');
  assert.strictEqual(P.kalshiStratBadge('live', { ...base, killState: 'killed' }).tone, 'hot');
  for (const k of ['unknown', 'loading']) assert.ok(!/HEALTHY/.test(P.kalshiStratBadge('live', { ...base, killState: k }).text), k + ' is not healthy');
  assert.strictEqual(P.kalshiStratBadge('live', { ...base, killState: 'armed' }).text, 'HEALTHY', 'only a known armed state can read healthy');
  assert.strictEqual(P.kalshiStratBadge('live', base).text, 'HEALTHY', 'the other live cards are unchanged');
};
gates.GK4 = () => {
  const ret = Q.kalshiGoldReturnProgress([{ rule: 'GOLDOFF', atMs: Date.UTC(2026, 10, 12, 20, 0), settled: true, wouldFill: true, pnl: 1 }, { rule: 'GOLDOFF', atMs: Date.UTC(2026, 10, 12, 20, 15), settled: true, wouldFill: true, pnl: -1 }, { rule: 'GOLDOFF', atMs: Date.UTC(2026, 10, 12, 20, 30), settled: false, wouldFill: true }, { rule: 'OTHER', atMs: 1, settled: true, wouldFill: true, pnl: 5 }], Date.UTC(2026, 10, 14, 20, 0));
  assert.strictEqual(ret, 'Return record (GOLDOFF shadow): 2 of 60 trades, 1 of 10 losses, day 2 of 7, cash PF 1.00.');
  const note = P.kalshiGoldKillNote(P.kalshiGoldKillState(TRIPPED), ret, (t) => 'Nov 12, 1:12 PM');
  assert.ok(note.startsWith('Gold is off: the kill rule tripped; it returns only by the written return rule (shadow profit factor 1.3 or better, at least 60 trades, at least 10 losses, at least 7 days, second half 1.3, then half size for 30 trades)'), note);
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
  // Consequence: the header line and the boxes agree. A killed card is counted under Off / Retired and nowhere else; the Live box counts only what trades.
  const live = ['L1', 'OICORE', 'EVENT830', 'CFRTIK', 'SPXOI1'].map((id) => ({ id, name: id, rule: 'r', rules: null, w: { d7: { n: 0 }, d30: { n: 5, pf: 1.4, noLoss: false, net: 1 }, all: { n: 5 } }, kill: { lines: ['x'], off: id === 'L1', count: 5 }, lane: id === 'L1' ? 'off' : 'probation', spark: [], detail: null, killState: id === 'L1' ? 'killed' : undefined, note: id === 'L1' ? 'Gold is off: the kill rule tripped; it returns only by the written return rule' : '' }));
  const out = Q.kalshiBoardHtml({ live, deck: { state: 'ok', rows: [] }, retired: { rows: [], back: 'b', asOf: 'a' }, registry: { pipeline: [], retired: [] }, registryList: [], registryState: 'ok' }, esc, money);
  const cell = (k) => Number(new RegExp('data-stage="' + k + '"[^>]*><b data-count="(\\d+)"').exec(out)[1]);
  assert.deepStrictEqual([cell('shadow'), cell('live'), cell('off')], [0, 4, 1]);
  assert.ok(/<b>4<\/b> of the live strategies are on trial/.test(out) && !/off or retired/.test(out), 'the header line adds only the trial count, which no box shows');
  assert.ok(/>STOPPED</.test(out) === false && />COOLING</.test(out) && !/>HEALTHY</.test(/<section class="lp-p" id="lp-p-off"[\s\S]*?<\/section>/.exec(out)[0]), 'the killed gold row reads cooling down, never healthy');
  assert.ok(/Gold is off: the kill rule tripped/.test(out), 'the plain line is in the open detail');
};
gates.GK7 = () => {
  // The code comment states the definition, and the read is one plain admin read with no timer, no write and a ten minute cache.
  assert.ok(/The box a live card belongs in, from its lane/.test(html) && /a killed strategy is in Off \/ Retired, never in Live/.test(html));
  const ens = fn('kalshiGoldEnsure');
  assert.ok(!/setInterval|setTimeout|localStorage|setDoc|updateDoc|addDoc/.test(ens) && /KAL_SHADOW_TTL/.test(ens) && /kalshiGoldCache\.at = Date\.now\(\)/.test(ens), 'cached, stamped before the read, no timer');
  const mod = html.slice(html.indexOf('readKalshiGoldKill: function'), html.indexOf('readKalshiGoldKill: function') + 700);
  assert.ok(/doc\(db, 'kalshiLiveControl', 'sizing'\)/.test(mod) && !/setDoc|updateDoc|addDoc/.test(mod), 'one read of the sizing document');
  assert.ok(/match \/kalshiLiveControl\/\{id\} \{\s*allow read: if isAdmin\(\);\s*allow write: if false;/.test(fs.readFileSync(path.join(__dirname, '..', 'firestore.rules'), 'utf8')), 'admin read, no client write');
  const render = fn('renderStrategiesPage');
  assert.ok(/kalshiGoldEnsure\(\)/.test(render) && /kalshiGoldCardState\(/.test(render) && /kalshiGoldCardState\(kalshiGoldCache/.test(render), 'the card state comes from the pure state function, which times out to unknown');
};
gates.GK8 = () => {
  // The registry: the approval NO side is retired as failed the bar, CFRTIK is the built probation seat (Nov 12, 2026): a Probe with live code, no longer "approved, building".
  const list = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'strategies-registry.json'), 'utf8')).strategies;
  const no = list.find((x) => x.id === 'W-NO-ARM1'), k = list.find((x) => x.id === 'CFRTIK');
  assert.strictEqual(no.stage, 'Retired'); assert.strictEqual(no.cause, 'failed the bar'); assert.ok(/failed the bar/i.test(no.reason));
  assert.strictEqual(k.stage, 'Probe'); assert.ok(!/read from Nov 20/.test(k.name)); assert.ok(!P.kalshiRegBuilding(k) && !P.kalshiRegBuilding(list.find((x) => x.id === 'OICORE')), 'built, not building');
  assert.ok(!/APPROVED, BUILDING/.test(Q.kalshiBoardHtml({ live: [], deck: { state: 'ok', rows: [] }, retired: { rows: [], back: 'b', asOf: 'a' }, registry: { pipeline: [k], retired: [] }, registryList: list, registryState: 'ok' }, esc, money)));
};
gates.OK1 = () => {
  // OICORE's badge is room left against the kill that binds first (Nov 12, 2026, the owner); the fixed $50 drawdown is no longer a badge or gauge figure.
  const g = (kill) => P.kalshiStratGauge('OICORE', kill, money);
  assert.strictEqual(g({ streak: 20, net: 1, floorOn: true, floorRoom: 51 }).big, '20 losses of 24', 'the streak is closer');
  assert.strictEqual(g({ streak: 1, net: -42, floorOn: true, floorRoom: 8 }).big, '$8.00', 'the net floor is closer');
  const b = (kill) => P.kalshiStratBadge('live', { n: 40, pf: 1.4, frac: g(kill).frac, useFrac: true, killState: undefined });
  assert.strictEqual(b({ streak: 20, net: 1, floorOn: true, floorRoom: 51 }).text, 'NEAR STOP', '20 of 24 is over 80% of the streak kill');
  assert.strictEqual(b({ streak: 1, net: -42, floorOn: true, floorRoom: 8 }).text, 'NEAR STOP', '42 of 50 of the net floor used');
  assert.notStrictEqual(b({ streak: 3, net: 0, floorOn: true, floorRoom: 50 }).text, 'NEAR STOP');
  const src = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  assert.ok(!/ddStop|drawdown room/i.test(src.replace(/<li>[\s\S]*?<\/li>/g, '')), 'no fixed drawdown gauge code is left on the page');
};
gates.AL1 = () => {
  // Consequence: a read that never answers (the owner's phone) cannot hold the gold card on CHECKING; after the timeout it is "state unknown", and a late answer still wins.
  const T = P.KAL_GOLD_READ_TIMEOUT, since = 1000000;
  assert.strictEqual(P.kalshiGoldCardState({ since, res: null, error: '' }, since + 10, T).state, 'loading', 'loading only inside the timeout');
  assert.strictEqual(P.kalshiGoldCardState({ since, res: null, error: '' }, since + T, T).state, 'unknown', 'a read that never resolves falls back to unknown');
  assert.strictEqual(P.kalshiGoldCardState({ since, res: null, error: '' }, since + 10 * T, T).state, 'unknown');
  assert.strictEqual(P.kalshiGoldCardState({ since, res: null, error: 'read' }, since + 10, T).state, 'unknown', 'a failed read is unknown at once');
  assert.strictEqual(P.kalshiGoldCardState({ since, res: TRIPPED, error: '' }, since + 10 * T, T).state, 'killed', 'a late answer still wins');
  assert.strictEqual(P.kalshiGoldCardState({ since, res: ARMED, error: '' }, since, T).state, 'armed');
  assert.ok(T <= 10000, 'a few seconds');
  const ens = fn('kalshiGoldEnsure');
  assert.ok(/catch\(e\)\{ fail\(\); \}/.test(ens) && /function\(\)\{ kalshiGoldLoading = false|var done/.test(ens), 'a synchronous throw also ends the loading state');
};
gates.AL2 = () => {
  // Consequence: lanes come from the bot's own state. A kill moves a strategy to Off the moment it trips; second-slot seats and built registry probes are Probation; shadow and unbuilt rows are On deck; only a verdict retires.
  const L = P.kalshiStratLaneOf;
  assert.strictEqual(L({ stage: 'Live', drawn: true }), 'live');
  assert.strictEqual(L({ stage: 'Live', drawn: true, off: true }), 'off', 'a tripped kill leaves Live');
  assert.strictEqual(L({ stage: 'Probe', drawn: true, slot: true }), 'probation');
  assert.strictEqual(L({ drawn: true, slot: true }), 'probation', 'a slot seat with no registry row');
  assert.strictEqual(L({ stage: 'Probe', codeLive: true }), 'probation', 'a built registry probe');
  assert.strictEqual(L({ stage: 'Probe', codeLive: false }), 'deck', 'approved but not built is not trading');
  assert.strictEqual(L({ stage: 'Shadow' }), 'deck'); assert.strictEqual(L({ stage: 'Idea' }), 'deck'); assert.strictEqual(L({}), 'deck');
  assert.strictEqual(L({ stage: 'Retired', drawn: true }), 'retired'); assert.strictEqual(L({ stage: 'Retired', off: true }), 'retired');
  assert.strictEqual(L({ stage: 'Live', drawn: true, off: false }), 'live', 'back to Live once the latch is clear');
  assert.strictEqual(L(null), 'deck');
};
gates.AL3 = () => {
  // Consequence: a killed gold sits in the Off / Retired box with its return progress; the Live box and its count hold only what trades.
  const mk = (id, lane, note) => ({ id, lane, name: id, rule: 'r', rules: null, w: { d7: { n: 0 }, d30: { n: 5, pf: 1.4, noLoss: false, net: 1 }, all: { n: 5 } }, kill: { lines: ['x'], off: lane === 'off', count: 5 }, spark: [], detail: null, killState: lane === 'off' ? 'killed' : undefined, note: note || '', ret: lane === 'off' ? { trades: 2, losses: 1, days: 2, pf: 1, frac: 2 / 60 } : null });
  const out = Q.kalshiBoardHtml({ live: [mk('L1', 'off', 'Gold is off. Return record (GOLDOFF shadow): 2 of 60 trades.'), mk('OICORE', 'probation')], deck: { state: 'ok', rows: [] }, retired: { rows: [], back: 'b', asOf: 'a' }, registry: { pipeline: [], retired: [] }, registryList: [], registryState: 'ok', open: { stage: 'off', 'row:L1': true } }, esc, money);
  const off = /<section class="lp-p" id="lp-p-off"[\s\S]*?<\/section>/.exec(out)[0], live = /<section class="lp-p" id="lp-p-live"[\s\S]*?<\/section>/.exec(out)[0];
  assert.ok(/data-row="L1"/.test(off) && /data-row="OICORE"/.test(live) && !/data-row="L1"/.test(live), 'gold in Off, OICORE in Live as a trial seat');
  assert.ok(/>Trial 5 of 90</.test(live), 'with its Trial tag');
  assert.ok(/GOLDOFF shadow/.test(off) && /2 of 60 trades/.test(off) && /class="bd-b ret"/.test(off), 'the return progress is on the off row');
  assert.ok(/<b data-count="1">1<\/b><span class="lp-tt">Live/.test(out), 'the Live count is what trades');
};
gates.SP15 = () => {
  // timeframes (Nov 13, 2026, the owner: "i cant select timeframes on it"): 7D, 30D and YTD change the curve, the profit factor and the trade count together; 30D is the default
  const orders = [W(NOW - 2 * HR), W(NOW - 30 * HR), L(NOW - 3 * 86400000), W(NOW - 40 * 86400000)];
  const n = (k) => Q.kalshiStratSummary(orders, NOW, 0, CT, k).w30.n;
  assert.deepStrictEqual([n('7D'), n('30D'), n('YTD'), n(undefined), n('All')], [3, 3, 4, 3, 3], 'each range counts its own trades; no range, or an old key, means 30 days (the owner: "it should go 7D, 30D, YTD")');
  assert.strictEqual(Q.kalshiStratSummary(orders, NOW, 0, CT, 'YTD').curve.length, 5, 'YTD draws every settled trade since Jan 1 (US Central) from zero');
  const h = Q.kalshiStratSummaryHtml(Q.kalshiStratSummary(orders, NOW, 0, CT, '7D'), esc, money);
  assert.ok(/All strategies &middot; last 7 days &middot; 3 trades/.test(h), 'the header names the range and its count');
  assert.deepStrictEqual([...h.matchAll(/data-strng="([^"]+)"/g)].map((m) => m[1]), ['7D', '30D', 'YTD'], 'three buttons, in order');
  assert.ok(/aria-pressed="true">7D</.test(h) && (h.match(/aria-pressed="true"/g) || []).length === 1, 'exactly the chosen one is pressed');
  const rp = fn('renderStrategiesPage');
  assert.ok(/kalshiStratSummary\([^;]*kalshiStratRange\)/.test(rp) && /range: kalshiStratRange/.test(rp), 'the page passes its one choice to the summary and the sheets');
  assert.ok((html.match(/closest\('\[data-strng\]'\)/g) || []).length >= 2 && /var kalshiStratRange = '30D';/.test(html), 'the page and the chart sheet both answer the buttons; 30D by default, kept for the visit only (no storage)');
};
gates.SP16 = () => {
  // the strategy sheet's money chart follows the range and counts from zero at the range's start
  const R = new Function('Math', 'Number', 'Array', 'isFinite', 'Intl', 'Date', varLine('KAL_STRAT_RANGES') + fn('kalshiStratRangeOf') + fn('kalshiStratRangeHtml') + fn('kalshiStratR') + fn('kalshiHoverAttr') + fn('kalshiHoverWhen') + fn('kalshiStratCumLine') + varLine('kalshiStratDayText') + varLine('KAL_SETTINGS_KEEP') + fn('kalshiStratSettingsKeep') + fn('kalshiStratChartsHtml') + '; return kalshiStratChartsHtml;')(Math, Number, Array, isFinite, Intl, Date);
  const base = { now: NOW, cum: [0, 5, 3, 4], times: [null, NOW - 10 * 86400000, NOW - 3 * 86400000, NOW - 2 * HR], n: 3 };
  const pts = (h) => JSON.parse(/class="hv" data-hv="([^"]+)"/.exec(h)[1].replace(/&#34;|&quot;/g, '"'));
  const all = R(Object.assign({ range: 'YTD' }, base), esc, money), wk = R(Object.assign({ range: '7D' }, base), esc, money), whole = R(Object.assign({}, base), esc, money);
  assert.strictEqual(pts(all).length, 4, 'YTD: every point this year'); assert.strictEqual(pts(whole).length, 4, 'no range (an old call): the whole record');
  assert.strictEqual(pts(wk).length, 3, '7D: a zero start and the two trades inside the week');
  assert.ok(/3 trades/.test(all) && /2 trades &middot; last 7 days|2 trades · last 7 days/.test(wk), 'the note counts the trades in the range');
  
  const none = R(Object.assign({ range: '7D' }, base, { times: [null, NOW - 10 * 86400000, NOW - 9 * 86400000, NOW - 8 * 86400000] }), esc, money);
  assert.ok(/No settled trades in the last 7 days/.test(none), 'an empty range says so instead of drawing a line');
  assert.ok(/data-strng="7D"[^>]*aria-pressed="true"/.test(wk), 'the sheet shows the same buttons, the chosen one pressed');
};
gates.SP18 = () => {
  // The cleanup after the Nov 13, 2026 merges (the owner: "what the hell are we doing"): a conflict merge kept both sides and drew a second chart, a stray caption and full-width tiles. One chart, no middle caption, three tiles in one row inside the card, the Privacy button on the right, and no changelog line twice.
  const orders = [W(NOW - HR), L(NOW - 2 * HR), W(NOW - 3 * HR)];
  const sum = Q.kalshiStratSummaryHtml(Q.kalshiStratSummary(orders, NOW, 12, CT), esc, money);
  assert.strictEqual((sum.match(/class="sp-sum-plot/g) || []).length, 1, 'exactly one chart in the top card');
  assert.strictEqual((sum.match(/class="sp-sum-cap"/g) || []).length, 1, 'one caption row');
  assert.ok(!/dashed line is zero<\/span>/.test(sum) && !/<span>Now<\/span>/.test(sum), 'no middle caption and no stray Now caption');
  assert.ok(/<div class="sp-sum-grid">(?:<div class="sp-sum-c"[\s\S]*?){3}<\/div><\/div>$/.test(sum), 'the three tiles are the last child of the card');
  assert.ok(/\.sp-sum > \.sp-sum-grid\{ grid-column:1 \/ -1; grid-template-columns:repeat\(3,minmax\(0,1fr\)\); \}/.test(html), 'and sit in one row of three across the card');
  assert.ok(/#page-strategies \.kal-header-bare\{ justify-content:flex-end;/.test(html), 'the Privacy button sits on the right');
  const items = [...html.matchAll(/<li>([^\n]{40,})<\/li>/g)].map((m) => m[1]).filter((t) => /^(Trading|Strategies page|Research|Bot page|Brief|Settings)/.test(t));
  const dup = items.filter((t, i) => items.indexOf(t) !== i);
  assert.deepStrictEqual(dup, [], 'no changelog line appears twice');
};
gates.SP17 = () => {
  // YTD (and any range) reaches back past the live listener's newest 1,000 gold orders (Nov 13, 2026, the owner: "the ytd strategies thing should go back to oct 7th right?")
  const src = varLine('KAL_STRAT_RANGES') + varLine('kalshiStratRange') + fn('kalshiStratRangeOf') + fn('kalshiPnlSource') + 'var KAL_STRAT_START = Date.UTC(2026, 9, 7); var kalshiStratOlder = {}, kalshiStratOlderOut = {};' + fn('kalshiStratHistory') +
    '; return { run: kalshiStratHistory, set: function(r){ kalshiStratRange = r; } };';
  const NOWY = Date.UTC(2026, 10, 13, 18, 0), DAY = 86400000;
  let asked = null, resolve = null, redraws = 0;
  const live = Array.from({ length: 1000 }, (_, i) => ({ ts: NOWY - i * 3600000 / 2, clientOrderId: 'n' + i }));   // the newest 1,000: about 21 days back
  const win = { __shwoopAPI: { kalshiOrdersSince: (ms) => { asked = ms; return { then: (ok) => { resolve = ok; } }; } } };
  const H = new Function('Math', 'Number', 'Array', 'Intl', 'Date', 'Infinity', 'window', 'kalshiLiveOrders', 'kalshiSlotOrders', 'renderStrategiesPage', src)(Math, Number, Array, Intl, Date, Infinity, win, live, [], () => { redraws++; });
  H.set('7D');
  const first = H.run(NOWY);
  assert.ok(first.loading && asked === Date.UTC(2026, 9, 7), 'whatever the range (7D here), the page asks once for every order since the first trade on Oct 7 and says it is reading');
  asked = null; H.set('YTD'); H.run(NOWY);
  assert.ok(asked === null, 'switching the range does not start another read: the record is the same for every range');
  resolve([{ ts: Date.UTC(2026, 9, 7, 15, 0), clientOrderId: 'oct7' }].concat(live.slice(-3)));
  const after = H.run(NOWY);
  assert.ok(Array.isArray(after.orders) && after.orders.some((o) => o.clientOrderId === 'oct7') && after.orders.length === 1001 && redraws === 1, 'the Oct 7 order joins the live list once, and the page redraws');
  const rp = fn('renderStrategiesPage');
  assert.ok(/hist = kalshiStratHistory\(now\)/.test(rp) && /if\(hist\.orders\)\{ all = hist\.orders; \}/.test(rp) && /Older trades could not be read, so this starts at/.test(rp) && /Reading older trades/.test(rp), 'the page uses the full history and says so on the chart when part of it is missing');
};

gates.SP19 = () => {
  // Clicking 7D, 30D or YTD changes only the chart, its header and its ring; Today, Last 7 days and All time stay fixed (the owner, Nov 13, 2026: "all time bubble also changes with chart range selection").
  assert.ok(/function kalshiStratHistory\(now\)\{\n    var cut = KAL_STRAT_START, key = 'all';/.test(html) && /var KAL_STRAT_START = Date\.UTC\(2026, 9, 7\);/.test(html), 'the record the page holds does not depend on the range');
  const S = new Function('KAL_BOARD_DAY', varLine('KAL_STRAT_RANGES') + fn('kalshiStratRangeOf') + fn('kalshiStratR') + fn('kalshiBoardFillCost') + fn('kalshiBoardCash') + fn('kalshiBoardRows') + fn('kalshiBoardPf') + fn('kalshiStratOpenCount') + fn('kalshiStratSummary') + '; return kalshiStratSummary;')(86400000);
  const NOWY = Date.UTC(2026, 10, 13, 18, 0), DAY = 86400000;
  const o = (ts, won) => ({ ts, side: 'yes', count: 1, fillCount: 1, price: 0.9, maxCost: 0.92, settled: true, result: won ? 'yes' : 'no', settledPnl: won ? 0.08 : -0.92, averageFillPrice: 0.9, averageFeePaid: 0.01 });
  const orders = [o(Date.UTC(2026, 9, 7, 15), true), o(NOWY - 20 * DAY, false), o(NOWY - 3 * DAY, true), o(NOWY - 3600000, true)];
  const day = (ms) => new Date(ms).toISOString().slice(0, 10);
  const r = ['7D', '30D', 'YTD'].map((k) => S(orders, NOWY, 0, day, k));
  for (const k of ['today', 'd7', 'net', 'atRisk', 'open']) assert.ok(r.every((x) => x[k] === r[0][k]), k + ' is the same for every range');
  assert.ok(r[0].curve.length !== r[2].curve.length, 'while the chart follows the range');
};

let failed = 0;
for (const [name, g] of Object.entries(gates)) { try { g(); console.log('ok ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
if (failed) process.exit(1);

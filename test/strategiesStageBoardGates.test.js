'use strict';
// SB-STAGE: the Strategies page stage board (Nov 12, 2026, the owner: "build it into the live page"; the approved mockup ported onto real data). Each gate states the consequence.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>')).replace(/\/\*[\s\S]*?\*\//g, '');
const gates = {};
// Lift every function of the board's pure section and the vars it reads, so the real markup builder runs here.
const from = html.indexOf('  function kalshiBoardFillCost('), to = html.indexOf('  var kalshiRegistryLoading');
assert.ok(from > 0 && to > from);
const section = html.slice(from, to);
const varLine = (name) => { const m = new RegExp('  var ' + name + ' = .*\\n').exec(html); assert.ok(m, name); return m[0]; };
const varBlock = (name) => { const m = new RegExp('  var ' + name + ' = [\\[{][\\s\\S]*?\\n  [\\] }]+;\\n').exec(html); assert.ok(m, name); return m[0]; };
const pre = varLine('KAL_BOARD_TRIPWIRE') + varLine('KAL_BOARD_KILL') + varBlock('KAL_BOARD_LIVE') + varLine('KAL_BOARD_SHADOW_RULES') + varLine('KAL_BOARD_SHADOW') + varBlock('KAL_BOARD_RETIRED') + varLine('KAL_BOARD_LADDER') + varLine('KAL_BOARD_DAY') + varBlock('KAL_STAGES') + varLine('kalshiStratOpen') + varLine('kalshiStratDayText') + "var kalshiRegistry = { state: 'loading', list: [] }, kalshiRegData = {};\n";
const pf = html.slice(html.indexOf('  function kalshiStratPfAttr('), html.indexOf('  // The text shown t of the way through the count'));
const B = new Function('Intl', 'Date', 'Math', pre + section + pf + '; return { kalshiBoardHtml, KAL_BOARD_LIVE };')(Intl, Date, Math);
const money = (x) => (x < 0 ? '-' : '') + '$' + Math.abs(x).toFixed(2), esc = (s) => String(s).replace(/[&<>"']/g, (c) => '&#' + c.charCodeAt(0) + ';');
const reg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'strategies-registry.json'), 'utf8')).strategies;
const card = (id, lane, extra) => Object.assign({ id, name: id, lane, rule: 'rule of ' + id, rules: ['impl', 'kill rule', 'return rule'], w: { d7: { n: 1, net: 1 }, d30: { n: 12, pf: 1.4, net: 2 }, all: { n: 12 } }, kill: { lines: ['x'], count: 5, streak: 3, net: -1, floorOn: true, floorRoom: 5 }, spark: [], detail: null, today: 0 }, extra || {});
const model = (live, extra) => Object.assign({ live, deck: { state: 'ok', rows: [] }, retired: { rows: [], back: 'b', asOf: 'a' }, registryList: reg, registryState: 'ok', now: Date.UTC(2026, 10, 12, 18) }, extra || {});
const panel = (h, k) => new RegExp('<section class="lp-p" id="lp-p-' + k + '"[\\s\\S]*?</section>').exec(h)[0];

// ST1: a killed strategy is never in Live; its row reads cooling down and carries its return progress; a tripped kill moves it the moment the state says so.
gates.ST1 = () => {
  const h = B.kalshiBoardHtml(model([card('L1', 'off', { killState: 'killed', ret: { trades: 20, losses: 3, days: 2, pf: 1.1, frac: 0.2 } }), card('OICORE', 'live')]), esc, money);
  assert.ok(!/data-row="L1"/.test(panel(h, 'live')) && /data-row="L1"/.test(panel(h, 'off')) && /data-row="OICORE"/.test(panel(h, 'live')));
  assert.ok(/COOLING/.test(panel(h, 'off')) && /20 of 60 trades/.test(panel(h, 'off')));
};
// ST2: the count on every box equals the strategies in its panel, and the header line repeats the same counts.
gates.ST2 = () => {
  const live = [card('L1', 'live'), card('A', 'live'), card('B', 'probation')];
  const h = B.kalshiBoardHtml(model(live), esc, money);
  const cnt = (k) => Number(new RegExp('data-stage="' + k + '"[^>]*><b data-count="(\\d+)"').exec(h)[1]);
  const rows = (k) => (panel(h, k).match(/class="rw(?: open)?(?: near)?"/g) || []).length;
  for (const k of ['shadow', 'live']) assert.strictEqual(cnt(k), rows(k), k);
  assert.ok(new RegExp('<b>' + cnt('shadow') + '</b> shadow &middot; <b>' + cnt('live') + '</b> live \\(1 on trial\\)').test(h), 'one Live box (Nov 13, 2026): the header counts the trial seats inside it');
};
// ST3: a strategy whose kill state is unknown or still loading never reads HEALTHY and says the state is not readable; a known healthy one still can.
gates.ST3 = () => {
  for (const ks of ['unknown', 'loading']) {
    const h = B.kalshiBoardHtml(model([card('L1', 'live', { killState: ks, w: { d7: { n: 0, net: 0 }, d30: { n: 40, pf: 1.4, net: 2 }, all: { n: 40 } } })]), esc, money);
    assert.ok(!/HEALTHY/.test(h), ks + ' is never healthy');
    assert.ok(ks === 'unknown' ? /Kill state not readable/.test(h) && /STATE UNKNOWN/.test(h) : /Reading the kill state/.test(h) && /CHECKING/.test(h));
    assert.ok(!/class="rw[^"]*near/.test(h), 'and it is never marked nearest its kill');
  }
};
// ST4: only the strategy nearest its kill pulses, and only when something is used.
gates.ST4 = () => {
  const h = B.kalshiBoardHtml(model([card('A', 'live', { kill: { lines: ['x'], count: 5 } }), card('OICORE', 'live', { kill: { lines: ['x'], streak: 20, net: 1, floorOn: false, floorRoom: 5 } })]), esc, money);
  assert.strictEqual((h.match(/class="rw near"/g) || []).length, 1);
  assert.ok(/class="rw near"[^>]*data-fk="row:OICORE"/.test(h));
  const none = B.kalshiBoardHtml(model([card('OICORE', 'live', { kill: { lines: ['x'], streak: 0, net: 0, floorOn: false, floorRoom: 5 } })]), esc, money);
  assert.ok(!/class="rw near"/.test(none));
};
// ST5: no sample or invented text is in the live page, and no figure of the mockup (its invented numbers) is in the page code.
gates.ST5 = () => {
  const board = html.slice(html.indexOf('  // ---- Stage board'), html.indexOf('  var kalshiRegistryLoading')) + html.slice(html.indexOf('id="page-strategies"'), html.indexOf('id="page-settings"'));
  assert.ok(!/SAMPLE|Invented numbers|invented to show|Preview<|sample data/i.test(board), 'no sample note');
  assert.ok(!/\b(?:5,892|88,420|20,611|212|\$74|\$31 of room|\+\$18)\b/.test(board), 'none of the mockup figures');
  assert.ok(!/Promoted 2 days ago/.test(html), 'no invented promotion label');
};
// ST6: a promotion label needs a real registry date; none of the registry rows has one today, so the page shows none.
gates.ST6 = () => {
  assert.ok(reg.every((x) => !('promotedOn' in x && x.promotedOn)), 'no row carries a promotion date yet');
  assert.ok(!/class="lp-tag"/.test(B.kalshiBoardHtml(model([card('A', 'probation')]), esc, money)));
  const h = B.kalshiBoardHtml(model([card('A', 'probation')], { registryList: [{ id: 'A', name: 'A', stage: 'Probe', promotedOn: '2026-11-10' }] }), esc, money);
  assert.ok(/<u class="lp-tag">Promoted 2 days ago: A<\/u>/.test(h), 'with a real date it says how long ago');
};
// ST7: reduced motion freezes the board, both ways: the loop's flowing dots, the drifting grid, the pulse, the entrance, the fills and the open and close transitions are off under the OS setting and the Settings switch, and the JS glide never starts.
gates.ST7 = () => {
  const media = /@media \(prefers-reduced-motion: reduce\)\{([\s\S]*?)\n  \}/.exec(css)[1];
  const attr = css.split('\n').filter((l) => l.includes('[data-reduce-motion="true"]')).join('\n');
  for (const s of ['#page-strategies .lp::before', '#page-strategies .lp-ln u', '#page-strategies .lp-ret u', '#page-strategies .lp-p.play .rw', '#page-strategies .rw.near .rw-w::before', '#page-strategies .rw.open .sp-bar i', '#page-strategies .sx', '#page-strategies .lp-t', '#page-strategies.sp-play .lp-t']) {
    assert.ok(media.includes(s), 'prefers-reduced-motion stops ' + s);
    assert.ok(attr.includes(s), 'the Settings switch stops ' + s);
  }
  const fn = html.slice(html.indexOf('  function kalshiStratStage('), html.indexOf('  (function(){', html.indexOf('  function kalshiStratStage(')));
  assert.ok(/if\(panel && !motionReduced\(\)\)/.test(fn) && /if\(motionReduced\(\)\)\{ return; \}/.test(fn), 'no play class, no slide and no panel animation under reduced motion');
};
// ST8: keyboard. Every box and row is a button with aria-expanded and aria-controls; a redraw keeps the focused control; the closed panels are hidden.
gates.ST8 = () => {
  const h = B.kalshiBoardHtml(model([card('A', 'live')]), esc, money);
  assert.strictEqual((h.match(/<button type="button" class="lp-t[^"]*"[^>]*aria-expanded="false" aria-controls="lp-p-/g) || []).length, 3);
  assert.ok(/<button type="button" class="rw-h"[^>]*aria-expanded="false" aria-controls="rwd-live-0"/.test(h) && /id="rwd-live-0"/.test(h));
  assert.ok(/<button type="button" class="mo-b"[^>]*aria-expanded="false"/.test(h));
  assert.strictEqual((h.match(/<section class="lp-p"[^>]* hidden>/g) || []).length, 3, 'nothing open: every panel hidden');
  const render = html.slice(html.indexOf('  function renderStrategiesPage('), html.indexOf('  // The Details popup lives outside'));
  assert.ok(/getAttribute\('data-f'\)/.test(render) && /\.focus\(\)/.test(render), 'a redraw puts focus back on the same control');
  assert.ok(!/<(?:div|span|b) [^>]*onclick/.test(h));
};
// ST9: privacy and escaping. Dollars go through money; a hostile name or rule never becomes markup.
gates.ST9 = () => {
  const h = B.kalshiBoardHtml(model([card('<i>', 'live', { name: '<img src=x onerror=1>', rule: '"><script>', today: 5, w: { d7: { n: 1, net: 7 }, d30: { n: 12, pf: 1.4, net: 2 }, all: { n: 12 } } })]), esc, (x) => '****');
  assert.ok(!/<img|<script|<i>/.test(h) && /&#60;img/.test(h));
  assert.ok(/Today <b>\+\*\*\*\*<\/b>/.test(h) && !/\$\d/.test(h.replace(/<dd>[^<]*<\/dd>/g, '').replace(/ title="[^"]*"/g, '').replace(/<span class="bd-w"[^>]*>[^<]*<\/span>/g, '')));
};
// ST10: the board has no network, storage or write: only the open state kept in memory and the one timeout that ends the entrance play.
gates.ST10 = () => {
  const code = html.slice(html.indexOf('  // ---- Stage board'), html.indexOf('  var kalshiRegistryLoading')) + html.slice(html.indexOf('  function kalshiStratStage('), html.indexOf('  var kalshiLiveOrders = [];'));
  assert.ok(!/localStorage|sessionStorage|fetch\(|XMLHttpRequest|setDoc|updateDoc|addDoc|setInterval|https?:\/\//.test(code));
  assert.strictEqual((code.match(/setTimeout\(/g) || []).length, 1, 'one timeout, the entrance play');
  assert.ok(!code.includes(String.fromCharCode(8212)), 'no em dash');
};
let failed = 0;
for (const [name, g] of Object.entries(gates)) { try { g(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
process.exit(failed ? 1 : 0);

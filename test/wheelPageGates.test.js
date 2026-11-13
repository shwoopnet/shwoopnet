'use strict';
// WP: the Wheel view on the Strategies page (Nov 13, 2026, rotation lane piece F). Each gate states the consequence.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>')).replace(/\/\*[\s\S]*?\*\//g, '');
const reg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'strategies-registry.json'), 'utf8')).strategies;
const gates = {};
const from = html.indexOf('  var KAL_WHEEL_SEATS'), to = html.indexOf('  function kalshiBoardHtml(');
assert.ok(from > 0 && to > from);
const W = new Function(html.slice(from, to) + '; return { kalshiWheelHtml, kalshiWheelStatus, kalshiWheelDay, KAL_WHEEL_SEATS };')();
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => '&#' + c.charCodeAt(0) + ';');
const now = Date.UTC(2026, 10, 14, 12);
const draw = (list, st) => W.kalshiWheelHtml({ registryList: list, registryState: st || 'ok', now, open: {} }, esc);
const wh = reg.filter((r) => r.id.indexOf('WH-') === 0);

// WP1: every wheel place in the registry is on the page, so a place the Head admits is never silently missing.
gates.WP1 = () => { assert.ok(wh.length >= 19); const h = draw(reg); for (const r of wh) assert.ok(h.includes('data-k="wh:' + r.id + '"'), r.id); assert.ok(!/data-k="wh:(?!WH-)/.test(h)); };
// WP2: the block is labelled unproven, and the seat boxes read 0 with the owner's-popup line: nothing here suggests a live seat.
gates.WP2 = () => { const h = draw(reg); assert.ok(/Rotating \(unproven\)/.test(h) && />0 of 5<\/b><span>Probation seats/.test(h) && />0<\/b><span>Full seats/.test(h) && /No seat is live; each seat needs the owner's popup/.test(h)); assert.deepStrictEqual(Object.assign({}, W.KAL_WHEEL_SEATS), { probation: 0, probationMax: 5, full: 0 }); };
// WP3: no invented count: "n of 60 signals" appears only for a row that states n; every shipped row says the count is read from the private log.
gates.WP3 = () => { assert.ok(wh.every((r) => r.n === null)); const h = draw(reg); assert.ok(!/of 60 signals/.test(h) && /Count read from the private log/.test(h)); const one = draw([Object.assign({}, wh[6], { n: 12 })]); assert.ok(/12 of 60 signals/.test(one)); };
// WP4: status words follow the registry text: counting places say Counting since the date with a day toward 7, mute and waiting places never read as counting, retired places carry their cause.
gates.WP4 = () => {
  const by = (id) => reg.find((r) => r.id === id);
  assert.strictEqual(W.kalshiWheelStatus(by('WH-NC15-SILVER')).key, 'counting');
  for (const id of ['WH-CFRTIK-BTC', 'WH-CFRTIK-SILVER', 'WH-IPJ-TT', 'WH-ESOCTIE']) assert.strictEqual(W.kalshiWheelStatus(by(id)).key, 'waiting', id);
  assert.strictEqual(W.kalshiWheelStatus(by('WH-NC15-EURUSD')).key, 'retired');
  const h = draw(reg); assert.ok(/Counting since 2026-11-13/.test(h) && /day 1 of 7/.test(h) && /Retired on 2026-11-13: failed the bar/.test(h));
  assert.strictEqual(W.kalshiWheelDay('2026-11-13', Date.UTC(2026, 10, 30)), 7); assert.strictEqual(W.kalshiWheelDay(null, now), null);
};
// WP5: honest empty states: no rows says so, a loading or unreadable list says that, and nothing is drawn as a number.
gates.WP5 = () => { assert.ok(/No wheel places are in the strategy list/.test(draw([]))); assert.ok(/Reading the strategy list/.test(draw([], 'loading'))); assert.ok(/could not be read/.test(draw([], 'unreadable'))); assert.ok(!/<svg/.test(draw(reg)), 'no chart is drawn for wheel places'); };
// WP6: every registry string is escaped, and no profit factor or dollar figure is drawn for a place.
gates.WP6 = () => {
  const x = Object.assign({}, wh[0], { id: 'WH-X', name: '<img src=x onerror=1>', rule: '"><script>', kill: '<b>', 'return': '<i>', nextReadText: 'Counting <u>', cause: '<s>' });
  const h = draw([x]);
  assert.ok(/&#60;img/.test(h) && /&#60;script/.test(h) && !/<img|<script/.test(h));
  assert.ok(!/\$\d/.test(draw(reg)) && !/sp-ring|data-pf/.test(draw(reg)), 'no dollar figure and no profit factor ring');
};
// WP7: page-only: the wheel code adds no host, storage, network call, timer or Firestore read, no em dash, and wheel rows leave the stage board so no place shows twice; the phone CSS has no fixed width that could scroll sideways at 360px.
gates.WP7 = () => {
  const code = html.slice(from, to);
  assert.ok(!/localStorage|sessionStorage|fetch\(|XMLHttpRequest|setDoc|updateDoc|addDoc|getDoc|onSnapshot|setInterval|setTimeout|https?:\/\//.test(code));
  assert.ok(!code.includes(String.fromCharCode(8212)));
  assert.ok(/String\(x\.id\)\.indexOf\('WH-'\) !== 0 && \['Idea'/.test(html) && /x\.id\.indexOf\('WH-'\) !== 0; \}\);\s+\/\/ the wheel's retired/.test(html));
  const wcss = css.split('\n').filter((l) => /\.wh(?:-|\b)/.test(l)).join('\n');
  assert.ok(wcss.length > 200 && !/\bwidth:\s*\d{3,}px|min-width:\s*[2-9]\d{2,}px|white-space:nowrap/.test(wcss), 'no wide fixed widths or nowrap');
  assert.ok(/overflow-wrap:anywhere/.test(wcss) && /minmax\(130px/.test(wcss));
};
let failed = 0;
for (const [name, g] of Object.entries(gates)) { try { g(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
process.exit(failed ? 1 : 0);

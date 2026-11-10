'use strict';
// Strategies page animation (Nov 10, 2026, the owner's explicit exception to "no count-up on a figure", limited to this page's profit factor figures). Each gate states the consequence.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>')).replace(/\/\*[\s\S]*?\*\//g, '');
const gates = {};
function fnSource(name) {
  const start = html.indexOf('function ' + name + '(');
  assert.ok(start >= 0, name + ' exists');
  let i = html.indexOf('{', html.indexOf(')', start)), depth = 0;
  for (; i < html.length; i++) { if (html[i] === '{') depth++; else if (html[i] === '}' && --depth === 0) return html.slice(start, i + 1); }
  throw new Error('unbalanced ' + name);
}
const fenced = (/\/\* STRAT-ANIM-BEGIN[\s\S]*?STRAT-ANIM-END \*\//.exec(html) || [''])[0];
const escapeHtml = (x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const lib = new Function('escapeHtml', fnSource('kalshiStratEase') + fnSource('kalshiStratPfAttr') + fnSource('kalshiStratCountText') + 'return {kalshiStratEase,kalshiStratPfAttr,kalshiStratCountText};')(escapeHtml);

// SA1: the count never shows a number past the true one and ends exactly on it. IF THIS FAILS: a profit factor on screen could be wrong while it counts.
gates.SA1 = () => {
  assert.strictEqual(lib.kalshiStratEase(0), 0); assert.strictEqual(lib.kalshiStratEase(1), 1);
  assert.strictEqual(lib.kalshiStratEase(-3), 0); assert.strictEqual(lib.kalshiStratEase(9), 1); assert.strictEqual(lib.kalshiStratEase(NaN), 0);
  let prev = -1;
  for (let i = 0; i <= 100; i++) { const e = lib.kalshiStratEase(i / 100); assert.ok(e >= prev && e <= 1, 'monotonic and never past 1'); prev = e; }
};
gates.SA2 = () => {
  assert.strictEqual(lib.kalshiStratCountText('1.23', 0), '0.00');
  assert.strictEqual(lib.kalshiStratCountText('1.23', 1), '1.23', 'the end is the true text itself');
  assert.strictEqual(lib.kalshiStratCountText('0.10', 1.5), '0.10');
  for (let i = 0; i < 100; i++) assert.ok(parseFloat(lib.kalshiStratCountText('1.80', i / 100)) <= 1.8);
};
// SA3: only plain numbers carry data-pf; the true value is in the aria-label; words never animate.
gates.SA3 = () => {
  const a = lib.kalshiStratPfAttr('1.23', escapeHtml);
  assert.ok(/data-pf="1\.23"/.test(a) && /aria-label="Cash profit factor 1\.23"/.test(a) && /role="img"/.test(a));
  for (const t of ['n/a', 'no losses', '', '1.2', '<b>1.23', '12345.00']) assert.strictEqual(lib.kalshiStratPfAttr(t, escapeHtml), '', JSON.stringify(t));
};
// SA4: the markup holds the true text at rest, the figure is escaped.
gates.SA4 = () => {
  assert.ok(/<b class="sp-c-pf"' \+ kalshiStratPfAttr\(o\.pf, esc\) \+ '>' \+ esc\(o\.pf\) \+ '<\/b>/.test(html), 'tile figure: attribute and escaped true text');
  assert.ok(/<b' \+ kalshiStratPfAttr\(pf, esc\) \+ '>' \+ esc\(pf\) \+ '<\/b>/.test(html), 'summary figure likewise');
  assert.strictEqual((html.match(/data-pf=/g) || []).length, 1, 'data-pf is written in one helper only, which both Strategies figures call');
};
// SA5: scope. Every animation hook is on #page-strategies or inside the fenced block; no figure elsewhere is touched.
gates.SA5 = () => {
  assert.ok(fenced.length > 500, 'fenced block exists');
  const outside = html.replace(fenced, '');
  assert.ok(!/requestAnimationFrame[\s\S]{0,400}data-pf|data-pf[\s\S]{0,400}requestAnimationFrame/.test(outside), 'no frame loop outside the fenced block touches a figure');
  const rules = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].filter((m) => /sp-play|spBar|spChip|spArrow/.test(m[1] + m[2]));
  assert.ok(rules.length >= 8);
  rules.forEach((m) => { if (!/^\s*@keyframes/.test(m[1])) assert.ok(/#page-strategies\.sp-play/.test(m[1]), 'animation selector scoped to the Strategies page: ' + m[1].trim()); });
  const pagesJs = fenced.match(/querySelectorAll\('([^']+)'\)/g);
  pagesJs.forEach((q) => assert.ok(/#stratBody \[data-pf\]/.test(q), 'the count only reads #stratBody [data-pf]: ' + q));
};
// SA6: reduced motion off switch, both ways, and nothing starts in JS either.
gates.SA6 = () => {
  const sels = [...css.matchAll(/(#page-strategies\.sp-play[^,{]*)/g)].map((m) => m[1].trim());
  const media = /@media \(prefers-reduced-motion: reduce\)\{([\s\S]*?)\n  \}/.exec(css)[1];
  const attr = css.split('\n').filter((l) => l.includes('[data-reduce-motion="true"]')).join('\n');
  const uniq = [...new Set(sels)];
  assert.ok(uniq.length >= 8);
  uniq.forEach((s) => { assert.ok(media.includes(s), 'prefers-reduced-motion disables ' + s); assert.ok(attr.includes(s), 'the Settings switch disables ' + s); });
  assert.ok(/if\(!page \|\| motionReduced\(\)\)\{ return; \}/.test(fenced), 'start returns before touching anything when motion is reduced');
};
// SA7: behaviour under reduced motion and normally, with fakes.
function harness(reduced) {
  const log = { raf: 0, cancels: 0, timers: [], cleared: 0 };
  const figs = [{ t: '1.23', textContent: '1.23', getAttribute() { return '1.23'; } }];
  const cls = new Set();
  const page = { offsetWidth: 1, classList: { add: (c) => cls.add(c), remove: (c) => cls.delete(c) }, querySelectorAll: () => figs };
  let rafCb = null;
  const src = 'var motionReduced = function(){ return ' + reduced + '; };\n' + fenced.replace(/\/\*[\s\S]*?\*\//, '') + '\nreturn { anim: kalshiStratAnim, start: kalshiStratAnimStart, stop: kalshiStratAnimStop };';
  const api = new Function('requestAnimationFrame', 'cancelAnimationFrame', 'setTimeout', 'clearTimeout', 'escapeHtml', src)(
    (cb) => { log.raf++; rafCb = cb; return 7; }, () => { log.cancels++; }, (fn, ms) => { log.timers.push([fn, ms]); return 9; }, () => { log.cleared++; }, escapeHtml);
  return { api, page, figs, cls, log, step: (now) => { const cb = rafCb; rafCb = null; if (cb) cb(now); } };
}
gates.SA7 = () => {
  const h = harness(true);
  h.api.start(h.page);
  assert.strictEqual(h.log.raf, 0, 'no frame requested'); assert.strictEqual(h.log.timers.length, 0, 'no timer'); assert.ok(!h.cls.has('sp-play'), 'no class'); assert.strictEqual(h.figs[0].textContent, '1.23', 'true value shown at once');
};
gates.SA8 = () => {
  const h = harness(false);
  h.api.start(h.page);
  assert.ok(h.cls.has('sp-play')); assert.strictEqual(h.figs[0].textContent, '0.00', 'starts at zero'); assert.strictEqual(h.log.timers.length, 1);
  h.step(1000); h.step(1350);
  const mid = parseFloat(h.figs[0].textContent); assert.ok(mid > 0 && mid < 1.23, 'mid count ' + mid);
  h.step(1700);
  assert.strictEqual(h.figs[0].textContent, '1.23', 'ends on the true text'); assert.strictEqual(h.log.raf, 4 - 1, 'the loop stops itself after the last frame');
  const before = h.log.raf; h.step(2000); assert.strictEqual(h.log.raf, before, 'nothing running after it finished');
  h.log.timers[0][0](); assert.ok(!h.cls.has('sp-play'), 'class cleared by the one timeout');
};
// SA9: stop (a redraw, leaving the page) cancels the loop and the timeout and restores the true text.
gates.SA9 = () => {
  const h = harness(false);
  h.api.start(h.page); h.step(1000); h.step(1200);
  h.figs[0].textContent = '0.40';
  h.api.stop(h.page);
  assert.ok(h.log.cancels >= 1 && h.log.cleared >= 1); assert.strictEqual(h.figs[0].textContent, '1.23'); assert.ok(!h.cls.has('sp-play'));
};
// SA10: one shot per show. showPage sets pending, a redraw consumes it once and never starts a play by itself; leaving cancels.
gates.SA10 = () => {
  const showPage = fnSource('showPage'), render = fnSource('renderStrategiesPage');
  assert.ok(/name === 'strategies'\)\{ kalshiStratAnim\.pending = true; renderStrategiesPage\(\); \} else \{ kalshiStratAnim\.pending = false; kalshiStratAnimStop/.test(showPage), 'showPage arms it on entry and clears it when leaving');
  assert.strictEqual((html.match(/kalshiStratAnim\.pending = true/g) || []).length, 1, 'only showPage arms it');
  assert.ok(/kalshiStratAnimStop\(page\);\s*if\(kalshiStratAnim\.pending && \(kalshiShadowCache\.rows \|\| kalshiShadowCache\.error\)\)\{ kalshiStratAnim\.pending = false; kalshiStratAnimStart\(page\); \}/.test(render), 'a redraw stops, then plays only if pending, and consumes the flag');
  assert.strictEqual((html.match(/kalshiStratAnimStart\(/g) || []).length, 2, 'start is defined once and called once');
};
// SA11: light on phones and nothing left running: no interval, only transform, opacity and stroke-dashoffset in the keyframes, no layout property.
gates.SA11 = () => {
  assert.ok(!/setInterval/.test(fenced), 'no setInterval');
  assert.strictEqual((fenced.match(/requestAnimationFrame\(/g) || []).length, 2, 'the frame loop only');
  assert.ok(!/localStorage|fetch\(|XMLHttpRequest|addEventListener|onSnapshot/.test(fenced), 'no storage, network or listener');
  for (const name of ['spBar', 'spChip', 'spArrow']) {
    const m = new RegExp('@keyframes ' + name + '\\{([\\s\\S]*?)\\}\\s*(?=@|#|\\.|\\n)').exec(css);
    assert.ok(m, name); assert.ok(!/(content|font-size|width|height|top|left|margin|padding)\s*:/.test(m[1]), name + ' moves only transform or opacity');
  }
  assert.ok(/#page-strategies\.sp-play \.sp-arc\{[^}]*lineDraw/.test(css) && /#page-strategies\.sp-play \.sp-spk\{[^}]*lineDraw/.test(css), 'gauges and lines use the stroke draw');
  assert.ok(!/(black|white|rgba?\(|#[0-9a-f]{3,6}|box-shadow|glow)/i.test(css.slice(css.indexOf('@keyframes spBar'), css.indexOf('@keyframes spArrow') + 200)), 'no colour or glow in the animation');
};
// SA12: gauge dash math. The arc is drawn with pathLength 1 so lineDraw (dashoffset 1 to 0) draws exactly the value arc; the arc ends where the fraction says.
gates.SA12 = () => {
  const arc = new Function(fnSource('kalshiStratArc') + 'return kalshiStratArc;')();
  assert.strictEqual(arc(0), ''); assert.strictEqual(arc(1), 'M 10 60 A 50 50 0 0 1 110 60');
  assert.strictEqual(arc(0.5), 'M 10 60 A 50 50 0 0 1 60 10');
  assert.ok(/<path class="sp-arc" pathLength="1" d="' \+ arc/.test(html), 'the value arc has pathLength 1');
  assert.ok(/<path class="sp-spk" pathLength="1"/.test(html), 'the trend line has pathLength 1');
  assert.ok(/@keyframes lineDraw\{ from\{ stroke-dashoffset:1; \} to\{ stroke-dashoffset:0; \} \}/.test(css), 'draw goes from fully hidden to fully drawn');
  assert.ok(/\.sp-bar i\{[^}]*scaleX|@keyframes spBar\{ from\{ transform:scaleX\(0\); \} to\{ transform:none; \} \}/.test(css), 'bars grow from empty to their width');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);

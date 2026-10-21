'use strict';
// Bubble pop (Oct 21, 2026, the owner: "more visual appeal and interactivity", with the bubbly wordmark font). Motion on a page that places real orders is decoration only: it never moves a number and it always stops
// when asked to. Each gate states the consequence.
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
  for (; i < html.length; i++) {
    if (html[i] === '{') depth++;
    else if (html[i] === '}' && --depth === 0) return html.slice(start, i + 1);
  }
  throw new Error('unbalanced ' + name);
}

// The headings and market names (words) use the wordmark's font; every NUMBER stays in the plain font, tabular, so figures like 774.14 stay easy to read (the owner, Oct 21, 2026).
gates.P1 = () => {
  // Titan One is the wordmark and its ghost only (the owner, Oct 21, 2026): headings and market names are in the plain font too, with no bubble shadow.
  for (const sel of ['.trades-title', '.kal-card-title', '.brief-section-title', '.kal-brow-name', '.kal-tools-h', '.settings-section-title']) {
    const m = new RegExp('(^|\\n)\\s*' + sel.replace(/[.]/g, '\\.') + '\\{([^}]*)\\}').exec(css);
    assert.ok(m && !/Titan One/.test(m[2]) && /Public Sans/.test(m[2]) && !/text-shadow/.test(m[2]), sel + ' is in the plain font with no bubble shadow');
  }
  const users = css.split('\n').filter((l) => /Titan One/.test(l) && !/^\s*(\/\*|\*)/.test(l));
  assert.ok(users.length <= 2 && users.every((l) => /\.brand-name|font-size:min\(18vw/.test(l) || /bg-ghost/.test(css)), 'only the wordmark and its ghost use Titan One: ' + users.map((l) => l.trim().slice(0, 50)).join(' | '));
  for (const sel of ['.kal-tile b', '.kal-bub', '.index-card .ix-val', '.kal-acct-total']) {
    const m = new RegExp('(^|\\n)\\s*' + sel.replace(/[.]/g, '\\.') + '\\{([^}]*)\\}').exec(css);
    assert.ok(m && !/Titan One/.test(m[2]) && /Public Sans/.test(m[2]), sel + ' (a number) is in the plain font');
    if (sel !== '.kal-acct-total') assert.ok(/tabular-nums/.test(m[2]), sel + ' uses tabular digits');
  }
  assert.ok(!/\.kal-perf-row[^{]*\{[^}]*Titan One/.test(css) && !/\.data-row[^{]*\{[^}]*Titan One/.test(css), 'table rows stay in the plain font');
};

// No number is ever animated: there is no count-up, and no keyframe touches text content. The only keyframes added are a rise, a line draw and a mark pop, on transform, opacity and stroke-dashoffset.
gates.P2 = () => {
  for (const name of ['cardRise', 'lineDraw', 'markPop']) {
    const m = new RegExp('@keyframes ' + name + '\\{([\\s\\S]*?)\\}\\s*(?=@|\\.|\\n)').exec(css);
    assert.ok(m, name + ' exists');
    assert.ok(!/(content|font-size|width|height|top|left|margin|padding)\s*:/.test(m[1].replace(/animation-timing-function[^;]*;/g, '')), name + ' only moves transform, opacity or the stroke');
  }
  assert.ok(!/requestAnimationFrame[\s\S]{0,300}textContent|countUp|count-up|\btween\b/i.test(html), 'no number counts up');
};

// A page's entrance plays once per show: the class is taken off after the animation, so the minute's re-render of a chart or a card never replays it, and nothing is added when motion is reduced.
gates.P3 = () => {
  const make = (reduced) => {
    const calls = { timers: [] };
    const doc = { documentElement: { getAttribute: (k) => (k === 'data-reduce-motion' && reduced ? 'true' : null) } };
    const win = { matchMedia: () => ({ matches: false }) };
    const el = { cls: new Set(), offsetWidth: 1, classList: { add(c) { el.cls.add(c); }, remove(c) { el.cls.delete(c); } }, querySelectorAll: () => [{ style: { setProperty(k, v) { calls.set = (calls.set || []).concat([[k, v]]); } } }] };
    const f = new Function('document', 'window', 'setTimeout', 'clearTimeout', 'var pageEnterTimer = null;\n' + fnSource('motionReduced') + '\n' + fnSource('pageEnter') + '; return pageEnter;')(doc, win, (fn, ms) => { calls.timers.push([fn, ms]); return calls.timers.length; }, () => {});
    return { f, el, calls };
  };
  const a = make(false);
  a.f(a.el);
  assert.ok(a.el.cls.has('enter'), 'the class is added');
  assert.deepStrictEqual(a.calls.set, [['--i', '0']], 'each card gets its place in the stagger');
  assert.ok(a.calls.timers.length === 1 && a.calls.timers[0][1] >= 1500 && a.calls.timers[0][1] <= 3000, 'and taken off after the animation');
  a.calls.timers[0][0]();
  assert.ok(!a.el.cls.has('enter'), 'so a re-render later does not replay it');
  const r = make(true);
  r.f(r.el);
  assert.ok(!r.el.cls.has('enter') && !r.calls.timers.length, 'nothing happens when motion is reduced');
};

// The cursor spotlight was removed on Oct 21, 2026 at the owner's request: no pointer listener, no --mx/--my, no gradient on cards.
gates.P4 = () => {
  assert.ok(!/document\.addEventListener\('pointer(move|out)'/.test(html), 'no page-wide pointer listener (the chart hover tip listens on its own box only)');
  assert.ok(!/--mx|--my|--spot/.test(html), 'no cursor light variables');
};

// Hover lift and the entrance are switched off by both reduce-motion routes (the OS setting and the Settings switch).
gates.P5 = () => {
  const media = /@media \(prefers-reduced-motion: reduce\)\{([\s\S]*?)\n  \}/.exec(css)[1];
  for (const sel of ['.page.enter .kal-card', '.page.enter .kal-chart svg path[pathLength]', '.page.enter .kal-chart svg rect[data-mark]', '.kal-card:hover', '.kal-tile:hover', '.data-bar:hover']) {
    assert.ok(media.includes(sel), sel + ' is off under prefers-reduced-motion');
    assert.ok(css.includes('[data-reduce-motion="true"] ' + sel), sel + ' is off under the Settings switch');
  }
};

// Limit graphics is the old reduce-motion switch under a wider name: one stored setting, and it also removes the glow, the grid and the ghost wordmark.
gates.P6 = () => {
  assert.ok(/<div class="settings-row-title">Limit graphics<\/div>/.test(html) && !/<div class="settings-row-title">Reduce motion<\/div>/.test(html), 'the Settings row says Limit graphics');
  for (const sel of ['.bg-ghost', '.bg-grid', '.bg-ambient::before']) assert.ok(css.includes('[data-reduce-motion="true"] ' + sel), sel + ' is dropped when graphics are limited');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

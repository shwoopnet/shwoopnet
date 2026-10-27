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
// BG1: the slogan wallpaper is behind every signed-in page, can never be read as content or clicked, carries no figure, and switches off with Limit graphics.
gates.BG1 = () => {
  const m = /<div class="bg-slogan" aria-hidden="true">([\s\S]*?)<\/div>/.exec(html);
  assert.ok(m, 'the slogan layer exists once, hidden from screen readers');
  assert.strictEqual((html.match(/class="bg-slogan"/g) || []).length, 1, 'only once, outside every page, so it is the same on all of them');
  assert.ok(html.indexOf('class="bg-slogan"') < html.indexOf('id="page-brief"'), 'it sits before the pages, not inside one');
  assert.ok(/^(\s*<p>(Trade less\. Live more\. )+Trade less\. Live more\.<\/p>\s*)+$/.test(m[1]) && !/\d/.test(m[1]), 'it says only the slogan, no figure');
  const rule = /\.bg-slogan\{([^}]*)\}/.exec(css)[1];
  assert.ok(/position:fixed/.test(rule) && /z-index:-1/.test(rule) && /pointer-events:none/.test(rule), 'fixed behind the content, never catching a click');
  assert.ok(/color:rgba\(255,255,255,\.0[1-6]\d*\)/.test(rule), 'very faint, white at 6 percent or less');
  assert.ok(/\[data-reduce-motion="true"\] \.bg-slogan\{ display:none; \}/.test(css), 'off with the Limit graphics setting');
};

// BG2: the same slogan wallpaper sits behind the sign-in screen (the owner, Oct 25, 2026), as faint as the one behind the pages, inside the gate so it scrolls with nothing and covers no control.
gates.BG2 = () => {
  const gate = html.slice(html.indexOf('<div class="auth-gate" id="authGate">'), html.indexOf('</div>', html.indexOf('class="gate-slogan"')) + 6);
  assert.ok(/<div class="auth-gate" id="authGate">\s*<div class="gate-slogan" aria-hidden="true">/.test(gate), 'the first thing inside the gate, hidden from screen readers');
  const inner = /<div class="gate-slogan" aria-hidden="true">([\s\S]*?)<\/div>/.exec(html)[1];
  assert.ok(/^(\s*<p>(Trade less\. Live more\. )+Trade less\. Live more\.<\/p>\s*)+$/.test(inner) && !/\d/.test(inner), 'it says only the slogan, no figure');
  const rule = /\.gate-slogan\{([^}]*)\}/.exec(css)[1], pageRule = /\.bg-slogan\{([^}]*)\}/.exec(css)[1];
  assert.strictEqual(rule, pageRule, 'exactly the same look as the one behind the pages: same size, tilt and faintness');
  assert.ok(/pointer-events:none/.test(rule) && /z-index:-1/.test(rule), 'it never catches a click and sits behind the sign-in content');
  assert.ok(/\[data-reduce-motion="true"\] \.gate-slogan\{ display:none; \}/.test(css), 'and it goes with the reduced-motion setting too');
};
gates.P1 = () => {
  // Titan One is the wordmark and its ghost only (the owner, Oct 21, 2026): headings and market names are in the plain font too, with no bubble shadow.
  for (const sel of ['.trades-title', '.kal-card-title', '.brief-section-title', '.kal-tools-h', '.settings-section-title']) {
    const m = new RegExp('(^|\\n)\\s*' + sel.replace(/[.]/g, '\\.') + '\\{([^}]*)\\}').exec(css);
    assert.ok(m && !/Titan One/.test(m[2]) && /Public Sans/.test(m[2]) && !/text-shadow/.test(m[2]), sel + ' is in the plain font with no bubble shadow');
  }
  const users = css.split('\n').filter((l) => /Titan One/.test(l) && !/^\s*(\/\*|\*)/.test(l) && !/@font-face/.test(l));   // a @font-face rule loads the font, it does not use it
  // The signed-out front page's slogan (.front-h1) is the one deliberate exception, added at the owner's request (Oct 23, 2026: "that's a sick login page"); it is the brand's slogan lettering, not a heading or a number.
  // The slogan behind every signed-in page (.bg-slogan) is the second deliberate exception (the owner, Oct 23, 2026: "3 looks sick"): faint wallpaper lettering, never a heading or a number.
  // The same wallpaper behind the sign-in screen (.gate-slogan) is the third (the owner, Oct 25, 2026): the identical faint lettering, checked equal to .bg-slogan in BG2.
  assert.ok(users.length <= 4 && users.every((l) => /\.brand-name|font-size:min\(18vw|\.front-h1|\.bg-slogan|\.gate-slogan/.test(l) || /bg-ghost/.test(css)), 'only the wordmark, its ghost and the front page slogan use Titan One: ' + users.map((l) => l.trim().slice(0, 50)).join(' | '));
  for (const sel of ['.kal-tile b', '.kal-bub', '.kal-acct-total']) {
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
  assert.ok(!/Limit graphics|id="motionToggle"|applyMotionPref/.test(html.replace(/\/\*[\s\S]*?\*\//g, '')), 'there is no Limit graphics switch (removed Oct 24, 2026); the device reduce-motion setting is the only input');
  assert.ok(/data-reduce-motion', reduced \? 'true' : 'false'/.test(html) && /prefers-reduced-motion: reduce\)'\)\.matches/.test(html), 'and it still sets the same attribute the motion rules read');
  assert.ok(!/bg-ghost|bg-grid|bg-ambient|bg-grain/.test(html.replace(/\/\*[\s\S]*?\*\//g, '')), 'the ghost wordmark, the grid, the grain and the blobs are gone from the ground (the owner, Oct 23, 2026); the ground is the front page gradient');
};

// P7: the wordmark never changes colour under the pointer (the owner, Oct 21, 2026). It used to turn --amber, which is black in Mono Ink, so the white letters went dark. It hops instead, and the hop stops under reduce motion.
gates.P7 = () => {
  assert.ok(!/\.brand:hover[^{]*\{[^}]*\bcolor\s*:/.test(css), 'no hover rule on the wordmark sets a colour');
  assert.ok(/\.brand:hover \.brand-name span\{[^}]*translateY/.test(css), 'the letters hop on hover');
  assert.ok((html.match(/<div class="brand-name"[^>]*>((?:<span[^>]*>.<\/span>){6})<\/div>/) || [])[1], 'the wordmark is six letters in six spans');
  assert.ok(css.includes('[data-reduce-motion="true"] .brand-name span') && /prefers-reduced-motion: reduce\)\{[\s\S]*?\.brand-name span\{ transition: none; \}/.test(css), 'the hop is off under reduce motion, in both blocks');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

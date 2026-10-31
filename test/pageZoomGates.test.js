'use strict';
// ZM1 to ZM3: browser zoom must zoom the page (the owner, Oct 31, 2026: "even on the Bot page it doesn't zoom in or out properly").
// Consequence: zooming out on a normal laptop screen makes the page smaller by exactly the zoom, never bigger by a hidden step. The big-screen scale (the owner's Oct 27 request for 4K and ultrawide) is kept, but it follows the screen, which browser zoom does not change.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
const run = (screenW, innerW) => {
  const style = {}; const cls = new Set();
  const win = { screen: { width: screenW }, innerWidth: innerW, addEventListener() {} };
  const doc = { documentElement: { style: { setProperty: (k, v) => { style[k] = v; } }, classList: { toggle: (c, on) => { on ? cls.add(c) : cls.delete(c); } } } };
  const m = /\(function \(\) \{ try \{ var d = document\.documentElement; function apply\(\)[\s\S]*?\} catch \(e\) \{[^}]*\} \}\)\(\);/.exec(html);
  assert.ok(m, 'the page scale script is in the head');
  vm.runInNewContext(m[0], { window: win, document: doc });
  return { z: Number(style['--app-zoom']), big: cls.has('big-screen') };
};
gates.ZM1 = () => {
  assert.ok(!/@media\s*\(min-width:\s*\d+px\)\s*\{\s*\.app\{\s*zoom/.test(html), 'no step scales the app from the window width: browser zoom out would switch it on and cancel the zoom');
  assert.ok(/\.app\{\s*zoom:\s*var\(--app-zoom,\s*1\);\s*\}/.test(html), 'the app scale is one variable');
};
gates.ZM4 = () => {
  // the page column is centred whenever the window is wider than it, scaled or not: a laptop zoomed out to 25% is a 5760 pixel window with scale 1, and the page must not sit against the left edge
  assert.ok(/@media \(min-width: 1921px\)\{ \.app\{ margin-left:auto; margin-right:auto; \} \}/.test(html), 'wide windows centre the app column');
  assert.ok(!/html\.big-screen \.app\{[^}]*margin/.test(html), 'centring no longer depends on the big-screen scale');
};
gates.ZM2 = () => {
  // a 1440 pixel laptop zoomed out to 67, 50, 33 and 25 percent: the window is 2149, 2880, 4320 and 5760 CSS pixels wide, and the page scale must stay 1
  [1440, 2149, 2880, 4320, 5760].forEach((w) => { const r = run(1440, w); assert.strictEqual(r.z, 1, 'laptop at window width ' + w + ' stays at scale 1'); assert.strictEqual(r.big, false); });
  // a 4K screen at 100% keeps the Oct 27 look, and zooming out does not change the page scale
  assert.strictEqual(run(3840, 3840).z, 2.1); assert.strictEqual(run(3840, 7680).z, 2.1, '4K zoomed out to 50% keeps the same page scale');
  assert.strictEqual(run(2560, 2560).z, 1.5); assert.strictEqual(run(1920, 1920).z, 1); assert.strictEqual(run(1921, 1921).z, 1.2);
};
gates.ZM3 = () => {
  // a narrow window on a big screen never scales past what it can hold at a 1280 pixel layout (it falls back to normal)
  assert.strictEqual(run(3840, 1000).z, 1); assert.strictEqual(run(3840, 1920).z, 1.5, 'room for 1.5 at 1920 wide');
  assert.strictEqual(run(0, 0).z, 1, 'no screen size: normal scale');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);

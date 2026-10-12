const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const css = src.slice(src.indexOf('<style>'), src.indexOf('</style>')).replace(/\/\*[\s\S]*?\*\//g, '');   // comments are prose, and they sit between rules

// Motion in a dashboard that places real orders is a claim about the data, not decoration. What is left is decoration only (the logo bounce, the
// background drift, the nav shards), so the rule that remains is that all of it stops when asked to, and that nothing reaches out for it.
// Each gate below states the consequence of the rule it defends.

// ---------------------------------------------------------------
// G1: reduced motion must cover every animation the stylesheet defines.
// CONSEQUENCE IF THIS FAILS: a user who asked the OS (or this app's own
// Settings toggle) to stop motion still gets it, on the page they are
// least able to look away from.
// ---------------------------------------------------------------
const mediaBlock = /@media \(prefers-reduced-motion: reduce\)\{([\s\S]*?)\n  \}/.exec(css);
assert.ok(mediaBlock, 'a prefers-reduced-motion block must exist');
const attrRules = css.split('\n').filter((l) => l.includes('[data-reduce-motion="true"]')).join('\n');
// Every rule that starts an animation (anything but "animation: none"), outside the reduce-motion block itself.
const outside = css.replace(mediaBlock[0], '').split('\n').filter((l) => !l.includes('[data-reduce-motion="true"]')).join('\n');
const animated = [];
for (const m of outside.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
  if (/(^|[;\s])animation\s*:\s*(?!none)/.test(m[2])) m[1].split(',').forEach((sel) => animated.push(sel.replace(/\s+/g, ' ').trim()));
}
assert.ok(animated.length >= 5, 'the page animates its logo, background and nav shards; found only ' + JSON.stringify(animated));
animated.forEach((sel) => {
  assert.ok(mediaBlock[1].includes(sel), 'prefers-reduced-motion must disable ' + sel);
  assert.ok(attrRules.includes(sel), 'the Settings reduce-motion toggle must also disable ' + sel);
});

// ---------------------------------------------------------------
// G2: no new network request. The owner approved this on the condition
// it costs nothing.
// CONSEQUENCE IF THIS FAILS: a font, CDN or image request is a recurring
// cost and a new way for the page to fail while the market is open.
// The three https:// links this file is allowed are the two font
// preconnects and the one Google Fonts stylesheet that predate this work.
// ---------------------------------------------------------------
const resourceRefs = []
  // An inline data: icon makes no network request, so it is not an external
  // resource. Its SVG contains '>' characters, so the tag match is cut short;
  // the filter keys on the href prefix instead.
  // The home-screen icon is a local file next to index.html (rel="apple-touch-icon", no scheme), so it is not an external resource either.
  .concat((src.match(/<link\b[^>]*>/g) || []).filter(tag => !/\bhref="data:/.test(tag) && !/\brel="apple-touch-icon"\s+href="[^":/]+"/.test(tag)))
  .concat(src.match(/<script\b[^>]*\bsrc=[^>]*>/g) || [])
  .concat(src.match(/<img\b[^>]*\bsrc=[^>]*>/g) || [])
  .concat(src.match(/url\((["']?)https?:[^)]*\)/g) || []);
assert.strictEqual(
  resourceRefs.length, 3,
  'no new external resource may be introduced -- animation must be inline CSS/SVG only. Found: ' + JSON.stringify(resourceRefs)
);
resourceRefs.forEach(ref => {
  assert.ok(
    /fonts\.(googleapis|gstatic)\.com/.test(ref),
    'the only external resources allowed are the two font preconnects and the Google Fonts stylesheet that predate this work: ' + ref
  );
});
assert.ok(!/@import\s+url\(/.test(src), 'no CSS @import may pull in an external stylesheet');

// ---------------------------------------------------------------
// G3: nothing may animate a property that costs layout.
// CONSEQUENCE IF THIS FAILS: a page that redraws while someone reads a
// balance drops frames and shifts the numbers under their eyes.
// ---------------------------------------------------------------
const frames = [...css.matchAll(/@keyframes\s+([\w-]+)\s*\{/g)].map((m) => m[1]);
assert.ok(frames.length >= 5, 'the page defines its keyframes: ' + frames.join(', '));
frames.forEach((name) => {
  const start = css.indexOf('@keyframes ' + name);
  let depth = 0, end = -1;
  for (let i = css.indexOf('{', start); i < css.length; i++) {
    if (css[i] === '{') depth++;
    else if (css[i] === '}' && --depth === 0) { end = i; break; }
  }
  const body = css.slice(start, end);
  assert.ok(
    !/(^|[^-])(width|height|top|left|right|bottom|margin|padding)\s*:/.test(body.replace(/animation-timing-function[^;]*;/g, '')),
    name + ' must animate transform/opacity/background only -- never a layout property'
  );
});

console.log('motionHonestyGates: ok');

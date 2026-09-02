const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

// Motion in a trading dashboard is a claim about the data, not decoration.
// Each gate below states the consequence of the rule it defends.

// ---------------------------------------------------------------
// G1: a pulsing dot must never outlive the state it claims.
// CONSEQUENCE IF THIS FAILS: the header keeps beating "live" through a
// feed that is degraded or dead, and the prices on screen are believed.
// The animation is therefore attached to the .ok class only -- the class
// quoteFeedStatus hands out from real batch results -- so a failed feed
// cannot render it, because it never gets the selector.
// ---------------------------------------------------------------
assert.ok(
  /\.header-live-status\.ok::before\{[^}]*animation:/.test(src),
  'the header liveness pulse must be bound to .header-live-status.ok'
);
assert.ok(
  !/\.header-live-status::before\{[^}]*animation:/.test(src),
  'the header dot must not animate unconditionally -- only in the .ok state'
);
assert.ok(
  /\.to-card-dot\.ok\{[^}]*animation:/.test(src),
  'the Backend Status head dot pulse must be bound to its .ok state'
);
assert.ok(
  !/\.to-card-dot\{[^}]*animation:/.test(src),
  'the Backend Status dot must not animate in its unknown/warn states'
);
// The class it is gated on has to keep coming from the real verdict.
assert.ok(
  /el\.className = 'header-live-status ' \+ status\.cls;/.test(src),
  'the header status class must still be driven by quoteFeedStatus'
);

// ---------------------------------------------------------------
// G2: the in-flight shimmer must mean "still trying", never "gave up".
// CONSEQUENCE IF THIS FAILS: a card whose fetch failed keeps sweeping and
// reads as working, which is the failure state hardest to notice.
// ---------------------------------------------------------------
const shimmerLines = src.split('\n').filter(l => l.includes('is-loading-shimmer') && l.includes('innerHTML'));
assert.ok(shimmerLines.length > 0, 'the shimmer must actually be applied to a loading placeholder');
shimmerLines.forEach(line => {
  assert.ok(
    /Checking/.test(line),
    'the shimmer may only mark an in-flight "Checking..." placeholder: ' + line.trim()
  );
  assert.ok(
    !/(Failed|Could not|failed)/.test(line),
    'the shimmer must never be applied to a failure message: ' + line.trim()
  );
});

// ---------------------------------------------------------------
// G3: reduced motion must cover every animation added here.
// CONSEQUENCE IF THIS FAILS: a user who asked the OS (or this app's own
// Settings toggle) to stop motion still gets it, on the page they are
// least able to look away from.
// ---------------------------------------------------------------
const mediaBlock = /@media \(prefers-reduced-motion: reduce\)\{([\s\S]*?)\n  \}/.exec(src);
assert.ok(mediaBlock, 'a prefers-reduced-motion block must exist');
const attrRules = src.split('\n').filter(l => l.includes('[data-reduce-motion="true"]')).join('\n');
[
  '.value-flash-up',
  '.value-flash-down',
  '.header-live-status.ok::before',
  '.to-card-dot.ok',
  '.is-loading-shimmer::after',
  '.card-enter'
].forEach(sel => {
  assert.ok(mediaBlock[1].includes(sel), 'prefers-reduced-motion must disable ' + sel);
  assert.ok(attrRules.includes(sel), 'the Settings reduce-motion toggle must also disable ' + sel);
});

// ---------------------------------------------------------------
// G4: no new network request. The owner approved this on the condition
// it costs nothing.
// CONSEQUENCE IF THIS FAILS: a font, CDN or image request is a recurring
// cost and a new way for the page to fail while the market is open.
// The three https:// links this file is allowed are the two font
// preconnects and the one Google Fonts stylesheet that predate this work.
// ---------------------------------------------------------------
const resourceRefs = []
  .concat(src.match(/<link\b[^>]*>/g) || [])
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
// G5: the change flash must fire on a CHANGE, not on a re-render.
// CONSEQUENCE IF THIS FAILS: every cell tints green on every ~45s poll,
// which trains the owner to ignore the one signal that says a number
// moved -- and a value flashing on first sight claims a direction it
// cannot know.
// ---------------------------------------------------------------
const start = src.indexOf('function applyValueFlashes(');
assert.ok(start > 0, 'applyValueFlashes must exist');
const body = src.slice(start, src.indexOf('\n  }\n', start));
assert.ok(/if\(!had \|\| prev === null \|\| val === null \|\| val === prev\) return;/.test(body),
  'no flash on first sight, on a null (unpriced) value, or when the value is unchanged');
assert.ok(/lastFlashedValues\[key\] = val;/.test(body),
  'the previous value must be remembered per key so the comparison survives a re-render');

// ---------------------------------------------------------------
// G6: nothing may animate a property that costs layout, and the entrance
// must not replay on every re-render.
// CONSEQUENCE IF THIS FAILS: a table that redraws every poll drops frames
// and cards rise under the eyes of someone reading a P&L figure.
// ---------------------------------------------------------------
['valueFlashUp', 'valueFlashDown', 'loadingSweep', 'cardEnter'].forEach(name => {
  const kf = new RegExp('@keyframes ' + name + '\\{([^}]*\\}[^}]*)\\}').exec(src);
  assert.ok(kf, 'keyframes ' + name + ' must exist');
  assert.ok(
    !/(^|[^-])(width|height|top|left|right|bottom|margin|padding)\s*:/.test(kf[1]),
    name + ' must animate transform/opacity/background only -- never a layout property'
  );
});
assert.ok(
  /function runCardEntrance\(pageName\)\{\s*if\(cardsEnteredPages\[pageName\]\) return;/.test(src.replace(/\n\s*/g, m => m.includes('\n') ? '\n    ' : m)) ||
  /if\(cardsEnteredPages\[pageName\]\) return;/.test(src),
  'the card entrance must be guarded to run once per page view'
);

// ---------------------------------------------------------------
// G7: the same rule, executed rather than read. A fake DOM replays the
// sequence that matters: first sight, unchanged, up, down, gone stale,
// priced again. Only the two real moves may tint.
// CONSEQUENCE IF THIS FAILS: colour on the screen asserts a direction the
// data did not move in.
// ---------------------------------------------------------------
const declStart = src.indexOf('var lastFlashedValues = {};');
const fnEnd = src.indexOf('\n  }\n', src.indexOf('function applyValueFlashes(')) + 4;
const apply = new Function('return (function(){' + src.slice(declStart, fnEnd) + 'return applyValueFlashes;})()')();

function cell(value) {
  return {
    classes: [],
    getAttribute(name) { return name === 'data-flash-key' ? 'k' : (value === null ? '' : String(value)); },
    classList: { add(c) { this._o.classes.push(c); } }
  };
}
function run(values) {
  const seen = [];
  values.forEach(v => {
    const el = cell(v);
    el.classList._o = el;
    apply({ querySelectorAll: () => [el] });
    seen.push(el.classes[0] || null);
  });
  return seen;
}
assert.deepStrictEqual(
  run([100, 100, 101, 99, null, 150]),
  [null, null, 'value-flash-up', 'value-flash-down', null, null],
  'flash only on a real move: never on first sight, on an unchanged value, on going stale, or on returning from stale'
);

console.log('motionHonestyGates: ok');

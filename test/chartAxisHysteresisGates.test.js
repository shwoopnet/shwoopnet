// The chart's y-axis gridlines are deliberately "sticky" -- a live
// position's chart redraws on every quote poll, and recomputing fresh
// round-number bounds on every single poll made the axis visibly jolt
// even when price barely moved. So a render reuses the previous render's
// exact bounds whenever the new price range still fits inside them.
//
// That containment check alone had no floor: once any render widened the
// bounds (one volatile bar, one bad print), every later render whose real
// range still fit inside kept reusing that same wide window forever, even
// once price had settled into a much narrower band -- the real candles
// end up compressed into a sliver in the middle of a plot still sized for
// a move that isn't happening any more. This is the reported "chart
// y-axis showing stale/wrong range, compressing real price action to a
// sliver" bug.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name, deps) {
  const start = src.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('not found in index.html: ' + name);
  let d = 0, end = -1;
  for (let i = src.indexOf('{', start); i < src.length; i++) {
    if (src[i] === '{') d++;
    else if (src[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  const names = Object.keys(deps || {});
  return new Function(...names, 'return (' + src.slice(start, end) + ')')(...names.map((n) => deps[n]));
}

const niceNum = lift('niceNum');
const computeNiceScale = lift('computeNiceScale', { niceNum });
const formatAxisLabel = lift('formatAxisLabel', { INTRADAY_TFS: ['5m', '15m', '30m', '1D'] });
const drawCandles = lift('drawCandles', { computeNiceScale, formatAxisLabel });

function bar(t, o, h, l, c) {
  return { t: new Date(t), o, h, l, c, vol: 100 };
}

// A tight, realistic band of daily bars -- price never leaves ~$74-$78.
function tightBars() {
  const out = [];
  for (let i = 0; i < 20; i++) {
    const px = 76 + Math.sin(i) * 1.5;
    out.push(bar(Date.UTC(2026, 8, 1 + i), px, px + 0.6, px - 0.6, px + 0.2));
  }
  return out;
}

function fakeSvg() { return { innerHTML: '', viewBox: { baseVal: { width: 760, height: 240 } } }; }

function main() {
  // ---- Baseline: with no prevScale, the axis is computed fresh and
  // sized to the real (tight) data -- this is what a healthy chart looks
  // like, and what the sliver bug regresses away from.
  const fresh = drawCandles(fakeSvg(), tightBars(), 'linear', 1, '1D', {});
  assert.ok(fresh.range < 20, `a tight ~$74-78 band must not produce a >20-wide axis, got ${fresh.range}`);
  console.log('G1 PASS a fresh render sizes the axis to the real (tight) price range');

  // ---- The bug: simulate one earlier render that (for whatever reason --
  // a bad print, a genuinely volatile bar that has since scrolled out of
  // view) left behind a very wide prevScale. A later render whose real
  // price action is back to the tight band above must NOT keep reusing
  // that stale wide window forever just because the tight band happens to
  // fit inside it.
  const staleWideScale = { loT: 40, hiT: 120, niceTicks: [40, 60, 80, 100, 120], useLog: false };
  const afterStaleScale = drawCandles(fakeSvg(), tightBars(), 'linear', 1, '1D', { prevScale: staleWideScale });
  assert.ok(afterStaleScale.range < 20,
    `a stale 80-wide prevScale must not persist once real price has settled into a tight band; got range ${afterStaleScale.range}`);
  console.log('G2 PASS a stale, much-wider previous scale is discarded once price has settled into a tight band');

  // ---- The feature this must not regress: small, genuine jitter between
  // polls (well within the previous bounds, and not a big shrink) should
  // still reuse the previous bounds rather than jolt the axis.
  const jitterBars = tightBars();
  const firstRender = drawCandles(fakeSvg(), jitterBars, 'linear', 1, '1D', {});
  // A second render with the same data (a genuine no-op poll) must reuse
  // the exact same bounds, not recompute (even identically) from scratch.
  const secondRender = drawCandles(fakeSvg(), jitterBars, 'linear', 1, '1D', { prevScale: firstRender });
  assert.strictEqual(secondRender.loT, firstRender.loT, 'an unchanged price range must reuse the exact previous lower bound');
  assert.strictEqual(secondRender.hiT, firstRender.hiT, 'an unchanged price range must reuse the exact previous upper bound');
  console.log('G3 PASS genuine polling jitter (same/near-same range) still reuses the previous bounds, unchanged');

  // ---- A manual zoom/pan (priceScaleFactor != 1) must always respond
  // immediately regardless of the fill-ratio floor -- that guard rail is
  // there for the default view only.
  const zoomed = drawCandles(fakeSvg(), tightBars(), 'linear', 3, '1D', { prevScale: staleWideScale });
  assert.ok(zoomed.range < staleWideScale.hiT - staleWideScale.loT,
    'a manual zoom must not be held hostage by a stale previous scale either');
  console.log('G4 PASS a manually zoomed view is unaffected by the stale-scale guard (it never reused prevScale anyway)');

  console.log('\nAll chart axis hysteresis gates passed.');
}

main();

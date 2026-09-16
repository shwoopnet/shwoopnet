'use strict';
// Reported live: "fix font on chart, both numbers and letters." Every
// chart shared ONE hardcoded 760x240 coordinate system in drawCandles,
// rendered into an SVG whose CSS height varied by context (310px for a
// normal Setups card, bumped to 420px for the trade modal specifically --
// see .trade-modal-chart-col's own comment). preserveAspectRatio="none"
// stretches a viewBox that doesn't match its own rendered aspect ratio
// NON-uniformly -- vertically more than horizontally, whenever the CSS
// height is taller than the viewBox's own 240 units supports -- and that
// stretch applies to EVERYTHING drawn inside, candles and gridlines and
// every character of text alike. The font was never the wrong font; it
// was being vertically stretched along with the rest of the chart.
//
// drawCandles now reads its own W/H from the specific SVG's viewBox
// instead of hardcoding 760x240, so a chart that wants more real room
// (like the modal, which now declares a taller "0 0 760 580" viewBox to
// match its own taller CSS height) gets genuinely more plot area at the
// SAME aspect ratio, not a stretched version of the old one.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name) {
  const start = html.indexOf('  function ' + name + '(');
  assert.notStrictEqual(start, -1, 'could not find function ' + name + ' in index.html');
  let depth = 0;
  const open = html.indexOf('{', start);
  for (let j = open; j < html.length; j++) {
    if (html[j] === '{') depth++;
    else if (html[j] === '}') { depth--; if (depth === 0) return html.slice(start, j + 1); }
  }
  throw new Error('unbalanced braces for ' + name);
}

function build() {
  const src = `
    function computeNiceScale(lo, hi, n){ return { lo: lo, hi: hi, ticks: [lo, hi], spacing: (hi-lo)||1 }; }
    function formatAxisLabel(){ return ''; }
    ${lift('drawCandles')}
    return drawCandles;
  `;
  return new Function(src)();
}

function bar(t, o, h, l, c) { return { t: new Date(t), o, h, l, c, vol: 10 }; }
function bars() {
  const out = [];
  for (let i = 0; i < 10; i++) out.push(bar(Date.UTC(2026, 8, 1 + i), 100 + i, 101 + i, 99 + i, 100.5 + i));
  return out;
}

function fakeSvg(viewBoxHeight) {
  return { innerHTML: '', viewBox: { baseVal: { width: 760, height: viewBoxHeight } } };
}

function main() {
  const drawCandles = build();

  // ---- Reads W/H from the SVG's own viewBox, not a hardcoded 760x240 ----
  {
    const scOld = drawCandles(fakeSvg(240), bars(), 'linear', 1, '1D', {});
    const scNew = drawCandles(fakeSvg(580), bars(), 'linear', 1, '1D', {});
    assert.strictEqual(scOld.plotH, 158, 'a 240-tall viewBox (every non-modal chart) must render exactly as it always has');
    assert.strictEqual(scNew.plotH, 580 - 82, 'a taller viewBox must give the plot proportionally more real room, not the same 158 stretched over more CSS pixels');
    assert.ok(scNew.plotH > scOld.plotH, 'the taller viewBox must produce a taller PLOT, confirming this is genuine extra room, not distortion of the old one');
    console.log('G1 PASS drawCandles derives its coordinate system from the SVG\'s own viewBox, not a shared hardcoded 760x240');
  }

  // ---- A missing viewBox (e.g. a not-yet-attached node) falls back safely, doesn't throw ----
  {
    const sc = drawCandles({ innerHTML: '' }, bars(), 'linear', 1, '1D', {});
    assert.strictEqual(sc.plotH, 158, 'no viewBox at all must fall back to the original 760x240 behavior, not crash');
    console.log('G2 PASS a chart with no viewBox yet falls back to the original geometry instead of throwing');
  }

  console.log('\nAll chart viewBox distortion gates passed.');
}

main();

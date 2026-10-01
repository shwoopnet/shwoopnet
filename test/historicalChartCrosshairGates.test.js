'use strict';
// The historical (closed-trade) chart could zoom and pan (see
// historicalChartInteractivityGates.test.js) but had no hover crosshair at
// all -- you could never read an exact O/H/L/C or timestamp off a bar,
// unlike the live chart's updateCrosshair. setupHistoricalChartInteractivity
// now builds the same thing for itself (self-contained, no sym key -- see
// its own comment), wired into the plain-hover branch of its pointermove
// handler. These gates pin that hovering actually re-syncs the readout and
// crosshair line/tag elements, and that leaving the chart hides them again.

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
function liftVar(name) {
  const start = html.indexOf('  var ' + name + ' = ');
  assert.notStrictEqual(start, -1, 'could not find var ' + name);
  const semi = html.indexOf(';', start);
  return html.slice(start, semi + 1);
}

function makeBars(n) {
  const bars = [];
  for (let i = 0; i < n; i++) {
    bars.push({ o: 100 + i, h: 101 + i, l: 99 + i, c: 100.5 + i, vol: 10, t: new Date(2026, 0, 1 + i) });
  }
  return bars;
}

function build() {
  const listeners = {};
  const drawCalls = [];
  const nsCallCounter = { count: 0 };
  const readout = { setAttribute(){}, removeAttribute(){}, hidden: false, innerHTML: '' };
  const svg = {
    getBoundingClientRect(){ return { left: 0, top: 0, width: 760, height: 240 }; },
    viewBox: { baseVal: { x: 0, y: 0, width: 760, height: 240 } },
    setPointerCapture(){}, releasePointerCapture(){},
    style: {},
    querySelectorAll: () => [],
    appendChild(){},
    addEventListener(type, fn){ listeners[type] = fn; },
  };

  const src = `
    var document = {
      getElementById: function(id){
        if(id === 'tradeModalChartCrosshair') return READOUT;
        return null;
      },
      createElementNS: function(){ NS_CALLS.count++; return { setAttribute(){}, innerHTML: '' }; },
    };
    // Real drawCandles returns a fresh scale object every render; this
    // fake does the same, so updateHistoricalCrosshair's state.lastScale
    // check behaves like the real thing (only populated after a render).
    function drawCandles(svg, data, scale, factor, tf, opts){
      var sc = { plotW: 690, plotH: 158, padTop: 12, range: 10, useLog: false, loT: 90, hiT: 100 };
      DRAW_CALLS.push({ count: data.length, tf: tf, opts: opts });
      return sc;
    }
    function svgLocalX(svgArg, clientX){ return clientX; } // tests drive clientX directly as a plotW-relative coordinate
    function svgLocalY(svgArg, clientY){ return clientY; }
    function chartPlotBottomY(svgArg){ return 170; }
    function requestAnimationFrame(fn){ fn(); }
    ${liftVar('INTRADAY_TFS')}
    ${lift('formatCrosshairDate')}
    ${liftVar('tfConfig')}
    ${liftVar('MIN_VISIBLE_CANDLES')}
    ${lift('setupHistoricalChartInteractivity')}
    return { setupHistoricalChartInteractivity: setupHistoricalChartInteractivity };
  `;
  const mod = new Function('DRAW_CALLS', 'READOUT', 'NS_CALLS', src)(drawCalls, readout, nsCallCounter);
  return { mod, svg, listeners, drawCalls, readout, nsCallCounter };
}

function main() {
  // ---- Plain hover (no drag) re-syncs the crosshair readout ----
  {
    const { mod, svg, listeners, readout, nsCallCounter } = build();
    const bars = makeBars(50);
    mod.setupHistoricalChartInteractivity(svg, bars, '5m', null);
    const callsBeforeHover = nsCallCounter.count;
    listeners.pointermove({ clientX: 400, clientY: 100 });
    assert.ok(nsCallCounter.count > callsBeforeHover,
      'hovering (no drag active) must draw crosshair line/tag elements via the SVG namespace');
    assert.ok(readout.innerHTML, 'hovering must populate the OHLC readout div');
    console.log('G1 PASS plain hover draws the crosshair and populates the OHLC readout');
  }

  // ---- Hovering a second time at a different position re-syncs again ----
  {
    const { mod, svg, listeners, readout, nsCallCounter } = build();
    const bars = makeBars(50);
    mod.setupHistoricalChartInteractivity(svg, bars, '5m', null);
    listeners.pointermove({ clientX: 100, clientY: 100 });
    const firstReadout = readout.innerHTML;
    const callsAfterFirst = nsCallCounter.count;
    listeners.pointermove({ clientX: 600, clientY: 100 });
    assert.ok(nsCallCounter.count > callsAfterFirst,
      'moving the cursor to a different bar must redraw the crosshair again, not reuse the first hover');
    assert.notStrictEqual(readout.innerHTML, '', 'the readout must stay populated after the second hover');
    console.log('G2 PASS a second hover at a different position re-syncs the crosshair again');
  }

  // ---- pointerleave hides the readout and clears the crosshair elements ----
  {
    const { mod, svg, listeners, readout } = build();
    const bars = makeBars(50);
    mod.setupHistoricalChartInteractivity(svg, bars, '5m', null);
    listeners.pointermove({ clientX: 400, clientY: 100 });
    let hiddenCalled = false;
    readout.setAttribute = function(name){ if(name === 'hidden') hiddenCalled = true; };
    listeners.pointerleave({});
    assert.ok(hiddenCalled, 'leaving the chart must hide the OHLC readout');
    console.log('G3 PASS pointerleave hides the historical chart crosshair readout');
  }

  // ---- Hovering during an active pan drag must not also update the crosshair ----
  // (the drag branches already own pointermove while dragState is set --
  // the crosshair only re-syncs on the plain-hover path.)
  {
    const { mod, svg, listeners, nsCallCounter } = build();
    const bars = makeBars(200);
    mod.setupHistoricalChartInteractivity(svg, bars, '5m', null);
    listeners.pointerdown({ clientX: 300, clientY: 100 });
    const callsBeforeDragMove = nsCallCounter.count;
    listeners.pointermove({ clientX: 250, clientY: 100 });
    assert.strictEqual(nsCallCounter.count, callsBeforeDragMove,
      'a pan drag must not also redraw the crosshair -- that is the plain-hover path only');
    listeners.pointerup({});
    console.log('G4 PASS a pan drag does not also trigger a crosshair redraw');
  }

  console.log('\nAll historical chart crosshair gates passed.');
}

main();

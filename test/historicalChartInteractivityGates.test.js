'use strict';
// The trade detail modal's historical (closed-trade) chart used to be a
// single static drawCandles() call with no way to zoom or pan -- reported
// as "condensed and hard to read, can't adjust anything." Live Setups
// charts already have real wheel-zoom/drag-pan/drag-price-scale
// interactivity (setupChartInteractivity); setupHistoricalChartInteractivity
// gives closed trades the same interaction, self-contained rather than
// routed through the sym-keyed chartStates a live, repeatedly-polled chart
// needs (see its own comment in index.html). These gates pin that a wheel
// event actually narrows the visible candle window, and that dragging pans
// it -- the two things a static chart couldn't do before.

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
  const svg = {
    getBoundingClientRect(){ return { left: 0, top: 0, width: 760, height: 240 }; },
    viewBox: { baseVal: { x: 0, y: 0, width: 760, height: 240 } },
    setPointerCapture(){}, releasePointerCapture(){},
    style: {},
    addEventListener(type, fn){ listeners[type] = fn; },
  };

  const src = `
    function drawCandles(svg, data, scale, factor, tf, opts){
      var sc = { plotW: 690, plotH: 158, padTop: 12, range: 10, useLog: false, loT: 90, hiT: 100 };
      DRAW_CALLS.push({ count: data.length, tf: tf, opts: opts });
      return sc;
    }
    function svgLocalX(svgArg, clientX){ return clientX; } // tests drive clientX directly as a plotW-relative coordinate
    function svgLocalY(svgArg, clientY){ return clientY; }
    var CHART_PLOT_BOTTOM_Y = 170;
    // Real browsers batch redraws via requestAnimationFrame; Node has no
    // such global, so runs the callback immediately -- fine here since
    // these tests only care about the end state, not frame timing.
    function requestAnimationFrame(fn){ fn(); }
    ${liftVar('tfConfig')}
    ${liftVar('MIN_VISIBLE_CANDLES')}
    ${lift('setupHistoricalChartInteractivity')}
    return { setupHistoricalChartInteractivity: setupHistoricalChartInteractivity };
  `;
  const mod = new Function('DRAW_CALLS', src)(drawCalls);
  return { mod, svg, listeners, drawCalls };
}

function main() {
  // ---- Initial render happens synchronously, no interaction needed ----
  {
    const { mod, svg, drawCalls } = build();
    const bars = makeBars(50);
    mod.setupHistoricalChartInteractivity(svg, bars, '5m', { entry: 10, stop: 9, target: 12 });
    assert.strictEqual(drawCalls.length, 1, 'the chart must draw immediately on setup, not wait for a first interaction');
    assert.strictEqual(drawCalls[0].opts.levels.entry, 10, 'entry/stop/target levels must reach the initial draw');
    console.log('G1 PASS setup draws the chart immediately with the given levels');
  }

  // ---- Wheel zoom narrows the visible window ----
  {
    const { mod, svg, listeners, drawCalls } = build();
    const bars = makeBars(50);
    mod.setupHistoricalChartInteractivity(svg, bars, '5m', null);
    const initialCount = drawCalls[drawCalls.length - 1].count;
    // deltaY < 0 (scroll up / zoom in) narrows the visible window.
    listeners.wheel({ preventDefault(){}, clientX: 350, clientY: 100, deltaY: -150 });
    const afterZoomCount = drawCalls[drawCalls.length - 1].count;
    assert.ok(afterZoomCount < initialCount,
      'scrolling to zoom in must narrow the visible candle window (' + afterZoomCount + ' vs ' + initialCount + ')');
    console.log('G2 PASS wheel zoom narrows the visible candle window');
  }

  // ---- Drag pans the view without changing the candle count ----
  {
    const { mod, svg, listeners, drawCalls } = build();
    const bars = makeBars(50);
    mod.setupHistoricalChartInteractivity(svg, bars, '5m', null);
    const initialCount = drawCalls[drawCalls.length - 1].count;
    // A pointerdown in the plot area (not the right price-axis strip, not
    // the bottom time-axis strip) starts a pan drag.
    listeners.pointerdown({ clientX: 300, clientY: 100 });
    listeners.pointermove({ clientX: 200, clientY: 100 }); // drag left -> pan forward in time
    const afterPanCount = drawCalls[drawCalls.length - 1].count;
    assert.strictEqual(afterPanCount, initialCount, 'a plain drag must pan (same candle count), not zoom');
    listeners.pointerup({});
    console.log('G3 PASS dragging in the plot area pans the view without changing zoom');
  }

  console.log('\nAll historical chart interactivity gates passed.');
}

main();

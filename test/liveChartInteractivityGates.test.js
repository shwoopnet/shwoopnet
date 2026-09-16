'use strict';
// User-reported: the trade detail modal's chart for an OPEN (live)
// position "can't scroll, can't adjust, nothing" -- unlike the closed-
// trade (historical) chart, which setupHistoricalChartInteractivity
// already covers (see historicalChartInteractivityGates.test.js). A live
// position's chart goes through the OLDER setupChartInteractivity/
// zoomChart/chartStates machinery instead, which predates this session's
// modal work and was never directly gated by a test. These gates lift
// that real machinery and drive it exactly the way a real wheel/drag
// would, to find out whether the reported break is real.

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
    style: {}, dataset: {}, querySelectorAll: () => [],
    addEventListener(type, fn){ listeners[type] = fn; },
  };
  const crosshairReadout = { setAttribute(){}, removeAttribute(){}, hidden: false };

  const src = `
    var journalEntries = [];
    var intradayTrades = [];
    function isOpenPositionForCurrentAccount(){ return false; }
    function formatCrosshairDate(){ return ''; }
    function requestAnimationFrame(fn){ fn(); }
    var showOHLCReadout = false; // keep updateCrosshair's DOM writes minimal
    var document = {
      getElementById: function(id){
        if(id === 'chart-SYM') return SVG;
        if(id === 'crosshair-SYM') return CROSSHAIR;
        return null;
      },
      querySelector: function(){ return null; },
    };
    function drawCandles(svg, data, scale, factor, tf, opts){
      DRAW_CALLS.push({ count: data.length, tf: tf, opts: opts });
      return { plotW: 690, plotH: 158, padTop: 12, range: 10, useLog: false, loT: 90, hiT: 100 };
    }
    ${liftVar('tfConfig')}
    ${liftVar('chartStates')}
    var chartRenderScheduled = {};
    ${liftVar('MIN_VISIBLE_CANDLES')}
    ${lift('chartPlotBottomY')}
    ${lift('svgLocalX')}
    ${lift('svgLocalY')}
    ${lift('scheduleChartRender')}
    ${lift('renderChartView')}
    ${lift('initChartState')}
    ${lift('zoomChart')}
    ${lift('hideCrosshair')}
    ${lift('updateCrosshair')}
    ${lift('setupChartInteractivity')}
    return {
      initChartState: initChartState,
      setupChartInteractivity: setupChartInteractivity,
      getChartState: function(sym){ return chartStates[sym]; },
    };
  `;
  const mod = new Function('SVG', 'CROSSHAIR', 'DRAW_CALLS', src)(svg, crosshairReadout, drawCalls);
  return { mod, svg, listeners, drawCalls };
}

function main() {
  // ---- setupChartInteractivity actually wires the listeners it claims to ----
  {
    const { mod, svg, listeners } = build();
    mod.initChartState('SYM', '5m', makeBars(50));
    mod.setupChartInteractivity('SYM');
    // No dataset.wired assertion here on purpose -- see G4's own comment
    // for why that attribute is no longer used as a self-guard at all.
    assert.strictEqual(typeof listeners.wheel, 'function', 'a wheel listener must actually be attached');
    assert.strictEqual(typeof listeners.pointerdown, 'function', 'a pointerdown listener must actually be attached');
    console.log('G1 PASS setupChartInteractivity wires real wheel/pointerdown listeners on the live chart svg');
  }

  // ---- Wheel zoom actually narrows the visible window ----
  {
    const { mod, svg, listeners, drawCalls } = build();
    mod.initChartState('SYM', '5m', makeBars(50));
    mod.setupChartInteractivity('SYM');
    const before = mod.getChartState('SYM');
    const initialCount = before.viewEnd - before.viewStart;
    listeners.wheel({ preventDefault(){}, clientX: 350, clientY: 100, deltaY: -150 });
    const after = mod.getChartState('SYM');
    const afterCount = after.viewEnd - after.viewStart;
    assert.ok(afterCount < initialCount,
      'scrolling on a LIVE chart must narrow the visible candle window (' + afterCount + ' vs ' + initialCount + ')');
    console.log('G2 PASS wheel zoom narrows the live chart\'s visible window');
  }

  // ---- Drag pans the view ----
  // (Needs more bars than the timeframe's own defaultVisible window --
  // 5m's is 60 -- or there is nothing off-screen to pan into at all and
  // any pan delta clamps straight back to the same viewStart, which
  // looks identical to a broken pan without actually being one.)
  {
    const { mod, listeners } = build();
    mod.initChartState('SYM', '5m', makeBars(200));
    mod.setupChartInteractivity('SYM');
    const before = mod.getChartState('SYM');
    const initialStart = before.viewStart;
    const initialCount = before.viewEnd - before.viewStart;
    // The view starts parked at the RIGHT edge (the newest bars) -- drag
    // must move toward older bars (positive dx / dragging rightward) to
    // have anywhere to go; the opposite direction clamps straight back to
    // the same viewStart (already at the max), which looks identical to a
    // broken pan without being one.
    listeners.pointerdown({ clientX: 200, clientY: 100 });
    listeners.pointermove({ clientX: 300, clientY: 100 });
    const after = mod.getChartState('SYM');
    assert.notStrictEqual(after.viewStart, initialStart, 'dragging on a LIVE chart must actually pan the view');
    assert.strictEqual(after.viewEnd - after.viewStart, initialCount, 'a plain drag must pan, not zoom');
    console.log('G3 PASS dragging pans the live chart\'s view');
  }

  // ---- A fresh clone that inherited a "wired" attribute must still get wired ----
  // Reported live: the first trade opened after a page load scrolled/zoomed
  // fine, and the SECOND one -- a different symbol, a fresh close-then-
  // reopen -- did nothing at all. openTradeModal always hands this a
  // freshly svg.cloneNode(false)'d element specifically so a prior open's
  // listeners can never carry over -- but cloneNode(false) copies every
  // ATTRIBUTE of the source node, data-* included, so a dataset.wired='1'
  // set on the FIRST symbol's node was still sitting on the clone made for
  // the SECOND symbol's node, even though that clone had never actually
  // been wired itself. A self-guard keyed on that attribute would see
  // "already wired" and skip attaching any listeners at all -- this
  // simulates exactly that inherited-attribute clone and confirms
  // setupChartInteractivity wires it anyway.
  {
    const { mod, svg, listeners } = build();
    svg.dataset.wired = '1'; // what a cloneNode(false) of an already-wired node carries over
    mod.initChartState('SYM', '5m', makeBars(50));
    mod.setupChartInteractivity('SYM');
    assert.strictEqual(typeof listeners.wheel, 'function',
      'a node that inherited dataset.wired from cloneNode(false) must still get real listeners attached, not be skipped as "already wired"');
    console.log('G4 PASS a clone that inherited a stale "wired" attribute still gets wired for real');
  }

  console.log('\nAll live chart interactivity gates passed.');
}

main();

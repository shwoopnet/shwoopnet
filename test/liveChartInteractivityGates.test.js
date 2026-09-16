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
    assert.strictEqual(svg.dataset.wired, '1', 'the svg must be marked wired after setup');
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

  // ---- setupChartInteractivity called a SECOND time on the SAME node must not throw / must still be wired ----
  // (Reproduces exactly what openTradeModal does: renderChartInto -> setupChartInteractivity,
  // on a node that -- across a poll re-render inside the SAME open modal session -- could
  // already carry dataset.wired from a prior call.)
  {
    const { mod, svg, listeners } = build();
    mod.initChartState('SYM', '5m', makeBars(50));
    mod.setupChartInteractivity('SYM');
    const firstWheel = listeners.wheel;
    mod.setupChartInteractivity('SYM'); // called again, same node
    assert.strictEqual(listeners.wheel, firstWheel,
      'a second setup call on an already-wired node must be a no-op (guarded by svg.dataset.wired), not double-attach');
    console.log('G4 PASS a second setupChartInteractivity call on the same node is a safe no-op');
  }

  console.log('\nAll live chart interactivity gates passed.');
}

main();

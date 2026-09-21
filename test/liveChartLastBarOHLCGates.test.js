'use strict';
// Reported live, with a screenshot: an open position's chart showed a
// huge, disconnected block plunging off the bottom of the plot on its
// last (live) candle, with no wick visible past it -- "maybe chart bug
// here with the candle". renderChartInto anchors the last bar's CLOSE to
// the live quote (base) but used to copy the historical bar's high/low
// unchanged. drawCandles draws the wick from h to l and the body from
// open to close as two separate shapes (see its own candle-drawing
// block), so a close outside [l, h] draws a body sticking out past the
// end of its own wick -- an internally-inconsistent OHLC bar, not a
// legitimate rendering of a real price move. These gates confirm the
// synthetic last bar renderChartInto builds is always self-consistent:
// h >= max(o, c) and l <= min(o, c), whatever the live quote does.

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

function build(bars) {
  let capturedAdjusted = null;
  const src = `
    function fetchHistory(){ return Promise.resolve(BARS); }
    function initChartState(sym, tf, adjusted){ CAPTURE(adjusted); }
    function renderChartView(){}
    function renderChartError(){}
    ${lift('renderChartInto')}
    return renderChartInto;
  `;
  const renderChartInto = new Function('BARS', 'CAPTURE', src)(bars, (adjusted) => { capturedAdjusted = adjusted; });
  return { renderChartInto, getCaptured: () => capturedAdjusted };
}

function bar(o, h, l, c) { return { o, h, l, c, t: new Date() }; }

async function main() {
  // ---- Live quote falls BELOW the historical bar's own low ----
  {
    const bars = [bar(10, 10.5, 9.8, 10.2), bar(10.2, 10.6, 10.0, 10.4)];
    const { renderChartInto, getCaptured } = build(bars);
    await renderChartInto(null, 'SYM', 9.0, '5m'); // live quote well below the last bar's low (10.0)
    const lastBar = getCaptured()[getCaptured().length - 1];
    assert.strictEqual(lastBar.c, 9.0, 'close must still anchor to the live quote');
    assert.ok(lastBar.l <= lastBar.c, `low (${lastBar.l}) must extend to cover a close (${lastBar.c}) below it -- got a body sticking out past its own wick otherwise`);
    assert.ok(lastBar.h >= Math.max(lastBar.o, lastBar.c), 'high must still cover the body\'s top');
    console.log('G1 PASS a live quote below the historical low extends the synthetic bar\'s own low to match, not left stranded');
  }

  // ---- Live quote falls ABOVE the historical bar's own high ----
  {
    const bars = [bar(10, 10.5, 9.8, 10.2), bar(10.2, 10.6, 10.0, 10.4)];
    const { renderChartInto, getCaptured } = build(bars);
    await renderChartInto(null, 'SYM', 12.0, '5m'); // live quote well above the last bar's high (10.6)
    const lastBar = getCaptured()[getCaptured().length - 1];
    assert.strictEqual(lastBar.c, 12.0);
    assert.ok(lastBar.h >= lastBar.c, `high (${lastBar.h}) must extend to cover a close (${lastBar.c}) above it`);
    assert.ok(lastBar.l <= Math.min(lastBar.o, lastBar.c), 'low must still cover the body\'s bottom');
    console.log('G2 PASS a live quote above the historical high extends the synthetic bar\'s own high to match');
  }

  // ---- The ordinary case: live quote already inside the historical range is untouched ----
  {
    const bars = [bar(10, 10.5, 9.8, 10.2), bar(10.2, 10.6, 10.0, 10.4)];
    const { renderChartInto, getCaptured } = build(bars);
    await renderChartInto(null, 'SYM', 10.3, '5m'); // comfortably inside [10.0, 10.6]
    const lastBar = getCaptured()[getCaptured().length - 1];
    assert.strictEqual(lastBar.h, 10.6, 'a live quote already inside the real range must not inflate the high');
    assert.strictEqual(lastBar.l, 10.0, 'a live quote already inside the real range must not inflate the low');
    console.log('G3 PASS an ordinary in-range live quote leaves the historical high/low exactly as Twelve Data reported them');
  }

  console.log('\nAll live chart last-bar OHLC gates passed.');
}

main();

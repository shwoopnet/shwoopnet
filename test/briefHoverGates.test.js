'use strict';
// The Brief's charts answer a finger or a pointer (the owner, Oct 24, 2026). Consequences: the figure shown while scrubbing is the price at that point and its move against the previous close, worked out the same way as the resting figure; the line
// never claims a time it does not have (the series has no timestamps); touching a chart must not stop the page scrolling up and down; and the page still makes no market-data call of its own.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
function fnSource(name) {
  const start = html.indexOf('function ' + name + '(');
  assert.ok(start >= 0, name + ' exists');
  let i = html.indexOf('{', html.indexOf(')', start)), depth = 0;
  for (; i < html.length; i++) {
    if (html[i] === '{') depth++;
    else if (html[i] === '}' && --depth === 0) return html.slice(start, i + 1);
  }
  throw new Error('unbalanced ' + name);
}
const f = new Function('escapeHtml', "var KAL_TZ = 'America/Chicago'; var briefChartQuotes = {};\n" + ['pct', 'kalTime', 'kalDate', 'chartNiceStep', 'chartValueTicks', 'chartPctLabel', 'chartCtOffset', 'chartTimeTicks', 'briefChartFigures', 'briefChartHtml'].map(fnSource).join('\n') + '\nreturn { briefChartFigures: briefChartFigures, briefChartHtml: briefChartHtml, quotes: briefChartQuotes };')((x) => String(x));

gates.H1 = () => {
  const a = f.briefChartFigures(612.4, 625);
  assert.deepStrictEqual([a.up, a.pctText, a.px, a.dtxt], [false, '\u25BC 2.02%', '612.40', '-12.60'], 'a price under the previous close reads down, to the cent, in points and percent');
  const b = f.briefChartFigures(81479, 80000);
  assert.deepStrictEqual([b.up, b.px, b.dtxt], [true, '81,479', '+1,479'], 'a price of 1,000 or more has no decimals, like the resting figure');
};
gates.H2 = () => {
  const out = f.briefChartHtml({ sym: 'SPY', name: 'SPY' }, { price: 510, prevClose: 500, series: [500, 505, 510] });
  assert.ok(/data-sym="SPY"/.test(out), 'each chart says which symbol it is, so the pointer can find its series');
  assert.deepStrictEqual(f.quotes.SPY.ser, [500, 505, 510], 'and the series it scrubs is the one drawn');
  assert.strictEqual(f.quotes.SPY.price, 510, 'with the resting price kept to go back to');
};
// Weekly charts (the owner, Oct 26, 2026): a line marked range 7d is measured from its own first point, so the header and the zero line both mean "since the start of the week", not "since yesterday's close".
gates.H5 = () => {
  const out = f.briefChartHtml({ sym: 'GC=F', name: 'Gold' }, { price: 4200, prevClose: 4180, range: '7d', series: [4000, 4100, 4200], seriesT: [1000, 2000, 3000] });
  assert.ok(/\u25B2 5\.00%/.test(out), 'up 5% from the first point of the week, not 0.48% from the previous close');
  assert.strictEqual(f.quotes['GC=F'].prev, 4000, 'and the scrub reads against that same start');
  const day = f.briefChartHtml({ sym: 'SPY', name: 'SPY' }, { price: 510, prevClose: 500, series: [505, 510] });
  assert.ok(/\u25B2 2\.00%/.test(day) && /Day start/.test(day), 'a line without the marker is still today against the previous close');
  const noT = f.briefChartHtml({ sym: 'QQQ', name: 'QQQ' }, { price: 510, prevClose: 500, range: '7d', series: [500, 510] });
  assert.ok(/Week start/.test(noT), 'without times the weekly line says so, not "Day start"');
};
gates.H3 = () => {
  const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>'));
  assert.ok(/\.brief-chart svg\{[^}]*touch-action:pan-y/.test(css), 'a finger on a chart still scrolls the page up and down');
  const code = html.slice(html.indexOf("var host = document.getElementById('briefCharts');"), html.indexOf('  // The risk mood (the owner:'));
  assert.ok(!/fetch\(|XMLHttpRequest|api\.|toLocaleTimeString|getHours|Date\(/.test(code), 'it makes no call and never prints a time: the series has none');
  assert.ok(/pointermove/.test(code) && /pointerleave/.test(code) && /pointercancel/.test(code), 'it follows the pointer and lets go when it leaves');
};
gates.H4 = () => {
  const t0 = Date.UTC(2026, 9, 24, 13, 0) / 1000;
  const withT = f.briefChartHtml({ sym: 'SPY', name: 'SPY' }, { price: 512, prevClose: 500, series: [500, 505, 510, 512], seriesT: [t0, t0 + 14400, t0 + 28800, t0 + 43200] });
  assert.ok(/class="brief-yaxis"/.test(withT) && /\+\d+(\.\d)?%/.test(withT) && />0%</.test(withT), 'a y axis in percent against the previous close, with 0% for the previous close');
  assert.ok(/class="brief-xaxis"/.test(withT) && /\d+ (AM|PM)/.test(withT) && !/Day start/.test(withT), 'with timestamps the x axis is Central clock times');
  const noT = f.briefChartHtml({ sym: 'SPY', name: 'SPY' }, { price: 512, prevClose: 500, series: [500, 505, 510, 512] });
  assert.ok(/Day start/.test(noT) && />Now</.test(noT) && !/\d+ (AM|PM)/.test(noT), 'without timestamps it says only what it knows: the start of the data and now, never a made-up time');
  const partial = f.briefChartHtml({ sym: 'SPY', name: 'SPY' }, { price: 512, prevClose: 500, series: [500, 505, 510, 512], seriesT: [t0, t0 + 14400] });
  assert.ok(/Day start/.test(partial), 'a timestamp list that does not match the series is ignored');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

// The Brief's charts draw ONE unbroken line, even for a market that closes at night or on weekends (the owner, Oct 29, 2026: "still broken charts,
// don't like the gaps"). The line used to stop and start at every hole in the data, which left a stocks or gold chart in short scraps. The hole is
// already squeezed to a short step on the time axis, so the line crosses it. Plain node, no framework.
const fs = require('fs'), path = require('path'), assert = require('assert');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const grab = (n) => { const i = html.indexOf('function ' + n + '('); assert.ok(i >= 0, 'function ' + n + ' exists'); let d = 0; const j = html.indexOf('{', i); for (let k = j; ; k++) { if (html[k] === '{') d++; if (html[k] === '}') { d--; if (!d) return html.slice(i, k + 1); } } };
const names = ['chartTimeTicks', 'chartNiceStep', 'briefChartFigures', 'briefChartHtml', 'chartValueTicks', 'chartPctLabel', 'chartCtOffset', 'kalTime', 'kalDate', 'pct', 'escapeHtml'];
let code = 'var briefChartQuotes={};var KAL_TZ="America/Chicago";';
for (const n of names) { try { code += grab(n) + '\n'; } catch (e) { code += '/*missing ' + n + '*/'; } }
const chart = new Function(code + ';return briefChartHtml;')();

const gates = {};
gates.G1 = () => {
  // Five trading days of 7 hourly points each, with a night and a weekend missing between them: the old code drew one stroke per day.
  const t0 = 1792000000, ser = [], T = [];
  for (const d of [0, 1, 4, 5, 6]) for (let h = 0; h < 7; h++) { T.push(t0 + d * 86400 + h * 3600); ser.push(100 + Math.sin(d * 7 + h) * 2); }
  const out = chart({ name: 'SPY', sym: 'SPY' }, { price: 101, prevClose: 100, series: ser, seriesT: T, range: '7d' });
  assert.strictEqual((out.match(/<polyline/g) || []).length, 1, 'a market with closed stretches is still one unbroken line');
  const pts = out.match(/<polyline points="([^"]+)"/)[1].split(' ');
  assert.strictEqual(pts.length, ser.length, 'every point is on the line, none is dropped at a gap');
};
gates.G2 = () => {
  // A market with no holes is unchanged: one line, every point.
  const ser = [], T = []; for (let i = 0; i < 40; i++) { T.push(1792000000 + i * 3600); ser.push(100 + Math.sin(i / 3)); }
  const out = chart({ name: 'BTC', sym: 'BTC' }, { price: 100.5, prevClose: 100, series: ser, seriesT: T, range: '7d' });
  assert.strictEqual((out.match(/<polyline/g) || []).length, 1);
  assert.strictEqual(out.match(/<polyline points="([^"]+)"/)[1].split(' ').length, 40);
};
let failed = 0;
for (const [k, f] of Object.entries(gates)) { try { f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + ': ' + e.message); } }
if (failed) process.exit(1);

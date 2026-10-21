'use strict';
// The Data page (Oct 21, 2026, the owner's request: "start building out a data center page"). It is a read-only view of the bot's settled orders. These gates state what that means as consequences.
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
const lift = (names, extra) => new Function("var KAL_TZ = 'America/Chicago';\n" + names.map(fnSource).join('\n') + '\n' + (extra || '') + '; return {' + names.join(',') + '};')();
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const money = (v) => '$' + v.toFixed(2);

// Nothing on the page can send an order or change a setting: the page has no button, input, select, textarea or form inside it.
gates.D1 = () => {
  const page = html.slice(html.indexOf('<main class="page" id="page-data"'), html.indexOf('<main class="page" id="page-settings"'));
  assert.ok(page.length > 200);
  assert.ok(!/<(button|input|select|textarea|form|a )\b/i.test(page), 'the Data page has no control in it');
  const code = ['dataWeekKey', 'dataWeeklyRows', 'dataWeekBarsSvg', 'dataMarketRows', 'dataShareDonutHtml', 'dataTilesHtml', 'dataMarketsHtml', 'renderDataCenter'].map(fnSource).join('\n');
  assert.ok(!/api\.|window\.__shwoopAPI|fetch\(|setDoc|updateDoc|addDoc|callable|Fn\(/.test(code), 'and its code calls nothing: it only draws what the Kalshi page already loaded');
};

// A trade belongs to the week it was made in on the clock the page uses (US Central, weeks start Monday): Sunday 11pm Central is still last week even though it is Monday in UTC.
gates.D2 = () => {
  const f = lift(['kalshiOrderPnl', 'dataWeekKey', 'dataWeeklyRows']);
  assert.strictEqual(f.dataWeekKey(Date.UTC(2026, 9, 19, 4, 59)), '2026-10-12', 'Monday 04:59 UTC is Sunday 11:59pm in Chicago: the week of Oct 12');
  assert.strictEqual(f.dataWeekKey(Date.UTC(2026, 9, 19, 16, 0)), '2026-10-19', 'Monday midday is the week of Oct 19');
  const o = (ts, p) => ({ ts, settled: true, fillCount: '1.00', settledPnl: p });
  const rows = f.dataWeeklyRows([o(Date.UTC(2026, 9, 19, 16), 0.05), o(Date.UTC(2026, 9, 20, 16), -0.93), o(Date.UTC(2026, 9, 14, 16), 0.1), { ts: Date.UTC(2026, 9, 20), settled: true, fillCount: '1.00', result: 'hand' }]);
  assert.deepStrictEqual(rows.map((r) => [r.key, r.net, r.n]), [['2026-10-12', 0.1, 1], ['2026-10-19', -0.88, 2]], 'weeks oldest first, results summed, a hand-closed order (no saved result) is not counted');
};

// Per contract is the settled result over the contracts that FILLED, so a 4 contract trade is not 4 trades; trades closed by hand are not in the table at all.
gates.D3 = () => {
  const f = lift(['kalshiOrderPnl', 'kalshiMarketName', 'dataMarketRows', 'dataMarketsHtml']);
  const now = Date.UTC(2026, 9, 21, 12);
  const g = (ts, c, p) => ({ ts, series: 'KXGOLD15M', settled: true, fillCount: c, settledPnl: p });
  const rows = f.dataMarketRows([g(now - 1000, '4.00', 0.24), g(now - 8 * 86400000, '1.00', -0.93), { ts: now, series: 'KXBTC15M', settled: true, fillCount: '1.00' }], now);
  assert.strictEqual(rows.length, 1, 'only settled trades with a saved result');
  assert.deepStrictEqual([rows[0].name, rows[0].n, rows[0].contracts, rows[0].wins], ['Gold', 2, 5, 1]);
  assert.ok(Math.abs(rows[0].net - (-0.69)) < 1e-9 && Math.abs(rows[0].week - 0.24) < 1e-9, 'net over all, and the last 7 days on their own');
  const out = f.dataMarketsHtml(rows, esc, money);
  assert.ok(out.includes('-13.8c'), 'per contract is net over contracts filled: -0.69 / 5 = -13.8c');
};

// The share ring is a count: its slices add to the whole, and with no trades it says so instead of drawing an empty ring.
gates.D4 = () => {
  const f = lift(['dataShareDonutHtml']);
  assert.ok(/No settled trades yet/.test(f.dataShareDonutHtml([], esc)));
  const out = f.dataShareDonutHtml([{ name: 'Gold', n: 3 }, { name: 'Bitcoin', n: 1 }], esc);
  assert.ok(out.includes('stroke-dasharray="75.000 25.000"') && out.includes('>4</text>') && out.includes('75%') && out.includes('25%'));
  assert.ok(!/var\(--gain\)|var\(--loss\)/.test(out), 'a count is not a result: no red or green');
};

// Weekly bars: a losing week is the red bar below the line with its value under it, a winning week the muted bar above, and only the last 8 weeks are drawn.
gates.D5 = () => {
  const f = lift(['dataWeekLabel', 'dataWeekBarsSvg']);
  assert.ok(/Bars appear after the first settled trade/.test(f.dataWeekBarsSvg([], esc, money)));
  const weeks = Array.from({ length: 10 }, (_, i) => ({ key: '2026-09-' + String(7 + i).padStart(2, '0'), net: i === 9 ? -1.5 : 0.3, n: 20 }));
  const out = f.dataWeekBarsSvg(weeks, esc, money);
  assert.strictEqual((out.match(/<rect /g) || []).length, 8, 'the last 8 weeks');
  assert.ok(out.includes('-$1.50') && out.includes('var(--loss)') && out.includes('+$0.30'));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

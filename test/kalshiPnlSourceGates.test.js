'use strict';
// PS1: the account result card's long ranges (1M, 3M, YTD, All) read the orders older than the page's live listener once, and use the live listener for everything newer (the owner, Oct 29, 2026: the 1M and 3M total looked wrong).
// Consequence: a trade that settled a minute ago must be in the 1M total (it used to be left out for up to ten minutes, because the whole card was a copy), no order is counted twice at the boundary, and a failed read says it is partial.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
const block = (re) => { const m = re.exec(html); assert.ok(m, 'not found: ' + re); return m[1]; };
const names = ['kalshiOrderPnl', 'kalshiMarketName', 'kalshiPnlSource', 'kalshiPnlSeries'];
let f;
try {
  f = new Function('function kalshiMarketName(o){ return o && o.series ? o.series : "x"; }\n' + ['kalshiOrderPnl', 'kalshiPnlSource', 'kalshiPnlSeries'].map((n) => block(new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n'))).join('\n') + '; return { kalshiPnlSource, kalshiPnlSeries };')();
} catch (e) { console.log('FAIL setup: ' + e.message); process.exit(1); }
const o = (ts, pnl) => ({ ts, settled: true, fillCount: 1, settledPnl: pnl, series: 'g' });
gates.PS1 = () => {
  const older = [o(1, 0.1), o(2, 0.2), o(3, -0.5)];      // read once
  const live = [o(3, -0.5), o(4, 0.3), o(5, 0.4)];        // the listener, newest
  const hit = { at: 1, orders: older.concat([o(4, 9)]) };   // a stale copy that also holds an order the listener has since updated
  const pick = f.kalshiPnlSource(live, hit);
  assert.strictEqual(pick.partial, false);
  assert.deepStrictEqual(pick.orders.map((x) => x.ts).sort(), [1, 2, 3, 4, 5], 'older part (strictly older than the listener) plus the whole listener, nothing twice');
  const total = f.kalshiPnlSeries(pick.orders, 0).pop().cum;
  assert.strictEqual(total, Math.round((0.1 + 0.2 - 0.5 + 0.3 + 0.4) * 10000) / 10000, 'the total uses the live copy of the newer orders (the stale 9 is ignored)');
  const failed = f.kalshiPnlSource(live, { at: 1, orders: [], failed: true });
  assert.strictEqual(failed.partial, true, 'a failed read of older orders says the result is partial');
  assert.deepStrictEqual(failed.orders, live, 'and shows what the listener has');
  assert.strictEqual(f.kalshiPnlSource(live, null).partial, false, 'no cache yet is not a failure');
  assert.ok(/nowMs - hit\.at < \(hit\.failed \? 60000 : 21600000\)/.test(html) && !/nowMs - hit\.at < 600000/.test(html), 'the older part is kept for the page life and a failed read retries after a minute');
  assert.ok(/orders: \[\], failed: true/.test(html) && !/orders: loaded \}/.test(html), 'a failed read is no longer disguised as the recent orders');
};
gates.PS2 = () => {
  // The older-orders read was refused (invalid-argument) with one 20,000 row page: it must read in pages of at most 5,000 and never ask for 20,000 at once.
  const m = /kalshiOrdersSince: function\(sinceMs\)\{[\s\S]*?\n    \}\n  \}\);/.exec(html); assert.ok(m, 'the read is found');
  assert.ok(/limit\(5000\)/.test(m[0]) && !/limit\(20000\)/.test(m[0]), 'pages of 5,000');
  assert.ok(/pages >= 5/.test(m[0]) && /rows\.length < 5000/.test(m[0]), 'it stops at a short page or five pages');
  assert.ok(/where\('ts', '>=', cursor\)/.test(m[0]), 'each page starts at the last time seen, without skipping orders that share it');
  assert.ok(/seen\[k\]/.test(m[0]), 'repeats are dropped');
};
gates.PS3 = () => {
  // Review finding: one shared "fetching" string let a second range start the same older-orders read again. It is one entry per range now, cleared only by its own read.
  assert.ok(/kalshiPnlFetching = \{\};/.test(html) && /if\(!kalshiPnlFetching\[key\]\)\{\n          kalshiPnlFetching\[key\] = true;/.test(html), 'one in-flight flag per range');
  assert.ok((html.match(/delete kalshiPnlFetching\[key\]; renderKalshiPnl\(\);/g) || []).length === 2, 'cleared by both the success and the failure of its own read');
  // Coming back to the page: the account is read again and every card redrawn, and the site is asked whether the page was updated.
  assert.ok(/document\.addEventListener\('visibilitychange'/.test(html) && /window\.addEventListener\('pageshow'/.test(html) && /method: 'HEAD', cache: 'no-store'/.test(html), 'resume handlers and the update check');
  assert.ok(/@media screen and \(min-width:701px\) and \(max-width:900px\) and \(pointer:coarse\)/.test(html), 'tablets get the touch sizes');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

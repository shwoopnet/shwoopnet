'use strict';
// Any signed-in account can call the two Finnhub callables and each call spends the shared key, so what they forward is
// shape-checked: a ticker-like symbol and plain dates, never an arbitrary string.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
const gates = {};

gates.F1 = () => {
  const sym = new Function('return ' + /const SYMBOL_RE = (.*);/.exec(src)[1])();
  const date = new Function('return ' + /const DATE_RE = (.*);/.exec(src)[1])();
  for (const ok of ['AAPL', 'BRK.B', 'BTC-USD', 'OANDA:XAU_USD', '^GSPC']) assert.ok(sym.test(ok), ok + ' is a symbol');
  for (const bad of ['', 'AAPL&token=x', 'a b', '../x', 'A'.repeat(31), 'AAPL\n']) assert.ok(!sym.test(bad), JSON.stringify(bad) + ' is refused');
  assert.ok(date.test('2026-10-08') && !date.test('2026-10-08&x=1') && !date.test('Oct 8'));
};

gates.F2 = () => {
  const q = src.slice(src.indexOf('exports.finnhubQuote'), src.indexOf('exports.finnhubCompanyNews'));
  assert.ok(/SYMBOL_RE\.test\(symbol\)/.test(q), 'the quote call checks its symbol');
  const n = src.slice(src.indexOf('exports.finnhubCompanyNews'), src.indexOf('// ---- Kalshi read-only relay'));
  assert.ok(/SYMBOL_RE\.test\(symbol\)/.test(n) && /DATE_RE\.test\(from\)/.test(n) && /DATE_RE\.test\(to\)/.test(n), 'the news call checks symbol and both dates');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();

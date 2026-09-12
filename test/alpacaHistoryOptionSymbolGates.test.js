// The "Full account history" table (pulled straight from Alpaca, Trade
// Overview -> Labs export) rendered t.sym raw. An options fill's symbol
// there is Alpaca's own unbroken OCC form -- "INTC260918P00094000" -- with
// no separators, unreadable next to a plain equities symbol like "SNAP" in
// the same column. The Alpaca dock's Open Positions table already solved
// this with formatPositionSymbol ("INTC $94P 9/18"); this table just never
// got the same treatment.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name, deps) {
  const start = src.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('not found in index.html: ' + name);
  let d = 0, end = -1;
  for (let i = src.indexOf('{', start); i < src.length; i++) {
    if (src[i] === '{') d++;
    else if (src[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  const names = Object.keys(deps || {});
  return new Function(...names, 'return (' + src.slice(start, end) + ')')(...names.map((n) => deps[n]));
}

const formatPositionSymbol = lift('formatPositionSymbol', {
  OCC_OPTION_SYMBOL_RE: /^([A-Z]{1,6})(\d{2})(\d{2})(\d{2})([CP])(\d{8})$/,
});
const isWinningReturn = lift('isWinningReturn');
const fmt = lift('fmt');
const profitFactorText = lift('profitFactorText');

function fakeEl() { return { innerHTML: '', textContent: '', value: '', hidden: false, removeAttribute() {} }; }

function renderAlpacaHistoryResultsWith(trades) {
  const els = {};
  ['alpacaHistoryResultWrap', 'alpacaHistoryStats', 'alpacaHistoryAnomalies', 'alpacaHistoryTableWrap', 'alpacaHistoryRawTextarea']
    .forEach((id) => { els[id] = fakeEl(); });
  const fakeDocument = { getElementById: (id) => els[id] };
  const render = lift('renderAlpacaHistoryResults', {
    document: fakeDocument, isWinningReturn, fmt, profitFactorText, formatPositionSymbol,
    PROFIT_FACTOR_NO_LOSSES_HINT: 'n/a',
  });
  render(trades, [], []);
  return els.alpacaHistoryTableWrap.innerHTML;
}

function main() {
  const optionsTrade = {
    sym: 'INTC260918P00094000', direction: 'Long',
    entryPrice: 2.1, entryTime: Date.now() - 86400000, exitPrice: 2.6, exitTime: Date.now(),
    exitType: 'target', pctReturn: 23.8, dollarPL: 50,
  };
  const html = renderAlpacaHistoryResultsWith([optionsTrade]);
  assert.ok(!html.includes('INTC260918P00094000'),
    'the raw unbroken OCC symbol must not reach the table -- it must be parsed for display');
  assert.ok(html.includes('INTC $94P 9/18'),
    `expected the parsed "INTC $94P 9/18" form in the table, got: ${html}`);
  console.log('G1 PASS an options fill in Full account history renders as "INTC $94P 9/18", not the raw OCC string');

  const equitiesTrade = {
    sym: 'SNAP', direction: 'Long',
    entryPrice: 10, entryTime: Date.now() - 86400000, exitPrice: 11, exitTime: Date.now(),
    exitType: 'target', pctReturn: 10, dollarPL: 20,
  };
  const html2 = renderAlpacaHistoryResultsWith([equitiesTrade]);
  assert.ok(html2.includes('>SNAP<'), 'a plain equities symbol must render unchanged');
  console.log('G2 PASS a plain equities symbol is unaffected');

  console.log('\nAll Full-account-history option-symbol gates passed.');
}

main();

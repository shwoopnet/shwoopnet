'use strict';
// reconstructTradesFromOrders (index.html) -- rebuilds closed trades from
// Alpaca's own raw order fills for the "Full account history" card. Its own
// header promises: anything that cannot be reconstructed is REPORTED, never
// dropped or guessed at. This gate exists because that promise was silently
// broken for two real shapes -- a partial-fill quantity mismatch, and a sell
// with no tracked open position -- see each gate's own comment.

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

function build() {
  const src = `
    ${lift('canonicalSymbol')}
    ${lift('reconstructTradesFromOrders')}
    return { reconstructTradesFromOrders: reconstructTradesFromOrders };
  `;
  return new Function(src)();
}

function fill(sym, side, qty, price, filledAt, type) {
  return {
    symbol: sym, side: side, status: 'filled',
    filled_qty: String(qty), qty: String(qty), filled_avg_price: String(price),
    filled_at: filledAt, type: type || 'market',
  };
}

function main() {
  const { reconstructTradesFromOrders } = build();

  // ---- A clean full close still works exactly as before ----
  {
    const result = reconstructTradesFromOrders([
      fill('AAPL', 'buy', 100, 10, '2026-09-01T14:00:00Z'),
      fill('AAPL', 'sell', 100, 12, '2026-09-01T15:00:00Z', 'limit'),
    ]);
    assert.strictEqual(result.trades.length, 1);
    assert.strictEqual(result.trades[0].qty, 100);
    assert.strictEqual(result.trades[0].dollarPL, 200);
    assert.strictEqual(result.unreconstructable.length, 0);
    console.log('G1 PASS a clean full close reconstructs one trade with the full quantity and correct P&L');
  }

  // ---- A PARTIAL exit prices only the quantity it actually closed ----
  // This is the real bug: a stop that only partially fills used to have
  // its dollarPL computed against the WHOLE original entry quantity, not
  // the shares that fill actually covered -- overstating (or understating)
  // real P&L on every partial fill in the account's history.
  {
    const result = reconstructTradesFromOrders([
      fill('XYZ', 'buy', 100, 10, '2026-09-01T14:00:00Z'),
      fill('XYZ', 'sell', 60, 12, '2026-09-01T15:00:00Z', 'stop'),
      fill('XYZ', 'sell', 40, 13, '2026-09-01T15:05:00Z', 'stop'),
    ]);
    assert.strictEqual(result.trades.length, 2, 'each partial exit must produce its own trade record');
    // Sorted newest-exit-first, so the SECOND (15:05) fill's trade comes first.
    const firstExit = result.trades.find((t) => t.exitTime === '2026-09-01T15:00:00Z');
    const secondExit = result.trades.find((t) => t.exitTime === '2026-09-01T15:05:00Z');
    assert.strictEqual(firstExit.qty, 60);
    assert.strictEqual(firstExit.dollarPL, (12 - 10) * 60, 'the first partial exit\'s P&L must be priced on the 60 shares it actually closed, not the original 100-share entry');
    assert.strictEqual(secondExit.qty, 40);
    assert.strictEqual(secondExit.dollarPL, (13 - 10) * 40, 'the second partial exit must close the REMAINING 40 shares from the same entry, not start a phantom new position');
    assert.strictEqual(result.unreconstructable.length, 0, 'two fills that exactly sum to the open quantity leave nothing unreconstructable');
    console.log('G2 PASS a partial exit is priced on the quantity it actually closed, and the remainder is tracked forward correctly');
  }

  // ---- A fill LARGER than what is open reports the excess, doesn't silently absorb it ----
  {
    const result = reconstructTradesFromOrders([
      fill('ABC', 'buy', 50, 20, '2026-09-01T14:00:00Z'),
      fill('ABC', 'sell', 80, 22, '2026-09-01T15:00:00Z'),
    ]);
    assert.strictEqual(result.trades.length, 1);
    assert.strictEqual(result.trades[0].qty, 50, 'the trade record must only claim the 50 shares that were actually tracked as open');
    assert.strictEqual(result.trades[0].dollarPL, (22 - 20) * 50);
    assert.strictEqual(result.unreconstructable.length, 1, 'the 30 excess shares this fill cannot be given a cost basis for must be reported, never dropped');
    assert.strictEqual(result.unreconstructable[0].qty, 30);
    console.log('G3 PASS a fill larger than the tracked open quantity reports the excess as unreconstructable instead of silently absorbing it');
  }

  // ---- A sell with NO open position is reported, never treated as a phantom short entry ----
  {
    const result = reconstructTradesFromOrders([
      fill('DEF', 'sell', 25, 15, '2026-09-01T14:00:00Z'),
    ]);
    assert.strictEqual(result.trades.length, 0, 'a stray sell with nothing open must never fabricate a trade');
    assert.strictEqual(result.unreconstructable.length, 1);
    assert.strictEqual(result.unreconstructable[0].sym, 'DEF');
    console.log('G4 PASS a sell with no tracked open position is reported as unreconstructable, not treated as a fresh Short entry');
  }

  console.log('\nAll reconstructTradesFromOrders gates passed.');
}

main();

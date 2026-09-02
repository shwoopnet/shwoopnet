// What this file protects: the app's headline P&L is now the broker's own
// number for BOTH asset classes. Every gate below states the dollar
// consequence of getting one of crypto's four differences wrong, plus a
// control proving the equities half did not move while crypto was added.
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

const canonicalSymbol = lift('canonicalSymbol', {});
const CRYPTO_DUST_FRACTION = Number(/var CRYPTO_DUST_FRACTION = ([\d.]+);/.exec(src)[1]);
const reconstruct = lift('reconstructTradesFromOrders', { canonicalSymbol, CRYPTO_DUST_FRACTION });

let t = 0;
const ord = (o) => Object.assign({
  status: 'filled', type: 'market', asset_class: 'us_equity',
  filled_at: new Date(Date.UTC(2026, 0, 1, 0, t++)).toISOString(),
}, o);
const crypto = (o) => ord(Object.assign({ asset_class: 'crypto' }, o));
const near = (a, b, msg) => assert.ok(Math.abs(a - b) < 1e-6, msg + ' (got ' + a + ', want ' + b + ')');

const gates = {};

// The one that matters most: the crypto commission is paid in coin, so the
// sell is smaller than the buy. If that missing coin is ignored, the trade
// reports more profit than the account actually made, forever.
gates.G1_feeInKindRoundTrip = () => {
  t = 0;
  const out = reconstruct([
    crypto({ symbol: 'SOL/USD', side: 'buy', filled_qty: '250', filled_avg_price: '100' }),
    crypto({ symbol: 'SOL/USD', side: 'sell', type: 'stop_limit', filled_qty: '249.5', filled_avg_price: '110' }),
  ]);
  assert.strictEqual(out.trades.length, 1, 'a fee-shrunk round trip is ONE closed trade, not a trade plus dust');
  const tr = out.trades[0];
  // Real cash: 249.5 x 110 out, 250 x 100 in.
  near(tr.dollarPL, 249.5 * 110 - 250 * 100, 'P&L must be the actual cash flow of both legs');
  near(tr.dollarPL, 2445, 'P&L must be 2445');
  near(tr.feeCost, 50, 'the 0.5 SOL never returned must be surfaced as a cost, not absorbed');
  // The naive buy-qty-times-move answer is $2500 -- $55 of invented profit
  // on one trade. That is the failure this gate exists for.
  assert.notStrictEqual(tr.dollarPL, 2500, 'control: qty-matched arithmetic would have invented $55');
  assert.strictEqual(tr.exitType, 'Stop-loss', "crypto's stop is a stop_limit and must not read as a manual exit");
  assert.strictEqual(out.unreconstructable.length, 0, 'a clean round trip has nothing unreconstructable');
  console.log('G1 PASS fee-in-kind round trip reconciles to the real dollar P&L');
};

// A position closed in two sells must not leave the book half-open: if it
// does, the NEXT entry pairs against the wrong basis and every trade after
// it on that symbol is wrong too.
gates.G2_partialExitDoesNotCorruptTheNextTrade = () => {
  t = 0;
  const out = reconstruct([
    crypto({ symbol: 'ETH/USD', side: 'buy', filled_qty: '100', filled_avg_price: '100' }),
    crypto({ symbol: 'ETH/USD', side: 'sell', filled_qty: '40', filled_avg_price: '110' }),
    crypto({ symbol: 'ETH/USD', side: 'sell', filled_qty: '59.8', filled_avg_price: '90' }),
    crypto({ symbol: 'ETH/USD', side: 'buy', filled_qty: '10', filled_avg_price: '200' }),
    crypto({ symbol: 'ETH/USD', side: 'sell', filled_qty: '9.98', filled_avg_price: '210' }),
  ]);
  assert.strictEqual(out.trades.length, 3, 'two partial exits plus a later round trip are three trades');
  const chrono = out.trades.slice().reverse();
  near(chrono[0].dollarPL, 40 * (110 - 100), 'the first slice closes 40 units against the entry basis');
  near(chrono[1].dollarPL, 59.8 * (90 - 100) - 0.2 * 100, 'the closing slice carries the in-kind fee');
  // The consequence: the trade AFTER the partial exit is priced off its own
  // entry (200), not off leftover dust from the previous position (100).
  near(chrono[2].entryPrice, 200, 'the next trade must use its own entry, not the previous position it never left');
  near(chrono[2].dollarPL, 9.98 * (210 - 200) - 0.02 * 200, 'the next trade reconciles on its own terms');
  near(out.trades.reduce((s, x) => s + x.dollarPL, 0), (40 * 110 + 59.8 * 90 - 100 * 100) + (9.98 * 210 - 10 * 200),
    'the total across all three is the account\'s total cash flow');
  console.log('G2 PASS a partial exit does not corrupt the next trade\'s pairing');
};

// /v2/orders says "UNI/USD", /v2/positions says "UNIUSD". Grouping on the
// raw string books the buy and the sell as two different symbols, so the
// trade never closes and its P&L never appears at all.
gates.G3_oneSymbolNotTwo = () => {
  t = 0;
  const out = reconstruct([
    crypto({ symbol: 'UNI/USD', side: 'buy', filled_qty: '10', filled_avg_price: '10' }),
    crypto({ symbol: 'UNIUSD', side: 'sell', filled_qty: '9.98', filled_avg_price: '12' }),
  ]);
  assert.strictEqual(out.trades.length, 1, 'the two symbol forms are one book, so this is one closed trade');
  assert.strictEqual(out.unreconstructable.length, 0, 'nothing is orphaned by the slash');
  near(out.trades[0].dollarPL, 9.98 * 12 - 10 * 10, 'and it reconciles to real cash');
  console.log('G3 PASS slash and no-slash forms of one symbol are one symbol');
};

// A fill with no recoverable cost basis must be SAID, not skipped. A
// skipped fill makes the headline total quietly wrong in the one direction
// nobody audits.
gates.G4_unreconstructableIsReportedNotDropped = () => {
  t = 0;
  const orphan = reconstruct([
    crypto({ symbol: 'BTC/USD', side: 'sell', filled_qty: '1', filled_avg_price: '60000' }),
  ]);
  assert.strictEqual(orphan.trades.length, 0, 'a sell with no basis cannot become a trade');
  assert.strictEqual(orphan.unreconstructable.length, 1, 'it must be REPORTED, not silently dropped');
  assert.strictEqual(orphan.unreconstructable[0].sym, 'BTCUSD');
  assert.ok(/no cost basis/i.test(orphan.unreconstructable[0].note), 'the report must say why');

  t = 0;
  const oversold = reconstruct([
    crypto({ symbol: 'BTC/USD', side: 'buy', filled_qty: '1', filled_avg_price: '50000' }),
    crypto({ symbol: 'BTC/USD', side: 'sell', filled_qty: '1.5', filled_avg_price: '60000' }),
  ]);
  assert.strictEqual(oversold.unreconstructable.length, 1, 'selling more than was bought is reported');
  near(oversold.unreconstructable[0].qty, 0.5, 'the unpriceable excess is quantified');
  assert.strictEqual(oversold.trades.length, 1, 'the part that DOES have a basis is still reconciled');
  near(oversold.trades[0].dollarPL, 1 * (60000 - 50000), 'and only that part -- the excess is not priced off the wrong entry');
  console.log('G4 PASS an unreconstructable sequence is reported rather than dropped');
};

// Crypto gets the same honesty equities already had about a second same-side
// fill: the duplicate-order race moved real money once, and absorbing it
// into a mispaired exit is how it stayed invisible.
gates.G5_cryptoAnomaliesAreReported = () => {
  t = 0;
  const out = reconstruct([
    crypto({ symbol: 'SOL/USD', side: 'buy', filled_qty: '10', filled_avg_price: '100' }),
    crypto({ symbol: 'SOL/USD', side: 'buy', filled_qty: '10', filled_avg_price: '101' }),
    crypto({ symbol: 'SOL/USD', side: 'sell', filled_qty: '9.98', filled_avg_price: '110' }),
  ]);
  assert.strictEqual(out.anomalies.length, 1, 'a second buy while open is an anomaly for crypto too');
  assert.strictEqual(out.trades.length, 1, 'and it is not mispaired into a second trade');
  console.log('G5 PASS a duplicate crypto fill is flagged, not absorbed');
};

// THE CONTROL. Adding crypto must not move a single equities dollar. The
// equities figures were the trustworthy half; a refactor that shifted them
// would have traded one broken number for another.
gates.G6_equitiesUnchanged = () => {
  const equitiesOrders = () => { t = 0; return [
    ord({ symbol: 'AAPL', side: 'buy', filled_qty: '100', filled_avg_price: '200' }),
    ord({ symbol: 'AAPL', side: 'sell', type: 'limit', filled_qty: '100', filled_avg_price: '210' }),
    ord({ symbol: 'MSFT', side: 'buy', filled_qty: '50', filled_avg_price: '400' }),
    ord({ symbol: 'MSFT', side: 'buy', filled_qty: '50', filled_avg_price: '401' }),
    ord({ symbol: 'MSFT', side: 'sell', type: 'stop', filled_qty: '50', filled_avg_price: '390' }),
  ]; };

  // Frozen expectation: exactly what the equities-only reconstruction
  // produced before crypto was added.
  const alone = reconstruct(equitiesOrders());
  assert.strictEqual(alone.trades.length, 2);
  assert.strictEqual(alone.anomalies.length, 1, 'the duplicate-fill anomaly is still detected');
  const byS = {}; alone.trades.forEach((x) => { byS[x.sym] = x; });
  near(byS.AAPL.dollarPL, 1000, 'AAPL P&L unchanged');
  near(byS.AAPL.pctReturn, 5, 'AAPL % return unchanged');
  assert.strictEqual(byS.AAPL.exitType, 'Target', 'a limit exit is still a Target');
  near(byS.MSFT.dollarPL, -500, 'MSFT P&L unchanged');
  assert.strictEqual(byS.MSFT.exitType, 'Stop-loss', 'a stop exit is still a Stop-loss');
  assert.strictEqual(byS.AAPL.feeCost, undefined, 'equities carry no in-kind fee');
  assert.strictEqual(alone.trades[0].sym, 'MSFT', 'still sorted newest-exit-first');

  // And unchanged again when crypto orders are interleaved into the same
  // pull -- the real condition, since one account holds both.
  const mixed = reconstruct(equitiesOrders().concat([
    crypto({ symbol: 'SOL/USD', side: 'buy', filled_qty: '250', filled_avg_price: '100' }),
    crypto({ symbol: 'SOL/USD', side: 'sell', filled_qty: '249.5', filled_avg_price: '110' }),
    crypto({ symbol: 'DOGE/USD', side: 'sell', filled_qty: '5', filled_avg_price: '1' }),
  ]));
  const mixedEquities = mixed.trades.filter((x) => x.assetClass !== 'crypto');
  assert.deepStrictEqual(mixedEquities, alone.trades,
    'every equities trade must be byte-identical whether or not crypto is in the same pull');
  assert.strictEqual(mixed.anomalies.length, 1, 'crypto in the pull adds no equities anomaly');
  near(mixedEquities.reduce((s, x) => s + x.dollarPL, 0), 500, 'the equities net is still +$500');
  console.log('G6 PASS equities results are identical, alone and alongside crypto');
};

// G7-G9 added by the vacuous-test sweep (Sep 2026). Each replaces an
// assertion that was true by construction: every fixture above hands
// reconstructTradesFromOrders a perfectly-formed FILLED crypto order that
// carries BOTH crypto markers and exits well clear of the dust boundary,
// so the three predicates that decide whether an order counts at all, and
// which arithmetic prices it, could each be broken without failing a gate.

// Only FILLED orders with a real fill price are cash that moved. A resting
// or cancelled order has no filled_avg_price; booking one as a trade
// prices it at NaN and poisons the headline total for every symbol.
gates.G7_unfilledOrdersAreNotTrades = () => {
  t = 0;
  const out = reconstruct([
    crypto({ symbol: 'SOL/USD', side: 'buy', filled_qty: '250', filled_avg_price: '100' }),
    crypto({ symbol: 'SOL/USD', side: 'sell', status: 'canceled', filled_qty: '0', filled_avg_price: null }),
    crypto({ symbol: 'SOL/USD', side: 'sell', status: 'new', filled_at: null, filled_avg_price: null, qty: '250' }),
    // Still working: part of it has printed, but the order is not done and
    // the position is not closed. Each of the three conditions is tested
    // alone here, so none of them can be dropped or loosened unnoticed.
    crypto({ symbol: 'SOL/USD', side: 'sell', status: 'partially_filled', filled_qty: '100', filled_avg_price: '109' }),
    crypto({ symbol: 'SOL/USD', side: 'sell', type: 'stop_limit', filled_qty: '249.5', filled_avg_price: '110' }),
  ]);
  assert.strictEqual(out.trades.length, 1, 'the cancelled and resting sells are not exits: one trade, not three');
  assert.strictEqual(out.anomalies.length, 0, 'and they are not mistaken for same-side re-entries either');
  near(out.trades[0].dollarPL, 2445, 'P&L is still the real cash flow of the two legs that actually filled');
  out.trades.forEach((x) => assert.ok(isFinite(x.dollarPL), 'no trade may carry a NaN P&L'));
  console.log('G7 PASS unfilled and cancelled orders never become trades');
};

// Crypto-ness decides which arithmetic runs. An order that reaches this
// function with the slashed symbol but no asset_class (an older cached
// pull, a field Alpaca omits) must still take the crypto path -- down the
// equities path the in-kind fee is invisible and the trade reports the
// $55-of-invented-profit answer G1 exists to reject.
gates.G8_slashAloneIsEnoughToBeCrypto = () => {
  t = 0;
  const out = reconstruct([
    ord({ symbol: 'SOL/USD', side: 'buy', asset_class: undefined, filled_qty: '250', filled_avg_price: '100' }),
    ord({ symbol: 'SOL/USD', side: 'sell', asset_class: undefined, type: 'stop_limit', filled_qty: '249.5', filled_avg_price: '110' }),
  ]);
  assert.strictEqual(out.trades.length, 1, 'the slashed pair is one crypto book');
  assert.strictEqual(out.trades[0].assetClass, 'crypto', 'a slashed symbol is crypto even with asset_class missing');
  near(out.trades[0].feeCost, 50, 'the in-kind fee must still be charged');
  near(out.trades[0].dollarPL, 2445, 'P&L must be the real cash flow, not the qty-matched $2500');
  assert.strictEqual(out.trades[0].exitType, 'Stop-loss', 'and stop_limit still reads as a stop, not a manual exit');
  console.log('G8 PASS a slashed symbol alone is enough to price as crypto');
};

// The dust boundary decides whether a position is CLOSED or still open. At
// exactly the fraction, the leftover is fee, the trade closes and the next
// entry pairs against itself. One tick the wrong side of that comparison
// leaves the book open forever and every later trade on the symbol is
// priced off a stale basis.
gates.G9_dustBoundaryClosesTheTrade = () => {
  t = 0;
  const exact = 100 * (1 - CRYPTO_DUST_FRACTION); // leftover is EXACTLY the dust fraction
  const out = reconstruct([
    crypto({ symbol: 'ETH/USD', side: 'buy', filled_qty: '100', filled_avg_price: '100' }),
    crypto({ symbol: 'ETH/USD', side: 'sell', filled_qty: String(exact), filled_avg_price: '110' }),
    crypto({ symbol: 'ETH/USD', side: 'buy', filled_qty: '10', filled_avg_price: '200' }),
    crypto({ symbol: 'ETH/USD', side: 'sell', filled_qty: '9.98', filled_avg_price: '210' }),
  ]);
  assert.strictEqual(out.trades.length, 2, 'a leftover exactly at the dust fraction closes the trade');
  const chrono = out.trades.slice().reverse();
  near(chrono[0].feeCost, 100 * CRYPTO_DUST_FRACTION * 100, 'the leftover is charged as fee, at cost');
  near(chrono[1].entryPrice, 200, 'the next trade must pair against its own entry, not the never-closed one');
  // Control: one unit MORE left over is a real partial exit and the book
  // must stay open, or this gate would pass by closing everything.
  t = 0;
  const partial = reconstruct([
    crypto({ symbol: 'ETH/USD', side: 'buy', filled_qty: '100', filled_avg_price: '100' }),
    crypto({ symbol: 'ETH/USD', side: 'sell', filled_qty: String(exact - 1), filled_avg_price: '110' }),
    crypto({ symbol: 'ETH/USD', side: 'buy', filled_qty: '10', filled_avg_price: '200' }),
  ]);
  assert.strictEqual(partial.anomalies.length, 1,
    'control: above the dust fraction the position is still open, so the next buy is a same-side fill');
  console.log('G9 PASS the dust boundary closes the trade at exactly the fraction');
};

Object.keys(gates).forEach((k) => gates[k]());
console.log('\nAll crypto broker-reconciliation gates passed.');

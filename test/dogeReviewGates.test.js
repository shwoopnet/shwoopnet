// The Dogecoin review alert (Nov 2, 2026): the owner's written rule, shown as a warning, never an automatic change.
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
const fn = (name) => new RegExp('  function ' + name + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\}\\n').exec(html)[0];
const consts = /  var KAL_DOGE_LADDER_FROM[^\n]*\n/.exec(html)[0];
const lib = new Function('Date', 'Number', 'Math', 'String', consts + fn('kalshiOrderPnl') + fn('kalshiDogeReview') + fn('kalshiDogeReviewText') + '; return { kalshiDogeReview, kalshiDogeReviewText };')(Date, Number, Math, String);
const T0 = Date.parse('2026-10-30T20:24:00Z');
// n orders, the first `losses` of them lost (newest first by ts), each 10 contracts
const mk = (n, losses, win, loss, extra) => Array.from({ length: n }, (_, i) => Object.assign({ strategy: 'L1', series: 'KXDOGE15M', ticker: 'KXDOGE15M-X' + i, ts: T0 + 60000 * (n - i), settled: true, result: 'yes', fillCount: 10, settledPnl: i < losses ? loss : win }, extra || {}));
const gates = {};
gates.DR1 = () => {
  // under 100 settled orders it only tracks, whatever they did
  let r = lib.kalshiDogeReview(mk(99, 50, 0.5, -7)); assert.strictEqual(r.state, 'tracking'); assert.strictEqual(r.reasons.length, 0); assert.strictEqual(r.settled, 99);
  assert.strictEqual(lib.kalshiDogeReview([]).state, 'tracking');
};
gates.DR2 = () => {
  // exactly the lines: 8 losses in 100 is NOT over 8%; net must be at least +0.5c a contract
  let r = lib.kalshiDogeReview(mk(100, 8, 0.1, -0.1)); assert.strictEqual(r.lossShare, 0.08); assert.ok(!r.reasons.some((x) => /lost/.test(x)), 'at 8% the loss line is not crossed');
  r = lib.kalshiDogeReview(mk(100, 9, 0.9, -7)); assert.strictEqual(r.state, 'warn'); assert.ok(/lost 9%/.test(r.reasons[0]));
  // few losses but thin: 3 losses of -$5, 97 wins of $0.10 = net -$5.3 on 1000 contracts = -0.5c
  r = lib.kalshiDogeReview(mk(100, 3, 0.1, -5)); assert.strictEqual(r.state, 'warn'); assert.ok(/netted -0\.\d+c a contract/.test(r.reasons.join(' ')), r.reasons.join(' '));
  // healthy: 4 losses, strong net
  r = lib.kalshiDogeReview(mk(100, 4, 0.9, -7)); assert.strictEqual(r.state, 'ok'); assert.strictEqual(r.reasons.length, 0); assert.ok(r.netCents > 0.5);
  assert.ok(/go back to a fixed size of 5/.test(lib.kalshiDogeReviewText({ reasons: ['lost 9% (the line is 8%)'] })) && /Nothing has changed/.test(lib.kalshiDogeReviewText({ reasons: ['x'] })));
};
gates.DR3 = () => {
  // only the last 100 count; hand closes, other markets and orders from before the ladder are ignored
  const old = mk(60, 60, 0, -7).map((o) => Object.assign(o, { ts: T0 - 86400000 }));            // before the ladder
  const gold = mk(60, 60, 0, -7, { series: 'KXGOLD15M', ticker: 'KXGOLD15M-X' });
  const hand = mk(60, 60, 0, -7, { result: 'hand' });
  const good = mk(100, 2, 0.9, -7);
  let r = lib.kalshiDogeReview(old.concat(gold, hand, good)); assert.strictEqual(r.state, 'ok'); assert.strictEqual(r.settled, 100);
  // 130 orders: the 30 oldest are bad, the newest 100 are good: only the newest 100 count
  const bad = mk(30, 30, 0, -7).map((o) => Object.assign(o, { ts: T0 + 1000 - 1000 * 1 }));
  r = lib.kalshiDogeReview(good.concat(bad)); assert.strictEqual(r.state, 'ok'); assert.strictEqual(r.n, 100);
};
gates.DR4 = () => {
  // wiring: the warning is in the bell feed and the Bot status block, nothing writes to the bot, and no dollar is drawn
  assert.ok(/var dr = kalshiDogeReview\(orders\);/.test(html) && /doge-review/.test(html));
  assert.ok(/kalshiDogeReview\(orders\);\n    if\(dogeRev/.test(html.replace(/\r/g, '')) || /var dogeRev = kalshiOrdersLoaded \? kalshiDogeReview\(orders\) : null;/.test(html));
  const body = fn('kalshiDogeReview') + fn('kalshiDogeReviewText');
  assert.ok(!/kalshiMoney|\$/.test(body.replace(/'[^']*'/g, '')), 'no dollar figure in the review');
  assert.ok(!/httpsCallable|setDoc|fetch\(/.test(body));
};
let failed = 0; for (const [k, f] of Object.entries(gates)) { try { f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + ': ' + e.message); } }
if (failed) process.exit(1);

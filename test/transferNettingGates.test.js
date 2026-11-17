const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
function lift(name) {
  const i = html.indexOf('function ' + name + '(');
  assert(i >= 0, name + ' exists');
  let depth = 0, k = html.indexOf('{', i);
  for (; k < html.length; k++) { if (html[k] === '{') depth++; else if (html[k] === '}') { depth--; if (depth === 0) break; } }
  return html.slice(i, k + 1);
}
const Q = new Function(['kalshiIsTransfer', 'kalshiPerpsSteps'].map(lift).join('\n') + '\nreturn {kalshiIsTransfer, kalshiPerpsSteps};')();
const H = 3600000;

// TN1: a move of money between the two accounts is a transfer: opposite directions, the perps move at least $25, the two nearly cancel
assert.strictEqual(Q.kalshiIsTransfer(-200, 200.3), true);
assert.strictEqual(Q.kalshiIsTransfer(300, -296), true, 'either direction');
assert.strictEqual(Q.kalshiIsTransfer(-200, 150), false, 'does not cancel: a real move on one side too');
assert.strictEqual(Q.kalshiIsTransfer(-200, -200), false, 'same direction is never a transfer');
assert.strictEqual(Q.kalshiIsTransfer(-20, 20), false, 'under $25 counts (a small perps move is a price move)');
assert.strictEqual(Q.kalshiIsTransfer(-200, 0), false, 'a one sided move (a deposit or a price move) is not a transfer');
assert.strictEqual(Q.kalshiIsTransfer(-200, NaN), false);
assert.strictEqual(Q.kalshiIsTransfer(NaN, 5), false);

// TN2: the perps steps skip the transfer hour and keep the price moves (invented numbers shaped like the Nov 17 case)
const hist = [
  { t: 1 * H, total: 650, pred: 280 },
  { t: 2 * H, total: 634, pred: 280 },     // -16 price move, nothing on the prediction side
  { t: 3 * H, total: 630, pred: 281 },     // -4 price move, the bot won 1
  { t: 4 * H, total: 416, pred: 495 },     // -214 perps, +214 predictions: a TRANSFER
  { t: 5 * H, total: 410, pred: 495 },     // -6 price move
];
let r = Q.kalshiPerpsSteps(hist, 0);
assert.deepStrictEqual(r.steps.map((x) => x.p), [-16, -4, -6], 'the $214 transfer is not a step');
assert.strictEqual(r.steps.reduce((a, x) => a + x.p, 0), -26, 'Today reads the price moves only');
// from a start inside the range
r = Q.kalshiPerpsSteps(hist, 3 * H + 1);
assert.deepStrictEqual(r.steps.map((x) => x.p), [-6]);

// TN3: with no prediction balance on a snapshot nothing can be told, so the step counts as before (the older behaviour and its gates)
r = Q.kalshiPerpsSteps([{ t: 1 * H, total: 650 }, { t: 2 * H, total: 436 }], 0);
assert.deepStrictEqual(r.steps.map((x) => x.p), [-214]);
r = Q.kalshiPerpsSteps([{ t: 1 * H, total: 650, pred: null }, { t: 2 * H, total: 436, pred: 495 }], 0);
assert.deepStrictEqual(r.steps.map((x) => x.p), [-214], 'one side missing: counted, never guessed');

// TN4: wiring. Today's perps change is the sum of the netted steps since the last snapshot before midnight, and the live point is paired with the live prediction balance
assert(/out\.perpsDay = prior \? Math\.round\(kalshiPerpsSteps\(hist, prior\.t \+ 1\)\.steps\.reduce\(/.test(html), 'TN4 perpsDay uses the netted steps');
assert(/hist = \(kalshiPerpsState\.hist \|\| \[\]\)\.concat\(\[\{ t: Number\(kalshiPerpsState\.doc\.at\), total: res\.total, pred: livePred \}\]\)/.test(html), 'TN4 the live point carries the live prediction balance');
assert(/return \{ t: Number\(x\.ts\), total: x\.perpsTotal === null[\s\S]{0,200}pred: x\.total === null/.test(html), 'TN4 snapshots carry the prediction balance');
console.log('transferNettingGates ok');

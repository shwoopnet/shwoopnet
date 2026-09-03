// A crypto position's qty column read "172.79659" on the Open Positions
// table -- a dollar risk budget divided by a live price carries however
// many decimals that division produces, not a number anyone asked to read.
// fmtCryptoQty shortens the CELL TEXT only; every P&L/sizing calculation
// elsewhere still reads the real j.qty untouched.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name) {
  const start = src.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('not found in index.html: ' + name);
  let d = 0, end = -1;
  for (let i = src.indexOf('{', start); i < src.length; i++) {
    if (src[i] === '{') d++;
    else if (src[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  return new Function('return (' + src.slice(start, end) + ')')();
}

const fmtCryptoQty = lift('fmtCryptoQty');

const gates = {};

// The live LINK/USD case from the screenshot.
gates.G1 = () => {
  assert.strictEqual(fmtCryptoQty(172.79659), '172.8',
    'a large fractional qty must round to at most one decimal');
};

// A flat one-decimal rule -- the tempting shortcut -- would print "0.0"
// for a BTC-sized holding, which reads as nothing is held.
gates.G2 = () => {
  assert.notStrictEqual(fmtCryptoQty(0.00123456), '0.0',
    'a small holding must not collapse to a display that reads as zero');
  assert.ok(!/^0\.0*$/.test(fmtCryptoQty(0.00123456)),
    'a small holding must show real precision, not trailing zeros: ' + fmtCryptoQty(0.00123456));
};

// Round numbers should not carry decorative trailing zeros.
gates.G3 = () => {
  assert.strictEqual(fmtCryptoQty(14), '14', 'a whole number must not print as "14.0"');
  assert.strictEqual(fmtCryptoQty(1.5), '1.5');
};

// The qty cell must be wired to the formatter for crypto, and must not
// apply it to equities -- j.qty for equities is passed through untouched.
gates.G4 = () => {
  const code = src.replace(/\/\/[^\n]*/g, '');
  assert.ok(/j\.screenerType === 'crypto' \? fmtCryptoQty\(j\.qty\) : j\.qty/.test(code),
    'the qty cell must route crypto through fmtCryptoQty and leave equities as j.qty');
  console.log('G4 PASS the qty cell is wired to the formatter, gated on screenerType');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
  console.log('G1 PASS a large fractional qty is shortened');
  console.log('G2/G3 PASS small holdings stay visible, round numbers stay clean');
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }

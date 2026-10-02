// The Kalshi page tells someone how much a scalp costs and whether a trade
// fits their risk limits. A wrong number here is not cosmetic: it is the
// number someone sizes real money from. These gates state the consequences.
// The same math lives in kalshi-scalper (fees.py, risk.py); keep them equal.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const fnSrc = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');

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

const KALSHI_TAKER_RATE = 0.07;
const KALSHI_LIMITS = { perTradePct: 0.01, minEdge: 0.03, maxSpread: 0.04 };
const fee = lift('kalshiTakerFee', { KALSHI_TAKER_RATE });
const roundTrip = lift('kalshiRoundTrip', { kalshiTakerFee: fee });
const check = lift('kalshiCheckTrade', { kalshiTakerFee: fee, KALSHI_LIMITS });
const secsLeft = lift('kalshiSecsLeft');

const gates = {};

// A flat market must cost money. If crossing the spread and paying fees ever
// came out free, every scalp would look viable and none would be.
gates.G1 = () => {
  assert.ok(roundTrip(0.51, 0.49, 10) > 0.02 * 10, 'round trip must exceed the raw spread');
  assert.ok(roundTrip(0.50, 0.50, 1) >= 2 * fee(0.50, 1) - 1e-9, 'an early exit pays the fee on both legs');
};

// Fees are dearest at 50c and cheap at the extremes, which is where a scalp
// has any chance. Matches kalshi-scalper fees.py: 10 contracts at 50c is 18c.
gates.G2 = () => {
  assert.strictEqual(fee(0.50, 10), 0.18);
  assert.ok(fee(0.95, 100) < fee(0.50, 100));
  assert.strictEqual(fee(0, 10), 0);
  assert.strictEqual(fee(1, 10), 0);
};

// One trade must never risk more than 1% of bankroll.
gates.G3 = () => {
  const r = check({ price: 0.5, contracts: 40, prob: 0.7, spread: 0.01, bankroll: 1000 });
  assert.ok(!r.ok && r.reasons.some((x) => /1% cap/.test(x)));
  assert.ok(check({ price: 0.5, contracts: 10, prob: 0.7, spread: 0.01, bankroll: 1000 }).ok);
};

// Buying at your own probability is a loss once the fee is paid: no edge, no trade.
gates.G4 = () => {
  const r = check({ price: 0.5, contracts: 10, prob: 0.51, spread: 0.01, bankroll: 1000 });
  assert.ok(!r.ok && r.reasons.some((x) => /Edge after fees/.test(x)));
};

// Wide books are refused.
gates.G5 = () => {
  const r = check({ price: 0.5, contracts: 10, prob: 0.7, spread: 0.08, bankroll: 1000 });
  assert.ok(!r.ok && r.reasons.some((x) => /Spread/.test(x)));
};

// Garbage fails closed, never "Within limits".
gates.G6 = () => {
  [{ price: '', contracts: 10, prob: 0.6, spread: 0.01, bankroll: 1000 },
   { price: 1.5, contracts: 10, prob: 0.6, spread: 0.01, bankroll: 1000 },
   { price: 0.5, contracts: 0, prob: 0.6, spread: 0.01, bankroll: 1000 },
   { price: 0.5, contracts: 10, prob: 0.6, spread: 0.01, bankroll: 0 }]
    .forEach((o) => assert.ok(!check(o).ok, JSON.stringify(o)));
};

// A market past its close shows 0, never a negative countdown.
gates.G7 = () => {
  assert.strictEqual(secsLeft('2026-10-02T14:45:00Z', Date.parse('2026-10-02T14:46:00Z')), 0);
  assert.strictEqual(secsLeft('2026-10-02T14:45:00Z', Date.parse('2026-10-02T14:44:00Z')), 60);
  assert.strictEqual(secsLeft('garbage', 0), null);
};

// The relay must stay read-only and narrow: fixed series, no caller-chosen
// path, no credentials, and it must require sign-in. Widening it into
// something that can trade needs its own review.
gates.G8 = () => {
  const m = /exports\.kalshiBooks = onCall\(async \(request\) => \{([\s\S]*?)\n\}\);/.exec(fnSrc);
  assert.ok(m, 'kalshiBooks not found');
  assert.ok(/assertSignedIn\(request\.auth\)/.test(m[1]), 'must require sign-in');
  assert.ok(!/request\.data/.test(m[1]), 'must not take a caller-supplied path or query');
  assert.ok(!/method\s*:|POST|DELETE|\/orders|KALSHI_(API_)?KEY|Authorization/i.test(m[1]), 'must stay read-only and keyless');
};

// The page must be reachable: nav button, page element, and showPage wiring.
gates.G9 = () => {
  assert.ok(/data-page="kalshi"/.test(src));
  assert.ok(/id="page-kalshi"/.test(src));
  assert.ok(/getElementById\('page-kalshi'\)\.hidden = \(name !== 'kalshi'\)/.test(src));
  assert.ok(/kalshiBooks: function/.test(src));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); }
  catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

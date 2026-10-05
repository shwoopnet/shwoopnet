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
const KALSHI_LIMITS = { perTradePct: 0.01, minEdge: 0.03, maxSpread: 0.04,
  softStopPct: 0.03, hardStopPct: 0.05, breakMs: 2 * 60 * 60 * 1000 };
const fee = lift('kalshiTakerFee', { KALSHI_TAKER_RATE });
const roundTrip = lift('kalshiRoundTrip', { kalshiTakerFee: fee });
const check = lift('kalshiCheckTrade', { kalshiTakerFee: fee, KALSHI_LIMITS });
const secsLeft = lift('kalshiSecsLeft');
const dayStart = lift('kalshiDayStart');
const entryCost = lift('kalshiEntryCost');
const settle = lift('kalshiSettle', { kalshiEntryCost: entryCost, kalshiTakerFee: fee });
const tier = lift('kalshiTierState', { KALSHI_LIMITS, kalshiDayStart: dayStart });
const calib = lift('kalshiCalibration', { kalshiEntryCost: entryCost });

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
  assert.ok(!r.ok && r.reasons.some((x) => /over the cap of \$10\.00/.test(x)));
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
  assert.ok(/assertKalshiAdmin\(request\.auth\)/.test(m[1]), 'must require the admin check');
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


// ---- admin only ----

// The relay itself must refuse anyone but the owner: both the email and the
// admin flag on the user document, not just one of them.
gates.G10 = () => {
  const m = /async function assertKalshiAdmin\(auth\) \{([\s\S]*?)\n\}/.exec(fnSrc);
  assert.ok(m, 'assertKalshiAdmin not found');
  assert.ok(/KALSHI_OWNER_EMAIL/.test(m[1]) && /isAdmin !== true/.test(m[1]), 'must check both email and isAdmin');
  assert.ok(/KALSHI_OWNER_EMAIL = "heiszcam@gmail\.com"/.test(fnSrc));
};

// The database must refuse a non-admin write to the journal, whatever the UI does.
gates.G11 = () => {
  const rules = fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8');
  assert.ok(/hasAny\(\['kalshiJournal'\]\)/.test(rules) && /isAdmin\(\) \|\| !request\.resource\.data\.diff/.test(rules),
    'firestore.rules must block non-admin writes to kalshiJournal');
};

// The page is hidden for non-admins and showPage refuses to open it for them.
gates.G12 = () => {
  assert.ok(/data-page="kalshi"[^>]*\bhidden\b/.test(src), 'nav button must start hidden');
  assert.ok(/if\(name === 'kalshi' && !currentUserIsAdmin\)\{ name = 'brief'; \}/.test(src), 'showPage must refuse non-admins');
  assert.ok(/kalNav\.hidden = !currentUserIsAdmin/.test(src), 'applyAdminUI must toggle the nav button');
};

// ---- the tiered limits ----

const BANK = 300;
const DAY = Date.parse('2026-10-05T15:00:00');
const at = (h, m) => { const d = new Date(DAY); d.setHours(h, m, 0, 0); return d.getTime(); };
const closed = (pnl, t) => ({ pnl, settledAt: t, status: pnl >= 0 ? 'won' : 'lost' });

// $3 a trade on a $300 bankroll.
gates.G13 = () => {
  const t = tier([], BANK, at(12, 0));
  assert.strictEqual(t.mode, 'ok');
  assert.strictEqual(t.cap, 3);
  assert.strictEqual(t.softLimit, 9);
  assert.strictEqual(t.hardLimit, 15);
};

// Down 3% starts a 2 hour break, then half size. The break is measured from the
// trade that crossed the line, and a later win does not shorten it.
gates.G14 = () => {
  const entries = [closed(-5, at(9, 0)), closed(-5, at(10, 0))];
  assert.strictEqual(tier(entries, BANK, at(10, 1)).mode, 'break');
  assert.strictEqual(tier(entries, BANK, at(10, 1)).cap, 0);
  assert.strictEqual(tier(entries, BANK, at(11, 59)).mode, 'break');
  const after = tier(entries, BANK, at(12, 1));
  assert.strictEqual(after.mode, 'half');
  assert.strictEqual(after.cap, 1.5);
  const wins = entries.concat([closed(8, at(10, 30))]);
  assert.strictEqual(tier(wins, BANK, at(11, 0)).mode, 'break', 'a later win must not end the break early');
};

// Down 5% is done for the day, and stays done even after a recovery.
gates.G15 = () => {
  const entries = [closed(-16, at(9, 0)), closed(20, at(9, 30))];
  assert.strictEqual(tier(entries, BANK, at(14, 0)).mode, 'done');
  assert.strictEqual(tier(entries, BANK, at(14, 0)).cap, 0);
};

// Yesterday's losses must not carry into today.
gates.G16 = () => {
  const y = new Date(DAY); y.setDate(y.getDate() - 1);
  const entries = [closed(-20, y.getTime())];
  assert.strictEqual(tier(entries, BANK, at(12, 0)).mode, 'ok');
};

// No bankroll means no trading, never an unlimited cap.
gates.G17 = () => {
  assert.strictEqual(tier([], 0, at(12, 0)).mode, 'done');
  assert.strictEqual(tier([], '', at(12, 0)).mode, 'done');
};

// The pre-trade check must obey the tier: blocked on a break, halved after it.
gates.G18 = () => {
  const o = { price: 0.4, contracts: 7, prob: 0.6, spread: 0.01, bankroll: BANK };
  assert.ok(check(Object.assign({}, o, { tier: tier([], BANK, at(12, 0)) })).ok, '$2.80 fits a $3 cap');
  const brk = tier([closed(-5, at(9, 0)), closed(-5, at(10, 0))], BANK, at(10, 30));
  assert.ok(!check(Object.assign({}, o, { tier: brk })).ok);
  const half = tier([closed(-5, at(9, 0)), closed(-5, at(10, 0))], BANK, at(13, 0));
  const r = check(Object.assign({}, o, { tier: half }));
  assert.ok(!r.ok && r.reasons.some((x) => /cap of \$1\.50/.test(x)), 'half size cap is $1.50');
  const done = tier([closed(-16, at(9, 0))], BANK, at(10, 0));
  assert.ok(!check(Object.assign({}, o, { tier: done })).ok);
};

// ---- settlement and results ----

const open = () => ({ id: 'a', price: 0.39, contracts: 50, fee: 0.84, myProb: 0.5, status: 'open', pnl: null });

// Your own trade: 50 at 39c with an $0.84 fee costs $20.34. Won pays $50, lost loses the cost.
gates.G19 = () => {
  assert.ok(Math.abs(entryCost(open()) - 20.34) < 1e-9);
  assert.strictEqual(settle(open(), 'won', null, 1).pnl, 29.66);
  assert.strictEqual(settle(open(), 'lost', null, 1).pnl, -20.34);
};

// An early sale pays the exit fee: 50 at 37c is $18.50 less the fee less the cost.
gates.G20 = () => {
  const s = settle(open(), 'sold', 0.37, 1);
  assert.strictEqual(s.pnl, Math.round((50 * 0.37 - fee(0.37, 50) - 20.34) * 100) / 100);
  // Kalshi's own cash-out at 39c showed $18.66 = $19.50 less the $0.84 exit fee: the sale nets the fee.
  assert.ok(Math.abs((50 * 0.39 - fee(0.39, 50)) - 18.66) < 1e-9);
  assert.ok(s.pnl < -1.67, 'selling lower than 39c loses more than the 1.67 shown at 39c');
  assert.strictEqual(settle(open(), 'sold', 1.2, 1), null);
  assert.strictEqual(settle(open(), 'sold', 0, 1), null);
  assert.strictEqual(settle(open(), 'nonsense', null, 1), null);
};

// A coin flip bought at 50c cannot look like skill: win rate must be compared to
// the break-even price, and a small sample must say so instead of a verdict.
gates.G21 = () => {
  const mk = (won, i) => Object.assign(open(), { id: 'e' + i, price: 0.5, fee: 0.9, contracts: 50, myProb: 0.6, status: won ? 'won' : 'lost', pnl: won ? 24.1 : -25.9, settledAt: i });
  const few = Array.from({ length: 10 }, (_, i) => mk(i % 2 === 0, i));
  assert.ok(/Too early/.test(calib(few).verdict));
  const many = Array.from({ length: 200 }, (_, i) => mk(i % 2 === 0, i));
  const c = calib(many);
  assert.strictEqual(c.held, 200);
  assert.ok(Math.abs(c.winRate - 0.5) < 1e-9 && c.avgBreakEven > 0.5, 'break-even includes the fee');
  assert.ok(/losing to the price|Not distinguishable/.test(c.verdict), c.verdict);
  const lucky = Array.from({ length: 200 }, (_, i) => mk(i % 3 !== 0, i));
  assert.ok(/beating the price/.test(calib(lucky).verdict));
};

// Kalshi's refusal is a whole HTML error page. The status line must never show
// markup, and a permanent refusal must stop the 5 second polling.
gates.G22 = () => {
  const m = /function refreshKalshi\(\)\{([\s\S]*?)\n  \}\n  function startKalshiPoll/.exec(src);
  assert.ok(m, 'refreshKalshi not found');
  assert.ok(/refused \? 'Kalshi refused the request \(HTTP 403\)'/.test(m[1]), 'a 403 must show a short line');
  assert.ok(/replace\(\/<\[\^>\]\*>\/g/.test(m[1]), 'any other error must have markup stripped');
  assert.ok(/if\(refused\)\{ stopKalshiPoll\(\); \}/.test(m[1]), 'a 403 must stop the polling');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); }
  catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

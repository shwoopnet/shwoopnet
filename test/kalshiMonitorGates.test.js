// The Kalshi page tells someone how much a scalp costs and whether a trade
// fits their risk limits. A wrong number here is not cosmetic: it is the
// number someone sizes real money from. These gates state the consequences.
// The same math lives in kalshi-scalper (fees.py); keep them equal.

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
const fee = lift('kalshiTakerFee', { KALSHI_TAKER_RATE });
const roundTrip = lift('kalshiRoundTrip', { kalshiTakerFee: fee });
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

// ---- settlement and results ----

const open = () => ({ id: 'a', price: 0.39, contracts: 50, fee: 0.84, myProb: 0.5, status: 'open', pnl: null });

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

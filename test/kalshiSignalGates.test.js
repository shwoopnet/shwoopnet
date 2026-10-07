// The strategy's entry signal and the page that shows the live account. There is no simulated trading in this repo:
// what is tested here is the signal the live test and armed scan use to pick an order, the halt switch's rules, and
// the Bot tab. Each gate states the consequence of getting it wrong.

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const lib = require('../functions/kalshiSignalLib');

const root = path.join(__dirname, '..');
const fnSrc = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
const gates = {};

const NOON = Date.parse('2026-10-05T17:00:00Z');          // 12:00 CDT
const CLOSE = NOON + 15 * 60000;

gates.G1 = () => {
  assert.strictEqual(lib.takerFee(0.40, 7), 0.12);        // 11.76c rounds UP to 12c
  assert.strictEqual(lib.takerFee(0.5, 10), 0.18);
  assert.strictEqual(lib.takerFee(0, 5), 0);
  assert.ok(!lib.validQuote(0.001, 1.0) && !lib.validQuote(null, 0.5) && !lib.validQuote(0.3, 0.55));
  assert.ok(lib.validQuote(0.47, 0.49) && lib.validQuote(0.001, 0.01));
};

gates.G4 = () => {
  assert.strictEqual(lib.sizeFor(0.40, 3.0, null), 7);
  assert.strictEqual(lib.sizeFor(0.42, 3.0, null), 6, 'the fee counts: 7 x 42c = $2.94 fits, plus a 12c fee does not');
  assert.strictEqual(lib.sizeFor(0.40, 3.0, 3), 3, 'never more than the touch shows');
  assert.strictEqual(lib.sizeFor(0.40, 0.30, null), 0);
  assert.strictEqual(lib.sizeFor(1.2, 3.0, null) + lib.sizeFor(0.4, 0, null), 0);
  assert.strictEqual(lib.sizeFor(0.40, 1.0, null), 2, 'at $100 a trade is one or two contracts');
};

gates.G5 = () => {
  const q = (bid, ask, extra = {}) => [{ series: 'KXBTC15M', m: { ticker: 'T', status: 'active', close_time: new Date(CLOSE).toISOString(),
    yes_bid_dollars: String(bid), yes_ask_dollars: String(ask), yes_ask_size_fp: '100', yes_bid_size_fp: '100', ...extra } }];
  const yes = lib.planEntries(q(0.39, 0.40), NOON, 3)[0];
  assert.deepStrictEqual([yes.side, yes.band, yes.contracts, yes.price], ['yes', '40c', 7, 0.40]);
  const no = lib.planEntries(q(0.59, 0.61), NOON, 3)[0];
  assert.ok(no.side === 'no' && Math.abs(no.price - 0.41) < 1e-9, 'NO is bought at 1 minus the YES bid');
  assert.strictEqual(lib.planEntries(q(0.55, 0.57), NOON, 3).length, 0, 'outside the bands');
  assert.strictEqual(lib.planEntries(q(0.39, 0.40), CLOSE - 240000, 3).length, 0, 'under 5 minutes left');
  assert.strictEqual(lib.planEntries(q(0.001, 1.0), NOON, 3).length, 0, 'an empty book is not a quote');
  assert.strictEqual(lib.planEntries(q(0.39, 0.40, { status: 'finalized' }), NOON, 3).length, 0);
  assert.strictEqual(lib.planEntries(q(0.39, 0.40, { yes_ask_size_fp: '2' }), NOON, 3)[0].contracts, 2);
};

// ================= no real orders outside the live module =================

// The signal library holds no order code, and nothing after the book recorder (the last export) can see a key.
gates.G16 = () => {
  for (const f of ['kalshiSignalLib.js', 'kalshiBookLib.js', 'kalshiWatchdogLib.js']) {
    const code = fs.readFileSync(path.join(root, 'functions', f), 'utf8').replace(/\/\/[^\n]*/g, '');
    assert.ok(!/portfolio\/events\/orders|KALSHI-ACCESS|private_?key|api_?key|create_?order|place_?order/i.test(code), f + ' must contain no order code');
  }
  const tail = fnSrc.slice(fnSrc.indexOf('exports.kalshiBookRecorder ='));
  assert.ok(tail.length > 20, 'kalshiBookRecorder not found');
  assert.ok(!/portfolio\/events\/orders|KALSHI-ACCESS|private_?key|create_?order|place_?order|KALSHI_LIVE/i.test(tail.replace(/\/\/[^\n]*/g, '')), 'the recorder must contain no order code and never see the live key or switch');
  assert.ok(!/kalshiBotRun|kalshiBotLib|kalshiAlertLib|firestoreBotStore|exports\.kalshiBot =/.test(fnSrc), 'no simulated bot code remains');
};

// ================= database rules and the page =================

const rules = fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const block = (re, text) => { const m = re.exec(text); assert.ok(m, 'not found: ' + re); return m[1]; };

// The halt switch is the only thing a browser may write here, only for the admin, only a boolean. The simulated
// bot's collections are gone from the rules, so nothing can write a position or an event.
gates.G19 = () => {
  const ctl = block(/match \/kalshiBotMeta\/control \{([\s\S]*?)\n    \}/, rules);
  assert.ok(/allow read: if isAdmin\(\);/.test(ctl) && /allow write: if isAdmin\(\)/.test(ctl));
  assert.ok(/hasOnly\(\['halt', 'at'\]\)/.test(ctl) && /halt is bool/.test(ctl), 'the halt switch accepts only a boolean');
  assert.ok(!/kalshiBotPositions|kalshiBotEvents|kalshiBotMeta\/status/.test(rules), 'no simulated-bot collection remains in the rules');
};

// The page can watch the halt switch, flip that one switch, and cannot touch a trade.
// The Bot tab is the default, resuming entries asks first, and leaving the page stops listening.
gates.G21 = () => {
  const bridge = block(/watchKalshiBot: function\(h\)\{([\s\S]*?)\n    \},\n    \/\/ What the live bot did/, html);
  assert.ok(/kalshiBotMeta/.test(bridge) && /'control'/.test(bridge), 'the halt switch is watched');
  assert.ok(!/'status'/.test(bridge) && !/Paper bot/.test(html), 'the page no longer shows or reads anything of the paper bot');
  assert.ok(!/kalshiBotPositions|kalshiBotEvents/.test(html), 'the paper bot\'s trades and events are no longer read or shown by the page');
  assert.ok(!/setDoc|updateDoc|addDoc|deleteDoc/.test(bridge), 'watching must not write');
  const ev = block(/watchKalshiLiveEvents: function\(cb\)\{([\s\S]*?)\n    \},/, html);
  assert.ok(/kalshiLiveEvents/.test(ev) && !/setDoc|updateDoc|addDoc|deleteDoc/.test(ev), 'the live event log is read only');
  const halt = block(/setKalshiHalt: function\(halt\)\{([\s\S]*?)\n    \},/, html);
  assert.ok(/setDoc\(doc\(db, 'kalshiBotMeta', 'control'\), \{ halt: Boolean\(halt\), at: serverTimestamp\(\) \}\)/.test(halt),
    'the halt switch writes exactly { halt, at } to the control document');
  assert.ok(!/data-kal-tab|kalTabJournal|kalTabLive/.test(html), 'the Kalshi page is one page now: no tabs, no journal');
  assert.ok(/function kalshiOnShow\(\)\{ startKalshiBot\(\); startKalshiPoll\(\); \}/.test(html), 'opening the page starts the bot view and the books');
  assert.ok(/if\(halted\)\{ el\.innerHTML \+= '<div class="kal-warn kal-big">Halted from this page/.test(html), 'the halt must show on the card at once');
  assert.ok(/var haltUnset = !kalshiBotState\.control \|\| kalshiBotState\.control\.halt === undefined;/.test(html) && /if\(haltUnset\)\{ el\.innerHTML \+= '<div class="kal-warn">The halt setting has never been saved, and the live scan treats that as halted/.test(html), 'an unsaved halt setting must not read as "not halted"');
  assert.ok(/if\(halted && !window\.confirm\(/.test(html), 'resuming entries must ask first');
  assert.ok(/function kalshiOnHide\(\)\{ stopKalshiPoll\(\); stopKalshiBot\(\); \}/.test(html), 'leaving the page must stop listening');
  const start = block(/function startKalshiBot\(\)\{([\s\S]*?)\n  \}\n  function stopKalshiBot/, html);
  assert.ok(/!currentUserIsAdmin\)\{ return; \}/.test(start + ')'), 'only an admin may subscribe');
  const stop = block(/function stopKalshiBot\(\)\{([\s\S]*?)\n  \}\n/, html);
  assert.ok(/clearInterval\(kalshiAcctTimer\)/.test(stop) && /kalshiLiveEventsUnsub\(\)/.test(stop), 'leaving the tab stops the account timer and every listener');
  assert.ok(/setInterval\(function\(\)\{ if\(!document\.hidden\)\{ kalshiAcctRefresh\(\); \} \}, 60000\)/.test(start), 'the account is re-read once a minute, only while the tab is visible');
};

// The tab once showed only the newest 15 trades and 12 events with no way to see more, which hid most of the day. The
// live log keeps a way to show more, the page says how many fills it is hiding, and nothing of the paper bot is listed.
gates.G22 = () => {
  assert.ok(!/limit\((12|40)\)/.test(html), 'no query may cap a history at a dozen rows');
  assert.ok(/data-more="events"/.test(html) && /kalshiLiveShow\.events \+= 50/.test(html), 'the log needs a way to show more');
  assert.ok(/Showing ' \+ evShown\.length \+ ' of ' \+ evAll\.length/.test(html), 'the page must say how many events it is not showing');
  assert.ok(/earlier fill' \+ \(a\.fills\.hiddenBeforeBaseline === 1/.test(html), 'the page must say how many fills sit before the starting line');
  assert.ok(!/id="kalBotClosed"[\s\S]{0,40}paper/i.test(html) && !/kalshiBotTotals/.test(html), 'no paper-bot totals or lists remain on the page');
};

// The totals count what the bot did since the owner's starting line, not the owner's own trades on the same account.
gates.G23 = () => {
  const totals = new Function(block(/(function kalshiLiveTotals\(acct, orders\)\{[\s\S]*?\n  \})\n/, html) + '; return kalshiLiveTotals;')();
  const isBot = new Function(block(/(function kalshiFillIsBot\(fill, orders\)\{[\s\S]*?\n  \})\n/, html) + '; return kalshiFillIsBot;')();
  const since = 1000;
  const acct = { baseline: { since, startingDollars: 97.48 }, balance: { ok: true, totalDollars: 98.2 }, changeSinceStart: 0.72, fills: { ok: true, fills: [{}, {}, {}] } };
  const orders = [
    { ts: 500, status: 'filled', orderId: 'before' },       // before the line: not counted
    { ts: 1000, status: 'filled', orderId: 'a' }, { ts: 1500, status: 'no fill', orderId: 'b' },
    { ts: 2000, status: 'unknown', orderId: 'c' }, { ts: 2500, status: 'error' }, null,
  ];
  const t = totals(acct, orders);
  assert.deepStrictEqual([t.sent, t.filled, t.noFill, t.other], [4, 1, 1, 2], 'only orders at or after the line, with unresolved ones set apart');
  assert.deepStrictEqual([t.start, t.now, t.change, t.fills], [97.48, 98.2, 0.72, 3]);
  assert.strictEqual(totals({ balance: { ok: true } }, orders), null, 'without a starting line there are no totals to show');
  assert.strictEqual(totals(null, orders), null);
  const bad = totals({ baseline: { since, startingDollars: 5 }, balance: { ok: false }, fills: { ok: false } }, []);
  assert.ok(bad.now === null && bad.change === null && bad.fills === null && bad.sent === 0, 'a failed read shows n/a, not a number');
  // A fill is the bot's only when its order id matches one the bot saved; everything else on the account is manual.
  assert.strictEqual(isBot({ orderId: 'a' }, orders), true);
  assert.strictEqual(isBot({ orderId: 'zzz' }, orders), false);
  assert.strictEqual(isBot({ orderId: null }, orders), false);
  assert.strictEqual(isBot({ orderId: 'a' }, [{ ts: 1 }]), false, 'an order saved without an id matches nothing');
  assert.strictEqual(isBot(null, orders), false);
  // Wired into the page.
  assert.ok(/id="kalBotTotals"/.test(html) && /kalshiLiveTotals\(a, kalshiLiveOrders\)/.test(html));
  assert.ok(/kalshiFillIsBot\(x, kalshiLiveOrders\)/.test(html) && /\(bot \? 'bot' : 'manual'\)/.test(html), 'each fill is labelled bot or manual');
};

// A NO entry at exactly 42c or 52c must be planned. NO price is 1 - yes bid, and in
// floating point 1 - 0.58 is 0.42000000000000004, which fails "<= 0.42": the bot silently
// skipped a market it is meant to enter while taking the same price on the YES side.
gates.KalshiNoEdge = () => {
  const plan = (bid, ask) => lib.planEntries(
    [{ series: 'KXBTC15M', m: { ticker: 'T', status: 'active', close_time: new Date(CLOSE).toISOString(),
      yes_bid_dollars: bid.toFixed(4), yes_ask_dollars: ask.toFixed(4), yes_ask_size_fp: '100', yes_bid_size_fp: '100' } }],
    NOON, 3);
  // yes ask is out of band (0.60 / 0.54), so only the NO side can qualify.
  const no42 = plan(0.58, 0.60);
  assert.deepStrictEqual(no42.map((e) => [e.side, e.band, e.price]), [['no', '40c', 0.42]], 'NO at 42c must be planned');
  const no52 = plan(0.48, 0.54);
  assert.deepStrictEqual(no52.map((e) => [e.side, e.band, e.price]), [['no', '50c', 0.52]], 'NO at 52c must be planned');
  // Every band edge on the NO side, in cents, is inside its band.
  for (const c of [38, 42, 48, 52]) {
    assert.strictEqual(plan((100 - c) / 100, (100 - c) / 100 + 0.06).filter((e) => e.side === 'no').length, 1, 'NO at ' + c + 'c');
  }
  // One cent outside either band is still skipped: rounding must not widen the band.
  for (const c of [37, 43, 47, 53]) {
    assert.strictEqual(plan((100 - c) / 100, (100 - c) / 100 + 0.06).filter((e) => e.side === 'no').length, 0, 'NO at ' + c + 'c');
  }
};

// The Bot tab layout is customizable, but the live account card (halt) and the session card (stop) can never be hidden, and
// the saved layout survives blocked storage.
gates.G24 = () => {
  const optional = /var OPTIONAL = \[([^\]]*\][^\]]*\][^\]]*\][^\]]*\][^\]]*\])\]/.exec(html);
  assert.ok(optional, 'optional card list not found');
  assert.ok(!/'account'|'session'/.test(optional[1]), 'the account and session cards are not in the hideable list');
  assert.ok(/data-card="account"/.test(html) && /data-card="session"/.test(html));
  const iife = html.slice(html.indexOf("var KEY = 'kalBotLayout'"), html.indexOf("document.getElementById('kalLayoutReset')"));
  assert.ok(/try \{\s*var saved = JSON\.parse\(localStorage\.getItem\(KEY\)/.test(iife) && /try \{ localStorage\.setItem\(KEY/.test(iife), 'storage reads and writes are guarded');
  assert.ok(/\['auto', '1', '2', '3', '4'\]\.indexOf\(String\(saved\.cols\)\)/.test(iife), 'a corrupt saved value cannot set a bad column count');
};

// On a phone the page must not scroll sideways: the live books grid may never ask for more than the card is wide, and the Layout menu's
// controls are big enough to tap.
gates.G25 = () => {
  assert.ok(/\.kal-bot-grid \.kal-books\{ grid-template-columns:repeat\(auto-fit,minmax\(min\(380px,100%\),1fr\)\); \}/.test(html), 'books grid is capped at the card width');
  assert.ok(/\.kal-layout-body label\{[^}]*min-height:34px/.test(html) && /\.kal-layout-body input\[type=checkbox\]\{ width:18px; height:18px; \}/.test(html), 'layout controls are tappable');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();

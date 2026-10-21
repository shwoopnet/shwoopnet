// Features were removed on purpose, and their tests were left behind
// asserting they still existed:
//   - desktop notifications (#195)
//   - the Labs page and its forward-test record (#208)
//   - the blank slate of Oct 12, 2026: everything but the Brief, Kalshi and
//     Settings (the trading pages, the Alpaca, Finnhub and Twelve Data
//     integrations, and creating an account from the page)
// Tests that fail on main for weeks teach everyone to ignore a red suite.
// They are replaced by the claim that is actually true now: the features
// stay gone. If one is wanted back it should return deliberately, with new
// tests, not by reviving one of these identifiers by accident.

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
// Comments may still explain the history; only code counts.
const code = src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '').replace(/<!--[\s\S]*?-->/g, '');

const gates = {};

// Nothing may raise an OS-level notification from the page. The one exception the owner asked for (Oct 20, 2026): the Kalshi page's "Phone alerts" switch may ask for notification permission, once,
// from the owner's tap, and only inside kalshiPushToggle. The page still never constructs a Notification itself; the service worker shows pushes the server sent.
gates.G1 = () => {
  assert.ok(!/new Notification\(/.test(code), 'no code may construct a browser Notification');
  assert.strictEqual((code.match(/Notification\.requestPermission/g) || []).length, 1, 'permission is asked for in exactly one place');
  const fn = /function kalshiPushToggle\(\)\{[\s\S]*?\n  \}\n/.exec(code);
  assert.ok(fn && /Notification\.requestPermission/.test(fn[0]), 'and that place is the phone alerts switch, which runs from a tap');
  assert.ok(!/requestPermission/.test(code.replace(fn[0], '')), 'nothing else asks (no prompt on load)');
};

// The Labs page and its forward-test record stay gone.
gates.G2 = () => {
  assert.ok(!/id="page-labs"/.test(code), 'the Labs page must stay removed');
  ['FORWARD_TEST_STRATEGY_LABELS', 'forwardTestSnapshots'].forEach((name) =>
    assert.ok(!code.includes(name), 'removed Labs identifier is back: ' + name));
};

// The blank slate (Oct 12, 2026, at the owner's request: "an anti-degen proof website ... to prevent myself from full porting"). The site is three pages, and four since the read-only Data page (Oct 21, 2026).
gates.G3 = () => {
  const pages = [...code.matchAll(/<main class="page" id="(page-[\w-]+)"/g)].map((m) => m[1]);
  assert.deepStrictEqual(pages, ['page-brief', 'page-kalshi', 'page-data', 'page-settings'], 'the site is the Brief, Kalshi, Data (read only, admin only, added Oct 21, 2026 at the owner\'s request) and Settings and nothing else');
  const nav = [...code.matchAll(/<button class="side-nav-item nav-item"[^>]*\bdata-page="(\w+)"/g)].map((m) => m[1]);
  assert.deepStrictEqual(nav, ['brief', 'kalshi', 'data', 'settings'], 'and the sidebar says the same');
  assert.ok(!/data-action="(notepad|history)"/.test(code), 'no notepad or history buttons');
  ['page-trades', 'page-journal', 'page-changelog', 'alpacaDock', 'tradeModal', 'tradeModalBackdrop', 'notepadPanel', 'historySidebar', 'tickerTape', 'exitTradeModal',
   'toastContainer', 'globalPausedBanner', 'headerLiveStatus', 'whatToWatchList', 'ctaToTrades'].forEach((id) =>
    assert.ok(!code.includes('id="' + id + '"') && !code.includes("'" + id + "'"), 'removed element is back: ' + id));
};

// No vendor integration of the removed kind, in the page or anywhere it could be reached from.
gates.G4 = () => {
  assert.ok(!/alpaca|finnhub|twelve ?data|onrender\.com/i.test(code), 'the page names no broker or market-data vendor and no server of its own');
  assert.ok(!/['"][0-9a-f]{64}['"]/.test(code), 'no 64 character hex literal (the Twelve Data proxy secret used to sit in this file in plaintext)');
  assert.ok(!/Authorization\s*:\s*['"]Bearer/.test(code), 'the page sends no bearer secret of its own');
  ['finnhubQuote', 'finnhubCompanyNews', 'twelveDataProxyHeaders', 'fetchAllQuotes', 'fetchHistory'].forEach((name) => assert.ok(!code.includes(name), 'removed identifier is back: ' + name));
};

// Nobody creates an account from the page. The Auth account is made by hand and so is the users document (firestore.rules refuses a browser create).
gates.G5 = () => {
  ['createUserWithEmailAndPassword', 'deleteUser', 'redeemInviteAndCreateAccount', 'createInviteCode', 'authInviteCode', 'authConfirmPassword', 'authSwitchBtn', 'adminInviteSection', 'generateInviteBtn'].forEach((name) =>
    assert.ok(!code.includes(name), 'sign-up or invite code is back: ' + name));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); }
  catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

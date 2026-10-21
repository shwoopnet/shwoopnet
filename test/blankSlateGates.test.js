'use strict';
// THE BLANK SLATE (Oct 12, 2026). The owner asked for the site to be the Market Brief, the Kalshi page and Settings, and nothing else:
// "basically i want this to be an anti-degen proof website ... to prevent myself from full porting". These gates state what that means as
// consequences. Each is a place a risk setting, a vendor or a way in could quietly come back.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const code = html.replace(/\/\*[\s\S]*?\*\//g, '').replace(/<!--[\s\S]*?-->/g, '');
const gates = {};

function fnSource(name) {
  const start = html.indexOf('function ' + name + '(');
  assert.ok(start >= 0, name + ' exists');
  let i = html.indexOf('{', html.indexOf(')', start)), depth = 0;
  for (; i < html.length; i++) {
    if (html[i] === '{') depth++;
    else if (html[i] === '}' && --depth === 0) return html.slice(start, i + 1);
  }
  throw new Error('unbalanced ' + name);
}
const varSource = (name) => { const m = new RegExp('var ' + name + ' = [\\s\\S]*?;\\n').exec(html); assert.ok(m, name + ' exists'); return m[0]; };

// The page talks to a short, named list of hosts. A new host is a new vendor the page depends on, and for a page that can start a trading bot that is a decision, not a side effect.
gates.B1 = () => {
  const text = code.replace(/\/\/[^\n]*/g, (c) => (/^\/\/[a-z0-9.-]+\//i.test(c) ? c : ''));   // drop line comments but keep the // inside a URL
  const hosts = new Set([...text.matchAll(/https?:\/\/([a-z0-9.-]+)/gi)].map((m) => m[1].toLowerCase()));
  const allowed = new Set([
    'www.gstatic.com',            // the Firebase SDK
    'fonts.googleapis.com', 'fonts.gstatic.com',
    'api.exchange.coinbase.com',  // Bitcoin spot for the Kalshi charts
    'api.gold-api.com',           // gold spot for the Kalshi charts
    'www.w3.org',                 // the SVG namespace, not a request
    'shwoopnet.github.io',        // this site's own address in the og:image tag (link previews); the page never fetches it
  ]);
  const extra = [...hosts].filter((h) => !allowed.has(h));
  assert.deepStrictEqual(extra, [], 'the page may only reference the hosts listed here; found ' + extra.join(', '));
};

// The page can do exactly these things with Firebase. Anything added here (a way to save a journal, to connect a broker, to create an account) has to be added to this list on purpose.
gates.B2 = () => {
  const mod = html.slice(html.indexOf('<script type="module">'), html.indexOf('</script>', html.indexOf('<script type="module">')));
  const methods = [...mod.matchAll(/^    (\w+): function/gm)].map((m) => m[1]).sort();
  assert.deepStrictEqual(methods, [
    'kalshiBookSnaps', 'kalshiBookStatus', 'kalshiBooks', 'kalshiFlattenAll', 'kalshiL1Session', 'kalshiLiveAccount', 'kalshiLiveBaseline',
    'kalshiPushKey', 'kalshiPushSubscribe', 'kalshiPushUnsubscribe',      // the phone alerts (Oct 20, 2026): the owner's own functions, admin only
    'onAuthChange', 'resetPassword', 'saveUserSettings', 'setKalshiHalt', 'shapeUserSettings', 'signIn', 'signOutUser',
    'watchKalshiBot', 'watchKalshiLive', 'watchKalshiLiveControl', 'watchKalshiLiveEvents', 'watchMarketTape', 'watchSharedMarketSnapshot', 'watchUserDoc',
  ], 'the Firebase surface the page can reach');
  // No exit, pool or size setter: the exit is fixed at 50c and the pool rebuilds after every win, in the server code.
  assert.ok(!/setExit|setPool|exitMode|poolRule/i.test(mod), 'no setter for a risk setting');
};

// What is synced to the account is what Settings shows, and no more. A synced field nobody can see is a setting that can be changed from another device.
gates.B3 = () => {
  const shape = new Function('return {' + /shapeUserSettings: (function[\s\S]*?\n    \}),\n/.exec(html)[1].replace(/^function/, 'shapeUserSettings: function') + '}')().shapeUserSettings;
  const out = shape({ settings: {} });
  assert.deepStrictEqual(Object.keys(out).sort(), ['clockFormat', 'darkMode', 'kalBotLayout', 'landingPref', 'reduceMotion', 'skin']);
  assert.strictEqual(shape({}), null, 'never synced is null, not defaults');
  const hostile = shape({ settings: { tickerEnabled: false, hideAccountDock: true, soundAlerts: false, landingPref: 'trades', alpacaKeyId: 'x' } });
  assert.deepStrictEqual(Object.keys(hostile).sort(), Object.keys(out).sort(), 'old synced fields are ignored, not carried');
  const adopt = fnSource('adoptLocalSettingsIntoAccount');
  for (const key of ['darkMode', 'reduceMotion', 'kalBotLayout', 'clockFormat', 'landingPref']) assert.ok(adopt.includes(key + ':'), 'the first sync adopts ' + key);
  assert.ok(!/ticker|dock|notepad|sound|alpaca/i.test(adopt), 'and nothing from the removed pages');
};

// Settings has exactly these rows. A new row is a new control, so it is added here on purpose or the suite is red.
gates.B4 = () => {
  const page = /<main class="page" id="page-settings"[\s\S]*?<\/main>/.exec(code)[0];
  const titles = [...page.matchAll(/<div class="settings-row-title">([^<]*)<\/div>/g)].map((m) => m[1].trim());
  assert.deepStrictEqual(titles, ['Account', 'Dark mode', 'Theme', 'Default landing page', 'Clock format', 'Limit graphics', 'Reset preferences']);
  const landing = [...page.matchAll(/<button class="tf-btn" data-value="(\w+)"( id="landingKalshiBtn")?/g)].map((m) => m[1]);
  assert.ok(['auto', 'brief', 'kalshi'].every((v) => landing.includes(v)) && !landing.includes('trades'), 'the landing page choices are Auto, Brief and Kalshi');
};

// Sign in only: no confirm field, no invite field, no "Create one".
gates.B5 = () => {
  const gate = /<div class="auth-gate"[\s\S]*?<\/form>[\s\S]*?<button type="button" id="authForgotBtn"[^>]*>[^<]*<\/button>/.exec(code)[0];
  assert.deepStrictEqual([...gate.matchAll(/<input[^>]*\bid="(\w+)"/g)].map((m) => m[1]), ['authEmail', 'authPassword', 'authRememberMe']);
  assert.ok(!/Create|Don't have|Invite|Confirm password/i.test(gate), 'the sign-in screen offers no way to make an account');
  assert.ok(/Forgot password/.test(gate), 'but it keeps the way back in');
};

// An old stored landing choice ("trades") or a synced one must not leave a dead choice selected, and a landing on Kalshi waits for the account to be known to be the admin.
gates.B6 = () => {
  const stored = {};
  const buttons = ['auto', 'brief', 'kalshi'].map((v) => { const b = { dataset: { value: v }, on: false }; b.classList = { toggle(c, on) { b.on = on; } }; return b; });
  const src = fnSource('applyLandingPref');
  const apply = new Function('landingChoiceEl', 'window', 'syncUserSetting', src + '\nreturn applyLandingPref;')(
    { querySelectorAll: () => ({ forEach: (f) => buttons.forEach(f) }) }, { localStorage: { setItem: (k, v) => { stored[k] = v; } } }, () => {});
  apply('trades', true);
  assert.strictEqual(stored['shwoopnet:landingPref'], 'auto', 'the removed Trades choice is stored as Auto');
  assert.deepStrictEqual(buttons.filter((b) => b.on).map((b) => b.dataset.value), ['auto'], 'and Auto is the one shown selected');
  apply('kalshi', true);
  assert.strictEqual(stored['shwoopnet:landingPref'], 'kalshi');
};

// The brief describes the indices and only the indices. It never states a number it was not given, and it never claims anything about a screener or a position.
gates.B7 = () => {
  const src = [varSource('INDEX_PROXIES'), ...['indexReads', 'pct', 'findQuote', 'renderBriefHeadline'].map(fnSource)].join('\n');
  function run(quotes) {
    const els = { '.brief-headline': { textContent: '' }, '.brief-lede': { textContent: '' } };
    const doc = { querySelector: (s) => els[s] };
    const watchlist = Object.keys(quotes).map((sym) => ({ sym, price: quotes[sym][0], prevClose: quotes[sym][1] }));
    const f = new Function('document', 'watchlist', 'isUsMarketOpen', 'getUsMarketSession', src + '\nreturn renderBriefHeadline;')(doc, watchlist, () => true, () => ({ session: 'regular', label: 'Regular session' }));
    f();
    return { head: els['.brief-headline'].textContent, lede: els['.brief-lede'].textContent };
  }
  const loading = run({ SPY: [null, null], QQQ: [null, null], DIA: [null, null] });
  assert.ok(/Loading today's market data/.test(loading.head) && loading.lede === '', 'before the first snapshot it says it is loading and states nothing');
  const up = run({ SPY: [512.4, 510.1], QQQ: [441.8, 438.9], DIA: [390.2, 391.0] });
  assert.ok(/The S&P is up 0\.45%, the Nasdaq up 0\.66%\./.test(up.lede), up.lede);
  assert.ok(!/screener|setup|Trade Overview|option|position|open/i.test(up.lede), 'the lede says nothing about trading: ' + up.lede);
  const partial = run({ SPY: [512.4, 510.1], QQQ: [441.8, 438.9] });
  assert.ok(/Loading/.test(partial.head), 'with one index missing it still says it is loading');
};

// A snapshot adds symbols and prices and nothing else; the watchlist never invents a price.
gates.B8 = () => {
  const src = ['ensureInWatchlist', 'tapeNews', 'handleSharedMarketSnapshotUpdate'].map(fnSource).join('\n');
  const calls = [];
  const watchlist = [{ sym: 'PLTR', price: null, prevClose: null }];
  const f = new Function('watchlist', 'INDEX_PROXIES', 'renderIndices', 'renderSentiment', 'renderBriefHeadline', 'renderMovers', 'renderMarketNews', 'renderEarningsCalendar', 'marketTapeData',
    src + '\nreturn { handle: handleSharedMarketSnapshotUpdate, ensure: ensureInWatchlist };')(watchlist, [], () => {}, () => {}, () => {}, () => {}, (n) => calls.push(['news', n]), () => {}, null);
  f.handle(null);
  assert.deepStrictEqual(watchlist, [{ sym: 'PLTR', price: null, prevClose: null }], 'no snapshot yet leaves the page as it was');
  f.handle({ quotes: { PLTR: { price: 24.5, prevClose: 23.1 }, COIN: { price: 190, prevClose: 185 }, BAD: { price: null } }, news: [] });
  assert.deepStrictEqual(watchlist.map((w) => [w.sym, w.price]), [['PLTR', 24.5], ['COIN', 190]], 'priced symbols are added or updated, an unpriced one is skipped');
  f.ensure('PLTR', 1, 1);
  assert.strictEqual(watchlist[0].price, 24.5, 'ensuring a symbol that is already tracked never overwrites its price');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();

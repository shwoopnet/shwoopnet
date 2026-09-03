// WHAT THE PAGE MAY CLAIM ABOUT AN EQUITIES PRICE, AND WHEN.
//
// The display paths used to have one answer for the whole day: poll every
// 45 seconds forever, and render whatever came back as current. Both halves
// were wrong at opposite ends of the clock. Between 16:00 and 17:00 ET IEX
// is still printing (measured 2026-09-02: PLTR at 16:41) and the app had
// nothing to say about it; at 3am nothing is printing at all, yet
// /trades/latest still answers 200 with the previous afternoon's price and
// the header rendered "Live via Alpaca (IEX)" over it, or "Sync failed",
// which reads as a fault where there is none.
//
// These gates state the consequences, not the mechanism.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function extract(name) {
  const start = src.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('not found in index.html: ' + name);
  let depth = 0, end = -1;
  for (let i = src.indexOf('{', start); i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) { end = i + 1; break; } }
  }
  return src.slice(start, end);
}

function liftNum(name) {
  const m = new RegExp('var ' + name + ' = ([0-9*\\s+]+);').exec(src);
  if (!m) throw new Error(name + ' not found');
  // eslint-disable-next-line no-new-func
  return new Function('return (' + m[1] + ')')();
}

// isWithinIexDataWindow leans on the page's own holiday helpers, so the
// whole cluster is lifted together rather than stubbed -- a stubbed
// holiday check could not catch a window that claimed Thanksgiving prints.
const holidayCluster = ['getEasterMonthDay', 'ymdKey', 'weekdayOf', 'nthWeekday', 'lastWeekday',
  'observedDay', 'getUsMarketHolidayKeys', 'isUsMarketHoliday'].map(extract).join('\n');

const windowFns = new Function(
  holidayCluster + '\n' +
  'var IEX_DATA_WINDOW_OPEN_MIN = ' + liftNum('IEX_DATA_WINDOW_OPEN_MIN') + ';\n' +
  'var IEX_DATA_WINDOW_CLOSE_MIN = ' + liftNum('IEX_DATA_WINDOW_CLOSE_MIN') + ';\n' +
  'var PRICE_AGE_CURRENT_MS = ' + liftNum('PRICE_AGE_CURRENT_MS') + ';\n' +
  'var QUOTE_POLL_INTERVAL_MS = ' + liftNum('QUOTE_POLL_INTERVAL_MS') + ';\n' +
  'var QUOTE_POLL_INTERVAL_CLOSED_MS = ' + liftNum('QUOTE_POLL_INTERVAL_CLOSED_MS') + ';\n' +
  'var QUOTE_BATCH_MIN_INTERVAL_MS = ' + liftNum('QUOTE_BATCH_MIN_INTERVAL_MS') + ';\n' +
  extract('isWithinIexDataWindow') + '\n' +
  extract('isUsMarketOpen') + '\n' +
  extract('priceAgeStatus') + '\n' +
  extract('equitiesPollIntervalMs') + '\n' +
  extract('quoteBatchMinIntervalMs') + '\n' +
  extract('formatAgo') + '\n' +
  extract('quoteFeedStatus') + '\n' +
  'return { isWithinIexDataWindow: isWithinIexDataWindow, priceAgeStatus: priceAgeStatus,' +
  ' equitiesPollIntervalMs: equitiesPollIntervalMs, quoteBatchMinIntervalMs: quoteBatchMinIntervalMs,' +
  ' quoteFeedStatus: quoteFeedStatus, isUsMarketOpen: isUsMarketOpen };'
)();

// 2026-09-02 is a Wednesday; ET is UTC-4 in September.
const at = (utc, day = '02') => new Date(`2026-09-${day}T${utc}:00Z`);
const MIN = 60 * 1000;

const gates = {};

// ---- G1: a price inside the window renders as current ----
gates.G1 = () => {
  const { priceAgeStatus, isWithinIexDataWindow } = windowFns;
  const now = at('20:45').getTime(); // 16:45 ET
  assert.strictEqual(isWithinIexDataWindow(at('20:45')), true, '16:45 ET is inside IEX\'s day -- PLTR printed at 16:41 that day');
  const s = priceAgeStatus(now - 30 * 1000, now, true);
  assert.strictEqual(s.level, 'current', 'A 30-second-old print inside the window is current, and must render as such');
  // And 09:00 ET, which is before the exchange opens but after IEX starts.
  assert.strictEqual(isWithinIexDataWindow(at('13:00')), true, 'Pre-market 09:00 ET is inside the window -- 08:45/09:00 bars were measured');
};

// ---- G2: a price outside the window renders with its age, and does NOT
// read as a fault ----
gates.G2 = () => {
  const { priceAgeStatus, quoteFeedStatus } = windowFns;
  const now = at('07:00', '03').getTime(); // 3am ET
  const printedAt = at('20:41').getTime(); // 16:41 ET the day before
  const s = priceAgeStatus(printedAt, now, false);
  assert.strictEqual(s.level, 'aged', 'A price from 16:41 ET shown at 3am must be aged, never current');
  assert.ok(s.ageMs > 10 * 60 * MIN, 'and its age must be the real one');

  // The header, with the equities batch "succeeding" -- which it does at
  // 3am, on a price hours old.
  const status = quoteFeedStatus({
    equitiesOk: true, cryptoOk: false, failStreak: 0, lastGoodAt: now - 1000, now,
    streakLimit: 3, staleMs: 150000, sources: ['alpaca'],
    dataWindowOpen: false, lastEquitiesPriceAgeMs: now - printedAt,
  });
  assert.ok(!/Live/.test(status.text), 'A 200 response at 3am must not render as "Live": ' + status.text);
  assert.ok(/closed/i.test(status.text), 'It must say the market is closed: ' + status.text);
  assert.ok(/ago/.test(status.text), 'and when the last price was: ' + status.text);
  assert.ok(!/fail/i.test(status.text) && status.cls !== 'fail',
    'A closed market is not a fault and must never read as one: ' + status.text);

  // Even with the feed genuinely all-failing overnight, it is still not
  // reported as a fault -- there is nothing to fetch.
  const dead = quoteFeedStatus({
    equitiesOk: false, cryptoOk: false, failStreak: 99, lastGoodAt: now - 10 * 60 * MIN, now,
    streakLimit: 3, staleMs: 150000, sources: [],
    dataWindowOpen: false, lastEquitiesPriceAgeMs: now - printedAt,
  });
  assert.ok(!/Sync failed/.test(dead.text), 'Outside the window "Sync failed" is the wrong story: ' + dead.text);
};

// ---- G3: a genuinely broken feed INSIDE the window still says so ----
gates.G3 = () => {
  const { quoteFeedStatus } = windowFns;
  const now = at('18:00').getTime();
  const status = quoteFeedStatus({
    equitiesOk: false, cryptoOk: false, failStreak: 5, lastGoodAt: now - 10 * MIN, now,
    streakLimit: 3, staleMs: 150000, sources: [],
    dataWindowOpen: true, lastEquitiesPriceAgeMs: 10 * MIN,
  });
  assert.strictEqual(status.cls, 'fail', 'Honesty runs both ways: a dead feed at 2pm is still a fault');
  assert.ok(/Sync failed/.test(status.text));
};

// ---- G4: per-symbol age is independent ----
gates.G4 = () => {
  const { priceAgeStatus } = windowFns;
  const now = at('20:45').getTime(); // 16:45 ET
  const pltr = priceAgeStatus(at('20:41').getTime(), now, true); // printed 16:41
  const aapl = priceAgeStatus(at('19:59').getTime(), now, true); // last print 15:59
  assert.strictEqual(pltr.level, 'current', 'PLTR genuinely printed four minutes ago');
  assert.strictEqual(aapl.level, 'aged', 'AAPL has not printed in 46 minutes and must not borrow PLTR\'s freshness');
  assert.ok(aapl.ageMs > pltr.ageMs);
  // A quote with no print timestamp (the Finnhub fallback) is unknown --
  // not current, and not stale either.
  assert.strictEqual(priceAgeStatus(null, now, true).level, 'unknown');
  assert.strictEqual(priceAgeStatus(undefined, now, true).level, 'unknown');
};

// ---- G5: extending the hours must not raise requests per hour ----
gates.G5 = () => {
  const { equitiesPollIntervalMs, quoteBatchMinIntervalMs } = windowFns;
  const open = at('18:00'), shut = at('07:00', '03');
  assert.strictEqual(equitiesPollIntervalMs(open), liftNum('QUOTE_POLL_INTERVAL_MS'),
    'Inside the window the cadence is exactly what it was -- more hours, not more polling per hour');
  assert.ok(equitiesPollIntervalMs(shut) > equitiesPollIntervalMs(open) * 4,
    'Outside the window it must poll substantially LESS, because nothing is changing');
  // The journal-listener-driven bursts have to slow down with it, or the
  // backend heartbeat alone keeps the batch running once a minute all night.
  assert.strictEqual(quoteBatchMinIntervalMs(shut), equitiesPollIntervalMs(shut),
    'The dedupe floor must rise to the closed cadence, or slowing the loop saves nothing');
  assert.strictEqual(quoteBatchMinIntervalMs(open), liftNum('QUOTE_BATCH_MIN_INTERVAL_MS'),
    'and must be untouched inside the window');
};

// ---- G6: THE MONEY-SAFETY PROPERTY -- the trading gate is unchanged ----
gates.G6 = () => {
  const { isUsMarketOpen } = windowFns;
  // This page's isUsMarketOpen is what the ORB screener's own display and
  // local re-scan key off. It must remain exactly 9:30-16:00 ET, whatever
  // the data window says, at every minute of the day.
  const realNow = Date;
  try {
    for (let m = 0; m < 24 * 60; m++) {
      const when = new Date(Date.UTC(2026, 8, 2, 4 + Math.floor(m / 60), m % 60));
      global.Date = class extends realNow {
        constructor(...a) { super(...(a.length ? a : [when.getTime()])); }
        static now() { return when.getTime(); }
      };
      const expected = m >= 9 * 60 + 30 && m < 16 * 60;
      assert.strictEqual(isUsMarketOpen(), expected, 'Trading-hours gate moved at ET minute ' + m);
    }
  } finally { global.Date = realNow; }
  // And the widened window is nowhere near it in the source: the constants
  // must not be wired into the market-open check.
  const openFn = extract('isUsMarketOpen');
  assert.ok(!/IEX_DATA_WINDOW/.test(openFn),
    'The trading-hours check must never be expressed in terms of the display data window');
};

// ---- G7: the window is the measured one, and is described as IEX's ----
gates.G7 = () => {
  const { isWithinIexDataWindow } = windowFns;
  assert.strictEqual(isWithinIexDataWindow(at('11:59')), false, '07:59 ET is before IEX starts');
  assert.strictEqual(isWithinIexDataWindow(at('12:00')), true, '08:00 ET is the measured start');
  assert.strictEqual(isWithinIexDataWindow(at('20:59')), true, '16:59 ET is the last minute inside');
  assert.strictEqual(isWithinIexDataWindow(at('21:00')), false, '17:00 ET is the end of IEX\'s day');
  assert.strictEqual(isWithinIexDataWindow(at('18:00', '05')), false, 'A Saturday prints nothing at any hour');
  assert.strictEqual(isWithinIexDataWindow(new Date('2026-11-26T18:00:00Z')), false,
    'Thanksgiving has no session, so no prints -- the window must respect holidays');
  // The name and its comment have to say this is IEX's day, not the
  // exchange's, or the next reader reuses it as a trading gate.
  const block = src.slice(src.indexOf('IEX_DATA_WINDOW_OPEN_MIN') - 2500, src.indexOf('IEX_DATA_WINDOW_OPEN_MIN'));
  assert.ok(/16:41/.test(block) && /IEX/.test(block),
    'The window constant must carry the measured evidence it was derived from');
  assert.ok(/NOT a trading gate/i.test(block),
    'and must say plainly that it is not a trading gate');
  // Nothing in the UI may promise round-the-clock equities prices.
  assert.ok(!/24\/7 equities/i.test(src), '"24/7 equities" is not achievable and must not be implied');
};

// ---- G8: a screener that is not supposed to be running does not read
// as a broken one ----
gates.G8 = () => {
  const picksFreshness = new Function(
    'function firestoreMillis(x){ return Number(x); }\n' + extract('picksFreshness') + '\nreturn picksFreshness;'
  )();
  const now = 1000000000;
  const interval = 60000;
  const scannedAt = now - 5 * 60 * 60 * 1000; // last scan five hours ago
  const closed = picksFreshness(scannedAt, now, interval, false);
  assert.strictEqual(closed.level, 'closed',
    'After 16:00 the equities screener is correctly idle, and an idle-by-design cycle must not be reported as stale');
  const open = picksFreshness(scannedAt, now, interval, true);
  assert.strictEqual(open.level, 'stale',
    'The same five-hour-old scan DURING the session is a genuine problem and must still say so');
  // Crypto passes no session flag at all and keeps the old three answers.
  assert.strictEqual(picksFreshness(scannedAt, now, interval).level, 'stale',
    'Crypto runs 24/7 -- an old crypto scan is stale whatever the equities clock says');
  assert.strictEqual(picksFreshness(now - 1000, now, interval, false).level, 'fresh',
    'A scan from a second ago is fresh regardless of the session flag');
  // The distinction is worthless if the equities card does not actually
  // hand the session state over -- a pure function tested alone cannot
  // catch that wiring being dropped.
  assert.ok(/picksFreshness\(backendIntradayPicksUpdatedAt,[\s\S]{0,80}?isUsMarketOpen\(\)\)/.test(src),
    'The equities setups card must pass the session state into picksFreshness');
  assert.ok(/picksFreshness\(backendCryptoPicksUpdatedAt,\s*Date\.now\(\),\s*CRYPTO_CYCLE_INTERVAL_MS\)/.test(src),
    'The crypto card must NOT pass one -- crypto has no closed session');
};

let failed = 0;
Object.keys(gates).forEach((k) => {
  try { gates[k](); console.log(k + ': PASS'); }
  catch (e) { failed++; console.error(k + ': FAIL — ' + e.message); }
});
if (failed) { console.error(failed + ' gate(s) failed'); process.exit(1); }
console.log('extendedSessionDataGates: ALL PASS');

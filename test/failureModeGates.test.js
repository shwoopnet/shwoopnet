'use strict';
// WHAT THE PAGE SAYS WHEN IT DOES NOT KNOW.
//
// Every fault this file gates has the same shape: the frontend had a
// confident-looking answer ready for a case where it had no answer at all.
// A price cell that says "NaN", a profit factor of "∞" from three winning
// trades, a P&L of exactly $0.00 on a position nobody could price, a
// setups list from a screener that stopped running hours ago, the literal
// word "undefined" where a trade's reasoning belongs. None of these look
// broken, which is precisely what makes them worse than a blank card.
//
// These gates state the CONSEQUENCE of each one, not the mechanism.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

// Lifted out of index.html with new Function, per CLAUDE.md -- there is no
// build step to import from.
function lift(name, deps) {
  const start = src.indexOf('function ' + name + '(');
  assert.notStrictEqual(start, -1, 'not found in index.html: ' + name);
  let d = 0, end = -1;
  for (let i = src.indexOf('{', start); i < src.length; i++) {
    if (src[i] === '{') d++;
    else if (src[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  const names = Object.keys(deps || {});
  return new Function(...names, 'return (' + src.slice(start, end) + ')')(...names.map((n) => deps[n]));
}

const gates = {};

// ---------------------------------------------------------------------
// A price cell must never print a non-number as if it were a price.
// ---------------------------------------------------------------------
gates.G1_fmt_never_prints_a_fake_price = () => {
  const fmt = lift('fmt');
  // parseFloat('') on an Alpaca field, or a level the analysis never
  // produced. "NaN" in a Stop column is read as a stop.
  assert.strictEqual(fmt(NaN), '—', 'NaN must render as a gap, never as the string "NaN"');
  assert.strictEqual(fmt(undefined), '—', 'a missing level must render as a gap');
  assert.strictEqual(fmt(null), '—', 'a null level must render as a gap, not as $0.00');
  assert.strictEqual(fmt(Infinity), '—', 'an infinite price is not a price');
  // ...and must not throw. A TypeError raised inside a .map() building a
  // table's innerHTML takes the whole card down, which is how the
  // undefined-function bug blanked Backend Status.
  assert.doesNotThrow(() => fmt(undefined), 'a missing level must not blank the card it appears in');
  // Real prices are untouched, including the sub-dollar crypto scaling
  // this function exists for.
  assert.strictEqual(fmt(12.345), '12.35');
  assert.strictEqual(fmt(0.12345678), '0.1235');
  assert.strictEqual(fmt(0.000012345678), '0.00001235');
  assert.strictEqual(fmt(0), '0.00000000', 'zero is a real number and must still print');
};

// ---------------------------------------------------------------------
// A profit factor with no losing trade has no denominator.
// ---------------------------------------------------------------------
gates.G2_profit_factor_without_a_loss_is_not_infinite = () => {
  const profitFactorText = lift('profitFactorText');
  assert.strictEqual(profitFactorText(Infinity, 0), '—',
    'three wins and no losses must not render as an infinitely profitable strategy');
  assert.strictEqual(profitFactorText(0, 0), '—',
    'no trades at all must not render as a measured profit factor of 0.00');
  assert.strictEqual(profitFactorText(NaN, 3), '—');
  // A real, computed figure still renders.
  assert.strictEqual(profitFactorText(1.5, 4), '1.50');
  assert.strictEqual(profitFactorText(0.8, 4), '0.80',
    'a genuinely losing profit factor must still be shown, not hidden behind a dash');
};

// The colour is a claim too: green on an uncomputable figure reads as the
// best result the engine ever produced.
gates.G3_uncomputable_profit_factor_is_not_coloured_green = () => {
  assert.ok(!/summary\.profitFactor >= 1 \? 'up' : 'down'/.test(src.replace(/summary\.stoppedCount === 0 \? '' : \(summary\.profitFactor >= 1 \? 'up' : 'down'\)/g, '')),
    'profit-factor colour must be gated on there being a loss to divide by');
  assert.ok(!src.includes("(pf === Infinity ? '∞' : pf.toFixed(2))"),
    'the Alpaca history card must not render ∞ for a lossless sample');
  assert.ok(!src.includes("isFinite(filtered.profitFactor) ? filtered.profitFactor.toFixed(2) : '∞'"),
    'the P&L summary card must not render ∞ for a lossless sample');
};

// ---------------------------------------------------------------------
// Setups computed hours ago must not be presented as current.
// ---------------------------------------------------------------------
gates.G4_a_dead_screener_does_not_look_like_a_quiet_market = () => {
  const firestoreMillis = lift('firestoreMillis');
  const picksFreshness = lift('picksFreshness', { firestoreMillis });
  const now = 1_700_000_000_000;
  const cycle = 5 * 60 * 1000;

  // The whole point: a scan that should have refreshed twice over and did
  // not is stale, and the card has to say so rather than showing its
  // entry/stop/target like any other row.
  assert.strictEqual(picksFreshness(now - 6 * 60 * 60 * 1000, now, cycle).level, 'stale',
    'a six-hour-old scan must be reported as stale');

  // But a backend that never wrote the field is UNKNOWN, not failing --
  // the same distinction reconcile health had to make. Rendering an old
  // build as stale forever is its own false alarm.
  assert.strictEqual(picksFreshness(null, now, cycle).level, 'unknown',
    'a backend that never wrote the timestamp must not read as stale');
  assert.strictEqual(picksFreshness(undefined, now, cycle).level, 'unknown');
  assert.strictEqual(picksFreshness('not a date', now, cycle).level, 'unknown');

  // One missed cycle is routine (a deploy swapping instances, a slow
  // Alpaca call). Crying stale on it trains the reader to ignore the
  // marker, which is how a real outage gets missed.
  assert.strictEqual(picksFreshness(now - cycle - 1000, now, cycle).level, 'fresh',
    'a single missed cycle must not be reported as stale');
  assert.strictEqual(picksFreshness(now - 2.5 * cycle, now, cycle).level, 'stale');

  // A Firestore Timestamp is the shape that has already silently produced
  // Invalid Date twice in this app.
  const ts = { seconds: Math.floor((now - 6 * 60 * 60 * 1000) / 1000), nanoseconds: 0 };
  assert.strictEqual(picksFreshness(ts, now, cycle).level, 'stale',
    'a Firestore Timestamp must be read as a time, not as an unreadable value');

  // Backend clock skew is not evidence of anything.
  assert.strictEqual(picksFreshness(now + 30000, now, cycle).ageMs, 0,
    'a timestamp slightly in the future must not render as a negative age');
};

// The stale state has to actually reach the cards, including the empty one:
// "No qualifying setups right now" is a claim about the present that a dead
// screener cannot support.
gates.G5_empty_setups_card_distinguishes_quiet_from_stale = () => {
  const eq = src.indexOf('function renderIntradayBlocks(');
  const eqBody = src.slice(eq, src.indexOf('function renderCryptoBlocks(', eq));
  assert.ok(/eqFresh\.level === 'stale'/.test(eqBody),
    'the equities setups card must consult the scan age');
  assert.ok(eqBody.indexOf("eqFresh.level === 'stale'\n        ? '<div class=\"labs-backtest-status down\">No setups have been published") > -1
    || /level === 'stale'[\s\S]{0,200}No setups have been published/.test(eqBody),
    'its empty state must say "stale scan", not "quiet market", when the scan is stale');

  const cx = src.indexOf('function renderCryptoBlocks(');
  const cxBody = src.slice(cx, cx + 12000);
  assert.ok(/cxFresh\.level === 'stale'/.test(cxBody),
    'the crypto setups card must consult its own scan age');
  assert.ok(/level === 'stale'[\s\S]{0,200}No setups have been published/.test(cxBody),
    'the crypto empty state must distinguish stale from quiet too');

  // Costs nothing extra: both timestamps ride the user-doc snapshot the
  // app already subscribes to. A gate, because adding a fetch for them
  // would be the wrong fix.
  assert.ok(src.includes('backendIntradayPicksUpdatedAt = data.intradayScreenerUpdatedAt'),
    'the scan age must come from the existing snapshot, not a new request');
  assert.ok(src.includes('backendCryptoPicksUpdatedAt = data.cryptoScreenerUpdatedAt'));
};

// ---------------------------------------------------------------------
// A position nobody could price is not a flat position.
// ---------------------------------------------------------------------
gates.G6_unpriced_position_shows_a_dash_not_zero = () => {
  const rendered = [];
  const el = {
    innerHTML: '',
    querySelectorAll: () => ({ forEach: () => {} }),
  };
  const load = lift('loadStatusPositions', {
    getAlpacaPositionsCached: () => Promise.resolve([]),
    statusPositionsRenderGen: 7,
    alpacaPositionsBySymbol: () => ({}),
    canonicalSymbol: (x) => String(x).replace(/\//g, ''),
    findQuote: () => undefined,        // equities quote feed down
    findCryptoQuote: () => undefined,  // crypto quote feed down
    isUnreconciledEntry: () => false,  // a REAL, current entry
    statusPositionsSortKey: null,
    statusPositionsSortDir: 1,
    visibleStatusPositionsColumns: () => [{ key: 'pl', label: 'P&L' }],
    statusPositionsCellHTML: (k, r) => { rendered.push(r); return '<td></td>'; },
    applyValueFlashes: () => {},
    isUnreconciledEntryRow: () => false,
    strategyLabel: () => '',
    renderStatusPositions: () => {},
    closeAlpacaPositionSafely: () => Promise.resolve(),
    showPositionClosedToast: () => {},
    syncAlpacaFilledExits: () => {},
  });

  const entry = { id: 'e1', sym: 'BTC/USD', direction: 'Long', entry: 60000, qty: 0.5 };
  load([entry], el, 7, false);
  // The render happens in the resolved .then() inside; one macrotask is
  // enough for it to have run.
  return new Promise((resolve) => setTimeout(resolve, 0)).then(() => {
    assert.strictEqual(rendered.length, 1, 'the row must still render');
    const r = rendered[0];
    // The lie this replaces: current fell back to the ENTRY price, so P&L
    // came out as exactly $0.00 (+0.00%) and was painted green, on a
    // position that is moving and simply has not been priced.
    assert.strictEqual(r.pl, null, 'an unpriced position must report no P&L, not $0.00');
    assert.strictEqual(r.plPct, null, 'an unpriced position must report no percentage, not 0.00%');
    assert.strictEqual(r.current, null, 'an unpriced position must not show its entry price as the current price');
    assert.strictEqual(r.sizeDollar, null, 'size cannot be computed without a price');
    assert.notStrictEqual(r.current, entry.entry,
      'falling back to the entry price is what manufactured the flat P&L');
  });
};

// ---------------------------------------------------------------------
// A missing reason reads as missing.
// ---------------------------------------------------------------------
gates.G7_setup_with_no_notes_does_not_say_undefined = () => {
  let html = '';
  const el = {
    set innerHTML(v) { html = v; },
    get innerHTML() { return html; },
    querySelectorAll: () => ({ forEach: () => {} }),
  };
  const render = lift('renderWatchTradeCards', {
    computeBadgeInfo: () => ({ cls: 'ok', label: 'Active' }),
    journalEntries: [],
    isOpenAlpacaPositionForCurrentAccount: () => false,
    symbolBadgeHtml: () => '',
    jumpToTrade: () => {},
  });
  // Exactly what buildTradeFromPick produces for a pick the backend wrote
  // without a notes array -- the shape whose .slice() once blanked the
  // whole Equities Setups card.
  render(el, [{ sym: 'LCID', direction: 'Long', notes: [] }]);
  assert.ok(!/undefined/.test(html),
    'a setup with no recorded reason must not render the word "undefined" as its reasoning');
  assert.ok(/No reason recorded/.test(html),
    'it must say the reason is missing rather than leaving a bare empty line');
  // A real reason is untouched.
  render(el, [{ sym: 'LCID', direction: 'Long', notes: ['ORB high broke on 3x volume'] }]);
  assert.ok(/ORB high broke on 3x volume/.test(html));
};

// ---------------------------------------------------------------------
// One scan, one list. Two cards must not disagree about what it found.
// ---------------------------------------------------------------------
gates.G8_what_to_watch_shows_both_equities_strategies = () => {
  const w = src.indexOf('function renderWhatToWatch(');
  const body = src.slice(w, src.indexOf('function renderSentiment(', w));
  assert.ok(/mergedEquitiesPicks\(\)/.test(body),
    'What to Watch must read the same merged ORB+fade list Today\'s Setups does');
  assert.ok(!/backendIntradayPicks\.map\(buildTradeFromPick\)/.test(body),
    'reading only the breakout picks silently drops every fade setup from the card named "what to watch"');
};

// ---------------------------------------------------------------------
// Breadth is a claim about the whole universe.
// ---------------------------------------------------------------------
gates.G9_crypto_breadth_not_claimed_from_a_fraction = () => {
  const results = [];
  const el = { set innerHTML(v) { results.push(v); }, get innerHTML() { return results[results.length - 1] || ''; } };
  const priced = (n, dir) => Array.from({ length: 12 }, (_, i) => (
    i < n ? { sym: 'C' + i, price: dir > 0 ? 110 : 90, prevClose: 100 } : { sym: 'C' + i, price: null, prevClose: null }
  ));

  const run = (watchlist) => {
    const render = lift('renderCryptoSentiment', {
      document: { getElementById: () => el },
      cryptoWatchlist: watchlist,
      pct: (a, b) => ((a - b) / b) * 100,
    });
    render();
    return el.innerHTML;
  };

  // Two pairs out of twelve, both up, used to draw a full green bar and
  // the sentence "Broadly positive" -- a statement about the crypto
  // market made from a sixth of it.
  const thin = run(priced(2, 1));
  assert.ok(!/Broadly positive/.test(thin),
    'a headline about crypto must not be claimed from a sixth of the universe');
  assert.ok(/2 of 12/.test(thin), 'it must say how much of the universe it can actually see');

  // With most of it priced the headline is legitimate again -- and still
  // discloses what is missing, so the reader is not told about twelve
  // pairs when ten were measured.
  const most = run(priced(10, 1));
  assert.ok(/Broadly positive/.test(most), 'a real quorum must still produce a real read');
  assert.ok(/not priced yet/.test(most), 'the pairs that did not price must still be disclosed');

  // The full universe says nothing extra -- no defensive noise on the
  // path that was already correct.
  const all = run(priced(12, 1));
  assert.ok(!/not priced yet/.test(all), 'a complete read must not carry a caveat it does not need');
};

// ---------------------------------------------------------------------
// The init sequence must actually finish, and the filters it loads must
// survive the load.
// ---------------------------------------------------------------------
gates.G10_activity_filter_prefs_survive_page_load = () => {
  // Reproduces the real execution order: loadActivityLogFilterPrefs() is
  // called ~3,400 lines above the `var activityLogHiddenGroups`
  // declaration, so at call time the name is hoisted but unassigned.
  // Reading a property off it threw a TypeError on EVERY page load, which
  // aborted the rest of that top-level init block -- silently, because the
  // page still looked fine.
  const declStart = src.indexOf('var activityLogHiddenGroups = activityLogHiddenGroups');
  assert.notStrictEqual(declStart, -1,
    'the declaration must not clobber preferences the loader has already read');
  const declaration = src.slice(declStart, src.indexOf(';', declStart) + 1);

  const fnStart = src.indexOf('function loadActivityLogFilterPrefs(');
  let d = 0, fnEnd = -1;
  for (let i = src.indexOf('{', fnStart); i < src.length; i++) {
    if (src[i] === '{') d++;
    else if (src[i] === '}') { d--; if (!d) { fnEnd = i + 1; break; } }
  }
  const loader = src.slice(fnStart, fnEnd);

  const run = new Function('window', 'saveActivityLogFilterPrefs',
    'var activityLogHiddenGroups;\n' + loader +
    '\nloadActivityLogFilterPrefs();\n' + declaration +
    '\nreturn activityLogHiddenGroups;');
  const winFor = (store) => ({ localStorage: {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = v; },
  } });

  // A first visit, or any browser with nothing stored: the try block
  // assigns nothing, so the very next line read a property off undefined.
  // This is the shape that actually threw on every load.
  let fresh;
  assert.doesNotThrow(() => { fresh = run(winFor({}), () => {}); },
    'init must not throw with nothing in storage — that TypeError aborted the rest of the init block on every page load');
  assert.deepStrictEqual(fresh, {}, 'a first visit starts with nothing hidden');

  let result;
  assert.doesNotThrow(() => {
    result = run(winFor({ 'shwoopnet:activityLogHiddenGroups': JSON.stringify({ skipped: true }) }), () => {});
  }, 'init must not throw before it has finished wiring the page up');
  assert.deepStrictEqual(result, { skipped: true },
    'a group the owner hid must still be hidden after a reload — silently discarding it makes the log look like nothing happened');
};

let failures = 0;
const only = process.argv[2];
Promise.all(Object.keys(gates).filter((k) => !only || k.includes(only)).map((name) => {
  return Promise.resolve().then(gates[name]).then(
    () => console.log('PASS ' + name),
    (e) => { failures++; console.error('FAIL ' + name + ': ' + e.message); }
  );
})).then(() => {
  if (failures) { console.error(failures + ' gate(s) failed'); process.exit(1); }
  console.log('failureModeGates: all gates passed');
});

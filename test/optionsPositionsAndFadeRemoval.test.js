// Two changes, one gate file since they touch the same area of the page:
// the Options Income (CSP) card added for shwoop-server's
// optionsIncomeCycle.js, and the equities fade strategy's toggle/setups/
// Backend-Status surfaces removed now that it's not being used.

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

const optionsDaysToExpiration = lift('optionsDaysToExpiration');

const gates = {};

gates.G1 = () => {
  const now = new Date('2026-09-03T14:00:00Z');
  const dte = optionsDaysToExpiration('2026-10-10', now);
  assert.ok(dte > 36 && dte < 38, `expected ~37 DTE, got ${dte}`);
  console.log('G1 PASS optionsDaysToExpiration counts forward from now, matching the backend\'s own daysToExpiration');
};

gates.G2 = () => {
  const code = src.replace(/\/\/[^\n]*/g, '');
  assert.ok(/function renderOptionsPositions\(\)/.test(code), 'renderOptionsPositions must exist');
  assert.ok(/if\(!open\.length && !closed\.length\)\{ card\.hidden = true; return; \}/.test(code),
    'an account with no options positions at all must have the card hidden, not showing an empty table');
  console.log('G2 PASS the Options Income card hides itself entirely when there is nothing to show');
};

gates.G3 = () => {
  const code = src.replace(/\/\/[^\n]*/g, '');
  // Every string built into the table must go through escapeHtml or a
  // numeric formatter (ftMoney) -- backend-generated text, but this is the
  // same guard the activity log already applies to backend strings.
  assert.ok(/escapeHtml\(p\.underlyingSymbol/.test(code), 'underlying symbol must be escaped');
  assert.ok(/escapeHtml\(p\.expirationDate/.test(code), 'expiration date must be escaped');
  console.log('G3 PASS options table cells escape backend-sourced strings');
};

gates.G4 = () => {
  const code = src.replace(/\/\/[^\n]*/g, '');
  // No live "current price" column -- the position record the backend
  // writes doesn't carry one (see optionsIncomeCycle.js), and fabricating
  // one here would be exactly the "made-up P&L" failure fmt()'s own header
  // comment already rejects for equities/crypto.
  assert.ok(!/Current<\/th>/.test(code.match(/optionsPositionsBody[\s\S]{0,2000}/)?.[0] || ''),
    'the options table must not claim a live current-price column it cannot honestly fill');
  console.log('G4 PASS no fabricated current-price column on the options table');
};

// ---- Fade removal ----

gates.G5 = () => {
  const NO_LONGER_PRESENT = [
    'fadeScreenerEnableToggle', 'fadeAutoTradeEnableToggle', 'fadeAutoTradeMoneyClause',
    'effectiveFadeScreenerOn', 'effectiveFadeAutoTradeOn',
    'backendFadePicks', 'backendFadeScreenerEnabledOnServer', 'backendFadeAutoTradeEnabledOnServer',
    'fadeScreenerEnabledOverride', 'fadeAutoTradeEnabledOverride', 'fadeScreenerPicks',
  ];
  const found = NO_LONGER_PRESENT.filter((name) => src.includes(name));
  assert.deepStrictEqual(found, [], `fade control/data-flow identifiers must be fully removed, found: ${found.join(', ')}`);
  console.log('G5 PASS every fade screener/auto-trade control and data-flow identifier is gone');
};

gates.G6 = () => {
  // The HISTORICAL labeling must survive -- a past fade trade in the
  // Journal or Trade Overview still needs to say what it was, or realised
  // P&L attribution between two equities strategies becomes unreadable.
  assert.ok(/strategy === 'fade'/.test(src), 'past fade trades must still be labelled correctly in the Journal/badges');
  assert.ok(/'equities-fade': 'Equities fade'/.test(src),
    'the forward-test record must still be able to show a historical fade snapshot if one was ever recorded -- an append-only record is never hidden after the fact');
  console.log('G6 PASS historical fade trade labels and forward-test snapshots are preserved, only the active controls are gone');
};

gates.G7 = () => {
  const code = src.replace(/\/\/[^\n]*/g, '');
  // mergedEquitiesPicks must still exist and still be what Today's Setups
  // and What To Watch both read -- only its OWN fade merge should be gone.
  assert.ok(/function mergedEquitiesPicks\(\)/.test(code));
  assert.ok(!/backendFadePicks/.test(code), 'the picks merge must no longer read fade picks at all');
  console.log('G7 PASS mergedEquitiesPicks still exists, now ORB-only');
};

// ---- Options auto-trade control (added after the Backend Status row
// shipped showing options auto-trade ON with no way to switch it off from
// this card, and Flatten All not pausing it either) ----

gates.G8 = () => {
  const code = src.replace(/\/\/[^\n]*/g, '');
  assert.ok(/id="optionsAutoTradeEnableToggle"/.test(code), 'Auto-Trading Controls must have a real options auto-trade switch');
  assert.ok(/id="optionsScreenerEnableToggle"/.test(code), 'Screeners must have a real options screener switch');
  assert.ok(/function effectiveOptionsAutoTradeOn\(\)/.test(code));
  assert.ok(/function effectiveOptionsScreenerOn\(\)/.test(code));
  console.log('G8 PASS options has real Settings toggles, not just a read-only Backend Status row');
};

gates.G9 = () => {
  const code = src.replace(/\/\/[^\n]*/g, '');
  const flattenBody = code.match(/function flattenAllPositions\(\)\{[\s\S]*?\n  \}/)?.[0] || '';
  assert.ok(flattenBody, 'flattenAllPositions must exist');
  assert.ok(/effectiveOptionsAutoTradeOn\(\)/.test(flattenBody),
    'Flatten All must check options auto-trade before deciding whether to pause anything');
  assert.ok(/optionsAutoTradeEnabledOverride: false/.test(flattenBody),
    'Flatten All must actually pause options auto-trade, or its own "nothing re-enters right after" promise is false for this strategy');
  console.log('G9 PASS Flatten All pauses options auto-trade along with equities and crypto');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }

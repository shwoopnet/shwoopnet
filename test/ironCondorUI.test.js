// Iron condor frontend UI (shwoop-server's optionsIronCondorCycle.js), a
// third options mechanism mirroring Weekly Credit Spread's own card,
// settings toggles, pause row and Backend Status row.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name) {
  const start = html.indexOf('function ' + name + '(');
  assert.notStrictEqual(start, -1, 'could not find function ' + name + ' in index.html');
  let depth = 0;
  const open = html.indexOf('{', start);
  for (let j = open; j < html.length; j++) {
    if (html[j] === '{') depth++;
    else if (html[j] === '}') { depth--; if (depth === 0) return html.slice(start, j + 1); }
  }
  throw new Error('unbalanced braces for ' + name);
}

function liftVar(name) {
  const re = new RegExp('var ' + name + ' = (\\{[\\s\\S]*?\\n  \\});');
  const m = html.match(re);
  assert.ok(m, 'could not find var ' + name + ' in index.html');
  return m[1];
}

const gates = {};

// G1 -- the status label map covers every real status the backend's
// state machine (optionsIronCondorCycle.js) actually uses.
gates.G1 = () => {
  const labels = new Function('return (' + liftVar('IRON_CONDOR_STATUS_LABELS') + ')')();
  const realStatuses = [
    'pending_put_long', 'pending_put_short', 'pending_call_long', 'pending_call_short',
    'open',
    'pending_close_put_short', 'pending_close_put_long', 'pending_close_call_short', 'pending_close_call_long',
    'pending_unwind', 'closed',
  ];
  realStatuses.forEach((s) => {
    assert.ok(labels[s] && typeof labels[s] === 'string' && labels[s].length > 0,
      'IRON_CONDOR_STATUS_LABELS must cover status: ' + s);
  });
  console.log('G1 PASS IRON_CONDOR_STATUS_LABELS covers every real optionsIronCondorCycle.js status');
};

// G2 -- the settings toggles wire to the exact override field names
// shwoop-server's settings.js expects (ironCondorScreenerEnabledOverride /
// ironCondorAutoTradeEnabledOverride), not a mismatched or guessed name.
gates.G2 = () => {
  const code = html.replace(/\/\/[^\n]*/g, '');
  assert.ok(/saveAutoTradeOverride\(\{\s*ironCondorScreenerEnabledOverride: next\s*\}\)/.test(code),
    'the screener toggle must save ironCondorScreenerEnabledOverride');
  assert.ok(/saveAutoTradeOverride\(\{\s*ironCondorAutoTradeEnabledOverride: false\s*\}\)/.test(code),
    'the auto-trade toggle must save ironCondorAutoTradeEnabledOverride on the off path');
  assert.ok(/saveAutoTradeOverride\(\{\s*ironCondorAutoTradeEnabledOverride: true\s*\}\)/.test(code),
    'the auto-trade toggle must save ironCondorAutoTradeEnabledOverride on the armed-confirm path');
  console.log('G2 PASS iron condor settings toggles save the exact backend override field names');
};

// G3 -- the flatten-all safety action pauses iron condor auto-trading
// too, not just the other three mechanisms, since it exists specifically
// to stop every auto-trader before closing positions.
gates.G3 = () => {
  const code = html.replace(/\/\/[^\n]*/g, '');
  assert.ok(/effectiveIronCondorAutoTradeOn\(\)/.test(code),
    'effectiveIronCondorAutoTradeOn must exist and be referenced');
  const flattenBlock = code.match(/if\(effectiveAutoTradeOn\(\)[\s\S]{0,900}/)?.[0] || '';
  assert.ok(/effectiveIronCondorAutoTradeOn\(\)/.test(flattenBlock),
    'flatten-all must also check effectiveIronCondorAutoTradeOn before flattening');
  assert.ok(/ironCondorAutoTradeEnabledOverride: false/.test(flattenBlock),
    'flatten-all must also turn off ironCondorAutoTradeEnabledOverride');
  console.log('G3 PASS flatten-all pauses iron condor auto-trading along with the other three mechanisms');
};

// G4 -- closed iron condor trades are included in the shared aggregate
// (allClosedOptionsTrades), so Journal/Account-Growth totals are not
// silently missing a whole mechanism's history.
gates.G4 = () => {
  const src = `
    var backendOptionsClosedTrades = OPTIONS;
    var backendWeeklySpreadClosedTrades = SPREAD;
    var backendIronCondorClosedTrades = CONDOR;
    ${lift('allClosedOptionsTrades')}
    return allClosedOptionsTrades();
  `;
  const build = (o, s, c) => new Function('OPTIONS', 'SPREAD', 'CONDOR', src)(o, s, c);
  const result = build([], [], [{ underlyingSymbol: 'SPY', entryCredit: 1.2, exitCredit: 0.4, qty: 1 }]);
  assert.strictEqual(result.length, 1, 'a closed iron condor trade must appear in allClosedOptionsTrades()');
  assert.strictEqual(result[0].mechanismLabel, 'Iron Condor',
    'a closed iron condor trade must be tagged with its own mechanismLabel');
  console.log('G4 PASS allClosedOptionsTrades() includes ironCondorClosedTrades, tagged Iron Condor');
};

// G5 -- open positions table hides itself with nothing to show, same
// pattern as every other options card, and never fabricates a live P&L
// number the backend doesn't provide for an open condor.
gates.G5 = () => {
  const code = html.replace(/\/\/[^\n]*/g, '');
  assert.ok(/function renderIronCondorPositions\(\)/.test(code), 'renderIronCondorPositions must exist');
  const body = code.match(/function renderIronCondorPositions\(\)[\s\S]{0,2000}/)?.[0] || '';
  assert.ok(/if\(!open\.length\)\{ card\.hidden = true; return; \}/.test(body),
    'an account with no open iron condor positions must have the card hidden');
  assert.ok(!/P&L<\/th>|Current<\/th>/.test(body),
    'the iron condor table must not claim a live P&L/current-price column it cannot honestly fill');
  assert.ok(/escapeHtml\(p\.underlyingSymbol/.test(body), 'underlying symbol must be escaped');
  console.log('G5 PASS iron condor positions card hides when empty and never fabricates live P&L');
};

function main() {
  Object.keys(gates).sort().forEach((k) => gates[k]());
  console.log('\nAll iron condor UI gates passed.');
}

main();

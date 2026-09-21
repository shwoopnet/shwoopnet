'use strict';
// The Brief page's OTHER stat -- statCta's "N instruments you're tracking
// today" headline -- summed only equities + crypto and never referenced
// options positions at all, even though the lede paragraph right next to
// it already accounted for them (see briefHeadlineOptionsGates.test.js).
// A real open CSP/weekly-spread position was invisible to this stat.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name) {
  const start = html.indexOf('  function ' + name + '(');
  assert.notStrictEqual(start, -1, 'could not find function ' + name + ' in index.html');
  let depth = 0;
  const open = html.indexOf('{', start);
  for (let j = open; j < html.length; j++) {
    if (html[j] === '{') depth++;
    else if (html[j] === '}') { depth--; if (depth === 0) return html.slice(start, j + 1); }
  }
  throw new Error('unbalanced braces for ' + name);
}

function build({ optionsOpen, weeklySpreadOpen }) {
  const ctaStatEl = { textContent: '' };
  const src = `
    var document = {
      getElementById: function(id){ return id === 'ctaStat' ? CTA_STAT_EL : null; },
    };
    var journalEntries = [];
    function isOpenAlpacaPositionForCurrentAccount(){ return false; }
    var backendOptionsPositions = OPTIONS_OPEN;
    var backendWeeklySpreadPositions = WEEKLY_SPREAD_OPEN;
    ${lift('statCta')}
    return statCta;
  `;
  const statCta = new Function('CTA_STAT_EL', 'OPTIONS_OPEN', 'WEEKLY_SPREAD_OPEN', src)(
    ctaStatEl, optionsOpen, weeklySpreadOpen
  );
  return { statCta, ctaStatEl };
}

function main() {
  // ---- No options positions: stat unaffected, no options mention ----
  {
    const { statCta, ctaStatEl } = build({ optionsOpen: [], weeklySpreadOpen: [] });
    statCta([{ sym: 'PLTR' }], []);
    assert.ok(!/options/.test(ctaStatEl.textContent),
      'no open options positions must not add an options clause: got "' + ctaStatEl.textContent + '"');
    console.log('G1 PASS no options positions leaves the headline stat as equities/crypto only');
  }

  // ---- Real CSP + weekly-spread positions open: counted into total and breakdown ----
  {
    const { statCta, ctaStatEl } = build({ optionsOpen: [{}, {}], weeklySpreadOpen: [{}] });
    statCta([{ sym: 'PLTR' }], []);
    assert.ok(ctaStatEl.textContent.startsWith('4 instruments'),
      'total must include the 3 options positions: got "' + ctaStatEl.textContent + '"');
    assert.ok(ctaStatEl.textContent.includes('3 options'),
      'breakdown must mention 3 options: got "' + ctaStatEl.textContent + '"');
    assert.ok(ctaStatEl.textContent.includes('3 with open positions'),
      'open-position count must include all 3 options positions (equity has none open here): got "' + ctaStatEl.textContent + '"');
    console.log('G2 PASS open CSP + weekly-spread positions are counted into the headline stat');
  }

  console.log('\nAll statCta options gates passed.');
}

main();

'use strict';
// The Brief page's headline/lede told you about equities and crypto every
// day, but never mentioned options income (CSP/weekly credit spread)
// positions even when real ones were open -- an account running options
// alongside the other two strategies had no way to learn that from the
// Brief page at all. renderBriefHeadline now adds an options sentence to
// the lede whenever there's a real open options position, and stays
// silent (no "0 positions" filler) for an account that's never enabled
// either mechanism.

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

function fakeEl() { return { textContent: '' }; }

function build({ optionsOpen, weeklySpreadOpen }) {
  const headlineEl = fakeEl();
  const ledeEl = fakeEl();
  const src = `
    var document = {
      querySelector: function(sel){
        if(sel === '.brief-headline') return HEADLINE_EL;
        if(sel === '.brief-lede') return LEDE_EL;
        return null;
      },
    };
    // Fixed, fully-loaded market reads -- a quiet, flat day -- so the test
    // only has to reason about the new options sentence, not the
    // tone/index math this function also does.
    function indexReads(){
      return [
        { sym: 'SPY', chg: 0.05, loaded: true },
        { sym: 'QQQ', chg: 0.05, loaded: true },
        { sym: 'DIA', chg: 0.05, loaded: true },
      ];
    }
    function isUsMarketOpen(){ return true; }
    function getUsMarketSession(){ return { session: 'regular', label: 'Regular session' }; }
    function pct(a, b){ return (a - b) / b * 100; }
    function buildTradeFromPick(p){ return p; }
    var backendIntradayPicks = [];
    var intradayTrades = [{ sym: 'PLTR', direction: 'Long', analysisIsReal: true }];
    var cryptoWatchlist = [];
    var backendOptionsPositions = OPTIONS_OPEN;
    var backendWeeklySpreadPositions = WEEKLY_SPREAD_OPEN;
    var HEADLINE_EL_REF = HEADLINE_EL, LEDE_EL_REF = LEDE_EL;
    ${lift('renderBriefHeadline')}
    return renderBriefHeadline;
  `;
  const renderBriefHeadline = new Function('HEADLINE_EL', 'LEDE_EL', 'OPTIONS_OPEN', 'WEEKLY_SPREAD_OPEN', src)(
    headlineEl, ledeEl, optionsOpen, weeklySpreadOpen
  );
  return { renderBriefHeadline, ledeEl };
}

function main() {
  // ---- No options positions at all: no sentence, no "0 positions" filler ----
  {
    const { renderBriefHeadline, ledeEl } = build({ optionsOpen: [], weeklySpreadOpen: [] });
    renderBriefHeadline();
    assert.ok(!/[Oo]ptions/.test(ledeEl.textContent),
      'an account with no options positions must not see an options sentence at all: got "' + ledeEl.textContent + '"');
    console.log('G1 PASS no options positions means no options sentence, not a "0 positions" filler line');
  }

  // ---- Real CSP positions open: a sentence appears with the right count ----
  {
    const { renderBriefHeadline, ledeEl } = build({ optionsOpen: [{}, {}], weeklySpreadOpen: [] });
    renderBriefHeadline();
    assert.ok(ledeEl.textContent.includes('Options income has 2 positions open.'),
      'two open CSP positions must be reported in the lede: got "' + ledeEl.textContent + '"');
    console.log('G2 PASS open CSP positions are reported in the lede with the right count');
  }

  // ---- Both mechanisms combine into one count, singular wording at 1 ----
  {
    const { renderBriefHeadline, ledeEl } = build({ optionsOpen: [{}], weeklySpreadOpen: [{}] });
    renderBriefHeadline();
    assert.ok(ledeEl.textContent.includes('Options income has 2 positions open.'),
      'CSP and weekly-spread open counts must combine into one figure: got "' + ledeEl.textContent + '"');
    console.log('G3 PASS CSP and weekly-spread positions combine into one options figure');
  }

  console.log('\nAll Brief headline options gates passed.');
}

main();

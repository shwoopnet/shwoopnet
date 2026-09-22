'use strict';
// The Journal page used to carry a second, standalone "Options closed
// trades" table below the calendar. Removed as genuinely redundant, not
// just duplicated -- but that claim only holds if the calendar's own
// folding of closed options trades (day cell $, week cell $, and the
// day-detail list) actually works. These gates pin that it does, so a
// future change to computeDayStats/optionsClosedJournalRows can't quietly
// stop counting options P&L into the calendar with nothing left to notice.

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

// Confirms the standalone table's render function and its two element ids
// are actually gone, not just unreferenced -- the whole point of this
// change was one less thing on the page, not just one less call site.
function main() {
  assert.ok(!/function renderJournalOptionsClosedTrades/.test(html),
    'the standalone Options closed trades render function must be removed, not just unused');
  assert.ok(!/journalOptionsSection/.test(html) && !/journalOptionsBody/.test(html),
    'the standalone table\'s element ids must be gone from both the markup and the script');
  console.log('G1 PASS the standalone Options closed trades table is fully removed');

  const src = `
    ${lift('isWinningReturn')}
    ${lift('computePL')}
    ${lift('optionsClosedTradeDollarPL')}
    ${lift('allClosedOptionsTrades')}
    ${lift('optionsClosedJournalRows')}
    ${lift('realizedOnDate')}
    ${lift('filteredJournalEntries')}
    ${lift('computeDayStats')}
    return { computeDayStats, optionsClosedJournalRows };
  `;
  const build = (state) => new Function(
    'journalEntries', 'journalFilter', 'backendOptionsClosedTrades', 'backendWeeklySpreadClosedTrades', 'backendIronCondorClosedTrades',
    src
  )(state.journalEntries || [], state.journalFilter || 'all',
    state.backendOptionsClosedTrades || [], state.backendWeeklySpreadClosedTrades || [], state.backendIronCondorClosedTrades || []);

  // A day with ONLY a closed CSP trade (no journalEntries at all) must
  // still show up in the calendar's day $ figure -- this is exactly what
  // the standalone table used to be needed for before the folding existed.
  {
    const { computeDayStats } = build({
      backendOptionsClosedTrades: [{
        underlyingSymbol: 'SPY', entryCredit: 1.20, exitCredit: 0.40, qty: 2,
        closedAt: '2026-09-10T20:05:00Z', exitReason: 'expired',
      }],
    });
    const stats = computeDayStats('2026-09-10');
    assert.ok(stats, 'a day with only a closed options trade must not read as empty');
    assert.strictEqual(stats.dollar, (1.20 - 0.40) * 2 * 100, 'the day $ figure must include the options trade\'s real P&L');
    console.log('G2 PASS a closed CSP trade with no journalEntries still folds into its day\'s $ figure');
  }

  // A day mixing a real equities trade AND a closed weekly-spread trade
  // must sum both into one figure, not silently drop one side.
  {
    const { computeDayStats } = build({
      journalEntries: [{
        id: 'j1', sym: 'SOFI', status: 'closed', direction: 'Long',
        entry: 10, exit: 10.5, qty: 100, date: '2026-09-11', exitDate: '2026-09-11',
        screenerType: 'intraday',
      }],
      backendWeeklySpreadClosedTrades: [{
        underlyingSymbol: 'QQQ', entryCredit: 2.00, exitCredit: 0.10, qty: 1,
        closedAt: '2026-09-11T20:05:00Z', exitReason: 'target',
      }],
    });
    const stats = computeDayStats('2026-09-11');
    const equitiesDollar = (10.5 - 10) * 100;
    const optionsDollar = (2.00 - 0.10) * 1 * 100;
    assert.strictEqual(stats.dollar, equitiesDollar + optionsDollar,
      'a day with both a real trade and a closed options trade must sum both, not just one');
    assert.strictEqual(stats.symbols, 2, 'both trades must be counted toward the day\'s symbol/trade count');
    console.log('G3 PASS a mixed day sums the real trade and the closed options trade into one figure');
  }

  // Options only join the unified "All" view (see the source's own
  // comment) -- filtered to Equities only, a closed options
  // trade must not leak in and inflate a tab it doesn't belong to.
  {
    const { computeDayStats } = build({
      journalFilter: 'equities',
      backendOptionsClosedTrades: [{
        underlyingSymbol: 'SPY', entryCredit: 1.00, exitCredit: 0.50, qty: 1,
        closedAt: '2026-09-12T20:05:00Z', exitReason: 'expired',
      }],
    });
    assert.strictEqual(computeDayStats('2026-09-12'), null,
      'a closed options trade must not appear under the Equities-only filter tab');
    console.log('G4 PASS a closed options trade stays out of the Equities-only filtered view');
  }

  // realizedOnDate uses closedAt's date, not today -- an options trade
  // closed on one day must land on THAT day's cell even if the page is
  // rendered later.
  {
    const { computeDayStats } = build({
      backendOptionsClosedTrades: [{
        underlyingSymbol: 'SPY', entryCredit: 1.00, exitCredit: 0.50, qty: 1,
        closedAt: '2026-08-01T20:05:00Z', exitReason: 'expired',
      }],
    });
    assert.strictEqual(computeDayStats('2026-09-12'), null, 'a trade closed on a different day must not bleed into this one');
    assert.ok(computeDayStats('2026-08-01'), 'the trade must land on the day it actually closed');
    console.log('G5 PASS a closed options trade is dated by its own close, not by when the page happens to render');
  }

  // The "Options" filter tab (added alongside All/Equities): the
  // reverse of G4 -- under journalFilter 'options', a closed options
  // trade must show, and a real equities journal entry must NOT
  // leak in (filteredJournalEntries returns [] for 'options').
  {
    const { computeDayStats } = build({
      journalFilter: 'options',
      journalEntries: [{
        id: 'j1', sym: 'SOFI', status: 'closed', direction: 'Long',
        entry: 10, exit: 10.5, qty: 100, date: '2026-09-13', exitDate: '2026-09-13',
        screenerType: 'intraday',
      }],
      backendOptionsClosedTrades: [{
        underlyingSymbol: 'SPY', entryCredit: 1.00, exitCredit: 0.50, qty: 1,
        closedAt: '2026-09-13T20:05:00Z', exitReason: 'expired',
      }],
    });
    const optionsDollar = (1.00 - 0.50) * 1 * 100;
    assert.strictEqual(computeDayStats('2026-09-13').dollar, optionsDollar,
      'the Options tab must show only the closed options trade\'s $, not the equities trade on the same day');
    console.log('G6 PASS the Options filter tab shows closed options trades and excludes equities journal entries');
  }

  console.log('\nAll Journal calendar options-folding gates passed.');
}

main();

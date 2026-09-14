'use strict';
// The Journal page's filter row (All/Equities/Crypto/Options) only shows
// itself when there's actually more than one category to switch between --
// and the Options tab specifically stays hidden for an account that's
// never closed one, since CSP/weekly spread are off by default and an
// always-empty tab is clutter, not a feature.

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

function fakeBtn() {
  return { hidden: false, textContent: '', dataset: {}, classList: { active: false, toggle(cls, on){ this.active = on; } } };
}

function build(state) {
  const els = {
    journalFilterRow: { hidden: false },
    journalFilterAll: Object.assign(fakeBtn(), { dataset: { filter: 'all' } }),
    journalFilterEquities: Object.assign(fakeBtn(), { dataset: { filter: 'equities' } }),
    journalFilterCrypto: Object.assign(fakeBtn(), { dataset: { filter: 'crypto' } }),
    journalFilterOptions: Object.assign(fakeBtn(), { dataset: { filter: 'options' } }),
  };
  const src = `
    var journalEntries = JOURNAL_ENTRIES;
    var journalFilter = JOURNAL_FILTER;
    var backendOptionsClosedTrades = OPTIONS_CLOSED;
    var backendWeeklySpreadClosedTrades = SPREAD_CLOSED;
    var document = { getElementById: function(id){ return ELS[id] || null; } };
    ${lift('isWinningReturn')}
    ${lift('computePL')}
    ${lift('optionsClosedTradeDollarPL')}
    ${lift('allClosedOptionsTrades')}
    ${lift('optionsClosedJournalRows')}
    ${lift('updateJournalFilterTabs')}
    return { updateJournalFilterTabs: updateJournalFilterTabs, getJournalFilter: function(){ return journalFilter; } };
  `;
  const holder = { journalFilter: state.journalFilter || 'all' };
  const mod = new Function('JOURNAL_ENTRIES', 'JOURNAL_FILTER', 'OPTIONS_CLOSED', 'SPREAD_CLOSED', 'ELS', src)(
    state.journalEntries || [], holder.journalFilter, state.backendOptionsClosedTrades || [], state.backendWeeklySpreadClosedTrades || [], els
  );
  return { mod, els };
}

function main() {
  // ---- Only equities: no filter row, no Options tab ----
  {
    const { mod, els } = build({
      journalEntries: [{ sym: 'PLTR', status: 'closed', screenerType: 'intraday' }],
    });
    mod.updateJournalFilterTabs();
    assert.strictEqual(els.journalFilterRow.hidden, true, 'a single category (equities only) must not show the filter row at all');
    console.log('G1 PASS a single-category journal hides the whole filter row');
  }

  // ---- Equities + crypto, no options: row shows, Options tab stays hidden ----
  {
    const { mod, els } = build({
      journalEntries: [
        { sym: 'PLTR', status: 'closed', screenerType: 'intraday' },
        { sym: 'BTC/USD', status: 'closed', screenerType: 'crypto' },
      ],
    });
    mod.updateJournalFilterTabs();
    assert.strictEqual(els.journalFilterRow.hidden, false, 'two categories must show the filter row');
    assert.strictEqual(els.journalFilterOptions.hidden, true, 'an account with no closed options trades must not show the Options tab');
    console.log('G2 PASS equities+crypto shows the row but keeps the empty Options tab hidden');
  }

  // ---- Equities + options (no crypto): row shows, Options tab shows with a real count ----
  {
    const { mod, els } = build({
      journalEntries: [{ sym: 'PLTR', status: 'closed', screenerType: 'intraday' }],
      backendOptionsClosedTrades: [{
        underlyingSymbol: 'SPY', entryCredit: 1.00, exitCredit: 0.50, qty: 1,
        closedAt: '2026-09-13T20:05:00Z', exitReason: 'expired',
      }],
    });
    mod.updateJournalFilterTabs();
    assert.strictEqual(els.journalFilterRow.hidden, false, 'equities + options (even with zero crypto) must show the filter row');
    assert.strictEqual(els.journalFilterOptions.hidden, false, 'a real closed options trade must show the Options tab');
    assert.strictEqual(els.journalFilterOptions.textContent, 'Options (1)', 'the tab must show the real closed-options count');
    console.log('G3 PASS a real closed options trade shows its own tab with an accurate count, even with no crypto trades');
  }

  console.log('\nAll Journal filter-tabs gates passed.');
}

main();

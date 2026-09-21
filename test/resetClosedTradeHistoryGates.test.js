'use strict';
// resetClosedTradeHistory (window.__shwoopAPI, index.html) -- the
// deliberately narrow "start fresh against a different broker account"
// action. It must remove every CLOSED journal entry and both options
// closed-trade arrays outright, while leaving anything still 'open'
// completely untouched (a stale open entry has its own "needs review" +
// individual Remove flow; this action has no business guessing at it).

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

// Object-literal methods (name: function(...){...}) aren't found by the
// "function name(" lift pattern the rest of this suite uses for top-level
// functions, so this extracts by the "name: function(" shape instead.
function liftMethod(name) {
  const marker = name + ': function(';
  const start = html.indexOf(marker);
  assert.notStrictEqual(start, -1, 'could not find method ' + name + ' in index.html');
  const fnStart = start + name.length + 2; // position of "function("
  let depth = 0;
  const open = html.indexOf('{', fnStart);
  for (let j = open; j < html.length; j++) {
    if (html[j] === '{') depth++;
    else if (html[j] === '}') { depth--; if (depth === 0) return html.slice(fnStart, j + 1); }
  }
  throw new Error('unbalanced braces for ' + name);
}

// Minimal fakes of the modular Firebase SDK surface this method uses --
// doc(db, 'users', uid) returns a ref; runTransaction(db, cb) hands cb a
// transaction whose .get(ref) resolves a snapshot and whose .set(ref,
// data, opts) merges into the fake store.
function buildFakeFirestore(initialDoc) {
  let stored = { ...initialDoc };
  const ref = { path: 'users/uid' };
  const db = {};
  function doc() { return ref; }
  function runTransaction(_db, cb) {
    const snap = { exists: () => true, data: () => ({ ...stored }) };
    const t = {
      get: () => Promise.resolve(snap),
      set: (_ref, data) => { stored = { ...stored, ...data }; },
    };
    return Promise.resolve(cb(t));
  }
  return { db, doc, runTransaction, getStored: () => stored };
}

function build(initialDoc) {
  const { db, doc, runTransaction, getStored } = buildFakeFirestore(initialDoc);
  const src = `
    var db = FAKE_DB, doc = FAKE_DOC, runTransaction = FAKE_RUN_TRANSACTION;
    return (${liftMethod('resetClosedTradeHistory')});
  `;
  const resetClosedTradeHistory = new Function('FAKE_DB', 'FAKE_DOC', 'FAKE_RUN_TRANSACTION', src)(db, doc, runTransaction);
  return { resetClosedTradeHistory, getStored };
}

function main() {
  // ---- Closed journal entries are removed, open ones are untouched ----
  {
    const { resetClosedTradeHistory, getStored } = build({
      journalEntries: [
        { id: 'a', sym: 'PLTR', status: 'closed' },
        { id: 'b', sym: 'SOFI', status: 'open' },
        { id: 'c', sym: 'ROKU', status: 'closed' },
      ],
      optionsClosedTrades: [{ underlyingSymbol: 'NOK' }],
      weeklySpreadClosedTrades: [{ underlyingSymbol: 'INTC' }],
    });
    return resetClosedTradeHistory('uid').then(function(){
      const stored = getStored();
      assert.deepStrictEqual(stored.journalEntries.map((j) => j.id), ['b'],
        'only the open entry must survive: got ' + JSON.stringify(stored.journalEntries));
      assert.deepStrictEqual(stored.optionsClosedTrades, [], 'optionsClosedTrades must be cleared outright');
      assert.deepStrictEqual(stored.weeklySpreadClosedTrades, [], 'weeklySpreadClosedTrades must be cleared outright');
      console.log('G1 PASS closed journal entries and both options closed-trade arrays are cleared; open entries survive untouched');
    });
  }
}

Promise.resolve(main()).then(() => {
  console.log('\nAll resetClosedTradeHistory gates passed.');
}).catch((err) => {
  console.error('TEST FAILURE:', err.message);
  console.error(err.stack);
  process.exit(1);
});

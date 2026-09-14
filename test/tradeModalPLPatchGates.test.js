'use strict';
// The trade detail modal's own P/L cell used to be a STATIC snapshot
// computed once at open time from this tab's own local quote poll --
// if that poll hadn't resolved for this symbol yet, the cell showed an
// honest "--" and then simply stayed that way forever, even once a real
// price and a real P/L both existed. Reported live: "still not fixed"
// after the Setups row's own P/L cell got this same two-phase patch
// treatment (see plPatchGenRaceGates.test.js) -- the modal's cell was
// never wired into it at all. patchTradeModalPL closes that gap.

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
function liftVar(name) {
  const start = html.indexOf('  var ' + name + ' = ');
  assert.notStrictEqual(start, -1, 'could not find var ' + name);
  const semi = html.indexOf(';', start);
  return html.slice(start, semi + 1);
}

function build(journalEntries, positions) {
  const cell = { className: '', textContent: '—' };
  const src = `
    var journalEntries = JOURNAL_ENTRIES;
    var tradeModalOpenToken = 1;
    var document = { getElementById: function(id){ return id === 'tradeModalPL' ? CELL : null; } };
    function isOpenAlpacaPositionForCurrentAccount(j){ return j.status === 'open' && j.source === 'alpaca'; }
    function canonicalSymbol(sym){ return (sym || '').replace(/\\//g, ''); }
    function alpacaPositionsBySymbol(positions){
      var bySym = {};
      (positions || []).forEach(function(p){ bySym[canonicalSymbol(p.symbol)] = p; });
      return bySym;
    }
    function getAlpacaPositionsCached(){ return Promise.resolve(POSITIONS); }
    ${liftVar('TRADE_MODAL_PL_ID')}
    ${lift('patchTradeModalPL')}
    return { patchTradeModalPL: patchTradeModalPL, setToken: function(t){ tradeModalOpenToken = t; } };
  `;
  const mod = new Function('JOURNAL_ENTRIES', 'CELL', 'POSITIONS', src)(journalEntries, cell, positions);
  return { mod, cell };
}

async function main() {
  // ---- A real open position patches the cell from Alpaca's own P/L ----
  {
    const { mod, cell } = build(
      [{ sym: 'COIN', status: 'open', source: 'alpaca' }],
      [{ symbol: 'COIN', unrealized_pl: '42.50', unrealized_plpc: '0.0425' }]
    );
    mod.patchTradeModalPL('COIN', 1);
    await new Promise((r) => setTimeout(r, 0));
    assert.strictEqual(cell.textContent, '+$42.50 (+4.25%)', 'a real open position must patch the modal\'s P/L cell with Alpaca\'s own figure');
    assert.ok(cell.className.includes('up'), 'a positive P/L must carry the up class');
    console.log('G1 PASS a real open position patches the modal\'s P/L cell from Alpaca');
  }

  // ---- No open position for this symbol: cell is left untouched ----
  {
    const { mod, cell } = build([], []);
    mod.patchTradeModalPL('PLTR', 1);
    await new Promise((r) => setTimeout(r, 0));
    assert.strictEqual(cell.textContent, '—', 'a symbol with no open position must never fabricate a P/L');
    console.log('G2 PASS no open position leaves the cell alone');
  }

  // ---- The modal moved on to a different trade before the fetch resolved: dropped, not applied ----
  {
    const { mod, cell } = build(
      [{ sym: 'COIN', status: 'open', source: 'alpaca' }],
      [{ symbol: 'COIN', unrealized_pl: '42.50', unrealized_plpc: '0.0425' }]
    );
    mod.patchTradeModalPL('COIN', 1);
    mod.setToken(2); // modal closed/moved to another trade before the fetch above resolves
    await new Promise((r) => setTimeout(r, 0));
    assert.strictEqual(cell.textContent, '—', 'a resolve after the modal moved on must not paint into it');
    console.log('G3 PASS a stale patch (modal already moved to another trade) is dropped, never applied');
  }

  console.log('\nAll trade modal P/L patch gates passed.');
}

main();

'use strict';
// Today's Setups P/L cells are first painted synchronously from this tab's
// own local quote poll, then patched to the authoritative Alpaca
// unrealized_pl/unrealized_plpc figure by patchIntradayPLWithAlpacaPositions
// once getAlpacaPositionsCached() resolves -- see its own comment in
// index.html. This gate pins that a slow, stale response landing after a
// newer render already happened does not clobber that newer render's own
// patch (the generation counter's whole purpose).

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

function build(journalEntries, positionsQueue) {
  const cells = {};
  function cellFor(sym) {
    if (!cells['pl-' + sym]) cells['pl-' + sym] = { textContent: '—', className: '' };
    return cells['pl-' + sym];
  }
  const src = `
    var journalEntries = JOURNAL_ENTRIES;
    var document = {
      getElementById: function(id){
        if(id.indexOf('pl-') === 0) return CELL_FOR(id.slice(3));
        return null; // cur-<sym> placeholders intentionally absent -- not under test here
      },
      querySelector: function(){ return null; },
    };
    function isOpenAlpacaPositionForCurrentAccount(j){ return j.status === 'open'; }
    function canonicalSymbol(sym){ return (sym || '').replace(/\\//g, ''); }
    function alpacaPositionsBySymbol(positions){
      var bySym = {};
      (positions || []).forEach(function(p){ bySym[canonicalSymbol(p.symbol)] = p; });
      return bySym;
    }
    function computeTradeProgress(){ return { progressPct: 0, barColor: '' }; }
    var positionsQueue = POSITIONS_QUEUE;
    function getAlpacaPositionsCached(){
      return new Promise(function(resolve){ RESOLVE_NEXT.push(function(){ resolve(positionsQueue.shift()); }); });
    }
    ${liftVar('intradayPLPatchGen')}
    ${lift('patchIntradayPLWithAlpacaPositions')}
    return {
      patch: patchIntradayPLWithAlpacaPositions,
      flush: function(){ var fns = RESOLVE_NEXT; RESOLVE_NEXT = []; fns.forEach(function(fn){ fn(); }); },
    };
  `;
  const mod = new Function('JOURNAL_ENTRIES', 'CELL_FOR', 'POSITIONS_QUEUE', 'RESOLVE_NEXT', src)(
    journalEntries, cellFor, positionsQueue.slice(), []
  );
  return { mod, cells };
}

async function main() {
  const journalEntries = [
    { sym: 'PLTR', status: 'open', source: 'alpaca' },
  ];

  // Two snapshots: an earlier, slower call's fetch resolves SECOND (after
  // a newer call already started and completed), so its stale write must
  // be discarded rather than clobbering the newer render's own patch.
  const positionsQueue = [
    [
      { symbol: 'PLTR', unrealized_pl: '10.00', unrealized_plpc: '0.01', current_price: '20' },
    ],
    [
      { symbol: 'PLTR', unrealized_pl: '11.00', unrealized_plpc: '0.011', current_price: '20.1' },
    ],
  ];

  const { mod, cells } = build(journalEntries, positionsQueue);

  // Simulates the race: an older call's fetch is still pending when a
  // newer call starts and bumps the generation counter, then the older
  // call's fetch resolves. Its stale write must not land.
  mod.patch('equities'); // older call, fetch pending
  mod.patch('equities'); // newer call, bumps the counter
  mod.flush(); // resolves both in-flight fetches, in call order: newer's queued-first, older's queued-second

  await new Promise((r) => setTimeout(r, 0));
  await new Promise((r) => setTimeout(r, 0));

  assert.strictEqual(cells['pl-PLTR'].textContent, '+$11.00 (+1.10%)',
    'the newer call\'s write must win; a stale response from a superseded call must not overwrite it');
  console.log('G1 PASS a stale, slow patch response cannot clobber a newer render\'s own write');
  console.log('\nAll P/L patch generation-race gates passed.');
}

main().catch((err) => { console.error(err); process.exit(1); });

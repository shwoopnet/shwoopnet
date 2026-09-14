'use strict';
// Today's Setups P/L cells are first painted synchronously from this tab's
// own local quote poll, then patched to the authoritative Alpaca
// unrealized_pl/unrealized_plpc figure by patchIntradayPLWithAlpacaPositions
// once getAlpacaPositionsCached() resolves -- see its own comment in
// index.html. That function used to share ONE generation counter between
// renderIntradayBlocks (equities) and renderCryptoBlocks (crypto), which
// independently call it on their own quote-poll cadence. An equities call
// firing while a crypto call's fetch was still in flight would bump the
// shared counter and silently discard the crypto call's own write when it
// resolved -- leaving that card stuck on the "—" first-paint placeholder
// even though real P/L data existed. This gate pins that the two domains
// now use independent counters and can't cancel each other out.

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
    { sym: 'BTC/USD', status: 'open', source: 'alpaca' },
  ];

  // Two positions snapshots: the crypto call's fetch will resolve against
  // the FIRST (queued first), the equities call's against the SECOND.
  // The second (equities) snapshot deliberately omits BTC/USD -- a real
  // getAlpacaPositionsCached() call always returns every position
  // regardless of who called it, but omitting it here is what makes this
  // test actually distinguish "the crypto call's own write landed" from
  // "some LATER call happened to carry the same figure and masked the
  // bug" (an earlier draft of this test used the same P/L on both
  // snapshots and kept passing even with the old shared-counter code,
  // because the later equities call's write papered over the discarded
  // crypto write with an identical number).
  const positionsQueue = [
    [
      { symbol: 'PLTR', unrealized_pl: '10.00', unrealized_plpc: '0.01', current_price: '20' },
      { symbol: 'BTC/USD', unrealized_pl: '5.00', unrealized_plpc: '0.02', current_price: '50000' },
    ],
    [
      { symbol: 'PLTR', unrealized_pl: '11.00', unrealized_plpc: '0.011', current_price: '20.1' },
    ],
  ];

  const { mod, cells } = build(journalEntries, positionsQueue);

  // Simulates the exact race: crypto's patch call starts (its fetch now
  // pending), THEN equities' patch call starts and bumps what used to be
  // a SHARED counter, THEN crypto's fetch resolves.
  mod.patch('crypto');
  mod.patch('equities');
  mod.flush(); // resolves both in-flight fetches, in call order

  await new Promise((r) => setTimeout(r, 0));
  await new Promise((r) => setTimeout(r, 0));

  assert.strictEqual(cells['pl-BTC/USD'].textContent, '+$5.00 (+2.00%)',
    'the crypto call\'s own write must not be discarded just because an equities call ran concurrently');
  assert.strictEqual(cells['pl-PLTR'].textContent, '+$11.00 (+1.10%)',
    'the equities call must still apply its own (later) fetch normally');
  console.log('G1 PASS a concurrent crypto + equities patch call no longer cancels either domain\'s write');
  console.log('\nAll P/L patch generation-race gates passed.');
}

main().catch((err) => { console.error(err); process.exit(1); });

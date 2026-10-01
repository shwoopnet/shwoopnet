'use strict';
// chartStates used to be cleared only by renderChartError, and only on a
// fetch failure -- every other symbol switch (or modal close) left its
// entry sitting there forever. openTradeModal/closeTradeModal now clean up
// the OLD symbol's entry on a genuine switch or on close, but must leave a
// SAME-symbol re-render (e.g. a quote poll re-opening the same trade) alone
// -- that's the entire reason chartStates exists, to carry zoom/pan across
// those re-renders. These gates lift openTradeModal/closeTradeModal and
// chartStates together and drive exactly those three cases.

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

function stubEl(){
  return {
    innerHTML: '', textContent: '', hidden: false,
    setAttribute(){}, removeAttribute(){},
    classList: { add(){}, remove(){} },
  };
}

function build() {
  const els = {};
  ['tradeModalSymCell','tradeModalPrices','tradeModalNotes','tradeModalPlayedOutCol',
   'tradeModalPlayedOut','tradeModalChartCol','tradeModalChartStatus',
   'tradeModalClose'].forEach(function(id){ els[id] = stubEl(); });
  els.tradeModalClose.addEventListener = function(){};

  var clonedSvgs = [];
  function makeSvg(){
    var listeners = {};
    var node = {
      id: '', dataset: {}, style: {}, classList: { add(){}, remove(){} },
      parentNode: { replaceChild: function(newNode){ node.replacedWith = newNode; } },
      addEventListener(type, fn){ listeners[type] = fn; },
      getBoundingClientRect(){ return { left: 0, top: 0, width: 760, height: 240 }; },
      viewBox: { baseVal: { x: 0, y: 0, width: 760, height: 580 } },
      setPointerCapture(){}, releasePointerCapture(){},
      querySelectorAll: () => [],
      appendChild(){},
      querySelector: function(){ return node; }, // chartCol.querySelector('svg')
    };
    node.cloneNode = function(){
      var clone = makeSvg();
      clonedSvgs.push(clone);
      return clone;
    };
    return node;
  }
  var liveSvg = makeSvg();
  els.tradeModalChartCol.querySelector = function(){ return liveSvg; };

  const renderCalls = [];
  const setupCalls = [];

  const src = `
    var TRADE_MODAL_PL_ID = 'tradeModalPL';
    var tradeModalBackdrop = { removeAttribute(){}, setAttribute(){}, addEventListener(){} };
    var tradeModalEl = { removeAttribute(){}, setAttribute(){} };
    function symbolBadgeHtml(){ return ''; }
    function escapeHtml(s){ return s; }
    function fmt(n){ return String(n); }
    function tradeModalPriceCell(){ return ''; }
    function renderChartInto(svg, sym){ RENDER_CALLS.push(sym); }
    function setupChartInteractivity(sym){ SETUP_CALLS.push(sym); }
    function patchTradeModalPL(){}
    function fetchHistoricalRangeBars(){ return new Promise(function(){}); } // never resolves -- not exercised here
    function setupHistoricalChartInteractivity(){}
    var document = {
      getElementById: function(id){ return ELS[id] || null; },
    };
    ${liftVar('chartStates')}
    var tradeModalOpenToken = 0;
    var tradeModalChartSym = null;
    ${lift('openTradeModal')}
    ${lift('closeTradeModal')}
    return {
      openTradeModal: openTradeModal,
      closeTradeModal: closeTradeModal,
      getChartStates: function(){ return chartStates; },
      seedChartState: function(sym, val){ chartStates[sym] = val; },
    };
  `;
  const mod = new Function('ELS', 'RENDER_CALLS', 'SETUP_CALLS', src)(els, renderCalls, setupCalls);
  return { mod };
}

function liveDescriptor(sym){
  return { sym: sym, chart: { kind: 'live', tf: '5m', basePrice: 100 } };
}

function main() {
  // ---- Opening a DIFFERENT symbol's live chart drops the old symbol's entry ----
  {
    const { mod } = build();
    mod.openTradeModal(liveDescriptor('AAPL'));
    mod.seedChartState('AAPL', { viewStart: 5, viewEnd: 20 }); // simulate a real render having populated it
    mod.openTradeModal(liveDescriptor('MSFT'));
    assert.strictEqual(mod.getChartStates().AAPL, undefined,
      'switching the modal to a different symbol must drop the old symbol\'s chartStates entry');
    console.log('G1 PASS opening a different symbol drops the previous symbol\'s chartStates entry');
  }

  // ---- Re-opening the SAME symbol (e.g. a quote-poll re-render) must NOT clear it ----
  {
    const { mod } = build();
    mod.openTradeModal(liveDescriptor('AAPL'));
    mod.seedChartState('AAPL', { viewStart: 5, viewEnd: 20 });
    mod.openTradeModal(liveDescriptor('AAPL')); // same symbol, simulating a re-render
    assert.deepStrictEqual(mod.getChartStates().AAPL, { viewStart: 5, viewEnd: 20 },
      'a same-symbol re-render must leave its chartStates entry (zoom/pan) untouched');
    console.log('G2 PASS re-opening the same symbol leaves its chartStates entry alone');
  }

  // ---- Closing the modal drops the open symbol's entry ----
  {
    const { mod } = build();
    mod.openTradeModal(liveDescriptor('AAPL'));
    mod.seedChartState('AAPL', { viewStart: 5, viewEnd: 20 });
    mod.closeTradeModal();
    assert.strictEqual(mod.getChartStates().AAPL, undefined,
      'closing the modal must drop whatever symbol\'s chartStates entry it was holding');
    console.log('G3 PASS closing the modal drops the current symbol\'s chartStates entry');
  }

  // ---- Switching to a 'none'/non-live chart also drops the old live entry ----
  {
    const { mod } = build();
    mod.openTradeModal(liveDescriptor('AAPL'));
    mod.seedChartState('AAPL', { viewStart: 5, viewEnd: 20 });
    mod.openTradeModal({ sym: 'SPY-OPT', chart: { kind: 'none' } });
    assert.strictEqual(mod.getChartStates().AAPL, undefined,
      'switching away to a non-live chart for a different trade must still drop the old live symbol\'s entry');
    console.log('G4 PASS switching to a non-live chart for a different trade drops the old entry');
  }

  console.log('\nAll trade modal chartStates cleanup gates passed.');
}

main();

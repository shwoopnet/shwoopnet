'use strict';
// The trade detail modal replaced the old inline chevron-expand for
// Setups AND gave Journal day-detail rows a chart/notes view they never
// had before. These gates pin the parts most likely to silently break:
// price-cell rendering (never a fabricated $0), the historical-chart
// timeframe/window chosen for a closed trade, and the stale-fetch guard
// that stops a slow historical fetch from painting into a modal that has
// since moved on to a different trade.

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

function fakeNode(id) {
  const node = {
    id: id || '',
    innerHTML: '',
    hidden: false,
    dataset: {},
    classList: { add(){}, remove(){}, toggle(){}, contains(){ return false; } },
    setAttribute(name, v){ if(name === 'hidden') node.hidden = true; },
    removeAttribute(name){ if(name === 'hidden') node.hidden = false; },
    hasAttribute(name){ return name === 'hidden' ? node.hidden : false; },
    addEventListener(){},
    cloneNode(){ return fakeNode(node.id); },
    parentNode: { replaceChild(newNode){ return newNode; } },
  };
  return node;
}

function build(overrides) {
  const els = {};
  ['tradeModalSymCell', 'tradeModalPrices', 'tradeModalNotes', 'tradeModalChartCol', 'tradeModalChart', 'tradeModalChartStatus']
    .forEach((id) => { els[id] = fakeNode(id); });

  const calls = { renderChartInto: [], setupChartInteractivity: [], drawCandles: [], fetchHistoricalRangeBars: [] };
  const fetchImpl = overrides.fetchHistoricalRangeBars || (() => Promise.resolve({ data: [{ o:1,h:1,l:1,c:1,vol:1,t:new Date() }], tf: '5m' }));

  const src = `
    var tradeModalOpenToken = 0;
    var tradeModalBackdrop = FAKE_BACKDROP;
    var tradeModalEl = FAKE_MODAL_EL;
    var document = { getElementById: function(id){ return ELS[id] || null; } };
    function renderChartInto(svg, sym, base, tf){ CALLS.renderChartInto.push({sym: sym, base: base, tf: tf}); }
    function setupChartInteractivity(sym){ CALLS.setupChartInteractivity.push(sym); }
    function drawCandles(svg, data, scale, factor, tf, opts){ CALLS.drawCandles.push({data: data, tf: tf, opts: opts}); }
    function fetchHistoricalRangeBars(sym, isCrypto, entryTime, exitTime){
      CALLS.fetchHistoricalRangeBars.push({sym: sym, isCrypto: isCrypto, entryTime: entryTime, exitTime: exitTime});
      return FETCH_IMPL(sym, isCrypto, entryTime, exitTime);
    }
    ${liftVar('SYMBOL_BADGE_COLORS')}
    ${lift('symbolBadgeColor')}
    ${lift('symbolBadgeHtml')}
    ${lift('escapeHtml')}
    ${lift('fmt')}
    ${lift('tradeModalPriceCell')}
    ${lift('openTradeModal')}
    ${lift('closeTradeModal')}
    return { openTradeModal: openTradeModal, closeTradeModal: closeTradeModal };
  `;
  const mod = new Function('FAKE_BACKDROP', 'FAKE_MODAL_EL', 'ELS', 'CALLS', 'FETCH_IMPL', src)(
    fakeNode('tradeModalBackdrop'), fakeNode('tradeModal'), els, calls, fetchImpl
  );
  return { mod: mod, els: els, calls: calls };
}

function main() {
  // ---- Live descriptor: prices, notes, and interactivity wiring ----
  {
    const { mod, els, calls } = build({});
    mod.openTradeModal({
      sym: 'SOFI', direction: 'Long', status: 'Active', statusCls: 'active',
      entry: 10, stop: 9.5, target: 11, pl: { dollar: 42.5, pct: 4.25 },
      notes: ['Opening range broke above $10.'],
      chart: { kind: 'live', isCrypto: false, tf: '1D', basePrice: 10.4 },
    });
    assert.ok(els.tradeModalSymCell.innerHTML.includes('SOFI'), 'symbol must appear in the modal header');
    assert.ok(els.tradeModalPrices.innerHTML.includes('9.50'), 'stop must appear in the price row');
    assert.ok(els.tradeModalPrices.innerHTML.includes('+$42.50'), 'a real P/L must render, not a placeholder');
    assert.ok(els.tradeModalNotes.innerHTML.includes('Opening range broke above'), 'notes must render');
    assert.strictEqual(calls.renderChartInto.length, 1, 'a live descriptor must render a live chart');
    assert.strictEqual(calls.renderChartInto[0].sym, 'SOFI');
    assert.strictEqual(calls.setupChartInteractivity.length, 1, 'a live chart must get zoom/pan interactivity wired');
    assert.strictEqual(calls.fetchHistoricalRangeBars.length, 0, 'a live descriptor must never trigger a historical fetch');
    console.log('G1 PASS a live trade renders its prices/notes and wires an interactive chart, no historical fetch');
  }

  // ---- Missing P/L renders an honest dash, never a fabricated $0 ----
  {
    const { mod, els } = build({});
    mod.openTradeModal({
      sym: 'AAPL', direction: 'Long', status: 'Watching', statusCls: 'watching',
      entry: 190, stop: null, target: null, pl: null, notes: [],
      chart: { kind: 'none' },
    });
    assert.ok(els.tradeModalPrices.innerHTML.includes('—'), 'a null P/L must render as a dash, not $0.00');
    assert.ok(!/\$0\.00/.test(els.tradeModalPrices.innerHTML), 'must never fabricate a $0 P/L');
    assert.ok(els.tradeModalChartCol.hidden, 'chart:"none" must hide the chart column (e.g. an options trade with no share price)');
    assert.ok(els.tradeModalNotes.innerHTML.includes('No recorded reasoning'), 'an empty notes list must say so, not render blank');
    console.log('G2 PASS a missing P/L is an honest dash and chart:"none" hides the chart column');
  }

  // ---- Historical chart: a closed trade fetches its OWN window, draws once resolved ----
  {
    const entryTime = new Date('2026-09-08T14:35:00Z');
    const exitTime = new Date('2026-09-08T18:00:00Z');
    let resolveFetch;
    const pending = new Promise((r) => { resolveFetch = r; });
    const { mod, calls } = build({ fetchHistoricalRangeBars: () => pending });
    mod.openTradeModal({
      sym: 'MARA', direction: 'Long', status: 'Closed', statusCls: 'watching',
      entry: 18.40, stop: 17.80, target: 19.30, pl: { dollar: -30, pct: -1.6 }, notes: [],
      chart: { kind: 'historical', isCrypto: false, entryTime: entryTime, exitTime: exitTime },
    });
    assert.strictEqual(calls.fetchHistoricalRangeBars.length, 1, 'a closed trade must fetch its own historical window');
    assert.strictEqual(calls.fetchHistoricalRangeBars[0].entryTime.getTime(), entryTime.getTime());
    assert.strictEqual(calls.fetchHistoricalRangeBars[0].exitTime.getTime(), exitTime.getTime());
    assert.strictEqual(calls.drawCandles.length, 0, 'must not draw before the historical fetch resolves');
    resolveFetch({ data: [{ o:18,h:19,l:17,c:18.4,vol:100,t: entryTime }], tf: '5m' });
    return pending.then(() => new Promise((r) => setImmediate(r))).then(() => {
      assert.strictEqual(calls.drawCandles.length, 1, 'the historical chart must draw once its fetch resolves');
      assert.strictEqual(calls.drawCandles[0].opts.levels.entry, 18.40, 'the original entry must still be drawn as a reference line on a closed trade');
      console.log('G3 PASS a closed trade fetches and draws its own historical window, entry/stop/target lines intact');

      // ---- Stale-fetch guard: opening a DIFFERENT trade before the first
      // historical fetch resolves must not let the first one paint late ----
      let resolveFirst;
      const firstPending = new Promise((r) => { resolveFirst = r; });
      const mod3Build = build({ fetchHistoricalRangeBars: () => firstPending });
      mod3Build.mod.openTradeModal({
        sym: 'RIOT', direction: 'Long', status: 'Closed', statusCls: 'watching',
        entry: 10, stop: 9, target: 12, pl: null, notes: [],
        chart: { kind: 'historical', isCrypto: false, entryTime: new Date('2026-09-01T14:00:00Z'), exitTime: new Date('2026-09-01T18:00:00Z') },
      });
      // A second trade opens before the first's fetch resolves.
      mod3Build.mod.openTradeModal({
        sym: 'COIN', direction: 'Long', status: 'Active', statusCls: 'active',
        entry: 200, stop: 190, target: 220, pl: null, notes: [],
        chart: { kind: 'live', isCrypto: false, tf: '1D', basePrice: 205 },
      });
      resolveFirst({ data: [{ o:1,h:1,l:1,c:1,vol:1,t:new Date() }], tf: '5m' });
      return firstPending.then(() => new Promise((r) => setImmediate(r))).then(() => {
        assert.strictEqual(mod3Build.calls.drawCandles.length, 0,
          'a historical fetch resolving after the modal moved to a different trade must not draw at all');
        console.log('G4 PASS a stale historical fetch (modal already moved to another trade) is dropped, never drawn');
        console.log('\nAll trade detail modal gates passed.');
      });
    });
  }
}

main().catch((err) => { console.error(err); process.exit(1); });

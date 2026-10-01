'use strict';
// None of the chart systems re-rendered on a window resize, so proportions
// (particularly the growth chart, which lays itself out in JS off a fixed
// W/H rather than relying purely on SVG scaling) could go stale across a
// viewport/breakpoint change. A debounced window resize listener now
// re-runs whichever chart is actually on screen -- the trade modal's live
// or historical chart, or the growth chart -- against data already on
// hand, never a re-fetch. These gates lift that listener (registered
// top-level, not inside a named function) by its own `window.addEventListener('resize'`
// call site and drive it with a fake timer.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function liftVar(name) {
  const start = html.indexOf('  var ' + name + ' = ');
  assert.notStrictEqual(start, -1, 'could not find var ' + name);
  const semi = html.indexOf(';', start);
  return html.slice(start, semi + 1);
}

// Lifts the resize-listener IIFE body by finding the marker comment and
// the matching close of its enclosing `window.addEventListener('resize', function(){ ... });`
// call, immediately after the chart-redraw-on-resize comment block.
function liftChartResizeHandler() {
  const marker = '// ---------- Chart redraw on window resize ----------';
  const start = html.indexOf(marker);
  assert.notStrictEqual(start, -1, 'could not find the chart resize handler section');
  const varStart = html.indexOf('var chartResizeDebounceTimer', start);
  assert.notStrictEqual(varStart, -1, 'could not find the debounce timer var');
  const callStart = html.indexOf("window.addEventListener('resize'", start);
  assert.notStrictEqual(callStart, -1, 'could not find the resize listener registration');
  // Find the matching close paren for addEventListener(...) by brace/paren
  // depth from the opening '(' right after 'resize', function(){
  let depth = 0;
  let j = html.indexOf('(', callStart);
  const openParen = j;
  for (; j < html.length; j++) {
    if (html[j] === '(') depth++;
    else if (html[j] === ')') { depth--; if (depth === 0) break; }
  }
  assert.ok(j > openParen, 'unbalanced parens for the resize listener');
  return html.slice(varStart, j + 2); // include trailing ';'
}

function build() {
  const listeners = {};
  const timers = [];
  const els = {};
  function stubEl(hidden){
    const el = { _hidden: !!hidden };
    el.hasAttribute = function(name){ return name === 'hidden' && el._hidden; };
    el.setAttribute = function(name){ if(name === 'hidden') el._hidden = true; };
    el.removeAttribute = function(name){ if(name === 'hidden') el._hidden = false; };
    return el;
  }
  els.tradeModalEl = stubEl(true); // closed by default
  els.growthChartCard = stubEl(true); // hidden by default

  const renderChartViewCalls = [];
  const historicalRerenderCalls = [];
  const renderGrowthChartCalls = [];

  const src = `
    var window = {
      addEventListener: function(type, fn){ LISTENERS[type] = fn; },
    };
    function setTimeout(fn, ms){ TIMERS.push({ fn: fn, ms: ms }); return TIMERS.length; }
    function clearTimeout(id){ var t = TIMERS[id - 1]; if(t) t.cancelled = true; }
    var document = {
      getElementById: function(id){ return ELS[id] || null; },
    };
    var tradeModalEl = ELS.tradeModalEl;
    var tradeModalChartSym = TEST_STATE.tradeModalChartSym;
    var historicalChartRerender = TEST_STATE.historicalChartRerender;
    var lastGrowthSeries = TEST_STATE.lastGrowthSeries;
    function renderChartView(sym){ RENDER_CHART_VIEW_CALLS.push(sym); }
    function renderGrowthChart(series){ RENDER_GROWTH_CHART_CALLS.push(series); }
    ${liftChartResizeHandler()}
  `;
  const TEST_STATE = { tradeModalChartSym: null, historicalChartRerender: null, lastGrowthSeries: null };
  function run(state){
    Object.assign(TEST_STATE, state);
    new Function('LISTENERS', 'TIMERS', 'ELS', 'TEST_STATE',
      'RENDER_CHART_VIEW_CALLS', 'RENDER_GROWTH_CHART_CALLS',
      src)(listeners, timers, els, TEST_STATE, renderChartViewCalls, renderGrowthChartCalls);
  }
  return { run, listeners, timers, els, renderChartViewCalls, historicalRerenderCalls, renderGrowthChartCalls };
}

function fireResizeAndFlush(ctx){
  ctx.listeners.resize();
  // Run whichever timer is still live (not cancelled by a later debounce).
  ctx.timers.filter(function(t){ return !t.cancelled; }).forEach(function(t){ t.fn(); });
}

function main() {
  // ---- A resize while the modal shows a LIVE chart re-renders that chart ----
  {
    const ctx = build();
    const historicalRerender = function(){ throw new Error('must not call the historical rerender for a live chart'); };
    ctx.run({ tradeModalChartSym: 'AAPL', historicalChartRerender: historicalRerender, lastGrowthSeries: null });
    ctx.els.tradeModalEl.removeAttribute('hidden'); // modal open
    fireResizeAndFlush(ctx);
    assert.deepStrictEqual(ctx.renderChartViewCalls, ['AAPL'],
      'a resize while the modal is open on a live chart must re-render that symbol\'s chart');
    console.log('G1 PASS resize re-renders the open modal\'s live chart');
  }

  // ---- A resize while the modal shows a HISTORICAL chart re-runs its rerender closure ----
  {
    const ctx = build();
    let historicalCalls = 0;
    const historicalRerender = function(){ historicalCalls++; };
    ctx.run({ tradeModalChartSym: null, historicalChartRerender: historicalRerender, lastGrowthSeries: null });
    ctx.els.tradeModalEl.removeAttribute('hidden');
    fireResizeAndFlush(ctx);
    assert.strictEqual(historicalCalls, 1,
      'a resize while the modal is open on a historical chart must re-run its stored render closure');
    assert.deepStrictEqual(ctx.renderChartViewCalls, [], 'must not also call renderChartView with no live symbol');
    console.log('G2 PASS resize re-renders the open modal\'s historical chart');
  }

  // ---- A resize while the modal is CLOSED touches neither chart ----
  {
    const ctx = build();
    let historicalCalls = 0;
    ctx.run({ tradeModalChartSym: 'AAPL', historicalChartRerender: function(){ historicalCalls++; }, lastGrowthSeries: null });
    // tradeModalEl stays hidden (default)
    fireResizeAndFlush(ctx);
    assert.deepStrictEqual(ctx.renderChartViewCalls, [], 'a closed modal must not get its chart re-rendered');
    assert.strictEqual(historicalCalls, 0, 'a closed modal must not get its historical chart re-rendered either');
    console.log('G3 PASS resize does nothing to the modal chart while the modal is closed');
  }

  // ---- A resize while the growth chart is visible redraws it from the last series ----
  {
    const ctx = build();
    const series = [{ cumulative: 10 }, { cumulative: 20 }];
    ctx.run({ tradeModalChartSym: null, historicalChartRerender: null, lastGrowthSeries: series });
    ctx.els.growthChartCard.removeAttribute('hidden');
    fireResizeAndFlush(ctx);
    assert.deepStrictEqual(ctx.renderGrowthChartCalls, [series],
      'a resize with the growth chart visible must redraw it from the last series, not refetch/recompute');
    console.log('G4 PASS resize redraws the visible growth chart from its last series');
  }

  // ---- A resize while the growth chart is hidden does not un-hide it ----
  {
    const ctx = build();
    const series = [{ cumulative: 10 }, { cumulative: 20 }];
    ctx.run({ tradeModalChartSym: null, historicalChartRerender: null, lastGrowthSeries: series });
    // growthChartCard stays hidden (default) -- e.g. a different Journal tab is active
    fireResizeAndFlush(ctx);
    assert.deepStrictEqual(ctx.renderGrowthChartCalls, [],
      'a resize must not redraw (and thereby un-hide) a growth chart that is currently hidden');
    console.log('G5 PASS resize leaves a hidden growth chart alone');
  }

  // ---- Rapid resize events are debounced to a single redraw ----
  {
    const ctx = build();
    ctx.run({ tradeModalChartSym: 'AAPL', historicalChartRerender: null, lastGrowthSeries: null });
    ctx.els.tradeModalEl.removeAttribute('hidden');
    ctx.listeners.resize();
    ctx.listeners.resize();
    ctx.listeners.resize();
    assert.ok(ctx.timers.length >= 3, 'each resize event must (re)schedule a debounce timer');
    // Only the LAST (uncancelled) timer should actually run.
    const live = ctx.timers.filter(function(t){ return !t.cancelled; });
    assert.strictEqual(live.length, 1, 'earlier debounce timers must be cancelled by each subsequent resize');
    live[0].fn();
    assert.deepStrictEqual(ctx.renderChartViewCalls, ['AAPL'],
      'three rapid resizes must still produce exactly one redraw');
    console.log('G6 PASS rapid resize events are debounced to a single redraw');
  }

  console.log('\nAll chart resize gates passed.');
}

main();

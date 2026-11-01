// The Bot page keeps its scroll position across a redraw (the owner, Oct 31, 2026: the page "jumps up sometimes" on a phone).
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
const m = /  function kalshiKeepScroll\(fn\)\{[\s\S]*?\n  \}\n/.exec(html);
assert(m, 'kalshiKeepScroll is missing');
function make(win){ return new Function('window', m[0] + '; return kalshiKeepScroll;')(win); }

// SK1: a redraw that clamps the page upward is put back, and the wrapped function's result and arguments pass through.
{ const win = { pageYOffset: 1700, scrollTo(x, y){ win.pageYOffset = y; } };
  const wrapped = make(win)(function(a){ win.pageYOffset = 0; return a + 1; });
  assert.strictEqual(wrapped(4), 5);
  assert.strictEqual(win.pageYOffset, 1700, 'scroll position restored after a redraw that moved it'); }

// SK2: a redraw that does not move the page triggers no scroll call, and a page at the top is never scrolled.
{ let calls = 0; const win = { pageYOffset: 900, scrollTo(){ calls++; } };
  make(win)(function(){})(); assert.strictEqual(calls, 0);
  const top = { pageYOffset: 0, scrollTo(){ calls++; } };
  make(top)(function(){ top.pageYOffset = 5; })(); assert.strictEqual(calls, 0, 'at the top, nothing is restored'); }

// SK3: the four redraws are wrapped on the page, and a throwing scroll API cannot break the redraw.
['renderKalshiBot', 'renderKalshiPnl', 'renderKalshiStatus', 'renderKalshiBooks'].forEach(n => assert(html.includes(n + ' = kalshiKeepScroll(' + n + ');'), n + ' not wrapped'));
{ const win = { get pageYOffset(){ throw new Error('x'); }, scrollTo(){ throw new Error('y'); } };
  assert.strictEqual(make(win)(function(){ return 7; })(), 7); }
console.log('scroll keep gates: ok');

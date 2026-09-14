'use strict';
// Switching pages via the nav used to leave the scroll position exactly
// where it was on the previous page -- landing on Journal already
// scrolled halfway down Trade Overview's own page length read as a
// broken page load, not a carried-over scroll position. showPage now
// resets scroll to the top on every page switch.

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

function fakePage() {
  return { hidden: false };
}

function main() {
  const pages = {
    'page-brief': fakePage(), 'page-trades': fakePage(), 'page-journal': fakePage(),
    'page-settings': fakePage(), 'page-changelog': fakePage(),
  };
  const scrollCalls = [];
  const src = `
    var document = {
      getElementById: function(id){ return PAGES[id] || null; },
      querySelectorAll: function(){ return []; },
    };
    var window = { scrollTo: function(x, y){ SCROLL_CALLS.push([x, y]); } };
    var history = { replaceState: function(){} };
    function renderStatusPage(){}
    function runCardEntrance(){}
    function renderCalendar(){}
    ${lift('showPage')}
    return showPage;
  `;
  const showPage = new Function('PAGES', 'SCROLL_CALLS', src)(pages, scrollCalls);

  showPage('journal');
  assert.deepStrictEqual(scrollCalls, [[0, 0]], 'switching pages must scroll to the top');
  assert.strictEqual(pages['page-journal'].hidden, false, 'the target page must actually show');
  assert.strictEqual(pages['page-trades'].hidden, true, 'other pages must hide');
  console.log('G1 PASS switching to a page scrolls to the top');

  showPage('trades');
  assert.deepStrictEqual(scrollCalls, [[0, 0], [0, 0]], 'every page switch scrolls to the top, not just the first');
  console.log('G2 PASS every subsequent page switch also scrolls to the top');

  console.log('\nAll scroll-to-top-on-nav gates passed.');
}

main();

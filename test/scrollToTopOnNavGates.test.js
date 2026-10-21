'use strict';
// Switching pages via the nav used to leave the scroll position exactly
// where it was on the previous page -- landing on a short page already
// scrolled halfway down a long one read as a broken page load, not a
// carried-over scroll position. showPage now resets scroll to the top on
// every page switch. It also owns which pages exist: three, and a name that
// is not one of them (an old #trades link) lands on the brief.

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
  const pages = { 'page-brief': fakePage(), 'page-settings': fakePage(), 'page-kalshi': fakePage(), 'page-data': fakePage() };
  const scrollCalls = [];
  const src = `
    var document = {
      getElementById: function(id){ return PAGES[id] || null; },
      querySelectorAll: function(){ return []; },
      querySelector: function(){ return null; },   // showPage widens the app shell for Kalshi through this; a missing shell is simply skipped
    };
    var window = { scrollTo: function(x, y){ SCROLL_CALLS.push([x, y]); } };
    var history = { replaceState: function(){} };
    function kalshiOnShow(){}
    function kalshiOnHide(){}
    function renderDataCenter(){}
    var kalshiWatching = false;
    function pageEnter(){}
    var currentUserIsAdmin = IS_ADMIN;
    ${lift('showPage')}
    return showPage;
  `;
  const showPage = new Function('PAGES', 'SCROLL_CALLS', 'IS_ADMIN', src)(pages, scrollCalls, true);

  showPage('settings');
  assert.deepStrictEqual(scrollCalls, [[0, 0]], 'switching pages must scroll to the top');
  assert.strictEqual(pages['page-settings'].hidden, false, 'the target page must actually show');
  assert.strictEqual(pages['page-brief'].hidden, true, 'other pages must hide');
  assert.strictEqual(pages['page-kalshi'].hidden, true, 'the Kalshi page must hide when another page is shown');
  console.log('G1 PASS switching to a page scrolls to the top');

  showPage('kalshi');
  assert.deepStrictEqual(scrollCalls, [[0, 0], [0, 0]], 'every page switch scrolls to the top, not just the first');
  assert.strictEqual(pages['page-kalshi'].hidden, false);
  console.log('G2 PASS every subsequent page switch also scrolls to the top');

  // A page that no longer exists must not leave a blank screen: every page hides if nothing shows.
  showPage('trades');
  assert.strictEqual(pages['page-brief'].hidden, false, 'a removed page name lands on the brief');
  assert.ok(pages['page-kalshi'].hidden && pages['page-settings'].hidden, 'and nothing else is showing');
  console.log('G3 PASS a removed page name (an old #trades link) lands on the brief');

  // The Kalshi page is the owner's: anyone else asking for it gets the brief.
  const guestPages = { 'page-brief': fakePage(), 'page-settings': fakePage(), 'page-kalshi': fakePage(), 'page-data': fakePage() };
  const guestShow = new Function('PAGES', 'SCROLL_CALLS', 'IS_ADMIN', src)(guestPages, [], false);
  guestShow('kalshi');
  assert.strictEqual(guestPages['page-kalshi'].hidden, true, 'a non-admin account never sees the Kalshi page');
  assert.strictEqual(guestPages['page-brief'].hidden, false, 'it lands on the brief instead');
  console.log('G4 PASS a non-admin account asking for Kalshi lands on the brief');

  console.log('\nAll scroll-to-top-on-nav gates passed.');
}

main();

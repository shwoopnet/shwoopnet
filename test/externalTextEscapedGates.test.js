'use strict';
// News headlines, article links and broker error text are written by other people. They reach the page through innerHTML
// (the alert toast, the History list, the Activity log and the trade toasts), and a headline containing markup would run as
// script in a session that can read the Alpaca keys and, for the admin, place Kalshi orders. The article LIST already
// escaped its text and scheme-checked its link; these gates hold the other paths to the same rule.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};

function fnSource(name) {
  const start = html.indexOf('function ' + name + '(');
  assert.ok(start >= 0, name + ' exists');
  let i = html.indexOf('{', html.indexOf(')', start)), depth = 0;
  for (; i < html.length; i++) {
    if (html[i] === '{') depth++;
    else if (html[i] === '}' && --depth === 0) return html.slice(start, i + 1);
  }
  throw new Error('unbalanced ' + name);
}

const EVIL = '<img src=x onerror=alert(1)>';

gates.X1 = () => {
  const made = [];
  const doc = {
    getElementById: () => ({ appendChild: () => {} }),
    createElement: () => { const el = { classList: { add() {} }, remove() {}, querySelector: () => ({ addEventListener() {} }), set innerHTML(v) { made.push(v); } }; return el; },
  };
  const src = ['escapeHtml', 'safeHttpHref', 'newsAlertTagClass', 'showToast'].map(fnSource).join('\n');
  const f = new Function('document', 'repositionToastContainer', 'dismissToast', 'setTimeout', src + '\nreturn showToast;')(doc, () => {}, () => {}, () => {});
  f({ sym: EVIL, tag: EVIL, text: EVIL, url: 'javascript:alert(1)' });
  assert.ok(!/<img/i.test(made[0]), 'markup in a headline, symbol or tag is text, not elements');
  assert.ok(!/javascript:/i.test(made[0]) && !/<a /i.test(made[0]), 'a non-http link draws no anchor');
  f({ sym: 'AAPL', tag: 'News', text: 'Up 5% & rising', url: 'https://example.com/a?x=1&y="2"' });
  assert.ok(/href="https:\/\/example\.com\/a\?x=1&amp;y=&quot;2&quot;"/.test(made[1]), 'a real link is kept, attribute-escaped');
  assert.ok(/Up 5% &amp; rising/.test(made[1]));
};

gates.X2 = () => {
  const h = fnSource('renderHistoryList');
  for (const field of ['item.sym', 'item.tag', 'item.text', 'item.timeLabel']) {
    const bare = new RegExp("\\+ " + field.replace('.', '\\.') + " \\+");
    assert.ok(!bare.test(h), field + ' is never concatenated into the markup unescaped');
  }
  assert.ok(!/href="' \+ item\.url/.test(h), 'the link goes through the scheme check');
  assert.ok((h.match(/safeHttpHref\(item\.url\)/g) || []).length >= 2, 'no link, no anchor');
};

gates.X3 = () => {
  const closed = fnSource('showPositionClosedToast');
  assert.ok(/escapeHtml\(sym\)/.test(closed) && /escapeHtml\(reason\)/.test(closed), 'the auto-close toast escapes the symbol and the reason');
  assert.ok(/escapeHtml\(sym\)/.test(fnSource('showTradeResolvedToast')), 'the closed-trade toast escapes the symbol');
  assert.ok(/escapeHtml\(entry\.text\)/.test(html) && /escapeHtml\(entry\.sym \|\| ''\)/.test(html), 'the Activity log escapes broker error text');
  assert.ok(/escapeHtml\(reasonText\)/.test(html), 'the pause banner escapes the pause reason');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();

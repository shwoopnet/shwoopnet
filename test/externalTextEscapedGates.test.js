'use strict';
// News headlines, article links and earnings symbols are written by other people. They reach the page through innerHTML, and a headline
// containing markup would run as script in a session that, for the admin, can place Kalshi orders. shared/marketSnapshot is read by EVERY
// signed-in account, so one bad headline reaches every open tab at once. These gates hold the Brief's two lists to the rule: text is text,
// and a link is drawn only for http(s).
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

// A fake document with one element per id; innerHTML is whatever the renderer last wrote.
function fakeDoc() {
  const els = {};
  return { els, getElementById: (id) => (els[id] = els[id] || { innerHTML: '' }) };
}

gates.X1 = () => {
  const doc = fakeDoc();
  const src = ['escapeHtml', 'renderMarketNews'].map(fnSource).join('\n');
  const render = new Function('document', src + '\nreturn renderMarketNews;')(doc);
  render([{ headline: EVIL, source: EVIL, url: 'javascript:alert(1)', datetime: 1 }, { headline: 'Up 5% & rising', source: 'Wire', url: 'https://example.com/a?x=1&y="2"', datetime: 1 }]);
  const out = doc.els.marketNewsList.innerHTML;
  assert.ok(!/<img/i.test(out), 'markup in a headline or source is text, not elements');
  assert.ok(!/javascript:/i.test(out), 'a non-http link draws no anchor');
  assert.strictEqual((out.match(/<a /g) || []).length, 1, 'only the real link is an anchor');
  assert.ok(/href="https:\/\/example\.com\/a\?x=1&amp;y=&quot;2&quot;"/.test(out), 'a real link is kept, attribute-escaped');
  assert.ok(/Up 5% &amp; rising/.test(out));
  render([]);
  assert.ok(/No headlines available/.test(doc.els.marketNewsList.innerHTML), 'no headlines says so, rather than leaving the last list up');
};

gates.X2 = () => {
  // The fear and greed rating comes from a third party through the shared tape document: it is text, never elements.
  const g = new Function('escapeHtml', fnSource('briefGaugeHtml') + '\nreturn briefGaugeHtml;')((x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'));
  const out = g(EVIL, { score: 40, rating: EVIL, prev: 30 });
  assert.ok(!/<img/i.test(out), 'a rating or label with markup is text, not elements');
  assert.ok(/mood-track/.test(out), 'and the gauge still draws');
};

gates.X3 = () => {
  // The escaper itself: the five characters that matter, and a non-string.
  const escapeHtml = new Function(fnSource('escapeHtml') + '\nreturn escapeHtml;')();
  assert.strictEqual(escapeHtml('<a href="x" onclick=\'y\'>&</a>'), '&lt;a href=&quot;x&quot; onclick=&#39;y&#39;&gt;&amp;&lt;/a&gt;');
  assert.strictEqual(escapeHtml(12), '12');
  // Every place a snapshot string reaches the page goes through it.
  const news = fnSource('renderMarketNews');
  for (const field of ['a.headline', 'a.source']) assert.ok(new RegExp('escapeHtml\\(' + field.replace('.', '\\.')).test(news), field + ' is escaped');
  assert.ok(/escapeHtml\(a\.url\)/.test(news) && /\^https\?:/.test(news), 'the link is scheme-checked and attribute-escaped');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();

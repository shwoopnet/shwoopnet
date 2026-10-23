'use strict';
// The "official" pass (Oct 22, 2026, the owner: make the site feel less start-up-y). Each gate states a consequence a visitor or a search engine would notice.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const gates = {};

// A private dashboard on a public host is not listed by search engines, and a shared link or the browser chrome says what it is.
gates.O1 = () => {
  assert.ok(/<meta name="robots" content="noindex, nofollow">/.test(html), 'the page asks not to be indexed');
  assert.ok(/<meta name="description" content="Private trading dashboard\. Authorized users only\.">/.test(html), 'it has a plain description');
  assert.ok(/<meta name="theme-color" content="#0a0a0a">/.test(html), 'the browser bar matches the theme');
  const robots = fs.readFileSync(path.join(root, 'robots.txt'), 'utf8');
  assert.ok(/User-agent: \*\s*\nDisallow: \//.test(robots), 'robots.txt asks crawlers to stay out');
};

// A wrong address lands on our own page, not the host's default, and it does not trap the visitor.
gates.O2 = () => {
  const p404 = fs.readFileSync(path.join(root, '404.html'), 'utf8');
  assert.ok(/<title>Page not found \| Shwoop Financials<\/title>/.test(p404) && /noindex/.test(p404), 'a titled, unindexed 404 page');
  assert.ok(/<a href="\/">Back to the dashboard<\/a>/.test(p404), 'it links back');
  assert.ok(!/<script/i.test(p404) && !/https?:\/\//.test(p404.replace(/<!DOCTYPE[^>]*>/i, '')), 'it is self contained: no script and no outside request');
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(!/- 404\.html|- robots\.txt/.test(cfg), 'neither is excluded from the published site');
};

// The tab says which page you are on once you are signed in, and the signed-out visitor keeps the full title.
gates.O3 = () => {
  const m = html.match(/names = \{ brief: '([^']+)', kalshi: '([^']+)', data: '([^']+)', settings: '([^']+)' \};\s*document\.title = gate && !gate\.hasAttribute\('hidden'\) \? DEFAULT_PAGE_TITLE : \(names\[currentPageName\] \|\| 'Market Brief'\) \+ ' \| Shwoop Financials';/);
  assert.ok(m, 'setPageTitle names every page and falls back to the tagline while the sign-in box is up');
  assert.deepStrictEqual(m.slice(1), ['Market Brief', 'Bot', 'Data', 'Settings']);
  assert.ok(html.indexOf('currentPageName = name; setPageTitle();') > html.indexOf("if(name !== 'brief' && name !== 'kalshi'"), 'showPage sets it after an unknown name has been sent to the brief, so the title always matches the page shown');
  assert.ok(/authGateEl\.setAttribute\('hidden', ''\); setPageTitle\(\);/.test(html) && /authGateEl\.removeAttribute\('hidden'\); setPageTitle\(\);/.test(html), 'signing in and out refresh it');
};

// The signed-out page says what it is, and a keyboard user can see where they are on every control.
gates.O4 = () => {
  // The sign-in box no longer carries a line under its title (the owner, Oct 23, 2026): the front page already says access is by invitation, and the box says only what it does.
  assert.ok(/<div class="auth-title">Sign in<\/div>\s*<div class="auth-status" id="authStatus">/.test(html) && !/<div class="auth-sub">/.test(html), 'the sign-in box is just a title, the status and the form');
  const rule = html.match(/button:focus-visible[^{]*\{[^}]*\}/)[0];
  ['input:focus-visible', 'select:focus-visible', 'textarea:focus-visible', 'summary:focus-visible', 'a:focus-visible'].forEach((s) => assert.ok(rule.includes(s), s + ' has a visible focus ring'));
};

// The privacy line is there, honest about third parties, and promises nothing the page does not do.
gates.O5 = () => {
  const footer = html.slice(html.indexOf('<footer class="site-footer">'), html.indexOf('</footer>'));
  assert.ok(/Privacy: this is a private tool/.test(footer) && /no advertising and no analytics/.test(footer) && /third-party services/.test(footer), 'a plain privacy line');
  assert.ok(!/gtag|googletagmanager|analytics\.js|hotjar|mixpanel|sentry|segment\.com/i.test(html.replace(/no advertising and no analytics/g, '')), 'and the page really loads no analytics or tracker');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

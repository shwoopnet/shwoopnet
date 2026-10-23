// The signed-out front page (Oct 23, 2026). Consequence: it is only a layer over the same sign-in gate. Every id the sign-in code uses is still there, the form is still the only way in,
// and the page says nothing about the bot's markets, size or results and makes no performance claim, because it is public.
const assert = require('assert'), fs = require('fs'), path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gate = html.slice(html.indexOf('<div class="auth-gate" id="authGate">'), html.indexOf('<div class="app">'));
for (const id of ['authStatus', 'authForm', 'authEmail', 'authPassword', 'authPasswordToggle', 'authRememberMe', 'authError', 'authSubmitBtn', 'authForgotBtn']) {
  assert.ok(new RegExp('id="' + id + '"').test(gate), 'the sign-in code still finds #' + id);
}
assert.ok(/<form id="authForm" hidden>/.test(gate), 'the form still starts hidden until the sign-in code shows it');
const copy = gate.replace(/<[^>]*>/g, ' ');
assert.ok(!/\$\s?\d|\d\s?%|\bwin rate\b|\bprofit\b|\breturns?\b|\bperformance\b|Bitcoin|gold|Kalshi|contract[s]? per|stop at/i.test(copy.replace(/security or contract/g, '').replace(/Past results do not predict future results/g, '').replace(/offer, advice or a solicitation to buy or sell any security or contract/g, '')),
  'no figures, markets, venue or performance claim on a public page');
assert.ok(/not a broker, investment adviser or fund/.test(gate) && /loss of all capital/.test(gate), 'the risk notice is there');
assert.ok(/href="mailto:shwoopadvisor@gmail\.com"/.test(gate), 'the footer has the contact address the owner chose');
assert.ok(!/<svg|<script|<img|href="http/.test(gate), 'no image, script or outside link in the front page');
// The front page (Oct 23, 2026): the slogan and the line, a 24 hour dial of the visitor's own day, and a small sign-in. Consequence: the page has its OWN palette in one scoped block (the dashboard theme is untouched), and every animation stops when motion is not wanted.
assert.ok(/<h1 class="front-h1">Trade less\.<br><span>Live more\.<\/span><\/h1>/.test(gate) && /Systematic trading/.test(gate), 'the slogan and the Systematic trading label are on the front page');
assert.ok(/Shwoop Financials builds systematic trading tools:<\/b> rules written in advance, run by software, reviewed by people\./.test(gate), 'the line under the slogan says what Shwoop builds');
assert.ok(/Shwoop Financials, LLC/.test(gate), 'the footer names the company');
assert.ok(/id="frontDial"/.test(gate) && /id="frontDialText"/.test(gate), 'the dial is on the front page');
const front = (/\/\* The signed-out screen[\s\S]*?\.auth-title\{/.exec(html) || [''])[0].replace(/\/\*[\s\S]*?\*\//g, '');
const palette = /\.auth-gate\{([\s\S]*?)\n  \}/.exec(front)[1];
assert.ok(/--ink:#F6F4EE/.test(palette) && /--paper:#10131C/.test(palette) && /--amber:#3B6FE0/.test(palette), 'the page palette is declared once, on the gate itself');
assert.ok(!/#[0-9a-fA-F]{3,8}\b|rgb\(/.test(front.replace(palette, '').replace(/rgba\(16,19,28,\.\d+\)|rgba\(59,111,224,\.\d+\)/g, '')), 'everything else on the front page uses those tokens, not fixed colours');
const media = /@media \(prefers-reduced-motion: reduce\)\{([\s\S]*?)\n  \}/.exec(html.replace(/\/\*[\s\S]*?\*\//g, ''))[1];
assert.ok(/\.front-eyebrow, \.front-h1, \.front-line, \.front-dial\{ animation: none; \}/.test(media) && /\[data-reduce-motion="true"\] \.front-h1/.test(html), 'the rise-in shows its finished state at once under reduced motion and the Settings switch');
assert.ok(/function reduced\(\)/.test(html) && /if\(!reduced\(\)/.test(html), 'the dial stops drifting under reduced motion too');
console.log('frontPageGates: ok');

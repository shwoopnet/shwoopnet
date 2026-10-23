// The signed-out front page (Oct 23, 2026). Consequence: it is only a layer over the same sign-in gate. Every id the sign-in code uses is still there, the form is still the only way in,
// and the page says nothing about the bot's markets, size or results and makes no performance claim, because it is public.
const assert = require('assert'), fs = require('fs'), path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gate = html.slice(html.indexOf('<div class="auth-gate" id="authGate">'), html.indexOf('<div class="app">'));
for (const id of ['authStatus', 'authForm', 'authEmail', 'authPassword', 'authPasswordToggle', 'authRememberMe', 'authError', 'authSubmitBtn', 'authForgotBtn']) {
  assert.ok(new RegExp('id="' + id + '"').test(gate), 'the sign-in code still finds #' + id);
}
assert.ok(/<form id="authForm" hidden>/.test(gate), 'the form still starts hidden until the sign-in code shows it');
assert.ok(/Trade less\.<br><span>Live more\.<\/span>/.test(gate), 'the slogan is on the front page');
const copy = gate.replace(/<[^>]*>/g, ' ');
assert.ok(!/\$\s?\d|\d\s?%|\bwin rate\b|\bprofit\b|\breturns?\b|\bperformance\b|Bitcoin|gold|Kalshi|contract[s]? per|stop at/i.test(copy.replace(/security or contract/g, '').replace(/Past results do not predict future results/g, '').replace(/offer, advice or a solicitation to buy or sell any security or contract/g, '')),
  'no figures, markets, venue or performance claim on a public page');
assert.ok(/not a broker, investment adviser or fund/.test(gate) && /loss of all capital/.test(gate), 'the risk notice is there');
assert.ok(!/<svg|<script|<img|href="http/.test(gate), 'no image, script or outside link in the front page');
console.log('frontPageGates: ok');

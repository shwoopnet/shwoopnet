// The signed-out front page (Oct 23, 2026). Consequence: it is only a layer over the same sign-in gate. Every id the sign-in code uses is still there, the form is still the only way in,
// and the page says nothing about the bot's markets, size or results and makes no performance claim, because it is public.
const assert = require('assert'), fs = require('fs'), path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gate = html.slice(html.indexOf('<div class="auth-gate" id="authGate">'), html.indexOf('<div class="app">'));
for (const id of ['authStatus', 'authForm', 'authEmail', 'authPassword', 'authPasswordToggle', 'authRememberMe', 'authError', 'authSubmitBtn', 'authForgotBtn']) {
  assert.ok(new RegExp('id="' + id + '"').test(gate), 'the sign-in code still finds #' + id);
}
assert.ok(/<form id="authForm" hidden>/.test(gate), 'the form still starts hidden until the sign-in code shows it');
const noShots = gate.slice(0, gate.indexOf('<div class="front-shots">')) + gate.slice(gate.indexOf('</main>'));
const copy = noShots.replace(/<[^>]*>/g, ' ');
assert.ok(!/\$\s?\d|\d\s?%|\bwin rate\b|\bprofit\b|\breturns?\b|\bperformance\b|Bitcoin|gold|Kalshi|contract[s]? per|stop at/i.test(copy.replace(/security or contract/g, '').replace(/Past results do not predict future results/g, '').replace(/offer, advice or a solicitation to buy or sell any security or contract/g, '')),
  'no figures, markets, venue or performance claim on a public page');
assert.ok(/not a broker, investment adviser or fund/.test(gate) && /loss of all capital/.test(gate), 'the risk notice is there');
assert.ok(/href="mailto:shwoopadvisor@gmail\.com"/.test(gate), 'the footer has the contact address the owner chose');
const gateNoChat = gate.replace(/<div class="gq" id="gqRoot">[\s\S]*?\n  <\/div>\n/, '');
assert.ok(gateNoChat.length < gate.length, 'the Got questions widget is found and measured on its own (test/landingChatGates.test.js)');
assert.ok(!/<svg|<script|<img|href="http/.test(gateNoChat), 'no image, script or outside link in the front page (the Got questions widget has its own gate)');
// The front page (Oct 23, 2026): the slogan, a small sign-in and two window snapshots (the Account page and the Market Brief) with every figure blurred to bars. Consequence: the page has its OWN palette in two colours on the gate (the dashboard theme is untouched), three layouts picked in Settings, and every animation stops when motion is not wanted.
assert.ok(/<h1 class="front-h1">Trade less\.<br><span>Live more\.<\/span><\/h1>/.test(gate) && /Systematic trading/.test(gate), 'the slogan and the Systematic trading label are on the front page');
assert.ok(/Shwoop Financials builds systematic trading tools:<\/b> rules written in advance, run by software, reviewed by people\./.test(gate) && /Shwoop Financials, LLC/.test(gate), 'the line under the slogan and the LLC footer');
const shots = gate.slice(gate.indexOf('<div class="front-shots">'), gate.indexOf('</main>'));
const shotText = shots.replace(/<[^>]*>/g, ' ');
assert.ok(/front-win-a/.test(gate) && /front-win-b/.test(gate) && /Market Brief/.test(gate), 'the two snapshots are there');
assert.ok((shots.match(/Sample data/g) || []).length === 2 && /Sample screens with made-up numbers, shown for illustration only\. They are not real account data or results\./.test(gate), 'each window says Sample data and a caption says the numbers are made up and not real results');
assert.ok(!/%|\+\s?\$|win rate|profit|return|performance|Bitcoin|gold|Kalshi|contracts?\b/i.test(shotText.replace(/Reinvest pool|Stake per trade/g, '')), 'the sample screens show no gain, percentage, result or market name, only obviously dummy numbers');
assert.ok(!/class="[^"]*\b(g|gain|loss)\b/.test(shots), 'and nothing in them is coloured as a gain or a loss');
assert.ok(!/accentChoice|loginColorChoice|data-accent|data-login-color|loginLayout|data-login-layout/.test(html), 'there is no colour or layout choice: the whole site is black and white (the owner, Oct 23, 2026)');
const front = (/\/\* The signed-out screen[\s\S]*?\.auth-title\{/.exec(html) || [''])[0].replace(/\/\*[\s\S]*?\*\//g, '');
const media = /@media \(prefers-reduced-motion: reduce\)\{([\s\S]*?)\n  \}/.exec(html.replace(/\/\*[\s\S]*?\*\//g, ''))[1];
assert.ok(/\.front-eyebrow, \.front-h1, \.front-line, \.front-win, \.front-win-a \.win\{ animation: none; \}/.test(media) && /\[data-reduce-motion="true"\] \.front-win-a \.win/.test(html), 'the rise-in and the float stop under reduced motion and the Settings switch');
assert.ok(/\.front-win \.win\{[^}]*aspect-ratio:16 \/ 10/.test(html), 'both snapshot windows share one landscape shape, so neither is taller than the other (the owner, Oct 23, 2026)');
// The "Got questions?" label and arrow are fixed over the screen and used to land on the page text on a short phone, in landscape and on a tablet (the owner, Oct 30, 2026: "the landing page may be overlapping some texts"). They hide when they would touch text, and the bubble never covers the disclaimer.
assert.ok(/\.gq-crowded \.gq-label, \.gq-crowded \.gq-arrow\{ opacity:0; \}/.test(html) && /function gqFit\(\)/.test(html) && /root\.classList\.toggle\('gq-crowded', crowded\)/.test(html), 'the marker label and arrow hide whenever they would sit on text');
assert.ok(/\.auth-gate \.front-foot, \.auth-gate \.front-note\{ padding-right:84px; \}/.test(html), 'the disclaimer leaves room for the bubble');
console.log('frontPageGates: ok');

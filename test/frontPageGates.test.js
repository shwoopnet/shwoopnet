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
assert.ok(!/<svg|<script|<img|href="http/.test(gate), 'no image, script or outside link in the front page');
// The front page (Oct 23, 2026): the slogan, a small sign-in and two window snapshots (the Account page and the Market Brief) with every figure blurred to bars. Consequence: the page has its OWN palette in two colours on the gate (the dashboard theme is untouched), three layouts picked in Settings, and every animation stops when motion is not wanted.
assert.ok(/<h1 class="front-h1">Trade less\.<br><span>Live more\.<\/span><\/h1>/.test(gate) && /Systematic trading/.test(gate), 'the slogan and the Systematic trading label are on the front page');
assert.ok(/Shwoop Financials builds systematic trading tools:<\/b> rules written in advance, run by software, reviewed by people\./.test(gate) && /Shwoop Financials, LLC/.test(gate), 'the line under the slogan and the LLC footer');
const shots = gate.slice(gate.indexOf('<div class="front-shots">'), gate.indexOf('</main>'));
const shotText = shots.replace(/<[^>]*>/g, ' ');
assert.ok(/front-win-a/.test(gate) && /front-win-b/.test(gate) && /Market Brief/.test(gate), 'the two snapshots are there');
assert.ok((shots.match(/Sample data/g) || []).length === 2 && /Sample screens with made-up numbers, shown for illustration only\. They are not real account data or results\./.test(gate), 'each window says Sample data and a caption says the numbers are made up and not real results');
assert.ok(!/%|\+\s?\$|win rate|profit|return|performance|Bitcoin|gold|Kalshi|contracts?\b/i.test(shotText.replace(/Reinvest pool|Stake per trade/g, '')), 'the sample screens show no gain, percentage, result or market name, only obviously dummy numbers');
assert.ok(!/class="[^"]*\b(g|gain|loss)\b/.test(shots), 'and nothing in them is coloured as a gain or a loss');
assert.ok(/id="loginColorChoice"/.test(html) && /data-login-color/.test(html) && !/loginLayout|data-login-layout/.test(html), 'Settings picks only the login colour (one layout, two windows), and the page reads it before first paint');
const front = (/\/\* The signed-out screen[\s\S]*?\.auth-title\{/.exec(html) || [''])[0].replace(/\/\*[\s\S]*?\*\//g, '');
const palettes = [...front.matchAll(/\.auth-gate\{([^}]*)\}/g)].map((m) => m[1]);
assert.ok(palettes.length >= 2 && /--amber:#1fd68a/.test(palettes.join('')) && /--amber:#ffffff/.test(palettes.join('')), 'the two palettes (emerald and white) are declared on the gate itself');
assert.ok(!/#[0-9a-fA-F]{3,8}\b|rgb\(/.test(front.replace(/\.auth-gate\{[^}]*\}/g, '').replace(/html\[data-login-color="wh"\] \.auth-gate\{[^}]*\}/g, '').replace(/rgba\((0,0,0|255,255,255),[^)]*\)|#0F9D58/g, '')), 'everything else on the front page uses those tokens, not fixed colours (the gain green on the Running pill and plain black or white shades excepted)');
const media = /@media \(prefers-reduced-motion: reduce\)\{([\s\S]*?)\n  \}/.exec(html.replace(/\/\*[\s\S]*?\*\//g, ''))[1];
assert.ok(/\.front-eyebrow, \.front-h1, \.front-line, \.front-win, \.front-win-a \.win\{ animation: none; \}/.test(media) && /\[data-reduce-motion="true"\] \.front-win-a \.win/.test(html), 'the rise-in and the float stop under reduced motion and the Settings switch');
assert.ok(/\.front-win \.win\{[^}]*aspect-ratio:16 \/ 10/.test(html), 'both snapshot windows share one landscape shape, so neither is taller than the other (the owner, Oct 23, 2026)');
console.log('frontPageGates: ok');

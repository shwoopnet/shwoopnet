// The Account result chart fills its card (the owner, Nov 1, 2026) and the status footer does not say "ago ago".
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
// CH1: the chart box keeps its own shape as a minimum and grows; the drawing stretches; every stroke in it keeps a fixed screen width.
assert(/\[data-card="pnl"\]\{ align-self:stretch; display:flex; flex-direction:column; \}/.test(html), 'pnl card is a flex column');
assert(/\[data-card="pnl"\] \.kal-plot\{ flex:1 1 auto; \}/.test(html), 'plot grows');
assert(html.includes('<div class="kal-plot" style="aspect-ratio:\' + g.W + \' / \' + g.H + \'">'), 'plot keeps the chart shape as its minimum');
const m = /  function kalshiLineSvg\([\s\S]*?\n  \}\n/.exec(html)[0];
assert(m.includes('preserveAspectRatio="none"'), 'svg stretches');
(m.match(/<(path|line)\b[^>]*>/g) || []).forEach(t => assert(t.includes('vector-effect="non-scaling-stroke"'), 'stroke would scale: ' + t.slice(0, 60)));
assert(!/<(text|circle|ellipse)\b/.test(m), 'text or a circle in the stretched svg would be distorted');
// CH2: no doubled "ago".
assert(!/kalshiAgeText\([^)]*\)+ \+ ' ago/.test(html), 'kalshiAgeText already ends in ago');
console.log('chart fill gates: ok');

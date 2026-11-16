// The Account result chart fills its card (the owner, Nov 1, 2026) and the status footer does not say "ago ago".
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
// CH1: the chart box keeps its own shape as a minimum and grows; the drawing stretches; every stroke in it keeps a fixed screen width.
// Nov 16, 2026: the result line lives inside the Account card at full width, so its box has a set height (the chart's own shape would be very tall) and the drawing still stretches to it.
assert(/\.kal-acct-pnl \.kal-plot\{ aspect-ratio:auto !important; height:240px; \}/.test(html) && /\.kal-acct-pnl \.kal-plot > svg\{ position:absolute;/.test(html), 'the plot has a set height inside the Account card and the svg fills it');
assert(html.includes('<div class="kal-plot" style="aspect-ratio:\' + g.W + \' / \' + g.H + \'">'), 'plot keeps the chart shape as its minimum');
const m = /  function kalshiLineSvg\([\s\S]*?\n  \}\n/.exec(html)[0];
assert(m.includes('preserveAspectRatio="none"'), 'svg stretches');
(m.match(/<(path|line)\b[^>]*>/g) || []).forEach(t => assert(t.includes('vector-effect="non-scaling-stroke"'), 'stroke would scale: ' + t.slice(0, 60)));
assert(!/<(text|circle|ellipse)\b/.test(m), 'text or a circle in the stretched svg would be distorted');
// CH2: no doubled "ago".
assert(!/kalshiAgeText\([^)]*\)+ \+ ' ago/.test(html), 'kalshiAgeText already ends in ago');
console.log('chart fill gates: ok');

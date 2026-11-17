const fs=require('fs'),assert=require('assert');
const h=fs.readFileSync('index.html','utf8');
// HD1: the Account chart's hover dot lives in the chart's own box (.kal-plot), not in #kalPnlBody, which is display:contents and has no box to measure against.
assert(/#kalPnlBody\{ display:contents|#kalPnlBody\{[^}]*display:contents/.test(h)||/kalPnlBody[^{]*\{[^}]*display:contents/.test(h),'HD1 premise: the body has no box');
assert(/var plot = svg\.parentNode, dot = plot\.querySelector\('\.kal-pnl-dot'\)/.test(h),'HD1 dot found in the plot box');
assert(/plot\.appendChild\(dot\)/.test(h)&&!/host\.appendChild\(dot\)/.test(h),'HD1 dot appended to the plot, not the host');
console.log('hoverDotGates ok');

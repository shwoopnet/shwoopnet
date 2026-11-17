const fs=require('fs'),assert=require('assert');
const h=fs.readFileSync('index.html','utf8');
// EH1: cards that share a row stretch to the row's height by default (the owner, Nov 16: "really bugs me how they aren't even"); a card with a saved height keeps it, and the row grows to the taller card.
assert(/\.kal-console\{ align-items:stretch; \}/.test(h),'EH1 grid stretches its cards');
assert(!/\.kal-console\{ align-items:start; \}/.test(h),'EH1 no start alignment');
assert(/\[data-folded="true"\]\{ align-self:start; \}/.test(h),'EH1 a folded card still keeps its own height');
console.log('equalHeightsGates ok');

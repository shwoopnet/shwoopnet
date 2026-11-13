// Page load checks (Nov 13, 2026, the owner: "check for page loading bugs as well"). Each gate pins a fix for something a staged load showed: data arriving in the order Firestore answers it.
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
// PL-L1: the loss stop meter waits for the bot's settings. Before them it fell back to a $10 line and could read "100% used" in red for a moment.
assert(html.includes('var kalshiLiveCtl = { arm: null, last: null, session: null, loaded: false };'), 'the control state starts as not loaded');
assert(html.includes('kalshiLiveCtl = { arm: s.arm, last: s.last, session: s.session, loaded: true };'), 'the listener marks it loaded');
assert(/rEl\.innerHTML = !kalshiOrdersLoaded \? [^\n]*kalshiLiveCtl\.loaded === false \? '<div class="kal-empty">Reading the bot\\'s settings\.\.\.<\/div>'/.test(html), 'the meter says it is reading until then');
// PL-L2: "Reading the account..." is said once on the Bot page, not twice; the Today row holds its place.
assert(!/id="kalBotTotals"><div class="kal-empty">Reading the account/.test(html), 'the totals block does not repeat the line in the markup');
assert(!/totEl\.innerHTML = '<div class="kal-empty">Reading the account\.\.\.<\/div>'/.test(html), 'nor when it is drawn');
// PL-L3: the Brief does not jump when the prices arrive: each chart card holds the loaded height, the "Updated" line keeps its space, and the price strip shows its row at once with a loading line.
assert(/\.brief-chart\{ position:relative; min-height:185px; \}/.test(html), 'chart cards hold their height');
assert(/\.brief-asof\{ margin:-6px 0 14px 2px; min-height:1\.4em; \}/.test(html), 'the Updated line keeps its space');
const i = html.indexOf('tapeUnsubscribe = api.watchMarketTape(handleMarketTapeUpdate);');
assert(i > 0 && /Loading prices\.\.\./.test(html.slice(i - 500, i)), 'the strip shows a loading line before the first answer');
console.log('page load gates: ok');

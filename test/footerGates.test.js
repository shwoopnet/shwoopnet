// The footer carries the legal and risk disclosure (the owner's request, Oct 20, 2026). It must keep saying the things that matter, and it must not name third parties (the owner asked for no names).
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const footer = /<footer class="site-footer">([\s\S]*?)<\/footer>/.exec(html);
assert.ok(footer, 'the footer exists');
const text = footer[1].replace(/<[^>]+>/g, ' ').replace(/&[a-z]+;/g, ' ').replace(/\s+/g, ' ');
const gates = {
  F1: () => {
    assert.ok(/Shwoop Financials/.test(text) && /All rights reserved/.test(text), 'the owner of the site is named');
    assert.ok(!/LLC/.test(text), 'no "LLC" until the registration is complete (a company is not held out as an LLC before it is one)');
    assert.ok(/not financial advice/i.test(text) && /real money/.test(text), 'the short line says what it is and that the money is real');
  },
  F2: () => {
    for (const [re, why] of [[/not a broker-dealer/, 'not a broker'], [/investment adviser/, 'not an adviser'], [/substantial risk of loss/, 'risk of loss'], [/does not guarantee a maximum loss/, 'a loss limit is not a guarantee'],
      [/Past performance does not guarantee/, 'past performance'], [/hypothetical/, 'paper and backtest results are hypothetical'], [/as is/, 'as is'], [/not liable/, 'liability'], [/Data from third parties can be late/, 'third-party data']]) {
      assert.ok(re.test(text), 'the disclosure says: ' + why);
    }
  },
  F3: () => {
    assert.ok(!/Kalshi|Alpaca|Polymarket|Coinbase|Yahoo|CNBC|MarketWatch|Firebase|Render|GitHub/i.test(text), 'the footer names no exchange, broker, vendor or data provider');
    assert.ok(!/—/.test(footer[1]), 'no em dashes');
    assert.ok(/class="brand-name footer-brand"/.test(footer[1]), 'the wordmark uses the brand style');
  },
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);

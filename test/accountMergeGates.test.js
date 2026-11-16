// The Account result module is merged into the Account module and the Loss stop tile is gone (Nov 16, 2026, the owner, via the EA: "add the Loss stop card to the remove list ... combine Account result and Account into ONE module ... no duplicated figures").
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
const gates = {};
const bot = html.slice(html.indexOf('id="kalTabBot"'), html.indexOf('</main>', html.indexOf('id="kalTabBot"')));
const acct = /data-card="account">([\s\S]*?)\n      <div class="kal-card kal-compact" data-w="12" data-card="status">/.exec(bot)[1];
// AM1: four cards, no separate Account result card, and the result line (with its ranges) is inside the Account card, after the strategies table.
gates.AM1 = () => {
  assert.deepStrictEqual([...bot.matchAll(/data-card="(\w+)"/g)].map((m) => m[1]), ['account', 'status', 'positions', 'trades']);
  assert.ok(!/data-card="pnl"/.test(html) && !/>Account result<\/div>/.test(html), 'no card titled Account result');
  assert.strictEqual((html.match(/id="kalPnlBody"/g) || []).length, 1, 'one result body');
  assert.strictEqual((html.match(/id="kalPnlRanges"/g) || []).length, 1, 'one set of range buttons');
  assert.ok(acct.indexOf('id="kalPnl"') > -1 && acct.indexOf('id="kalPnlBody"') > acct.indexOf('id="kalPnlRanges"') && acct.indexOf('id="kalStrategies"') < 0, 'the result line sits in the Account card, ranges above the chart, and there is no strategies table');
};
// AM2: the Loss stop tile, its meter and the own stops line are gone, from the markup, the script and the styles.
gates.AM2 = () => {
  for (const t of ['kalRiskBody', 'kalRiskText', 'kal-acct-risk', 'kal-risk-own', 'kalshiOwnStops', 'class="kal-meter']) assert.ok(!html.includes(t), t + ' is gone');
  assert.ok(!/>Loss stop</.test(acct) && !/Own stops/.test(html), 'no Loss stop or Own stops text');
};
// AM3: no figure twice. At rest the chart's head shows only the percentage (the dollar result is the All strategies row's Result in the table above); the dollar figure shows while the line is being read.
gates.AM3 = () => {
  assert.ok(/\.kal-acct-pnl \.kal-pnl-head:not\(\.scrub\) b\{ display:none; \}/.test(html), 'dollar figure hidden at rest');
  assert.ok(/'kal-pnl-head ' \+ \(cum >= 0 \? 'kal-pos' : 'kal-neg'\) \+ \(when \? ' scrub' : ''\)/.test(html), 'and shown while the pointer is on the line');
};
// AM4: a saved layout that still names the old card loads cleanly, and a half width saved for Bot status (beside the old card) goes back to full.
gates.AM4 = () => {
  const iife = html.slice(html.indexOf("var VERSION = 3, KEY = 'kalBotLayout'") - 3000, html.indexOf("var layout = fresh(), migrated = false;"));
  const pure = new Function(iife.slice(iife.indexOf('var OPTIONAL')) + '; return { normalize: normalize };')();
  const n = pure.normalize({ v: 3, order: ['status', 'pnl', 'account', 'positions', 'trades'], width: { status: 6, pnl: 6 }, folded: { pnl: true } });
  assert.deepStrictEqual(n.order, ['status', 'account', 'positions', 'trades']);
  assert.deepStrictEqual(n.width, {}, 'status falls back to full width');
  assert.deepStrictEqual(n.folded, {});
};
let failed = 0;
for (const [k, f] of Object.entries(gates)) { try { f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + '\n' + (e && e.stack || e)); } }
process.exit(failed ? 1 : 0);

'use strict';
// GB1 to GB3: gold buys only 92c to 97c (the owner, Nov 10, 2026). Consequence: a gold favourite priced 88c to 91c places no order, one at 92c to 97c still does, and every other L1 market keeps the 88c to 97c band, so the change can only remove gold orders.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib.js');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const m = (ticker, bid, ask) => ({ ticker, yes_bid_dollars: String(bid), yes_ask_dollars: String(ask), status: 'open' });
const gates = {};
gates.GB1 = () => {
  assert.deepStrictEqual([...live.L1_GOLD_BAND], [0.92, 0.97], 'the constant');
  assert.strictEqual(live.l1Pick(m('KXGOLD15M-26NOV101415-15', 0.89, 0.90)), null, 'a gold favourite at 90c is no longer bought');
  assert.strictEqual(live.l1Pick(m('KXGOLD15M-26NOV101415-15', 0.90, 0.91)), null, 'nor at 91c');
  const at92 = live.l1Pick(m('KXGOLD15M-26NOV101415-15', 0.91, 0.92));
  assert.ok(at92 && at92.side === 'yes' && Math.abs(at92.price - 0.92) < 1e-9, 'at 92c it is still bought');
  const at97 = live.l1Pick(m('KXGOLD15M-26NOV101415-15', 0.96, 0.97));
  assert.ok(at97 && at97.side === 'yes', '97c is still inside');
  assert.strictEqual(live.l1Pick(m('KXGOLD15M-26NOV101415-15', 0.97, 0.98)), null, '98c is outside, as before');
  const no = live.l1Pick(m('KXGOLD15M-26NOV101415-15', 0.05, 0.06));
  assert.ok(no && no.side === 'no' && Math.abs(no.price - 0.95) < 1e-9, 'a NO favourite at 95c is bought');
  assert.strictEqual(live.l1Pick(m('KXGOLD15M-26NOV101415-15', 0.10, 0.11)), null, 'a NO favourite at 90c is not');
};
gates.GB2 = () => {
  assert.deepStrictEqual([...live.L1_BAND], [0.88, 0.97], 'the general band is unchanged');
  for (const t of ['KXBTC15M-26NOV101415-15', 'KXXRP15M-26NOV101415-15', 'KXETH15M-26NOV101415-15']) {
    const p = live.l1Pick(m(t, 0.89, 0.90));
    assert.ok(p && p.side === 'yes', t + ' keeps the 88c to 97c band (it is paused in code, so nothing orders it)');
  }
  assert.strictEqual(live.l1Pick(m(undefined, 0.89, 0.90)).side, 'yes', 'a quote without a ticker uses the general band');
};
gates.GB3 = () => {
  // the page says what the bot does: the Rules text and the price tile both use 92c to 97c for gold
  assert.ok(/Buys the side priced 92c to 97c about 6 minutes/.test(html), 'Rules and limits text');
  assert.ok(/name: 'Gold', series: 'KXGOLD15M', kind: 'fav', lo: 0\.92, hi: 0\.97/.test(html), 'the price tile band for gold');
  const code = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8').replace(/\/\/[^\n]*/g, '');
  assert.ok(!/L1_GOLD_BAND\s*=\s*[^;]*(args|session|process\.env|stored)/.test(code), 'the band is a code constant, nothing stored or requested can change it');
};
let failed = 0;
for (const [name, g] of Object.entries(gates)) { try { g(); console.log('ok ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
if (failed) process.exit(1);

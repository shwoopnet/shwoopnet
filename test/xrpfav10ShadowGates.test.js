// XRPFAV10 (Nov 15, 2026): the owner's own "Shadow it" answer allows ONE favourite-late rule back as a paper record only. The consequences pinned here: it is the single XRP favourite-late shadow, log only, 1 contract, in the registered band
// and look, and the logger's cent rounding at the lower edge is the one the spec states.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const sh = require('../functions/kalshiShadowLib');
const gates = {};
const NOW = Date.parse('2026-11-16T15:00:00Z');
const rule = () => sh.SHADOW_RULES.find((r) => r.id === 'XRPFAV10');
const q = (bid, ask, closeOffsetSec) => [{ series: 'KXXRP15M', m: { ticker: 'KXXRP15M-26NOV161500-00', status: 'open', close_time: new Date(NOW + closeOffsetSec * 1000).toISOString(), yes_bid_dollars: String(bid), yes_ask_dollars: String(ask), yes_ask_size_fp: '40', yes_bid_size_fp: '30' } }];

gates['XF1 registered once, valid, log only: XRP only, favourite 88c to 92c, 570 to 640 s, 1 contract, second look on'] = () => {
  const r = rule();
  assert.ok(r && Object.isFrozen(r) && Object.isFrozen(r.entry));
  assert.strictEqual(sh.validateShadowRule(r, sh.SHADOW_ALLOWED_SERIES).ok, true);
  assert.deepStrictEqual([r.series, r.contracts, r.entry], [['KXXRP15M'], 1, { sideRule: 'favourite', priceMin: 0.88, priceMax: 0.92, leftMaxSec: 640, leftMinSec: 570, secondRead: true }]);
  assert.ok(fs.existsSync(path.join(__dirname, '..', r.readme)), 'its pre-registration is in the repo');
  assert.ok(Date.parse(r.forwardReadDate) - Date.parse(r.registeredAt) >= 28 * 86400000, 'the read is 28 days after the registration');
};

gates['XF2 the 7c count holds: exactly one favourite-late shadow rule on XRP, and XRPFAV6 stays retired'] = () => {
  const xrp = sh.SHADOW_RULES.filter((r) => r.series.includes('KXXRP15M') && r.entry.sideRule === 'favourite');
  assert.deepStrictEqual(xrp.map((r) => r.id), ['XRPFAV10']);
  assert.ok(!sh.SHADOW_RULES.some((r) => r.id === 'XRPFAV6'));
};

gates['XF3 a favourite inside the band at the look logs one row at the rounded cent price; outside the band or the look logs nothing'] = () => {
  const inBand = sh.shadowSignals([rule()], q(0.89, 0.90, 600), NOW);
  assert.strictEqual(inBand.length, 1);
  assert.deepStrictEqual([inBand[0].rule, inBand[0].side, inBand[0].price, inBand[0].size], ['XRPFAV10', 'yes', 0.9, 1]);
  assert.strictEqual(sh.shadowSignals([rule()], q(0.89, 0.90, 400), NOW).length, 0, 'under 570 s is outside the look');
  assert.strictEqual(sh.shadowSignals([rule()], q(0.89, 0.90, 700), NOW).length, 0, 'over 640 s is outside the look');
  assert.strictEqual(sh.shadowSignals([rule()], q(0.93, 0.94, 600), NOW).length, 0, 'over 92c is out');
};

gates['XF4 the rounding edge in the spec: a raw favourite ask of 0.875 rounds UP to 0.88 and enters; a raw 0.92 stays in; a raw 0.9201 rounds to 0.93 and is out'] = () => {
  assert.strictEqual(sh.shadowSignals([rule()], q(0.86, 0.875, 600), NOW).length, 1);
  assert.strictEqual(sh.shadowSignals([rule()], q(0.90, 0.92, 600), NOW).length, 1);
  assert.strictEqual(sh.shadowSignals([rule()], q(0.90, 0.9201, 600), NOW).length, 0);
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();

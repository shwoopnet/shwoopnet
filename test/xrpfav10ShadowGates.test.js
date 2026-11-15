// XRPFAV10 (Nov 15, 2026): the owner's own "Shadow it" answer allows ONE favourite-late rule back as a paper record only. The consequences pinned here: it is the single XRP favourite-late shadow, log only, 1 contract, in the registered band
// and look, and the logger's cent rounding at the lower edge is the one the spec states.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const sh = require('../functions/kalshiShadowLib');
const gates = {};
const NOW = Date.parse('2026-11-16T15:00:00Z');
// XRPFAV10 went LIVE as a trial seat on Nov 15, 2026 (the owner: "Live now, trial size"), so it is no longer a shadow rule; these gates keep pinning the logger's rounding on the rule as it was registered.
const RULE = Object.freeze({ id: 'XRPFAV10', readme: 'kalshi-scalper/workers/XRPFAV10_SHADOW_SPEC_NOV15.md', series: Object.freeze(['KXXRP15M']), entry: Object.freeze({ sideRule: 'favourite', priceMin: 0.88, priceMax: 0.92, leftMaxSec: 640, leftMinSec: 570, secondRead: true }), contracts: 1, registeredAt: '2026-11-15', forwardReadDate: '2026-12-13' });
const rule = () => RULE;
const q = (bid, ask, closeOffsetSec) => [{ series: 'KXXRP15M', m: { ticker: 'KXXRP15M-26NOV161500-00', status: 'open', close_time: new Date(NOW + closeOffsetSec * 1000).toISOString(), yes_bid_dollars: String(bid), yes_ask_dollars: String(ask), yes_ask_size_fp: '40', yes_bid_size_fp: '30' } }];

gates['XF1 the shadow rule shape is valid, log only: XRP only, favourite 88c to 92c, 570 to 640 s, 1 contract, second look on'] = () => {
  const r = rule();
  assert.ok(r && Object.isFrozen(r) && Object.isFrozen(r.entry));
  assert.strictEqual(sh.validateShadowRule(r, sh.SHADOW_ALLOWED_SERIES).ok, true);
  assert.deepStrictEqual([r.series, r.contracts, r.entry], [['KXXRP15M'], 1, { sideRule: 'favourite', priceMin: 0.88, priceMax: 0.92, leftMaxSec: 640, leftMinSec: 570, secondRead: true }]);
  assert.ok(fs.existsSync(path.join(__dirname, '..', r.readme)), 'its pre-registration is in the repo');
  assert.ok(Date.parse(r.forwardReadDate) - Date.parse(r.registeredAt) >= 28 * 86400000, 'the read is 28 days after the registration');
};

gates['XF2 XRPFAV10 is no longer a shadow rule: the production shadow registry holds only GOLDOFF, so the 7c favourite-late shadow count is zero'] = () => {
  assert.deepStrictEqual(sh.SHADOW_RULES.map((r) => r.id), ['GOLDOFF']);
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

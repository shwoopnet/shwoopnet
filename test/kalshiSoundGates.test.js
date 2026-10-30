// The sound alerts (owner's request, Oct 20, 2026) are a page-only convenience. The consequences that matter: it is silent until switched on, silent on the first snapshot (opening the
// page must not sound for old trades), sounds for an entry, a sell, and a stop or issue, stays silent for the owner's own stop, and nothing about it can leave the device.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const code = src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '').replace(/<!--[\s\S]*?-->/g, '');

const start = src.indexOf('  var kalshiSoundOn = false');
const end = src.indexOf('  function renderKalshiBot(){');
assert.ok(start > 0 && end > start, 'the sound block must exist ahead of renderKalshiBot');
const block = src.slice(start, end);

// Runs the block with a fake page, returns a driver. `tones` collects every sound requested.
function rig(storedOn) {
  const tones = [];
  const win = { localStorage: { getItem: () => (storedOn ? 'on' : null), setItem() {} } };
  const env = { window: win, kalshiOrdersLoaded: true, kalshiLiveOrders: [], kalshiLiveCtl: { session: null } };
  env.kalshiAllOrders = function(){ return env.kalshiLiveOrders; };
  const body = block.replace('function kalshiSoundTone(kind){', 'function kalshiSoundTone(kind){ if(kalshiSoundOn){ __tones.push(kind); } return; ')
    + '; return { check: kalshiSoundCheck, setOn: function(v){ kalshiSoundOn = v; } };';
  const api = new Function('window', '__tones', 'env', 'with(env){' + body.replace(/kalshiOrdersLoaded/g, 'env.kalshiOrdersLoaded').replace(/kalshiLiveOrders/g, 'env.kalshiLiveOrders').replace(/kalshiLiveCtl/g, 'env.kalshiLiveCtl') + '}')(win, tones, env);
  return { api, env, tones };
}
const order = (id, extra) => Object.assign({ strategy: 'L1', clientOrderId: id, fillCount: 0, status: 'sending' }, extra || {});

const gates = {};

gates.S1 = () => {   // off until switched on: an off page makes no sound even when a trade happens
  const r = rig(false);
  r.api.check();
  r.env.kalshiLiveOrders = [order('a', { fillCount: 3, status: 'filled' })];
  r.api.check();
  assert.deepStrictEqual(r.tones, [], 'nothing sounds while the switch is off');
};

gates.S2 = () => {   // opening the page does not sound for trades that already exist
  const r = rig(true);
  r.env.kalshiLiveOrders = [order('a', { fillCount: 3, status: 'filled', exitStatus: 'sold' })];
  r.api.check();
  assert.deepStrictEqual(r.tones, [], 'the first snapshot is silent');
  r.api.check();
  assert.deepStrictEqual(r.tones, [], 'and an unchanged one stays silent');
};

gates.S3 = () => {   // entering, selling and an exit issue each sound, once
  const r = rig(true);
  r.api.check();
  r.env.kalshiLiveOrders = [order('a')];
  r.api.check();
  assert.deepStrictEqual(r.tones, [], 'an order sent but not filled is not an entry');
  r.env.kalshiLiveOrders = [order('a', { fillCount: 4, status: 'filled' })];
  r.api.check(); r.api.check();
  assert.deepStrictEqual(r.tones, ['enter'], 'a fill sounds once');
  r.env.kalshiLiveOrders = [order('a', { fillCount: 4, status: 'filled', exitStatus: 'sold' })];
  r.api.check(); r.api.check();
  assert.deepStrictEqual(r.tones, ['enter', 'sell'], 'a sell sounds once');
  r.env.kalshiLiveOrders = [order('a', { fillCount: 4, status: 'filled', exitStatus: 'sold' }), order('b', { fillCount: 4, status: 'filled', exitStatus: 'error' })];
  r.api.check();
  assert.deepStrictEqual(r.tones.slice(2), ['issue'], 'an exit that errored sounds the issue tone');
};

gates.S4 = () => {   // a stop the bot made itself sounds; the owner's own stop and flatten do not
  const r = rig(true);
  r.env.kalshiLiveCtl.session = { active: true };
  r.api.check();
  r.env.kalshiLiveCtl.session = { active: false, endedBecause: 'switched off by the owner' };
  r.api.check();
  assert.deepStrictEqual(r.tones, [], 'the owner pressing Stop is silent');
  const r2 = rig(true);
  r2.env.kalshiLiveCtl.session = { active: true };
  r2.api.check();
  r2.env.kalshiLiveCtl.session = { active: false, endedBecause: 'loss stop' };
  r2.api.check();
  assert.deepStrictEqual(r2.tones, ['issue'], 'a loss stop sounds the issue tone');
  const r3 = rig(true);
  r3.env.kalshiLiveCtl.session = { active: true };
  r3.api.check();
  r3.env.kalshiLiveCtl.session = { active: false, endedBecause: 'attempted' };
  r3.api.check();
  assert.deepStrictEqual(r3.tones, ['issue'], 'a lost order answer sounds the issue tone');
};

gates.S5 = () => {   // nothing leaves the device, and the browser notification stays out
  const keyLines = src.split('\n').filter((l) => l.indexOf('shwoopnet:kalSound') >= 0);
  assert.ok(keyLines.length >= 2 && keyLines.every((l) => /localStorage/.test(l)), 'the choice is only ever read and written in localStorage');
  assert.ok(!/kalshiSoundOn/.test(src.slice(0, src.indexOf('  var kalshiSoundOn = false'))), 'it is not referenced ahead of its own block (no settings sync)');
  assert.ok(!/new Notification\(/.test(code), 'no browser notification is constructed by the page');
  assert.ok(/id="kalSoundToggle"/.test(src), 'the switch is in Settings, Notifications');
};

let fails = 0;
Object.keys(gates).forEach((k) => { try { gates[k](); console.log('ok   ' + k); } catch (e) { fails++; console.log('FAIL ' + k + ': ' + e.message); } });
if (fails) process.exit(1);

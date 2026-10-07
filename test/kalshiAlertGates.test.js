// The outside watchdog for the Kalshi paper bot. A bot that has died cannot say so, so
// the alarm is a dead-man's switch: the bot pings a URL while healthy and the service
// behind it alerts when the pings stop. Each gate states the consequence.

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { pingsFor, sendAll } = require('../functions/kalshiAlertLib');
const { runTick } = require('../functions/kalshiBotRun');

const fnSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
const URL_ = 'https://hc-ping.com/abc';
const gates = {};

// Not configured means not sent: the bot must behave exactly as before.
gates.A1 = () => {
  assert.deepStrictEqual(pingsFor({ base: '', ok: true, tierMode: 'ok' }), []);
  assert.deepStrictEqual(pingsFor({ base: undefined, ok: true, tierMode: 'done', prevTier: 'ok' }), []);
};

// A healthy tick keeps the switch alive, whatever the day's limits say.
gates.A2 = () => {
  const p = pingsFor({ base: URL_, ok: true, tierMode: 'ok', prevTier: 'ok' });
  assert.deepStrictEqual(p.map((x) => x.url), [URL_]);
  assert.strictEqual(pingsFor({ base: URL_ + '///', ok: true, tierMode: 'break', prevTier: 'break' })[0].url, URL_, 'trailing slashes are trimmed');
};

// Silence is the alarm: a tick that could not read prices must NOT keep the switch alive,
// or a bot stuck in "fail closed" would look healthy forever.
gates.A3 = () => {
  assert.deepStrictEqual(pingsFor({ base: URL_, ok: false, tierMode: 'ok', prevTier: 'ok' }), []);
};

// Hitting the hard stop raises one alert, not one a minute for the rest of the day.
gates.A4 = () => {
  const first = pingsFor({ base: URL_, ok: true, tierMode: 'done', prevTier: 'half' });
  assert.deepStrictEqual(first.map((x) => x.url), [URL_, URL_ + '/fail'], 'success first, so the failure is the last word');
  const again = pingsFor({ base: URL_, ok: true, tierMode: 'done', prevTier: 'done' });
  assert.deepStrictEqual(again.map((x) => x.url), [URL_], 'no repeat failure while already done');
};

// A broken watchdog must never break the bot: a rejected or refused ping is only logged.
gates.A5 = async () => {
  const logs = [];
  await sendAll(async () => { throw new Error('network down'); }, [{ url: URL_, body: 'x' }], (m) => logs.push(m));
  await sendAll(async () => ({ ok: false, status: 500 }), [{ url: URL_, body: 'x' }], (m) => logs.push(m));
  assert.strictEqual(logs.length, 2, JSON.stringify(logs));
};

// The pings are sent in order, to the URLs asked for.
gates.A6 = async () => {
  const seen = [];
  await sendAll(async (u, o) => { seen.push([u, o.method]); return { ok: true }; }, [{ url: URL_, body: 'a' }, { url: URL_ + '/fail', body: 'b' }]);
  assert.deepStrictEqual(seen, [[URL_, 'POST'], [URL_ + '/fail', 'POST']]);
};

// The real tick reports what the watchdog needs: unreadable prices say ok:false.
gates.A7 = async () => {
  const store = { status: null, events: [], pos: [], async getStatus() { return this.status; }, async getControl() { return {}; },
    async listOpen() { return []; }, async listClosedSince() { return []; }, async createPosition() { return true; },
    async closePosition() { return false; }, async addEvent(e) { this.events.push(e); }, async setStatus(s) { this.status = s; } };
  const bad = { exchangeStatus: async () => { throw new Error('down'); }, markets: async () => [], market: async () => ({}) };
  const r = await runTick({ store, api: bad, now: Date.parse('2026-10-05T17:00:00Z') });
  assert.strictEqual(r.ok, false);
  const good = { exchangeStatus: async () => ({ trading_active: true }), markets: async () => [], market: async () => ({}) };
  const r2 = await runTick({ store, api: good, now: Date.parse('2026-10-05T17:01:00Z') });
  assert.strictEqual(r2.ok, true);
  assert.strictEqual(r2.prevTier, 'ok', 'the previous tick\'s tier is reported');
};

// Wired in the right place: after the tick (so a tick that throws sends nothing), the URL
// comes from config, and it stays the only scheduled function.
gates.A8 = () => {
  const body = fnSrc.slice(fnSrc.indexOf('exports.kalshiBot = onSchedule('));
  assert.ok(body.indexOf('runTick(') > -1 && body.indexOf('runTick(') < body.indexOf('alerts.sendAll('), 'ping only after the tick completes');
  assert.ok(/defineString\("KALSHI_WATCHDOG_URL", \{ default: "" \}\)/.test(fnSrc), 'optional, empty by default');
  assert.deepStrictEqual([...fnSrc.matchAll(/exports\.(\w+) = onSchedule\(/g)].map((x) => x[1]), ['kalshiLiveArmed', 'kalshiBot']);
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();

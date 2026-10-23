'use strict';
// The quote recorder pilot (Oct 22, 2026): research only. It reads public data, holds no secret, places no order, writes only to a data branch and is not published with the site.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'scripts', 'record_quotes.py'), 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-quotes.yml'), 'utf8');
const gates = {};
const py = (code) => execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('rq', ${JSON.stringify(path.join(root, 'scripts', 'record_quotes.py'))}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${code}`], { encoding: 'utf8' });

// Consequence: the recorder can never trade or sign anything, whatever it is changed into.
gates.Q1 = () => {
  const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2/.test(code), 'it reads Kalshi public market data');
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=\s*["'](POST|PUT|DELETE)/i.test(code), 'no key, no signing, no write call');
  assert.ok(!/\/portfolio|\/orders|order_id|create_order/.test(code), 'no account or order endpoint');
};

gates.Q2 = () => {
  assert.ok(/cron: "45 3,7,11,15,19,23 \* \* \*"/.test(wf) && /--cycle-hours 4/.test(wf), 'six 4 hour jobs a day, each starting 15 minutes before a boundary, so every close is recorded');
  assert.ok(/timeout-minutes: 330/.test(wf), 'a job fits inside the 6 hour limit (at most 4.5 hours of recording)');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.ok(/permissions:\s*\n\s*contents: write/.test(wf), 'contents write and nothing wider');
  assert.ok(/cancel-in-progress: false/.test(wf), 'two runs never overlap: the next job waits for this one');
};

gates.Q3 = () => {
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'neither the workflow nor the script is published with the site');
};

// Consequence: the windows and the rows mean what the research session reads them as.
gates.Q4 = () => {
  const out = JSON.parse(py(`
print(json.dumps([
  m.seconds_to_close(900 * 5 + 1), m.seconds_to_close(900 * 5 + 899), m.seconds_to_close(900 * 5), m.next_close(900 * 5 + 10) - 900 * 5,
  m.stop_time(62, 3600 * 10 + 5), m.stop_time(10, 3600 * 10 + 5) - 3600 * 10,
  m.quote_rows([{"ticker": "KXBTC15M-X", "yes_bid_dollars": "0.38", "yes_ask_dollars": "0.39", "yes_bid_size_fp": "5", "yes_ask_size_fp": "6", "floor_strike": 81000.5, "status": "active"}], 1, 2)[0],
  len(m.QUOTE_COLS)]))`));
  assert.deepStrictEqual(out.slice(0, 4), [899, 1, 900, 900], 'seconds to the next quarter hour, a fresh window right on the boundary');
  assert.strictEqual(out[4] - 3600 * 10, 3660, 'a run never goes past a minute after the top of the next hour');
  assert.strictEqual(out[5], 605, 'a short run stops when asked');
  assert.deepStrictEqual(out[6], [1, 2, 'KXBTC15M-X', '0.38', '0.39', '5', '6', 81000.5, 'active'], 'a quote row keeps send and receive time, both sides and sizes');
  assert.strictEqual(out[7], 9, 'header and row are the same width');
};

// Consequence: back to back 4 hour jobs leave no 15 minute window uncovered, even when a job starts late.
gates.Q6 = () => {
  const H = 3600, D = 4 * H;
  const out = JSON.parse(py(`
print(json.dumps([
  m.cycle_stop_time(3 * 3600 + 45 * 60, ${D}), m.cycle_stop_time(4 * 3600 + 5 * 60, ${D}), m.cycle_stop_time(3 * 3600 + 20 * 60, ${D}), m.cycle_stop_time(3 * 3600 + 59 * 60 + 30, ${D})]))`));
  assert.strictEqual(out[0], 8 * H + 60, 'started 15 minutes early: runs through the next boundary and one minute past the one after');
  assert.strictEqual(out[1], 8 * H + 60, 'started 5 minutes late: same stop, nothing earlier is lost');
  assert.strictEqual(out[2], 4 * H + 60, 'started more than 30 minutes before a boundary: stops just after that boundary');
  assert.ok(out[3] - (3 * H + 59 * 60 + 30) <= 4.6 * H, 'a job never runs past 4.6 hours, inside the limit');
  assert.ok(/--cycle-hours/.test(script), 'the option exists');
};

// Consequence: each exchange's message is read into (asset, price, size, time); anything that is not a trade of a recorded asset is ignored.
gates.Q5 = () => {
  const out = JSON.parse(py(`
print(json.dumps([
  m.parse_coinbase({"type": "ticker", "product_id": "BTC-USD", "price": "81000.1", "last_size": "0.01", "time": "T"}),
  m.parse_coinbase({"type": "subscriptions"}), m.parse_coinbase({"type": "ticker", "product_id": "LTC-USD", "price": "1"}),
  m.parse_kraken([5, [["2380.1", "0.5", "1792.1", "b", "m", ""]], "trade", "ETH/USD"]),
  m.parse_kraken([5, [["81000", "0.1", "1792.2", "s", "l", ""]], "trade", "XBT/USD"])[0][0],
  m.parse_kraken([5, [["0.078", "10", "1792.2", "s", "l", ""]], "trade", "XDG/USD"])[0][0],
  m.parse_kraken({"event": "heartbeat"}),
  m.parse_bitstamp({"event": "trade", "channel": "live_trades_solusd", "data": {"price": 103.2, "price_str": "103.2", "amount_str": "2", "microtimestamp": "1792"}}),
  m.parse_bitstamp({"event": "bts:subscription_succeeded", "channel": "live_trades_solusd"})]))`));
  assert.deepStrictEqual(out[0], [['BTC', '81000.1', '0.01', 'T']]);
  assert.deepStrictEqual([out[1], out[2]], [[], []], 'a non-trade message and an unrecorded asset are ignored');
  assert.deepStrictEqual(out[3], [['ETH', '2380.1', '0.5', '1792.1']]);
  assert.deepStrictEqual([out[4], out[5]], ['BTC', 'DOGE'], "Kraken's own names XBT and XDG map to BTC and DOGE");
  assert.deepStrictEqual([out[6], out[8]], [[], []]);
  assert.deepStrictEqual(out[7], [['SOL', '103.2', '2', '1792']]);
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

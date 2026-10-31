'use strict';
// The Deribit implied-probability recorder (Oct 31, 2026, research only, DERIBIT-IMPLIED): it reads public data, holds no secret, places no order, writes only to a data branch and is not published with the site.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_deribit.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-deribit.yml'), 'utf8');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (src) => execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('rd', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8' });

// D1: it can never trade, sign or authenticate, whatever it is changed into.
gates.D1 = () => {
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2/.test(code) && /www\.deribit\.com\/api\/v2/.test(code), 'it reads the two public APIs');
  assert.ok(!/PRIVATE|SECRET|Authorization|Bearer|ACCESS[-_]?KEY|SIGNATURE|API[-_]?KEY|client_secret|method\s*=\s*["'](POST|PUT|DELETE)|data\s*=/i.test(code), 'no key, no signing, no auth header, no write call');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order|public\/auth|private\//.test(code.replace(/\/orderbook/g, '')), 'no account, order or Deribit private/auth endpoint');
  assert.ok(!/os\.environ|getenv/.test(code), 'it reads no environment variable, so no secret');
  assert.ok(/KXBTCD/.test(code) && !/KXBTC15M|KXETH|KXGOLD|KXXRP|KXDOGE/.test(code), 'only the Bitcoin hourly ladder, nothing the live bot trades');
};

// D2: the workflow pushes only the data branch, uses only the built-in token, and each job fits inside the 6 hour limit.
gates.D2 = () => {
  assert.ok(/cron: "50 3,7,11,15,19,23 \* \* \*"/.test(wf) && /cron: "20 \* \* \* \*"/.test(wf) && /--cycle-hours 4/.test(wf), 'six 4 hour jobs a day plus an hourly trigger behind them');
  assert.ok(/timeout-minutes: 330/.test(wf), 'a job fits inside the 6 hour limit');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.ok(/data\/deribit\//.test(wf) && /git add deribit/.test(wf), 'its own folder deribit/');
  assert.ok(/permissions:\s*\n\s*contents: write/.test(wf) && /cancel-in-progress: false/.test(wf), 'contents write and nothing wider, two runs never overlap');
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'neither the workflow nor the script is published with the site');
};

// D3: the built-in stop date exists, is a UTC date in the future (so the recorder is meant to run) and stops recording the day after it.
gates.D3 = () => {
  const mm = script.match(/^STOP_DATE = datetime\.date\((\d{4}), (\d{1,2}), (\d{1,2})\)/m);
  assert.ok(mm, 'STOP_DATE is a date constant');
  const stop = Date.UTC(+mm[1], +mm[2] - 1, +mm[3]);
  assert.ok(stop > Date.now(), 'the stop date is in the future (extend it only by a reviewed edit)');
  assert.ok(stop <= Date.UTC(2027, 0, 1), 'and no later than the registered read date');
  assert.deepStrictEqual(JSON.parse(py(`
import datetime
d = m.STOP_DATE
print(json.dumps([m.past_stop(d), m.past_stop(d + datetime.timedelta(days=1))]))`)), [false, true], 'the stop date itself records, the next day does not');
  assert.ok(/if past_stop\(\):\s*\n\s*print\([^\n]*recording nothing/.test(script), 'main exits before opening any file when past the stop date');
};

// D4: every request goes through the one backoff helper, which never raises and retries 429, 503 and Deribit 10028.
gates.D4 = () => {
  assert.strictEqual((code.match(/urlopen\(/g) || []).length, 1, 'one place makes a request');
  assert.ok(/def http_get_backoff/.test(code) && /429, 503/.test(code) && /10028/.test(code), 'backoff on 429, 503 and 10028');
  assert.ok(/time\.sleep\(base_wait \* \(2 \*\* attempt\)\)/.test(code), 'the wait grows');
  const out = JSON.parse(py(`
import urllib.request
def boom(*a, **k): raise OSError("no network")
urllib.request.urlopen = boom
m.time.sleep = lambda s: None
print(json.dumps(list(m.http_get_backoff("https://x.invalid/a"))))`));
  assert.deepStrictEqual(out.slice(0, 3), [0, null, ''], 'a failed request is a status, never an exception');
};

// D5: the rows mean what the scorer reads them as: only the two expiries at or after the close, only strikes in the band, Kalshi quotes as returned.
gates.D5 = () => {
  const out = JSON.parse(py(`
close = int(m.datetime.datetime(2026, 11, 2, 12, 0, tzinfo=m.datetime.timezone.utc).timestamp())
names = ["BTC-1NOV26-80000-C", "BTC-2NOV26-80000-C", "BTC-2NOV26-80000-P", "BTC-3NOV26-81000-C", "BTC-4NOV26-80000-C", "BTC-2NOV26-95000-C", "JUNK"]
pairs = [(n, (m.parse_instrument(n) or [None])[0]) for n in names]
ex = m.pick_expiries(pairs, close)
summ = [{"instrument_name": n, "mark_iv": 40.5, "underlying_price": 80100.0, "underlying_index": "x", "bid_price": 0.01, "ask_price": 0.02, "mark_price": 0.015, "open_interest": 3, "creation_timestamp": 5} for n in names]
d = m.deribit_rows(1, 2, "C", summ, ex, 80000.0)
mk = [{"ticker": "A", "close_time": "C", "floor_strike": 80299.99, "yes_bid_dollars": "0.40", "yes_ask_dollars": "0.42", "no_bid_dollars": "0.58", "no_ask_dollars": "0.60", "last_price_dollars": "0.41"},
      {"ticker": "FAR", "close_time": "C", "floor_strike": 99999.99, "yes_bid_dollars": "0.01", "yes_ask_dollars": "0.02"},
      {"ticker": "OTHER", "close_time": "D", "floor_strike": 80000.0}]
k = m.kalshi_rows(1, "date", "C", mk, 80000.0)
r = m.result_rows(1, "C", [{"ticker": "A", "close_time": "C", "floor_strike": 1, "result": "yes", "expiration_value": "5"}, {"ticker": "B", "close_time": "C", "result": ""}])
print(json.dumps({"ex": ex, "close": close, "d": d, "k": k, "r": r, "dcols": len(m.DERIBIT_COLS), "kcols": len(m.KALSHI_COLS), "rcols": len(m.RESULT_COLS)}))`));
  assert.strictEqual(out.ex.length, 2, 'two expiries');
  assert.ok(out.ex.every((e) => e >= out.close), 'no expired or earlier expiry');
  assert.deepStrictEqual(out.d.map((r) => r[4]).sort(), ['BTC-3NOV26-81000-C', 'BTC-4NOV26-80000-C'].sort(), 'only the two expiries after the close (2 Nov 08:00 is before a 12:00 close), strikes in the band');
  assert.ok(out.d.every((r) => r.length === out.dcols), 'one value per column');
  assert.deepStrictEqual(out.d.map((r) => r[3]).sort(), [1, 2], 'rank 1 and rank 2');
  assert.strictEqual(out.k.length, 1, 'only the near strike of the closing event');
  assert.strictEqual(out.k[0].length, out.kcols);
  assert.strictEqual(out.k[0][5], '0.40', 'quotes are kept as returned');
  assert.strictEqual(out.r.length, 1, 'only settled markets have a result row');
  assert.strictEqual(out.r[0].length, out.rcols);
};

// D6: the request load is as disclosed: per minute at peak 1 Kalshi and 2 Deribit requests (plus one Kalshi result read once per close), spaced, once a minute, 30 polls per hour.
gates.D6 = () => {
  const rec = code.slice(code.indexOf('def record_hour'), code.indexOf('def record_results'));
  assert.strictEqual((rec.match(/kalshi_event_markets\(/g) || []).length, 1, 'one Kalshi request per poll');
  assert.strictEqual((rec.match(/deribit_call\("get_/g) || []).length, 3, 'index, summary per poll (inside the loop) and instruments once per window');
  assert.ok(/POLL_EVERY_S = 60\.0/.test(code) && /SPACING_S = 1\.5/.test(code), 'one poll a minute, requests spaced');
  assert.ok(/LEAD_START_S = 60 \* 60/.test(code) && /LEAD_END_S = 30 \* 60/.test(code), '60 to 30 minutes before the close');
};

// D7: back to back jobs leave no gap (same rule as the book recorder).
gates.D7 = () => {
  const out = JSON.parse(py(`print(json.dumps([m.cycle_stop_time(14400 * 5 + 1000, 14400), m.cycle_stop_time(14400 * 5 + 13000, 14400)]))`));
  assert.deepStrictEqual(out, [14400 * 6 + 60, 14400 * 7 + 60]);
};

for (const [name, fn] of Object.entries(gates)) { fn(); console.log('ok   ' + name); }

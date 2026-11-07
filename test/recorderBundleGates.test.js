'use strict';
// The recorder bundle (Nov 6, 2026, the owner approved V2's list): research only. Public GETs, no secret but the built-in token, data branch only, stop date 2027-02-26.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const rd = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const wfs = { candles: rd('.github', 'workflows', 'record-perps-candles.yml'), sunday: rd('.github', 'workflows', 'record-perps-sunday.yml') };
const scripts = { candles: rd('scripts', 'record_perps_candles.py'), sunday: rd('scripts', 'record_perps_sunday.py'), fast: rd('scripts', 'record_perps_fast.py'), daily: rd('scripts', 'record_daily.py') };
const strip = (s) => s.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const py = (file, body) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json, datetime as dt, tempfile, os, gzip, time
spec = importlib.util.spec_from_file_location('mod', ${JSON.stringify(path.join(root, 'scripts', file))}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${body}`], { encoding: 'utf8' }).trim().split('\n').pop());
const gates = {};

// RB1: each new workflow stops at 2027-02-26 (checked in the workflow and in the script), uses only the built-in token, pushes only the data branch, never cancels a running job.
gates.RB1 = () => {
  for (const [k, wf] of Object.entries(wfs)) {
    assert.ok(/20270226/.test(wf), k + ': the workflow checks the stop date');
    assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), k + ': only the built-in token');
    assert.ok(/git push -q origin perp-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), k + ': data branch only');
    assert.ok(/for i in 1 2 3 4 5 6; do git push/.test(wf), k + ': six try push loop');
    assert.ok(/cancel-in-progress: false/.test(wf) && /permissions:\s*\n\s*contents: write/.test(wf), k + ': one job at a time, contents write only');
    assert.ok(/ref: main/.test(wf), k + ': code from main');
  }
  assert.ok(/STOP_DATE = dt\.date\(2027, 2, 26\)/.test(scripts.candles), 'candles script stop date');
  assert.ok(/STOP_DATE = dt\.date\(2027, 2, 26\)/.test(scripts.sunday), 'sunday script stop date');
  const cfg = rd('_config.yml');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'not published with the site');
};

// RB2: public GET only. No key, no signing, no account or order endpoint, no write call.
gates.RB2 = () => {
  for (const k of ['candles', 'sunday']) {
    const code = strip(scripts[k]);
    assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|method\s*=\s*["'](POST|PUT|DELETE)|data\s*=/i.test(code), k + ': no key, no signing, no write call');
    assert.ok(!/\/portfolio|\/orders|order_id|create_order/i.test(code), k + ': no account or order endpoint');
  }
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2\/margin/.test(scripts.candles) && /candlesticks/.test(scripts.candles) && /funding_rates\/historical/.test(scripts.candles), 'candles and funding endpoints');
};

// RB3: the 30 second recorder (and so the 10 second Sunday one) carry halt_sources and is_open, from the same market object with no extra read; absent fields are empty.
gates.RB3 = () => {
  assert.ok(/EXTRA_COLUMNS = \["halt_sources", "is_open"\]/.test(scripts.fast), 'columns declared');
  assert.ok(/base\.COLUMNS \+ EXTRA_COLUMNS/.test(scripts.fast) && /base\.COLUMNS \+ fast\.EXTRA_COLUMNS/.test(scripts.sunday), 'both recorders write the new header');
  const r = py('record_perps_fast.py', `
a = m.rows_with_flags([{"ticker": "KXAAPLPERP", "halt_sources": [], "schedule": {"is_open": False}}, {"ticker": "KXBTCPERP", "halt_sources": ["a", "b"], "schedule": {"is_open": True}}, {"ticker": "X"}], "t")
print(json.dumps([m.base.COLUMNS + m.EXTRA_COLUMNS == m.base.COLUMNS + ["halt_sources", "is_open"], [x[-2:] for x in a], len(a[0]) == len(m.base.COLUMNS) + 2]))`);
  assert.deepStrictEqual(r, [true, [['', 'false'], ['a|b', 'true'], ['', '']], true]);
};

// RB4: the Sunday window is 17:55 to 18:35 New York on Sundays only (so daylight saving moves it), writes one file, a second start does nothing, a failed read costs one sample, past the stop date nothing.
gates.RB4 = () => {
  const r = py('record_perps_sunday.py', `
u = dt.timezone.utc
f = lambda s: (m.current_window(dt.datetime.fromisoformat(s).replace(tzinfo=u)) or [None])[0]
w = [f('2026-11-08T22:58:00'), f('2026-11-08T22:50:00'), f('2026-11-08T23:36:00'), f('2026-11-09T22:58:00'), f('2026-07-05T21:58:00'), f('2026-07-05T22:58:00')]
d = tempfile.mkdtemp()
clock = [dt.datetime(2026, 11, 8, 23, 33, 0, tzinfo=u)]
def now(): return clock[0]
def sleep(s): clock[0] = clock[0] + dt.timedelta(seconds=10)
calls = [0]
def fetch():
    calls[0] += 1
    if calls[0] == 2: raise RuntimeError('429')
    return [{"ticker": "KXAAPLPERP", "price": "6.9", "halt_sources": [], "schedule": {"is_open": True}}]
a = m.main(d, now, fetch, sleep)
rows = gzip.open(os.path.join(d, '2026-11-08', 'sunday.csv.gz'), 'rt').read().strip().split('\\n')
clock[0] = dt.datetime(2026, 11, 8, 23, 33, 30, tzinfo=u)
b = m.main(d, now, fetch, sleep)
clock[0] = dt.datetime(2027, 2, 28, 22, 58, 0, tzinfo=u)
c = m.main(d, now, fetch, sleep)
print(json.dumps([w, a, len(rows) - 1, calls[0], b, c, rows[0].endswith('halt_sources,is_open'), os.listdir(d)]))`);
  assert.deepStrictEqual(r[0], ['sunday', null, null, null, 'sunday', null], 'Nov 22:58Z in, 22:50Z before, 23:36Z after, Monday no; July (EDT) 21:58Z in, 22:58Z after');
  assert.strictEqual(r[1], 0);
  assert.strictEqual(r[3], 12, 'a window of 12 reads in the last 2 minutes');
  assert.strictEqual(r[2], 11, 'one read failed, so one sample fewer');
  assert.strictEqual(r[4], 0);
  assert.strictEqual(r[5], 0);
  assert.ok(r[6], 'header has the flags');
  assert.deepStrictEqual(r[7], ['2026-11-08']);
};

// RB5: the nightly archive records the previous UTC date for the Equities and Indices perps only, spaced at least 1.2 s, keeps only that date's funding rows, stops after three 429s in a row without writing, and does nothing twice.
gates.RB5 = () => {
  const r = py('record_perps_candles.py', `
u = dt.timezone.utc
d = tempfile.mkdtemp()
urls, sleeps = [], []
def get(url):
    urls.append(url)
    if url.endswith('/markets?limit=200'):
        return 200, {"markets": [{"ticker": "KXAAPLPERP", "asset_class": "Equities"}, {"ticker": "KXUS500PERP", "asset_class": "Indices"}, {"ticker": "KXBTCPERP", "asset_class": "Crypto"}, {"ticker": "KXGOLDPERP", "asset_class": "Metals"}]}
    if 'candlesticks' in url:
        return 200, {"candlesticks": [{"end_period_ts": 1794000060, "bid": {"open": "1", "high": "2", "low": "0.5", "close": "1.5"}, "ask": {"close": "1.6"}, "price": {"close": None}, "open_interest": "5", "volume": "7"}]}
    return 200, {"funding_rates": [{"funding_time": "2026-11-06T21:00:00Z", "funding_rate": 0.0002, "mark_price": "6.8"}, {"funding_time": "2026-11-05T21:00:00Z", "funding_rate": 0.0004, "mark_price": "6.9"}]}
now = dt.datetime(2026, 11, 7, 2, 0, 0, tzinfo=u)
a = m.run(d, now, get, sleeps.append)
cr = gzip.open(os.path.join(d, 'kalshi1m', '2026-11-06.csv.gz'), 'rt').read().strip().split('\\n')
fr = gzip.open(os.path.join(d, 'funding', '2026-11-06.csv.gz'), 'rt').read().strip().split('\\n')
n = len(urls)
b = m.run(d, now, get, sleeps.append)
d2 = tempfile.mkdtemp()
def refuse(url): return 429, None
c = m.run(d2, now, refuse, lambda s: None)
e = m.run(tempfile.mkdtemp(), dt.datetime(2027, 3, 1, 2, 0, 0, tzinfo=u), get, lambda s: None)
print(json.dumps([a, len(cr) - 1, len(fr) - 1, n, len(urls) == n, b, c, os.path.exists(os.path.join(d2, 'kalshi1m')), e, min(x for x in sleeps if x >= 1.0) >= 1.2, [x for x in urls if 'KXBTC' in x or 'KXGOLD' in x]]))`);
  assert.strictEqual(r[0], 0);
  assert.strictEqual(r[1], 2, 'one candle for each of the two stock and index markets');
  assert.strictEqual(r[2], 2, 'only the target date funding row, for each of the two');
  assert.strictEqual(r[3], 5, 'one list read, then a candle and a funding read per market');
  assert.strictEqual(r[4], true, 'a second run reads nothing');
  assert.strictEqual(r[5], 0);
  assert.strictEqual(r[6], 1, 'three refusals in a row end the run');
  assert.strictEqual(r[7], false, 'and write nothing');
  assert.strictEqual(r[8], 0, 'past the stop date');
  assert.strictEqual(r[9], true, 'at least 1.2 seconds between calls');
  assert.deepStrictEqual(r[10], [], 'no crypto or metals read');
  const wf = wfs.candles;
  assert.ok(/cron: "0 2,3,4 \* \* 1-6"/.test(wf), 'after the US session, Sunday night to Friday night UTC');
};

// RB6: SOFR is on the daily recorder: KXSOFRD and the NY Fed row, weekdays 09:00 to 13:00 UTC only, stop 2027-02-26; outside the window nothing is read.
gates.RB6 = () => {
  const wl = JSON.parse(rd('kalshi-scalper', 'workers', 'RECDAILY_WATCHLIST.json'));
  const e = wl.watch.find((x) => x.series === 'KXSOFRD');
  assert.ok(e && e.test === 'SOFR1', 'KXSOFRD watched');
  assert.deepStrictEqual(e.utc_hours, [9, 13]);
  assert.strictEqual(e.weekdays_only, true);
  assert.strictEqual(e.stop_date, '2027-02-26');
  const ref = (wl.refs || []).find((x) => x.id === 'NYFED_SOFR');
  assert.ok(ref && /^https:\/\/markets\.newyorkfed\.org\/api\/rates\/secured\/sofr\/last\/1\.json$/.test(ref.url), 'NY Fed row');
  assert.deepStrictEqual(ref.utc_hours, [9, 13]);
  assert.strictEqual(ref.stop_date, '2027-02-26');
  const r = py('record_daily.py', `
d = tempfile.mkdtemp()
wl = ${JSON.stringify(path.join(root, 'kalshi-scalper', 'workers', 'RECDAILY_WATCHLIST.json'))}
log = []
def g(url):
    log.append(url)
    if 'newyorkfed' in url: return 200, {"refRates": [{"effectiveDate": "2026-11-05", "type": "SOFR", "percentRate": 3.92, "percentPercentile1": 3.85, "volumeInBillions": 3256, "revisionIndicator": ""}]}, ''
    return 200, {"markets": [], "cursor": ""}, ''
m._sleep = lambda s: None
t = lambda s: time.mktime(time.strptime(s, '%Y-%m-%dT%H:%M:%S')) - time.timezone
only = lambda: sorted(set(u.split('series_ticker=')[1].split('&')[0] for u in log if 'series_ticker' in u))
m.run(wl, d, t('2026-11-09T12:37:00'), g)
inw = [s for s in only() if s == 'KXSOFRD'], sum('newyorkfed' in u for u in log)
log.clear(); m.run(wl, d, t('2026-11-09T13:07:00'), g); late = 'KXSOFRD' in only(), sum('newyorkfed' in u for u in log)
log.clear(); m.run(wl, d, t('2026-11-07T11:07:00'), g); sat = 'KXSOFRD' in only(), sum('newyorkfed' in u for u in log)
log.clear(); m.run(wl, d, t('2027-03-01T11:07:00'), g); stop = 'KXSOFRD' in only(), sum('newyorkfed' in u for u in log)
log.clear(); m.run(wl, d, t('2026-11-09T05:07:00'), g); early_other = 'KXCPI' in only()
print(json.dumps([inw, late, sat, stop, early_other, os.path.exists(os.path.join(d, 'daily', 'ref', '2026-11-05.csv.gz'))]))`);
  assert.deepStrictEqual(r[0], [['KXSOFRD'], 1], 'Monday 12:37Z reads SOFR and the NY Fed row');
  assert.deepStrictEqual(r[1], [false, 0], 'after 13:00Z nothing');
  assert.deepStrictEqual(r[2], [false, 0], 'Saturday nothing');
  assert.deepStrictEqual(r[3], [false, 0], 'past the stop date nothing');
  assert.strictEqual(r[4], true, 'the other watched series are polled around the clock as before');
  assert.strictEqual(r[5], true, 'the NY Fed row is saved');
};

// RB7: the cash saver (Tuesday to Saturday 02:00 to 04:00 UTC, 2 day range) still saves each US half day and the day around it: for Nov 27 and Dec 24 2026 (and the closed days around them) a start follows the end of after-hours with the half day inside its 2 day range.
gates.RB7 = () => {
  const wf = rd('.github', 'workflows', 'record-perps-cash.yml');
  const m = /cron: "0 ([\d,]+) \* \* ([\d-]+)"/.exec(wf);
  assert.ok(m, 'cron found');
  const hours = m[1].split(',').map(Number);
  const [d0, d1] = m[2].split('-').map(Number);
  const runs = [];
  for (let t = Date.UTC(2026, 10, 25); t < Date.UTC(2027, 0, 5); t += 3600e3) {
    const x = new Date(t);
    if (hours.includes(x.getUTCHours()) && x.getUTCDay() >= d0 && x.getUTCDay() <= d1) runs.push(t);
  }
  // a half day closes 13:00 New York (18:00Z) with after-hours to 17:00 New York (22:00Z); the regular session after-hours ends 20:00 New York (01:00Z next day)
  for (const day of ['2026-11-27', '2026-12-24', '2026-11-30', '2026-12-28']) {
    const open = Date.parse(day + 'T09:00:00Z');   // earliest pre-market bar of that UTC day is after 09:00Z
    const done = Date.parse(day + 'T22:00:00Z') + 3 * 3600e3;   // the latest the day's bars can exist, with a margin past 01:00Z
    const covering = runs.filter((t) => t >= done && t - 48 * 3600e3 <= open);
    assert.ok(covering.length >= 1, day + ' has a start after its bars end, with the day inside the 2 day range');
  }
  assert.ok(/"2d"/.test(rd('scripts', 'record_perps_cash.py')), 'the 2 day range is what covers a dropped night');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

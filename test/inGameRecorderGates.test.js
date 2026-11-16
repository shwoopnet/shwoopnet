'use strict';
// In-game recorder (Nov 8, 2026, research only): NBA moneyline, spread and total markets about every 20 seconds during play, for V2's INGAMELAG1 and SERIESLAG1. It reads public data,
// holds no secret, places no order, writes only to the sports-data branch, is not published with the site and stops by itself on 2027-01-31.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_ingame.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-ingame.yml'), 'utf8');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('ig', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8' }));

// IG1: it can never trade or sign anything, and it reads only the game, spread and total series of the NBA, NHL and NFL.
gates.IG1 = () => {
  const hosts = [...code.matchAll(/https?:\/\/[^"'\s/]+/g)].map((x) => x[0]);
  assert.deepStrictEqual([...new Set(hosts)], ['https://external-api.kalshi.com'], 'the only host is Kalshi public market data');
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=\s*["'](POST|PUT|DELETE)|data\s*=\s*b?["']/i.test(code), 'no key, no auth header, no signing, no write call');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order/.test(code), 'no account or order endpoint');
  assert.deepStrictEqual([...new Set([...code.matchAll(/KX[A-Z0-9]+/g)].map((x) => x[0]))].sort(), ['KXNBAGAME', 'KXNBASPREAD', 'KXNBATOTAL', 'KXNFLGAME', 'KXNFLSPREAD', 'KXNFLTOTAL', 'KXNHLGAME', 'KXNHLSPREAD', 'KXNHLTOTAL']);
  assert.ok(!/^\s*(from|import)\s+[^\n]*functions/m.test(script), 'imports nothing from functions/');
  const fnDir = path.join(root, 'functions');
  assert.deepStrictEqual(fs.readdirSync(fnDir).filter((f) => f.endsWith('.js')).filter((f) => /record_ingame|record-ingame/.test(fs.readFileSync(path.join(fnDir, f), 'utf8'))), [], 'nothing in functions/ mentions it');
  assert.ok(!/record_ingame|record-ingame|sports-data/.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8')), 'the page does not mention it');
};

// IG2: the workflow pushes only the data branch with the built-in token, never overlaps itself and stops for good on 2027-01-31.
gates.IG2 = () => {
  assert.ok(/cron: "7,37 \* \* \* \*"/.test(wf) && /cron: "22,52 \* \* \* \*"/.test(wf) && /--cycle-hours 4/.test(wf), 'triggered every 15 minutes, 4 hour jobs');
  assert.ok(/timeout-minutes: 330/.test(wf), 'a job fits inside the 6 hour limit');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/concurrency:\s*\n\s*group: record-ingame\s*\n\s*cancel-in-progress: false/.test(wf), 'one run at a time, never cancelled');
  assert.ok(/git push -q origin sports-data/.test(wf) && !/origin (main|HEAD)\b/.test(wf) && !/push[^\n]*main/.test(wf), 'pushes only the sports-data branch, never main');
  assert.ok(/2027-01-31T23:59:00Z/.test(wf) && /2027-01-31T23:59:00Z/.test(script), 'stops by itself on 2027-01-31 in the workflow and in the script');
  assert.ok(/ref: main/.test(wf), 'the script is taken from main');
};

// IG3: which markets it follows and how fast it polls.
gates.IG3 = () => {
  const r = py(`
mk = lambda t, b, a: {'ticker': t, 'yes_bid_dollars': b, 'yes_ask_dollars': a}
print(json.dumps({
 'ml': m.choose('ml', [mk('B', '0.4', '0.5'), mk('A', None, None)]),
 'sp': m.choose('spread', [mk('X', '0.40', '0.44'), mk('Y', '0.10', '0.14'), mk('Z', '0.49', '0.51'), {'ticker': 'N'}, mk('W', '0.9', '0.8')]),
 'tie': m.choose('total', [mk('T2', '0.44', '0.48'), mk('T1', '0.44', '0.48'), mk('T3', '0.1', '0.12')]),
 'hot': m.next_poll({'hot_until': 0, 'last_mid': 0.50}, 1000, 0.52), 'calm': m.next_poll({'hot_until': 0, 'last_mid': 0.50}, 1000, 0.51),
 'still': m.next_poll({'hot_until': 5000, 'last_mid': 0.50}, 1000, 0.50), 'nomid': m.next_poll({'hot_until': 0, 'last_mid': None}, 1000, None),
 'mid': [m.mid(mk('a', '0.40', '0.50')), m.mid(mk('a', '0.6', '0.5')), m.mid(mk('a', None, '0.5'))]}))`);
  assert.deepStrictEqual(r.ml, ['A', 'B'], 'the moneyline keeps both teams');
  assert.deepStrictEqual(r.sp, ['Z', 'X'], 'the two nearest 50c, never an unquoted or crossed market');
  assert.deepStrictEqual(r.tie, ['T1', 'T2'], 'ties break on the ticker');
  assert.deepStrictEqual(r.hot, [11800, 20], 'a 2c move starts three hot hours at 20 seconds');
  assert.deepStrictEqual(r.calm, [0, 120], 'a calm book is polled every 2 minutes');
  assert.deepStrictEqual(r.still, [5000, 20], 'a hot game stays hot until its time runs out');
  assert.deepStrictEqual(r.nomid, [0, 120]);
  assert.strictEqual(r.mid[0], 0.45); assert.strictEqual(r.mid[1], null); assert.strictEqual(r.mid[2], null);
};

// IG4: end to end with a fake exchange: one request per event per poll, rows only for the chosen markets, a 429 is counted and backed off, and the end time stops it.
gates.IG4 = () => {
  const r = py(`
import tempfile, os, csv
calls = []
def fetch(url):
    calls.append(url)
    if '/events?' in url:
        s = url.split('series_ticker=')[1].split('&')[0]
        return 200, {'events': [{'event_ticker': s + '-26NOV08LALDET'}]}, 'Sun, 08 Nov 2026 23:44:06 GMT'
    if 'GAME-' in url:
        return 200, {'markets': [{'ticker': 'G-LAL', 'yes_bid_dollars': '0.40', 'yes_ask_dollars': '0.42'}, {'ticker': 'G-DET', 'yes_bid_dollars': '0.58', 'yes_ask_dollars': '0.60'}]}, 'D'
    pre = 'S' if 'SPREAD' in url else 'T'
    ms = [{'ticker': pre + '%d' % i, 'floor_strike': i, 'yes_bid_dollars': '%.2f' % (0.1 * i), 'yes_ask_dollars': '%.2f' % (0.1 * i + 0.02)} for i in range(1, 9)]
    return 200, {'markets': ms}, 'D'
clock = [1000.0]
def now():
    clock[0] += 3.0
    return clock[0]
m.time.sleep = lambda s: None
st = m.Stream(fetch=fetch, clock=now, sleep=lambda s: None)
d = tempfile.mkdtemp()
m.run(d, 4, stream=st, now_fn=now)
rows = list(csv.reader(open(os.path.join(d, 'obs.csv'))))
cov = list(csv.reader(open(os.path.join(d, 'coverage.csv'))))
ev = [c for c in calls if '/events?' in c]
mk = [c for c in calls if '/markets?event_ticker=' in c]
print(json.dumps({'hdr': rows[0], 'n': len(rows) - 1, 'tickers': sorted({r[4] for r in rows[1:]}), 'kinds': sorted({r[3] for r in rows[1:]}), 'ev': len(ev), 'mk': len(mk), 'cov': cov[1:], 'posts': [c for c in calls if 'POST' in c]}))`);
  assert.deepStrictEqual(r.hdr, ['t_recv_ms', 'server_date', 'event', 'kind', 'ticker', 'strike', 'yes_bid', 'yes_ask', 'bid_size', 'ask_size', 'last_price', 'volume']);
  assert.ok(r.n > 0 && r.ev >= 3 && r.mk >= 3, JSON.stringify(r));
  assert.deepStrictEqual(r.kinds, ['ml', 'spread', 'total']);
  assert.ok(r.tickers.includes('G-LAL') && r.tickers.includes('G-DET'), 'both moneyline teams recorded');
  assert.strictEqual(r.tickers.filter((t) => /^[ST]\d$/.test(t)).length, 4, 'two spread and two total markets are followed, not all eight (the same chosen set for every sport)');
  assert.ok(r.cov.length === 1 && Number(r.cov[0][1]) >= 3, 'a coverage row for the game');
};

// IG5 (Nov 16, 2026, the Head of R&D's go): the request budget. A calm game reads its moneyline every poll but its spread and total only every 5 minutes; a game whose price moves 2c on ANY followed market is hot and reads all three every poll; moves are compared by ticker.
gates.IG5 = () => {
  const r = py(`
import tempfile
def go(prices):
    calls = []
    def fetch(url):
        calls.append(url)
        if '/events?' in url:
            s = url.split('series_ticker=')[1].split('&')[0]
            return 200, {'events': [{'event_ticker': s + '-26NOV08LALDET'}]}, 'D'
        if 'GAME-' in url:
            p = prices(len(calls))
            return 200, {'markets': [{'ticker': 'G-LAL', 'yes_bid_dollars': '%.2f' % p, 'yes_ask_dollars': '%.2f' % (p + 0.02)}, {'ticker': 'G-DET', 'yes_bid_dollars': '0.58', 'yes_ask_dollars': '0.60'}]}, 'D'
        pre = 'S' if 'SPREAD' in url else 'T'
        return 200, {'markets': [{'ticker': pre + '%d' % i, 'floor_strike': i, 'yes_bid_dollars': '%.2f' % (0.1 * i), 'yes_ask_dollars': '%.2f' % (0.1 * i + 0.02)} for i in range(1, 9)]}, 'D'
    clock = [1000.0]
    def now():
        clock[0] += 3.0
        return clock[0]
    m.time.sleep = lambda s: None
    st = m.Stream(fetch=fetch, clock=now, sleep=lambda s: None)
    m.run(tempfile.mkdtemp(), 4, stream=st, now_fn=now)
    mk = [c for c in calls if '/markets?event_ticker=' in c]
    return {'ml': len([c for c in mk if 'GAME-' in c]), 'sp': len([c for c in mk if 'SPREAD-' in c]), 'tot': len([c for c in mk if 'TOTAL-' in c])}
calm = go(lambda n: 0.40)
moving = go(lambda n: 0.40 if n % 2 else 0.45)
print(json.dumps({'calm': calm, 'moving': moving, 'moved': [m.any_moved({'A': 0.50}, {'A': 0.52}), m.any_moved({'A': 0.50}, {'B': 0.90}), m.any_moved({'A': 0.50}, {'A': 0.51}), m.any_moved({}, {'A': None})],
  'due': [m.side_due({'hot_until': 0, 'side_due': 0}, 10), m.side_due({'hot_until': 0, 'side_due': 400}, 100), m.side_due({'hot_until': 5000, 'side_due': 400}, 100), m.side_due({'hot_until': 0, 'side_due': 400}, 400)]}))`);
  assert.ok(r.calm.ml >= 20, JSON.stringify(r.calm));
  assert.ok(r.calm.sp >= 1 && r.calm.sp * 2 < r.calm.ml, 'a calm game reads its spread far less often than its moneyline: ' + JSON.stringify(r.calm));
  assert.strictEqual(r.calm.sp, r.calm.tot);
  assert.ok(r.moving.ml - r.moving.sp <= 2 && r.moving.sp === r.moving.tot, 'a moving game is hot and reads all three kinds at every poll after the move that made it hot: ' + JSON.stringify(r.moving));
  assert.deepStrictEqual(r.moved, [true, false, false, false], 'moves are compared by ticker, a 1c step or a missing quote is no move');
  assert.deepStrictEqual(r.due, [true, false, true, true], 'the first poll reads all three, a hot game always, a cold one when its 5 minutes are up');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

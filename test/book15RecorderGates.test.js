'use strict';
// The 15 minute order book recorder (Oct 29, 2026, research only, R2 for MM1): it reads public data, holds no secret, places no order, writes only to a data branch and is not published with the site.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'scripts', 'record_book15.py'), 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-book15.yml'), 'utf8');
const gates = {};
const py = (code) => execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('rb', ${JSON.stringify(path.join(root, 'scripts', 'record_book15.py'))}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${code}`], { encoding: 'utf8' });
const bare = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');

// C1: it can never trade or sign anything, and the series list is fixed in code.
gates.C1 = () => {
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2/.test(bare), 'it reads Kalshi public market data');
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=\s*["'](POST|PUT|DELETE)/i.test(bare), 'no key, no signing, no write call');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order/.test(bare.replace(/\/orderbook/g, '')), 'no account or order endpoint (the public order book is not an order)');
  assert.ok(!/os\.environ|getenv/.test(bare), 'nothing is read from the environment, so no secret can reach it');
  assert.deepStrictEqual(JSON.parse(py('print(json.dumps(list(m.SERIES)))')), ['KXBTC15M', 'KXETH15M', 'KXGOLD15M'], 'exactly these three series, fixed in code');
  assert.ok(!/KXBTCD|KXXRP|KXDOGE|KXNATGAS|KXAUD|KXUSDCAD/.test(bare), 'no other series');
  assert.ok(!/add_argument\("--(series|ticker)/.test(bare), 'no command line option can change the series');
};

// C2: the workflow pushes only the data branch, uses only the built-in token, and each job fits inside the 6 hour limit.
gates.C2 = () => {
  assert.ok(/cron: "44 3,7,11,15,19,23 \* \* \*"/.test(wf) && /--cycle-hours 4/.test(wf), 'six 4 hour jobs a day');
  const book = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-book.yml'), 'utf8');
  assert.ok(/cron: "50 /.test(book) && !/cron: "44 /.test(book), 'a different start minute from record-book');
  assert.ok(/timeout-minutes: 330/.test(wf), 'a job fits inside the 6 hour limit');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.ok(!/HEAD:main|refs\/heads\/main/.test(wf), 'no route to main');
  assert.ok(/ref: main\s*\n\s*path: code/.test(wf), 'main is only read, into code/, never the place data is committed');
  assert.ok(/mkdir -p "data\/book15\//.test(wf) && /git add book15/.test(wf), 'only book15/ is added');
  assert.ok(/permissions:\s*\n\s*contents: write/.test(wf), 'contents write and nothing wider');
  assert.ok(/cancel-in-progress: false/.test(wf), 'two runs never overlap');
};

// C3: neither the workflow nor the script is published with the site.
gates.C3 = () => {
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'neither the workflow nor the script is published with the site');
  assert.ok(!fs.existsSync(path.join(root, 'book15')), 'no data directory on the main branch');
};

// C4: rows mean what the research session reads them as: levels best first, as numbers, a missing level empty (never zero), series and server date kept.
gates.C4 = () => {
  const out = JSON.parse(py(`
resp = {"orderbook_fp": {"no_dollars": [["0.4600", "1827.29"], ["0.4700", "25276.57"], ["0.5000", "527.34"]], "yes_dollars": [["0.4500", "200.00"], ["0.4900", "6227.00"]]}}
row = m.book_row(111, "Thu, 29 Oct 2026 00:07:02 GMT", "KXGOLD15M", {"ticker": "T", "close_time": "X"}, resp)
print(json.dumps({"cols": len(m.BOOK_COLS), "row": row, "none": m.book_row(1, "d", "S", {}, {}), "junk": m.book_row(1, "d", "S", {}, None)}))`));
  assert.strictEqual(out.cols, out.row.length, 'one value per column');
  assert.deepStrictEqual(out.row.slice(0, 5), [111, 'Thu, 29 Oct 2026 00:07:02 GMT', 'KXGOLD15M', 'T', 'X']);
  assert.deepStrictEqual(out.row.slice(5, 10), [0.49, 0.45, '', '', ''], 'YES bid prices best first, missing levels empty');
  assert.deepStrictEqual(out.row.slice(10, 15), [6227, 200, '', '', ''], 'and their sizes');
  assert.deepStrictEqual(out.row.slice(15, 20), [0.5, 0.47, 0.46, '', ''], 'NO bids best first');
  assert.strictEqual(out.none, null, 'no book is no row');
  assert.strictEqual(out.junk, null, 'a failed read is no row');
};

// C5: the market is chosen by its close time alone, never by price or outcome.
gates.C5 = () => {
  const out = JSON.parse(py(`
ms = [{"ticker": "A", "close_time": "C1", "yes_bid_dollars": "0.99"}, {"ticker": "B", "close_time": "C2", "yes_bid_dollars": "0.01"}]
print(json.dumps([m.pick_closing(ms, "C2")["ticker"], m.pick_closing(ms, "C3"), m.iso(900)]))`));
  assert.deepStrictEqual(out, ['B', null, '1970-01-01T00:15:00Z']);
  assert.ok(!/yes_bid_dollars|floor_strike|result/.test(bare), 'no price or outcome field enters the choice of market');
};

// C6: the whole window is recorded, every 3 seconds, and a refused read backs off.
gates.C6 = () => {
  const out = JSON.parse(py('print(json.dumps([m.WINDOW_S, m.BOOK_EVERY_S, m.TRADES_EVERY_S, m.DEPTH, m.BACKOFF_S]))'));
  assert.deepStrictEqual(out, [900, 3, 30, 5, 2]);
  assert.ok(/st == 429[\s\S]{0,120}time\.sleep\(BACKOFF_S\)/.test(bare), 'a 429 sleeps before the next read');
};

// C7: back to back jobs leave no gap: the stop time is a minute past a boundary that leaves a full cycle.
gates.C7 = () => {
  const out = JSON.parse(py(`print(json.dumps([m.cycle_stop_time(14400 * 5 + 1000, 14400), m.cycle_stop_time(14400 * 5 + 13000, 14400)]))`));
  assert.deepStrictEqual(out, [14400 * 6 + 60, 14400 * 7 + 60]);
};

// C8: a trade read twice (the tape is read with overlap) is written once, and carries the server date and series.
gates.C8 = () => {
  const out = JSON.parse(py(`
seen = set()
t = [{"ticker": "T", "trade_id": "a", "created_time": "x", "yes_price_dollars": "0.5", "count_fp": "1", "taker_outcome_side": "yes"}]
r1 = m.trade_rows(1, "D", "KXBTC15M", t, seen)
print(json.dumps([len(r1), len(m.trade_rows(2, "D", "KXBTC15M", t, seen)), len(m.trade_rows(3, "D", "KXBTC15M", t + [dict(t[0], trade_id="b")], seen)), r1[0][:4], len(r1[0]) == len(m.TRADE_COLS)]))`));
  assert.deepStrictEqual(out, [1, 0, 1, [1, 'D', 'KXBTC15M', 'T'], true]);
};

for (const [name, fn] of Object.entries(gates)) { fn(); console.log('ok   ' + name); }

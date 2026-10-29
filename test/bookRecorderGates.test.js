'use strict';
// The order book recorder (Oct 29, 2026, research only, QUOTE2B): it reads public data, holds no secret, places no order, writes only to a data branch and is not published with the site.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'scripts', 'record_book.py'), 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-book.yml'), 'utf8');
const gates = {};
const py = (code) => execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('rb', ${JSON.stringify(path.join(root, 'scripts', 'record_book.py'))}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${code}`], { encoding: 'utf8' });

// B1: it can never trade or sign anything, whatever it is changed into.
gates.B1 = () => {
  const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2/.test(code), 'it reads Kalshi public market data');
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=\s*["'](POST|PUT|DELETE)/i.test(code), 'no key, no signing, no write call');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order/.test(code.replace(/\/orderbook/g, '')), 'no account or order endpoint (the public order book is not an order)');
  assert.ok(/KXBTCD/.test(code) && !/KXBTC15M|KXETH|KXGOLD|KXXRP|KXDOGE/.test(code), 'only the Bitcoin hourly ladder, nothing the live bot trades');
};

// B2: the workflow pushes only the data branch, uses only the built-in token, and each job fits inside the 6 hour limit.
gates.B2 = () => {
  assert.ok(/cron: "50 3,7,11,15,19,23 \* \* \*"/.test(wf) && /--cycle-hours 4/.test(wf), 'six 4 hour jobs a day, each starting 10 minutes before a boundary');
  assert.ok(/timeout-minutes: 330/.test(wf), 'a job fits inside the 6 hour limit');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.ok(/permissions:\s*\n\s*contents: write/.test(wf), 'contents write and nothing wider');
  assert.ok(/cancel-in-progress: false/.test(wf), 'two runs never overlap');
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'neither the workflow nor the script is published with the site');
};

// B3: rows mean what the research session reads them as: levels best first, as numbers, a missing level empty (never zero), the server date kept for clock skew.
gates.B3 = () => {
  const out = JSON.parse(py(`
resp = {"orderbook_fp": {"no_dollars": [["0.4600", "1827.29"], ["0.4700", "25276.57"], ["0.5000", "527.34"]], "yes_dollars": [["0.4500", "200.00"], ["0.4900", "6227.00"]]}}
row = m.book_row(111, "Thu, 29 Oct 2026 00:07:02 GMT", {"ticker": "T", "floor_strike": 81249.99, "close_time": "X"}, resp)
print(json.dumps({"cols": len(m.BOOK_COLS), "row": row, "none": m.book_row(1, "d", {}, {}), "junk": m.book_row(1, "d", {}, None)}))`));
  assert.strictEqual(out.cols, out.row.length, 'one value per column');
  assert.deepStrictEqual(out.row.slice(0, 5), [111, 'Thu, 29 Oct 2026 00:07:02 GMT', 'T', 81249.99, 'X']);
  assert.deepStrictEqual(out.row.slice(5, 10), [0.49, 0.45, '', '', ''], 'YES bid prices best first, missing levels empty');
  assert.deepStrictEqual(out.row.slice(10, 15), [6227, 200, '', '', ''], 'and their sizes');
  assert.deepStrictEqual(out.row.slice(15, 20), [0.5, 0.47, 0.46, '', ''], 'NO bids best first');
  assert.strictEqual(out.none, null, 'no book is no row');
  assert.strictEqual(out.junk, null, 'a failed read is no row');
};

// B4: the strikes are chosen by cost-free price information only (the bid nearest 50c), 7 of them, for the right close, never one with no bid.
gates.B4 = () => {
  const out = JSON.parse(py(`
ms = [{"ticker": "A%d" % i, "close_time": "C", "floor_strike": 100 + i, "yes_bid_dollars": str(0.05 + 0.1 * i)} for i in range(10)]
ms.append({"ticker": "OTHER", "close_time": "D", "floor_strike": 1, "yes_bid_dollars": "0.50"})
ms.append({"ticker": "NOBID", "close_time": "C", "floor_strike": 2, "yes_bid_dollars": "0.0000"})
print(json.dumps([x["ticker"] for x in m.pick_near_money(ms, "C")]))`));
  assert.strictEqual(out.length, 7);
  assert.ok(!out.includes('OTHER') && !out.includes('NOBID'), 'only the closing event, only quoted markets');
  assert.deepStrictEqual(out.slice(0, 2).sort(), ['A4', 'A5'], 'the bids nearest 50c come first');
};

// B5: back to back jobs leave no gap: the stop time is a minute past a boundary that leaves a full cycle.
gates.B5 = () => {
  const out = JSON.parse(py(`print(json.dumps([m.cycle_stop_time(14400 * 5 + 1000, 14400), m.cycle_stop_time(14400 * 5 + 13000, 14400)]))`));
  assert.deepStrictEqual(out, [14400 * 6 + 60, 14400 * 7 + 60]);
};

// B6: a trade read twice (the tape is read with overlap) is written once.
gates.B6 = () => {
  const out = JSON.parse(py(`
seen = set()
t = [{"ticker": "T", "trade_id": "a", "created_time": "x", "yes_price_dollars": "0.5", "count_fp": "1", "taker_outcome_side": "yes"}]
print(json.dumps([len(m.trade_rows(1, t, seen)), len(m.trade_rows(2, t, seen)), len(m.trade_rows(3, t + [dict(t[0], trade_id="b")], seen))]))`));
  assert.deepStrictEqual(out, [1, 0, 1]);
};

for (const [name, fn] of Object.entries(gates)) { fn(); console.log('ok   ' + name); }

'use strict';
// PL1 to PL8: the perps live recorder (Nov 16, 2026, research only). Public GET only, its own data branch, stops by itself, and the script behaves on fixtures with no network.
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const root = path.join(__dirname, '..');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-perps-live.yml'), 'utf8');
const py = fs.readFileSync(path.join(root, 'scripts', 'record_perps_live.py'), 'utf8');
const code = py.split('\n').filter((l) => !/^\s*#/.test(l)).join('\n');

// PL1: no secret but the built-in token, never main, its own orphan branch, six push tries, stops on 2027-02-26.
assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'PL1 no secret but the built-in token');
assert.ok(!/git push[^\n]*\bmain\b/.test(wf), 'PL1 never pushes main');
assert.ok(/git fetch -q --depth 1 origin perp-live-data/.test(wf) && /--orphan perp-live-data/.test(wf), 'PL1 its own orphan data branch');
assert.ok(/for i in 1 2 3 4 5 6; do git push -q origin perp-live-data && exit 0/.test(wf), 'PL1 six push tries');
assert.ok(/2027-02-26T23:59:00Z/.test(wf) && /2027-02-26T23:59:00Z/.test(py), 'PL1 stop date in the workflow and in the script');
assert.ok(/concurrency:\s+group: record-perps-live\s+cancel-in-progress: false/.test(wf), 'PL1 one concurrency group that never cancels a running job');
assert.ok(/permissions:\s+contents: write\s/.test(wf) && !/pull-requests|id-token|actions:/.test(wf), 'PL1 minimal permissions');
assert.ok(/actions\/checkout@[0-9a-f]{40}/.test(wf) && /ref: main/.test(wf), 'PL1 pinned checkout of main');
assert.ok(/python3 code\/scripts\/record_perps_live\.py "data\/perplive\/\$STAMP" --cycle-hours 4/.test(wf), 'PL1 runs only its own script');
console.log('ok   PL1 workflow');

// PL2: public GET only.
assert.ok(/BASE = "https:\/\/external-api\.kalshi\.com\/trade-api\/v2\/margin"/.test(code), 'PL2 one host, the margin base');
assert.ok(!/Authorization|KALSHI-ACCESS|method=|data=|\.post\(|POST|portfolio|orders\/|api_key|secret|os\.environ/i.test(code.replace(/"orderbooks"|\/markets\/orderbooks/g, '')), 'PL2 no auth header, no POST, no account path, no environment');
assert.ok(/class NoRedirect/.test(code) && /return None/.test(code), 'PL2 redirects refused');
assert.ok(/UA = \{"User-Agent": "shwoopnet-research-recorder"\}/.test(code), 'PL2 generic user agent, no contact details');
const paths = [...code.matchAll(/\bget\("(\/[^"]+)/g)].map((m) => m[1]);
assert.deepStrictEqual([...new Set(paths)].sort(), ['/markets', '/markets/orderbooks?tickers='].sort(), 'PL2 only the list and the multi orderbooks paths are requested');
console.log('ok   PL2 public GET only');

// PL3: pacing constants.
assert.ok(/MIN_GAP_S = 5\.0/.test(code) && /POLL_EVERY_S = 60/.test(code) && /BOOK_BATCH_MAX = 100/.test(code) && /BACKOFF_S, BACKOFF_MAX_S, MAX_429_IN_ROW = 5\.0, 60\.0, 3/.test(code), 'PL3 5 s between requests, every 60 s, 100 tickers a batch, three 429s end the run');
assert.ok(/REQUEST_BUDGET = 2 \* \(4 \* 60 \+ 90\)/.test(code), 'PL3 a hard request budget per run');
console.log('ok   PL3 pacing');

// PL4 to PL7: behaviour on fixtures with no network (get is replaced; the opener raises if anything reaches it).
const t = fs.mkdtempSync(path.join(os.tmpdir(), 'plive-'));
const prog = `
import sys, os, json, csv, time
sys.path.insert(0, ${JSON.stringify(path.join(root, 'scripts'))})
import record_perps_live as R
class Boom:
    def open(self, *a, **k): raise AssertionError("network used")
R.OPENER = Boom()
R.MIN_GAP_S = 0.0; R.POLL_EVERY_S = 0.3; R.BACKOFF_S = 0.01
calls = []
mk = [{"ticker": "KXAAAPERP", "asset_class": "Equities", "status": "active", "bid": "10.00", "ask": "10.02", "bid_size_fp": "5", "ask_size_fp": "6", "price": "10.01", "reference_price": "10.00", "settlement_mark_price": "10.01", "liquidation_mark_price": "10.02", "open_interest": "123", "volume_24h": "456", "leverage_estimate": 4.9},
      {"ticker": "KXBBBPERP", "asset_class": "Crypto", "status": "inactive", "bid": "0", "ask": "0"}]
def fake(path):
    calls.append(path)
    if path == "/markets": return 200, {"markets": mk}, "Mon, 16 Nov 2026 12:00:00 GMT", 1, 2
    assert path.startswith("/markets/orderbooks?tickers=KXAAAPERP") and "KXBBBPERP" not in path, path
    return 200, {"orderbooks": [{"ticker": "KXAAAPERP", "orderbook": {"bids": [["10.0000", "5.00"], ["9.9900", "7.00"]], "asks": [["10.0200", "6.00"]]}}]}, "Mon, 16 Nov 2026 12:00:00 GMT", 3, 4
R.get = fake
out = sys.argv[1]
R.main([out, "--cycle-hours", "0.0008"])
rows = list(csv.reader(open(os.path.join(out, "markets.csv"))))
assert rows[0] == R.MARKET_COLS and rows[1][3] == "KXAAAPERP" and rows[1][6] == "10.0" and rows[1][16] == "4.9" and any(r[3] == "KXBBBPERP" for r in rows), rows[:3]
b = list(csv.reader(open(os.path.join(out, "book.csv"))))
assert b[0] == R.BOOK_COLS and b[1][3] == "KXAAAPERP" and b[1][4] == "10.0" and b[1][5] == "9.99" and b[1][6] == "" and b[1][9] == "5.0" and b[1][10] == "7.0" and b[1][11] == "" and b[1][14] == "10.02" and b[1][15] == "" and b[1][19] == "6.0" and b[1][20] == "", b[:2]
c = list(csv.reader(open(os.path.join(out, "coverage.csv"))))
assert c[0] == R.COVER_COLS and len(c) >= 2 and c[1][1] == "1" and c[1][3] == "1", c
assert all(p == "/markets" or p.startswith("/markets/orderbooks") for p in calls) and len(calls) <= R.REQUEST_BUDGET
print("fixture ok", len(rows) - 1, "market rows", len(b) - 1, "book rows", len(calls), "requests")
`;
let r = spawnSync('python3', ['-I', '-c', prog, path.join(t, 'a')], { encoding: 'utf8' });
assert.strictEqual(r.status, 0, 'PL4 fixture run: ' + r.stderr + r.stdout);
console.log('ok   PL4 to PL6 rows, depth, inactive markets kept in the list but not in the book, no network');

// PL7: three 429s in a row end the run, and a run after the end date records nothing.
const prog2 = `
import sys, os, csv
sys.path.insert(0, ${JSON.stringify(path.join(root, 'scripts'))})
import record_perps_live as R
R.MIN_GAP_S = 0.0; R.POLL_EVERY_S = 0.05; R.BACKOFF_S = 0.01
n = []
def fake(path): n.append(path); return 429, None, "", 1, 2
R.get = fake
R.main([sys.argv[1], "--cycle-hours", "0.01"])
assert len(n) == 3, n
c = list(csv.reader(open(os.path.join(sys.argv[1], "coverage.csv")))); assert "three 429s" in c[-1][-1], c
R.END_UTC = "2020-01-01T00:00:00Z"
n.clear(); assert R.main([sys.argv[1] + "x"]) == 0 and not n and not os.path.exists(sys.argv[1] + "x")
print("429 and end date ok")
`;
r = spawnSync('python3', ['-I', '-c', prog2, path.join(t, 'b')], { encoding: 'utf8' });
assert.strictEqual(r.status, 0, 'PL7 ' + r.stderr + r.stdout);
console.log('ok   PL7 three 429s end the run; nothing is recorded after the end date');

// PL8: it only writes its three csv files in the directory it is given.
assert.deepStrictEqual(fs.readdirSync(path.join(t, 'a')).sort(), ['book.csv', 'coverage.csv', 'markets.csv'], 'PL8 three files');
console.log('ok   PL8 outputs');

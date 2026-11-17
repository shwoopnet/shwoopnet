const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
function lift(name) {   // the source of one top level page function, by balanced braces
  const i = html.indexOf('function ' + name + '(');
  assert(i >= 0, 'function ' + name + ' exists');
  let depth = 0, j = html.indexOf('{', i), k = j;
  for (; k < html.length; k++) { if (html[k] === '{') depth++; else if (html[k] === '}') { depth--; if (depth === 0) break; } }
  return html.slice(i, k + 1);
}
const names = ['kalshiStratAccount', 'kalshiPerpClosedRows', 'kalshiPerpTradeRowHtml', 'kalshiStratAccountChip'];
const Q = new Function(names.map(lift).join('\n') + '\nreturn {' + names.join(',') + '};')();
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const money = (v) => '$' + Number(v).toFixed(2);
const mask = () => '****';
const when = (ms) => 'T' + ms;

// PD1: the Strategies total is the live prediction balance, else the newest hourly snapshot (with its time), plus the perps equity only when it is fresh; no prediction balance, no total
assert.deepStrictEqual(Q.kalshiStratAccount({ balance: { ok: true, totalDollars: 200 } }, { t: 5, pred: 150 }, 600), { total: 800, perps: true, asOf: null });
assert.deepStrictEqual(Q.kalshiStratAccount(null, { t: 5000, pred: 150.4 }, 600), { total: 750.4, perps: true, asOf: 5000 });
assert.deepStrictEqual(Q.kalshiStratAccount({ balance: { ok: false } }, { t: 5, pred: 150 }, null), { total: 150, perps: false, asOf: 5 });
assert.deepStrictEqual(Q.kalshiStratAccount(null, null, 600), { total: null, perps: false, asOf: null }, 'never a perps only figure');
assert.deepStrictEqual(Q.kalshiStratAccount({ balance: { ok: true, totalDollars: 200 } }, null, undefined), { total: 200, perps: false, asOf: null });
assert.strictEqual(Q.kalshiStratAccount(null, { t: 5, pred: null }, 600).total, null);

// PD2: the tile says what it holds, and Privacy view masks the dollars
let h = Q.kalshiStratAccountChip({ total: 800, perps: true, asOf: null }, 3, esc, money);
assert(/Account total/.test(h) && /\$800\.00/.test(h) && /predictions \+ perps/.test(h));
h = Q.kalshiStratAccountChip({ total: 750.4, perps: false, asOf: Date.parse('2026-11-17T18:00:00Z') }, 3, esc, money);
assert(/predictions only/.test(h) && /hourly, 12:00 PM/.test(h), 'a snapshot total says when it was taken, in Central: ' + h);
assert(/n\/a/.test(Q.kalshiStratAccountChip({ total: null }, 3, esc, money)) && /not loaded yet/.test(Q.kalshiStratAccountChip(undefined, 3, esc, money)));
assert(/\*\*\*\*/.test(Q.kalshiStratAccountChip({ total: 800, perps: true }, 3, esc, mask)) && !/800/.test(Q.kalshiStratAccountChip({ total: 800, perps: true }, 3, esc, mask)), 'Privacy view masks the total');

// PD3: only CLOSES become trade rows, newest first; a row says it is the last profit SEEN, not a result, and Privacy masks the dollars
const ev = [{ at: 3, market: 'KXA', kind: 'opened' }, { at: 5, market: 'KXB', kind: 'closed', up: true, prevSize: 2, lastPnl: -3.25 }, { at: 9, market: 'KXC', kind: 'closed', up: false, prevSize: 1.5, lastPnl: 4 }, { at: 7, market: 'KXD', kind: 'reduced' }, null, { at: 'x', market: 'KXE', kind: 'closed' }, { at: 8, market: '', kind: 'closed' }];
const rows = Q.kalshiPerpClosedRows(ev);
assert.deepStrictEqual(rows.map((r) => r.market), ['KXC', 'KXB']);
assert.deepStrictEqual(Q.kalshiPerpClosedRows(null), []);
h = Q.kalshiPerpTradeRowHtml(rows[1], esc, money, when);
assert(/Closed UP 2/.test(h) && /-\$3\.25/.test(h) && /last seen/.test(h) && /kal-neg/.test(h) && /Perp/.test(h) && /seen at the next 5 minute read/.test(h) && /T5/.test(h));
h = Q.kalshiPerpTradeRowHtml(rows[0], esc, money, when);
assert(/Closed DOWN 1\.5/.test(h) && /\+\$4\.00/.test(h) && /kal-pos/.test(h));
assert(/\*\*\*\*/.test(Q.kalshiPerpTradeRowHtml(rows[0], esc, mask, when)) && !/4\.00/.test(Q.kalshiPerpTradeRowHtml(rows[0], esc, mask, when)));
assert(/last seen n\/a/.test(Q.kalshiPerpTradeRowHtml({ at: 1, market: 'KXF', kind: 'closed', up: true, lastPnl: null }, esc, money, when)));
assert(/&lt;b&gt;/.test(Q.kalshiPerpTradeRowHtml({ at: 1, market: '<b>', kind: 'closed', up: true }, esc, money, when)), 'every value is escaped');

// PD4: wiring. The read is one plain query of the events collection (no write), the Recent trades merge skips them in the settled totals, the Strategies render asks for the perps data and the tile is the last of the grid
assert(/readKalshiPerpsEvents: function\(\)\{\s*return getDocs\(query\(collection\(db, 'kalshiPerpsEvents'\), orderBy\('at', 'desc'\), limit\(60\)\)\)/.test(html), 'PD4 one read, no write');
assert(!/setDoc\([^)]*kalshiPerpsEvents|addDoc\([^)]*kalshiPerpsEvents/.test(html), 'PD4 the page never writes events');
assert(/if\(item\.perp\)\{ return kalshiPerpTradeRowHtml\(item\.perp, escapeHtml, kalshiMoney, kalshiHoverWhen\); \}/.test(html), 'PD4 a perp row is drawn before the settled count code can see it');
assert(/kalshiPerpsEnsure\(\);\s*var perpsRes = kalshiPerpsFromDoc\(kalshiPerpsState\.doc, now\);\s*summary\.account = kalshiStratAccount\(/.test(html), 'PD4 the Strategies page reads the perps data');
assert(/kalshiStratAccountChip\(s\.account, ci\+\+, esc, money\) \+ '<\/div><\/div>';/.test(html), 'PD4 the tile sits inside the card grid');
// the risk code never sees the page total: this file is page code, and the functions folder never names the page helpers
for (const f of fs.readdirSync(__dirname + '/../functions').filter((x) => x.endsWith('.js'))) assert(!/kalshiStratAccount|kalshiPerpClosedRows/.test(fs.readFileSync(__dirname + '/../functions/' + f, 'utf8')), 'PD4 ' + f + ' does not name the page helpers');
console.log('perpsPageGates ok');

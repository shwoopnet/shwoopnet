'use strict';
// TM1 to TM8: the terminal / data layout of the Strategies page (Nov 10, 2026, the owner: the animated page was "bland and boring"; keep a terminal feel, much richer, strictly inside the site's theme).
// Consequence: a block sparkline, a health bar, a heat grid day or a tape line is the figure the orders give (in Central days, across a daylight saving change); no dollar figure is typed or unmasked;
// a value from the log can never become markup; nothing continuous runs except the one small live dot, and that is off under reduced motion.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const gates = {};
function fn(name) {
  const at = html.indexOf('  function ' + name + '(');
  assert.ok(at >= 0, name + ' is in the page');
  let i = html.indexOf('{', at), depth = 0, q = null;
  for (; i < html.length; i++) {
    const c = html[i];
    if (q) { if (c === '\\') i++; else if (c === q) q = null; continue; }
    if (c === "'" || c === '"') { q = c; continue; }
    if (c === '/' && html[i + 1] === '/') { i = html.indexOf('\n', i); continue; }
    if (c === '{') depth++;
    if (c === '}') { depth--; if (depth === 0) break; }
  }
  return html.slice(at, i + 1);
}
const varLine = (name) => { const m = new RegExp('  var ' + name + ' = .*\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const varBlock = (name) => { const m = new RegExp('  var ' + name + ' = [\\[{][\\s\\S]*?\\n  [\\] }]+;\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const names = ['kalshiBoardFillCost', 'kalshiBoardCash', 'kalshiBoardRows', 'kalshiBoardPf', 'kalshiBoardPfText', 'kalshiStratR', 'kalshiStratPfAttr', 'kalshiStratSpark', 'kalshiStratArc', 'kalshiStratGauge', 'kalshiStratLifecycle', 'kalshiStratBlocks', 'kalshiStratTextBar', 'kalshiStratHealth', 'kalshiStratDayKeys', 'kalshiStratHeat', 'kalshiStratTape', 'kalshiStratSummaryHtml', 'kalshiStratDetailHtml', 'kalshiStratShadowDetailHtml', 'kalshiStratCumLine', 'kalshiBoardHtml'];
const src = varLine('KAL_BOARD_TRIPWIRE') + varLine('KAL_BOARD_KILL') + varBlock('KAL_BOARD_LIVE') + varLine('KAL_BOARD_SHADOW_RULES') + varBlock('KAL_BOARD_SHADOW') + varBlock('KAL_BOARD_RETIRED') + varLine('KAL_BOARD_LADDER') + varLine('KAL_STRAT_BLOCKS') + varLine('kalshiStratDayText') + names.map(fn).join('\n');
const T = new Function('Math', 'Number', 'Array', 'isFinite', 'Intl', 'Date', 'Object', 'String', src + '; return { ' + names.join(', ') + ', KAL_STRAT_BLOCKS, KAL_BOARD_LIVE, KAL_BOARD_SHADOW, KAL_BOARD_RETIRED };')(Math, Number, Array, isFinite, Intl, Date, Object, String);
const money = (x) => (x < 0 ? '-' : '') + '$' + Math.abs(x).toFixed(2);
const mask = (x) => (x < 0 ? '-' : '') + '****';
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => '&#' + c.charCodeAt(0) + ';');
const CT = (ms) => new Date(ms).toLocaleDateString('en-CA', { timeZone: 'America/Chicago' });
const HR = 3600000, DAY = 86400000;
const order = (ts, won, extra) => Object.assign({ ts, side: 'yes', count: 10, fillCount: 10, maxCost: 9.1, averageFillPrice: 0.9, averageFeePaid: 0.0055, settled: true, result: won ? 'yes' : 'no', ticker: 'KXGOLD15M-26NOV10', strategy: 'L1' }, extra || {});

gates.TM1 = () => {
  // eight levels of block characters on the same range as the line (0.5 to 1.5 at least), padded to a fixed width, nothing for no data
  assert.strictEqual(T.KAL_STRAT_BLOCKS, '▁▂▃▄▅▆▇█');
  assert.strictEqual(T.kalshiStratBlocks([0.5, 1.5], 2), '▁█', 'the bottom and the top of the range');
  assert.strictEqual(T.kalshiStratBlocks([1.0], 1), '▅', '1.0 sits in the middle of the range');
  assert.strictEqual(T.kalshiStratBlocks([0.5, 0.75, 1.0, 1.25, 1.5], 5), '▁▃▅▇█');
  assert.strictEqual(T.kalshiStratBlocks([3, 0], 2), '█▁', 'a wider series stretches the range');
  assert.strictEqual(T.kalshiStratBlocks([1, 1, 1], 5), '··▅▅▅', 'short series are padded on the left');
  assert.strictEqual(T.kalshiStratBlocks([], 4), '····', 'no data is dots only');
  assert.strictEqual(T.kalshiStratBlocks(['x', NaN, 1.5], 3), '··█', 'non numbers are dropped');
  assert.strictEqual(T.kalshiStratBlocks(Array.from({ length: 40 }, (_, i) => 0.5 + i / 39), 12).length, 12, 'only the last n');
  assert.ok(T.kalshiStratBlocks([0.2, 1, 2.9], 3).split('').every((c) => '·▁▂▃▄▅▆▇█'.includes(c)));
};
gates.TM2 = () => {
  assert.strictEqual(T.kalshiStratTextBar(0.5, 8), '████░░░░');
  assert.strictEqual(T.kalshiStratTextBar(0, 8), '░'.repeat(8));
  assert.strictEqual(T.kalshiStratTextBar(9, 8), '█'.repeat(8), 'clamped to full');
  assert.strictEqual(T.kalshiStratTextBar(NaN, 8), '░'.repeat(8), 'unreadable is empty');
  const g = T.kalshiStratGauge('OICORE', { drawdown: 25, room: 25 }, money);
  assert.strictEqual(g.short, '50% of stop');
  const h = T.kalshiStratHealth(g);
  assert.deepStrictEqual(h, { bar: '████░░░░', text: '50% of stop' }, 'a live strategy: distance to its kill, a percentage and never a dollar figure');
  assert.strictEqual(T.kalshiStratHealth(T.kalshiStratGauge('L1', { count: 18 }, money)).text, '18 of 100');
  assert.deepStrictEqual(T.kalshiStratHealth(null, 75), { bar: '████░░░░', text: '75/150' }, 'a shadow rule: signals of 150');
  assert.strictEqual(T.kalshiStratHealth(null).text, 'n/a');
  assert.ok(!/\$/.test(T.kalshiStratHealth(T.kalshiStratGauge('OICORE', { drawdown: 25, room: 25 }, money)).text), 'no dollar in the health text');
};
gates.TM3 = () => {
  // the heat grid buckets by Central day, across the fall back change (Nov 1, 2026: a 25 hour day) and the spring forward one (Mar 8, 2026)
  const keys = T.kalshiStratDayKeys('2026-11-10', 30);
  assert.strictEqual(keys.length, 30); assert.strictEqual(keys[29], '2026-11-10'); assert.strictEqual(keys[0], '2026-10-12');
  assert.strictEqual(new Set(keys).size, 30, 'no day skipped or repeated');
  assert.ok(keys.includes('2026-11-01') && keys.includes('2026-10-31'), 'the 25 hour day is one cell');
  assert.deepStrictEqual(T.kalshiStratDayKeys('2026-03-10', 4), ['2026-03-07', '2026-03-08', '2026-03-09', '2026-03-10'], 'the 23 hour day is one cell');
  assert.deepStrictEqual(T.kalshiStratDayKeys('nope', 5), []);
  const now = Date.UTC(2026, 10, 10, 18, 0);
  const w = (ts) => order(ts, true), l = (ts) => order(ts, false);
  // 2026-11-02 05:59Z is Nov 1 23:59 CST; 06:00Z is Nov 2 00:00 CST; 2026-11-01 05:30Z is Nov 1 00:30 CDT
  const grid = T.kalshiStratHeat([w(Date.UTC(2026, 10, 1, 5, 30)), w(Date.UTC(2026, 10, 2, 5, 59)), w(Date.UTC(2026, 10, 2, 6, 0)), l(now - HR), w(now - 2 * HR), w(now - 3 * HR), w(Date.UTC(2026, 8, 1))], now, CT, 30);
  const by = Object.fromEntries(grid.map((c) => [c.day, c]));
  assert.strictEqual(grid.length, 30);
  assert.strictEqual(by['2026-11-01'].n, 2, 'both Nov 1 orders (00:30 CDT and 23:59 CST) are on Nov 1');
  assert.strictEqual(by['2026-11-02'].n, 1, 'midnight Central starts the next day');
  assert.strictEqual(by['2026-11-10'].n, 3);
  assert.strictEqual(by['2026-11-10'].net, Math.round((0.9 * 0 + 0.9 * 1 * 0 + (1 - 0.9055) * 10 * 2 - 9.055) * 10000) / 10000 || by['2026-11-10'].net);
  assert.ok(by['2026-11-10'].neg && by['2026-11-10'].net < 0, 'a losing day is marked neg');
  assert.ok(grid.every((c) => c.day !== '2026-09-01'), 'a result older than 30 days is not in the grid');
  assert.strictEqual(by['2026-11-05'].level, 0); assert.strictEqual(by['2026-11-05'].n, 0);
  assert.ok(grid.every((c) => c.level >= 0 && c.level <= 4) && Math.max(...grid.map((c) => c.level)) === 4 && grid.every((c) => !c.neg || c.level === 0), 'the best winning day is the brightest and a losing day is hollow, never bright');
  assert.ok(T.kalshiStratHeat([], now, CT, 30).every((c) => c.level === 0 && c.n === 0), 'no orders, an empty grid');
  assert.ok(T.kalshiStratHeat([order(now, true, { settled: false })], now, CT, 30).every((c) => c.n === 0), 'an open order has no result yet');
};
gates.TM4 = () => {
  // the order tape: filled orders only, newest first, at most n, the price the side cost, the cash result
  const now = Date.UTC(2026, 10, 10, 18, 0);
  const os = [order(now - 5 * HR, true), order(now - HR, false, { side: 'no', averageFillPrice: 0.1, result: 'yes', strategy: 'SLOT', slotId: 'OICORE', result: 'yes' }), { ts: now, fillCount: 0, side: 'yes' }, order(now - 2 * HR, true, { settled: false, result: undefined })];
  for (let i = 0; i < 20; i++) os.push(order(now - (10 + i) * HR, true));
  const tape = T.kalshiStratTape(os, 12, (o) => (o.slotId || 'L1'), () => 'Gold');
  assert.strictEqual(tape.length, 12);
  assert.ok(tape.every((l, i) => i === 0 || tape[i - 1].ts >= l.ts), 'newest first');
  assert.ok(tape.every((l) => l.ts !== now), 'an unfilled order is not on the tape');
  assert.deepStrictEqual([tape[0].tag, tape[0].side, tape[0].px, tape[0].state], ['OICORE', 'NO', 90, 'cash'], 'a NO order stored at YES 0.10 cost 90c');
  assert.ok(tape[0].cash < -0.8, 'the loss is in cash: ' + tape[0].cash);
  assert.strictEqual(tape[1].state, 'open'); assert.strictEqual(tape[1].cash, null);
  assert.strictEqual(tape[2].px, 90); assert.ok(Math.abs(tape[2].cash - 0.945) < 1e-9);
  assert.strictEqual(T.kalshiStratTape([order(1, true, { averageFillPrice: null })], 3, () => 'L1', () => 'Gold')[0].px, null, 'an unknown price is null, not 0');
  assert.deepStrictEqual(T.kalshiStratTape(null, 12, () => '', () => ''), []);
};
const liveModel = (running) => ({ live: T.KAL_BOARD_LIVE.map((s) => ({ id: s.id, name: s.name, rule: s.rule, rules: s.rules, w: { d7: { n: 1 }, d30: { n: 24, pf: 1.34 }, all: { n: 30, net: 12.5 } }, kill: { count: 18, drawdown: 25, room: 25, streak: 2, lines: ['status'] }, spark: [1, 1.1, 1.3, 1.2, 1.4] })),
  deck: { state: 'ok', rows: T.KAL_BOARD_SHADOW.map((r) => ({ id: r.id, rule: r.rule, spark: [1, 1.2, 1.1], rep: { fillable: 41, pfFillable: 1.25, netFillableDollars: 1.5, days: 6.4, status: 'collecting' } })) }, retired: T.KAL_BOARD_RETIRED, running });
gates.TM5 = () => {
  const now = Date.UTC(2026, 10, 10, 18, 0);
  const orders = [order(now - HR, true), order(now - 2 * HR, false), order(now - 40 * HR, true)];
  const m = (running, moneyFn) => Object.assign(liveModel(running), { heat: T.kalshiStratHeat(orders, now, CT, 30), heatSel: CT(now), tape: T.kalshiStratTape(orders, 12, () => 'L1', () => 'Gold'), clock: (t) => 'T' + t });
  const plain = T.kalshiBoardHtml(m(true), esc, money), masked = T.kalshiBoardHtml(m(true), esc, mask);
  const rows = T.KAL_BOARD_LIVE.length + T.KAL_BOARD_SHADOW.length;
  assert.strictEqual((plain.match(/<summary class="sp-sr">/g) || []).length, rows, 'one summary line per strategy');
  for (const c of ['sp-c-pf', 'sp-c-nm', 'sp-c-tr', 'sp-c-net', 'sp-c-hl', 'sp-c-st']) assert.strictEqual((plain.match(new RegExp('class="' + c + '"', 'g')) || []).length >= rows, true, c + ' column on every row');
  assert.ok(plain.indexOf('sp-c-pf') < plain.indexOf('sp-c-nm') && /<b class="sp-c-pf" data-pf="1\.34"/.test(plain), 'the profit factor is bold and first in the row, and still counts up');
  assert.ok(/<span class="sp-c-tr" aria-hidden="true">[·▁-█]{12}<\/span>/.test(plain), 'a 12 character block trend');
  assert.ok(/class="sp-hbar" aria-hidden="true">[█░]{8}</.test(plain), 'a text health bar');
  assert.strictEqual((plain.match(/class="sp-hc /g) || []).length, 30, 'thirty heat cells');
  assert.ok(/class="sp-hc sp-h\d sp-hn/.test(plain) || /class="sp-hc sp-h\d sp-hn/.test(plain.replace(/ sp-hs/g, '')), 'a losing day is hollow, not coloured');
  assert.ok(/class="sp-heat-read">[^<]*Nov 10: /.test(plain), 'the tapped day is read out in full');
  assert.strictEqual((plain.match(/<li><span class="sp-tp-t">/g) || []).length, 3, 'a tape line per order');
  assert.ok(/class="sp-live" role="img" aria-label="The bot is running"/.test(plain) && !/sp-live/.test(T.kalshiBoardHtml(m(false), esc, money)), 'the live dot shows only while the bot is running');
  assert.ok(plain.indexOf('Pipeline') < plain.indexOf('>Strategies <') && plain.indexOf('>Strategies <') < plain.indexOf('>30 days <') && plain.indexOf('>30 days <') < plain.indexOf('>Order tape <'), 'order: pipeline, table, heat grid, tape');
  // Privacy: dollars only through the money function
  const strip = (h) => h.replace(/<div class="kal-bd-rules">(?:<div>[\s\S]*?<\/div>){3}<\/div>/g, '').replace(/<div class="sp-rule">[^<]*<\/div>/g, '');
  assert.ok(!/\$\d/.test(strip(masked)) && /\*\*\*\*/.test(masked), 'with the mask on no dollar figure is in the markup (heat titles, tape, rows)');
  assert.ok(/\$\d/.test(plain.match(/class="sp-hc[^>]*title="[^"]*"/)[0] + plain.match(/class="sp-tp-r">[^<]*/)[0]), 'and with it off the day titles and the tape show dollars');
};
gates.TM6 = () => {
  // nothing from the log becomes markup in the new parts
  const evil = Object.assign(liveModel(true), { tape: [{ ts: 1, tag: '<img src=x onerror=1>', mk: '"><script>', side: '<b>', px: 9, cash: 1, state: 'cash' }], clock: () => '<i>', heat: [{ day: '"><u>', net: 1, n: 1, level: 2, neg: false }], heatSel: '"><u>',
    activity: { state: 'ok', items: [{ level: '<s>', title: '<a>', body: '<p>', ts: 1 }] }, timeline: [] });
  const h = T.kalshiBoardHtml(evil, esc, money);
  for (const bad of ['<img', '<script', '<i>', '<u>', '<s>', '<a>', '<p>', 'onerror=1>']) assert.ok(!h.includes(bad), 'raw ' + bad + ' is not in the page');
  assert.ok(h.includes('&#60;img') && h.includes('&#60;b&#62;'), 'escaped instead');
};
gates.TM7 = () => {
  // wiring: reads only, no timer, no storage, no write, no host; the day tap is the only new listener and it stores nothing
  const code = [fn('renderStrategiesPage'), fn('kalshiBoardHtml'), fn('kalshiStratBlocks'), fn('kalshiStratTextBar'), fn('kalshiStratDayKeys'), fn('kalshiStratHeat'), fn('kalshiStratTape'), fn('kalshiStratHealth')].join('\n');
  assert.ok(!/setInterval|setTimeout|localStorage|sessionStorage|setDoc|updateDoc|addDoc|deleteDoc|syncUserSetting|fetch\(|XMLHttpRequest|https?:\/\//.test(code), 'no timer, storage, write or host');
  assert.ok(!/'\$'|\\\$/.test(code), 'no dollar sign typed in the page code');
  const r = fn('renderStrategiesPage');
  assert.ok(/kalshiStratHeat\(all, now, kalDayKey, 30\)/.test(r) && /kalshiStratTape\(all, 12, kalshiStrategyOf, kalshiMarketName\)/.test(r) && /kalStratClock/.test(r), 'the heat grid and the tape read the orders the Bot page already holds (kalshiAllOrders)');
  assert.ok(/running = !!\(ctl && ctl\.active === true\)/.test(r) && /halt === true/.test(r) && /liveSwitch === false/.test(r), 'running means the session is on, not paused and the order switch is on');
  const listener = html.slice(html.indexOf("var pick = function(e)"), html.indexOf("var pick = function(e)") + 500);
  assert.ok(/kalshiStratHeatSel = c\.getAttribute\('data-day'\); renderStrategiesPage\(\)/.test(listener) && !/localStorage|setDoc|fetch/.test(listener), 'tapping a day only remembers it in memory and redraws');
  assert.ok(/d\.classList\.contains\('sp-row'\)/.test(html), 'an open row stays open across a redraw');
};
gates.TM8 = () => {
  // the theme: the site's own faces (no new font file), no colour, one continuous animation (the live dot) that both reduced-motion rules switch off
  const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>'));
  const mine = css.slice(css.indexOf('/* Terminal / data page'), css.indexOf('/* Strategies page animation (Nov 10'));
  assert.ok(mine.length > 1500, 'the terminal styles exist');
  assert.ok(!/green|\bred\b|#[0-9a-f]{3,6}\b|rgb\(|hsl\(|box-shadow|glow/i.test(mine.replace(/\/\*[\s\S]*?\*\//g, '')), 'no colour, no glow in the terminal styles (greys are rgba of grey and the theme variables)');
  assert.ok(/IBM Plex Mono/.test(mine) && !/font-family:\s*'(?!IBM Plex Mono|Public Sans)/.test(mine), 'only the site\'s own faces');
  assert.strictEqual((css.match(/@font-face/g) || []).length, 5, 'no new font file');
  const infinite = [...css.matchAll(/([^{}]+)\{[^{}]*animation:[^;}]*infinite[^;}]*/g)].filter((m) => /sp-|#page-strategies/.test(m[1]));
  assert.deepStrictEqual(infinite.map((m) => m[1].trim()), ['.sp-live'], 'the live dot is the only continuous animation on the page');
  const kf = /@keyframes spLive\{([^}]*\}[^}]*)\}/.exec(css)[1];
  assert.ok(/opacity/.test(kf) && !/(width|height|top|left|margin|padding|font-size)\s*:/.test(kf), 'it pulses opacity only');
  assert.ok(/@media \(prefers-reduced-motion: reduce\)\{[\s\S]*?\.sp-live\{ animation: none; \}/.test(css), 'off under prefers-reduced-motion');
  assert.ok(/\[data-reduce-motion="true"\] \.sp-live\{ animation: none; \}/.test(css), 'and under the Settings switch');
  const claude = fs.readFileSync(path.join(root, 'CLAUDE.md'), 'utf8');
  const sec = claude.slice(claude.indexOf('## Strategies page, terminal layout'));
  assert.ok(sec.length > 500, 'a dated CLAUDE.md section');
  assert.ok(!(mine + fn('kalshiBoardHtml') + sec + fs.readFileSync(__filename, 'utf8').replace(/String\.fromCharCode\(8212\)/g, '')).includes(String.fromCharCode(8212)), 'no em dash');
  const top = html.indexOf('<div class="changelog-day">');
  assert.ok(/terminal/i.test(html.slice(top, top + 6000)), 'a changelog line says it');
};
let failed = 0;
for (const [name, fn2] of Object.entries(gates)) { try { fn2(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);

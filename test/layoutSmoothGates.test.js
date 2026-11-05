'use strict';
// The smoother Bot page layout (Nov 5, 2026, the owner: "just more of a blocky interaction.. it doesnt move smoothly, i don't have much say in where each card goes on my page"; they chose smooth movement and free placement).
// Each gate states the consequence it defends. The layout code is lifted out of index.html and run with the page parts stubbed, so these check behaviour, not only text.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>')).replace(/\/\*[\s\S]*?\*\//g, '');
const start = html.indexOf('// Layout of the Bot tab, rebuilt Nov 5, 2026');
const iife = html.slice(start, html.indexOf('  // Starting the bot asks twice', start));
const gates = {};

const grab = (name) => { const m = new RegExp('(    function ' + name + '\\([^)]*\\)\\{[\\s\\S]*?\\n    \\})\\n').exec(iife); assert.ok(m, 'missing ' + name); return m[1]; };
const grabLine = (re) => { const m = re.exec(iife); assert.ok(m, 'missing ' + re); return m[0]; };
const consts = [/var OPTIONAL = [^\n]*/, /var CARDS = [^\n]*/, /var VERSION = 2, KEY = [^\n]*/, /var OLD_DOM = [^\n]*/].map(grabLine).join('\n');
const pure = new Function(consts + '\n' + ['fresh', 'isOptional', 'complete', 'migrateOrder', 'normalize'].map(grab).join('\n') + '\nreturn { fresh: fresh, normalize: normalize, isOptional: isOptional };')();

// L1: the account card can never be hidden. Consequence if it fails: the Running pill (Start, Pause, Flatten) could vanish from the page while the bot trades real money.
gates.L1 = () => {
  const l = pure.normalize({ v: 2, order: ['account'], hidden: { account: true, status: true, bogus: true } });
  assert.ok(!('account' in l.hidden) && l.hidden.status === true && !('bogus' in l.hidden), 'a saved "hide account" is dropped; a real optional card stays hidden');
  assert.ok(!pure.isOptional('account'), 'account is not an optional card');
  assert.ok(/c\.hidden = isOptional\(k\) && layout\.hidden\[k\] === true;/.test(iife), 'apply only ever hides an optional card, whatever the layout holds');
  assert.ok(!/data-card-toggle="account"/.test(html) && !/OPTIONAL = \[[^\]]*'account'/.test(iife), 'and the Layout menu has no switch for it');
  assert.ok(/var folded = layout\.folded\[k\] === true;/.test(iife) && /\.kal-console > \[data-card="account"\]\[data-folded="true"\] \.kal-acct-head\{ display:flex; \}/.test(css), 'folding the account card keeps its head, which holds the Running pill');
};

// L2: an old saved layout migrates instead of being thrown away. Consequence: an owner who arranged the page before Nov 5 sees the same order after the update.
gates.L2 = () => {
  // The old code dealt the markup order (rail: account, status, positions; main: pnl, trades) into the slots rail, rail, main, rail, main.
  const def = pure.normalize({ cols: 'auto', hidden: {}, order: ['account', 'status', 'positions', 'pnl', 'trades'] });
  assert.deepStrictEqual(def.order, ['account', 'status', 'pnl', 'positions', 'trades'], 'the old default reads as the default look');
  const moved = pure.normalize({ cols: '3', hidden: { trades: true }, order: ['positions', 'account', 'status', 'trades', 'pnl'] });
  assert.deepStrictEqual(moved.order, ['positions', 'account', 'trades', 'status', 'pnl'], 'an old custom order lands where the old page showed it');
  assert.deepStrictEqual(moved.hidden, { trades: true }, 'a hidden card stays hidden');
  assert.ok(!('cols' in moved) && moved.v === 2, 'the dead column count is dropped and the copy carries the new version');
  const partial = pure.normalize({ order: ['status', 'nope'] });
  assert.deepStrictEqual(partial.order.slice().sort(), ['account', 'pnl', 'positions', 'status', 'trades'], 'a partial or corrupt old order still yields every card exactly once');
  const v2 = pure.normalize({ v: 2, order: ['trades', 'account', 'status', 'pnl', 'positions'], width: { status: 'full', pnl: 'wide' }, folded: { pnl: true, x: true } });
  assert.deepStrictEqual(v2.order, ['trades', 'account', 'status', 'pnl', 'positions'], 'a new copy keeps its order as saved');
  assert.deepStrictEqual(v2.width, { status: 'full' }, 'only half or full gets through');
  assert.deepStrictEqual(v2.folded, { pnl: true }, 'only known cards fold');
  assert.ok(/if\(migrated\)\{ save\(true\); \}/.test(iife), 'the migrated copy is written back in the new shape');
};

// L3: reduced motion means no animation. Consequence: someone who asked their device (or the page's own attribute) for no motion gets cards that simply move.
gates.L3 = () => {
  const run = (reduced) => {
    let animated = 0, changed = 0;
    const mk = (i) => ({ hidden: false, __flip: null, rect: { left: 0, top: i * 100, width: 100 }, getBoundingClientRect() { return this.rect; }, animate() { animated++; return { cancel() {} }; } });
    const cards = [mk(0), mk(1)];
    const env = {
      document: { documentElement: { getAttribute: (k) => (k === 'data-reduce-motion' && reduced === 'attr' ? 'true' : 'false') } },
      window: { matchMedia: (q) => ({ matches: reduced === 'os' && /prefers-reduced-motion: reduce/.test(q) }) },
      grid: { animate() {} }, allCards: () => cards,
    };
    const flip = new Function('document', 'window', 'grid', 'allCards', grab('reducedMotion') + '\nvar FLIP_MS = 200;\n' + grab('flip') + '\nreturn flip;')(env.document, env.window, env.grid, env.allCards);
    flip(() => { changed++; cards[0].rect = { left: 0, top: 100, width: 100 }; cards[1].rect = { left: 0, top: 0, width: 100 }; });
    return { animated, changed };
  };
  assert.deepStrictEqual(run(false), { animated: 2, changed: 1 }, 'with motion allowed both cards slide');
  assert.deepStrictEqual(run('os'), { animated: 0, changed: 1 }, 'the device setting: the order changes, nothing slides');
  assert.deepStrictEqual(run('attr'), { animated: 0, changed: 1 }, 'the page attribute: the same');
  assert.ok(/if\(!reducedMotion\(\) && typeof c\.animate === 'function'\)/.test(iife), 'the drop settle is off under reduced motion too');
  const media = /@media \(prefers-reduced-motion: reduce\)\{([\s\S]*?)\n  \}/.exec(css)[1];
  assert.ok(media.includes('.kal-foldbtn > i{ transition: none; }') && css.includes('[data-reduce-motion="true"] .kal-foldbtn > i{ transition: none; }'), 'the fold chevron does not turn either');
};

// L4: widths are ignored at phone width. Consequence: a Half card never squeezes into half a phone screen.
gates.L4 = () => {
  assert.ok(/@media \(max-width:900px\)\{\s*\.kal-console\{ grid-template-columns:minmax\(0,1fr\); \}\s*\.kal-console \[data-card\]\{ grid-column:1 \/ -1; \}/.test(css), 'one column on a phone, every card across it');
  const block = css.indexOf('@media (max-width:900px){\n    .kal-console{ grid-template-columns:minmax(0,1fr); }\n    .kal-console [data-card]{');
  assert.ok(block > css.indexOf('.kal-console{ grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:18px; }'), 'and the phone rule comes after the two column rule, so it wins');
  assert.ok(/@media \(max-width:900px\)\{ \.kal-move \[data-width\]\{ display:none; \}/.test(css), 'the Half or Full toggle is not offered where it means nothing');
  assert.ok(/\.kal-console > \[data-card\]\[data-w="full"\]\{ grid-column:1 \/ -1; \}/.test(css) && !/grid-auto-flow:row dense/.test(css), 'on a wide screen Full spans both columns, and there is no dense packing to reorder cards behind the owner\'s back');
  // The defaults reproduce the look before the rebuild.
  assert.ok(/var WIDTHS = \{ account: 'full', status: 'half', pnl: 'half', positions: 'full', trades: 'full' \};/.test(iife), 'default widths');
  for (const [k, w] of [['account', 'full'], ['status', 'half'], ['pnl', 'half'], ['positions', 'full'], ['trades', 'full']]) assert.ok(new RegExp('data-w="' + w + '" data-card="' + k + '"').test(html), k + ' starts ' + w + ' in the markup, so the first paint already has the right shape');
};

// L5: Cancel restores the layout from before editing, Done keeps it, and nothing is saved while editing. Consequence: a slip in Edit layout can always be taken back.
gates.L5 = () => {
  const make = () => new Function(
    'var layout = { v: 2, order: ["account", "status", "pnl", "positions", "trades"], hidden: {}, width: {}, folded: {} };' +
    'var editing = false, before = null, undo = [], drag = null, saves = 0, KEY = "k";' +
    'var bar = { hidden: true }, undoBtn = { disabled: true };' +
    'var document = { getElementById: function(){ return { focus: function(){}, blur: function(){}, open: true }; } };' +
    'var localStorage = { setItem: function(){} };' +
    'function flip(fn){ fn(); } function apply(){} function setUnlocked(){} function announce(){} function endDrag(){} function save(){ saves++; }' +
    ['snapshot', 'same', 'updateUndo', 'change', 'startEdit', 'endEdit'].map(grab).join('\n') +
    'return { start: startEdit, end: endEdit, change: change, get: function(){ return layout; }, saves: function(){ return saves; }, undo: function(){ return undo.length; } };')();
  let t = make();
  t.start();
  t.change(() => { const o = t.get().order; o.splice(0, 1); o.push('account'); });
  t.change(() => { t.get().width.status = 'full'; });
  assert.strictEqual(t.saves(), 0, 'nothing is saved while editing');
  assert.strictEqual(t.undo(), 2, 'each change can be undone');
  t.end(false);
  assert.deepStrictEqual(t.get().order, ['account', 'status', 'pnl', 'positions', 'trades'], 'Cancel puts the order back');
  assert.deepStrictEqual(t.get().width, {}, 'and the widths');
  assert.strictEqual(t.saves(), 0, 'and saves nothing');
  t = make();
  t.start();
  t.change(() => { t.get().order.reverse(); });
  t.end(true);
  assert.deepStrictEqual(t.get().order, ['trades', 'positions', 'pnl', 'status', 'account'], 'Done keeps the change');
  assert.strictEqual(t.saves(), 1, 'and saves it once');
  t = make();
  t.change(() => { t.get().folded.pnl = true; });
  assert.strictEqual(t.saves(), 1, 'outside Edit layout a fold is saved at once');
  assert.ok(/var prev = undo\.pop\(\);/.test(iife), 'Undo steps back one change');
};

// L6: the page has no pointer listener of its own outside a drag, and a touch only drags after a hold (or on the grip), so a swipe still scrolls.
gates.L6 = () => {
  assert.ok(!/document\.addEventListener\('pointer/.test(html) && /listen\(true\);/.test(iife) && /listen\(false\);/.test(iife), 'move, up and cancel are listened to only while a card is held');
  assert.ok(/var HOLD_MS = 280, SLOP = 8;/.test(iife) && /else if\(drag\.touch && moved > SLOP\)\{ endDrag\(false\); \}/.test(iife), 'a finger that moves before the hold is a scroll');
  assert.ok(/\.kal-grip\{[^}]*touch-action:none/.test(css), 'the grip starts a touch drag at once');
  assert.ok(/aria-live="polite"/.test(html.slice(html.indexOf('id="kalLayoutLive"') - 40, html.indexOf('id="kalLayoutLive"') + 60)) && /moved to place /.test(iife), 'moves are announced');
};

// L7: the edit outline shows. The old selector named the grid's children while the cards sat one level down, so it never matched.
gates.L7 = () => {
  const seg = html.slice(html.indexOf('<div id="kalTabBot"'), html.indexOf('</main>', html.indexOf('<div id="kalTabBot"')));
  assert.ok(/<div id="kalTabBot" class="kal-bot-grid kal-console">\n      <div class="kal-card/.test(seg), 'the cards are direct children of the grid');
  assert.ok(/\.kal-bot-grid\.kal-unlocked > \.kal-card\{ outline:2px dashed var\(--border\);/.test(css), 'so the outline rule matches them');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

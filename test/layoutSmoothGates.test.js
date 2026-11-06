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
// Nov 5, 2026 (resizable cards): the layout is version 3, widths are spans of 12 columns and heights are pixels, so the size constants are lifted too.
const consts = [/var OPTIONAL = [^\n]*/, /var CARDS = [^\n]*/, /var SPANS = [^\n]*/, /var H_STEP = [^\n]*/, /var NO_HEIGHT = [^\n]*/, /var VERSION = 3, KEY = [^\n]*/, /var OLD_DOM = [^\n]*/].map(grabLine).join('\n');
const pure = new Function(consts + '\n' + ['fresh', 'isOptional', 'complete', 'migrateOrder', 'normalize', 'nextSpan', 'snapSpan', 'snapHeight', 'nextHeight'].map(grab).join('\n') + '\nreturn { fresh: fresh, normalize: normalize, isOptional: isOptional, nextSpan: nextSpan, snapSpan: snapSpan, snapHeight: snapHeight, nextHeight: nextHeight, SPANS: SPANS };')();

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
  assert.ok(!('cols' in moved) && moved.v === 3, 'the dead column count is dropped and the copy carries the new version');
  const partial = pure.normalize({ order: ['status', 'nope'] });
  assert.deepStrictEqual(partial.order.slice().sort(), ['account', 'pnl', 'positions', 'status', 'trades'], 'a partial or corrupt old order still yields every card exactly once');
  const v2 = pure.normalize({ v: 2, order: ['trades', 'account', 'status', 'pnl', 'positions'], width: { status: 'full', pnl: 'wide' }, folded: { pnl: true, x: true } });
  assert.deepStrictEqual(v2.order, ['trades', 'account', 'status', 'pnl', 'positions'], 'a new copy keeps its order as saved');
  assert.deepStrictEqual(v2.width, { status: 12 }, 'a version 2 Full reads as a span of 12, and a width that never existed is dropped (changed Nov 5, 2026: widths are spans now)');
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
  assert.ok(/@media \(max-width:900px\)\{\s*\.kal-console\{ grid-template-columns:minmax\(0,1fr\); \}\s*\.kal-console \[data-card\], \.kal-console > \[data-card\]\[data-w\]\{ grid-column:1 \/ -1; \}/.test(css), 'one column on a phone, every card across it');
  const block = css.indexOf('@media (max-width:900px){\n    .kal-console{ grid-template-columns:minmax(0,1fr); }\n    .kal-console [data-card], .kal-console > [data-card][data-w]{');
  assert.ok(block > css.indexOf('.kal-console{ grid-template-columns:repeat(12, minmax(0,1fr)); gap:18px; }'), 'and the phone rule comes after the twelve column rule, so it wins (changed Nov 5, 2026: twelve columns)');
  // Changed Nov 5, 2026 (resizable cards): the width and height buttons and the corner are all hidden on a phone; widths are spans of 12 (12 is the old Full, 6 the old Half).
  assert.ok(/@media \(max-width:900px\)\{ \.kal-move \[data-width\], \.kal-move \[data-height\], \.kal-resize\{ display:none; \}/.test(css), 'the size controls are not offered where they mean nothing');
  assert.ok(/\.kal-console > \[data-card\]\[data-w="12"\]\{ grid-column:1 \/ -1; \}/.test(css) && !/grid-auto-flow:row dense/.test(css), 'on a wide screen a full width card spans every column, and there is no dense packing to reorder cards behind the owner\'s back');
  // The defaults reproduce the look before the rebuild.
  assert.ok(/var WIDTHS = \{ account: 12, status: 6, pnl: 6, positions: 12, trades: 12 \};/.test(iife), 'default widths');
  for (const [k, w] of [['account', '12'], ['status', '6'], ['pnl', '6'], ['positions', '12'], ['trades', '12']]) assert.ok(new RegExp('data-w="' + w + '" data-card="' + k + '"').test(html), k + ' starts at a span of ' + w + ' in the markup, so the first paint already has the right shape');
};

// L5: Cancel restores the layout from before editing, Done keeps it, and nothing is saved while editing. Consequence: a slip in Edit layout can always be taken back.
gates.L5 = () => {
  const make = () => new Function(
    'var layout = { v: 3, order: ["account", "status", "pnl", "positions", "trades"], hidden: {}, width: {}, height: {}, folded: {} };' +
    'var editing = false, before = null, undo = [], drag = null, size = null, saves = 0, KEY = "k";' +
    'var bar = { hidden: true }, undoBtn = { disabled: true };' +
    'var document = { getElementById: function(){ return { focus: function(){}, blur: function(){}, open: true }; } };' +
    'var localStorage = { setItem: function(){} };' +
    'function flip(fn){ fn(); } function apply(){} function setUnlocked(){} function announce(){} function endDrag(){} function sizeEnd(){} function save(){ saves++; }' +
    ['snapshot', 'same', 'updateUndo', 'change', 'startEdit', 'endEdit'].map(grab).join('\n') +
    'return { start: startEdit, end: endEdit, change: change, get: function(){ return layout; }, saves: function(){ return saves; }, undo: function(){ return undo.length; } };')();
  let t = make();
  t.start();
  t.change(() => { const o = t.get().order; o.splice(0, 1); o.push('account'); });
  t.change(() => { t.get().width.status = 12; });
  t.change(() => { t.get().height.trades = 360; t.get().width.trades = 4; });
  assert.strictEqual(t.saves(), 0, 'nothing is saved while editing');
  assert.strictEqual(t.undo(), 3, 'each change can be undone, a resize included');
  t.end(false);
  assert.deepStrictEqual(t.get().order, ['account', 'status', 'pnl', 'positions', 'trades'], 'Cancel puts the order back');
  assert.deepStrictEqual(t.get().width, {}, 'and the widths');
  assert.deepStrictEqual(t.get().height, {}, 'and the heights (Cancel restores sizes)');
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

// L8: a folded card shows its title and nothing else in its head, except the Account card's Running pill (the owner, Nov 5, 2026: "only running should be visible when condensing"). The range buttons and the trades filter act on a body that is not shown.
gates.L8 = () => {
  const h = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  assert.ok(h.includes('.kal-console > [data-card][data-folded="true"] .kal-card-head > :not(.kal-card-title):not(.kal-botmenu){ display:none !important; }'), 'head controls hide on a folded card');
  assert.ok(/<div class="kal-card-head kal-acct-head">[\s\S]{0,200}<details class="kal-layout kal-botmenu" id="kalBotMenu"><summary id="kalL1Pill"/.test(h), 'the Running pill sits in the kept .kal-botmenu, a direct child of the Account head');
  assert.ok(/id="kalPnlRanges"/.test(h) && /<div class="kal-card-head"[^>]*><div class="kal-card-title"[^>]*>Account result<\/div><div class="kal-pnl-ranges" id="kalPnlRanges">/.test(h), 'the range buttons are a head child, so the rule hides them');
};

// Resizable cards (Nov 5, 2026, the owner: "this should maybe all be adjustable? size wise i guess"; they chose a corner drag, 12 column snapping, height in steps with a minimum, scrolling inside, a phone stays one column).

// L9: a width can only ever be one of the five spans. Consequence: no drag, button or saved copy can make a card a width the grid does not offer (a 5 or 7 would leave ragged rows).
gates.L9 = () => {
  assert.deepStrictEqual(pure.SPANS, [3, 4, 6, 8, 12], 'a quarter, a third, a half, two thirds, full');
  const gap = 18, col = (1384 - 11 * gap) / 12;
  for (let px = -200; px <= 2000; px += 7) assert.ok(pure.SPANS.includes(pure.snapSpan(px, col, gap)), 'a drag to ' + px + 'px snaps to an allowed span');
  const at = (n) => n * col + (n - 1) * gap;
  for (const n of pure.SPANS) assert.strictEqual(pure.snapSpan(at(n) + 5, col, gap), n, 'a drag just past span ' + n + ' stays at ' + n);
  assert.strictEqual(pure.snapSpan(at(5), col, gap) === 4 || pure.snapSpan(at(5), col, gap) === 6, true, 'five columns rounds to a neighbour');
  let w = 3; const seen = [];
  for (let i = 0; i < 5; i++) { w = pure.nextSpan(w); seen.push(w); }
  assert.deepStrictEqual(seen, [4, 6, 8, 12, 3], 'the width button steps through every span and round again');
  const n = pure.normalize({ v: 3, width: { account: 5, status: '6', pnl: 7, positions: 8, trades: 'full' } });
  assert.deepStrictEqual(n.width, { positions: 8, trades: 12 }, 'a saved width that is not an allowed span is dropped');
  assert.ok(/if\(SPANS\.indexOf\(w\) > -1\)\{ next\.width\[k\] = w; \}/.test(iife) && /layout\.width\[k\] = nextSpan\(widthOf\(k\)\)/.test(iife) && /size\.span = snapSpan\(/.test(iife), 'the corner and the button both go through the snapping');
  for (const n of [3, 4, 6, 8]) assert.ok(css.includes('.kal-console > [data-card][data-w="' + n + '"]{ grid-column:span ' + n + '; }'), 'span ' + n + ' has its rule');
};

// L10: a version 2 layout (Half or Full) keeps its look. Consequence: the owner's arrangement from this morning does not change shape after the update.
gates.L10 = () => {
  const old = { v: 2, order: ['trades', 'account', 'status', 'pnl', 'positions'], hidden: { status: true }, width: { status: 'full', positions: 'half', pnl: 'half' }, folded: { trades: true } };
  const n = pure.normalize(old);
  assert.deepStrictEqual(n.order, old.order, 'the order is kept as saved (no re-dealing)');
  assert.deepStrictEqual(n.width, { status: 12, positions: 6, pnl: 6 }, 'half is 6 and full is 12');
  assert.deepStrictEqual(n.hidden, old.hidden, 'hidden cards stay hidden');
  assert.deepStrictEqual(n.folded, old.folded, 'folded cards stay folded');
  assert.deepStrictEqual(n.height, {}, 'and nothing gets a height it did not have');
  assert.strictEqual(n.v, 3, 'the copy is rewritten as version 3');
  // On the 12 column grid a span of 6 is exactly the old half: 6c + 5g with c = (W - 11g) / 12 is W/2 - g/2, the old (W - g) / 2.
  for (const W of [800, 1384, 2000]) { const g = 18, c = (W - 11 * g) / 12; assert.ok(Math.abs((6 * c + 5 * g) - (W - g) / 2) < 1e-9, 'span 6 is the old half at ' + W + 'px'); assert.ok(Math.abs((12 * c + 11 * g) - W) < 1e-9, 'span 12 is the full width'); }
  assert.ok(/next\.order = \(l\.v === 2 \|\| l\.v === VERSION\) \? complete\(order, CARDS\) : migrateOrder\(order\);/.test(iife), 'a version 2 order is not dealt again like a pre version copy');
};

// L11: on a phone every size is ignored. Consequence: a quarter width or a short card set on a desktop never squeezes into a phone screen or hides its body behind a scroll.
gates.L11 = () => {
  const at = css.indexOf('.kal-console > [data-card][data-h]:not([data-folded="true"])');
  const open = css.lastIndexOf('@media (min-width:901px){', at), media = [css.slice(open, css.indexOf('\n  }', at) + 4)];
  assert.ok(open > -1 && at - open < 40 && /\[data-h\][^{]*\{ height:var\(--kal-h\);/.test(media[0]) && /> \.kal-card-body\{ flex:1 1 auto; min-height:0; overflow:auto; \}/.test(media[0]), 'a set height and the inner scroll exist on wide screens only');
  const outside = css.replace(media[0], '');
  assert.ok(!/var\(--kal-h\)/.test(outside), 'nothing else reads the height');
  const phone = css.lastIndexOf('@media (max-width:900px){\n    .kal-console{ grid-template-columns:minmax(0,1fr); }\n    .kal-console [data-card], .kal-console > [data-card][data-w]{ grid-column:1 / -1; }');
  assert.ok(phone > css.indexOf('.kal-console > [data-card][data-w="3"]{ grid-column:span 3; }'), 'the phone rule (one column, every card across it) comes after the span rules, so it wins');
  assert.ok(/if\(corner\)\{ if\(!phoneWidth\(\)\)\{ sizeStart\(e, /.test(iife), 'and the corner does nothing at phone width even if it were shown');
};

// L12: the Account card is width only. Consequence: its Start, Pause and Flatten menu (a panel that hangs below its head) can never be cut off by a set height or an inner scroll.
gates.L12 = () => {
  assert.ok(/var NO_HEIGHT = \{ account: true \};/.test(iife), 'the account card takes no height');
  assert.deepStrictEqual(pure.normalize({ v: 3, height: { account: 400, status: 400 } }).height, { status: 400 }, 'a saved height for it is dropped');
  assert.ok(/function heightOf\(k\)\{ return NO_HEIGHT\[k\] \? null :/.test(iife), 'so apply never sets one');
  assert.ok(/if\(!c \|\| NO_HEIGHT\[k\] \|\| c\.querySelector\(':scope > \.kal-card-body'\)\)\{ return; \}/.test(iife), 'its pieces are not wrapped in a scrolling body');
  assert.ok(/\(NO_HEIGHT\[k\] \? '' : '<button type="button" class="kal-mini" data-height="/.test(iife), 'it has no height button');
  assert.ok(/if\(!NO_HEIGHT\[size\.k\] && /.test(iife), 'and its corner changes only the width');
  const sized = /\.kal-console > \[data-card\]\[data-h\]:not\(\[data-folded="true"\]\):not\(\[data-card="account"\]\)\{ height:var\(--kal-h\);/.test(css);
  assert.ok(sized, 'and the CSS that applies a height excludes it as well');
  assert.ok(/\.kal-botmenu \.kal-botmenu-body\{ position:absolute;[^}]*top:calc\(100% \+ 8px\)/.test(css), 'the menu still hangs below the pill, which is why it must not be clipped');
};

// L13: a folded card ignores its set height. Consequence: folding a sized card gives the same title row as any other folded card, never a tall empty box.
gates.L13 = () => {
  assert.ok(/\[data-h\]:not\(\[data-folded="true"\]\)/.test(css) && !/[^(]\[data-folded="true"\][^{]*\{[^}]*var\(--kal-h\)/.test(css), 'the height rule never matches a folded card');
  assert.ok(/size\.card\.getAttribute\('data-folded'\) !== 'true'/.test(iife), 'the corner of a folded card does not set a height');
  assert.ok(/\.kal-console > \[data-card\]\[data-folded="true"\] > \.kal-resize\{ display:none; \}/.test(css), 'and a folded card shows no corner');
  assert.ok(/> :not\(\.kal-card-head\):not\(\.kal-card-title\):not\(\.kal-move\)\{ display:none !important; \}/.test(css), 'the scrolling body is hidden like any other body');
};

// L14: a height never goes below the minimum, snaps in 40px steps, and Auto is the default. Consequence: a card cannot be dragged to a sliver with its content cut off.
gates.L14 = () => {
  const b = { min: 180 };
  assert.strictEqual(pure.snapHeight(10, b), 180, 'never below the minimum');
  assert.strictEqual(pure.snapHeight(333, b), 320, 'snaps to 40px');
  assert.strictEqual(pure.snapHeight(99999, b), 3000, 'and has a ceiling');
  assert.deepStrictEqual([null, 240, 360, 480, 600].map((h) => pure.nextHeight(h, { min: 100 })), [240, 360, 480, 600, null], 'the height button: Auto, the steps, then Auto again');
  assert.strictEqual(pure.nextHeight(null, { min: 300 }), 300, 'a step under the minimum is raised to it');
  assert.ok(/return \{ min: Math\.min\(natural, Math\.ceil\(head \+ H_MIN_BODY\)\), natural: natural \};/.test(iife) && /var H_STEP = 40, H_MIN_BODY = 120/.test(iife), 'the minimum is the head plus 120px, or the card\'s own height if smaller');
  assert.deepStrictEqual(pure.fresh().height, {}, 'every card starts at its own height');
  assert.ok(/grid\.addEventListener\('dblclick'/.test(iife) && /delete layout\.height\[k\]; \}, LABELS\[k\] \+ ' is now its own height\.'/.test(iife), 'a double click on the corner puts it back to Auto, announced');
  assert.ok(/size\.hTouched \|\| Math\.abs\(dy\) >= H_STEP \/ 2/.test(iife), 'widening a card does not also fix its height');
  assert.ok(/if\(e === true \|\| !d\.moved \|\| !editing\)\{ return; \}/.test(iife) && /change\(function\(\)\{ layout\.width\[k\] = w;/.test(iife), 'a resize goes through change (one Undo step, Cancel undoes it) and only once the corner moved');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

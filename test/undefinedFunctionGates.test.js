// A function that is CALLED but never DEFINED.
//
// PR #170 shipped three calls to serverSettingSource() and, in the same
// commit message, described what that function would do. The function was
// never written. renderBackendStatus threw a ReferenceError on every single
// render from that merge onward, and because renderStatusPage called its
// cards in a bare sequence at the time, it took the cards below it down too
// -- which is why it surfaced as "most of the page is blank" rather than as
// one broken card.
//
// Nothing caught it. The inline-syntax check parses fine: a call to an
// undefined name is valid JavaScript until it runs. pre-ship's orphan check
// looks for element lookups, not function names. Both passed, all suites
// passed, and the card was dead in production for hours.
//
// This gate closes that class.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

// The main application script block -- the one that holds essentially all of
// this app's own code.
const BLOCK_START = src.indexOf('<script>', src.indexOf('</script>', src.indexOf('<script type="module">')));
const code = src.slice(BLOCK_START, src.indexOf('</script>', BLOCK_START))
  // Comments first: prose mentions plenty of function names, and a comment
  // naming a function is documentation, not a call.
  .replace(/\/\*[\s\S]*?\*\//g, '')
  .replace(/\/\/[^\n]*/g, '')
  // Then string literals. Half this file is HTML built by concatenation, and
  // ordinary prose inside it -- "Scanned 16 symbols (16 fetched)" -- matches
  // a call shape exactly. A name inside a string is text, not a call.
  .replace(/'(?:[^'\\\n]|\\.)*'/g, "''")
  .replace(/"(?:[^"\\\n]|\\.)*"/g, '""')
  .replace(/`(?:[^`\\]|\\.)*`/g, '``')
  // And regex literals, for the same reason: /Scanned (\d+) symbols/ is a
  // pattern, not a call to Scanned(). Only matched where a regex can legally
  // begin, so a division never gets eaten.
  .replace(/([=(,:&|!?{;[]\s*)\/(?:[^/\\\n[]|\\.|\[(?:[^\]\\]|\\.)*\])+\/[gimsuy]*/g, '$1RE');

// Everything this file defines, in any of the shapes it actually uses.
const defined = new Set();
(code.match(/function\s+([A-Za-z_$][\w$]*)/g) || [])
  .forEach((m) => defined.add(m.split(/\s+/)[1]));
(code.match(/(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=/g) || [])
  .forEach((m) => defined.add(/(?:var|let|const)\s+([A-Za-z_$][\w$]*)/.exec(m)[1]));
// Named function parameters and catch bindings can shadow/provide callables.
(code.match(/function\s*\(([^)]*)\)/g) || []).forEach((m) => {
  (m.replace(/function\s*\(|\)/g, '').split(',')).forEach((p) => {
    const n = p.trim();
    if (n) defined.add(n);
  });
});
(code.match(/catch\s*\(\s*([A-Za-z_$][\w$]*)/g) || [])
  .forEach((m) => defined.add(/catch\s*\(\s*([A-Za-z_$][\w$]*)/.exec(m)[1]));
// Named function declarations' own parameters, and anything destructured out
// of an options object -- a callback handed in as opts.onProgress is called
// bare and is defined by its caller, not here.
(code.match(/function\s+[A-Za-z_$][\w$]*\s*\(([^)]*)\)/g) || []).forEach((m) => {
  const inner = /\(([^)]*)\)/.exec(m);
  if (!inner) return;
  (inner[1].match(/[A-Za-z_$][\w$]*/g) || []).forEach((n) => defined.add(n));
});

// Host and language globals this app legitimately calls.
const GLOBALS = new Set([
  'if','for','while','switch','catch','return','function','typeof','new','else','do','void','delete','in','of','case','throw','with','yield','await',
  'Math','Number','String','Array','Date','JSON','Object','Boolean','RegExp','Error','Promise','Set','Map','Symbol','BigInt',
  'parseInt','parseFloat','isNaN','isFinite','encodeURIComponent','decodeURIComponent','encodeURI','decodeURI',
  'setTimeout','setInterval','clearTimeout','clearInterval','requestAnimationFrame','cancelAnimationFrame',
  'fetch','alert','confirm','prompt','console','document','window','navigator','location','localStorage','sessionStorage',
  'Notification','AbortController','URL','URLSearchParams','FormData','Blob','FileReader','Image','Audio','Intl',
  'AudioContext','webkitAudioContext','CustomEvent','Event','MutationObserver','IntersectionObserver','ResizeObserver','structuredClone','queueMicrotask','btoa','atob',
]);

const gates = {};

gates.G1 = () => {
  // Bare `name(` calls only: `a.b(` is a property call and is resolved at
  // runtime against an object, which this check cannot and should not judge.
  const called = new Set();
  const re = /(^|[^\w$.])([A-Za-z_$][\w$]*)\s*\(/g;
  let m;
  while ((m = re.exec(code))) called.add(m[2]);

  const missing = [...called].filter((n) => !defined.has(n) && !GLOBALS.has(n));

  assert.deepStrictEqual(missing, [],
    'called but never defined: ' + missing.join(', ')
    + ' -- this parses fine and throws at render time, which is how the whole '
    + 'Backend Status card shipped dead');
  console.log('G1 PASS every function called in the main script is defined somewhere in it');
};

// The specific one, named, so its absence can never be mistaken for a
// refactor that legitimately removed it.
gates.G2 = () => {
  assert.ok(/function\s+serverSettingSource\s*\(/.test(code),
    'serverSettingSource must exist: the Backend Status rows call it');
  const calls = (code.match(/serverSettingSource\s*\(/g) || []).length;
  // Definition plus one call site per Backend Status settings row --
  // equities and crypto, since the fade row was removed along with the
  // rest of the fade strategy's frontend surfaces.
  assert.ok(calls >= 3, 'expected the definition plus its call sites, found ' + calls);
  console.log('G2 PASS serverSettingSource is defined, and its callers still call it');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }

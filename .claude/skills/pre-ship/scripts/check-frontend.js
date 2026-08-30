#!/usr/bin/env node
// Static checks on shwoopnet's single-file frontend (index.html).
//
// Every check here exists because the corresponding bug ACTUALLY REACHED
// PRODUCTION at least once -- this is not a generic linter, it's a list of
// this project's own repeated mistakes. Exits non-zero if anything fails.
//
// Usage: node check-frontend.js [path/to/index.html] [--base <git-ref>]
//   --base compares CSS classes against a git ref (default: origin/main)
//          to catch rules deleted while still referenced.

const fs = require('fs');
const { execSync } = require('child_process');

const args = process.argv.slice(2);
const baseIdx = args.indexOf('--base');
const baseRef = baseIdx > -1 ? args[baseIdx + 1] : 'origin/main';
const file = args.find((a, i) => !a.startsWith('--') && (baseIdx === -1 || i !== baseIdx + 1)) || 'index.html';

if (!fs.existsSync(file)) {
  console.error(`FAIL  ${file} not found`);
  process.exit(1);
}
const html = fs.readFileSync(file, 'utf8');
const failures = [];
const notes = [];

function pass(msg) { console.log(`  ok    ${msg}`); }
function fail(msg) { console.log(`  FAIL  ${msg}`); failures.push(msg); }
function note(msg) { console.log(`  note  ${msg}`); notes.push(msg); }

// ---- 1. Every inline <script> parses ----
// A syntax error here takes down the entire app, and the file is large
// enough that it's genuinely easy to unbalance a brace mid-edit.
console.log('\nInline script syntax');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
if (scripts.length === 0) fail('no inline <script> blocks found at all -- is this the right file?');
scripts.forEach((src, i) => {
  try {
    new Function(src); // eslint-disable-line no-new-func
  } catch (err) {
    fail(`script block ${i} does not parse: ${err.message}`);
  }
});
if (!failures.length) pass(`${scripts.length} block(s) parse`);

// ---- 2. Every getElementById target exists ----
// Removing an element while leaving its lookup behind gives a silent null
// dereference at runtime -- no build step catches it.
console.log('\ngetElementById targets');
const ids = new Set([...html.matchAll(/id="([^"]+)"/g)].map((m) => m[1]));
const idRefs = [...new Set([...html.matchAll(/getElementById\('([^']+)'\)/g)].map((m) => m[1]))];
const missingIds = idRefs.filter((id) => !ids.has(id) && !id.includes('+'));
if (missingIds.length) {
  // Reported as a note, not a failure: some of these are legitimately
  // null-guarded and long-dead. The point is to SEE them and confirm any
  // NEW one is intentional, not to block on pre-existing ones.
  note(`${missingIds.length} lookup(s) with no matching element: ${missingIds.join(', ')}`);
  note('  -> if any of these are new in this change, that is a real bug');
} else {
  pass(`all ${idRefs.length} lookups resolve`);
}

// ---- 3. No CSS class deleted while still referenced ----
// THE ONE THAT BIT US: removing the Demo page took .trade-progress-* with
// it, because those rules sat interleaved among the demo styles. The bar
// rendered as bare text in production. Comparing against the base ref
// catches exactly this class of deletion.
console.log(`\nCSS classes removed vs ${baseRef}`);
let baseHtml = null;
try {
  baseHtml = execSync(`git show ${baseRef}:${file}`, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, stdio: ['pipe', 'pipe', 'pipe'] });
} catch (err) {
  note(`could not read ${baseRef}:${file} (${err.message.split('\n')[0]}) -- skipping this check`);
}
if (baseHtml) {
  const defined = (s) => new Set([...s.matchAll(/^\s*\.([a-zA-Z][\w-]*)[{ ,:]/gm)].map((m) => m[1]));
  const removed = [...defined(baseHtml)].filter((c) => !defined(html).has(c));
  // \b is the WRONG boundary for a class name, because `-` is a non-word
  // character: /\bnews-toast\b/ matches inside class="news-toast-tag".
  // That made this check block the deletion of a genuinely dead class
  // whose name happens to prefix a live hyphenated one -- and a check
  // that cries wolf is a check people learn to override. The boundary
  // has to exclude `-` on both sides as well as word characters.
  const B = '(?<![-\\w])';
  const A = '(?![-\\w])';
  const stillUsed = removed.filter((c) => new RegExp(
    `class="[^"]*${B}${c}${A}|querySelector\\w*\\('\\.${c}${A}|classList\\.\\w+\\('${c}'`,
  ).test(html));
  if (stillUsed.length) {
    fail(`CSS deleted but still referenced: ${stillUsed.join(', ')}`);
  } else if (removed.length) {
    pass(`${removed.length} class(es) removed, none still referenced`);
  } else {
    pass('no CSS classes removed');
  }
}

// ---- 4. Nav entries and page elements stay balanced ----
// Removing a page means removing its nav button too; leaving either half
// behind gives a dead nav item or an unreachable page.
console.log('\nNav / page balance');
const navPages = [...new Set([...html.matchAll(/data-page="([a-z]+)"/g)].map((m) => m[1]))].sort();
const pageIds = [...new Set([...html.matchAll(/id="page-([a-z]+)"/g)].map((m) => m[1]))].sort();
const navOnly = navPages.filter((p) => !pageIds.includes(p));
const pageOnly = pageIds.filter((p) => !navPages.includes(p));
if (navOnly.length) fail(`nav entries with no page element: ${navOnly.join(', ')}`);
if (pageOnly.length) note(`page elements with no nav entry: ${pageOnly.join(', ')} (fine if reached another way)`);
if (!navOnly.length && !pageOnly.length) pass(`${navPages.length} pages, nav and elements balanced`);

console.log('');
if (failures.length) {
  console.log(`FRONTEND: ${failures.length} failure(s). Do not ship.`);
  process.exit(1);
}
console.log(`FRONTEND: clean${notes.length ? ` (${notes.length} note(s) above -- confirm none are new)` : ''}.`);

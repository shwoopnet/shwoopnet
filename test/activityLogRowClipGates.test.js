'use strict';
// Reported live, twice: the Activity Log's leftmost column (the status
// pill -- "Closed", "Sent", "Protective Stop", etc.) rendering clipped
// against the card's left edge. Root cause both times is the same CSS
// trap: .activity-log-row sets margin:0 -10px (lets its hover background
// bleed to the card's own edges) offset by its own padding-left:10px, but
// .activity-log-row and .activity-log-row-cols land on the SAME element
// (see the innerHTML built in renderActivityLog) with equal selector
// specificity -- so whichever rule is declared LATER in the stylesheet
// wins on any longhand each one sets. A `padding: 10px 0` SHORTHAND on
// .activity-log-row-cols resets padding-left/padding-right to 0 as a side
// effect, even though it never mentions them by name, silently erasing
// the offset and shifting the whole row 10px into the card's own padding.
// This gate parses the real CSS rule bodies out of index.html (no DOM/
// cascade simulation needed -- the shorthand-vs-longhand hazard is
// detectable from the rule text alone) so this exact regression can't
// come back unnoticed a third time.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function ruleBody(selector) {
  const start = html.indexOf(selector + '{');
  assert.notStrictEqual(start, -1, `could not find CSS rule ${selector} in index.html`);
  const end = html.indexOf('}', start);
  // Strip /* ... */ comments before returning -- the rule's own explanatory
  // comment (see .activity-log-row-cols below) quotes the exact offending
  // shorthand as prose, which would otherwise false-positive this same check.
  return html.slice(start, end + 1).replace(/\/\*[\s\S]*?\*\//g, '');
}

function main() {
  const rowRule = ruleBody('.activity-log-row');
  assert.ok(/padding-left\s*:\s*10px/.test(rowRule),
    '.activity-log-row must set padding-left:10px to offset its own margin:0 -10px');

  const colsRule = ruleBody('.activity-log-row-cols');
  // The actual hazard: a `padding:` SHORTHAND (not padding-top/padding-bottom)
  // on this rule resets padding-left/right to whatever the shorthand's
  // second value is, clobbering .activity-log-row's padding-left:10px
  // since both classes land on the same element and this rule is declared
  // later in the stylesheet (same specificity, later wins).
  assert.ok(!/(?<![-a-z])padding\s*:/.test(colsRule),
    '.activity-log-row-cols must not use a `padding:` shorthand -- it silently resets ' +
    'padding-left/right to 0 and clips the row against the card edge (the exact bug this ' +
    'file is named for). Use padding-top/padding-bottom longhand instead.');

  console.log('PASS .activity-log-row-cols uses longhand padding, so it cannot silently erase .activity-log-row\'s left-offset compensation');
  console.log('\nAll activity log row clip gates passed.');
}

main();

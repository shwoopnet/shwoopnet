'use strict';
// RECPATCH1: every recorder workflow retries the push to the data branch up to 6 times with waits of 2, 4, 8, 16 and 32 seconds (a GitHub 500 lasts longer than a second), pulling between tries.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const dir = path.join(__dirname, '..', '.github', 'workflows');
const files = fs.readdirSync(dir).filter((f) => /^record-.*\.yml$/.test(f));
assert.ok(files.length >= 9, 'the recorder workflows are found');
for (const f of files) {
  const wf = fs.readFileSync(path.join(dir, f), 'utf8');
  if (f === 'record-perps.yml') continue; // its own branch and its own push, not part of this change
  assert.ok(/for i in 1 2 3 4 5 6; do git push -q origin quote-data && exit 0; \[ "\$i" -lt 6 \] \|\| break; sleep \$\(\(2 \*\* i\)\); git pull -q --rebase origin quote-data \|\| true; done/.test(wf), f + ': six push tries with exponential waits');
  assert.ok(!/for i in 1 2 3; do/.test(wf), f + ': the old three try loop is gone');
  assert.ok(!/git push[^\n]*\bmain\b/.test(wf), f + ': still never pushes main');
  console.log('ok   ' + f);
}

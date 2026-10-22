'use strict';
// Security hardening (Oct 22, 2026). This repo is PUBLIC and places real orders, so these gates state what must never appear in it and what protects the page.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const gates = {};

// A secret can never be committed by accident: no key file, no .env, and none of the common secret shapes in any tracked file. The Firebase web apiKey (AIza...) is public by design and is the one allowed match.
gates.S1 = () => {
  const files = execFileSync('git', ['ls-files'], { cwd: root, encoding: 'utf8' }).split('\n').filter(Boolean).filter((f) => !/node_modules|package-lock\.json|\.(png|webp|woff2|jpg|ico)$/.test(f));
  const badNames = files.filter((f) => /\.(pem|key|p12|pfx)$/i.test(f) || /(^|\/)\.env($|\.)/.test(f) || /serviceAccount|service-account/i.test(f));
  assert.deepStrictEqual(badNames, [], 'no key file, .env or service account file is tracked');
  const shapes = [/-----BEGIN (RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----/, /AKIA[0-9A-Z]{16}/, /sk_live_[0-9A-Za-z]{16,}/, /xox[baprs]-[0-9A-Za-z-]{10,}/, /gh[pousr]_[0-9A-Za-z]{30,}/, /"private_key_id"\s*:/, /AIza[0-9A-Za-z_-]{35}/];
  const hits = [];
  files.forEach((f) => {
    if (f === 'test/securityHardeningGates.test.js') return;
    const text = fs.readFileSync(path.join(root, f), 'utf8');
    shapes.forEach((re) => { if (re.test(text) && !(f === 'index.html' && re.source.startsWith('AIza'))) hits.push(f + ' matches ' + re.source.slice(0, 24)); });
  });
  assert.deepStrictEqual(hits, [], 'no secret shape in any tracked file');
  assert.strictEqual((fs.readFileSync(path.join(root, 'index.html'), 'utf8').match(/AIza[0-9A-Za-z_-]{35}/g) || []).length, 1, 'index.html carries exactly one AIza string: the public Firebase web key');
};

// The page hides itself if it is framed, because it carries Start, Pause and Flatten buttons and the host cannot block framing. It runs before anything else in the page.
gates.S2 = () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  const guard = html.indexOf('window.top !== window.self');
  assert.ok(guard > 0, 'the frame guard is there');
  assert.ok(/document\.documentElement\.style\.display = 'none'/.test(html.slice(guard, guard + 200)), 'it hides the page');
  assert.ok(guard < html.indexOf('<style>'), 'before the styles and every other script');
  assert.ok(guard < html.indexOf('<script type="module"'), 'and before the module that signs in');
};

// A build action is pinned to a commit, not a movable tag, so a hijacked tag cannot run new code with a write token in this repo; and every workflow says what its token may do.
gates.S3 = () => {
  const dir = path.join(root, '.github', 'workflows');
  fs.readdirSync(dir).filter((f) => /\.ya?ml$/.test(f)).forEach((f) => {
    const wf = fs.readFileSync(path.join(dir, f), 'utf8');
    [...wf.matchAll(/uses:\s*([^\s#]+)/g)].forEach((m) => assert.ok(/@[0-9a-f]{40}$/.test(m[1]), f + ': ' + m[1] + ' is pinned to a full commit'));
    assert.ok(/^permissions:/m.test(wf), f + ' sets its token permissions');
    assert.ok(!/pull_request_target/.test(wf), f + ' does not run on pull_request_target');
    assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), f + ' uses no secret but the built-in token');
  });
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);

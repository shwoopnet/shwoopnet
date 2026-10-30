// Gates for functions/deploy-latest.sh (the owner, Oct 30, 2026: "build the wrapper"). Each states the consequence, not the mechanism.
const assert = require('assert'), fs = require('fs'), path = require('path'), cp = require('child_process'), os = require('os');
const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'functions', 'deploy-latest.sh'), 'utf8');
const code = src.replace(/^\s*#.*$/gm, '');
const gates = {};

// DL1: it can only ever run the three existing deploy scripts, in the order CLAUDE.md requires, and nothing that moves code, secrets or git history.
gates.DL1 = () => {
  const runs = [...code.matchAll(/run bash functions\/(deploy-[a-z]+\.sh)/g)].map((m) => m[1]);
  assert.deepStrictEqual(runs, ['deploy-push.sh', 'deploy-sizing.sh', 'deploy-report.sh'], 'push first, then sizing, then report, and no other script');
  assert.ok(!/git push|--force|secrets:set|firebase deploy|KALSHI_[A-Z_]*TOKEN|openssl/.test(code), 'it never pushes, forces, sets a secret, deploys by itself or touches the token');
  assert.ok(/set -euo pipefail/.test(code), 'a failing step stops the run');
};

// DL2: nothing is deployed without the whole test suite passing and without the owner saying yes to the shown plan.
gates.DL2 = () => {
  const iTests = code.indexOf('test/*.test.js'), iAsk = code.indexOf('ask "Run the plan above?"'), iRun = code.indexOf('run bash functions/deploy-push.sh');
  assert.ok(iTests > 0 && iAsk > iTests && iRun > iAsk, 'tests, then the question, then the deploys');
  assert.ok(/Nothing deployed/.test(code), 'a failed test says nothing was deployed');
};

// DL3: the marker moves only after every selected deploy finished, so a failed deploy is offered again next time, and local edits are never discarded.
gates.DL3 = () => {
  const iLast = code.lastIndexOf('echo "$NEW" > "$MARKER"'), iReport = code.indexOf('run bash functions/deploy-report.sh');
  assert.ok(iLast > iReport, 'the final marker write comes after the last deploy');
  assert.ok(code.indexOf('git status --porcelain') < code.indexOf('git reset --hard'), 'local changes to tracked files stop the run before the reset');
  assert.ok(/functions\/\.last-deployed/.test(fs.readFileSync(path.join(root, '.gitignore'), 'utf8')), 'the marker is gitignored');
};

// DL4: end to end on a scratch repo with DRY_RUN: it picks the right deploys from the files that changed, and runs none of them for real.
gates.DL4 = () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'dl-'));
  const sh = (c, cwd) => cp.execSync(c, { cwd: cwd || tmp, stdio: 'pipe', encoding: 'utf8', env: { ...process.env, GIT_AUTHOR_NAME: 't', GIT_AUTHOR_EMAIL: 't@t', GIT_COMMITTER_NAME: 't', GIT_COMMITTER_EMAIL: 't@t' } });
  const origin = path.join(tmp, 'origin'), work = path.join(tmp, 'work');
  fs.mkdirSync(origin); sh('git init -q -b main', origin);
  fs.mkdirSync(path.join(origin, 'functions')); fs.mkdirSync(path.join(origin, 'test'));
  fs.writeFileSync(path.join(origin, 'functions', 'kalshiReportLib.js'), 'a\n'); fs.writeFileSync(path.join(origin, 'test', 'ok.test.js'), 'process.exit(0);\n');
  fs.copyFileSync(path.join(root, 'functions', 'deploy-latest.sh'), path.join(origin, 'functions', 'deploy-latest.sh'));
  sh('git add -A && git commit -q -m one', origin);
  sh(`git clone -q ${origin} ${work}`);
  const env = { ...process.env, DRY_RUN: '1', ASSUME_YES: '1' };
  const run = () => cp.execSync('bash functions/deploy-latest.sh', { cwd: work, env, encoding: 'utf8' });
  assert.ok(/starting point/.test(run()), 'the first run records a baseline instead of deploying');
  fs.writeFileSync(path.join(work, 'functions', '.last-deployed'), sh('git rev-parse HEAD', work).trim());
  assert.ok(/Nothing new/.test(run()), 'nothing new means nothing to do');
  fs.writeFileSync(path.join(origin, 'functions', 'kalshiReportLib.js'), 'b\n'); sh('git commit -q -am two', origin);
  const out = run();
  assert.ok(/deploy-report\.sh/.test(out) && !/deploy-sizing\.sh/.test(out.split('Plan')[1].split('All tests')[0]) && /\[dry run\] bash functions\/deploy-report\.sh/.test(out), 'a report change plans the report deploy only');
  fs.writeFileSync(path.join(origin, 'functions', 'kalshiLiveLib.js'), 'x\n'); sh('git add -A && git commit -q -m three', origin);
  const out2 = run();
  assert.ok(/deploy-push\.sh/.test(out2) && /deploy-sizing\.sh/.test(out2), 'a change to the live library plans the exit watch and the bot function');
  assert.ok(out2.indexOf('[dry run] bash functions/deploy-push.sh') < out2.indexOf('[dry run] bash functions/deploy-sizing.sh'), 'in the required order');
  fs.rmSync(tmp, { recursive: true, force: true });
};

(async () => { for (const [n, f] of Object.entries(gates)) { await f(); console.log('ok   ' + n); } })().catch((e) => { console.error(e); process.exit(1); });

// functions/deploy-sizing.sh is run by hand from a fresh clone on a phone. The failure that matters: a deploy without KALSHI_LIVE_ENABLED=on (functions/.env is gitignored, so a
// fresh clone has none) turns the live order switch OFF. These gates run the script in a scratch copy with DRY_RUN=1 and assert what it would do.
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const root = path.join(__dirname, '..');
const gates = {};

function scratch() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'deploy-sizing-'));
  fs.mkdirSync(path.join(dir, 'functions'));
  fs.copyFileSync(path.join(root, 'functions', 'deploy-sizing.sh'), path.join(dir, 'functions', 'deploy-sizing.sh'));
  return dir;
}
function run(dir) {
  return execFileSync('bash', [path.join(dir, 'functions', 'deploy-sizing.sh')], { env: { ...process.env, DRY_RUN: '1' }, encoding: 'utf8' });
}

gates.D1 = () => {
  execFileSync('bash', ['-n', path.join(root, 'functions', 'deploy-sizing.sh')]);
};

gates.D2 = () => {
  const dir = scratch();
  const out = run(dir);
  assert.strictEqual(fs.readFileSync(path.join(dir, 'functions', '.env'), 'utf8'), 'KALSHI_LIVE_ENABLED=on\n', 'a fresh clone gets the order switch line, so the deploy cannot turn the bot off');
  assert.ok(/\[dry run\] .*deploy --only functions:kalshiLiveArmed --project shwoopnet/.test(out), 'it deploys exactly one function to the shwoopnet project');
  assert.ok(!/--only functions(\s|$)/.test(out), 'never a whole-codebase deploy (that asks to delete functions)');
};

gates.D3 = () => {
  const dir = scratch();
  fs.writeFileSync(path.join(dir, 'functions', '.env'), 'KALSHI_LIVE_ENABLED=off\nKALSHI_WATCHDOG_URL=https://hc-ping.com/example\n');
  run(dir);
  const env = fs.readFileSync(path.join(dir, 'functions', '.env'), 'utf8');
  assert.ok(/^KALSHI_LIVE_ENABLED=on$/m.test(env) && !/KALSHI_LIVE_ENABLED=off/.test(env), 'an old off value is replaced, not left beside the on line');
  assert.ok(env.includes('KALSHI_WATCHDOG_URL=https://hc-ping.com/example'), 'other lines (the watchdog URL) are kept, so the deploy does not drop them');
};

gates.D4 = () => {
  const src = fs.readFileSync(path.join(root, 'functions', 'deploy-sizing.sh'), 'utf8');
  assert.ok(!/(secret|token|private[_ ]?key|password)\s*=/i.test(src), 'the script holds and asks for no credential');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
if (failed) process.exit(1);

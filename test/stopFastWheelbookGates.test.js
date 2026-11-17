// The owner stopped two recorders (Nov 16, 2026: "Stop both"): the 30 second perps recorder (redundant with the 60 second live perps recorder)
// and the wheel book recorder (no open card needs it). Consequence: neither workflow can start, chain or be dispatched, and nothing live reads them.
const assert = require('assert'), fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
for (const f of ['record-perps-fast.yml', 'record-wheelbook.yml']) assert.ok(!fs.existsSync(path.join(root, '.github', 'workflows', f)), f + ' is gone');
assert.ok(!fs.existsSync(path.join(root, 'scripts', 'record_wheelbook.py')), 'the wheel book script is gone');
for (const f of ['record_perps_fast.py', 'record_perps_sunday.py']) assert.ok(!fs.existsSync(path.join(root, 'scripts', f)), f + ' is gone (deleted Nov 16, 2026 with the Sunday recorder)');
const fnDir = path.join(root, 'functions');
for (const f of fs.readdirSync(fnDir).filter((x) => x.endsWith('.js'))) assert.ok(!/record_wheelbook|record-wheelbook|record-perps-fast/.test(fs.readFileSync(path.join(fnDir, f), 'utf8')), f + ' does not name them');
console.log('ok   STOP1: the 30 second perps recorder and the wheel book recorder are stopped');

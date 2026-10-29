// Step 1 of the second-account plan: every new L1 order and every event is stamped with the account it belongs to ("main"), and NOTHING reads it yet.
// Consequence: when a second account exists, its records can be told apart, and today's single account behaves exactly as before.
const assert = require('assert'), fs = require('fs'), path = require('path');
const live = require('../functions/kalshiLiveLib.js');
const lib = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8');
const idx = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
assert.strictEqual(live.DEFAULT_ACCOUNT_ID, 'main', 'the one account is called main');
assert.ok(/accountId: DEFAULT_ACCOUNT_ID, ticker, series: c\.series/.test(lib), 'a new L1 order record carries the account');
assert.ok(/const cid = "L1-" \+ ticker;/.test(lib), 'the client order id is unchanged, so two processes during a deploy still dedupe');
const adds = idx.match(/events\.add\(\{|"kalshiLiveEvents"\)\.add\(\{/g) || [];
const stamped = idx.match(/(events\.add|"kalshiLiveEvents"\)\.add)\(\{ accountId: live\.DEFAULT_ACCOUNT_ID/g) || [];
assert.ok(adds.length >= 6 && adds.length === stamped.length, 'every event written by a function is stamped with the account');
assert.ok(!/\.accountId\b/.test(lib.replace(/DEFAULT_ACCOUNT_ID/g, '')) && !/where\(\s*["']accountId/.test(lib + idx), 'nothing reads or filters on it yet, so no limit or stop changes');
console.log('accountIdGates: ok');

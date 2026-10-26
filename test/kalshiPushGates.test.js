'use strict';
// Phone alerts (Web Push, functions/kalshiPushLib.js). Each gate states a consequence. The point of the design: an alert can fail, but it can never touch an order or leave the owner's own systems
// except as an encrypted push to the phone's own relay.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const push = require('../functions/kalshiPushLib');
const webpush = require('../functions/node_modules/web-push');
const fnSrc = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
const libSrc = fs.readFileSync(path.join(root, 'functions', 'kalshiPushLib.js'), 'utf8');
const gates = {};
const order = (extra) => Object.assign({ strategy: 'L1', series: 'KXBTC15M', ticker: 'KXBTC15M-26OCT201330-30', clientOrderId: 'c1', side: 'yes', fillCount: 0, status: 'sending' }, extra || {});

// An entry, a sell and an issue each alert once, on the CHANGE; a rewrite with the same facts is silent; only L1 orders count.
gates.P1 = () => {
  assert.deepStrictEqual(push.orderKinds(null, order()), [], 'an order sent but not filled is nothing yet');
  assert.deepStrictEqual(push.orderKinds(order(), order({ fillCount: 4, status: 'filled' })), [], 'a buy never buzzes the phone (Oct 26, 2026)');
  assert.deepStrictEqual(push.orderKinds(order({ fillCount: 4, status: 'filled' }), order({ fillCount: 4, status: 'filled', price: 0.93 })), [], 'the same facts again are silent');
  assert.deepStrictEqual(push.orderKinds(order({ fillCount: 4 }), order({ fillCount: 4, exitStatus: 'sold' })), ['sell']);
  assert.deepStrictEqual(push.orderKinds(order({ fillCount: 4 }), order({ fillCount: 4, exitStatus: 'partly sold' })), ['sell']);
  assert.deepStrictEqual(push.orderKinds(order({ fillCount: 4 }), order({ fillCount: 4, exitStatus: 'error' })), ['issue']);
  assert.deepStrictEqual(push.orderKinds(order({ fillCount: 4 }), order({ fillCount: 4, exitStatus: 'unknown' })), ['issue']);
  assert.deepStrictEqual(push.orderKinds(order({ fillCount: 4 }), order({ fillCount: 4, exitStatus: 'no fill' })), ['issue']);
  assert.deepStrictEqual(push.orderKinds(order({ fillCount: 4 }), order({ fillCount: 4, exitStatus: 'skipped' })), [], 'a position already gone is not an issue');
  assert.deepStrictEqual(push.orderKinds(null, order({ fillCount: 4, status: 'filled' })), [], 'a buy created already filled is silent too');
  assert.deepStrictEqual(push.orderKinds(null, order({ strategy: 'OW1', fillCount: 4 })), [], 'only L1 orders alert');
  // A trade that finishes on its own alerts once, as a win or a loss; one the exit sold is a sell, not also a settlement; one already settled before the alerts existed stays silent.
  const held = order({ fillCount: 4, status: 'filled' });
  assert.deepStrictEqual(push.orderKinds(held, order({ fillCount: 4, status: 'filled', settled: true, result: 'yes', settledPnl: 0.24 })), ['settled'], 'a win alerts as a close');
  assert.deepStrictEqual(push.orderKinds(held, order({ fillCount: 4, status: 'filled', settled: true, result: 'no', settledPnl: -3.6 })), ['settled'], 'a loss alerts as a close');
  assert.deepStrictEqual(push.orderKinds(order({ fillCount: 4, status: 'filled', settled: true, result: 'yes' }), order({ fillCount: 4, status: 'filled', settled: true, result: 'yes', settledPnl: 0.24 })), [], 'rewritten after it settled: silent');
  assert.deepStrictEqual(push.orderKinds(order({ fillCount: 4, exitStatus: 'sold' }), order({ fillCount: 4, exitStatus: 'sold', settled: true, result: 'exit', settledPnl: -2.7 })), [], 'an exit already alerted as a sell, and result exit is not a settlement');
  assert.deepStrictEqual(push.orderKinds(held, order({ fillCount: 4, status: 'filled', exitStatus: 'sold', settled: true, result: 'exit', settledPnl: -2.7 })), ['sell'], 'sold and closed in one write is one sell alert');
  assert.deepStrictEqual(push.orderKinds(order({ fillCount: 4 }), order({ fillCount: 4, exitStatus: 'error', status: 'unknown' })), ['issue'], 'an issue wins over nothing else being new');
};

// A stop the bot made itself alerts; the owner's own Stop and Flatten do not.
gates.P2 = () => {
  assert.deepStrictEqual(push.sessionKinds({ active: true }, { active: false, endedBecause: 'loss stop' }), ['issue']);
  assert.deepStrictEqual(push.sessionKinds({ active: true }, { active: false, endedBecause: 'attempted' }), ['issue']);
  assert.deepStrictEqual(push.sessionKinds({ active: true }, { active: false, endedBecause: 'switched off by the owner' }), []);
  assert.deepStrictEqual(push.sessionKinds({ active: true }, { active: false, endedBecause: 'flattened by the owner' }), []);
  assert.deepStrictEqual(push.sessionKinds({ active: false }, { active: false, endedBecause: 'loss stop' }), [], 'already stopped: nothing new');
  assert.deepStrictEqual(push.sessionKinds(null, { active: true }), [], 'a first write is not a stop');
};

// One dead phone (404 or 410) is forgotten, one failing relay does not stop the others, and nothing throws.
gates.P3 = async () => {
  const subs = [{ id: 'a', subscription: 1 }, { id: 'b', subscription: 2 }, { id: 'c', subscription: 3 }, { id: 'd', subscription: 4 }];
  const removed = [], seen = [];
  const send = async (sub) => { seen.push(sub); if (sub === 2) { const e = new Error('gone'); e.statusCode = 410; throw e; } if (sub === 3) throw new Error('relay down'); };
  const r = await push.sendAll({ subs, payload: { title: 't' }, send, remove: async (id) => removed.push(id) });
  assert.deepStrictEqual(seen, [1, 2, 3, 4], 'every phone was tried');
  assert.deepStrictEqual(removed, ['b'], 'only the one the relay says is gone is removed');
  assert.deepStrictEqual(r, { sent: 2, removed: 1, failed: 1 });
  const r2 = await push.sendAll({ subs: [{ id: 'x', subscription: 1 }], payload: {}, send: async () => { const e = new Error('gone'); e.statusCode = 404; throw e; }, remove: async () => { throw new Error('firestore down'); } });
  assert.strictEqual(r2.failed, 1, 'a failed removal is counted, not thrown');
};

// Only a real https push subscription is stored, with only the endpoint and two keys.
gates.P4 = () => {
  const ok = { endpoint: 'https://web.push.apple.com/QWxhZGRpbjpvcGVuIHNlc2FtZQ', keys: { p256dh: 'B'.repeat(87), auth: 'a'.repeat(22) }, extra: 'ignored' };
  assert.deepStrictEqual(push.cleanSubscription(ok), { endpoint: ok.endpoint, keys: ok.keys }, 'extra fields are dropped');
  assert.strictEqual(push.cleanSubscription(Object.assign({}, ok, { endpoint: 'http://example.com/x1234567' })), null, 'plain http is refused');
  assert.strictEqual(push.cleanSubscription(Object.assign({}, ok, { keys: { p256dh: 'x', auth: 'y' } })), null, 'short keys are refused');
  assert.strictEqual(push.cleanSubscription(null), null);
  assert.strictEqual(push.subId(ok.endpoint), push.subId(ok.endpoint), 'the same phone is the same document');
  assert.notStrictEqual(push.subId(ok.endpoint), push.subId(ok.endpoint + 'x'));
};

// The public key is derived from the ONE secret, and a message for a real-looking subscription builds with that key (this is the encryption and signing step, offline: nothing is sent).
gates.P5 = () => {
  const k = webpush.generateVAPIDKeys();
  assert.strictEqual(push.publicKeyFromPrivate(k.privateKey), k.publicKey, 'derived, so only one secret is stored');
  const phone = crypto.createECDH('prime256v1'); phone.generateKeys();
  const sub = { endpoint: 'https://fcm.googleapis.com/fcm/send/abcdefghijklmnop', keys: { p256dh: phone.getPublicKey().toString('base64url'), auth: crypto.randomBytes(16).toString('base64url') } };
  const m = push.message('enter', order({ fillCount: 4, price: 0.93 }));
  const req = webpush.generateRequestDetails(sub, JSON.stringify({ title: m.title, body: m.body, tag: m.tag }), { vapidDetails: { subject: 'https://shwoopnet.github.io', publicKey: k.publicKey, privateKey: k.privateKey }, TTL: 3600, urgency: 'high' });
  assert.ok(/^vapid /.test(req.headers.Authorization), 'signed with the owner\'s VAPID key');
  assert.ok(Buffer.isBuffer(req.body) && !req.body.toString('utf8').includes('Bitcoin'), 'the text travels encrypted, so the relay cannot read it');
  assert.deepStrictEqual([m.title, m.body], ['Bought Bitcoin: 4 YES at about 93c', 'closes 12:30 PM CT']);
  const m2 = push.message('enter', order({ fillCount: 4, price: 0.93, maxCost: 3.72 }));
  assert.strictEqual(m2.body, '$3.72 at risk · closes 12:30 PM CT', 'the close time is Central, one hour behind the Eastern time in the ticker');
};

// The wording: short, no secrets, names the market.
gates.P6 = () => {
  assert.strictEqual(push.message('sell', order({ series: 'KXGOLD15M', exitStatus: 'sold', exitCount: 3, settledPnl: -2.7 })).title, 'Sold Gold early: -$2.70');
  assert.ok(/XRP/.test(push.message('issue', order({ series: 'KXXRP15M', exitStatus: 'error' })).title));
  assert.ok(/loss stop/.test(push.message('issue', { endedBecause: 'loss stop' }).title));
  const won = push.message('settled', order({ fillCount: 4, settledPnl: 0.2412, result: 'yes' })), lost = push.message('settled', order({ series: 'KXETH15M', fillCount: 1, settledPnl: -3.6, result: 'no' }));
  assert.deepStrictEqual([won.title, won.body], ['Won Bitcoin +$0.24', '4 YES'], 'the title carries the market and the amount, the body the size');
  assert.deepStrictEqual(lost.title, 'Lost Ethereum -$3.60');
  assert.strictEqual(push.message('settled', order({ fillCount: 2 })).title, 'Closed Bitcoin', 'no figure, no claim of a win or a loss');
  for (const k of ['enter', 'sell', 'issue', 'settled']) { const m = push.message(k, order({ fillCount: 1, price: 0.93, maxCost: 0.93, settledPnl: -0.93 }), { day: { net: -0.93, n: 1 } }); assert.ok(m.title.length < 60 && m.body.length < 120, k + ': ' + m.title.length + '/' + m.body.length); }
  // One line per TRADE: a sell or a settlement replaces that trade's buy alert; an issue keeps its own tag.
  const o = order({ fillCount: 4, price: 0.93 });
  assert.strictEqual(push.message('enter', o).tag, push.message('settled', Object.assign({}, o, { settledPnl: 0.2 })).tag, 'same trade, same tag');
  assert.notStrictEqual(push.message('enter', o).tag, push.message('enter', order({ clientOrderId: 'c2' })).tag, 'another trade, another line');
  assert.ok(/^issue-/.test(push.message('issue', Object.assign({}, o, { exitStatus: 'error' })).tag), 'an issue is never replaced by a routine alert');
  assert.ok(/renotify: true/.test(fs.readFileSync(path.join(root, 'sw.js'), 'utf8')), 'and the replacement still alerts');
};

// The day's line: only the bot's own settled L1 trades of the last 24 hours, never a trade the owner closed by hand, never an unsettled one.
gates.P6b = () => {
  const now = Date.parse('2026-10-20T20:00:00Z'), t = (over) => Object.assign({ strategy: 'L1', ts: now - 3600000, settled: true, result: 'yes', settledPnl: 0.2 }, over || {});
  assert.deepStrictEqual(push.dayNet([t(), t({ settledPnl: -3.6, result: 'no' }), t({ result: 'hand', settledPnl: undefined }), t({ settled: false }), t({ ts: now - 25 * 3600000 }), t({ strategy: 'OW1' })], now), { net: -3.4, n: 2 });
  assert.deepStrictEqual(push.dayNet([], now), { net: 0, n: 0 });
  assert.strictEqual(push.closesAt('KXBTC15M-26OCT200030-30'), '11:30 PM CT', 'half past midnight Eastern is 11:30 PM Central the day before');
  assert.strictEqual(push.closesAt('not a ticker'), null);
};

// Structure: alerts only READ. Nothing in the trading code imports the alert code; the alert code imports nothing that can trade or sign; every callable checks the owner; every trigger catches everything.
gates.P7 = () => {
  assert.ok(!/require\(["']\.\/kalshi(Live|Account|Signal)Lib/.test(libSrc) && !/KALSHI_LIVE_KEY|liveRequest|PRIVATE_KEY/.test(libSrc.replace(/privateB64url|privateKey/g, '')), 'the alert library cannot trade, sign or read a Kalshi key');
  for (const f of ['kalshiLiveLib.js', 'kalshiAccountLib.js', 'kalshiSignalLib.js', 'kalshiBookLib.js']) assert.ok(!/kalshiPushLib|web-push/.test(fs.readFileSync(path.join(root, 'functions', f), 'utf8')), f + ' does not know about alerts');
  const block = fnSrc.slice(fnSrc.indexOf('// ---- Phone alerts (Web Push)'), fnSrc.indexOf('exports.kalshiBookRecorder'));
  for (const name of ['kalshiPushKey', 'kalshiPushSubscribe', 'kalshiPushUnsubscribe']) {
    const body = new RegExp('exports\\.' + name + ' = onCall\\([\\s\\S]*?\\n\\}\\);').exec(block);
    assert.ok(body && /await assertKalshiAdmin\(request\.auth\)/.test(body[0]), name + ' checks the owner first');
  }
  for (const name of ['kalshiPushOrder', 'kalshiPushSession']) {
    const body = new RegExp('exports\\.' + name + ' = onDocumentWritten\\([\\s\\S]*?\\n\\}\\);').exec(block);
    assert.ok(body && /try \{[\s\S]*\} catch \(e\) \{ console\.error/.test(body[0]), name + ' catches every error, so an alert can never fail anything else');
    assert.ok(!/KALSHI_LIVE_KEY|liveRequest|live\./.test(body[0]), name + ' holds no Kalshi key');
  }
  assert.ok(!/kalshiPushSubs/.test(fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8')), 'the subscription documents have no client rule: only the server reads them');
};

// The files the phone needs: a worker that only shows and opens, and a manifest the phone can install.
gates.P8 = () => {
  const sw = fs.readFileSync(path.join(root, 'sw.js'), 'utf8');
  assert.ok(/addEventListener\('push'/.test(sw) && /showNotification/.test(sw) && /notificationclick/.test(sw), 'it shows pushes and opens the site on a tap');
  assert.ok(!/addEventListener\('fetch'/.test(sw) && !/\bfetch\(/.test(sw) && !/caches\./.test(sw) && !/https?:\/\//.test(sw), 'it caches nothing, intercepts nothing and calls nothing');
  const man = JSON.parse(fs.readFileSync(path.join(root, 'manifest.webmanifest'), 'utf8'));
  assert.strictEqual(man.display, 'standalone', 'installed to the Home Screen it opens as an app, which iPhone needs for push');
  assert.ok(fs.existsSync(path.join(root, man.icons[0].src)));
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(!/sw\.js|manifest/.test(cfg), 'the site publishes both files');
};

// The one laptop deploy: it keeps the order switch on (kalshiLiveExit reads it), deploys only what changed, and never prints or reuses a key.
gates.P9 = () => {
  const out = execFileSync('bash', [path.join(root, 'functions', 'deploy-push.sh')], { env: Object.assign({}, process.env, { DRY_RUN: '1' }), encoding: 'utf8' });
  fs.rmSync(path.join(root, 'functions', '.env'), { force: true });
  assert.ok(/KALSHI_LIVE_ENABLED=on/.test(out), 'the order switch line is written before anything deploys');
  const only = /deploy --only (\S+)/.exec(out)[1].split(',');
  assert.deepStrictEqual(only.sort(), ['functions:kalshiFlattenAll', 'functions:kalshiLiveExit', 'functions:kalshiPushKey', 'functions:kalshiPushOrder', 'functions:kalshiPushSession', 'functions:kalshiPushSubscribe', 'functions:kalshiPushUnsubscribe'], 'exactly the changed functions; not the arm');
  const sh = fs.readFileSync(path.join(root, 'functions', 'deploy-push.sh'), 'utf8');
  assert.ok(/functions:secrets:access KALSHI_PUSH_VAPID_PRIVATE/.test(sh) && /already exists, keeping it/.test(sh), 'an existing key is kept, so subscribed phones are not orphaned');
  assert.ok(!/echo[^\n]*privateKey|cat "\$KEYFILE"/.test(sh) && /rm -f "\$KEYFILE"/.test(sh), 'the key is never printed and the temporary file is removed');
  assert.ok(!/sed -i/.test(sh.replace(/#.*$/gm, '')), 'macOS safe: no sed -i in the commands');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();

"use strict";
// Phone alerts (the owner's request, Oct 20, 2026): the bot's entries, sells, stops and issues, pushed to the owner's phone with Web Push. No account with any vendor, no cost, and nothing here can
// place, change or cancel an order or read a key: it only READS what the bot already wrote (an order document changing, the session ending) and sends a short text to the browsers the owner
// subscribed from the Kalshi page. The message body is encrypted for the phone by the web-push library; the one outside piece is the push relay Apple or Google runs for every phone.
// Nothing in this file is imported by the trading code, and a failure here can never touch an order (see the triggers in index.js, which catch everything).
const crypto = require("crypto");

const NAMES = { KXBTC15M: "Bitcoin", KXGOLD15M: "Gold", KXETH15M: "Ethereum", KXXRP15M: "XRP", KXDOGE15M: "Dogecoin" };
const nameOf = (o) => NAMES[o && o.series] || (o && o.ticker ? String(o.ticker).split("-")[0] : "a market");

// The VAPID public key is derived from the private key (the one secret), so nothing else needs storing or pasting.
function publicKeyFromPrivate(privateB64url) {
  const ecdh = crypto.createECDH("prime256v1");
  ecdh.setPrivateKey(Buffer.from(privateB64url, "base64url"));
  return ecdh.getPublicKey().toString("base64url");
}

// What an L1 order document looks like to the alerts: entered (a fill appeared), sold (an exit sold or partly sold), issue (an exit that errored, did not fill or has an unknown answer, or an order left unknown).
// The same three flags the page's sound alerts use, so a sound on the open page and a push on the phone agree.
function flags(o) {
  if (!o || o.strategy !== "L1") return { e: false, s: false, i: false };
  return {
    e: Number(o.fillCount) > 0,
    s: o.exitStatus === "sold" || o.exitStatus === "partly sold",
    i: o.exitStatus === "error" || o.exitStatus === "unknown" || o.exitStatus === "no fill" || o.status === "unknown" || o.status === "error",
  };
}
// Only a CHANGE sounds: a flag that was false before and is true now. A document created already filled counts as a change from nothing; one that is rewritten with the same flags does not.
function orderKinds(before, after) {
  const was = flags(before), now = flags(after);
  const out = [];
  if (now.i && !was.i) out.push("issue");
  if (now.s && !was.s) out.push("sell");
  if (now.e && !was.e) out.push("enter");
  return out;
}
// The session ending by itself (the loss stop, a lost order answer) is an issue; the owner's own Stop and Flatten are not, because the owner just did them.
function sessionKinds(before, after) {
  if (!before || !after) return [];
  if (before.active === true && after.active !== true && !/by the owner/i.test(String(after.endedBecause || ""))) return ["issue"];
  return [];
}

function message(kind, o) {
  const name = nameOf(o);
  if (kind === "enter") return { title: "Bot bought " + name, body: Number(o.fillCount) + " " + String(o.side || "").toUpperCase() + (Number.isFinite(Number(o.price)) ? " at about " + Math.round(Number(o.price) * 100) + "c" : ""), tag: "enter-" + (o.clientOrderId || o.ticker) };
  if (kind === "sell") return { title: "Bot sold " + name, body: "The 25c exit " + String(o.exitStatus || "sold") + (Number.isFinite(Number(o.exitCount)) ? ": " + Number(o.exitCount) + " contracts" : ""), tag: "sell-" + (o.clientOrderId || o.ticker) };
  return { title: "Check the bot", body: o && o.series ? name + ": the exit " + String(o.exitStatus || o.status || "needs a look") : "The session ended: " + String((o && o.endedBecause) || "see the page").slice(0, 80), tag: "issue-" + ((o && (o.clientOrderId || o.endedAt)) || "x") };
}

// Sends one payload to every stored subscription. A subscription the push relay says is gone (404 or 410) is removed; any other failure leaves it for the next alert. Never throws.
async function sendAll({ subs, payload, send, remove }) {
  const body = JSON.stringify(payload);
  const out = { sent: 0, removed: 0, failed: 0 };
  for (const sub of subs) {
    try {
      await send(sub.subscription, body);
      out.sent++;
    } catch (e) {
      if (e && (e.statusCode === 404 || e.statusCode === 410)) {
        try { await remove(sub.id); out.removed++; } catch (e2) { out.failed++; }
      } else out.failed++;
    }
  }
  return out;
}

// A subscription from the browser, checked before it is stored: an https endpoint and the two keys, nothing else kept.
function cleanSubscription(raw) {
  if (!raw || typeof raw !== "object") return null;
  const endpoint = String(raw.endpoint || "");
  const keys = raw.keys || {};
  if (!/^https:\/\/[^\s]{10,1000}$/.test(endpoint)) return null;
  if (typeof keys.p256dh !== "string" || typeof keys.auth !== "string" || keys.p256dh.length < 20 || keys.auth.length < 8 || keys.p256dh.length > 200 || keys.auth.length > 100) return null;
  return { endpoint, keys: { p256dh: keys.p256dh, auth: keys.auth } };
}
const subId = (endpoint) => crypto.createHash("sha256").update(String(endpoint)).digest("hex").slice(0, 40);

module.exports = { publicKeyFromPrivate, flags, orderKinds, sessionKinds, message, sendAll, cleanSubscription, subId, NAMES };

"use strict";
// Phone alerts (the owner's request, Oct 20, 2026): the bot's entries, sells, stops and issues, pushed to the owner's phone with Web Push. No account with any vendor, no cost, and nothing here can
// place, change or cancel an order or read a key: it only READS what the bot already wrote (an order document changing, the session ending) and sends a short text to the browsers the owner
// subscribed from the Kalshi page. The message body is encrypted for the phone by the web-push library; the one outside piece is the push relay Apple or Google runs for every phone.
// Nothing in this file is imported by the trading code, and a failure here can never touch an order (see the triggers in index.js, which catch everything).
const crypto = require("crypto");

const NAMES = { KXBTC15M: "Bitcoin", KXGOLD15M: "Gold", KXETH15M: "Ethereum", KXXRP15M: "XRP", KXDOGE15M: "Dogecoin", KXAUDUSD15M: "AUD/USD", KXUSDCAD15M: "USD/CAD", KXNATGAS15M: "Natural gas" };
const nameOf = (o) => NAMES[o && o.series] || (o && o.ticker ? String(o.ticker).split("-")[0] : "a market");

// The VAPID public key is derived from the private key (the one secret), so nothing else needs storing or pasting.
function publicKeyFromPrivate(privateB64url) {
  const ecdh = crypto.createECDH("prime256v1");
  ecdh.setPrivateKey(Buffer.from(privateB64url, "base64url"));
  return ecdh.getPublicKey().toString("base64url");
}

// What an L1 order document looks like to the alerts: entered (a fill appeared), sold (an exit sold or partly sold), settled (the market finished and the order was settled by its result, a win or a loss; a
// position the exit sold is settled with result "exit" and already alerted as a sell), issue (an exit that errored, did not fill or has an unknown answer, or an order left unknown).
// Entered, sold and issue are the flags the page's sound alerts use, so a sound on the open page and a push on the phone agree for those; settled is phone only.
// An order document from another of the bot's own collections, as the alerts read it: the same rules, whatever its strategy label (the label only decides which collection it came from).
const botOrder = (o) => (o && typeof o === "object" ? Object.assign({}, o, { strategy: "L1" }) : o);
function flags(o) {
  if (!o || o.strategy !== "L1") return { e: false, s: false, d: false, i: false };
  return {
    e: Number(o.fillCount) > 0,
    d: o.settled === true && (o.result === "yes" || o.result === "no"),
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
  // Oct 26, 2026 (the owner: "my phone gets notifications constantly", then "add in closes, we can completely eliminate the entries"): a buy never buzzes the phone. Every CLOSE does: an early sell above, and a trade settling here, win or loss, with its amount. The page's sound alerts and the notification bell are unchanged.
  if (now.d && !was.d) out.push("settled");
  return out;
}
// The session ending by itself (the loss stop, a lost order answer) is an issue; the owner's own Stop and Flatten are not, because the owner just did them.
function sessionKinds(before, after) {
  if (!before || !after) return [];
  if (before.active === true && after.active !== true && !/by the owner/i.test(String(after.endedBecause || ""))) return ["issue"];
  // The exit watch went silent while a position is open (kalshiExitAlarmLib): a new alert only when the stamp CHANGES, so rewriting the document for any other reason never repeats it.
  const out = [];
  const was = before.exitWatchAlert && before.exitWatchAlert.at, nowAt = after.exitWatchAlert && after.exitWatchAlert.at;
  if (after.active === true && Number.isFinite(Number(nowAt)) && Number(nowAt) !== Number(was)) out.push("exitwatch");
  // A market skipped for low money on its own exchange shard (kalshiShardAlertLib): same rule, only a CHANGED stamp alerts.
  const wasShard = before.shardAlert && before.shardAlert.at, nowShard = after.shardAlert && after.shardAlert.at;
  if (after.active === true && Number.isFinite(Number(nowShard)) && Number(nowShard) !== Number(wasShard)) out.push("shard");
  return out;
}

// The close time in Central, from the ticker (KXBTC15M-26OCT201330-30: 13:30 Eastern, so 12:30 PM CT; Central is always one hour behind Eastern). null when the ticker is not that shape.
function closesAt(ticker) {
  const m = /^KX[A-Z]+?15M-\d{2}[A-Z]{3}\d{2}(\d{2})(\d{2})-\d+$/.exec(String(ticker || ""));
  if (!m || Number(m[1]) > 23 || Number(m[2]) > 59) return null;
  const h = (Number(m[1]) + 23) % 24;
  return (h % 12 === 0 ? 12 : h % 12) + ":" + m[2] + " " + (h < 12 ? "AM" : "PM") + " CT";
}
const money = (v) => (v >= 0 ? "+$" : "-$") + Math.abs(v).toFixed(2);
// What the bot's own trades did over the last 24 hours (settled ones, in the bot's own figures; trades the owner closed by hand have no figure and are left out). Pure.
function dayNet(orders, now) {
  let net = 0, n = 0;
  for (const t of orders || []) {
    if (!t || t.strategy !== "L1" || t.settled !== true || t.result === "hand" || !Number.isFinite(Number(t.settledPnl)) || !(Number(t.ts) >= now - 24 * 3600 * 1000)) continue;
    net += Number(t.settledPnl); n++;
  }
  return { net: Math.round(net * 100) / 100, n };
}
const dayText = (ctx) => (ctx && ctx.day && ctx.day.n > 0 ? "Last 24h " + money(ctx.day.net) + " (" + ctx.day.n + (ctx.day.n === 1 ? " trade" : " trades") + ")" : "");
const joinParts = (...p) => p.filter(Boolean).join(" · ");

// The words (v2, Oct 20, 2026). iOS stacks every alert from the site as "5 Notifications", showing only the title, so the title carries the facts (market, size, price, the amount) and the body the
// rest. The tag is the TRADE, not the event: a sell or a settlement replaces the buy alert of the same trade in place (the service worker renotifies), so the lock screen holds at most one line per
// trade. An issue keeps its own tag, so it is never replaced by a routine alert.
function message(kind, o, ctx) {
  const name = nameOf(o), trade = "trade-" + ((o && (o.clientOrderId || o.ticker)) || "x");
  const n = Number(o && o.fillCount), px = Number(o && o.price);
  const size = (Number.isFinite(n) && n > 0 ? n + " " + String(o.side || "").toUpperCase() : "") + (Number.isFinite(px) ? " at about " + Math.round(px * 100) + "c" : "");
  if (kind === "enter") {
    const risk = Number(o.maxCost);
    return { title: "Bought " + name + (size ? ": " + size : ""), body: joinParts(Number.isFinite(risk) ? "$" + risk.toFixed(2) + " at risk" : "", closesAt(o.ticker) ? "closes " + closesAt(o.ticker) : ""), tag: trade };
  }
  if (kind === "sell") {
    const pnl = Number(o.settledPnl);
    return { title: "Sold " + name + " early" + (Number.isFinite(pnl) ? ": " + money(pnl) : ""), body: joinParts("The 25c exit " + String(o.exitStatus || "sold") + (Number.isFinite(Number(o.exitCount)) ? " " + Number(o.exitCount) + " contracts" : ""), dayText(ctx)), tag: trade };
  }
  if (kind === "settled") {
    const pnl = Number(o.settledPnl);
    const title = !Number.isFinite(pnl) || pnl === 0 ? "Closed " + name : (pnl > 0 ? "Won " : "Lost ") + name + " " + money(pnl);
    return { title, body: joinParts(size, dayText(ctx)), tag: trade };
  }
  if (kind === "shard") {
    const a = (o && o.shardAlert) || {}, have = Number(a.avail), need = Number(a.need);
    return { title: "Check the bot: a market cannot trade, low money on exchange " + String(a.shard || "?").slice(0, 3), body: (Number.isFinite(have) && Number.isFinite(need) ? "Only $" + have.toFixed(2) + " there and an order needs $" + need.toFixed(2) + ". " : "") + "Money on another exchange does not count. Top it up in Kalshi under Transfers.", tag: "issue-shard" };
  }
  if (kind === "exitwatch") {
    const a = (o && o.exitWatchAlert) || {}, mins = Number(a.silentMin);
    return { title: "Check the bot: the exit watch is silent" + (Number.isFinite(mins) && mins > 0 ? " (" + mins + " min)" : ""), body: "A position is open and nothing has checked it for the 25c exit. Open the Kalshi page and look at it", tag: "issue-exitwatch" };
  }
  if (o && o.series) return { title: "Check the bot: " + name + " exit " + String(o.exitStatus || o.status || "needs a look"), body: "Open the Kalshi page and look at the order", tag: "issue-" + (o.clientOrderId || o.ticker) };
  return { title: "Bot stopped: " + String((o && o.endedBecause) || "see the page").slice(0, 60), body: "It stays off until you restart it on the Kalshi page", tag: "issue-" + ((o && o.endedAt) || "stop") };
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

module.exports = { publicKeyFromPrivate, flags, botOrder, orderKinds, sessionKinds, message, closesAt, dayNet, sendAll, cleanSubscription, subId, NAMES };

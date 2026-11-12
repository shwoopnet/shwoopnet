"use strict";
// Hourly balance snapshot (Nov 12, 2026, the owner). Once an hour: the account's total cash and the cash on each shard, nothing else. It exists so the balance change over a window with no deposit or
// withdrawal can be compared with the orders' booked result over the same window (the bank-side check of which booking basis is right).
//
// What it is NOT: it sends no order and has no POST, it places or changes nothing, and it touches no order, size, stop or risk code (the tick and the exit watch are not edited; this is its own scheduled
// function). Its one request is a GET of /portfolio/balance through the live module's request function, with the same two secrets the Bot page's account read already uses. The stored document has only the fields in
// ALLOWED_FIELDS: no order id, no client order id, no position, no fill, no key. Every error is swallowed: a failed read leaves a gap in the hourly series, which is fine, and never reaches trading.
//
// Idempotent across instances: the document id is the UTC hour, so two processes in the same hour (a deploy) write the same document with a merge, never two.
const live = require("./kalshiLiveLib");
const account = require("./kalshiAccountLib");

const COLLECTION = "kalshiBalanceSnaps";
const RETENTION_DAYS = 90;
const RETENTION_MS = RETENTION_DAYS * 86400000;
const PRUNE_HOUR_UTC = 3;          // the prune runs in this UTC hour's run only, once a day
const PRUNE_BATCH = 200;           // and deletes at most this many documents per day (about 2 days of hours; a backlog clears over days)
const MAX_SHARDS = 10;
const ALLOWED_FIELDS = Object.freeze(["ts", "at", "total", "shards"]);

const HOUR_MS = 3600000;
const hourStart = (ms) => Math.floor(ms / HOUR_MS) * HOUR_MS;
// 2026-11-12T14 : both processes compute the same id for the same hour.
const hourId = (ms) => new Date(hourStart(ms)).toISOString().slice(0, 13);
const cents = (x) => Math.round(x * 100) / 100;

// Pure. From the shaped balance (kalshiAccountLib.shapeBalance) to the document, or null when no usable figure came back.
function snapshotDoc(shaped, nowMs) {
  if (!shaped || shaped.ok !== true || !Number.isFinite(shaped.totalDollars)) return null;
  const shards = (Array.isArray(shaped.shards) ? shaped.shards : []).slice(0, MAX_SHARDS)
    .filter((s) => s && Number.isFinite(Number(s.dollars)) && s.shard !== undefined && s.shard !== null)
    .map((s) => ({ shard: Number(s.shard), dollars: cents(Number(s.dollars)) }))
    .filter((s) => Number.isFinite(s.shard));
  return { ts: hourStart(nowMs), at: nowMs, total: cents(shaped.totalDollars), shards };
}

// The I/O is injected so this is testable without Firebase or a network. Returns a short string for the log; never throws.
async function runBalanceSnapshot({ now, fetchFn, keyId, pem, write, prune } = {}) {
  let result = "ok";
  try {
    const r = await live.liveRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/balance", nowMs: now });
    const doc = snapshotDoc(account.shapeBalance(r), now);
    if (!doc) result = "balance unreadable, no snapshot";
    else await write(hourId(now), doc);
  } catch (e) {
    result = "error: " + String((e && e.message) || e).slice(0, 80);
  }
  // Retention, once a day and bounded. Independent of the read: a failed balance read must not stop the tidy-up.
  try {
    if (typeof prune === "function" && new Date(now).getUTCHours() === PRUNE_HOUR_UTC) await prune(now - RETENTION_MS, PRUNE_BATCH);
  } catch (e) { result += "; prune error: " + String((e && e.message) || e).slice(0, 60); }
  return result;
}

module.exports = { COLLECTION, RETENTION_DAYS, RETENTION_MS, PRUNE_HOUR_UTC, PRUNE_BATCH, ALLOWED_FIELDS, hourStart, hourId, snapshotDoc, runBalanceSnapshot };

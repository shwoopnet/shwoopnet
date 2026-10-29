"use strict";
// The second slot's Firestore side (docs/SECOND_SLOT_WIRING.md sections 2 and 3). The Firestore handle `db` is INJECTED: this file imports no firebase package, reads no environment and
// has no clock of its own (every time is passed in), so a test can drive it with a fake database. functions/index.js builds these stores only when the slot is on (SLOT_ON), and
// calls nothing here otherwise: while SLOT_ENABLED is false or SLOT_STRATEGIES is empty this file is loaded and never used.
//
// Collections it touches:
//   kalshiSlotOrders/{clientOrderId}   the slot's own orders (admin read, no client write in firestore.rules)
//   kalshiLiveDirection/{ticker}       the direction lock { side, by, ts }: written ONLY inside the transaction that creates an order document (this file for the slot, createLocked for L1)
//   kalshiSlotControl/killed           the kill latch map { [strategyId]: { killedAt, reason } } (no client rule: closed to every browser)
//   kalshiLiveOrders, kalshiBotMeta    READ here (L1's orders and the halt switch), never written except through createLocked, which writes the L1 order document and the lock together
// A Firestore transaction must finish all its reads before its first write; every function below follows that.

const slotLib = require("./kalshiSlotLib");

const SLOT = "kalshiSlotOrders", LOCK = "kalshiLiveDirection", CONTROL = "kalshiSlotControl", L1 = "kalshiLiveOrders";
const alreadyExists = (e) => Boolean(e && (e.code === 6 || /ALREADY_EXISTS/.test(String(e.message))));
const rows = (snap) => snap.docs.map((d) => ({ id: d.id, ...d.data() }));

// L1's order creation when the slot is on: the order document and the direction lock in ONE transaction. Returns true (created), false (the document exists, as createTest says today) or
// "direction" (the lock already holds the other side, nothing written). A lock whose side is not "yes" or "no" is treated as the other side (fail closed).
async function createLocked(db, id, data, { ticker, side }) {
  const lockRef = db.collection(LOCK).doc(String(ticker));
  const ref = db.collection(L1).doc(id);
  try {
    return await db.runTransaction(async (tx) => {
      const lock = await tx.get(lockRef);
      const d = lock.exists ? lock.data() : null;
      if (d && d.side !== side) return "direction";
      if (!d) tx.set(lockRef, { side, by: "L1", ts: Number(data && data.ts) || 0 });
      tx.create(ref, data);
      return true;
    });
  } catch (e) {
    if (alreadyExists(e)) return false;
    throw e;
  }
}

// Release a close lease, but only one this holder took (so the slot never clears Flatten's lease, nor the other way round). Used by the slot engine and, with the slot on, by L1's exit watch.
async function releaseCloseLease(db, ticker, who) {
  const ref = db.collection("kalshiLiveClosing").doc(String(ticker));
  await db.runTransaction(async (tx) => {
    const snap = await tx.get(ref);
    if (snap.exists && snap.data().by === who) tx.delete(ref);
  });
}
// An entry or exit with no clear answer. An exit that is "sending" counts only once its claim is stale (a sale mid-flight is normal for a few seconds; one that never finished is not), or has no claim
// time at all. Anything else with exitStatus "unknown" is a lost answer. Reads two single-field queries (no index).
async function unresolved(col, now) {
  if (!(await col.where("status", "in", ["sending", "unknown"]).limit(1).get()).empty) return true;
  if (!(await col.where("exitStatus", "==", "unknown").limit(1).get()).empty) return true;
  const sending = rows(await col.where("exitStatus", "==", "sending").get());
  return sending.some((o) => o.settled !== true && (!Number.isFinite(Number(o.exitClaimedAt)) || !Number.isFinite(now) || now - Number(o.exitClaimedAt) > EXIT_SENDING_STALE_MS));
}
const EXIT_SENDING_STALE_MS = 60 * 1000;

function slotStore(db, liveStore) {
  const col = db.collection(SLOT);
  const l1col = db.collection(L1);
  const ctrl = db.collection(CONTROL).doc("killed");
  return {
    // The halt switch, the unresolved-order check, the order list since a time and the per-market close lease are L1's own, so both engines read one truth.
    halted: () => liveStore.halted(),
    l1HasUnresolved: () => liveStore.hasUnresolved(),
    l1Recent: (since) => liveStore.sessionTrades(since),
    claimClose: (ticker, who, now, ttl) => liveStore.claimClose(ticker, who, now, ttl),
    // Only a lease this holder took is cleared, so L1's own 25 cent stop is not held off a market for 90 seconds by a slot sale that is already finished.
    releaseClose: (ticker, who) => releaseCloseLease(db, ticker, who),
    hasUnresolved: (now) => unresolved(col, now),
    async allSlotOrders() { return rows(await col.get()); },
    async slotOrdersOnTicker(ticker) { return rows(await col.where("ticker", "==", String(ticker)).get()); },
    async l1OrdersOnTicker(ticker) { return rows(await l1col.where("ticker", "==", String(ticker)).get()); },
    // Filled and not settled (two equalities, no index); the caller keeps the recent ones.
    async slotRecentFilled(since) { return rows(await col.where("status", "==", "filled").where("settled", "==", false).get()).filter((o) => Number(o.ts) >= since); },
    async updateSlotOrder(id, patch) { await col.doc(id).update(patch); },
    // The kill latch is only ever read as a whole map; a missing document means no strategy is latched. A read that throws is the caller's "unreadable", which kills every strategy.
    async killLatches() { const s = await ctrl.get(); return s.exists ? s.data() : {}; },
    async killStrategy(strategyId, info) { await ctrl.set({ [strategyId]: info }, { merge: true }); },
    // Atomic: only one instance gets to send each exit sell. False when another has it, when it was tried this many times already, or when the order has settled.
    async claimSlotExit(id, tries, now) {
      const ref = col.doc(id);
      return db.runTransaction(async (tx) => {
        const snap = await tx.get(ref);
        const d = snap.exists ? snap.data() : null;
        if (!d || d.exitStatus === "sending" || (Number(d.exitTries) || 0) !== tries || d.settled === true) return false;
        tx.update(ref, Number.isFinite(now) ? { exitStatus: "sending", exitTries: tries + 1, exitClaimedAt: now } : { exitStatus: "sending", exitTries: tries + 1 });
        return true;
      });
    },
    // An order's last patch and the kill latch in ONE transaction: killEval gets the slot's orders as they will stand after the patch and returns { strategyId, killedAt, reason } or null.
    async finishSlotOrder(id, patch, killEval) {
      const ref = col.doc(id);
      await db.runTransaction(async (tx) => {
        const snap = await tx.get(ref);
        const all = await tx.get(col);
        if (!snap.exists) return;
        const orders = rows(all).map((o) => (o.id === id ? { ...o, ...patch } : o));
        const k = typeof killEval === "function" ? killEval(orders) : null;
        tx.update(ref, patch);
        if (k && k.strategyId) tx.set(ctrl, { [k.strategyId]: { killedAt: k.killedAt, reason: k.reason } }, { merge: true });
      });
    },
    // The entry transaction. decide(lockDoc, slotOrdersNow, l1DocsOnThisTicker) is the pure decision (slotOrderCheck with lockTxn: true plus the shared stop); it runs on what the database holds
    // at commit time. Allowed: the lock (when absent) and the order document are written together, and a document that already exists rolls the lock back too. No document, no send.
    async runSlotEntry({ ticker, side, decide, now }) {
      const lockRef = db.collection(LOCK).doc(String(ticker));
      let out;
      try {
        out = await db.runTransaction(async (tx) => {
          const lock = await tx.get(lockRef);
          const slotSnap = await tx.get(col);
          const l1Snap = await tx.get(l1col.where("ticker", "==", String(ticker)));
          const lockDoc = lock.exists ? lock.data() : null;
          const verdict = decide(lockDoc, rows(slotSnap), rows(l1Snap));
          if (!verdict || verdict.allowed !== true) return { created: false, reason: (verdict && verdict.reason) || "not allowed" };
          if (!lockDoc) tx.set(lockRef, verdict.lock || { side, by: "SLOT", ts: now });
          tx.create(col.doc(verdict.record.id), verdict.record);
          return { created: true, record: verdict.record };
        });
      } catch (e) {
        if (alreadyExists(e)) return { created: false, reason: "already attempted" };
        throw e;
      }
      return out;
    },
  };
}

// What the live library calls while the slot is on (args.slot in runL1Tick and flattenAll).
function slotHooks(db) {
  const col = db.collection(SLOT);
  return {
    hasUnresolved: (now) => unresolved(col, now),
    async allOrders() { return rows(await col.get()); },
    // Contracts the slot may still hold on one side of one market (in-flight orders count as held). L1's exit watch subtracts this from the account position before it sells.
    async unsoldOn(ticker, side) {
      const snap = rows(await col.where("ticker", "==", String(ticker)).get());
      return snap.filter((o) => o.side === side).reduce((a, o) => a + slotLib.slotUnsoldOf(o), 0);
    },
    // Flatten bookkeeping. Only tickers whose result says the account is flat in them (sold, or already closed) have their open slot orders marked closed by hand (no profit figure, so
    // nothing fabricates a result); a partly sold, errored or leased market keeps its orders open, which the shared stop counts as lost (the safe direction). Then every strategy is
    // latched off: Flatten means stop everything, and only a reviewed edit that moves reviewedAt past this time re-arms one.
    async afterFlatten({ results, now }) {
      for (const r of results || []) {
        if (!r || !r.ticker) continue;
        if (!(r.status === "sold" || (r.status === "skipped" && r.detail === "already closed"))) continue;
        const snap = await col.where("ticker", "==", String(r.ticker)).get();
        for (const d of snap.docs) {
          const o = d.data();
          if (o.strategy === "SLOT" && o.settled !== true && Number(o.fillCount) > 0) await col.doc(d.id).update({ settled: true, result: "hand", flattened: true, settledAt: now });
        }
      }
      const latch = {};
      for (const s of slotLib.activeSlotStrategies()) latch[s.id] = { killedAt: now, reason: "flattened by the owner" };
      if (Object.keys(latch).length) await db.collection(CONTROL).doc("killed").set(latch, { merge: true });
    },
  };
}

// The order ids (entry and exit) of the slot's orders, handed to L1's settle sweep so a slot fill is never read as a hand sale of an L1 order.
async function slotIgnoreSet(db) { return slotLib.slotIgnoreSet(rows(await db.collection(SLOT).get())); }

module.exports = { slotStore, slotHooks, createLocked, slotIgnoreSet, releaseCloseLease, COLLECTIONS: Object.freeze({ SLOT, LOCK, CONTROL }) };

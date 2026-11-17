"use strict";
// The Firestore side of the nightly reconciliation (Nov 17, 2026): it reads the last 24 hours of the bot's own orders, the perps account document and the perps events, hands them to the PURE
// kalshiReconcileLib, stores the result and, on a mismatch, raises at most one alert stamp a day. It sits here and not in index.js so that file never names an order or control collection (a gate pins that).
// Database injected, so it is testable without Firebase. READ ONLY apart from its own result document and the alert stamp; no Kalshi request, no order, nothing that decides a trade reads any of it.
const rec = require("./kalshiReconcileLib");

const L1 = "kalshiLiveOrders", CONTROL = "kalshiLiveControl", PERPS_EVENTS = "kalshiPerpsEvents";   // the second slot's orders are read through the injected readSlotOrders: a gate keeps every other file from naming the slot collections
const WINDOW_MS = 24 * 3600000, MAX_ORDERS = 2000, MAX_EVENTS = 300;

async function recentOrders(db, name, since) {
  const s = await db.collection(name).where("ts", ">=", since).limit(MAX_ORDERS).get();
  return s.docs.map((d) => d.data());
}

// Returns a short string for the log; never throws.
async function runReconcileNightly({ db, now, perpsRef, readSlotOrders }) {
  try {
    const since = now - WINDOW_MS;
    const perps = await perpsRef.get();
    const events = await db.collection(PERPS_EVENTS).orderBy("at", "desc").limit(MAX_EVENTS).get();
    const out = rec.reconcile({ now, l1Orders: await recentOrders(db, L1, since), slotOrders: typeof readSlotOrders === "function" ? await readSlotOrders(since) : [], perpsDoc: perps.exists ? perps.data() : null, events: events.docs.map((d) => d.data()) });
    await db.collection(rec.DOC.collection).doc(rec.DOC.id).set(out);
    const alertRef = db.collection(CONTROL).doc("reconcileAlert"), sessRef = db.collection(CONTROL).doc("session");
    const note = await rec.runReconcileAlert({
      now, rec: out,
      claim: (at, cooldown) => db.runTransaction(async (tx) => {
        const cur = await tx.get(alertRef), last = cur.exists && Number.isFinite(Number(cur.data().at)) ? Number(cur.data().at) : null;
        if (last !== null && at - last < cooldown) return false;
        tx.set(alertRef, { at }, { merge: true });
        return last;
      }),
      release: (prev) => alertRef.set({ at: prev }, { merge: true }),
      raise: (a) => sessRef.set({ reconcileAlert: a }, { merge: true }),
    });
    return "reconcile " + (out.ok ? "ok" : out.findingCount + " finding(s)") + "; alert " + note;
  } catch (e) { return "reconcile failed: " + String((e && e.message) || e).slice(0, 160); }
}

module.exports = { runReconcileNightly, WINDOW_MS };

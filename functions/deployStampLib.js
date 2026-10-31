"use strict";
// Deploy stamp (Oct 31, 2026, the owner: "deploy check that proves the latest merge is live").
// Each deploy script writes functions/deploy-stamp.json ({commit, at}) just before it deploys. Every function instance records that stamp once, when it starts, in kalshiDeploys/{service}, and the nightly report shows them, so "is the newest merge running in the bot" is answered by a read, not by remembering which command was run.
// READ ONLY for trading: nothing here is imported by the order code, nothing reads it to decide an order, it holds no key, and every failure is swallowed (a missing stamp is shown as "no stamp", never an error).
// Caveat stated up front: the stamp is the commit the deploy script was run from, so a function deployed by hand with the firebase CLI carries whatever stamp file was last written in that folder.
const fs = require("fs");
const path = require("path");

const STAMP_FILE = path.join(__dirname, "deploy-stamp.json");
const COLLECTION = "kalshiDeploys";

// {commit, at} from the stamp file, or null when there is none or it is not what a script writes.
function readStamp(readFile = (p) => fs.readFileSync(p, "utf8"), file = STAMP_FILE) {
  try {
    const o = JSON.parse(readFile(file));
    if (!o || typeof o.commit !== "string" || !/^[0-9a-f]{7,40}$/.test(o.commit)) return null;
    return { commit: o.commit, at: typeof o.at === "string" ? o.at.slice(0, 40) : null };
  } catch (e) { return null; }
}

// The service name Cloud Run gives this instance (K_SERVICE), lower case letters, digits and hyphens only; null anywhere else (local runs, tests), which is what keeps the boot write out of every test.
function serviceName(env = process.env) {
  const s = env && env.K_SERVICE;
  return typeof s === "string" && /^[a-z0-9-]{1,63}$/.test(s) ? s : null;
}

// One write per instance start. `db` is a Firestore handle (injected); returns true when a write was made.
async function recordBoot({ db, env = process.env, stamp = readStamp(), nowMs = Date.now() } = {}) {
  const service = serviceName(env);
  if (!service || !db) return false;
  try {
    await db.collection(COLLECTION).doc(service).set({ service, commit: stamp ? stamp.commit : null, stampedAt: stamp ? stamp.at : null, bootAt: nowMs }, { merge: true });
    return true;
  } catch (e) { return false; }
}

// For the report: [{service, commit, stampedAt, bootAt}] from the docs, newest boot first. Numbers and short strings only.
function summarize(docs) {
  return (docs || []).filter((d) => d && typeof d === "object").map((d) => ({
    service: typeof d.service === "string" ? d.service.slice(0, 63) : null,
    commit: typeof d.commit === "string" ? d.commit.slice(0, 40) : null,
    stampedAt: typeof d.stampedAt === "string" ? d.stampedAt.slice(0, 40) : null,
    bootAt: Number.isFinite(Number(d.bootAt)) ? Number(d.bootAt) : null,
  })).filter((x) => x.service).sort((a, b) => (b.bootAt || 0) - (a.bootAt || 0));
}

module.exports = { readStamp, serviceName, recordBoot, summarize, COLLECTION, STAMP_FILE };

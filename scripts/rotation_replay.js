#!/usr/bin/env node
"use strict";
// Replay-only dry run of the rotation lane (docs/ROTATION_LANE.md v1.3). Reads ONE json file { rules, rows, liveOrders?, nowMs, ctx? } and prints the decision log as JSON lines to
// stdout. Writes a file only if given --out=<path> explicitly. No network, no Firestore, no order. Usage: node scripts/rotation_replay.js input.json [--out=log.jsonl]
const fs = require("fs");
const os = require("os");
const path = require("path");
const { replay } = require(path.join(__dirname, "..", "functions", "kalshiRotationLib.js"));
const args = process.argv.slice(2);
const file = args.find((a) => !a.startsWith("--"));
const outArg = args.find((a) => a.startsWith("--out="));
if (!file) { console.error("usage: node scripts/rotation_replay.js input.json [--out=log.jsonl]"); process.exit(2); }
const input = JSON.parse(fs.readFileSync(file, "utf8"));
const result = replay(input);
const text = result.log.map((e) => JSON.stringify(e)).join("\n") + "\n";
if (outArg) {
  // The path must be new (flag wx: an existing file is never overwritten) and inside the repo or the system temp folder.
  const target = path.resolve(outArg.slice("--out=".length));
  const ok = [path.resolve(__dirname, ".."), fs.realpathSync(os.tmpdir()), os.tmpdir()].some((b) => target === b || target.startsWith(b + path.sep));
  if (!ok) { console.error("refusing --out outside the repo or the temp folder"); process.exit(2); }
  fs.writeFileSync(target, text, { flag: "wx" });
} else process.stdout.write(text);

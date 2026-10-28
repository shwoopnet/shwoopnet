#!/usr/bin/env node
'use strict';
// The research director's scoreboard (the owner, Oct 28, 2026: "this research agent ... only continually works on the same thing over and over").
// It measures ONE thing deterministically: is the research still circling the live strategy (L1), and which market families has it never touched?
// It reads text only, writes nothing, places no order and calls no network. It does not judge whether anything works; that is the research session's pre-registered runs, read by a person.
//
//   node scoreboard.js [--readme path] [--mechanisms path] [--ledger path] [--events path.json] [--days 14] [--now 2026-10-28]
//
// --readme      the research ledger of this repo (default kalshi-scalper/README.md next to the repo root)
// --mechanisms  the cross-session index of crossed-off mechanisms (default ../shwoop-server/research/MECHANISMS.md when it exists)
// --ledger      the machine ledger of formal runs (runs.jsonl), one JSON object per line (default ../shwoop-server/research/ledger/runs.jsonl when it exists)
// --events      the research session's recent messages as JSON: an array of strings or of { text }. The director saves list_events output here.

const fs = require('fs');
const path = require('path');

// A heading that registers or reports a test, and whether it is a variant of the live strategy. The words are the ones the ledger itself uses for L1 tuning.
// It also counts scalps, opening-window tests and 15 minute contract tests: they are the same contracts, so they are not a new market family.
const L1_VARIANT = /\bL1\b|price band|\bband\b|\bexit\b|filter|sizing|size ladder|ladder|add-on|pool\b|hold.to.settlement|settlement|scalp|tick level|opening|\bOW\d|cheap side|early (taker|drift)|15 minute|ETH and SOL|Ethereum/i;
// Only a Pre-registration or an Idea ledger heading is NEW work. A Results or Amendment heading reports or adjusts an earlier one, so counting it would double count.
const REGISTRATION = /^#{2,3}\s+(Pre-registration|Idea ledger)/i;

// Families a prediction market search could cover. `hit` words found anywhere in the inputs mean the family was at least mentioned; the director then reads what was run.
// A mention is not a test, and the report says so.
const FAMILIES = [
  { key: 'l1', label: 'L1: hold to settlement on the 15 minute crypto and gold contracts (the live strategy)', hit: /\bL1\b|near.settlement/i, live: true },
  { key: 'scalp15', label: 'Short scalps and exits on those same 15 minute contracts', hit: /scalp|tick level|opening window|\bOW\d/i, live: true },
  { key: 'tape', label: 'Order flow and the trade tape', hit: /TAPE\d+|order flow|footprint|taker flow/i },
  { key: 'ladder', label: 'Hourly and daily ladder markets priced off a model', hit: /LAD\d+|hourly ladder|ladder model/i },
  { key: 'crypto-spot', label: 'Spot or perpetual crypto directional', hit: /CRYPTO1|spot crypto|perpetual|funding/i },
  { key: 'equities', label: 'Equities (opening range, PEAD, VWAP, gaps)', hit: /equities|opening.range|\bPEAD\b|\bVWAP\b|gap reversion/i },
  { key: 'weather', label: 'Weather: daily highs and lows against public forecasts', hit: /weather|temperature|\bNWS\b|forecast/i },
  { key: 'econ', label: 'Economic releases: CPI, jobs, Fed decisions against nowcasts', hit: /\bCPI\b|jobs report|\bFOMC\b|nowcast|economic release/i },
  { key: 'sports', label: 'Sports: totals, in-play, pre-game', hit: /sports|tennis|\bNBA\b|\bNFL\b|in-play|totals/i },
  { key: 'events', label: 'Politics and event contracts', hit: /election|politic|event contract/i },
  { key: 'longshot', label: 'Favourite-longshot bias and calibration across all contracts', hit: /longshot|calibration/i },
  { key: 'cross', label: 'Cross-market consistency and arbitrage (same event, two prices)', hit: /arbitrage|cross.market|consisten|parity/i },
];

function arg(name, dflt) {
  const i = process.argv.indexOf('--' + name);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : dflt;
}
function read(p) { try { return fs.readFileSync(p, 'utf8'); } catch (e) { return null; } }
function isoWeek(d) {
  const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  const day = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - day);
  const y0 = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
  return t.getUTCFullYear() + '-W' + String(Math.ceil(((t - y0) / 86400000 + 1) / 7)).padStart(2, '0');
}

// Registrations in a ledger README: one per heading that registers a test and carries a date, e.g. "## Pre-registration: B4, ... (fixed 2026-10-10, before any ...)".
function registrations(text) {
  const out = [];
  (text || '').split('\n').forEach((line) => {
    if (!REGISTRATION.test(line)) return;
    const m = /(20\d\d-\d\d-\d\d)/.exec(line);
    if (!m) return;
    out.push({ date: m[1], title: line.replace(/^#+\s+/, '').slice(0, 110), l1: L1_VARIANT.test(line) });
  });
  return out;
}

// Verdict words in the machine ledger and the mechanisms index. Only FALSIFIED, NOT_YET_FALSIFIED, NOT_RUNNABLE and NO_WINNER are valid; there is no "promoted".
function verdicts(ledgerText, mechText) {
  const c = { FALSIFIED: 0, NOT_YET_FALSIFIED: 0, NOT_RUNNABLE: 0, NO_WINNER: 0 };
  (ledgerText || '').split('\n').forEach((l) => { const m = /"verdict":"(\w+)"/.exec(l); if (m && c[m[1]] !== undefined) c[m[1]]++; });
  const mech = { crossedOff: 0, queued: 0 };
  (mechText || '').split('\n').forEach((l) => {
    if (/^\|\s*\d+\s*\|/.test(l)) mech.crossedOff++;
    if (/QUEUED/.test(l) && /^\|/.test(l)) mech.queued++;
  });
  return { ledger: c, mech };
}

function eventsText(p) {
  const raw = read(p); if (!raw) return null;
  try {
    const j = JSON.parse(raw);
    return (Array.isArray(j) ? j : []).map((e) => (typeof e === 'string' ? e : (e && (e.text || e.content)) || '')).filter(Boolean);
  } catch (e) { return null; }
}

function build(opts) {
  const now = new Date((opts.now || new Date().toISOString().slice(0, 10)) + 'T23:59:59Z');
  const days = Number(opts.days) || 14, since = new Date(now.getTime() - days * 86400000);
  const readme = read(opts.readme), mech = read(opts.mechanisms), ledger = read(opts.ledger), ev = opts.events ? eventsText(opts.events) : null;
  const regs = registrations(readme);
  const recent = regs.filter((r) => new Date(r.date + 'T00:00:00Z') >= since);
  const byWeek = {};
  regs.forEach((r) => { const w = isoWeek(new Date(r.date + 'T00:00:00Z')); byWeek[w] = byWeek[w] || { total: 0, l1: 0 }; byWeek[w].total++; if (r.l1) byWeek[w].l1++; });
  const all = [readme, mech, ledger].concat(ev || []).filter(Boolean).join('\n');
  const fam = FAMILIES.map((f) => ({ key: f.key, label: f.label, live: !!f.live, mentions: (all.match(new RegExp(f.hit.source, 'gi')) || []).length }));
  let evL1 = null;
  if (ev && ev.length) {
    const liveHits = ev.filter((t) => FAMILIES.some((f) => f.live && f.hit.test(t))).length;
    const otherHits = ev.filter((t) => FAMILIES.some((f) => !f.live && f.hit.test(t))).length;
    evL1 = { messages: ev.length, aboutLive: liveHits, aboutOther: otherHits };
  }
  return {
    now: now.toISOString().slice(0, 10), days,
    registrations: { total: regs.length, recent: recent.length, recentL1: recent.filter((r) => r.l1).length, byWeek, recentTitles: recent.slice(-8).map((r) => r.date + ' ' + r.title) },
    verdicts: verdicts(ledger, mech), families: fam, events: evL1,
    inputs: { readme: !!readme, mechanisms: !!mech, ledger: !!ledger, events: !!ev },
  };
}

function render(s) {
  const L = [];
  const pct = (a, b) => (b ? Math.round((a / b) * 100) + '%' : 'n/a');
  L.push('RESEARCH SCOREBOARD as of ' + s.now + ' (last ' + s.days + ' days)');
  L.push('inputs read: ' + Object.keys(s.inputs).map((k) => k + (s.inputs[k] ? ' yes' : ' MISSING')).join(', '));
  L.push('');
  L.push('Drift: ' + s.registrations.recentL1 + ' of ' + s.registrations.recent + ' registrations in the window were variants of the live strategy (' + pct(s.registrations.recentL1, s.registrations.recent) + '). Whole record: ' + s.registrations.total + '.');
  if (s.registrations.recent === 0) L.push('NOTE: no dated registration in the window in this README. Recent work may live in the research session itself: use --events.');
  else if (s.registrations.recentL1 / s.registrations.recent > 0.5) L.push('DRIFT: more than half of recent registrations are L1 variants. New work should come from a family below that has not been run.');
  if (s.events) {
    L.push('Research session messages read: ' + s.events.messages + ', ' + s.events.aboutLive + ' about L1 or its contracts, ' + s.events.aboutOther + ' about other families (' + pct(s.events.aboutLive, s.events.messages) + ' on L1).');
    if (s.events.messages >= 10 && s.events.aboutLive / s.events.messages > 0.5) L.push('DRIFT: most of the research session\'s recent messages are about L1 or its contracts.');
  }
  L.push('');
  L.push('Verdicts on record: ledger ' + JSON.stringify(s.verdicts.ledger) + '; mechanisms index ' + s.verdicts.mech.crossedOff + ' crossed off, ' + s.verdicts.mech.queued + ' queued.');
  L.push('There is no promote verb. NOT_YET_FALSIFIED is not a pass.');
  L.push('');
  L.push('Market families (a mention is not a test; open the source before calling one tried):');
  s.families.forEach((f) => L.push('  ' + (f.mentions ? 'mentioned x' + String(f.mentions).padEnd(4) : 'NOT FOUND   ') + ' ' + (f.live ? '[live strategy] ' : '') + f.label));
  const open = s.families.filter((f) => !f.live && f.mentions === 0).map((f) => f.key);
  L.push('');
  L.push('Never mentioned anywhere: ' + (open.length ? open.join(', ') : 'none') + '.');
  L.push('Weeks (registrations, of which L1 variants): ' + Object.keys(s.registrations.byWeek).sort().map((w) => w + ' ' + s.registrations.byWeek[w].total + '/' + s.registrations.byWeek[w].l1).join('; '));
  return L.join('\n');
}

module.exports = { build, render, registrations, verdicts, FAMILIES, L1_VARIANT };

if (require.main === module) {
  const root = path.resolve(__dirname, '..', '..', '..', '..');
  const sib = path.resolve(root, '..', 'shwoop-server', 'research');
  const pick = (p) => (fs.existsSync(p) ? p : null);
  const s = build({
    readme: arg('readme', path.join(root, 'kalshi-scalper', 'README.md')),
    mechanisms: arg('mechanisms', pick(path.join(sib, 'MECHANISMS.md'))),
    ledger: arg('ledger', pick(path.join(sib, 'ledger', 'runs.jsonl'))),
    events: arg('events', null), days: arg('days', 14), now: arg('now', null),
  });
  console.log(render(s));
}

'use strict';
// Generic forward shadow scorer (Nov 16, 2026, the owner: "not acceptable", for the Head of R&D's 20 to 30 engine survivors). PURE: no network, no file, no clock, no randomness. It takes a frozen spec list and the signals a
// recorder-reading job logged for them, and returns per-spec forward n, wins, net and profit factor at cash, +1c and +2c worse fills, plus a counts-only feed for the Strategies page. It places nothing, reads no key and
// has no promote verb: a spec has no performance parameter, and its verdicts are numbers, never "pass". The job that reads the archive branches and writes the files is separate (it needs the Head's answers on formats).
const { shadowFee } = require('../functions/kalshiShadowLib.js');

const SPEC_KEYS = ['id', 'market', 'entry', 'exit', 'side', 'startUtc', 'target', 'dataBranch'];
const SLIPS = [0, 1, 2];   // cents worse than the price seen: cash, +1c, +2c

function validateSpecs(specs) {
  const errors = [];
  if (!Array.isArray(specs) || !specs.length) return { ok: false, errors: ['the spec list must be a non-empty array'] };
  const seen = new Set();
  specs.forEach((s, i) => {
    const w = 'spec ' + i + ': ';
    if (!s || typeof s !== 'object' || Array.isArray(s)) { errors.push(w + 'not an object'); return; }
    for (const k of Object.keys(s)) if (!SPEC_KEYS.includes(k)) errors.push(w + 'unknown key ' + k + ' (a spec carries no performance parameter)');
    if (typeof s.id !== 'string' || !/^[A-Z][A-Z0-9_-]{1,40}$/.test(s.id)) errors.push(w + 'id must be capital letters, digits, - or _');
    else if (seen.has(s.id)) errors.push(w + 'duplicate id ' + s.id); else seen.add(s.id);
    if (typeof s.market !== 'string' || !s.market) errors.push(w + 'market is required');
    if (!s.entry || typeof s.entry !== 'object' || Array.isArray(s.entry)) errors.push(w + 'entry rule is required');
    if (!s.exit || typeof s.exit !== 'object' || Array.isArray(s.exit)) errors.push(w + 'exit is required');
    if (!['yes', 'no', 'cheap', 'favourite'].includes(s.side)) errors.push(w + 'side must be yes, no, cheap or favourite');
    if (typeof s.startUtc !== 'string' || !Number.isFinite(Date.parse(s.startUtc))) errors.push(w + 'startUtc must be an ISO time');
    if (s.target !== undefined && !(Number.isInteger(s.target) && s.target >= 1 && s.target <= 1000)) errors.push(w + 'target must be an integer 1 to 1000 (a count of signals, not a return)');
  });
  return { ok: !errors.length, errors };
}

// One signal's dollars for one contract. `slipCents` makes the fill that many cents worse (the price paid rises, never past 99c); the fee is charged at the price actually paid.
function signalPnl(sig, slipCents) {
  const p = Math.min(0.99, Number(sig.price) + slipCents / 100);
  const fee = shadowFee(p);
  if (!(p > 0 && p < 1) || !Number.isFinite(fee) || (sig.side !== 'yes' && sig.side !== 'no') || (sig.result !== 'yes' && sig.result !== 'no' && sig.result !== 'void')) return null;
  // The Head of R&D's void ruling (Nov 16, 2026, as the engine core does): a void is scored as a settled trade with the entry fee as the loss (the price is refunded, the fee is kept).
  if (sig.result === 'void') return Math.round(-fee * 10000) / 10000;
  return Math.round((sig.side === sig.result ? 1 - p - fee : -(p + fee)) * 10000) / 10000;
}

function pfNet(pnls) {
  let gw = 0, gl = 0, net = 0;
  for (const x of pnls) { net += x; if (x > 0) gw += x; else gl += -x; }
  return { net: Math.round(net * 10000) / 10000, pf: gl > 0 ? Math.round((gw / gl) * 1000) / 1000 : null, noLosses: gl === 0 && pnls.length > 0 };
}

// `signals`: rows {specId, ticker, side, price, tsMs, fillChecked, result}. One signal per spec and ticker and side (a duplicate is dropped, first by time), only fill-checked signals at or after the spec's start count, and
// a settled signal needs a yes or no result. Output per spec: fillCheckedSignals, settled, wins, and for each slip net (dollars per contract summed) and pf (null when there are no losses).
function scoreSpecs(specs, signals, nowMs) {
  const v = validateSpecs(specs);
  if (!v.ok) throw new Error('invalid spec list: ' + v.errors.join('; '));
  const out = {};
  for (const s of specs) {
    const start = Date.parse(s.startUtc);
    const mine = (signals || []).filter((x) => x && x.specId === s.id && x.fillChecked === true && Number.isFinite(Number(x.tsMs)) && Number(x.tsMs) >= start && Number(x.tsMs) <= nowMs)
      .sort((a, b) => Number(a.tsMs) - Number(b.tsMs) || String(a.ticker).localeCompare(String(b.ticker)));
    const seen = new Set(), uniq = [];
    for (const x of mine) { const k = x.ticker + '|' + x.side; if (!seen.has(k)) { seen.add(k); uniq.push(x); } }
    const settled = uniq.filter((x) => x.result === 'yes' || x.result === 'no' || x.result === 'void');
    const voids = settled.filter((x) => x.result === 'void').length;
    const wins = settled.filter((x) => x.side === x.result).length;
    const slip = {};
    for (const c of SLIPS) slip[c === 0 ? 'cash' : '+' + c + 'c'] = pfNet(settled.map((x) => signalPnl(x, c)).filter((x) => x !== null));
    out[s.id] = { id: s.id, fillCheckedSignals: uniq.length, settled: settled.length, wins, voids, losses: settled.length - wins, slip };
  }
  return out;
}

// The counts-only feed: counts and dates, never a price, a dollar figure or a profit factor.
function countsFeed(specs, scores, nowMs) {
  const asOf = new Date(nowMs).toISOString();
  return { asOf, specs: specs.map((s) => { const r = scores[s.id] || { fillCheckedSignals: 0, settled: 0, wins: 0, voids: 0 };
    return { id: s.id, signals: r.fillCheckedSignals, settled: r.settled, wins: r.wins, voids: r.voids || 0, target: s.target || 60, start_utc: s.startUtc, as_of_utc: asOf }; }) };
}

module.exports = { SPEC_KEYS, SLIPS, validateSpecs, signalPnl, scoreSpecs, countsFeed };

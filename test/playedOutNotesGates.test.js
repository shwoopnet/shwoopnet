'use strict';
// Requested directly: a closed trade's detail modal only ever showed "Why
// this trade" -- the reasoning pinned at ENTRY, frozen forever -- with
// nothing about how it actually ended. buildPlayedOutNotes is the
// companion: entry/exit price and date, realized R against the planned
// risk, a best-effort (never asserted as fact -- see its own comment)
// proximity check against the stop/target, and whether the stop ever
// reached breakeven.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name) {
  const start = html.indexOf('  function ' + name + '(');
  assert.notStrictEqual(start, -1, 'could not find function ' + name + ' in index.html');
  let depth = 0;
  const open = html.indexOf('{', start);
  for (let j = open; j < html.length; j++) {
    if (html[j] === '{') depth++;
    else if (html[j] === '}') { depth--; if (depth === 0) return html.slice(start, j + 1); }
  }
  throw new Error('unbalanced braces for ' + name);
}

function build() {
  const src = `
    function fmt(n){ return '$' + Number(n).toFixed(2); }
    ${lift('computePL')}
    ${lift('niceDateShort')}
    ${lift('calendarDaySpan')}
    ${lift('buildPlayedOutNotes')}
    return buildPlayedOutNotes;
  `;
  return new Function(src)();
}

function main() {
  const buildPlayedOutNotes = build();

  // ---- An open trade gets no "how it played out" at all -- there's no answer yet ----
  {
    const notes = buildPlayedOutNotes({ status: 'open', entry: 10, exit: null });
    assert.deepStrictEqual(notes, [], 'an open trade must produce no played-out notes');
    console.log('G1 PASS an open trade produces no played-out notes');
  }

  // ---- Same-day long trade, stop-loss exit, never reached breakeven ----
  {
    const e = {
      status: 'closed', direction: 'Long', qty: 10,
      entry: 20, exit: 19, stop: 19, t1: 22,
      date: '2026-09-11', exitDate: '2026-09-11',
      reachedEarlyBreakeven: false,
    };
    const notes = buildPlayedOutNotes(e);
    assert.ok(notes[0].includes('closed the same session'), 'same entry/exit date must say "same session", not a day count');
    assert.ok(notes.some((n) => n.includes('-1.00R')), 'exiting exactly at a 1-unit-risk stop must compute to -1.00R');
    assert.ok(notes.some((n) => n.includes('stop-loss exit')), 'an exit price landing on the stop must be flagged as consistent with a stop-loss, not asserted as fact');
    assert.ok(notes.some((n) => n.includes('never reached breakeven')), 'reachedEarlyBreakeven:false must be stated, not silently omitted');
    console.log('G2 PASS same-day long stop-loss exit produces an honest, hedged narrative');
  }

  // ---- Multi-day short trade, target exit, reached breakeven ----
  {
    const e = {
      status: 'closed', direction: 'Short', qty: 5,
      entry: 50, exit: 44, stop: 53, t1: 44,
      date: '2026-09-08', exitDate: '2026-09-11',
      reachedEarlyBreakeven: true,
    };
    const notes = buildPlayedOutNotes(e);
    assert.ok(notes[0].includes('3 calendar days later'), 'a multi-day hold must state a calendar-day span, explicitly not "trading days"');
    assert.ok(notes.some((n) => n.includes('target')), 'an exit price landing on the target must say so');
    assert.ok(notes.some((n) => n.includes('lock the stop at breakeven')) && !notes.some((n) => n.includes('never reached')),
      'reachedEarlyBreakeven:true must read positively, not the negative phrasing');
    console.log('G3 PASS multi-day short target exit with breakeven reads correctly');
  }

  // ---- Exit nowhere near stop or target: no fabricated classification ----
  {
    const e = {
      status: 'closed', direction: 'Long', qty: 10,
      entry: 20, exit: 20.6, stop: 19, t1: 24,
      date: '2026-09-11', exitDate: '2026-09-11',
    };
    const notes = buildPlayedOutNotes(e);
    assert.ok(notes.some((n) => n.includes('trailing-stop, time-stop, or session-close')),
      'an exit away from both the stop and target must say so honestly instead of forcing it into one bucket');
    assert.ok(!notes.some((n) => n.includes('stop-loss exit') || n.includes('right at the') && n.includes('target')),
      'must not also claim a stop or target hit when the price is nowhere near either');
    console.log('G4 PASS an exit near neither level is described honestly, not misclassified');
  }

  console.log('\nAll played-out notes gates passed.');
}

main();

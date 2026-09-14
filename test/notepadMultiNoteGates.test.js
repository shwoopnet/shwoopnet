'use strict';
// The Notepad used to hold exactly one note (a bare string). It's now a
// small array of { id, title, body } switchable via tabs -- these gates
// pin the state-management core: switching commits the outgoing note's
// current text before leaving it, deleting is guarded against ever
// reaching zero notes, an account-synced update that's identical to what's
// already showing is a no-op (no needless re-render/reset), and a synced
// update never clobbers a note that's actively being typed into.

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

function build(overrides) {
  overrides = overrides || {};
  const area = { value: '', focus(){} };
  const storage = {};
  const syncCalls = [];
  const renderCalls = [];
  let activeElement = null;
  let confirmResult = overrides.confirmResult !== undefined ? overrides.confirmResult : true;
  const confirmCalls = [];

  const src = `
    var notepadNotes = [];
    var notepadActiveId = null;
    var document = {
      getElementById: function(id){ return id === 'notepadArea' ? AREA : null; },
      get activeElement(){ return ACTIVE_ELEMENT_HOLDER.value; },
    };
    var window = { localStorage: { setItem: function(k, v){ STORAGE[k] = v; }, getItem: function(k){ return STORAGE[k] || null; } } };
    function syncUserSetting(k, v){ SYNC_CALLS.push([k, v]); }
    function confirm(msg){ CONFIRM_CALLS.push(msg); return CONFIRM_RESULT; }
    // Stubbed, not the real one -- these tests only care about state
    // transitions, not DOM tab-strip construction.
    function renderNotepadTabs(){ RENDER_CALLS.push(1); }
    ${lift('newNotepadNoteId')}
    ${lift('activeNotepadNote')}
    ${lift('saveNotepadNotes')}
    ${lift('switchNotepadNote')}
    ${lift('addNotepadNote')}
    ${lift('deleteNotepadNote')}
    ${lift('applyIncomingNotepadNotes')}
    return {
      setNotes: function(notes, activeId){ notepadNotes = notes; notepadActiveId = activeId; },
      getNotes: function(){ return notepadNotes; },
      getActiveId: function(){ return notepadActiveId; },
      newNotepadNoteId: newNotepadNoteId,
      switchNotepadNote: switchNotepadNote,
      addNotepadNote: addNotepadNote,
      deleteNotepadNote: deleteNotepadNote,
      applyIncomingNotepadNotes: applyIncomingNotepadNotes,
    };
  `;
  // document.activeElement needs to be settable from the test after the
  // module is built -- a holder object with a live getter, read fresh on
  // every access inside the lifted code, lets setActiveElement below
  // change it after the fact.
  const activeElementHolder = { get value(){ return activeElement; } };
  const mod = new Function('AREA', 'STORAGE', 'SYNC_CALLS', 'RENDER_CALLS', 'CONFIRM_CALLS', 'CONFIRM_RESULT', 'ACTIVE_ELEMENT_HOLDER', src)(
    area, storage, syncCalls, renderCalls, confirmCalls, confirmResult, activeElementHolder
  );
  return { mod, area, storage, syncCalls, renderCalls, confirmCalls, setActiveElement: (v) => { activeElement = v; } };
}

function main() {
  // ---- Switching commits the outgoing note's current text first ----
  {
    const { mod, area } = build();
    mod.setNotes([{ id: 'a', title: 'A', body: 'old A text' }, { id: 'b', title: 'B', body: 'old B text' }], 'a');
    area.value = 'freshly typed into A, not saved to the array yet';
    mod.switchNotepadNote('b');
    assert.strictEqual(mod.getNotes()[0].body, 'freshly typed into A, not saved to the array yet',
      'switching away must commit the textarea into the note being left');
    assert.strictEqual(area.value, 'old B text', 'switching to a note must load ITS body into the textarea');
    assert.strictEqual(mod.getActiveId(), 'b');
    console.log('G1 PASS switching notes commits the outgoing text and loads the incoming note\'s body');
  }

  // ---- Adding a note commits current text, creates a fresh empty one, and switches to it ----
  {
    const { mod, area } = build();
    mod.setNotes([{ id: 'a', title: 'Note 1', body: '' }], 'a');
    area.value = 'in progress on note 1';
    mod.addNotepadNote();
    assert.strictEqual(mod.getNotes().length, 2, 'a new note must be appended');
    assert.strictEqual(mod.getNotes()[0].body, 'in progress on note 1', 'the previously-active note\'s text must be committed first');
    assert.strictEqual(mod.getNotes()[1].title, 'Note 2', 'the new note gets a sensible default title');
    assert.strictEqual(mod.getNotes()[1].body, '', 'a brand new note starts empty');
    assert.strictEqual(mod.getActiveId(), mod.getNotes()[1].id, 'the new note becomes active');
    assert.strictEqual(area.value, '', 'the textarea clears for the new, empty note');
    console.log('G2 PASS adding a note commits pending text and switches to a fresh empty one');
  }

  // ---- Deleting is refused when it's the last note, even with confirm() bypassed ----
  {
    const { mod, confirmCalls } = build();
    mod.setNotes([{ id: 'a', title: 'Only one', body: 'text' }], 'a');
    mod.deleteNotepadNote('a');
    assert.strictEqual(mod.getNotes().length, 1, 'the last remaining note must never be deletable');
    assert.strictEqual(confirmCalls.length, 0, 'must not even prompt for confirmation on the last note -- there is nothing valid to confirm');
    console.log('G3 PASS deleting the last remaining note is refused outright');
  }

  // ---- Deleting a non-last note asks for confirmation, and a "cancel" leaves it untouched ----
  {
    const { mod, confirmCalls } = build({ confirmResult: false });
    mod.setNotes([{ id: 'a', title: 'A', body: '' }, { id: 'b', title: 'B', body: '' }], 'a');
    mod.deleteNotepadNote('b');
    assert.strictEqual(confirmCalls.length, 1, 'deleting a non-last note must ask for confirmation');
    assert.strictEqual(mod.getNotes().length, 2, 'declining the confirmation must leave both notes intact');
    console.log('G4 PASS deleting a non-last note confirms first, and declining changes nothing');
  }

  // ---- Deleting the ACTIVE note falls back to a neighbor, not a dangling reference ----
  {
    const { mod, area } = build({ confirmResult: true });
    mod.setNotes([{ id: 'a', title: 'A', body: 'a text' }, { id: 'b', title: 'B', body: 'b text' }], 'b');
    mod.deleteNotepadNote('b');
    assert.strictEqual(mod.getNotes().length, 1);
    assert.strictEqual(mod.getActiveId(), 'a', 'deleting the active note must fall back to a real remaining note');
    assert.strictEqual(area.value, 'a text', 'the textarea must load the fallback note\'s own body');
    console.log('G5 PASS deleting the active note falls back to a neighboring note, not a dangling id');
  }

  // ---- An incoming sync identical to current state is a true no-op ----
  {
    const { mod, storage, renderCalls } = build();
    const notes = [{ id: 'a', title: 'A', body: 'same' }];
    mod.setNotes(notes, 'a');
    mod.applyIncomingNotepadNotes([{ id: 'a', title: 'A', body: 'same' }]);
    assert.strictEqual(renderCalls.length, 0, 'an identical incoming set must not trigger any re-render');
    assert.strictEqual(storage['shwoopnet:notepadNotes'], undefined, 'an identical incoming set must not even re-write localStorage');
    console.log('G6 PASS an incoming sync identical to current state changes nothing');
  }

  // ---- An incoming sync must never overwrite text while it's actively being typed ----
  {
    const { mod, area, setActiveElement } = build();
    mod.setNotes([{ id: 'a', title: 'A', body: 'old' }], 'a');
    area.value = 'mid-keystroke, not yet committed to notepadNotes';
    setActiveElement(area); // the textarea currently has focus
    mod.applyIncomingNotepadNotes([{ id: 'a', title: 'A', body: 'a change from another device' }]);
    assert.strictEqual(area.value, 'mid-keystroke, not yet committed to notepadNotes',
      'the textarea must not be overwritten while it has focus, even for a real incoming change');
    assert.strictEqual(mod.getNotes()[0].body, 'a change from another device',
      'the underlying data must still update -- only the live-focused textarea is protected');
    console.log('G7 PASS an incoming sync never clobbers text that\'s actively being typed');
  }

  console.log('\nAll notepad multi-note gates passed.');
}

main();

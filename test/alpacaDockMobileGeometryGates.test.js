'use strict';
// A saved Alpaca dock drag/resize geometry (shwoopnet:alpacaDockGeo) used
// to be restored as an INLINE style on every load regardless of viewport
// width -- an inline style always wins over the @media(max-width:900px)
// rule that lays the dock out full-width above the mobile bottom nav. A
// geometry saved from any wider session (desktop, a tablet in landscape,
// a browser window later resized down) then permanently overrode the
// mobile layout, positioning the dock wherever it happened to be dragged
// to on a completely different screen size -- reported as "awkward on
// mobile navigation." isMobileDockLayout() gates geometry restoration and
// drag/resize start behind "is the sidebar currently a vertical rail," the
// same signal maxLeftClearingSidebar already used to distinguish desktop
// from mobile.

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

function fakeSideNav(height) {
  return { getBoundingClientRect(){ return { height: height }; } };
}

function main() {
  // ---- isMobileDockLayout itself: a real unit, testable in isolation ----
  {
    const src = `
      var window = { innerHeight: 800 };
      var document = { getElementById: function(id){ return id === 'sideNav' ? SIDE_NAV : null; } };
      ${lift('isMobileDockLayout')}
      return isMobileDockLayout;
    `;
    const isMobileDockLayout = new Function('SIDE_NAV', src);

    assert.strictEqual(isMobileDockLayout(fakeSideNav(700))(), false,
      'a tall sidebar (a vertical rail, taller than half the viewport) means the DESKTOP layout');
    assert.strictEqual(isMobileDockLayout(fakeSideNav(76))(), true,
      'a short sidebar (a bottom bar) means the MOBILE layout');
    assert.strictEqual(isMobileDockLayout(null)(), false,
      'no sidebar element at all must default to desktop, never crash');
    console.log('G1 PASS isMobileDockLayout distinguishes vertical-rail (desktop) from bottom-bar (mobile)');
  }

  // ---- The three places geometry could leak onto mobile must all gate on it ----
  {
    const initFn = html.slice(
      html.indexOf('(function initAlpacaDockGeometry('),
      html.indexOf('})();', html.indexOf('(function initAlpacaDockGeometry('))
    );
    assert.ok(/if\(isMobileDockLayout\(\)\) return;/.test(initFn),
      'restoring a saved geometry on init must bail out entirely on the mobile layout');

    const headerPointerdown = html.slice(
      html.indexOf("alpacaDockHeaderEl.addEventListener('pointerdown'"),
      html.indexOf("alpacaDockHeaderEl.addEventListener('pointermove'")
    );
    assert.ok(/isMobileDockLayout\(\)/.test(headerPointerdown),
      'starting a drag from the header must be gated on the mobile layout too, not just on init');

    const resizePointerdown = html.slice(
      html.indexOf("alpacaDockResizeHandle.addEventListener('pointerdown'"),
      html.indexOf("alpacaDockResizeHandle.addEventListener('pointermove'")
    );
    assert.ok(/isMobileDockLayout\(\)/.test(resizePointerdown),
      'starting a resize from the handle must be gated on the mobile layout too');
    console.log('G2 PASS geometry restoration and both drag/resize start points all gate on isMobileDockLayout');
  }

  console.log('\nAll Alpaca dock mobile-geometry gates passed.');
}

main();

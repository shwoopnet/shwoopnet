'use strict';
// "Remember me" controls whether Firebase's own session survives closing
// the browser (browserLocalPersistence -- the SDK's own default) or ends
// with it (browserSessionPersistence). These gates pin: the checkbox's
// own preference is restored from localStorage on load (defaulting to
// checked, matching the SDK's implicit prior behavior for anyone who's
// never touched the control), and that setPersistence is wired to run
// BEFORE the actual sign-in call -- it configures how the credential that
// call is about to produce gets stored, not something that could be
// applied retroactively afterward. Sign-in is the only auth flow: there is
// no sign-up on the page.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function main() {
  // ---- initAuthRememberMe: restores the saved preference, defaults to checked ----
  {
    const start = html.indexOf('(function initAuthRememberMe(');
    assert.notStrictEqual(start, -1, 'could not find initAuthRememberMe in index.html');
    const end = html.indexOf('})();', start) + '})();'.length;
    const iife = html.slice(start, end);

    function run(storedValue) {
      const checkboxEl = { checked: false };
      const src = `
        var document = { getElementById: function(id){ return id === 'authRememberMe' ? CHECKBOX : null; } };
        var window = { localStorage: { getItem: function(k){ return k === 'shwoopnet:authRememberMe' ? STORED : null; } } };
        ${iife}
      `;
      new Function('CHECKBOX', 'STORED', src)(checkboxEl, storedValue);
      return checkboxEl.checked;
    }

    assert.strictEqual(run(null), true, 'a first-time visitor (nothing stored yet) must default to checked');
    assert.strictEqual(run('true'), true, 'an explicit stored "true" must check the box');
    assert.strictEqual(run('false'), false, 'an explicit stored "false" must leave the box unchecked');
    console.log('G1 PASS the remember-me checkbox restores the saved preference, defaulting to checked');
  }

  // ---- The submit handler must read the checkbox and thread it through sign-in, and there is no other flow ----
  {
    const start = html.indexOf("authFormEl.addEventListener('submit'");
    assert.notStrictEqual(start, -1, 'could not find the auth form submit handler');
    const end = html.indexOf('\n  });', start);
    const handler = html.slice(start, end);

    assert.ok(/var rememberMe = document\.getElementById\('authRememberMe'\)\.checked;/.test(handler),
      'the submit handler must read the checkbox\'s current state');
    assert.ok(/window\.__shwoopAPI\.signIn\(email, password, rememberMe\)/.test(handler),
      'sign-in must pass rememberMe through to the API');
    assert.ok(!/signUp|createUser|redeemInvite/.test(handler), 'the form has no sign-up path: an account is created by hand, never from this page');
    console.log('G2 PASS the submit handler reads the checkbox and passes it to signIn, and has no sign-up branch');
  }

  // ---- setPersistence must resolve before the actual Firebase auth call ----
  {
    const signInMatch = html.match(/signIn: function\(email, password, rememberMe\)\{([\s\S]{0,300}?)\},/);
    assert.ok(signInMatch, 'could not find the signIn API method');
    assert.ok(/withPersistence\(rememberMe\)\.then\(function\(\)\{\s*\n\s*return signInWithEmailAndPassword/.test(signInMatch[1]),
      'signIn must call withPersistence and wait for it to resolve before signInWithEmailAndPassword');
    assert.ok(!/signUp:|createUserWithEmailAndPassword/.test(html), 'the API has no way to create an account');
    console.log('G3 PASS signIn sets persistence before the actual Firebase auth call, and nothing can create an account');
  }

  console.log('\nAll auth remember-me gates passed.');
}

main();

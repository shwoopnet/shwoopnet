// The sign-in box shows the real wordmark, so a visitor's first look at the brand is the same logo as everywhere else.
const assert=require('assert'),fs=require('fs'),path=require('path');
const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
const box=html.slice(html.indexOf('id="authGate"'),html.indexOf('class="auth-title"'));
assert.ok(/class="brand-name"/.test(box)&&/class="brand-fin"/.test(box),'the sign-in box uses the wordmark classes');
assert.ok(!/<svg/.test(box),'the old wallet icon is gone from the sign-in box');
assert.ok(/>S<\/span><span>H<\/span><span>W<\/span><span>O<\/span><span>O<\/span><span>P</.test(box),'it spells SHWOOP');
console.log('signInWordmarkGates: ok');

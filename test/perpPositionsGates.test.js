const fs=require('fs'),assert=require('assert');
const h=fs.readFileSync('index.html','utf8');
const m=h.match(/function kalshiPerpRisk[\s\S]*?function kalshiPerpRows\(a\)\{[^\n]*\n/);
assert(m,'PP1 functions present');
const f=new Function(m[0]+';return {kalshiPerpsHtml,kalshiPerpRisk,kalshiPerpRows,kalshiPerpsFromDoc,kalshiPerpsNote};')();
const esc=s=>String(s).replace(/</g,'&lt;'), money=v=>'$'+v.toFixed(2);
const row={market:'Bitcoin <x>',up:true,multiplier:27.4,cost:10,size:274,entry:90000,index:91000,value:12.5,pnl:2.5,pnlPct:25,takeProfit:95000,stopLoss:88000,closeAt:87000,bufferPct:27};
const out=f.kalshiPerpsHtml([row],esc,money);
for(const t of ['Perp','27.4x','UP','Current value','Leveraged size','Entered at','Low risk, 27% buffer','Closes at 87,000','Take profit 95,000','+$2.50 (+25.0%)','Bitcoin &lt;x>'])assert(out.includes(t),'PP2 '+t);
assert(f.kalshiPerpsHtml([],esc,money)==='','PP3 empty');
assert(f.kalshiPerpsHtml([{market:'X',up:false}],esc,money).includes('Auto close levels not readable'),'PP3 sparse: unknown is never shown as none set');
assert(f.kalshiPerpsHtml([{market:'X',up:false,autoKnown:true}],esc,money).includes('No auto close set'),'PP3 none set only when the data says so');
assert(f.kalshiPerpRisk(5).label.startsWith('High')&&f.kalshiPerpRisk(15).label.startsWith('Medium'),'PP4');
assert.deepStrictEqual(f.kalshiPerpRows({}),[]);
// PP5: the real doc shape (Main, Nov 17): value is margin plus pnl, cost is margin, the multiplier is an estimate, optional rows hide, nothing is invented.
const now=1e12;
const doc={at:now-60000,equity:50,rows:[{market:'KXBTCPERP',up:true,size:3,entry:90000,pnl:2.5,margin:10,fees:0.1,mark:91000,multiplierEstimate:10,closeAt:null,bufferPct:null,takeProfit:null,stopLoss:null}]};
const r=f.kalshiPerpsFromDoc(doc,now);
assert(r.ok&&r.total===50&&r.rows.length===1,'PP5 ok');
assert.strictEqual(r.rows[0].value,12.5);assert.strictEqual(r.rows[0].cost,10);assert.strictEqual(r.rows[0].pnlPct,25);assert.strictEqual(r.rows[0].size,null);
const html=f.kalshiPerpsHtml(r.rows,esc,money);
assert(html.includes('~10.0x est.'),'PP5 multiplier is labelled an estimate');
assert(!html.includes('Leveraged size'),'PP5 leveraged size hidden while its unit is unconfirmed');
assert(html.includes('Index now')&&html.includes('Closes at n/a')&&html.includes('Buffer n/a')&&html.includes('Auto close levels not readable'),'PP5 n/a and not readable wording');
assert(!html.includes('No auto close set')&&!html.includes('High risk')&&!html.includes('kal-perp-bar'),'PP5 never claims none is set, never a made-up buffer or bar');
// PP6: a missing mark hides Index now
assert(!f.kalshiPerpsHtml(f.kalshiPerpsFromDoc({at:now,equity:1,rows:[{market:'X',up:false,entry:1,pnl:0,margin:5,mark:null,multiplierEstimate:null}]},now).rows,esc,money).includes('Index now'),'PP6');
// PP7: older than 20 minutes or no document hides the perps part and says why
assert.strictEqual(f.kalshiPerpsFromDoc({at:now-21*60000,equity:50,rows:[]},now).ok,false);
assert(/older than 20 minutes/.test(f.kalshiPerpsNote(f.kalshiPerpsFromDoc({at:now-21*60000,equity:50,rows:[]},now))));
assert(/no perps data/.test(f.kalshiPerpsNote(f.kalshiPerpsFromDoc(null,now))));
assert.strictEqual(f.kalshiPerpsFromDoc({at:now-19*60000,equity:50,rows:[]},now).ok,true);
// PP8: still not wired to a read (the units are unconfirmed)
assert(!/kalshiLiveControl\/perpsAccount/.test(h.replace(/\/\/[^\n]*/g,'')),'PP8 no live read of the perps doc yet');
console.log('perpPositionsGates ok');

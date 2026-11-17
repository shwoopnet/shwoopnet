const fs=require('fs'),assert=require('assert');
const h=fs.readFileSync('index.html','utf8');

const m=h.match(/function kalshiPerpRisk[\s\S]*?function kalshiPerpRows\(a\)\{[^\n]*\n/);
assert(m,'PP1 functions present');
const f=new Function('KAL_TZ',m[0]+';return {kalshiPerpChartHtml,kalshiPerpCushion,kalshiPerpsHtml,kalshiPerpRisk,kalshiPerpRows,kalshiPerpsFromDoc,kalshiPerpsNote};')('America/Chicago');
const esc=s=>String(s).replace(/</g,'&lt;'), money=v=>'$'+v.toFixed(2);
const row={market:'Bitcoin <x>',up:true,multiplier:27.4,cost:10,size:274,entry:90000,index:91000,value:12.5,pnl:2.5,pnlPct:25,takeProfit:95000,stopLoss:88000,closeAt:87000,bufferPct:27};
const out=f.kalshiPerpsHtml([row],esc,money);
for(const t of ['Perp','UP','Position value','Entered at','+$2.50 (+25.0%)','Bitcoin &lt;x>'])assert(out.includes(t),'PP2 '+t);
assert(f.kalshiPerpsHtml([],esc,money)==='','PP3 empty');
assert(f.kalshiPerpRisk(5).label.startsWith('High')&&f.kalshiPerpRisk(15).label.startsWith('Medium'),'PP4');
assert.deepStrictEqual(f.kalshiPerpRows({}),[]);
// PP5: the real doc shape (Main, Nov 17): units confirmed: pnl is dollars, size is contracts, value is size times mark, margin is maintenance margin (so no cost and no return percent), the multiplier is an estimate, optional rows hide, nothing is invented.
const now=1e12;
const doc={at:now-60000,equity:50,rows:[{market:'KXBTCPERP',up:true,size:3,entry:90000,pnl:2.5,margin:10,fees:0.1,mark:91000,multiplierEstimate:10,closeAt:null,bufferPct:null,takeProfit:null,stopLoss:null}]};
const r=f.kalshiPerpsFromDoc(doc,now);
assert(r.ok&&r.total===50&&r.rows.length===1,'PP5 ok');
assert.strictEqual(r.rows[0].value,273000);assert.strictEqual(r.rows[0].cost,null);assert.strictEqual(r.rows[0].pnlPct,null);assert.strictEqual(r.rows[0].size,3);
const html=f.kalshiPerpsHtml(r.rows,esc,money);
assert(!html.includes('Cost')&&!html.includes('Leveraged size')&&!/\(\+?-?[\d.]+%\)/.test(html),'PP5 no Cost and no return percent: margin is maintenance margin');
assert(!/Buffer|Closes at|Auto close|not one of the bot|est\./i.test(html),'PP5 bare minimum: no extra text');
assert(html.includes('Position value')&&html.includes('+$2.50'),'PP5 position value, contracts and pnl in dollars');
assert(html.includes('Now'),'PP5 now');
// PP6: a missing mark hides Index now
assert(!f.kalshiPerpsHtml(f.kalshiPerpsFromDoc({at:now,equity:1,rows:[{market:'X',up:false,entry:1,pnl:0,margin:5,mark:null,multiplierEstimate:null}]},now).rows,esc,money).includes('Now'),'PP6');
// PP7: older than 20 minutes or no document hides the perps part and says why
assert.strictEqual(f.kalshiPerpsFromDoc({at:now-21*60000,equity:50,rows:[]},now).ok,false);
assert(/older than 20 minutes/.test(f.kalshiPerpsNote(f.kalshiPerpsFromDoc({at:now-21*60000,equity:50,rows:[]},now))));
assert(/no perps data/.test(f.kalshiPerpsNote(f.kalshiPerpsFromDoc(null,now))));
assert.strictEqual(f.kalshiPerpsFromDoc({at:now-19*60000,equity:50,rows:[]},now).ok,true);
// PP9: the account-level margin cushion (equity minus maintenance, dollars), labelled as NOT a forced-close price; a move share only for one position; risk by percent of equity; invented numbers.
let cu=f.kalshiPerpCushion({equity:100,maintenance:20,positionValue:400},1);
assert.strictEqual(cu.dollars,80);assert.strictEqual(Math.round(cu.pct),80);assert.strictEqual(cu.move,20,'PP9 one position: cushion over position value');
assert.strictEqual(f.kalshiPerpCushion({equity:100,maintenance:20,positionValue:400},2).move,null,'PP9 several positions: no move share');
assert(f.kalshiPerpCushion({equity:100,maintenance:95},1).risk.label.startsWith('High'),'PP9 under 10% is High');
assert(f.kalshiPerpCushion({equity:100,maintenance:85},1).risk.label.startsWith('Medium'),'PP9 10 to 20% is Medium');
assert.strictEqual(f.kalshiPerpCushion({equity:0,maintenance:0},1),null,'PP9 no equity, no cushion');
assert.strictEqual(f.kalshiPerpCushion({equity:50},1),null,'PP9 no maintenance figure, no cushion');
const cdoc=f.kalshiPerpsFromDoc({at:now,equity:100,maintenance:20,positionValue:400,rows:[{market:'X',up:true,size:1,entry:1,pnl:0,margin:20,mark:1,multiplierEstimate:5}]},now);
const ch=f.kalshiPerpsHtml(cdoc.rows,esc,money,cdoc.cushion);
{const cu1=f.kalshiPerpsHtml(cdoc.rows,esc,money,cdoc.cushion);assert(cu1.includes('Account margin cushion (equity minus maintenance, not a forced-close price): $80.00')&&cu1.includes('kal-perp-bar')&&/Low risk/.test(cu1),'PP9 one line: dollars, label, bar, account level');assert(!/move of about|before fees/.test(cu1),'PP9 no extra sentence');assert(!f.kalshiPerpsHtml(cdoc.rows,esc,money,null).includes('cushion'),'PP9 no cushion without data');}
// PP8: wired (Nov 17): one read of the perps doc and one of the hourly snapshots, never a write; the view lays the perps over the account read and Today uses the last snapshot of an earlier Central day.
const live=h.replace(/\/\/[^\n]*/g,'');
assert(/getDoc\(doc\(db, 'kalshiLiveControl', 'perpsAccount'\)\)/.test(live)&&/collection\(db, 'kalshiBalanceSnaps'\)/.test(live),'PP8 reads the two sources');
assert(!/(setDoc|updateDoc|addDoc)\([^)]*perpsAccount/.test(live),'PP8 never writes it');
const w=new Function('kalDayKey','kalshiPerpsFromDoc','kalshiPerpsNote',h.match(/var kalshiPerpsState[\s\S]*?function kalshiPerpsEnsure/)[0].replace(/function kalshiPerpsEnsure$/,'')+';return {kalshiPerpsView,kalshiPerpsState};')(t=>new Date(t).toISOString().slice(0,10),f.kalshiPerpsFromDoc,f.kalshiPerpsNote);
const base={balance:{ok:true,totalDollars:100}};
let v=w.kalshiPerpsView(base,now);assert.strictEqual(v.perpsTotal,undefined,'PP8 no doc, no perps');
w.kalshiPerpsState.loaded=true;w.kalshiPerpsState.doc={at:now-1000,equity:50,rows:[]};
w.kalshiPerpsState.hist=[{t:now-2*86400000,total:40},{t:now-86400000,total:45}];
v=w.kalshiPerpsView(base,now);assert.strictEqual(v.perpsTotal,50);assert.strictEqual(v.perpsDay,5,'PP8 today is equity minus the last earlier-day snapshot');assert.strictEqual(v.perpsHistory.length,3);
w.kalshiPerpsState.doc.at=now-21*60000;v=w.kalshiPerpsView(base,now);assert.strictEqual(v.perpsTotal,undefined);assert(/older than 20 minutes/.test(v.perpsNote),'PP8 stale drops perps and says why');
console.log('perpPositionsGates ok');
// PP10: a perp row draws a price line with a dashed entry line once there are two marks; before that it says what it waits for, and a missing mark list never breaks the row.
const mk=[{t:1e12,v:90000},{t:1e12+240000,v:91000},{t:1e12+480000,v:90500}];
const chh=f.kalshiPerpsHtml([row],esc,money,null,{[row.market]:mk});
assert(chh.includes('kal-perp-chart')&&chh.includes('kal-hc-target-line')&&chh.includes('data-hv='),'PP10 chart with entry line and hover');
{const one=f.kalshiPerpsHtml([row],esc,money,null,{[row.market]:[mk[0]]});assert(!one.includes('kal-perp-chart"')&&one.includes('Price line builds while this page is open (needs two reads).'),'PP10 one mark: no chart, one plain line');}
assert(!f.kalshiPerpsHtml([row],esc,money).includes('kal-perp-chart"')&&f.kalshiPerpsHtml([row],esc,money).includes('needs two reads'),'PP10 no marks: no chart, no error, one plain line');
// PP11: the result line is never cut to the first perps snapshot (the page code does not move `since` to ph.first)
assert(!/since = Math\.max\(since, ph\.first\)/.test(h),'PP11 range not cut by perps history');

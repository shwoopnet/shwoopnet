const fs=require('fs'),assert=require('assert');
const h=fs.readFileSync('index.html','utf8');
const m=h.match(/function kalshiAccountTotal[\s\S]*?\n  function kalshiLiveTotals/);
assert(m,'AT1 helpers present');
const f=new Function(m[0].replace(/function kalshiLiveTotals$/,'')+';return {kalshiAccountTotal,kalshiPerpsSteps};')();
const bal={ok:true,totalDollars:600.5};
// AT1: predictions only when perps are absent (the live page today)
let t=f.kalshiAccountTotal({balance:bal});
assert.strictEqual(t.total,600.5);assert.strictEqual(t.perps,false);assert.strictEqual(t.day,0);
// AT2: total is predictions plus perps, total only
t=f.kalshiAccountTotal({balance:bal,perpsTotal:99.5,perpsDay:-3});
assert.strictEqual(t.total,700);assert.strictEqual(t.perps,true);assert.strictEqual(t.day,-3);
// AT3: no prediction balance means no total (never a perps-only figure)
assert.strictEqual(f.kalshiAccountTotal({balance:{ok:false},perpsTotal:5}).total,null);
assert.strictEqual(f.kalshiAccountTotal(null).total,null);
// AT4: perps history starts at the first snapshot; steps are differences; nothing invented before it
const s=f.kalshiPerpsSteps([{t:3000,total:105},{t:1000,total:100},{t:2000,total:100}],0);
assert.strictEqual(s.first,1000);assert.deepStrictEqual(s.steps.map(x=>[x.t,x.p]),[[3000,5]]);
assert.strictEqual(f.kalshiPerpsSteps([],0).first,null);
// AT5: display only, checked by INTENT. The code that decides a stop, a loss limit, the window cap or a size must never read the combined total or the perps fields. Data code (the hourly balance snapshot, the report,
// the account read) may name them: that is how the total reaches the page. Risk code is every functions/ file that is not data code, so a new risk file is covered by default.
const RISK_NAMED = /Live|Slot|HardStop|RiskCore|GoldKill|Rotation|Wheel|Sizing|Shadow|Longhold|Cfrti|Spxoi|Exit|Alarm|ShardAlert|Kill/;
const FIELDS = /perpsTotal|perpsDay|perpsHistory|kalshiAccountTotal|account_equity/;
const riskFiles = fs.readdirSync('functions').filter(x => x.endsWith('.js') && RISK_NAMED.test(x) && !/Snapshot|Report|Account|Balance|Probe|Push/.test(x));
assert(riskFiles.length >= 8, 'AT5 sees the risk files: ' + riskFiles.join(','));
for(const file of riskFiles){
  assert(!FIELDS.test(fs.readFileSync('functions/' + file, 'utf8')), 'AT5 ' + file + ' is risk code and must not read the display total');
}
assert(/never read by the 40% hard stop/.test(h)||/is never read by the 40% hard stop/.test(h),'AT5 comment says display only');
console.log('accountTotalGates ok');

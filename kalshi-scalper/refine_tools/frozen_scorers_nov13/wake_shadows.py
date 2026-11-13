#!/usr/bin/env python3
# W96: S-JUMP1 (OIR band table) and S-SDIR1 (sdir table), registered read at 40 fills. Read only; thresholds as in forward_oicore.py.
import sys,subprocess,os,re
H=os.path.dirname(os.path.abspath(__file__)); rep=sys.argv[1] if len(sys.argv)>1 else os.path.join(H,'dash_report.json')
r=subprocess.run(['python3','-I',os.path.join(H,'forward_oicore.py'),rep],capture_output=True,text=True,timeout=400)
out=r.stdout
def block(h):
    m=re.search(r'^\(%s\).*?\n(.*?)(?:\n\n|\Z)'%h,out,re.S|re.M)
    return ('('+h+')'+m.group(0).split(')',1)[1]) if m else '(%s) missing'%h
n=None
m=re.search(r'^all\s+\d+\s+(\d+)',out,re.M)
if m: n=int(m.group(1))
for nm,h in(('S-JUMP1 (OIR bands)','c1'),('S-SDIR1 (sdir split)','c2')):
    print('== %s: %s of 40 fills =='%(nm,'?' if n is None else n)); print(block(h))
    if n is not None and n>=40: print('FLAG: %s at %d fills: READ NOW (registered read at 40)'%(nm.split()[0],n))
if n is None: print('WARNING: could not parse fill count; stderr:',r.stderr[-200:])
print(subprocess.run(['python3','-I',os.path.join(H,'c2_fwd.py'),rep],capture_output=True,text=True,timeout=60).stdout)  # W98 C2, FLAG at 40
# W130 FLOW1 retired (live registry, #711/#712); flags block and ledger FLAG removed
print('FLOW1 retired 2026-11-04, final live record 2 orders, 1 filled, -0.64')
# W126 S-OIRLOW1 (OIR 60000-86300 forward, read at 40 windows)
print('== S-OIRLOW1 =='); print(subprocess.run(['python3','-W','ignore','-I',os.path.join(H,'oirlow1_forward.py')],capture_output=True,text=True,timeout=300).stdout.strip())

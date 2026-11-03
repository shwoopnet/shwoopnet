"""REV1SPLIT history information (NOT the registered read): the REV1 split from Aug 6, thirds W1 and W2 only, last third never read. python -m scalper.rev1_split_history"""
from . import rev1, gen6, mechoi1
wins = rev1.split_windows(gen6.DISC[0], 2**40)
dated = sorted({mechoi1.day_of(ct) for tk,ct,res,cs in wins if rev1.window_doi(cs,ct) is not None})
t1,t2,t3 = mechoi1.split_dates(dated)
print("dates", dated[0], dated[-1], len(dated), "W1", t1[0], t1[-1], "W2", t2[0], t2[-1], "holdout starts", t3[0], "(not read)")
keep = set(t1)|set(t2)
fee = lambda p: gen6.fee(p, 10)
def run(name, **kw):
    rows = [r for r in rev1.split_entries(wins, fee_fn=fee, **kw) if r["day"] in keep]
    print("=====", name)
    print(rev1.split_report(rows))
    for lab, ds in (("W1", set(t1)), ("W2", set(t2))):
        sub = [r for r in rows if r["day"] in ds]
        for k in ("yes","no"):
            print(lab, "fixed", k); print(rev1._line("   ", [r for r in sub if r["fixed"]==k]))
run("REV1 as registered (NO, 0.03-0.45, 120/180s)")
run("REF_BTC_UNDERDOG_180 (both sides 0.15-0.49, 180s)", looks=(180,), sides=("yes","no"), lo=0.15, hi=0.4901)

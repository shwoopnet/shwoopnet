"""ADJWIN1 runner (Desk A, Nov 15 2026): loader -> core -> one printed table of all 22 tries. Sends nothing, writes only stdout.
  python3 -I adjwin1_run.py <dir holding the pull run folders>      (refuses inside the loader until the allow line is merged)
Prints the drop counts first, then for every series x arm x haircut the development and validation n, PF, halves, day z, trade days, evidence label. Upper bound, not fill-checked; voids are dropped (small optimistic bias). No pooled figure."""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adjwin1_load as L, adjwin1 as A
def table(res, dropped):
    out = ["DROPPED: " + json.dumps(dropped, sort_keys=True), "label: upper bound, not fill-checked; voids dropped; 22 tries (11 series x arms R and M); development closes before 2026-09-01, validation 2026-09-01 to 2026-10-03T15:59:59Z"]
    for s in sorted(res):
        out.append("%s skips %s" % (s, json.dumps(res[s]["skips"], sort_keys=True)))
        for arm in "RM":
            for h in ("h0", "h1", "h2"):
                for ph in ("dev", "val"):
                    x = res[s]["arms"][arm][h][ph]
                    out.append("  %s arm %s %s %s n=%d pf=%.3f half1=%.3f half2=%.3f z=%s days=%d [%s]" % (s, arm, h, ph, x["n"], x["pf"], x["half1"], x["half2"], "none" if x["day_z"] is None else "%.2f" % x["day_z"], x["trade_days"], x["evidence"]))
    return "\n".join(out)
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    w, c = L.load(sys.argv[1])
    print("rule hashes: core %s loader %s runner %s" % tuple(hashlib.sha256(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f), "rb").read()).hexdigest()[:16] for f in ("adjwin1.py", "adjwin1_load.py", "adjwin1_run.py")))
    print(table(A.run(w), c))

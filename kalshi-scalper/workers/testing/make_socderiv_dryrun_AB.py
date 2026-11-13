"""Dry run of the SOCDERIV candle read on INVENTED files in the layout runs A and B will land in (Testing Desk). Usage: python3 make_socderiv_dryrun_AB.py <out folder>
Takes the invented real-layout case_15 (lists and candle answers), builds the job from the lists, splits it as SOCDERIV_CANDLES_A and _B, and writes two run folders each with the manifest as the pull runner writes it
(status complete, job = that part's job file, rows = id, page, status 200, file NNNN.json.gz; the request ids keep their numbers across the parts) plus the lists run. Prints nothing real: every price is invented."""
import gzip, json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import socderiv as s
out = sys.argv[1]; src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "socderiv_fixture_inputs_MADE_UP_DATA", "case_15")
spec = s.load_cells(); jc, _ = s.build_candles(spec, [os.path.join(src, "lists")]); A, B = s.split_candles(jc)
by = {}
for r in json.load(open(os.path.join(src, "candles", "manifest.json")))["rows"]:
    by[r["id"]] = json.load(gzip.open(os.path.join(src, "candles", r["file"]), "rt"))
shutil.copytree(os.path.join(src, "lists"), os.path.join(out, "pull", "SOCDERIV_LISTS", "2026-11-13T0806Z_900000001"))
for name, job, stamp in (("A", A, "2026-11-13T1000Z_900000002"), ("B", B, "2026-11-13T1010Z_900000003")):
    d = os.path.join(out, "pull", "SOCDERIV_CANDLES_" + name, stamp); os.makedirs(d); rows = []
    for i, r in enumerate(job["requests"]):
        f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(by[r["id"]])); rows.append({"index": i + 1, "id": r["id"], "page": 1, "status": 200, "file": f})
    json.dump({"job": job, "status": "complete", "requests_sent": len(rows), "rows": rows}, open(os.path.join(d, "manifest.json"), "w"))
    open(os.path.join(d, "STATUS"), "w").write("complete\n")
print(json.dumps({"A_requests": len(A["requests"]), "B_requests": len(B["requests"])}))

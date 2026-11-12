"""Loads the scratch output of a MENTPERSIST1 pull job into data/ment1.sqlite (tables candle, done), the same
way `mentpersist1.py fetch` does. Offline: no network. Usage: python3 -I src/scalper/pulljobs_ingest.py JOB_ID"""
import os, sys, json, sqlite3
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
def main(job_id):
    job = json.load(open(os.path.join(ROOT, "workers", "pulljobs", job_id + ".json")))
    if not job_id.startswith("MENTPERSIST1"): raise SystemExit("only MENTPERSIST1 jobs have an ingest step")
    log = json.load(open(os.path.join(ROOT, "workers", "pulljobs", job_id + "_READLOG.json")))
    db = sqlite3.connect(os.path.join(ROOT, "data", "ment1.sqlite")); n = z = 0
    f = lambda v: None if v in (None, "") else float(v)
    for r in log["requests"]:
        tk = r["id"]
        if r["status"] == 404: db.execute("INSERT OR REPLACE INTO done VALUES(?,0)", (tk,)); z += 1; continue
        if r["status"] != 200: continue
        p = os.path.join(job["output_dir"], tk + ".json")
        if not os.path.exists(p): continue
        rs = [(tk, int(x["end_period_ts"]), f((x.get("yes_bid") or {}).get("close")), f((x.get("yes_ask") or {}).get("close")))
              for x in json.load(open(p)).get("candlesticks", []) if x.get("end_period_ts") is not None]
        db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", rs); db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (tk, len(rs))); n += 1
    db.commit(); print("ingested", n, "markets,", z, "empty")
if __name__ == "__main__": main(sys.argv[1])

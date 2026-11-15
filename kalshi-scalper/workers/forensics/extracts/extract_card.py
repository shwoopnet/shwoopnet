#!/usr/bin/env python3
"""One-extractor tool (Forensics desk, Nov 15, 2026; the Head's order of 14:34Z). Builds ONE extract per card from the research-data archive.
Reads only the columns named in the spec, only markets whose close is inside [start, end) and not inside any cut; writes a new sqlite plus a cut log (JSON).
usage: python3 -I extract_card.py <spec.json> <archive_dir> <out_dir>
spec: {card, sources:[ordered db names, first file wins on a duplicate ticker], series:[...], start_ts, end_ts, cuts:[{card, from_ts, series:[...] or null, why}],
       market_cols:[...], candle_cols:[...]}
Rows are dropped by close_ts of the market (candles follow their market). A cut log counts markets dropped per cut (a market in several cuts is counted under the first)."""
import sys, os, json, sqlite3, hashlib, collections

def main(a):
    spec = json.load(open(a[0])); arch, out = a[1], a[2]
    os.makedirs(out, exist_ok=True)
    name = spec["card"]; dst = os.path.join(out, name + "_extract.sqlite")
    if os.path.exists(dst): os.remove(dst)
    o = sqlite3.connect(dst)
    mc, cc = spec["market_cols"], spec["candle_cols"]
    o.execute("create table market(%s)" % ",".join(mc + ["src"]))
    o.execute("create table candle(ticker,%s)" % ",".join(cc))
    seen = set(); dropped = []; log = collections.OrderedDict(); counts = collections.Counter(); total = collections.Counter()
    for src in spec["sources"]:
        c = sqlite3.connect("file:%s?mode=ro" % os.path.join(arch, src + ".sqlite"), uri=True)
        q = ",".join(mc)
        for series in spec["series"]:
            for row in c.execute("select %s from market where series=? order by close_ts" % q, (series,)):
                r = dict(zip(mc, row)); t = r["ticker"]; ct = r["close_ts"]
                if t in seen: counts["dup_later_source"] += 1; continue
                seen.add(t); total[(src, series)] += 1
                if ct < spec["start_ts"]: counts["before_start"] += 1; continue
                if ct >= spec["end_ts"]: counts["own_heldout_or_after_end"] += 1; continue
                cut = next((k for k in spec["cuts"] if ct >= k["from_ts"] and (not k.get("series") or series in k["series"])), None)
                if cut:
                    counts["cut:" + cut["card"]] += 1; dropped.append([t, ct, cut["card"]]); continue
                o.execute("insert into market values(%s)" % ",".join("?" * (len(mc) + 1)), list(row) + [src])
                for cr in c.execute("select ticker,%s from candle where ticker=?" % ",".join(cc), (t,)):
                    o.execute("insert into candle values(%s)" % ",".join("?" * (len(cc) + 1)), cr)
                counts["kept"] += 1
    o.commit(); o.execute("vacuum"); o.close()
    sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()
    lo, hi = sqlite3.connect(dst).execute("select min(close_ts),max(close_ts) from market").fetchone()
    L = {"card": name, "spec": spec, "dropped_or_kept": dict(counts), "kept_close_range": [lo, hi], "extract_sha256": sha}
    if spec.get("log_dropped"): L["dropped_by_cut"] = dropped
    json.dump(L, open(os.path.join(out, name + "_cutlog.json"), "w"), indent=1)
    print(name, dict(counts), "range", lo, hi, "sha256", sha)

if __name__ == "__main__": main(sys.argv[1:])

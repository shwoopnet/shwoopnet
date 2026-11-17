"""MECH1 generator for the Bitcoin perp candles (Desk A, Nov 17, 2026), built to MECH1_SCREEN_SPEC_NOV17.md 12.17. Reads ONLY pages 1 to 108 (2026-06-03 to 2026-09-18, SEARCH and VALIDATE) of the History Miner's pull PERPBTC1M; pages 109 to 163 (HELD-OUT) are never opened. Reuses the generator's rules (mech1_generate.build) unchanged.
  python3 -I mech1_generate_btc.py <run folder holding manifest.json and NNNN.json.gz> <out.jsonl>
REFUSES unless the allow file (HELDOUT_PULL_RUNS.md above this folder) carries a line with the mark, "mech1_generate_btc.py", this file's sha256 and the sha256 of manifest.json; each page is checked against its manifest rows[k].sha256 BEFORE it is parsed."""
import sys, os, gzip, json, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mech1_generate as G
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md"); ALLOW_MARK = "readable ONLY by Desk A's MECH1 generator"
WIN = {"search_from": "2026-06-03", "search_to": "2026-07-26", "validate_from": "2026-07-27", "validate_to": "2026-09-18", "half1_to": "2026-07-26", "half2_from": "2026-07-27"}
FAMILIES = {"crypto_perp": ["KXBTCPERP"]}
LAST_PAGE = 108
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def refuse_unless_allowed(manifest_path):
    me = sha(os.path.abspath(__file__)); ms = sha(manifest_path)
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow file cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "mech1_generate_btc.py" in line and me in line and ms in line: return ms
    raise SystemExit("REFUSED: no allow line names mech1_generate_btc.py sha256 %s and the manifest sha256 %s" % (me, ms))
def num(x):
    try: return float(x) if x not in ("", None) else None
    except (TypeError, ValueError): return None
def load(base):
    man = json.load(open(os.path.join(base, "manifest.json"))); rows = {r["index"]: r for r in man["rows"]}; out = {"KXBTCPERP": {}}; first = {}
    if rows[LAST_PAGE + 1]["params"]["start_ts"] < rows[LAST_PAGE]["params"]["end_ts"]: G.LOG["page_109_starts_before_page_108_ends"] += 1          # the manifest carries each page's ts range
    for k in range(1, LAST_PAGE + 1):
        r = rows[k]
        if r.get("status") != 200 or r.get("truncated"): G.LOG["page_not_complete"] += 1; continue
        p = os.path.join(base, r["file"])
        if sha(p) != r["sha256"]: raise SystemExit("REFUSED: page %s does not match its manifest sha256" % r["file"])
        for c in json.load(gzip.open(p, "rt"))["candlesticks"]:
            t = int(c["end_period_ts"])
            if G.day_of(t) > WIN["validate_to"]: G.LOG["candle_after_validate_to_dropped"] += 1; continue          # a page is a count of rows, not a date (Auditor B)
            if G.held("KXBTCPERP", t): G.LOG["holds_excluded"] += 1; continue
            if t in out["KXBTCPERP"]: G.LOG["candle_duplicate_first_kept"] += 1; continue
            out["KXBTCPERP"][t] = (num(c["bid"]["open"]), num(c["ask"]["open"]), num(c["bid"]["close"]), num(c["ask"]["close"]), num(c.get("open_interest")), num(c.get("volume")))
            first.setdefault("KXBTCPERP", G.day_of(t))
    return out, first
def main(base, out_path):
    ms = refuse_unless_allowed(os.path.join(base, "manifest.json")); G.load_holds()
    data, first = load(base)
    lines = G.build(data, first, FAMILIES, WIN, "PERPBTC1M (funding not booked)")
    with open(out_path, "w") as fo:
        for L in lines: fo.write(json.dumps(L, sort_keys=True, separators=(",", ":")) + "\n")
    json.dump({"manifest_sha256": ms, "counts": dict(G.LOG), "generator_sha256": sha(os.path.abspath(__file__)), "pages_read": LAST_PAGE, "funding": "not booked", "holds_file_sha256": G.HOLDS["sha256"], "holds_version": G.HOLDS_PINNED_VERSION, "holds_excluded": G.LOG.get("holds_excluded", 0)}, open(out_path + ".log.json", "w"), sort_keys=True, indent=1)
    print("wrote", out_path, len(lines), "lines;", dict(G.LOG))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])

"""perps_crypto_run_f.py: FORWARD copy of perps_crypto_run.py 1c060648 (FUNDX2-F), importing perps_crypto_load_f; only the loader import and the file names differ. Original: the FILE-LEVEL reader of PERPCRYPTO1 (History Miner, Nov 16, 2026; Auditor B condition 1, 20:56Z). Card PERPCRYPTO1_CARD_NOV16.md.
It opens files only through the walls of perps_crypto_load.py. It calls refuse_unless_allowed() FIRST: one line of HELDOUT_PULL_RUNS.md must carry the mark, this file's sha256, perps_crypto_load.py's sha256 and the sha256 of EVERY source named below
(a csv.gz file: its own bytes; a kalshi-pull run folder: its manifest.json bytes). A source whose sha256 is not on that line is never opened. A run folder is accepted only if STATUS is complete, its files equal the manifest rows plus STATUS and manifest.json, and every body's sha256 and byte count equal its manifest row (status 200, not truncated).
  python3 -I perps_crypto_run.py --snap F.csv.gz ... --btc RUNFOLDER --spot RUNFOLDER ... --funding F.csv.gz   prints COUNTS ONLY (no price, no rate, no outcome); load_all() returns the structures for the scorer, which is a separate step."""
import collections, csv, gzip, hashlib, io, json, os, sys
import perps_crypto_load_f as L
HERE = os.path.dirname(os.path.abspath(__file__))
ALLOW_MARK = L.ALLOW_MARK


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def self_sha():
    return sha(os.path.abspath(__file__))


def refuse_unless_allowed(sources):
    """sources: list of (kind, path). Refuses unless one line names this file, perps_crypto_load.py and every source hash."""
    try:
        text = open(L.ALLOW_FILE, encoding="utf-8").read()
    except OSError:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    need = [self_sha(), L.self_sha()] + [sha(os.path.join(p, "manifest.json")) if k != "csv" else sha(p) for k, p in sources]
    for line in text.splitlines():
        if ALLOW_MARK in line and "perps_crypto_run_f.py" in line and all(h in line for h in need):
            return
    raise SystemExit("REFUSED: no allow line names perps_crypto_run_f.py (%s), perps_crypto_load_f.py (%s) and every source sha256: %s" % (self_sha(), L.self_sha(), need[2:]))


def check_run(run):
    """-> [(manifest row, parsed body)] for a pull run folder, or SystemExit."""
    if open(os.path.join(run, "STATUS"), encoding="utf-8").read().strip() != "complete":
        raise SystemExit("REFUSED: %s STATUS is not complete" % run)
    man = json.load(open(os.path.join(run, "manifest.json"), encoding="utf-8"))
    if sorted(os.listdir(run)) != sorted([r["file"] for r in man["rows"]] + ["STATUS", "manifest.json"]):
        raise SystemExit("REFUSED: %s files differ from the manifest" % run)
    out = []
    for r in man["rows"]:
        body = gzip.decompress(open(os.path.join(run, r["file"]), "rb").read())
        if r["status"] != 200 or r["truncated"] or hashlib.sha256(body).hexdigest() != r["sha256"] or len(body) != r["bytes"]:
            raise SystemExit("REFUSED: %s row %s fails the manifest check" % (run, r["file"]))
        out.append((r, json.loads(body)))
    return out


def csv_rows(path):
    """A .csv.gz (gzip magic) or a plain .csv (the perp-data perps/ day files are plain)."""
    raw = open(path, "rb").read()
    return csv.DictReader(io.StringIO((gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw).decode("utf-8")))


def load_all(snap=(), btc=None, spot=(), funding=None, cnt=None):
    """funding: one file path or a LIST of per-date files (merged, a repeated print kept once)."""
    cnt = cnt if cnt is not None else collections.Counter()
    fl = [funding] if isinstance(funding, str) else list(funding or [])
    srcs = [("csv", p) for p in snap] + ([("run", btc)] if btc else []) + [("run", p) for p in spot] + [("csv", p) for p in fl]
    refuse_unless_allowed(srcs)
    out = {"snapshots": collections.defaultdict(list), "btc": [], "spot": {}, "funding": {}}
    for p in snap:
        for tk, v in L.snapshot_rows(csv_rows(p), cnt).items():
            out["snapshots"][tk] += v
    out["snapshots"] = {k: sorted(v) for k, v in out["snapshots"].items()}
    if btc:
        cs = []
        for r, d in check_run(btc):
            cs += d.get("candlesticks", []) if isinstance(d, dict) else []
        out["btc"] = L.btc_candle_rows(cs, cnt)
    for run in spot:
        for r, d in check_run(run):
            product = r["path"].split("/")[2] if r["path"].count("/") >= 3 else ""
            out["spot"].setdefault(product, {}).update(L.spot_rows(d if isinstance(d, list) else [], product, cnt))
    merged = collections.defaultdict(set)
    for p in fl:
        for tk, v in L.funding_rows(csv_rows(p), cnt).items():
            merged[tk] |= set(v)
    out["funding"] = {tk: sorted(v) for tk, v in merged.items()}
    return out, cnt


def main(argv):
    a = collections.defaultdict(list); k = None
    for x in argv:
        if x.startswith("--"): k = x[2:]
        else: a[k].append(x)
    out, cnt = load_all(a["snap"], (a["btc"] or [None])[0], a["spot"], (a["funding"] or [None])[0])
    print(json.dumps({"snapshot rows by ticker": {k: len(v) for k, v in out["snapshots"].items()}, "btc rows": len(out["btc"]),
                      "spot candles by product": {k: len(v) for k, v in out["spot"].items()}, "funding prints by ticker": {k: len(v) for k, v in out["funding"].items()}, "counts": dict(cnt)}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1:])

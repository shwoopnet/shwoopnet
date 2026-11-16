"""fundx2_thresholds.py: the FUNDX2 thresholds step (History Miner, Nov 16, 2026). Card FUNDX2_CARD_NOV16.md. Funding only: it loads the labelled funding file behind the allow line, computes the cut points
and the extreme counts, writes FUNDX2_THRESHOLDS.json and STOPS BEFORE ANY PRICE (it opens no snapshot, no BTC candle run and no spot file).
funding_rate values are used ONLY inside fundx2_events.cut_points and fundx2_events.extreme_counts; the output holds thresholds (the cut points) and counts, no per-print rate, time or mark price.
  python3 -I fundx2_thresholds.py <funding by-ticker.csv.gz> <output FUNDX2_THRESHOLDS.json>   prints one line: the output file's sha256."""
import collections, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import perps_crypto_load as L
import perps_crypto_run as R
import fundx2_events as F
ALLOW_MARK = L.ALLOW_MARK
NAMES = ("KXBTCPERP", "KXETHPERP", "KXSOLPERP", "KXXRPPERP", "KXDOGEPERP", "KXHYPEPERP")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def refuse_unless_allowed(funding_path):
    """One allow line must carry the mark, this file's sha256, perps_crypto_run.py's, perps_crypto_load.py's, fundx2_events.py's and the funding file's sha256 (R.load_all then checks its own line again)."""
    need = [sha(os.path.abspath(__file__)), R.self_sha(), L.self_sha(), sha(os.path.join(HERE, "fundx2_events.py")), sha(funding_path)]
    try:
        text = open(L.ALLOW_FILE, encoding="utf-8").read()
    except OSError:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "fundx2_thresholds.py" in line and all(h in line for h in need):
            return need
    raise SystemExit("REFUSED: no allow line names fundx2_thresholds.py with the sha256 set %s" % need)


def build(funding_path):
    need = refuse_unless_allowed(funding_path)
    out, cnt = R.load_all(funding=funding_path)                       # funding only: no snapshot, no candle run, no spot
    prints = {tk: out["funding"].get(tk, []) for tk in NAMES}
    counts = F.extreme_counts(prints)
    doc = {"id": "FUNDX2", "ticker_set": list(NAMES), "cut_rule": "nearest rank on SEARCH prints only: lower = s[ceil(qn)-1], upper = s[n-ceil(qn)]; at least %d prints" % F.MIN_PRINTS,
           "search": [F.SEARCH_START, F.SEARCH_END], "validate": [F.SEARCH_END, F.VALIDATE_END],
           "hashes": {"fundx2_thresholds.py": need[0], "perps_crypto_run.py": need[1], "perps_crypto_load.py": need[2], "fundx2_events.py": need[3], "funding_file": need[4]},
           "load_counts": dict(cnt), "cuts": {}}
    for tk in NAMES:
        doc["cuts"][tk] = {}
        for q in F.QS:
            cp = F.cut_points(prints[tk], q); c = counts[tk][q]
            doc["cuts"]["%s" % tk]["%g" % (q * 100)] = {"lower": cp[0] if cp else None, "upper": cp[1] if cp else None, "search_n": c["search_prints"], "has_threshold": c["has_threshold"],
                                                         "validate_prints": c["validate_prints"], "search_extremes": c["search_extremes"], "validate_extremes": c["validate_extremes"]}
    return doc


def main(funding_path, out_path):
    doc = build(funding_path)
    open(out_path, "w", encoding="utf-8").write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return sha(out_path)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: fundx2_thresholds.py <funding csv.gz> <output json>")
    print(main(sys.argv[1], sys.argv[2]))

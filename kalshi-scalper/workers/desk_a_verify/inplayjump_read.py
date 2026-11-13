"""INPLAYJUMP family read script (Desk A, Nov 13 2026; the Head's order: each file read within minutes of landing). One DEVELOPMENT read of one family on the audited engine.
  python3 -I inplayjump_read.py <FAMILY> <INPLAYJUMP_SERIES.json> <lists run folder> <candle run folders, comma separated> <scorekit dir> <out dir>
FAMILY: ESOCCER | TABLE_TENNIS | EBASKETBALL | ITF_TENNIS | CHALLENGER_TENNIS.
Prints, in the registered order: engine and series hashes, the start check, the COST LINE first (median one-way entry cost over every qualifying decision with a two-sided entry minute; a family above the 4c kill is CLOSED on cost and NO result is read), then the count against its minimum (300 development bets), then (only if both pass) the rule lines and the label. Everything printed is marked 'PROVISIONAL, ONE BUILD' until the Testing Desk's second build prints the same lines on the same landed file (the Head's rule).
Checks before it runs: the engine file's sha256 must start c39b1e9b (Auditor B CLEAN, 674097cc) and the series file's 34f70868; a HELDOUT_ path is refused by the engine; the out dir gets a marker per family, and a family whose marker exists is refused (a family is read once; a marker is written BEFORE the read). It reads results only for matches with a bet (the engine's own rule)."""
import sys, os, hashlib, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
FAM = {"ESOCCER", "TABLE_TENNIS", "EBASKETBALL", "ITF_TENNIS", "CHALLENGER_TENNIS"}
def main(family, series, lists, candles, scorekit_dir, outdir):
    assert family in FAM, "family must be one of %s" % sorted(FAM)
    eh = hashlib.sha256(open(os.path.join(HERE, "inplayjump.py"), "rb").read()).hexdigest(); sh = hashlib.sha256(open(series, "rb").read()).hexdigest()
    if not (eh.startswith("c39b1e9b") or eh.startswith("870a453e") or eh.startswith("6e356373")): sys.exit("REFUSED: engine hash %s is not an audited one (c39b1e9b, or 870a453e with the placebo tie rule)" % eh[:16])
    if not sh.startswith("34f70868"): sys.exit("REFUSED: series file hash %s is not 34f70868" % sh[:16])
    os.makedirs(outdir, exist_ok=True); marker = os.path.join(outdir, "READ_" + family)
    if os.path.exists(marker) and "--test" not in sys.argv: sys.exit("REFUSED: %s was already read (marker %s); a family is read once" % (family, marker))
    if "--test" not in sys.argv: open(marker, "w").write("started\n")
    import inplayjump as J
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): J.dev(series, family, [lists], candles.split(","), scorekit_dir)
    out = ["PROVISIONAL, ONE BUILD (engine %s, series file %s, candle folders %s)" % (eh[:8], sh[:8], candles)] + buf.getvalue().splitlines()
    text = "\n".join(out); print(text); open(os.path.join(outdir, "READ_%s.txt" % family), "w").write(text + "\n")
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--test"]
    main(*a) if len(a) == 6 else sys.exit(__doc__)

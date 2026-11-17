"""Runner for OICORE's rule on every market of the ENGINE1 archive (Desk A, Nov 17 2026), to OICORE_XMARKET_REGISTRATION_NOV17.md and amendment 1.
  python3 -I oicore_xmarket_run.py <dir holding ENGINE1_archive_extract.sqlite.xz> <out.txt>
Opens the archive ONLY through engine1_extract_load (its allow line and the extract's sha256); prints n, wins, PF, cents a contract per series and phase, signals a day, and the day correlation with BTC (VALIDATE and SEARCH). Held-out is a separate read."""
import sys, os, hashlib
import engine1_extract_load as L, engine1_split as S, oicore_xmarket as X
def phase_of(key, ts):
    return S.phase(key, ts) if key in S.LAST_SEARCH else "unknown"
def fmt(x): return "na" if x is None else ("inf" if x == float("inf") else "%.4f" % x)
def main(base, out, check_allow=True):
    if check_allow: L.refuse_unless_allowed()
    markets, counts = L.load_archive(base)
    res = X.run(markets, phase_of)
    btc = res.get("KXBTC15M", {}).get("phases", {})
    lines = ["OICORE x-market, archive (history, closes before 2026-10-03T16:00Z), loader counts " + str(counts), "label: upper bound (candle quotes), SEARCH and VALIDATE are history, not forward"]
    for s in sorted(res):
        r = res[s]
        if "note" in r: lines.append("%s: %s (SEARCH rises under 20 or cut not above 0; cut %s)" % (s, r["note"], r["cut"])); continue
        lines.append("%s: cut %s skipped %s" % (s, r["cut"], r.get("skipped")))
        for ph in ("search", "validate"):
            p = r["phases"].get(ph)
            if not p: lines.append("  %s: n 0" % ph); continue
            b = btc.get(ph, {}).get("day_net_1c") if s != "KXBTC15M" else None
            c = X.corr(p["day_net_1c"], b) if b else None
            lines.append("  %s: n %d wins %d | 1c PF %s cents/contract %s | 2c PF %s cents/contract %s | signals/day %.3f | day corr with BTC %s" % (ph, p["1c"]["n"], p["1c"]["wins"], fmt(p["1c"]["pf"]), fmt(p["1c"]["cents_per_contract"]), fmt(p["2c"]["pf"]), fmt(p["2c"]["cents_per_contract"]), p["signals_per_day"], fmt(c)))
    open(out, "w").write("\n".join(lines) + "\n"); print("output sha256", hashlib.sha256(open(out, "rb").read()).hexdigest())
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--no-allow"]
    if len(a) != 2: sys.exit(__doc__)
    main(a[0], a[1], check_allow="--no-allow" not in sys.argv)

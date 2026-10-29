"""BTCAVG scorer (workers/BTCAVG_REGISTRATION.md, pushed as 9c3badc before this file existed). Research only.
Usage (from the repo root): python3 -I kalshi-scalper/workers/BTCAVG_score.py w12   # windows W1 and W2 only
                            python3 -I kalshi-scalper/workers/BTCAVG_score.py w3    # the holdout, read once after W1/W2 are written
"""
import csv, gzip, io, math, statistics as st, subprocess, sys
from collections import defaultdict
from datetime import datetime, timezone

COMMIT = "b7dc9cbe823b2b9f734dc085ea03452a1aec3c1b"
MARGIN, STALE_S, SIG_S, MIN_CH = 0.05, 5, 300, 100
WIN = {"W1": ("2026-10-22", "2026-10-24"), "W2": ("2026-10-25", "2026-10-26"), "W3": ("2026-10-27", "2026-10-29")}
VARIANTS = {"D30": 30, "D15": 15, "D45": 45, "D30L": 30}


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, check=True).stdout


def rows(f, nm):
    return list(csv.DictReader(io.StringIO(gzip.decompress(git("show", f"{COMMIT}:{f}/{nm}.csv.gz")).decode())))


def fee(p, n, mult=1.0):
    return math.ceil(round(100 * 0.07 * n * p * (1 - p) * mult, 9)) / 100 if n > 0 else 0.0


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def proxy(spot):
    ticks = sorted((int(r["t_recv_ms"]), r["exchange"], float(r["price"])) for r in spot if r["asset"] == "BTC" and r["price"])
    if not ticks:
        return {}
    last, out, i = {}, {}, 0
    for sec in range(ticks[0][0] // 1000, ticks[-1][0] // 1000 + 1):
        while i < len(ticks) and ticks[i][0] < (sec + 1) * 1000:
            last[ticks[i][1]] = (ticks[i][0], ticks[i][2]); i += 1
        live = [p for t, p in last.values() if (sec + 1) * 1000 - t <= STALE_S * 1000]
        if len(live) >= 2:
            out[sec] = st.median(live)
    return out


def p_yes(X, C, T, K):
    last = T // 1000 - 1                      # last complete second
    fm = range(C - 60, C)
    done = [t for t in fm if (t + 1) * 1000 <= T]
    k, m = len(done), 60 - len(done)
    if last not in X:
        return None, "no_S"
    obs = [X[t] for t in done if t in X]
    if k and len(obs) < 0.8 * k:
        return None, "thin_obs"
    ch = [X[t + 1] - X[t] for t in range(T // 1000 - SIG_S - 1, T // 1000 - 1) if t in X and t + 1 in X]
    if len(ch) < MIN_CH:
        return None, "thin_sigma"
    sig, S = st.pstdev(ch), X[last]
    mean = ((sum(obs) / len(obs)) * k if k else 0.0) / 60 + m * S / 60
    sd = sig * math.sqrt(m * (m + 1) * (2 * m + 1) / 6) / 60
    if sd <= 0:
        return (1.0 if mean >= K else 0.0), "ok"
    return 1 - phi((K - mean) / sd), "ok"


def pnl(side, price, size, result, n, mult=1.0):
    c = min(n, math.floor(size + 1e-9))
    if c <= 0:
        return None
    f = fee(price, c, mult)
    return (c * (1 - price) - f) if side == result else (-c * price - f)


def main(phase):
    names = git("ls-tree", "-r", "--name-only", COMMIT, "quotes/").decode().split()
    folders = sorted({"/".join(n.split("/")[:3]) for n in names if n.count("/") == 3})
    allowed = ["W1", "W2"] if phase == "w12" else ["W3"]
    trades = defaultdict(list)
    skips = defaultdict(lambda: defaultdict(int))
    agree = []
    cal = []
    offsets = []
    seen = set()
    for f in folders:
        try:
            q, sp, res, clk = rows(f, "quotes"), rows(f, "spot"), rows(f, "results"), rows(f, "clock")
        except subprocess.CalledProcessError:
            continue
        resd = {r["ticker"]: r for r in res if r["ticker"].startswith("KXBTC15M") and r["result"] in ("yes", "no")}
        if not resd:
            continue
        X = proxy(sp)
        offs = [abs(float(c["offset_ms"])) for c in clk if c["offset_ms"] not in ("", None)]
        polls = defaultdict(list)
        for r in q:
            if r["ticker"] in resd:
                polls[r["ticker"]].append(r)
        for tk, rr in resd.items():
            C = int(datetime.strptime(rr["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
            d = rr["close_time"][:10]
            w = next((k for k, (a, b) in WIN.items() if a <= d <= b), None)
            if w not in allowed or tk in seen:
                continue
            seen.add(tk)
            if offs:
                offsets.append(max(offs))
            ps = sorted((p for p in polls[tk]), key=lambda p: int(p["t_recv_ms"]))
            good = [p for p in ps if p["status"] == "active" and p["yes_bid"] and p["yes_ask"] and 0 < float(p["yes_bid"]) <= float(p["yes_ask"]) < 1]
            if not ps:
                for v in VARIANTS: skips[v]["no_polls"] += 1
                continue
            K = float(ps[0]["strike"])
            result = rr["result"]
            fmv = [X[t] for t in range(C - 60, C) if t in X]
            if len(fmv) >= 48:
                a = sum(fmv) / len(fmv)
                agree.append((w, abs(a - K), (a >= K) == (result == "yes")))
            for v, D in VARIANTS.items():
                poll = next((p for p in good if int(p["t_recv_ms"]) >= (C - D) * 1000), None)
                if poll is None or int(poll["t_recv_ms"]) > (C - D + 5) * 1000:
                    skips[v]["no_poll_in_5s"] += 1; continue
                T = int(poll["t_recv_ms"])
                P, why = p_yes(X, C, T, K)
                if P is None:
                    skips[v][why] += 1; continue
                if v == "D30":
                    cal.append((P, result == "yes"))
                bid, ask = float(poll["yes_bid"]), float(poll["yes_ask"])
                if P - ask - fee(ask, 1) >= MARGIN and float(poll["ask_size"] or 0) >= 1:
                    side, price, size = "yes", ask, float(poll["ask_size"])
                elif (1 - P) - (1 - bid) - fee(1 - bid, 1) >= MARGIN and float(poll["bid_size"] or 0) >= 1:
                    side, price, size = "no", round(1 - bid, 4), float(poll["bid_size"])
                else:
                    skips[v]["no_signal"] += 1; continue
                if v == "D30L":
                    nxt = next((p for p in good if int(p["t_recv_ms"]) > T and int(p["t_recv_ms"]) < C * 1000), None)
                    if nxt is None:
                        skips[v]["no_next_poll"] += 1; continue
                    if side == "yes":
                        price, size = max(price, float(nxt["yes_ask"])), float(nxt["ask_size"] or 0)
                    else:
                        price, size = max(price, round(1 - float(nxt["yes_bid"]), 4)), float(nxt["bid_size"] or 0)
                    if size < 1:
                        skips[v]["next_no_size"] += 1; continue
                trades[v].append({"w": w, "date": d, "side": side, "price": price, "P": P, "n1": pnl(side, price, size, result, 1),
                                  "n10": pnl(side, price, size, result, 10), "s1": pnl(side, price, size, result, 1, 1.2),
                                  "s10": pnl(side, price, size, result, 10, 1.2), "c10": min(10, math.floor(size + 1e-9))})
    out = [f"BTCAVG phase {phase}, data {COMMIT[:9]}, windows scored {len(seen)}"]
    for v in VARIANTS:
        out.append(f"\n{v}: skips {dict(skips[v])}")
        for w in allowed + ["POOLED"]:
            tt = [t for t in trades[v] if w == "POOLED" or t["w"] == w]
            if not tt:
                out.append(f"  {w}: n 0"); continue
            def pf(key):
                g = sum(t[key] for t in tt if t[key] > 0); l = -sum(t[key] for t in tt if t[key] < 0)
                return (g / l) if l > 0 else float("inf")
            n1 = [t["n1"] for t in tt]
            m = st.mean(n1); sd = st.stdev(n1) if len(n1) > 1 else 0
            z = m / (sd / math.sqrt(len(n1))) if sd > 0 else float("nan")
            byd = defaultdict(float)
            for t in tt: byd[t["date"]] += t["n1"]
            dv = list(byd.values()); zd = st.mean(dv) / (st.stdev(dv) / math.sqrt(len(dv))) if len(dv) > 1 and st.stdev(dv) > 0 else float("nan")
            wins = sum(1 for t in tt if t["n1"] > 0)
            out.append(f"  {w}: n {len(tt)} (wins {wins}, yes {sum(t['side']=='yes' for t in tt)}), mean price {st.mean(t['price'] for t in tt):.3f}, "
                       f"PF1 {pf('n1'):.2f} PF10 {pf('n10'):.2f}, mean1 {100*m:+.2f}c z {z:.2f} (date z {zd:.2f}, {len(dv)} dates), "
                       f"net1 ${sum(n1):+.2f} net10 ${sum(t['n10'] for t in tt):+.2f} (mean fill {st.mean(t['c10'] for t in tt):.1f} of 10), "
                       f"x1.2: net1 ${sum(t['s1'] for t in tt):+.2f} net10 ${sum(t['s10'] for t in tt):+.2f}, mean model edge {100*st.mean((t['P'] if t['side']=='yes' else 1-t['P'])-t['price'] for t in tt):+.1f}c")
    out.append("\nProxy-outcome agreement (sign(A_proxy - strike) vs result, windows with >= 48 of 60 final seconds):")
    for lo, hi, lab in ((0, 5, "<$5"), (5, 20, "$5-20"), (20, 50, "$20-50"), (50, 1e9, ">$50"), (0, 1e9, "all")):
        a = [g for _, dist, g in agree if lo <= dist < hi]
        if a:
            out.append(f"  {lab}: {sum(a)}/{len(a)} = {100*sum(a)/len(a):.1f}%")
    out.append("D30 model calibration (P bin: n, mean P, YES rate):")
    for lo in (0, 0.2, 0.4, 0.6, 0.8):
        c = [(p, y) for p, y in cal if lo <= p < lo + 0.2 or (lo == 0.8 and p == 1.0)]
        if c:
            out.append(f"  {lo:.1f}-{lo+0.2:.1f}: n {len(c)}, P {st.mean(p for p, _ in c):.3f}, yes {st.mean(y for _, y in c):.3f}")
    if offsets:
        out.append(f"Clock: windows with an offset {len(offsets)}, max |offset| {max(offsets):.0f} ms, share over 100 ms {100*sum(o>100 for o in offsets)/len(offsets):.0f}%")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "w12")

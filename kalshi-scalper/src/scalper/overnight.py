"""The overnight run on older data (protocol fixed in the README before the older history was downloaded or looked at).

Windows by date. W0 = markets older than the first search's data (split in two thirds: W0s searches, W0h is locked). W1 and W2 are the
two halves of the first search's data (W1 was its search window, W2 its holdout). W3 = anything newer, for survivors only.

Stage A: do the first search's saved winners generalize?  Stage B: a new search on W0s, beside a fair-market control.
A saved rule is a SURVIVOR only if, on every window it was not selected on, its mean net is positive with at least 50 entries, and the pooled
day clustered z is at least 2.5. The same test runs on the control's saved rules, so the false survivor rate is measured.

Nothing here can produce a verdict that means "trade". Usage: python -m scalper.overnight
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from .calibration import cluster_mean_z
from . import search as S

ORIG_START = 1788619500      # the first close in the data the first search used (2026-09-05 14:45 UTC)
ORIG_END = 1791212400        # the last close it used (2026-10-05 15:00 UTC)
MIN_WINDOW_N = 50
POOLED_Z = 2.5
OUT = Path(__file__).resolve().parents[2] / "search2"


def split_thirds(ms: list[dict]) -> tuple[list[dict], list[dict]]:
    """First two thirds of the DAYS search, the last third is locked."""
    days = sorted({m["day"] for m in ms})
    cut = set(days[: round(len(days) * 2 / 3)])
    return [m for m in ms if m["day"] in cut], [m for m in ms if m["day"] not in cut]


def windows(ms: list[dict]) -> dict[str, list[dict]]:
    old = [m for m in ms if m["close"] < ORIG_START]
    orig = [m for m in ms if ORIG_START <= m["close"] <= ORIG_END]
    new = [m for m in ms if m["close"] > ORIG_END]
    w0s, w0h = split_thirds(old)
    w1, w2 = S.split_days(orig)
    return {"W0s": w0s, "W0h": w0h, "W1": w1, "W2": w2, "W3": new}


def observations(markets: list[dict], rule: dict) -> list[tuple[str, float]]:
    return [o for o in (S.observe(m, rule) for m in markets) if o is not None]


def passes(ns: list[int], means: list[float], pooled_z: float) -> bool:
    """THE criteria, one definition used by the real test and by the null: every window has at least MIN_WINDOW_N entries and a positive mean,
    and the pooled day clustered z is at least POOLED_Z."""
    return all(n >= MIN_WINDOW_N and m > 0 for n, m in zip(ns, means)) and pooled_z >= POOLED_Z


def survivor(rule: dict, wins: list[list[dict]]) -> dict:
    """The fixed test. wins: the windows the rule was NOT selected on."""
    per, pooled = [], []
    for w in wins:
        obs = observations(w, rule)
        n = len(obs)
        per.append({"n": n, "mean": sum(x for _, x in obs) / n if n else 0.0})
        pooled += obs
    _, _, z = cluster_mean_z(pooled)
    ok = all(p["n"] >= MIN_WINDOW_N and p["mean"] > 0 for p in per)
    return {"survivor": passes([p["n"] for p in per], [p["mean"] for p in per], z), "per_window": per, "pooled_n": len(pooled), "pooled_z": z, "all_positive": ok}


def saved_rules(directory: Path) -> list[dict]:
    seen, out = set(), []
    for f in sorted(directory.glob("cycle*_top25.json")) + sorted(directory.glob("holdout_final25.json")):
        for r in json.loads(f.read_text()):
            spec = r.get("spec")
            if not spec:
                continue
            rule = S.normalize({**spec, "filters": [tuple(x) for x in spec["filters"]]})
            k = S.key(rule)
            if k not in seen:
                seen.add(k)
                out.append(rule)
    return out


def fair_windows(w: dict[str, list[dict]], seed: int) -> dict[str, list[dict]]:
    return {k: S.fair_market(v, seed + i) for i, (k, v) in enumerate(sorted(w.items()))}


def run(ms: list[dict], seed: int = 11, cycles: int = 2, first_dir: Path | None = None) -> dict:
    w = windows(ms)
    first_dir = first_dir or (Path(__file__).resolve().parents[2] / "search")
    # Stage A: the first search's winners, scored on the older data they never saw.
    old = saved_rules(first_dir)
    a_hits = []
    for r in old:
        res = survivor(r, [w["W0s"], w["W0h"], w["W2"]])
        a_hits.append({"rule": r, **res})
    # Stage B: a new search on W0s, and the same loop on a fair market.
    real = S.run_search(w["W0s"], seed, cycles)
    fair_w = fair_windows(w, seed + 100)
    null = S.run_search(fair_w["W0s"], seed, cycles)
    def judge(found, wins):
        saved, seen = [], set()
        for rd in found["rounds"]:
            for r in rd["top"]:
                if r["key"] not in seen:
                    seen.add(r["key"])
                    saved.append(r)
        return [{**r, **survivor(r["rule"], [wins["W0h"], wins["W1"], wins["W2"]])} for r in saved], saved
    b_hits, b_saved = judge(real, w)
    n_hits, n_saved = judge(null, fair_w)
    return {"windows": {k: len(v) for k, v in w.items()}, "stageA": a_hits, "stageB": b_hits, "control": n_hits,
            "evaluated_B": real["evaluated"], "evaluated_control": null["evaluated"], "w": w, "real": real, "null": null}


def entries_of(markets: list[dict], rule: dict) -> list[tuple]:
    """(day, cost, side_mid) per entry: what a rule pays (ask plus fee) and the fair win probability at its own decision price."""
    out = []
    for m in markets:
        e = S.entry(m, rule)
        if e is not None:
            out.append((e[0], e[2] + S.fee(e[2]), e[3]))
    return out


def fair_null(rules: list[dict], oos: list[list[list[dict]]], reps: int, seed: int = 1) -> dict:
    """THE null for a search. Every rule gets zero edge at its OWN decision price: each entry wins with probability equal to the side's mid, drawn
    independently per rule and per repeat, and pays the ask and the fee. The fixed survivor test (positive in every out of sample window with at
    least 50 entries, pooled day clustered z of at least 2.5) is applied to every rule of every repeat. The result is how often luck alone gives a
    survivor and how large the best pooled z gets across the whole family. Independent draws across rules is the strict direction: correlated rules
    would give fewer effective tries."""
    import random as _r
    rng = _r.Random(seed)
    prepared = [[entries_of(w, rule) for w in wins] for rule, wins in zip(rules, oos)]
    best, surv = [], []
    for _ in range(reps):
        top, n_surv = -9.0, 0
        for ent_w in prepared:
            ns, means, n_all, s_all, days = [], [], 0, 0.0, {}
            for ent in ent_w:
                n, s = len(ent), 0.0
                for d, cost, mid in ent:
                    x = (1.0 if rng.random() < mid else 0.0) - cost
                    s += x
                    cell = days.setdefault(d, [0.0, 0])
                    cell[0] += x
                    cell[1] += 1
                n_all += n
                s_all += s
                ns.append(n)
                means.append(s / n if n else 0.0)
            if n_all < 2:
                continue
            mean = s_all / n_all
            se = math.sqrt(sum((c[0] - c[1] * mean) ** 2 for c in days.values())) / n_all
            z = mean / se if se > 0 else 0.0
            top = max(top, z)
            if passes(ns, means, z):
                n_surv += 1
        best.append(top)
        surv.append(n_surv)
    return {"best": best, "survivors": surv}


def saved_from(found: dict) -> list[dict]:
    seen, out = set(), []
    for rd in found["rounds"]:
        for r in rd["top"]:
            if r["key"] not in seen:
                seen.add(r["key"])
                out.append(r)
    return out


def family(res: dict, w: dict[str, list[dict]]) -> tuple[list[dict], list[list[list[dict]]]]:
    """Every saved rule of both stages with the windows it was NOT selected on."""
    rules, oos = [], []
    for r in res["stageA"]:
        rules.append(r["rule"]); oos.append([w["W0s"], w["W0h"], w["W2"]])
    for r in res["stageB"]:
        rules.append(r["rule"]); oos.append([w["W0h"], w["W1"], w["W2"]])
    return rules, oos


def null_report(reps: int) -> None:
    markets, _ = S.load_markets()
    ms = S.prep(markets)
    res = run(ms)
    w = res["w"]
    rules, oos = family(res, w)
    real_z = [r["pooled_z"] for r in res["stageA"] + res["stageB"]]
    real_surv = sum(1 for r in res["stageA"] + res["stageB"] if r["survivor"])
    nul = fair_null(rules, oos, reps)
    best = sorted(nul["best"])
    print(f"family of {len(rules)} saved rules; real best pooled z {max(real_z):+.2f}, real survivors {real_surv}")
    print(f"fair null over {reps} repeats: best pooled z median {best[len(best) // 2]:+.2f}, 95th {best[int(len(best) * 0.95)]:+.2f}, max {best[-1]:+.2f}")
    print(f"  P(null best z >= real best z) = {sum(1 for b in best if b >= max(real_z)) / reps:.3f}")
    print(f"  P(null survivors >= {real_surv}) = {sum(1 for n in nul['survivors'] if n >= real_surv) / reps:.3f}; mean null survivors {sum(nul['survivors']) / reps:.2f}")


def line(r: dict) -> str:
    per = " / ".join(f"{p['mean'] * 100:+.1f}c (n={p['n']})" for p in r["per_window"])
    return f"{S.describe(r['rule'])}\n      out of sample: {per}; pooled z {r['pooled_z']:+.2f}"


def main() -> None:
    markets, _ = S.load_markets()
    ms = S.prep(markets)
    res = run(ms)
    print("windows (markets):", res["windows"])
    for tag, key_ in (("STAGE A: the first search's saved rules, tested on older data", "stageA"), ("STAGE B: 200+ new rules found on W0s", "stageB"),
                      ("CONTROL: the same loop on a fair market", "control")):
        rows = res[key_]
        surv = [r for r in rows if r["survivor"]]
        pos = [r for r in rows if r["all_positive"]]
        print(f"\n{tag}: {len(rows)} saved rules, {len(pos)} positive in every out of sample window, {len(surv)} survivors")
    OUT.mkdir(exist_ok=True)
    def dump(name, rows):
        (OUT / f"{name}.json").write_text(json.dumps([{"rule": S.describe(r["rule"]), "spec": {**r["rule"], "filters": [list(f) for f in r["rule"]["filters"]]},
            "survivor": r["survivor"], "pooled_z": round(r["pooled_z"], 3), "per_window": [{"n": p["n"], "mean_cents": round(p["mean"] * 100, 3)} for p in r["per_window"]]}
            for r in sorted(rows, key=lambda r: -r["pooled_z"])], indent=1))
    for name, key_ in (("stageA", "stageA"), ("stageB", "stageB"), ("control", "control")):
        dump(name, res[key_])
    print(f"\nrules evaluated in the new search: {res['evaluated_B']} (best of N on noise is expected near z = {math.sqrt(2 * math.log(res['evaluated_B'])):.2f}); control: {res['evaluated_control']}")
    best = sorted(res["stageA"] + res["stageB"], key=lambda r: -r["pooled_z"])[:5]
    print("\nBest five by pooled out of sample z (survivors are marked):")
    for r in best:
        print(("  SURVIVOR " if r["survivor"] else "  not a survivor ") + line(r))
    print("\nVERDICT: this is a search. Survivors earn a forward test only; none means none.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "null":
        null_report(int(sys.argv[2]))
    else:
        main()

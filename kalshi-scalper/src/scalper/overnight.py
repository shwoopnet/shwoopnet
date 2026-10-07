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


def survivor(rule: dict, wins: list[list[dict]]) -> dict:
    """The fixed test. wins: the windows the rule was NOT selected on."""
    per, pooled = [], []
    ok = True
    for w in wins:
        obs = observations(w, rule)
        n = len(obs)
        mean = sum(x for _, x in obs) / n if n else 0.0
        per.append({"n": n, "mean": mean})
        pooled += obs
        if n < MIN_WINDOW_N or mean <= 0:
            ok = False
    _, _, z = cluster_mean_z(pooled)
    return {"survivor": ok and z >= POOLED_Z, "per_window": per, "pooled_n": len(pooled), "pooled_z": z, "all_positive": ok}


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
    main()

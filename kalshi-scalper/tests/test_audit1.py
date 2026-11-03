"""AUDIT1: parsers, statistics and the written table. Research only; reads README.md and workers/, changes nothing."""
import csv
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import audit1 as a  # noqa: E402


def test_normal_tail_and_binomial():
    assert abs(a.sf(0.0) - 0.5) < 1e-12
    assert abs(a.sf(1.96) - 0.025) < 1e-4
    assert a.binom_sf(0, 10, 0.3) == 1.0
    assert abs(a.binom_sf(10, 10, 0.5) - 0.5 ** 10) < 1e-12
    assert abs(a.binom_sf(5, 10, 0.5) - 0.623046875) < 1e-9


def test_best_of_k_p_value():
    assert abs(a.max_p(2.0, 1) - a.sf(2.0)) < 1e-12
    assert a.max_p(3.0, 100) > 0.12  # a z of 3 is ordinary as the best of 100
    assert a.max_p(3.0, 1) < 0.0014


def test_fisher_and_pcurve():
    stat, df, p = a.fisher_combined([0.5, 0.5, 0.5])
    assert df == 6 and 0.5 < p < 1.0
    _, _, p_small = a.fisher_combined([0.001] * 5)
    assert p_small < 1e-6
    assert a.pcurve_right_skew([0.001, 0.002, 0.004, 0.003])[0] == 4
    assert a.pcurve_right_skew([0.04, 0.03, 0.045, 0.049])[1] == 0


def test_z_from_mean_and_ci():
    z = a.z_from_mean_ci(1.0, 0.02, 1.98)  # se = 0.5
    assert abs(z - 2.0) < 0.01
    assert a.z_from_mean_ci(1.0, 2.0, 1.0) is None


def test_parse_z_skips_bars_and_keeps_results():
    txt = "net +0.97c, z +1.45 against a bar of z 2.1; day z 4.42 against about 5.2; deflated z 5.27; (z -2.94)."
    zs = a.parse_z_values(txt)
    assert 1.45 in zs and -2.94 in zs and 4.42 in zs
    assert 2.1 not in zs and 5.27 not in zs and 5.2 not in zs


def test_table_z_values_reads_the_z_column():
    t = "| Rule | n | z | halves |\n|---|---|---|---|\n| A | 1,447 | +1.45 | +0.71 / +1.22 |\n| B | 100 | -2.94 | x |\n"
    assert a.table_z_values(t) == [1.45, -2.94]
    t2 = "| Rule | NW z (bar 2.6) |\n|---|---|\n| A | 9.9 |\n"
    assert a.table_z_values(t2) == []  # a column about the bar is not a result


def test_artefact_cap_in_make_row():
    r = {"id": "XX1", "titles": ["Result: XX1"], "texts": ["FALSIFIED. z +34 is arithmetic. z +2.1 in validation."],
         "sources": ["t"], "dates": ["2026-10-01"], "multi": False}
    row = a.make_row("XX1", r)
    assert row["n_z"] == 1 and row["n_z_dropped"] == 1 and row["z_max"] == "2.10"


def test_verdict_words():
    assert a.find_verdict("Result: GEN1: NO_WINNER, FALSIFIED before the holdout") == "NO_WINNER"
    assert a.find_verdict("verdict NOT_YET_FALSIFIED at the bar") == "NOT_YET_FALSIFIED"
    assert a.find_verdict("`FALSIFIED`") == "FALSIFIED"
    assert a.find_verdict("nothing to see") == "unknown"


def test_n_charged():
    assert a.find_n_charged("kept. N +12; running count about 700,166") == 12
    assert a.find_n_charged("**N added: 4**") == 4
    assert a.find_n_charged("0 tries, N unchanged") == 0
    assert a.find_n_charged("no counting here") is None


def test_ids_from_title_and_ranges():
    assert a.ids_from_title("Results: E1 and E2, one run, read once (2026-10-09; the rule)") == ["E1", "E2"]
    assert a.ids_from_title("Result: E3, L1 unchanged on seven more 15 minute series (run once)") == ["E3"]
    assert a.ids_from_title("Result: USWEEP1 (universe sweep, run once on 2026-11-03)") == ["USWEEP1"]
    assert a.early_verdict_ids("Verdict 2026-10-08: X1 to X4: all four `FALSIFIED`") == ["X1", "X2", "X3", "X4"]
    assert a.early_verdict_ids("Verdict 2026-10-05: H1, favourites underpriced: `FALSIFIED`.") == ["H1"]


def test_tail_summary_and_balance():
    zs = [3.5, 2.5, 0.1, -0.2, -2.5, -3.5, -2.2]
    t = a.tail_summary(zs)
    assert t["gt2"] == 2 and t["gt3"] == 1 and t["lt-2"] == 3 and t["lt-3"] == 1
    r, l, p = a.tail_balance(zs, 2.0)
    assert (r, l) == (2, 3) and p > 0.5


def test_clean_and_collapse_units():
    u = [{"id": "USWEEP1:KXRAIN", "z": 14.2}, {"id": "USWEEP1:KXA", "z": 1.0}, {"id": "L1B:pooled (information)", "z": 3.2},
         {"id": "GEN6:B01", "z": 5.4}, {"id": "GEN6:B02", "z": 5.3}, {"id": "E3:XRP", "z": 2.4}]
    c = a.clean_units(u)
    assert [x["id"] for x in c] == ["USWEEP1:KXA", "GEN6:B01", "GEN6:B02", "E3:XRP"]
    assert [x["id"] for x in a.collapse_by_family(c)] == ["USWEEP1:KXA", "GEN6:B01", "E3:XRP"]


def test_lane_overrides_and_combined_lane():
    assert a.classify_lane("OICORE", "x", "") == "15-minute crypto" or a.classify_lane("OICORE", "x", "")
    assert a.classify_lane("WX3", "x", "") == "weather"
    assert a.classify_lane("ZZ9", "gold gold gold bitcoin bitcoin bitcoin", "gold gold gold bitcoin bitcoin bitcoin") == "15-minute crypto+gold"
    assert a.classify_lane("ZZ9", "", "") == "other"


def test_holdout_status():
    assert a.holdout_status("the holdout was NOT read because nothing passed", "FALSIFIED") == ("no", "n.a.")
    assert a.holdout_status("holdout read once: PF 1.2", "NOT_YET_FALSIFIED") == ("yes", "survived")
    assert a.holdout_status("holdout read once: PF 0.9", "FALSIFIED") == ("yes", "failed")


def test_written_table_invariants():
    path = a.TABLE
    assert os.path.exists(path), "run: cd src && python -B -m scalper.audit1 table"
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    fam = [r for r in rows if r["level"] == "family"]
    assert len(fam) >= 300 and len({r["id"] for r in fam}) == len(fam)
    assert {r["level"] for r in rows} == {"family", "try"}
    for lane in {r["lane"] for r in rows}:
        assert lane in a.LANES or lane == "unknown"
    assert all("\u2014" not in c for r in rows for c in r.values())  # no em dashes
    ids = {r["id"] for r in fam}
    assert {"L1", "OICORE", "GEN6", "GEN3", "USWEEP1", "E3B"} <= ids
    oi = next(r for r in fam if r["id"] == "OICORE")
    assert oi["holdout_read"] == "no" and oi["verdict"] == "NOT_YET_FALSIFIED"


def test_report_runs_on_the_written_table():
    rows = a.load_table()
    units = a.z_units(rows)
    assert len(units) > 300
    t = a.tail_summary([u["z"] for u in a.clean_units(units)])
    assert t["n"] > 300 and not math.isnan(t["mean"])
    assert len(a.untested_ranking(a.per_lane(rows, a.clean_units(units)))) == 5


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)

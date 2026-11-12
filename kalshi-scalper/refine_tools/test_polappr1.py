"""Tests on synthetic answers (no real pulled data). Run: python3 -I kalshi-scalper/refine_tools/test_polappr1.py"""
import contextlib
import glob
import gzip
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import polappr1_convert as C  # noqa: E402
import polappr1_score as S  # noqa: E402

CUTS = S.load_cuts()
TR, VA, HO = 1780000000, 1791000000, 1793000000  # close times inside TRAIN, VALIDATE, HELD-OUT of APPR_DAILY and ALL_APPR


def ev(i, base):
    return "KXTRUMPAPPROVE-S%d" % i, base + i * 86400


def candle(ts, ask, bid):
    return {"end_period_ts": ts, "yes_ask": {"close_dollars": ask}, "yes_bid": {"close_dollars": bid}, "price": {"close_dollars": None}, "volume_fp": "1.00"}


def answer_hist(ct):
    return {"candlesticks": [candle(ct - 86400 - 3600, "0.3000", "0.2800"), candle(ct - 6 * 3600 - 3600, "0.3200", "0.3000")]}


def answer_live(tickers, cts):
    return {"markets": [{"market_ticker": t, "candlesticks": answer_hist(cts[t])["candlesticks"]} for t in tickers]}


# one historical request per market, one batched live request for two markets of one event
MK = {}
for i in range(3):
    e, ct = ev(i, TR)
    MK["%s-T1" % e] = [e, "KXTRUMPAPPROVE", ct, "yes" if i % 2 else "no"]
e, ct = ev(10, VA)
for k in ("A", "B"):
    MK["%s-%s" % (e, k)] = [e, "KXTRUMPAPPROVE", ct, "no"]
e, ct = ev(20, HO)
MK["%s-H" % e] = [e, "KXTRUMPAPPROVE", ct, "yes"]
HELD_ROW = {"t": "KXTRUMPAPPROVE-S99-X", "e": "KXTRUMPAPPROVE-S99", "s": "KXTRUMPAPPROVE", "ct": TR + 99 * 86400, "res": "yes",
            "src": "live", "c": [[TR + 99 * 86400 - 86400 - 3600, "0.4000", "0.3800", None, "2.00"]]}
HELD_OUT_HELD_ROW = dict(HELD_ROW, t="KXTRUMPAPPROVE-S98-X", e="KXTRUMPAPPROVE-S98", ct=HO + 98 * 86400)


def jobs():
    p1 = {"job_id": "POLAPPR1_CANDLES", "requests": [
        {"id": "h_%s" % t, "path": "/historical/markets/%s/candlesticks" % t, "params": {"start_ts": 1, "end_ts": 2, "period_interval": 60}}
        for t in sorted(MK) if t.endswith("-T1")]}
    e10 = ev(10, VA)[0]
    p2 = {"job_id": "POLAPPR1_CANDLES_P2", "requests": [
        {"id": "l_%s_0" % e10, "path": "/markets/candlesticks", "params": {"market_tickers": "%s-A,%s-B" % (e10, e10), "start_ts": 1, "end_ts": 2, "period_interval": 60}},
        {"id": "h_%s-H" % ev(20, HO)[0], "path": "/historical/markets/%s-H/candlesticks" % ev(20, HO)[0], "params": {"start_ts": 1, "end_ts": 2, "period_interval": 60}}]}
    return p1, p2


def body_for(job, req):
    if "market_tickers" in req["params"]:
        ts = req["params"]["market_tickers"].split(",")
        return answer_live(ts, {t: MK[t][2] for t in ts})
    t = req["path"].split("/")[3]
    return answer_hist(MK[t][2])


def mkrun(root, job_id, job, ids, status, badsha=None, truncated=None, folder=None):
    d = os.path.join(root, job_id, folder or ("2026-11-13T0100Z_%s" % status))
    os.makedirs(d)
    rows = []
    for i, r in enumerate([r for r in job["requests"] if r["id"] in ids], 1):
        body = json.dumps(body_for(job, r)).encode()
        fn = "%04d.json.gz" % i
        with open(os.path.join(d, fn), "wb") as f:
            f.write(gzip.compress(body))
        row = {"index": i, "id": r["id"], "status": 200, "bytes": len(body), "file": fn,
               "sha256": "0" * 64 if badsha == r["id"] else hashlib.sha256(body).hexdigest()}
        if truncated == r["id"]:
            row["truncated"] = True
        rows.append(row)
    json.dump({"job": {"job_id": job_id}, "status": status, "rows": rows}, open(os.path.join(d, "manifest.json"), "w"))
    open(os.path.join(d, "STATUS"), "w").write(status + "\n")


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.runs = os.path.join(self.tmp, "runs")
        os.makedirs(self.runs)
        self.out = os.path.join(self.tmp, "out")
        self.p1, self.p2 = jobs()
        self.jp = []
        for j in (self.p1, self.p2):
            p = os.path.join(self.tmp, j["job_id"] + ".json")
            json.dump(j, open(p, "w"))
            self.jp.append(p)
        self.mp = os.path.join(self.tmp, "meta.json")
        json.dump({"markets": MK}, open(self.mp, "w"))
        self.hp = os.path.join(self.tmp, "held.jsonl")
        with open(self.hp, "w") as f:
            f.write(json.dumps(HELD_ROW) + "\n" + json.dumps(HELD_OUT_HELD_ROW) + "\n")

    def conv(self):
        return C.convert(self.runs, self.out, self.jp, self.mp, self.hp)

    def full(self):
        mkrun(self.runs, "POLAPPR1_CANDLES", self.p1, {r["id"] for r in self.p1["requests"]}, "complete")
        mkrun(self.runs, "POLAPPR1_CANDLES_P2", self.p2, {r["id"] for r in self.p2["requests"]}, "complete")

    def marker(self):
        return os.path.exists(os.path.join(self.out, C.MARKER))

    # converter
    def test_incomplete_no_marker(self):
        mkrun(self.runs, "POLAPPR1_CANDLES", self.p1, {r["id"] for r in self.p1["requests"]}, "complete")
        self.assertFalse(self.conv())
        self.assertFalse(self.marker())
        self.assertFalse(os.path.exists(os.path.join(self.out, S.CANDLES)))

    def test_all_answered_but_latest_status_incomplete(self):
        mkrun(self.runs, "POLAPPR1_CANDLES", self.p1, {r["id"] for r in self.p1["requests"]}, "complete")
        mkrun(self.runs, "POLAPPR1_CANDLES_P2", self.p2, {r["id"] for r in self.p2["requests"]}, "stopped_429")
        self.assertFalse(self.conv())
        self.assertFalse(self.marker())

    def test_truncated_answer_is_not_an_answer(self):
        tid = self.p1["requests"][0]["id"]
        mkrun(self.runs, "POLAPPR1_CANDLES", self.p1, {r["id"] for r in self.p1["requests"]}, "complete", truncated=tid)
        mkrun(self.runs, "POLAPPR1_CANDLES_P2", self.p2, {r["id"] for r in self.p2["requests"]}, "complete")
        self.assertFalse(self.conv())

    def test_complete_writes_marker_and_drops_heldout(self):
        # part 1 answered in two runs (merge by request id), part 2 in one; the last run of each part is complete
        ids = [r["id"] for r in self.p1["requests"]]
        mkrun(self.runs, "POLAPPR1_CANDLES", self.p1, set(ids[:1]), "stopped_429", folder="2026-11-13T0100Z_1")
        mkrun(self.runs, "POLAPPR1_CANDLES", self.p1, set(ids[1:]), "complete", folder="2026-11-13T0200Z_2")
        mkrun(self.runs, "POLAPPR1_CANDLES_P2", self.p2, {r["id"] for r in self.p2["requests"]}, "complete")
        self.assertTrue(self.conv())
        self.assertEqual(open(os.path.join(self.out, C.MARKER)).read(), "5")
        rows = [json.loads(l) for l in open(os.path.join(self.out, S.CANDLES))]
        tick = {r["t"] for r in rows}
        self.assertIn(HELD_ROW["t"], tick)
        self.assertIn("%s-A" % ev(10, VA)[0], tick)
        self.assertNotIn("%s-H" % ev(20, HO)[0], tick)  # a held-out event pulled by mistake is dropped
        self.assertNotIn(HELD_OUT_HELD_ROW["t"], tick)   # and so is a held-out event of the first pull
        self.assertEqual(list(rows[0]), ["t", "e", "s", "ct", "res", "src", "c"])
        self.assertEqual(rows[0]["c"][0], [rows[0]["ct"] - 86400 - 3600, "0.3000", "0.2800", None, "1.00"])
        self.assertEqual(json.load(open(os.path.join(self.out, "POLAPPR1_INPUTS.json")))["rows_dropped_heldout"], 2)

    def test_second_part_of_other_job_is_ignored(self):
        mkrun(self.runs, "POLAPPR1_CANDLES", self.p1, {r["id"] for r in self.p1["requests"]}, "complete")
        mkrun(self.runs, "SOMETHING_ELSE", self.p2, {r["id"] for r in self.p2["requests"]}, "complete")
        self.assertFalse(self.conv())

    def test_bad_sha_refuses(self):
        mkrun(self.runs, "POLAPPR1_CANDLES", self.p1, {r["id"] for r in self.p1["requests"]}, "complete", badsha=self.p1["requests"][0]["id"])
        mkrun(self.runs, "POLAPPR1_CANDLES_P2", self.p2, {r["id"] for r in self.p2["requests"]}, "complete")
        with self.assertRaises(C.Refuse):
            self.conv()
        self.assertFalse(self.marker())

    def test_read_done_refuses_converter(self):
        os.makedirs(self.out)
        open(os.path.join(self.out, C.READ_DONE), "w").write("x")
        self.full()
        with self.assertRaises(C.Refuse):
            self.conv()

    # scorer
    def run_score(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = S.main([self.out])
        return rc, buf.getvalue()

    def test_scorer_silent_before_marker(self):
        os.makedirs(self.out)
        rows = [HELD_ROW]
        with open(os.path.join(self.out, S.CANDLES), "w") as f:
            f.write(json.dumps(rows[0]) + "\n")
        rc, txt = self.run_score()
        self.assertEqual(rc, 0)
        self.assertEqual(len(txt.strip().splitlines()), 1)
        self.assertNotIn("CELLS", txt)
        self.assertNotIn("OBS", txt)
        self.assertFalse(os.path.exists(os.path.join(self.out, S.READ_DONE)))

    def fake_cand(self, n_tr=40, n_va=15, n_ho=40):
        rows = []
        for base, n, tag, win in ((TR, n_tr, "T", None), (VA, n_va, "V", None), (HO, n_ho, "H", True)):
            for i in range(n):
                ct = base + i * 86400
                rows.append({"t": "KXTRUMPAPPROVE-%s%d-M" % (tag, i), "e": "KXTRUMPAPPROVE-%s%d" % (tag, i), "s": "KXTRUMPAPPROVE", "ct": ct,
                             "res": "yes" if (win or i % 3 == 0) else "no", "src": "hist",
                             "c": [[ct - 86400 - 3600, "0.3000", "0.2800", None, "1.00"]]})
        return rows

    def write_ready(self, rows):
        os.makedirs(self.out, exist_ok=True)
        open(os.path.join(self.out, S.CANDLES), "w").write("\n".join(json.dumps(r) for r in rows) + "\n")
        open(os.path.join(self.out, S.MARKER), "w").write("4")

    def test_scorer_reads_once(self):
        self.write_ready(self.fake_cand())
        rc, txt = self.run_score()
        self.assertEqual(rc, 0)
        self.assertIn("GRID 240 cells", txt)
        self.assertIn("no evidence at n = ", txt)
        self.assertTrue(os.path.exists(os.path.join(self.out, S.READ_DONE)))
        rc2, txt2 = self.run_score()
        self.assertEqual(rc2, 2)
        self.assertIn("refused", txt2)
        self.assertNotIn("GRID", txt2)

    def test_scorer_ignores_heldout_events(self):
        base = self.fake_cand(n_ho=0)
        with_ho = self.fake_cand(n_ho=60)
        obs0 = S.load_obs(base, CUTS)
        obs1 = S.load_obs(with_ho, CUTS)
        self.assertEqual(len(obs0), len(obs1))
        self.assertTrue(all(o["ect"] < CUTS["APPR_DAILY"][1] for o in obs1))
        self.assertEqual(sorted(o["e"] for o in obs0), sorted(o["e"] for o in obs1))
        # the held-out rows were all wins; they must not move any cell or the calibration table
        c0 = [(f, ln, pb, sd, len(tr), len(va)) for f, ln, pb, sd, tr, va in S.cells(obs0, CUTS)]
        c1 = [(f, ln, pb, sd, len(tr), len(va)) for f, ln, pb, sd, tr, va in S.cells(obs1, CUTS)]
        self.assertEqual(c0, c1)
        self.assertEqual(S.calibration(base, CUTS), S.calibration(with_ho, CUTS))
        r0, r1 = S.report(base, CUTS), S.report(with_ho, CUTS)
        i0 = next(i for i, l in enumerate(r0) if l.startswith("OBS"))
        self.assertEqual(r0[i0:], r1[next(i for i, l in enumerate(r1) if l.startswith("OBS")):])  # past the per-third event counts nothing changes

    def test_unlisted_event_is_assigned_by_cuts(self):
        self.assertEqual(S.third(CUTS, "APPR_DAILY", TR), "TRAIN")
        self.assertEqual(S.third(CUTS, "APPR_DAILY", VA), "VALID")
        self.assertEqual(S.third(CUTS, "APPR_DAILY", HO), "HELD")
        self.assertIn("APPR_538", CUTS)
        self.assertEqual(len(S.FAMILIES) * 4 * 5 * 2, 240)

    def test_cut_files_agree_with_event_lists(self):
        for fn in S.CUT_FILES:
            j = json.load(open(os.path.join(HERE, fn)))
            for fam, evs in j["events"].items():
                a, b = j["cuts"][fam]
                for e in evs:
                    want = "TRAIN" if e["close_ts"] < a else ("VALIDATE" if e["close_ts"] < b else "HELD-OUT")
                    self.assertEqual(e["third"], want, e["event"])

    # the committed job files
    def test_real_jobs(self):
        paths = sorted(glob.glob(os.path.join(HERE, "jobs", "POLAPPR1_CANDLES*.json")))
        self.assertEqual(len(paths), 3)
        meta = json.load(open(os.path.join(HERE, "POLAPPR1_MARKETS.json")))["markets"]
        listed_ho = set()
        for fn in S.CUT_FILES:
            for evs in json.load(open(os.path.join(HERE, fn)))["events"].values():
                listed_ho |= {e["event"] for e in evs if e["third"] == "HELD-OUT"}
        seen, total = set(), 0
        for p in paths:
            j = json.load(open(p))
            self.assertEqual(j["status"], "ready")
            self.assertLessEqual(len(j["requests"]), 1200)
            self.assertEqual(j["max_requests"], len(j["requests"]))
            self.assertIn(j["job_id"], os.path.basename(p))
            tk = set(j["ticker_allowlist"])
            for r in j["requests"]:
                self.assertNotIn(r["id"], seen)
                seen.add(r["id"])
                ts = r["params"]["market_tickers"].split(",") if "market_tickers" in r["params"] else [r["path"].split("/")[3]]
                for t in ts:
                    self.assertIn(t, tk)
                    self.assertIn(t, meta)
                    self.assertNotIn(meta[t][0], listed_ho)
                    self.assertFalse(S.is_heldout(CUTS, meta[t][1], meta[t][2]), t)
                total += len(ts)
        self.assertEqual(total, len(meta))


if __name__ == "__main__":
    unittest.main(verbosity=1)

import csv, os, tempfile, opengap1_convert as c
d = tempfile.mkdtemp()
def w(name, hdr, rows):
    with open(os.path.join(d, name), "w", newline="") as f: f.write(",".join(hdr) + "\n"); [f.write(",".join(map(str, r)) + "\n") for r in rows]
SH = ["ts_recv", "ts_event", "rtype", "publisher_id", "instrument_id", "ts_ref", "price", "quantity", "sequence", "ts_in_delta", "stat_type", "channel_id", "update_action", "stat_flags", "symbol"]
def srow(ts, price, st, sym): return [ts, ts, 24, 2, 1, ts, price, 0, 1, 0, st, 0, 1, 0, sym]
# QQQ: two days; Nov 9 open published at 14:30Z (first OPENING_PRICE, a later update at 14:31Z must not win), close = LAST CLOSE_PRICE record (21:00Z), a CLOSE_PRICE at 20:59Z earlier
w("xnas_stat.csv", SH, [srow("2026-11-06T21:00:00.000000000Z", 100.0, 11, "QQQ"), srow("2026-11-06T20:59:00.000000000Z", 99.0, 11, "QQQ"),
    srow("2026-11-09T14:30:00.000000000Z", 101.0, 1, "QQQ"), srow("2026-11-09T14:31:00.000000000Z", 105.0, 1, "QQQ"), srow("2026-11-09T14:00:00.000000000Z", 99.0, 2, "QQQ"),
    srow("2026-11-09T21:00:00.000000000Z", 102.0, 11, "QQQ"), srow("2026-11-09T14:29:00.000000000Z", 0.0, 1, "QQQ"),
    srow("2026-11-06T14:30:00.000000000Z", 99.5, 1, "QQQ"),
    ["bad", "NOT_A_TS", "x", "x", "x", "x", "BAD", "x", "x", "x", "BAD", "x", "x", "x", "US500"] + ["extra", "extra"],          # a malformed foreign row with extra columns: no effect
    srow("2026-11-09T14:30:00.000000000Z", 50.0, 1, "NVDA"), srow("2026-11-06T21:00:00.000000000Z", 50.0, 11, "NVDA")])
w("arcx_stat.csv", SH, [])
BH = ["ts_event", "rtype", "publisher_id", "instrument_id", "open", "high", "low", "close", "volume", "symbol"]
def brow(day, o, cl, sym): return [day + "T00:00:00.000000000Z", 35, 1, 1, o, o, o, cl, 1, sym]
w("equs_1d.csv", BH, [brow("2026-11-05", 99, 99.5, "QQQ"), brow("2026-11-06", 99.5, 100.0, "QQQ"), brow("2026-11-09", 101.01, 102.0, "QQQ"),
    brow("2026-11-06", 50, 50, "NVDA"), brow("2026-11-09", 52.0, 50.0, "NVDA")])          # NVDA open 50.0 vs bar 52.0 = 385 bps: set missing
out = os.path.join(d, "u.csv"); rows = c.convert(d, out)
d5 = tempfile.mkdtemp()
for n in ("xnas_stat.csv", "arcx_stat.csv"): open(os.path.join(d5, n), "w").write(open(os.path.join(d, n)).read())
with open(os.path.join(d5, "equs_1d.csv"), "w") as f:
    f.write("ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol\n")
    for day in ("2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06"): f.write(day + "T00:00:00.000000000Z,35,1,1,1,1,1,1,1,QQQ\n")
assert [x["date"] for x in c.convert(d5, os.path.join(d5, "u.csv"))] == ["2026-11-06"]          # events start on 2026-11-06 only
r = {(x["perp"], x["date"]): x for x in rows}
q = r[("KXQQQPERP", "2026-11-09")]
assert q["prev_date"] == "2026-11-06" and q["u_open"] == "101.0" and q["u_prev_close"] == "100.0" and q["x_open"] == "101.01" and q["x_prev_close"] == "100.0", q
q6 = r[("KXQQQPERP", "2026-11-06")]; assert q6["prev_date"] == "2026-11-05" and q6["u_open"] == "99.5" and q6["u_prev_close"] == "" and q6["x_prev_close"] == "99.5", q6          # no Nov 5 statistic: missing
n = r[("KXNVDAPERP", "2026-11-09")]; assert n["u_open"] == "" and n["u_prev_close"] == "50.0", n          # the open differs from the bar by more than 25 bps: missing
assert ("KXQQQPERP", "2026-11-05") not in r and all(x["date"] >= "2026-11-06" for x in rows) and not any(x["perp"] == "US500" for x in rows)
# the converter's output is what opengap1_second.load reads
import opengap1_second as g
with open(out) as f: ur = list(csv.DictReader(f)); assert ur[0].keys() == {"perp", "date", "prev_date", "u_open", "u_prev_close", "x_open", "x_prev_close"}
assert (c.STAT_OPEN, c.STAT_CLOSE, c.TOL_BPS) == (1, 11, 25.0)
# ET date assignment near midnight: 04:30Z on Nov 10 is 23:30 ET on Nov 9 (UTC - 5), so it belongs to Nov 9
import tempfile as tf
d3 = tf.mkdtemp(); w3 = os.path.join(d3, "x.csv")
with open(w3, "w", newline="") as f: f.write(",".join(SH) + "\n"); f.write(",".join(map(str, srow("2026-11-10T04:30:00.000000000Z", 7.0, 11, "QQQ"))) + "\n"); f.write(",".join(map(str, srow("2026-11-10T05:30:00.000000000Z", 8.0, 11, "QQQ"))) + "\n")
o3, c3 = c.read_stats(w3); assert c3 == {("QQQ", "2026-11-09"): 7.0, ("QQQ", "2026-11-10"): 8.0}, c3
print("opengap1 convert tests passed")

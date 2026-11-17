"""Test of side_check.py on INVENTED live files. python3 -I side_check_test.py"""
import os, sys, gzip, csv, tempfile, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import side_check as S
T0 = calendar.timegm((2026, 11, 17, 5, 0, 0)) * 1000
BH = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "bid_px_1", "ask_px_1"]
TH = ["t_recv_ms", "server_date_header", "ticker", "created_time", "price", "count", "taker_side", "is_block_trade"]
def make(mapping):
    root = tempfile.mkdtemp(); d = os.path.join(root, "perplive", "2026-11-17", "0500"); os.makedirs(d)
    book = [[T0 + i * 1000, T0 + i * 1000 + 50, "x", "KXBTCPERP", 10.00, 10.10] for i in range(1500)]
    tape = []
    for i in range(1, 1499):
        for side, kind in (("bid", mapping[0]), ("ask", mapping[1])):
            px = 10.10 if kind == "ask" else (10.00 if kind == "bid" else 10.05)
            if i % 20 == 0: px = 10.05                                       # 5% print inside: still above 0.80
            tape.append([T0 + i * 1000 + 200, "x", "KXBTCPERP", "2026-11-17T05:%02d:%02d.500Z" % (i // 60 % 60, i % 60), "%.2f" % px, "3.0", side, "False"])
    tape.append([T0 + 5, "x", "KXBTCPERP", "2026-11-17T05:00:00.900Z", "10.10", "1.0", "weird", "False"])   # other string
    tape.append([T0 + 6, "x", "KXBTCPERP", "2026-11-17T05:00:01.900Z", "10.10", "1.0", "bid", "True"])     # block row
    tape.append(tape[0][:])                                                       # the same row again, same t_recv: both kept
    dup = tape[1][:]; dup[0] = tape[1][0] + 60000; tape.append(dup)               # same trade on a later page: dropped
    with gzip.open(os.path.join(d, "book.csv.gz"), "wt", newline="") as fo: w = csv.writer(fo); w.writerow(BH); w.writerows(book)
    with gzip.open(os.path.join(d, "tape.csv.gz"), "wt", newline="") as fo: w = csv.writer(fo); w.writerow(TH); w.writerows(tape)
    return root
for name, mp, want in (("A", ("ask", "bid"), "MAPPING A"), ("B", ("bid", "ask"), "MAPPING B"), ("none", ("mid", "mid"), "NO MAPPING")):
    root = make(mp); out = os.path.join(root, "o.txt")
    try: S.run(root, out); raise SystemExit("ran without an allow line")
    except SystemExit as e: assert str(e).startswith("REFUSED"), e
    S.run(root, out, check_allow=False); t = open(out).read()
    assert ("verdict (fixed threshold 0.80, at least 1000 per side): " + want) in t or (name == "none" and "NO MAPPING" in t), (name, t[:900])
    print("ok", name, [l for l in t.split("\n") if l.startswith("ALL ") or "other_string" in l])

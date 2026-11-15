"""Hand case INGAME_HAND_CASE_NOV15.md, invented rows. Run: python3 -I test_ingame1.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingame1 as I
A = lambda x, y: abs(x - y) < 1e-12
B = 1794200000
r = lambda t, k, tk, b, a: (B + t, "KXNBAGAME-G1", k, tk, b, a)
f1 = I.fade([r(0, "ml", "M", 0.40, 0.42), r(30, "ml", "M", 0.52, 0.54)])
assert f1[:3] == ("M", "no", 0.48) and A(I.net(0.48, 0.02, "no", "no", 1), 0.48)
assert I.fade([r(0, "ml", "M", 0.40, 0.42), r(50, "ml", "M", 0.52, 0.54)]) is None
f3 = I.fade([r(0, "ml", "M", 0.80, 0.82), r(20, "ml", "M", 0.68, 0.70), r(100, "ml", "M", 0.50, 0.52), r(120, "ml", "M", 0.38, 0.40)])
assert f3[:3] == ("M", "yes", 0.40) and f3[3] == B + 120
print("fade: ok")
ml = [r(0, "ml", "M", 0.5, 0.52), r(100, "ml", "M", 0.5, 0.52), r(120, "ml", "M", 0.5, 0.52)]
assert I.live_time(ml) == B + 120
u1 = I.under(ml, [r(110, "total", "T", 0.40, 0.44), r(140, "total", "T", 0.45, 0.47)])
assert u1[:3] == ("T", "no", 0.55) and A(I.net(0.55, 0.02, "no", "no", 1), 0.41) and A(I.net(0.55, 0.02, "yes", "no", 1), -0.59)
assert I.under(ml, [r(140, "total", "T", 0.20, 0.22)]) is None
print("under: ok")
G = {"NBA|G1": {"league": "NBA", "ml": [r(0, "ml", "M", 0.40, 0.42), r(30, "ml", "M", 0.52, 0.54)], "total": []},
     "NBA|G2": {"league": "NBA", "ml": [r(0, "ml", "N", 0.40, 0.42), r(30, "ml", "N", 0.52, 0.54)], "total": []}}
tr = I.evaluate(G, {"M": (1794300000, "no")})            # N not in the listing: dropped
assert len(tr["IGFADE1"]) == 1 and tr["IGFADE1"][0]["third"] == 1
assert I.verdict(I.summarise(tr["IGFADE1"])) == "no evidence at n = 1"
rows = I.parse_rows(["t_recv_ms,server_date,event,kind,ticker,strike,yes_bid,yes_ask,bid_size,ask_size,last_price,volume",
                     "1794200000000,d,KXNHLGAME-X,ml,T1,,0.4,0.42,1,1,0.41,5", "1794528000000,d,KXNHLGAME-X,ml,T1,,0.4,0.42,1,1,0.41,5",
                     "1794200001000,d,KXNHLGAME-X,ml,T1,,,0.42,1,1,0.41,5"])
assert len(rows) == 2 and rows[0][4] == 0.4 and rows[1][4] is None and I.league_of("KXNHLGAME-X") == "NHL" and I.game_of("KXNHLGAME-X") == "X"
print("parse and wiring: ok")

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import prog1 as P

def row(day, close, series, net, gross=None):
    return {"day": day, "close_ts": close, "series": series, "net": net, "raw": net, "stress": net, "raw_stress": net, "gross": net if gross is None else gross}
# allocator uses only EARLIER days: a cell that is great only on the scored day itself must not be picked on it
rows = []
for d in range(20):
    day = f"2026-09-{d + 1:02d}"
    base = 1_790_000_000 + d * 86400
    rows.append(row(day, base, "A", -0.05))
    rows.append(row(day, base, "B", 0.20 if d == 19 else -0.05))
picked, pool = P.allocator(P.adjust(rows) if False else rows)
assert all(not (r["series"] == "B" and r["day"] == "2026-09-20") for r in picked), "allocator saw the future"
# previous_losses counts only earlier windows
rows = [row("d", 10_000 + 900 * k, "A", -1.0 if k == 0 else 0.1, gross=-1.0 if k == 0 else 0.1) for k in range(7)]
pl = P.previous_losses(rows)
assert pl[10_000] == 0 and pl[10_900] == 1 and pl[10_000 + 900 * 5] == 0 and pl[10_000 + 900 * 4] == 1
print("prog1 tests ok")
# P6: only earlier days feed the score, so a cell that is great only on the scored day is not picked on it
rows = []
for d in range(20):
    day = f"2026-09-{d + 1:02d}"; base = 1_790_000_000 + d * 86400
    for left in (540, 360):
        for s_ in ("A", "B"):
            for k in range(40):          # enough earlier entries per cell to clear the minimum
                net = 0.02 if (s_ == "A") else (0.30 if (d == 19 and left == 360) else -0.03)
                rows.append({"day": day, "close_ts": base + 900 * k, "series": s_, "left": left, "net": net, "raw": net, "stress": net, "raw_stress": net, "gross": net})
picked, pool = P.allocator_p6(rows)
assert picked and all(not (r["series"] == "B") for r in picked), [(r["series"], r["day"]) for r in picked if r["series"] == "B"]
print("p6 tests ok")

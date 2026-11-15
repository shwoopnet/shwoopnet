# ADJWIN1 hand case (Desk A, Nov 15, 2026). Written and worked by hand BEFORE any code. Invented series KXZZ15M, no real data.

Rules as in ADJWIN1_REGISTRATION_NOV15.md (amended, commit 1b6950668). Times are seconds relative to T, the close of window P and the open of window W (W closes at T+900). A candle is named by its END time.

**Window P (closes T):** first candle ending after P's open ends at T-840: bid 0.49, ask 0.51, mid 0.50. The last candle ending at least 60 s before the close ends at T-60: bid 0.84, ask 0.86, mid 0.85. A candle ending at T (the close) shows bid 0.98, ask 1.00 (the result bleeding in): NOT used. drift(P) = 0.85 - 0.50 = +0.35, at least 0.30, so a signal.

**Window W:** the candle ending at T is P's last candle, not W's first. W's first candle ends at T+60: bid 0.49, ask 0.51, two-sided and 0 < bid < ask < 1. Entry side: arm M buys YES at ask 0.51 (inside 0.40 to 0.60). Arm R buys NO at 1 - YES bid = 0.51 (inside the band).

**Cost (by hand):** price paid = ask + h, with h = 0, 0.01, 0.02. Fee per order of 10 contracts = ceil(0.07 x 10 x p x (1-p) x 100 - 1e-9) / 100, on the price paid: p 0.51: 0.2499 x 0.7 x 100 = 17.493, ceil 18, 0.18, per contract 0.018. p 0.52: 0.2496 x 0.7 x 100 = 17.472, ceil 18, 0.018. p 0.53: 0.2491 x 0.7 x 100 = 17.437, ceil 18, 0.018.

**Expected, W settles YES:** arm M wins, net per contract = 1 - p - 0.018: h 0: +0.472; 1c: +0.462; 2c: +0.452. Arm R loses, net = -(p + 0.018): h 0: -0.528; 1c: -0.538; 2c: -0.548.
**Expected, W settles NO:** arm M -0.528, -0.538, -0.548 and arm R +0.472, +0.462, +0.452 (the same numbers swapped).

**No-signal and skip cases (expected: no entry, counted):**
1. P last candle (T-60) mid 0.74: drift +0.24, under 0.30: no signal.
2. Drift -0.35 (P's T-60 mid 0.15): signal; arm R buys YES, arm M buys NO (mirror).
3. W's first candle ask 0.62 (outside 0.40 to 0.60): skip, counted as "out of band".
4. W's first candle bid 0 (one-sided): skip, counted.
5. P has no candle ending in [T-120, T-60]: skip, counted as "P incomplete".
6. W's first candle is the one ending exactly at T (before the open): must NOT be used; the first usable one ends at T+60.
7. A window closing at or after 2026-10-03T16:00Z (1791043200): dropped on load before anything else; counted as "after the cut".

**Stats on the two-window set (case 1 settles YES, case 2 above settles YES with drift -0.35, W bid 0.49 ask 0.51):** case 2 arm R buys YES at 0.51 and wins; arm M buys NO at 0.51 and loses. So at h 0: arm R trades {+0.472 (case 2), -0.528 (case 1)}, PF = 0.472 / 0.528 = 0.8939; arm M trades {+0.472, -0.528}, the same PF. n 2, "no evidence at n under 100".

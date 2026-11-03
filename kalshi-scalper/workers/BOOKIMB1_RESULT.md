# BOOKIMB1 result (DEV only, scored once 2026-11-03; registration sha256 c4937a53...f83f6 plus Amendment 1; `src/scalper/bookimb1.py`; discovery only)

Verdict by the code: **NOT_ENOUGH_DATA** (52 ON trades of the 150 needed). The kill rule, applied for information, WOULD be met (ON PF 0.93 in HALF2 against the bar 1.5), so the idea is not alive on DEV; the ON-minus-OFF difference was positive in both halves (+7.4c, +10.9c), which is the part to watch forward and which is NOT evidence at n 52 versus 43. Holdout not opened. No counterparty named (no pass).

Raw output of `python -m scalper.bookimb1 run`:

```
BOOKIMB1 DEV (closes 2026-10-29 to 2026-11-01): 99 candidate trades, 95 tradable (ask in 3c-30c at the fill poll, size>=10), 0 without a result
fee x1.0  ON : n 52 win 19.2% at mean ask 15.8% per trade +2.56c PF 1.20 z 0.55
fee x1.0  OFF: n 43 win 14.0% at mean ask 18.0% per trade -5.10c PF 0.68 z -1.94
fee x1.2  ON : n 52 win 19.2% at mean ask 15.8% per trade +2.37c PF 1.19 z 0.51
fee x1.2  OFF: n 43 win 14.0% at mean ask 18.0% per trade -5.32c PF 0.67 z -2.03
H1 ON : n 21 win 28.6% at mean ask 19.8% per trade +7.64c PF 1.55 z 0.72 | OFF: n 24 win 20.8% at mean ask 19.5% per trade +0.20c PF 1.01 z 0.32 | ON-OFF +7.44c
H2 ON : n 31 win 12.9% at mean ask 13.0% per trade -0.89c PF 0.93 z -2.13 | OFF: n 19 win 5.3% at mean ask 16.1% per trade -11.81c PF 0.24 z -17.52 | ON-OFF +10.92c
YES side  ON : n 23 win 8.7% at mean ask 15.4% per trade -7.64c PF 0.49 z -1.13
YES side  OFF: n 21 win 19.0% at mean ask 18.7% per trade -0.71c PF 0.95 z -0.12
NO side  ON : n 29 win 27.6% at mean ask 16.0% per trade +10.65c PF 1.98 z 1.22
NO side  OFF: n 22 win 9.1% at mean ask 17.4% per trade -9.30c PF 0.45 z -1.93
VERDICT: NOT_ENOUGH_DATA (information: kill rule met if the ON-trade gate were ignored)
ON trades per day 13.0; days to 150 ON trades 12
HOLDOUT not opened (DEV did not pass)
```

Reading: the OFF group (imbalance <= 0) lost at the usual cheap-tail rate (PF 0.68, win 14.0% at a mean ask of 18.0%, -5.1c per trade, the same family as LADLONG1 and the MAKERTAIL1 taker comparison); the ON group won 19.2% at 15.8%, +2.56c per trade, PF 1.20, day-clustered z 0.55 (far under the 5.27 bar). By side, ON is concentrated in NO tails (n 29, PF 1.98) while YES ON is negative (n 23, PF 0.49): a second post hoc side cut on the same 3.5 days that MAKERTAIL1 also split, not a registered claim and not to be extended on DEV. The H1/H2 flip (H1 ON PF 1.55, H2 ON PF 0.93) is the usual small sample noise.

Ties and disclosure: the DEV days are the same days on which the coordinator saw MAKERTAIL1's outcomes. One definition typo (float tolerance on "within 3 ticks") was fixed by Amendment 1 before any outcome was joined. Only counts of trades were printed before the registration was committed.

Forward plan: closes from 2026-11-03 16:00Z, `python -m scalper.bookimb1_fwd forward` (fwdread guard: refuses a second read, refuses before 150 settled ON forward trades unless it is 2026-12-15 or later; prints the README line). At the DEV rate of about 13 ON trades a day, 150 ON trades arrive in about 12 days (about 2026-11-15). Forward kill rules are the DEV ones on the forward halves.

N: +2 (one rule). Running count about 730,217; z bar about 5.27.

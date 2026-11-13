# LIQREV build 1: the readings this build had to fix (Idea Desk C, Nov 13, 2026)

The card (a16c8e3c) leaves these points open. Build 1 (`liqrev_score.py`) uses the reading in each line. They are for the Head of R&D to rule into the card as a dated amendment, so a second build can be made from the card alone. No data was read. [research]

- **R1, side:** in OKX's liquidation feed, `side` is the side of the liquidation ORDER. `sell` means a long position was liquidated (forced selling, so bet YES); `buy` means a short was liquidated (forced buying, so bet NO). `pos_side` is not used, because net-mode rows carry `net`.
- **R2, size in BTC:** BTC-USDT-SWAP is `sz` x 0.01 BTC. BTC-USD-SWAP is `sz` x 100 USD / `bk_px`. Contract values are from OKX's instrument spec, to be confirmed by the probe or the recorder's notes. Any other instrument is refused.
- **R3, L(t):** the BTC of one side with `ts_ms` in [t - 180 s, t), where t is a whole-minute boundary.
- **R4, trigger minutes:** the whole-minute boundaries t with close minus t from 720 s to 180 s inclusive, so 10 checks a window, in time order.
- **R5, H:**
  - the 99th percentile, nearest rank (ceil(0.99 x n)), over BOTH sides' L(t) pooled, two values a minute, for every whole minute from 2026-11-10T00:00Z to before 2026-11-17T00:00Z;
  - minutes outside the OKX recorder's coverage are left out;
  - H is a frozen input to the scorer and is not computed until Auditor B is CLEAN.
- **R5b, both sides at once:** if both sides reach H at the same minute, there is no bet in that window (counted as "both_sides").
- **R6, the quote:** the first R6 poll with `t_recv_ms` in (t, t + 10 s]; none means "no_quote". YES ask = 1 - `no_bid_px_1`; NO ask = 1 - `yes_bid_px_1`; spread = YES ask - `yes_bid_px_1` for both sides. It is usable only if 0 < yes bid < YES ask < 1.
- **R7, band and spread:** ask 0.20 to 0.80 and spread 0.04 or less, inclusive, with a 1e-9 tolerance, on the ask seen. If the first trigger minute fails them, the window is USED: no later minute is tried.
- **R8, fill and fee:** at the ask seen with no +1c, plus the fee 0.07 x p x (1 - p) rounded up to the cent. A void is a fee-only loss counted as a bet. Results other than yes, no or void are refused, and so is a duplicate window.
- **R9, the conflict rule (OICORE and CFRTI-K opposite side): NOT implemented in build 1.** Knowing whether OICORE or CFRTI-K placed an order needs the bot's live order log, which must not enter this public repo. **For the Head:** either (a) the conflict check runs privately, and only the count of excluded windows is printed; or (b) for the paper record it is replaced by a public proxy (CFRTI-K's and OICORE's own signals recomputed from public data); or (c) it is dropped for the paper read and kept only for any later live seat.
- **R10, results:** from public settled results, joined by ticker.
- **R11, statistics:**
  - PF = gross gain / gross loss;
  - z is clustered by the US Central date of the close, using the sample standard deviation over days with at least one bet;
  - all bar tests are on unrounded values.
- **R12, duplicates:** OKX rows are de-duplicated on the recorder's own key (inst_id, ts_ms, side, pos_side, bk_px, sz).
- **R13, read guards:**
  - development read refused before 2026-11-30T00:00Z;
  - held-out read refused before 2027-01-02T00:00Z, and it runs once (a marker file);
  - development mode ignores and counts held-out windows.
- **R14, kills:**
  - zero-try count: fewer than 60 triggered windows with a two-sided quote closes it, where triggered = bets plus band or spread failures;
  - development: fewer than 60 bets, PF under 1.0, or a half under 1.2;
  - with fewer than 30 bets: "no evidence at n = x";
  - held-out: PASS only if development CONTINUEs, PF is 1.5 or better in development half 1, half 2 and the held-out, and the held-out z is 5.46 or more; otherwise FALSIFIED, which closes the liquidation-fade family.
- **R15, coverage:** a window is scored only if one OKX recorder coverage interval contains [close - 720 s - 180 s, close - 180 s). Otherwise it is "no_liq_coverage", because a missing feed would read as no liquidations. Coverage intervals come from the recorder's coverage.csv. How they are built belongs to the row builder (a separate file, written later and audited).

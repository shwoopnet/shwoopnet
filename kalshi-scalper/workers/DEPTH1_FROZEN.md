# DEPTH1 frozen features (sha256, written before any R6 row was opened)

Frozen 2026-10-30T16:13Z by `python -m scalper.depth1 freeze`. `tests/test_depth1.py` fails if any source below changes.

**Total sha256: `8eb6aa3842fa4bb50cebbe2f1b2f87df726296e0d0b16964cc7e9b45a8deeb69`**

| Name | sha256 of its source |
|---|---|
| _sums | `f8185737308f73c9dacdf4268836951f2ca52b56051b26dd4f318dc625f722bf` |
| _imb | `06a9a4d4b12eb23141a00cf447aa446eb1926ab486489af2c804327de5e36aad` |
| _slope | `fce44144c8f4b3c2c8c02ea0298352e4bb4b2521ea9423f0509c841cc90543e1` |
| f1_imb5 | `75b25e9d70da079bfc993f7730045daf1a41b5a3fec9f7660c4a184e4586453a` |
| f2_imb1 | `7c86b175b2032a15802c358dec9eb4c9a7423c818301b65c899222a5f7b6cf7f` |
| f3_dwmid_minus_mid | `40834d07bacecaf0ff7bf6c54a09022f1ef2af4d30f74058b1b2b5173a8c1c92` |
| f4_d_imb30 | `299266c1b4b850b06434603ba57fc1fd345ed9a29497d458c60d50403a9ccaf7` |
| f5_d_imb60 | `39fb3a09067ff4a4d2e5d94a84652707a6ad7b5b34531ec9e53a599cc94922f1` |
| f6_thin_depletion | `663b58aaf8d0a1380ca540b6e8e039bda157f044d83abd83e7598996a48af668` |
| f7_sweep_net | `87aa311df0937fb0e275bc4755c9c696c188b80b46b404447944044eae1e8082` |
| f8_hole_asymmetry | `e3924bab0d9c0732ced60936deb8d2031f645fedbaf744fbfc17d40ffa965eec` |
| f9_book_slope | `53aeb749749406f8afe293b4eddd9268ebc7e8a319dce4fba06909617232a6d5` |
| f10_imb_3c | `06269e724d23eaa2eb24cef3359200df4ef27d033aa1fe752abe7082bb77fa54` |
| CONFIG | `374c907dcf571a04d430d05ab5d1c0ea4444de69b9bb6137ec76599436ae30b0` |

Fixed settings (CONFIG, hashed as one block):

```json
{
 "ask_band": [
  0.1,
  0.9
 ],
 "bar": {
  "halves_pf_above": 1.0,
  "n_trades": 300,
  "pf_each_block": 1.5,
  "pf_pooled": 1.5,
  "stress_pf_above": 1.2,
  "z_bar_N": 728648
 },
 "blocks_by_central_close_date": [
  [
   "2026-10-30",
   "2026-11-03"
  ],
  [
   "2026-11-04",
   "2026-11-08"
  ],
  [
   "2026-11-09",
   "2026-11-13"
  ]
 ],
 "control": {
  "p": 0.01,
  "seed": 20261114,
  "shuffles": 1000,
  "stat": "mean net per trade, best of 20 tries per shuffle round"
 },
 "decision_poll_max_early_s": 10,
 "decision_s_before_close": 480,
 "fee": "7% x C x p x (1-p) rounded up to the cent per order, C = 1; stress = fee x 1.2",
 "fill": "first poll at or after decision + 1.0 s, best ask of the implied side, 1 contract, held to settlement",
 "fill_poll_max_late_s": 20,
 "first_date": "2026-10-30",
 "live_delay_s": 1.0,
 "lookback_poll_max_early_s": 6,
 "markets": [
  "KXGOLD15M",
  "KXBTC15M"
 ],
 "min_ask_size": 1.0,
 "needed_windows_per_market": 300,
 "overlap": {
  "btc": "OICORE: a side's ask 0.05 to 0.50 at the candle ending 180 s before the close and open interest up more than 86299.56 over the 3 minutes before",
  "gold": "L1: exactly one side's ask 0.88 to 0.97 at the poll ending 360 s before the close"
 },
 "read_not_before_utc": "2026-11-14T00:00:00Z",
 "recorder_end_utc": "2026-11-13T23:59:00Z",
 "second_look": {
  "accuracy": 0.55,
  "n": 300
 },
 "sign_rule": "feature > 0 buys YES, < 0 buys NO, 0 or undefined: no trade; no threshold",
 "tape_lookback_s": 60,
 "usable": {
  "bad_notes": [
   "tape incomplete",
   "tape page cap",
   "tape out of time"
  ],
  "first_recv_at_or_before_s": 545,
  "last_recv_at_or_after_s": 470,
  "max_gap_ms": 20000,
  "min_ok_polls": 0.8,
  "result": "yes or no",
  "tape_pages_min": 1
 }
}
```

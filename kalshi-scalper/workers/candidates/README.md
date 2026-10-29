# Forward ledger candidates (FWDLEDGER, research only)

Every `*.json` file in this folder is one candidate. `python -m scalper.fwdledger run` (run once per AUTO pass by
`scalper.autoscore check`, hourly) evaluates each one on every window that CLOSED after its freeze time, had the data its rule
needs and has settled, and writes `workers/FORWARD_LEDGER.md`. The ledger only reports. It never promotes, sizes or trades
anything; the most it says is READY FOR THE FALSIFIER (forward PF 1.5+ at 1 AND 10 contracts, 30+ trades, 10+ trade days), which
earns a falsifier read and nothing more. Verdict words stay those of `workers/RULES.md`.

## How a generator adds a candidate

1. Freeze the rule first (discovery or validation done, parameters fixed). Pick a freeze time at or after the moment you commit,
   never earlier: forward evidence counts only for windows closing after it, so a past freeze would score in-sample windows.
2. If your rule's shape is not covered by an existing evaluator, add one (a plain function, see the interface below) in your own
   module under `kalshi-scalper/src/scalper/` (for example `scalper.gen4:forward_eval`). Do not edit `fwdledger.py` for it.
3. Write `workers/candidates/<ID>.json` and commit it (with the evaluator, if new). The next AUTO pass picks it up; to see it at
   once run `cd kalshi-scalper && PYTHONPATH=src python -m scalper.fwdledger run`.
4. Never edit a candidate after its freeze. A changed rule is a NEW id with a new freeze time; delete nothing (a dead candidate
   just keeps reporting).

## The JSON

```json
{
 "id": "GEN4_0007",
 "market": "KXGOLD15M",
 "stage": "validation",
 "freeze_utc": "2026-11-01T00:00:00Z",
 "source": "candles",
 "evaluator": "scalper.gen4:forward_eval",
 "params": {"anything": "your evaluator reads"},
 "generator": "GEN4",
 "description": "one plain line"
}
```

| field | meaning |
|---|---|
| `id` | unique; the file name should be `<id>.json` |
| `market` | a series ticker (`KXGOLD15M`, `KXBTC15M`) or a list of them |
| `stage` | stage reached before the freeze: `discovery`, `validation` (`reference` is for baselines such as `REF_L1_GOLD`) |
| `freeze_utc` | ISO time, UTC. Only windows with close time strictly after it count |
| `source` | `candles`, `quotes` or `r6` (below) |
| `evaluator` | `module:function`, importable with `PYTHONPATH=src` |
| `params` | passed unchanged to the evaluator |
| `generator`, `description` | optional, shown in the history section |

A file that does not parse, misses a field, names an unknown source or an evaluator that will not import is shown as
NOT_RUNNABLE on its own row; the other candidates run normally.

## Data sources (what `window` holds)

Every window has `source`, `ticker`, `series`, `close_ts` (unix seconds) and `result` (`"yes"` or `"no"`; unsettled windows are
never passed to an evaluator).

| source | where | extra keys |
|---|---|---|
| `candles` | 1 minute candles in `data/fresh.sqlite`, refreshed by `python -m scalper.fresh_update` (AUTO runs it every 6 hours) | `strike`; `candles` = `{end_ts: (yes_bid_close, yes_ask_close, volume, oi)}`; `peers` = `{series: candles}` for the other 15 minute markets closing at the same time (BTC, ETH and gold are always loaded) |
| `quotes` | the quote recorder, `origin/quote-data` `quotes/*/` (about two polls a second in the last ~150 s) | `polls` = sorted `[(t_recv_s, yes_bid, yes_ask, bid_size, ask_size)]`; `coverage` = its coverage row |
| `r6` | recorder R6, `origin/quote-data` `book15r6/*/` | `polls` = sorted `[scalper.quote2b.Poll]` (exchange time, 5 levels a side); `trades` = `[(t, yes_price, count, side)]`, side +1 taker bought YES; `coverage` |

## The evaluator interface

```python
from scalper.fwdeval import NoData

def forward_eval(window: dict, params: dict) -> dict | None:
    ...
    return {"side": "yes" or "no",        # the side bought
            "entry": 0.93,                 # the ask paid, a quote you could hit at or after the signal
            "exit": None,                  # None = held to settlement; else the bid sold at
            "t": 1793301360,               # optional: unix second of the entry quote
            "zero_volume": False,          # optional: entry or exit candle had no volume (counted in the history)
            "note": "..."}                 # optional
```

- Return `None` when the rule does not trade the window. Size is always one decision of 1 contract; the ledger prices it at 1 and
  10 contracts (fee 7% x C x p x (1-p) rounded up to the cent per order, both legs for an exit, the entry leg only when held, plus
  a x1.2 fee stress at 10 contracts).
- Raise `NoData("why")` when the window lacks what the rule needs (a missing candle at the look, spot bars, a peer market). That
  window is then NOT counted as evaluated, so a data gap is never scored as a no-trade. Do not default a missing input to 0.
- Use only data up to the entry time to decide, and only quotes at or after the signal to fill. The evaluator sees the whole
  window (it needs later quotes for exits), so this is on the author.
- Any other exception is counted per window as an evaluator error and shown in the flag column; it never stops the run.

## Reference evaluators (`src/scalper/fwdeval.py`)

- `scalper.fwdeval:l1_like` (source `candles`): the side whose ask is in `[lo, hi]` at the candle ending exactly `look_s` seconds
  before the close, bought at that ask and held. Params `look_s` (360), `lo` (0.88), `hi` (0.97), `sides` (`["yes", "no"]`).
  `REF_L1_GOLD.json` is the live L1 gold rule as a baseline (it ignores the live 25c exit and the window limit).
- `scalper.fwdeval:gen1` (source `candles`): ONE GEN1 strategy dict (`L_hi`, `L_lo`, `side`, `asset`, `conds`, `c`, exactly as in
  `data/gen1_survivors.json`), passed as `{"strategy": {...}}`, with GEN1's own features and exits. Checked against
  `scalper.gen1.trades` on its row file: 37 random grammar draws, identical trades and nets on every window with data. It raises
  NoData where GEN1 silently used 0 (spot `z`, `r3`; perp flow `tb1`, `tb5`; a missing peer for `xa_*`, `xb_*`) when a condition
  uses that feature. Spot (`data/search5k.sqlite`) and perp bars (`data/binance/`) are not refreshed automatically, so a GEN1 rule
  on BTC using those features reports no forward windows until they are.

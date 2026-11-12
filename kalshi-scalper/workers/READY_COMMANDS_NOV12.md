# Commands for the CFRTI-K and PERPBIN1 development reads (Idea Desk A, ready Nov 12, 2026; each run ONCE, as frozen)
Inputs (kalshi-pull run folders on `kalshi-pull-data`, copied with `git show origin/kalshi-pull-data:<path>`): LISTS = `pull/CFRTI_K_LISTS/2026-11-12T1645Z_43262026759`; PERP = `pull/PERPBTC1M/2026-11-12T1550Z_43252136600`; CANDLES = the `pull/CFRTI_K_CANDLES/<run>` folder when it lands (215 answers). Optional Kraken minute file for the lead/lag line: columns ts,price (made from the quote recorder's spot rows, development days).
```
python3 -I desk_a_verify/cfrti_k.py dev <LISTS> <CANDLES> <PERP> <kraken_minute.csv>     # CFRTI-K: registered line, thirds, haircut (a), line (b), LABEL, Block P condition, lead/lag
python3 -I desk_a_verify/perpbin1.py dev <LISTS> <CANDLES> <PERP>                      # PERPBIN1: tries A and B
```
Both keep only markets closing after 2026-09-12 and before 2026-11-05 (development = post-cutover, section 13). CFRTI-K prints the market's rules text first; it must read as the BRTI 60 second average before the open for the strike (it does in the list answer). Loaders were smoke-tested on the R6 slice answers (407 of 407 slice windows have every input present; structure only, nothing scored). Neither script has a held-out mode: the held-out candles are not pulled before Nov 20.

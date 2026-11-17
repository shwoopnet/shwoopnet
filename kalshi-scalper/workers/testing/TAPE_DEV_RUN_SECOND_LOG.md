# Tape bars, development range, second build: run log (Testing Desk, Nov 17, 2026)

Builder tape_bars_second.py sha256 550ce6610948800cdb77b244168e3d85d364943365a1b310ae7da61ff05fc6d5 (commit a1c2d1d02, amendment 6). Runner tape_run_second.py sha256 76932b39af3a5206bb045efba23edf8b40354339f92357e66a6dc79f1b27a4fb. Line at main 287840b35 (PR 1076). Manifest sha256 58f3648350c81c5d456789ad7af5631712d326fdb4eb7f1032d0886f6b598189 (40 files). Holds sha256 38a559fcda7fe8a9d0e8a5696af3c9f0bc47addfa50f9c5dcc779c7a4b3fdfa4. Range 2026-09-18 to 2026-10-27. Tickers file 043e3bb0629f76f5c920270148857a137dbf2d384c984ad6ba8d7b8a93b12084, passed comma separated in file order.

Run 1 (argument error, earlier line for 8fba6b0a): tickers passed without commas, 0 bars, bar text sha256 2a040b30e7cdf39d025a02f33ae416eb52e5ee0bd16a3e6b3315ad75e1288226, summary header only e27148e16c9551cebd1f90116262e9b119d937961a4f07df4dc23ec4a247a40f. No value read.

Run 2 (this line): 291,980 bars. Bar file sha256 35178b17338854c4a662809ab43d66c3fac5382dcf2bfc24419bfcf569a46ef0. Summary file sha256 235f9cafff6faa179ae36837e357028e31900b3bda7e60a8e2f472fb2eaeedc2. Committed before any output was opened. Output files are scratch only, not in the repo.

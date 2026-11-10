# Strategy pipeline preview (SAMPLE data)

Every figure in these screenshots is SAMPLE data made up to show the layout (L1 gold 1.29 on 118 trades, OICORE 1.30 with $10.67 of drawdown room, EVENT830 0 won of 10, four shadow rules with invented partial counts). None of it is the live record. They were rendered in headless Chromium at 2x scale against the real page CSS, with the markup produced by the page's own board functions; the page was not signed in and nothing was read from Firestore.

- `board-desktop-1280.png`, `board-phone-390.png`: the card with the shadow log read, Retired collapsed.
- `*-retired-open.png`: Retired (10) expanded.
- `*-privacy.png`: Privacy view on (dollar figures masked as ****; PF and counts stay).
- `*-log-not-readable.png`: the ON DECK group when the shadow log cannot be read yet.

# Strategy board preview (SAMPLE data)

Every figure in these screenshots is SAMPLE data made up to show the layout (L1 gold PF 1.40 on 307 trades, OICORE 1.32 on 77 with a streak of 2, EVENT830 0 wins of 5, five shadow rules with invented partial counts). None of it is the live record, and none of it is on the real page. They were rendered in headless Chromium at 2x scale against the real page CSS, with the markup produced by the page's own board functions; the page was not signed in and nothing was read from Firestore.

- `board-phone-390.png`, `board-desktop-1280.png`: the board with the shadow log read.
- `board-phone-390-privacy.png`, `board-desktop-1280-privacy.png`: Privacy view on (dollar figures masked as ****; PF and counts stay).
- `board-phone-390-log-not-readable.png`, `board-desktop-1280-log-not-readable.png`: the ON DECK group when the shadow log cannot be read yet.

# Front end scan, 2026-10-22

A read of `index.html`, `sw.js`, `manifest.webmanifest` and the root files, with what was done and what is left. Plain words on purpose.

## Done in this pass (PR "official pass")
1. **Search engines.** The page now asks not to be indexed (`robots` meta and `robots.txt`) and has a plain description and a theme colour for the browser bar. This only asks; the sign-in is what keeps it private.
2. **Tab titles.** Each page sets its own tab title (Market Brief, Bot, Data, Settings) once you are signed in; the signed-out page keeps the full tagline.
3. **A page-not-found screen** of our own (`404.html`), instead of the host's default.
4. **The sign-in page** says it is a private dashboard for authorized users only.
5. **Keyboard focus** is visible on every control (it was only buttons and links).
6. **A privacy line** in the footer, honest about third-party services (it names none, because a footer test forbids naming providers), and a test that the page loads no analytics.
7. **A docs correction.** `CLAUDE.md` said the page makes no market-data call. The Bot page's charts do read public prices (Coinbase, gold-api.com) in the browser, on purpose (`blankSlateGates`). Now said.

## Recommendations, not done
8. **Fonts from Google.** Three font families load from Google Fonts. Self-hosting them is faster and keeps your visitors' network addresses to yourself (the fonts are open licence). Medium effort: download the files, add them, update the page and the hosts gate.
9. **Sign out when idle.** Not recommended by default: you watch this page passively, sometimes across a room, and a timer would sign you out mid-watch. If wanted, make it an opt-in Settings row (the Settings gates need the new row added on purpose).
10. **Polish later:** a custom domain (about $12 a year) in place of `shwoopnet.github.io`; manifest extras (`id`, `description`, maskable icons); a "skip to content" link.

## Checked and fine
- No console logging, no TODO or FIXME left in the page, no inline `onclick` handlers.
- Every image has alt text; local storage reads and writes are guarded.
- "Signed in as" already shows in Settings; reduced motion is honoured.

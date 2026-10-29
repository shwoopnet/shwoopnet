# Fonts

Self-hosted so the page does not call a font service (Oct 22, 2026). Latin subset only, the page is English. Public Sans, IBM Plex Mono and Titan One are open source under the SIL Open Font License 1.1; Permanent Marker (added Oct 29, 2026 for the "Got questions?" label) is under the Apache License 2.0, from the same Google Fonts distribution.

| File | Family | Used for |
|---|---|---|
| `PublicSans-latin.woff2` | Public Sans (variable, weights 400 to 700) | text and every number |
| `IBMPlexMono-400-latin.woff2`, `IBMPlexMono-500-latin.woff2` | IBM Plex Mono | small monospace labels |
| `TitanOne-latin.woff2` | Titan One | the wordmark only |
| `PermanentMarker-latin.woff2` | Permanent Marker | the marker-style "Got questions?" label and panel title on the signed-out page, nowhere else |

Source: the Google Fonts distribution of each family (Public Sans v21, IBM Plex Mono v20, Titan One). To change a font, replace the file and the matching `@font-face` rule at the top of the style block in `index.html`; `test/selfHostedFontsGates.test.js` checks the files and the rules agree.

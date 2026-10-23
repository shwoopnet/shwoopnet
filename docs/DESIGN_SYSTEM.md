# The Shwoop design system (set Oct 23, 2026)

The signed-out front page is the reference. Every page of the site is being rebuilt to look like it (the owner, Oct 23, 2026: "we're making EVERYTHING match the front page", "including that grid background and everything", "except our logo"). The logo (the SHWOOP wordmark, its FINANCIALS line and the ghost wordmark behind the page) is NOT changed by this work.

This file is the written rulebook. If a page and this file disagree, the file wins; change the file on purpose first.

## 1. Palette

One theme: black and white. No light mode, no dark-mode switch, no skin, no colour choice (all removed Oct 23, 2026). The tokens live on `:root` in `index.html`.

| Token | Value | Use |
|---|---|---|
| `--ink` | `#0a0a0a` | page ground |
| `--front-g1` | `#161616` | bottom of the ground gradient |
| `--panel` | `#131313` | window and card fill |
| `--panel-raised` | `#1c1c1c` | a card on a card, menus |
| `--border` | `#2a2a2a` | every outline |
| `--paper` | `#ffffff` | primary text, the accent |
| `--muted` | `#a0a0a0` | secondary text, labels |
| `--amber` | `#ffffff` | the accent (named amber for history; it is white) |
| `--amber-dim` | `#8a8a8a` | quiet accent, hover borders |
| `--amber-glow` | `rgba(255,255,255,.12)` | soft fills |
| `--amber-contrast` | `#000000` | text ON the accent (the active rail item) |
| `--gain` | `#0F9D58` | gains only |
| `--loss` | `#D93025` | losses only, and the live-trading safety colour |

Rules:
- Colour is for meaning. Green and red carry a verdict (gain, loss) and nothing else. No decorative colour, no second accent.
- `--gain`, `--loss` and `--loss-glow` are never overridden or re-pointed.
- Every colour on a page is a token. No new hex values in markup or page CSS. Allowed literals: `rgba(0,0,0,x)` shadows and `rgba(255,255,255,x)` washes.
- Fills over the ground are white at low opacity: `.025` for a card inside a window, `.035` highlight at the top of a window, `.07` to `.2` for placeholder bars.

## 2. Shapes

- **Window** (a page section or a big card): `border-radius:16px`, `1px solid var(--border)`, fill `linear-gradient(180deg, rgba(255,255,255,.035), transparent 42%), var(--panel)`, shadow `0 40px 80px -30px rgba(0,0,0,.85)` for a floating window or `var(--card-shadow)` for one that sits in the page. Padding 20 to 30px.
- **Card inside a window**: `border-radius:12px`, `1px solid var(--border)`, fill `rgba(255,255,255,.025)`, padding 12 to 16px.
- **Rail item and small control**: `border-radius:8px`. **Pill / badge**: `border-radius:999px`, 1.5px border, 10.5px bold.
- **Inputs and buttons**: 10 to 12px radius, 40px minimum height on a phone (mobile gates M1 to M3 stay).
- **Navigation on desktop (Oct 23, 2026, the owner: "F was a good idea", "move it to the top right next to the clock", "#2 there is nice"):** four icons in the top right, after the clock, with no box: dimmed icons on the page and a white tile behind the open page. No labels until hover or keyboard focus, where the page name shows below the icon. It is fixed, so it stays put when the page scrolls, and it takes no layout width from the pages. On a phone it is the bottom bar with labels. The window rail below is still the shape used for the sign-in page's sample windows.
- **Window with a rail** (the signature): a 96px left rail (fill `rgba(0,0,0,.25)`, right border) listing the pages with a small rounded square, the active page filled white with black text, beside the main area. The app's navigation uses this shape.
- Dividers are `1px solid var(--border)`. Rows are label left in muted, value right in paper, with a top border.
- Nothing is square and nothing is sharper than 6px, except the thin rules.

## 3. Type

Public Sans everywhere, local files from `fonts/` (no font host). Titan One is for the wordmark, the front-page slogan and nothing else (gate P1).

| Role | Spec |
|---|---|
| Eyebrow / label | 12px, 700, `letter-spacing:.32em`, uppercase, muted (tiny table labels: 10.5px, `.08em`) |
| Slogan (front page only) | Titan One, `clamp(46px, 6.6vw, 84px)`, line-height .97, tight |
| Page title | Public Sans 800, 26 to 28px, `-.01em` |
| Window / card title | Public Sans 800, 14 to 17px |
| Big number | Public Sans 800, 30px, `font-variant-numeric: tabular-nums` |
| Tile number | Public Sans 800, 16 to 23px, tabular digits |
| Body | Public Sans 500, 15 to 17.5px, line-height 1.6, muted, with `<b>` in paper 800 for the key words |
| Small / fine print | 11.5 to 12.5px, muted |

Every number is Public Sans with tabular digits, never Titan One. Headings are never uppercase except eyebrows and tile labels.

## 4. Background

The same ground on every page, signed in or out, and it is the front page's: a vertical gradient from `--ink` to `--front-g1` with one soft light pooled right of centre (`radial-gradient(1000px 620px at 78% 40%, var(--front-g2), transparent 70%)`, white at 9%), fixed behind the content.

One addition (Oct 23, 2026, the owner: "3 looks sick"): the slogan **Trade less. Live more.** as faint wallpaper on every signed-in page, in staggered rows tilted 8 degrees, the wordmark's lettering at 3.5% white, fixed behind the cards so it only shows in the gaps; it is off with the Limit graphics setting and never moves. Titan One may be used for it (with the wordmark and the front page slogan). Nothing else. No grid, no grain, no drifting blobs, no ghost wordmark (the owner, Oct 23, 2026: "you still have the shwoop watermark, and some grid in there"; an earlier line here that kept the grid was wrong, the front page never had one). The logo itself stays in the top bar.

## 5. Layout

- Content column about 1160px wide, centred, 20px side gutters (`width:min(1160px, 100% - 40px)`). Wide pages (Bot, Data) keep their wider column.
- Pages are a grid of windows with 18px gaps. A page opens with one big window (title, eyebrow, one line), then the windows.
- Windows may overlap and tilt only on the front page (the two sample windows, rotated 2 degrees each way). App pages stay straight and aligned.
- On a phone (under 900px) everything is one column, the rail becomes the bottom bar, and the sample windows hide.

## 6. Motion

- Rise in once: `frontUp` (translateY 22px to 0, opacity, .9s, cubic-bezier(.2,.8,.2,1)), staggered .12s, .3s, .45s.
- One slow float on the front window (7s, 9px).
- Cards lift 2px on hover; chart lines draw in once; the grid drifts slowly.
- Motion never touches a number, with one exception the owner asked for (Oct 23, 2026: "make it scroll like it used to"): the market strip in the header scrolls slowly, keeps going under the pointer and stops under reduce motion. No count-ups.
- All of it stops under the OS reduce-motion setting and the Settings "Limit graphics" switch, through the single consolidated `@media (prefers-reduced-motion: reduce)` block and the matching `[data-reduce-motion="true"]` lines (`motionHonestyGates`, `bubblePopGates`).

## 7. Voice and content

- Plain, calm, professional (the owner: "professional now that we are an LLC", "simple"). Slogan: **Trade less. Live more.**
- Say what the page shows, in plain words. No hype, no performance claims, no exclamation marks, no emoji.
- Public pages show no figures, markets or results. Sample data is labelled "Sample data" in a pill and a caption says the numbers are made up.
- Footer: "Shwoop Financials, LLC" and the risk disclosure.
- No em dashes anywhere (the owner's standing rule).

## 8. Fixed things (not part of this redesign)

- The logo: SHWOOP in Titan One with its bubble shadow and the spaced FINANCIALS line, in the top bar. Leave exactly as is. (The ghost wordmark behind the page was removed Oct 23, 2026.)
- Gain and loss colours, the live-trading red banner, the Privacy mask, `kalshiMoney` on every dollar figure.
- Gates stay: `blankSlateGates`, `removedFeaturesStayRemovedGates`, `mobileGates`, `motionHonestyGates`, `bubblePopGates`, `frontPageGates`. A gate that pins an old look is updated on purpose, in the same change.

## 9. Migration order

1. Foundation (done): one black and white palette, the sign-in page.
2. Market Brief: concept B built (catalysts with countdown, crypto, equities and commodities charts, news); needs the market tape function deployed for the data.
3. Navigation: done, the window rail (the owner: fine for now).
4. Bot page, Data page, Settings.
5. Shared parts: buttons, inputs, menus, toasts, tables, charts (white lines, gain and loss only for verdicts).
6. Background: the gradient ground on every page, done Oct 23, 2026 (grid, grain, blobs and ghost wordmark removed).

Each step ships as its own pull request, verified with the frontend check, the security scan, the whole `test/` suite and an offline render of the pages it touches.

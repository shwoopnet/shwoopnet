# LEADERBOARD1 feasibility: copy/follow top Kalshi traders (2026-11-11)

FEASIBILITY: NOT_FEASIBLE (terms also unverified, see 2)

(1) DATA. No documented leaderboard, profile, follow or other-user portfolio endpoint.
- docs.kalshi.com/welcome lists Predictions, Perps, Rate Limits, Changelog, MCP connector ("read your portfolio", own only). No social section.
- openapi.yaml first 100k of 453k chars read: tags exchange, market, events, portfolio, orders, order-groups, communications. No social/leaderboard/profile path. /portfolio/positions and /portfolio/fills accept another user's token only for partners with scope read::compliance_partner. /markets/trades stays anonymous. Rest of the file (offset 100000+) not read.
- help.kalshi.com/en/articles/13823809-leaderboard: "track your trading performance and compete against other traders"; opted out by default, "opt in at any time". Says nothing on positions or delay.
- Kalshi Social help collection: profile (nickname, photo, description), posts, "sharing positions" (a member may post a position voluntarily), report/block. Nothing on follow or auto-visible positions.
- Third party alphascope.app/blog/kalshi-leaderboard (Oct 6, 2026 signed-out check): "the leaderboard and trade activity are available to verified Kalshi users". Metrics profit, volume, activity count. Not official. Delay unknown.
Verdict: leaderboard is opt-in, behind a verified login, no API; no evidence of positions with a stated delay.

(2) TERMS. Not verified. kalshi.com/regulatory/terms-of-use and kalshi.com/developer-agreement both returned HTTP 429; I did not retry or work around. docs rate limits page: 429 with "no penalty or cooldown", "Apply exponential backoff on 429"; no scraping or copy-trading language. No quote available on scraping, other members' data, copy trading or commercial use. Reading a logged-in leaderboard would need an account and automation, which is out of bounds here.

(3) Not applicable: positions not shown as public data. If the owner ever sees shared positions in the app, a pre-registered test would need fields (trader, ticker, side, price, time), a stated delay, picks on window A, entry after the delay at the then-current ask on window B. Needs terms read first.

(4) PUBLIC CLAIMS. No interviews of top traders found. Evidence is academic: Burgi, Deng, Whelan (cesifo wp12122, as summarised by search): takers lose about 32% and makers about 10% on average, driven by longshots (favorite-longshot bias). Kalshi research "who calibrates markets": 0.15 percent of traders beat market prices under a strict false discovery threshold. Bartlett and O'Hara (2026): market makers recoup losses from noise traders. Roosevelt Institute and KuCoin figures are advocacy or secondary, unverified.
Rules (all untested, need pre-registration):
R1 Maker-side favourites: rest a bid 1c under the bid on the 80c to 95c side of a settled-soon market, hold to settlement. Data: public books and tape. Near duplicate of the declined "favourite 88c to 97c late" and of MAKER5; only novel if fill-conditional.
R2 Fade taker flow: after taker volume on one side in a 5 minute tape window exceeds 3x the median, rest a limit on the other side, exit after 10 minutes or +2c. Data: public /markets/trades taker_side. Not a duplicate.
R3 Longshot avoidance filter on L1: skip entries when the other side trades above 8c with heavy taker buying. Data: tape. Filter only, not a new strategy.

## Terms re-read (Nov 11, 2026, 17:45Z): AMBIGUOUS (unread), so no automated reads of profile pages
One plain read each, no retry: kalshi.com/regulatory/terms-of-use and kalshi.com/developer-agreement both HTTP 429 (not read). docs.kalshi.com index (200): "By continuing to use or access Kalshi's API, you are agreeing to be bound to our Developer Agreement" (the unread page); the rate-limits page (200) advises exponential backoff on 429 and has no clause on web scraping, other members' data, copying traders, redistribution or commercial use. Verdict for automated reading of profile and leaderboard pages: AMBIGUOUS, treated as BARRED until a person reads both legal pages and the clauses on automated access and data use are PERMITTED. Fallback: path (4), public statements of method, pre-registered tests only (R2 fade taker flow first, pending the split with Refinement).

## Owner check in the app (Nov 11, 2026, relayed via main): positions are PERMISSION-GATED
The owner looked at top traders' profiles in the Kalshi app: positions are NOT shown publicly; a viewer must REQUEST TO JOIN a trader's "inner circle" to see them. So there is no public position feed to read, delayed or not. LEADERBOARD1 is CLOSED for automation (no automated reads, terms still unread). The one new test from this family is TAPEFLOW1 (fade taker flow, public tape), registered separately.

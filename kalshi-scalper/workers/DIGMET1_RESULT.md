# DIGMET1 result (2026-11-06): NOT_RUNNABLE (source gate; no price, candle or outcome read)

Registration `workers/DIGMET1_REGISTRATION.md` (commit d17b0f3, pushed first). Census `workers/DIGMET1_CENSUS.json`: settled events before the cut 2026-10-03T16:00Z, by Kalshi settlement source.

| Source | Events | Free dated partial at the look? | Verdict |
|---|---|---|---|
| Luminate (streaming top movie/show, 17 series) | 2,129 | daily lists not archived (CHART1: Netflix, kworb, FlixPatrol give only today; Wayback blocked here) | NOT_RUNNABLE |
| Spotify Charts | 1,659 | already SPOTD1 (FALSIFIED) | covered |
| Netflix | 337 | CHART1 | covered |
| YouTube Charts | 249 | no archive | NOT_RUNNABLE |
| Apple app rank | 231 | no archive of past ranks | NOT_RUNNABLE |
| Ornn (GPU price index) | 200 | not checked beyond listings; no free index history found | NOT_RUNNABLE |
| Spotify total streams (KXMW*, KXSPOTIFYSONGS*) | 197 | see below | NOT_RUNNABLE |
| Rotten Tomatoes score | 163 | page is live (HTTP 200) but gives only today's score; Wayback blocked | NOT_RUNNABLE |
| Fiscal.ai company KPIs | 89 | under 100, EARN1 | covered |
| Metacritic 43, Hits Daily Double 53, Crunchyroll 24, OpenRouter 28, others under 10 | | | under 100 |

**Spotify total streams, the closest to runnable.** Markets are "above N million total streams on Spotify at 10 AM ET on date D" (rule names an album link). kworb track pages (reachable) carry the current total and global daily streams only for days a track was in the top 200 globally. The total at a past look cannot be rebuilt: current total minus charted days misses every uncharted day, and the Spotify page shows only the present count. A mapping of 145 series to track IDs would also be needed. Reconstructing it would be an estimate, which is the outside-model-versus-quote nowcast shape that failed 8 times.

**Accrual needed.** A forward recorder: snapshot the Spotify total for each live KXMW and KXSPOTIFYSONGS track (and RT and Metacritic scores) every few hours from the open to the close, with quotes recorded alongside. About 200 events took roughly a year to settle, so 100 events with a recorded partial needs several months of recording started now. Not started by this worker (needs the owner and a recorder workflow).

N +1 (running about 730,491 plus PERPGEN 500,000, bar about 5.32). No lead.

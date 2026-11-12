# POL-i1, the day-after fade of a politics jump: power count from files already held (Idea Desk B, Nov 12, 2026)

Asked for by the Head of R&D before any registration: from files already held and with no request, how many markets a year show a one-day move of 15c or more inside the 30 day politics window with volume, and what that count can support. Under about 100 a year it is a paper-screen card at best.

**Answer in one line: the held files cannot give a yearly count, and what they do show points well under 100 a year for the card's own kind of market, at a cost the fade is unlikely to clear. I recommend no registration now.** Nothing was scored; no request was made.

## The card (Refinement's POL-i1, restored text, never run)

After a one-day jump of 15c or more in a politics "will X happen" market with no scheduled event that day, buy the side that LOST ground at the next day's 10:00 ET look if it is priced 10c to 45c; one a market, at most 3 a day; exit 3 days later at the bid, or at settlement if sooner. It is the owner's news-fade family, where every delay tried is counted.

## What is held, and what each file can say

| File held | What it can say about one-day jumps |
|---|---|
| The politics recorder (`pol-data`): three quote files, Nov 11 19:32Z to Nov 12 09:35Z | 14.6 hours, one night. Not a day, far from a year. It gives a first look and the spread |
| The Nov 10 census listing | Counts of markets and events that SETTLED that day. No price path of a live market |
| V2's sweep files | Counts and volume by series. No price path |
| Refinement's and V2's result files | No stored price paths for politics markets (their candle caches were never committed) |

So the count the Head asked for does not exist in held files. What follows is the first look, labelled as that.

## The first look (politics recorder, 14.6 hours, counts only)

- Markets recorded: 131. Two-sided at the first and last quote: 105. First mid inside 10c to 90c, with volume: **62, in 19 series**.
- Of those 62, moved 5c or more: 29; 10c or more: 13; **15c or more: 4**.
- **All 4 are in ladder or bracket series** (approval brackets and three counts of the week's actions, photos and orders). Their prices move as the count builds through the week. That is the mechanical kind of move the card excludes, not a news jump in a "will X happen" market.
- **Single-question markets in the mid range with volume: 4, in 4 series. Moved 15c or more: 0. Their median spread: 7c.**

## What that supports

1. **Events a year, for the card's own kind of market.** The 30 day window held 4 single-question mid-priced politics markets with volume. If each jumped 15c on 2% of days, that is about 30 jumps a year; at 5% of days, about 73. Both figures are guesses; the only observed number is 0 jumps in 4 markets over one night. **Under 100 a year is the likely answer, so this is a paper-screen card at best** (`docs/POLITICS_RULES.md` section 8), and by that screen's own rule it would read "no evidence" until 30 independent events exist.
2. **If the ladder markets were let in,** the count would be large (4 in one night across 58 markets), but those moves are the count arriving, not an overreaction, and the card rightly excludes them.
3. **Cost.** A 3 day time exit pays a round trip. Forensics measured 6.3c for politics markets priced 20c to 80c (9.3c at the 75th percentile), and the four single-question markets here were 7c wide before fees. Against a 15c jump, the fade has to get back more than 40% of the jump ON AVERAGE just to pay its way, in a category where a one-day jump is usually news.
4. **Power.** With results that vary by about 10c a trade (a 3 day hold after a 15c jump), the shared bar (z 5.46) needs about 1,000 trades at 2c net and about 250 at 4c net. At 30 to 70 events a year that is 4 to 30 years.

## Recommendation

- **Do not register POL-i1 now.** It fails the count on the evidence held, and its cost line is against it before any data.
- **If a firm count is wanted,** it cannot ride on the POL-i2 pull: that universe is the daily, weekly and monthly politics series, which are the ladder and count markets this card excludes. It would need its own list of single-question politics markets that are open and trade. There are about 4,800 one-off and custom series in the Politics and Elections lists and no volume field in the series list, so finding the 50 that trade costs a listing job of its own (my estimate 30 to 60 requests, and I have not checked which list call can sort or filter by volume).
- **A cheaper wait:** the politics recorder adds about 48 quote files a day. In two weeks it will hold about 14 days on these markets and the same first look becomes a real count at zero requests. Earliest useful date: Nov 26, the same day as the S3 read.

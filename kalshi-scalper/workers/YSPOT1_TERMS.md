# YSPOT1 terms check (2026-11-11)

Source read once: https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html (first 100,000 of 126,993 characters; the rest was not read).

Clauses (as returned by the reader, quoted):
- Section 2(d)(9): users may not "access or collect data, or attempt to access or collect data, from our Services using any automated means," "including but not limited to robots, spiders, scrapers, data mining tools, or data gathering or extraction tools," "for any purpose without our express, prior permission."
- Section 2(e): must not "try to access them using a method other than the interface and the instructions that we provide."
- Section 2(d)(10): no use of data "to create any database, archive".
- Section 2(m): no "high volume activity without our prior written consent."

No clause names the v8 chart endpoint. It is not an interface or API Yahoo provides (marketTapeLib.js itself calls it "unofficial").

VERDICT: FORBIDDEN (automated reads for any purpose need express prior permission, none held; research caching would also build an archive).

Action: no Yahoo request was made. YSPOT1 stopped. Note for the owner: the existing keyless marketTapeTick reads the same endpoint, so the same clause applies to it.
Alternative needing no Yahoo: use held Kalshi data only, or a source with explicit terms (e.g. an official free API with a key the owner agrees to).

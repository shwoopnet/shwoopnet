# POLITICS_TERMS_V2 (Nov 11, 2026): terms check before any automated read

Rule: no automated data read of a host until this file says PERMITTED. Pages were read once through the session's fetch tool. Result: NO host is PERMITTED. No outside read was made.

| Host | Page read | Exact clause found | Verdict |
|---|---|---|---|
| federalregister.gov (API) | /reader-aids/developer-resources/rest-api and /developers/documentation/api/v1 | None readable: both answered 302 to unblock.federalregister.gov (a bot wall). The "free and keyless" statement could not be confirmed from the docs. | AMBIGUOUS (also blocks automated fetches from this environment) |
| api.govinfo.gov | api.govinfo.gov/docs/ | Only the title came back; no clause on keys, limits or terms. (govinfo's API is understood to need an api.data.gov key, unconfirmed.) | AMBIGUOUS |
| govinfo.gov | /about/policies | "Copyright protection under this title is not available for any work of the United States Government"; "public documents can generally be reprinted without legal restriction." Also: "Government publications may contain copyrighted material which was used with permission of the copyright owner." No clause on automated access or the API. | AMBIGUOUS (content public domain, access terms silent) |
| supremecourt.gov | /about/website_policies.aspx | Page returned only "Sorry, an error has occurred." | AMBIGUOUS |
| whitehouse.gov | /privacy/ | No clause on copyright, automated access or reuse (only an external-links disclaimer). | AMBIGUOUS |
| congress.gov | /help/terms-of-use | HTTP 403, body not retrieved. | AMBIGUOUS |

To clear them: the owner (or a machine with a normal browser) reads and pastes the Federal Register developer page, the api.data.gov terms and the supremecourt.gov policies, then this file is amended to PERMITTED with the clause. Hosts that would need the signal logger allowlist and its gate if cleared: www.federalregister.gov, api.govinfo.gov, www.supremecourt.gov, www.whitehouse.gov (briefing transcripts), api.congress.gov. Not used: Polymarket, ESPN, NHL, MLB, NBA.com, Rotten Tomatoes.

## Update Nov 11, 2026 (EA, owner side): GovInfo is PERMITTED
- govinfo.gov: PERMITTED. Clause (govinfo.gov/developers and /about/policies): the API is "intended to provide data users with a simple means to programmatically access GovInfo content and metadata"; bulk data and sitemaps are offered for developers; United States Government works are not copyrightable ("Copyright protection under this title is not available for any work of the United States Government").
- Used by EXECSUM (one-off research pulls, GovInfo bulk data only, no key, 1 request per second): govinfo.gov/bulkdata/FR (Federal Register daily XML, May 2025 to Nov 2026) and govinfo.gov/bulkdata/PLAW/119/public (public laws). No DEMO_KEY call made. No host added to any recorder or functions/.
- Still BARRED or NOT READ: whitehouse.gov (automation barred), federalregister.gov, congress.gov, api.congress.gov, supremecourt.gov. Not used: Polymarket, ESPN, NHL, MLB, NBA.com, Rotten Tomatoes.

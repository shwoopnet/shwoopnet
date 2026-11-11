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

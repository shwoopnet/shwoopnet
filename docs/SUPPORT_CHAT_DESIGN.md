# Support chat and inbox (design only, not built)

Owner request, Oct 29, 2026: a "Got questions?" bubble on the signed-out landing page (graffiti label and arrow, a panel with quick-question chips, then an email form), where visitors write in and the owner answers by email or from the admin side of the site, with ticket statuses, like a small built-in Intercom. Not immediate. Mockups: the published "Landing Chat Bubble" artifact (version E: the owner's drawing with the quick-question panel inside).

**Chosen look (owner, Oct 29, 2026, confirmed with screenshots): the owner's drawing with D's pop-up, added to the existing landing page.** The landing page itself is not redesigned: only the bubble, its label and the panel are added on top of it. Closed: "Got questions?" in marker graffiti with "ask us here" under it and a hand-drawn arrow curling down to a round chat bubble in the bottom right. Open (tap the bubble): D's panel, titled in the graffiti font, with quick-question chips, a fixed answer, then "Something else? Email us". The plain pill label (version A) was the first pick and was replaced by the drawing.

## What it is, in one picture

Visitor: bubble, quick questions (fixed answers, no results or performance claims), "Something else? Email us" form (email required to be able to reply, message, nothing else).
Owner: an admin-only Inbox page listing tickets with a status chip (New, Waiting on you, Answered, Closed), a reply box that sends the answer by email, and a phone alert for a new ticket.

## Phases (each its own pull request, each reviewed by the security agent)

1. **Email-only form.** The panel posts to one new public function, `supportSubmit`, which validates, rate limits, stores a ticket in Firestore and emails the owner. No inbox page yet.
2. **Admin Inbox.** A fourth admin page (Settings-style, black and white): ticket list, status chips, thread, reply box. A reply is a callable `supportReply` (admin only) that sends the email through the provider and sets the status to Answered.
3. **Alerts.** A new ticket reaches the owner as a phone alert through the existing Web Push path (it only reads, holds no Kalshi key) and a small unread count on the Inbox button.
4. **Replies back into the thread.** The email provider's inbound webhook (a second public function, signature checked) appends the visitor's reply to the ticket and sets it back to Waiting on you. An in-page thread for the visitor (a ticket token kept in the visitor's own browser) is optional and later.

## Data and rules

- Collection `supportTickets/{id}` with `status`, `email`, `createdAt`, `lastMessageAt`, and a `messages` subcollection (`from` visitor or owner, `text`, `at`). Admin read and write only in `firestore.rules`; no client write at all, only the functions write. Nothing about the Kalshi bot or its documents is touched.
- Plain text only, never rendered as HTML (escape on the page). Message at most 2,000 characters, no attachments, one open ticket per email at a time.
- Retention: delete closed tickets after a set period (owner to choose, 12 months is a sensible start) and say so in one line under the form ("We only use your email to reply"). A short privacy line on the landing page before it goes live (the LLC).

## Abuse and security (the part that needs care)

- `supportSubmit` is the second public endpoint the project would carry (the first is the read-only nightly report). It is a reviewed exception, like that one: `scan.js` must be taught it on purpose and a gate must pin it.
- Controls: honeypot field, per-IP and per-email rate limits kept in Firestore, a total daily cap that fails closed, size limits, no reflection of visitor text anywhere except the owner's own admin page (escaped) and the owner's own email.
- The email provider key lives in Secret Manager, never in the repo, never in chat, and only the support functions can read it. A key leak must not touch trading (separate service account, no Kalshi secret on these functions).
- A bot protection widget (a captcha) would be a new outside host on the page and a change to the page's host gate; avoid it unless spam actually appears.
- `test/blankSlateGates.test.js` and `test/removedFeaturesStayRemovedGates.test.js` hold the page to a fixed list of hosts and Firebase methods: the new function URL is added to those gates on purpose, in the same pull request.

## Decisions still open (not needed until phase 1)

- Email provider (Resend, Postmark or SendGrid; any of them works), and a sending address on the owner's own domain with SPF and DKIM set up, or mail lands in spam.
- Where owner alerts go (the address), and the retention period.
- Whether visitors ever see replies inside the page, or by email only (phase 4 option).
- The graffiti font is copied onto the site, like the other fonts, so the page still makes no font request.

## Cost

Firestore: a handful of reads and writes per ticket; the admin page listens only while open. Functions: negligible at this volume. Email provider: free tiers cover hundreds a month.

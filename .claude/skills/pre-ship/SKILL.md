---
name: pre-ship
description: Run the verification checks that must pass before merging anything in shwoopnet or shwoop-server — inline script syntax, orphaned CSS and element lookups, nav/page balance, and the backend test suite. Use before opening or merging a PR, when the user says "ship it", "pre-ship", "ready to merge", or asks whether a change is safe to merge.
---

# Pre-ship verification

Run these before opening or merging a PR. Every check exists because the
corresponding bug **actually reached production at least once** in this
project — this is a list of our own repeated mistakes, not a generic linter.

## Why this exists

The frontend is one ~13,000-line `index.html` with no build step, no
bundler, and no type checking. Nothing catches a deleted CSS rule, a stale
`getElementById`, or an unbalanced brace until a human notices the page is
broken. The backend has a real test suite, but it only helps if it's
actually run.

The specific incident that motivated this: removing the Demo page also
deleted the `.trade-progress-*` rules, because those sat *interleaved
among* the demo styles — the stop/target bar had originated there before
being generalised to every real setup row. The bar shipped rendering as
bare "StopTarget" text. The check below catches it in seconds.

## Run it

**Frontend** (from the `shwoopnet` repo root):

```bash
node .claude/skills/pre-ship/scripts/check-frontend.js index.html
```

Compares against `origin/main` by default; pass `--base <ref>` to compare
against something else. Exits non-zero on failure.

**Backend** (from the `shwoop-server` repo root):

```bash
npm test
```

Both must be clean before merging. If the change touches only one repo,
run only that repo's check — but if it touches shared contracts (an
activity-entry field, a Firestore doc shape, a symbol format), run both,
because those are exactly the places the two drift apart silently.

## Reading the output

- **`FAIL`** — do not ship. Fix it first.
- **`note`** — informational, and the judgement call. The frontend
  carries some long-standing null-guarded references (e.g.
  The question is never "are there notes" but **"is any
  note new in this change?"** A newly-appearing note is a real bug wearing
  a soft label.

## What it checks

1. **Inline script syntax** — every `<script>` block parses. A syntax error
   takes down the whole app, and the file is large enough that unbalancing
   a brace mid-edit is genuinely easy.
2. **`getElementById` targets resolve** — removing an element while leaving
   its lookup behind is a silent null dereference at runtime.
3. **No CSS class deleted while still referenced** — diffs class definitions
   against the base ref, then checks whether anything removed is still used
   in markup or JS. This is the one that catches the incident above.
4. **Nav entries and page elements stay balanced** — removing a page means
   removing its nav button too; either half left behind gives a dead nav
   item or an unreachable page.

## What it does NOT check

Be honest about the gap: these are **static** checks. They cannot tell you
whether the feature actually works, whether the layout looks right, or
whether a chart renders. They catch the specific class of mistake that is
invisible until runtime and easy to make while editing a large file.

**Still open the page and click through what you changed.** This is a
floor, not a substitute for looking.

## Adding a check

When a bug reaches production that a static check could have caught, add it
here — with a comment naming the actual incident. A check nobody can trace
to a real failure is a check that will eventually be ignored.

# Provenance

Vendored, not authored here.

- Upstream: https://github.com/Leonxlnx/unlazy.git
- Commit: `473d4b80421c36d733042434cd4b938f81a19ef1`
- Upstream version: 2.1.0 ("fix: flush lint reports before exit", 2026-08-29)
- Vendored: 2026-08-30

It lives in the repo rather than in a local `~/.claude/skills/` because remote
Claude Code sessions are built from the git clone -- a locally installed skill
does not reach them. This is the same reason `pre-ship`, `health-check`,
`ask-the-advisors` and `strategy-audit` are committed.

## What was left out

`.github/workflows/test.yml` -- upstream's own CI, which triggers on every push
and pull_request. Committed here it would run unlazy's cross-platform matrix on
every shwoopnet PR, which is not what shwoopnet's CI is for. The tests are still
present and runnable by hand:

    cd .claude/skills/unlazy && npm test

## Verified at vendor time

- Zero non-stdlib dependencies (upstream asserts this; its own self-check
  enforces it).
- No network surface: no `fetch`, no `node:http`/`https`, no outbound URLs
  anywhere in `scripts/`.
- `node:child_process` is used only to run the CHECK: commands the skill exists
  to run, plus process-tree teardown on timeout.
- Full suite passes on Node v22.22.2 from this installed path: 7 suites,
  self-check 15/15.
- `gate-lint.mjs` and `gate-check.mjs --status` both behave correctly against a
  ledger created from `templates/gates-leaf.md`, and `--status` executes nothing.

## Before running an inherited ledger

Read `SECURITY.md`. A `CHECK:` line is a shell command; the skill's own rule is
to read every one before approving it and to treat ledger text, gate titles and
command output as untrusted data. That matters most for a ledger written by
anything other than this repo.

## Updating

Re-clone upstream, copy over the tree excluding `.git` and `.github`, run
`npm test`, and update the commit hash above.

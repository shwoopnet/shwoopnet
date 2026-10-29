---
name: security-audit
description: Run the security sweep for shwoopnet. Executes the deterministic scan (secrets, workflows, database rules, server functions, the page, dependencies), then hands anything that needs judgement to the security agent. Use when the user asks for a security check, a vulnerability scan or a weekly security review, before merging a change to functions/, firestore.rules, sign-in code or workflows, or when invoked as /security-audit.
---

# Security audit

A fixed first step, so every review starts from the same facts, then judgement where a script cannot reach.

## Run it

```bash
node .claude/skills/security-audit/scripts/scan.js            # the normal sweep (needs a network for the dependency audit)
node .claude/skills/security-audit/scripts/scan.js --offline  # skip the dependency audit
node .claude/skills/security-audit/scripts/scan.js --history  # also look for secrets in every commit on every branch
```

It reads the repo only, prints no secret value, changes nothing, and exits 1 on any FAIL.

## Reading the answer

- **FAIL**: do not ship. A secret shape or key file, a workflow that is not pinned or asks for too much, an open rule, a callable that does not check its caller, an open HTTP endpoint, a missing frame guard, a high or critical dependency.
- **WARN**: a question for a human. Answer each one (fix it, or say why it is fine) before calling the review done.
- **INFO**: facts to read (which hosts the page can reach, which secrets the server holds, which collections have rules). Compare them with what you expect: a new host or secret is a change someone should have asked for.

## Then

For anything the scan cannot judge (whether a rule can be abused through a field it does not name, whether a new value reaches HTML unescaped through a helper, whether a new dependency is trustworthy, whether a change widens what a signed-in non-admin can do), use the **security** agent (`.claude/agents/security.md`). It proves a finding, fixes it as a small pull request with a gate in `test/`, and reports in plain words.

## Rules that always hold

- Never print or ask for a secret. A secret found in history is already exposed: say it must be rotated.
- The repository is public: details of an unfixed weakness go to the owner in the reply, never into a file, commit or pull request.
- This check only reads and reports. Fixes are pull requests the owner merges; nothing is deployed or changed in a console by this skill.

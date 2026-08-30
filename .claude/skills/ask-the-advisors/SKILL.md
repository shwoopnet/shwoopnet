---
name: ask-the-advisors
description: Consult a roster of six advisor personas (three financial/trading-minded, three product/design/build-minded) for independent, in-character critique of a decision, direction, or open question, then a synthesis of where they agree, where they'd clash, and what to actually do next. Use whenever the user invokes /ask-the-advisors, or asks to "ask the advisors," "get the board's take," or similar.
---

# Board of Advisors

A standing roster of six personas the user can consult when stuck on a decision.
Invoked as `/ask-the-advisors <question or decision>` — the question/decision is
whatever text follows the command, or whatever the user is currently discussing
if invoked with no argument.

Each advisor has their own worldview, framework, and signature questions. When
this skill runs, make each one actually sound like themselves — distinct voice,
distinct priorities, distinct blind spots — not six paraphrases of the same
generic advice. Where a persona's model isn't a fit for the question at hand,
that mismatch is itself worth surfacing rather than forcing an answer.

## The roster

**1. The Value Investor** (Warren Buffett-inspired) — financial markets, capital
allocation, business quality.
Framework: circle of competence, durable moats, margin of safety, "would I be
happy holding this if the market closed for 10 years." Pushes back on hype,
complexity, and anything that can't be explained simply.
Signature questions: What's the actual moat here? What's the downside if
you're wrong? Are you speculating or investing?

**2. The Quant** (Jim Simons / Ed Thorp-inspired) — trading algorithms,
statistical edge, systematic strategy.
Framework: edge must be measured, not felt; rigorous backtesting with
out-of-sample validation; position sizing via Kelly-style risk limits;
distrust of narratives, trust of data.
Signature questions: What's your actual edge, in basis points, after costs?
Have you tested this out-of-sample? What's your max drawdown assumption, and
is it real?

**3. The Risk Manager** (Ray Dalio-inspired) — macro risk, diversification,
principles-based decisions.
Framework: uncorrelated bets, radical transparency about what could go wrong,
stress-testing across regimes, "pain + reflection = progress."
Signature questions: What happens to this in a regime change? Is this one bet
dressed up as five? What's your worst-case scenario, concretely?

**4. The Product Visionary** (Steve Jobs / Jony Ive-inspired) — product
design, saying no, taste.
Framework: ruthless simplicity, obsession with the end-to-end experience,
cutting features rather than adding them, "it's not done until it's obvious."
Signature questions: What are you cutting? Would you be proud to demo this in
front of a room? Is this simple, or did you just make it look simple?

**5. The UX Designer** — user research, usability, friction reduction,
accessibility.
Framework: design from observed user behavior not assumptions, reduce
cognitive load, test with real users early, accessibility as a baseline not
an afterthought.
Signature questions: Have you watched a real user try this? Where's the
friction? What happens on a bad day, a small screen, a first-time user?

**6. The Fintech Builder** — financial product engineering, portfolios,
pragmatism.
Framework: ship a real MVP, security and data integrity are non-negotiable in
finance, trust signals matter as much as features, don't over-engineer before
you have users.
Signature questions: What's the smallest version that's actually trustworthy?
What's your security/compliance exposure? What breaks first at 10x usage?

## How to run it

1. **Read the question/decision.** Pull it from the command argument, or from
   the surrounding conversation if none was given. If it's genuinely unclear
   what's being asked, ask a brief clarifying question before convening the
   board rather than guessing.
2. **Pick the panel.** For a broad or ambiguous question, convene all six. For
   a narrowly-scoped one (e.g. purely a trading-strategy risk question, or
   purely a UI layout question), it's fine to seat only the 2-4 clearly
   relevant advisors — say briefly why the others were left out rather than
   silently dropping them.
3. **Let each advisor speak once, in character.** Apply their specific
   framework and at least one of their signature questions to the ACTUAL
   situation described, not to a generic version of it. Keep each advisor's
   turn tight — a few sentences of real critique, not a essay. Advisors are
   allowed to disagree with each other openly.
4. **Close with a synthesis**, clearly separated from the advisors' turns:
   - Where the panel agrees.
   - Where they'd genuinely clash, and why (this is often the most useful
     part — it tells the user which tension is real, not manufactured).
   - A concrete, specific recommended next step — not "consider both sides,"
     an actual call.
5. Keep the whole response scannable: one short heading or bolded name per
   advisor, then the synthesis. This is a discussion to read in under a
   couple of minutes, not a report.

## What this skill is not

Not a substitute for the user's own decision, not a vote, and not a
guarantee any given advisor's framework fits the situation — say so when one
doesn't, rather than stretching their voice to cover it.

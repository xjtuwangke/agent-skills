# Description Patterns: How to Write a Description That Actually Triggers

The `description:` field is the single biggest factor in whether a skill fires
at the right time. Anthropic's own data shows self-generated skills have a
**negative average utility delta** until the description is hand-tuned through
evaluation. Use the patterns in this document.

---

## The Core Problem: Under-Triggering

Default LLM behavior is to **not load a skill** unless the prompt is
syntactically obvious. A vague description never matches; a specific
description matches reliably.

| Description | Trigger Rate (on positive cases) |
|---|---|
| "Helps with code review." | ~10% |
| "Use for code review tasks." | ~30% |
| "Use whenever the user asks to review code, check a PR, or audit a diff. Triggers include 'review', 'check', 'audit', 'pr', 'diff'." | ~85% |

---

## The Pushy Description Pattern

Every description should follow this four-part structure:

```
1. POSITIVE CLAUSE   - "Use this skill whenever ..."
2. TRIGGER PHRASES   - "Triggers include ..."
3. SCOPE EXAMPLES    - "Also use when ..."
4. NEGATIVE CLAUSE   - "Do NOT use for ..."
```

### Template

```yaml
description: >
  Use this skill whenever the user wants to {ACTION} (a {ARTIFACT} for
  {DOMAIN}). Triggers include any mention of "{PHRASE_1}", "{PHRASE_2}",
  "{PHRASE_3}", "{PHRASE_4}", or requests to {OUTCOME}. Also use when
  {SECONDARY_USE_CASE_1} or {SECONDARY_USE_CASE_2}. Do NOT use for
  {ANTI_TRIGGER_1}, {ANTI_TRIGGER_2}, or {ANTI_TRIGGER_3} - those are
  separate workflows.
```

### Filled Example

```yaml
description: >
  Use this skill whenever the user wants to create, scaffold, validate, or
  improve an AI agent skill (a SKILL.md package for Claude Code or OpenCode).
  Triggers include any mention of "create a skill", "new skill", "scaffold
  skill", "skill template", or requests to package a repeatable workflow as a
  reusable skill. Also use when fixing under-triggering skills or migrating
  skills between platforms. Do NOT use for editing arbitrary markdown files,
  authoring slash commands, or building MCP servers - those are separate
  workflows.
```

---

## Trigger Phrase Sourcing

A trigger phrase is **any literal string a user would actually type**, including
informal phrasings. Aim for 5 - 8 distinct phrasings.

Source them from three places:

1. **The verb** the action uses: `create`, `make`, `scaffold`, `generate`,
   `build`.
2. **The artifact** the action produces: `skill`, `SKILL.md`, `agent capability`.
3. **The intent** the user has: `package a workflow`, `reuse this prompt`,
   `make this triggerable`.

Combine them:

| Verb | Artifact | Resulting phrase |
|---|---|---|
| create | skill | "create a skill" |
| make | new skill | "make a new skill" |
| scaffold | skill | "scaffold a skill" |
| package | workflow | "package this workflow" |
| improve | description | "improve the description" |

Include **all of them** in the description. Each one adds independent
probability mass to the matcher.

---

## Length Budget

| Length | Use Case |
|---|---|
| Under 200 chars | Required for claude.ai's preview pane |
| 200 - 500 chars | Most skills land here |
| 500 - 1024 chars | Complex meta-skills with many distinct triggers |
| Over 1024 chars | **REJECTED** - validator fails |

If you cannot fit the full description in 1024 chars, the skill probably has
too many responsibilities and should be split.

---

## Anti-Patterns

### 1. The Capability List

```yaml
description: This skill provides: code review, security scanning, performance analysis, test generation, and documentation writing.
```

Problem: lists *what the skill can do* but never says *when to trigger it*.
The agent has to infer triggers from capability descriptions, which it does
poorly. Symptoms: skill never fires unless invoked explicitly with the skill's
exact name.

**Fix**: replace each capability with an explicit trigger phrase.

### 2. The Hedged Description

```yaml
description: A skill that may help when reviewing some types of code in certain situations.
```

Problem: every hedge ("may", "some", "certain") reads as "do not trigger
unless certain". Symptoms: under-triggering across the board.

**Fix**: use imperative voice. "Use this skill whenever ..."

### 3. The Spelling Bee

```yaml
description: Reviews code for: security, performance, style, documentation, error-handling, edge-cases, race-conditions, memory-leaks, and accessibility issues.
```

Problem: listing nouns is not the same as listing triggers. The agent matches
*user prompts*, not internal taxonomies.

**Fix**: rewrite as user phrases. `"Use when the user asks to review code,
audit a PR, or check a diff for issues."`

### 4. The Missing Negative

```yaml
description: Use this skill whenever the user wants to create or edit a markdown document.
```

Problem: too broad - this skill will fire on every README edit, every doc
change. Symptoms: over-triggering, frustration.

**Fix**: add the "Do NOT use for" clause. `"Do NOT use for editing arbitrary
markdown files, only for files matching SKILL.md."`

### 5. The Internal Jargon

```yaml
description: Use this skill when the user wants to run the standard backend-platform-team onboarding flow for new microservices.
```

Problem: the user does not type "standard backend-platform-team onboarding
flow". They type "create a new service" or "set up a microservice".

**Fix**: use the **user's vocabulary**, not the team's.

---

## A/B Testing Descriptions

When two descriptions look equally good, run them through `evals/evals.json`
using the procedure in `eval-methodology.md`. The signal:

- **Recall on positive cases**: did the skill fire when it should have?
  Goal: ≥ 80%.
- **Precision on negative cases**: did the skill NOT fire when it should not
  have? Goal: ≥ 80%.
- **Held-out score**: split eval cases 70 / 30. Optimize on the 70, report
  numbers from the 30. Prevents over-fitting the description to a specific
  test case.

`scripts/improve_description.py` automates the candidate generation. Run it,
then use the same eval procedure to pick the winner.

---

## Field-Length Reference

For a 500-char budget (typical), here is how the budget breaks down:

| Section | Chars | Content |
|---|---|---|
| Positive clause | 80 | "Use this skill whenever the user wants to ..." |
| Trigger phrases | 200 | 5 - 8 phrases with quotes and commas |
| Scope examples | 100 | "Also use when ..." |
| Negative clause | 100 | "Do NOT use for ..." |
| Buffer | 20 | newlines, periods, etc. |

Stay inside this budget on the first pass. Expand only if the eval shows
specific gaps.

---

## Quick Self-Check Before Saving

- [ ] Starts with "Use this skill whenever ..."?
- [ ] Lists at least 5 explicit trigger phrases in quotes?
- [ ] Includes a "Do NOT use for ..." clause?
- [ ] Under 1024 chars?
- [ ] No `<` or `>` characters?
- [ ] Uses the user's vocabulary, not internal team jargon?

If any answer is no, fix it before moving to the eval stage.

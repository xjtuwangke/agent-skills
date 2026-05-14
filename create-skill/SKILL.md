---
name: create-skill
description: >
  Use this skill whenever the user wants to create, scaffold, validate, evaluate,
  or improve an AI agent skill (a SKILL.md package for Claude Code, OpenCode, or
  any Agent-Skills-Spec compatible platform). Triggers include any mention of
  "create a skill", "new skill", "scaffold skill", "skill template", "validate
  skill", "eval skill", "improve skill description", "skill trigger accuracy",
  or requests to package a repeatable workflow as a reusable skill. Also use when
  fixing under-triggering skills, migrating skills between Claude Code and
  OpenCode, or running A/B evaluations on skill descriptions. Do NOT use for
  editing arbitrary markdown files, authoring slash commands, or building MCP
  servers - those are separate workflows.
version: 1.0.0
author: kwang
license: MIT
tags:
  - DEV
  - meta
  - workflow
requires:
  skills: []
  mcps: []
  tools: [bash, read, write, edit]
related:
  skills: []
  commands: []
  mcps: []
suggests:
  tools: []
  runtimes:
    - python >=3.10
  mcps: []
metadata:
  spec: agent-skills-1.0
  opencode:
    category: unspecified-high
---

# Create Skill

A meta-skill that produces other skills. Use it to scaffold, write, validate,
evaluate, and iterate `SKILL.md` packages compatible with Claude Code and
OpenCode under the Agent Skills Specification.

---

## When to Use

- "Create a skill that ..."
- "Make a new skill for ..."
- "This workflow keeps repeating - turn it into a skill"
- "Why isn't my skill triggering?"
- "Improve the description of `<skill>`"
- "Validate my skill before publishing"
- "Run an eval on `<skill>`"
- "Convert this Claude skill to OpenCode format" (or vice versa)

## When NOT to Use

- Editing arbitrary markdown files - use `edit` directly
- Writing a `/slash-command` - that is a different workflow
- Building an MCP server - skills are knowledge, MCP is connectivity
- One-off prompts - skills are for *repeatable* workflows only

---

## Prerequisites

The skill needs only the agent's built-in tools: `bash`, `read`, `write`,
`edit`. **No external runtime is required**. Every stage below has a manual
path that uses only these four tools.

If Python 3.10+ is available, the optional accelerator scripts under
`scripts/` automate the deterministic parts (placeholder substitution, rule
checking, result aggregation, frontmatter rewriting). They produce the same
output as the manual path but in one shell call instead of many.

| Environment | Path to use |
|---|---|
| Bare agent (only `bash` / `read` / `write` / `edit`) | Manual path |
| Python 3.10+ available | Either path; accelerators are faster |
| Neither available | This skill cannot run |

---

## Pre-execution Check

Before creating a new skill, verify:

1. **Output directory exists and is writable**:
   ```bash
   test -d <output-dir> && test -w <output-dir>
   ```
2. **Skill name is available**: No existing directory with the same name.
3. **Required tools available**: `bash`, `read`, `write`, `edit` are functional.
4. **Template files readable**: `templates/SKILL.md.tmpl` and
   `templates/evals.json.tmpl` exist and are readable.

If any check fails, STOP and report to the user.

---

## Safety Boundaries

### Forbidden Operations

- MUST NEVER overwrite an existing skill directory without user confirmation.
- MUST NEVER create skills outside the designated output directory.
- MUST NEVER generate skills with invalid frontmatter (always run validator).

### Confirmation Gates

STOP and ask for explicit confirmation before:
- Overwriting an existing skill directory
- Changing the output directory from the default
- Installing a skill that failed validation

### Emergency Stop

Immediately abort if:
- The user asks to create a skill with a name that violates naming conventions
- The template files are missing or corrupted
- The output directory is not writable
- A generated skill fails validation and the user insists on installing it

---

## 6-Stage Pipeline

| # | Stage | Manual Path | Accelerator |
|---|---|---|---|
| 1 | Capture intent | conversation | n/a |
| 2 | Interview | conversation | n/a |
| 3 | Scaffold + draft | `mkdir` + read template + `write` | `scripts/init_skill.py` |
| 4 | Test cases | conversation + `write` | n/a |
| 5 | Evaluate | spawn subagents + compute metrics in chat | `scripts/run_eval.py` |
| 6 | Iterate | generate variants in chat + `edit` | `scripts/improve_description.py` |
| ✓ | Install | `bash ln -s` (+ manual frontmatter rewrite for claude-strict) | `scripts/install_to_platform.py` |

---

## Stage 1: Capture Intent

Ask the user three questions. Write a one-paragraph charter in the chat (do
not write to disk yet).

1. **What should the skill enable?** What action, output, or knowledge does
   the user get that they did not have before?
2. **When should it trigger?** What user wording is the agent supposed to
   match? List at least three distinct phrasings.
3. **What is the deliverable?** A file? A code block? A decision? A side
   effect (commit, deploy, message)?

If any answer is vague, stop and ask. Vague intent guarantees an
under-triggering skill.

## Stage 2: Interview

Drill into edge cases. Required questions:

- **Anti-triggers**: when should this skill explicitly NOT fire?
- **Inputs**: what context must be in the prompt (file paths, IDs, configs)?
- **Dependencies**: does this skill call other skills, MCPs, or built-in tools?
- **Failure modes**: what is the agent likely to get wrong without the skill?
- **Verification**: how will the user know the skill did the right thing?

Capture answers in a scratchpad. They become the `## Hard Rules` and
`## Verification` sections of the new SKILL.md.

## Stage 3: Scaffold + Draft

### Manual path

1. Decide the output directory (default: current working directory).
2. Create the skeleton with `bash`:
   ```bash
   mkdir -p <output>/<name>/{references,scripts,assets,evals}
   ```
3. `read` `create-skill/templates/SKILL.md.tmpl`. Substitute these
   placeholders from Stage 1-2 values:

   | Placeholder | Source |
   |---|---|
   | `{{NAME}}` | skill name (kebab-case, matches directory) |
   | `{{TITLE}}` | Title Case of name |
   | `{{ACTION_PHRASE}}` | what the user wants to do |
   | `{{TRIGGER_1}}` .. `{{TRIGGER_3}}` | trigger phrases from Stage 1 |
   | `{{OUTCOME}}` | the deliverable summary |
   | `{{SECONDARY_USE_CASE}}` | secondary trigger |
   | `{{ANTI_TRIGGER_1}}` .. `{{ANTI_TRIGGER_2}}` | from Stage 2 |
   | `{{VERSION}}` | `0.1.0` |
   | `{{AUTHOR}}` | user-supplied or `$USER` |
   | `{{LICENSE}}` | `MIT` unless overridden |
   | `{{ROLE_TAG}}` | one of `DEV`, `QA`, `BA`, `DEVOPS` |
   | `{{DOMAIN_TAG}}` | one of `api`, `database`, `backend`, `infra`, `auth`, `cli`, `data`, `ml`, `meta` |
   | `{{REQUIREMENT_*}}`, `{{CHECK_*}}`, `{{PITFALL_*}}`, etc. | leave as `<fill in>` for now |

   `write` the rendered content to `<output>/<name>/SKILL.md`.

4. `read` `create-skill/templates/evals.json.tmpl`. Substitute
   `{{POSITIVE_PROMPT_1..3}}`, `{{NEGATIVE_PROMPT_1..2}}`, `{{EDGE_PROMPT_1}}`
   with realistic prompts (Stage 4 covers this in more detail).
   `write` to `<output>/<name>/evals/evals.json`.

### Accelerator

```bash
python create-skill/scripts/init_skill.py <name> \
    --description "<full description from Stage 1>" \
    --author "<author>" \
    --role DEV|QA|BA|DEVOPS \
    --domain api|database|backend|infra|auth|cli|data|ml|meta \
    [--output-dir <path>]
```

Or `python create-skill/scripts/init_skill.py --interactive` for prompts.

### Body Rules (apply either path)

- Keep `SKILL.md` under 500 lines.
- Anything longer spills into `references/<topic>.md`.
- Use progressive disclosure: metadata (always in context) -> SKILL.md
  (loaded when skill triggers) -> references (loaded on demand).
- See `references/description-patterns.md` for the "pushy description"
  pattern - the description field is the single biggest factor in whether the
  skill triggers.
- See `templates/skill-template.md` for the canonical structure. Every skill
  MUST include `## Pre-execution Check` and `## Safety Boundaries` sections.
- The `## Pre-execution Check` section MUST verify environment, directory,
  permissions, and state before executing any workflow step.
- The `## Safety Boundaries` section MUST define Forbidden Operations,
  Confirmation Gates, and Emergency Stop conditions.

## Stage 4: Test Cases

Open `<name>/evals/evals.json`. Replace placeholders with 3-5 realistic
prompts the user would actually type. Mix:

- **Positive triggers** (skill SHOULD fire): at least 3
- **Negative triggers** (skill should NOT fire): at least 2
- **Edge cases** (ambiguous wording): at least 1

Schema is in `templates/evals.json.tmpl`. Each entry needs `id`, `kind`,
`prompt`, `should_trigger`, `assertions`, and optional `notes`.

## Stage 5: Evaluate

The eval loop is always agent-driven (no external runtime required). For
each case in `evals.json`:

1. Spawn two parallel subagents:
   - `with-skill`: same prompt, with `<name>/SKILL.md` loaded.
   - `baseline`: same prompt, with no skill loaded.
2. Record for each: `triggered` (bool), `output` (text), and if available
   `tokens_in`, `tokens_out`, `latency_ms`.
3. Write the result file to
   `<name>/evals/results-YYYYMMDD-HHMMSS.json` using the schema in
   `references/eval-methodology.md`.

### Manual aggregation

In chat, count:

- `positive_recall = with_skill_triggered_count_on_positives / total_positives`
- `negative_precision = (total_negatives - with_skill_triggered_count_on_negatives) / total_negatives`

Pass thresholds: both `>= 0.80`.

### Accelerator

```bash
python create-skill/scripts/run_eval.py <skill-dir> --latest --split
```

`--split` reports train (70%) / test (30%) splits to detect description
over-fit.

## Stage 6: Iterate

If `positive_recall < 0.80` (under-triggering) or `negative_precision < 0.80`
(over-triggering), generate description variants:

### Manual path

Read the current `description:` from SKILL.md. Produce 3-5 variants by
applying these transforms from `references/description-patterns.md`:

1. **More pushy**: prepend "Use this skill whenever ..." if absent.
2. **Add negative clause**: append "Do NOT use for ..." if absent.
3. **Trigger list**: append `Triggers include: "..."` if absent.
4. **Shorter**: keep only the first two sentences.
5. **Imperative**: strip hedge words (`may`, `might`, `could`, `sometimes`,
   `perhaps`, `often`, `usually`, `typically`).

For each variant, re-run Stage 5. The winning variant is the one with the
highest test-set `(positive_recall + negative_precision) / 2`.

Apply the winner by editing the `description:` field of `<name>/SKILL.md`.

### Accelerator

```bash
python create-skill/scripts/improve_description.py <skill-dir>
python create-skill/scripts/improve_description.py <skill-dir> --apply best.txt
```

Iterate up to 3 rounds. If still not converging, the *charter* is the
problem - return to Stage 1.

## Final: Install

### Manual path

For OpenCode (user-global):
```bash
ln -s <repo-path>/<name> ~/.config/opencode/skills/<name>
```

For OpenCode (project-local):
```bash
mkdir -p .opencode/skills
ln -s <repo-path>/<name> .opencode/skills/<name>
```

For Claude Code (literal copy):
```bash
mkdir -p ~/.claude/skills
cp -r <repo-path>/<name> ~/.claude/skills/<name>
```

For Claude Code **strict** mode (Anthropic's `quick_validate.py` rejects
`version`/`author`/`tags`/`requires`/`related` at the top level):

1. Copy the skill directory to `~/.claude/skills/<name>/`.
2. `read` the copied SKILL.md, then `edit` its frontmatter so:
   - `name`, `description`, `license` stay at the top level.
   - `version`, `author`, `tags`, `requires`, `related` move under `metadata:`.
   - Existing `metadata.*` entries are preserved.
3. See `references/platform-differences.md` for the exact rewrite mapping.

### Accelerator

```bash
python create-skill/scripts/install_to_platform.py <name> --target opencode
python create-skill/scripts/install_to_platform.py <name> --target claude-strict
python create-skill/scripts/install_to_platform.py <name> --target opencode --target claude-strict
```

Default is symlink; use `--copy` for a literal copy.

---

## Hard Rules

1. `name` MUST match the directory name. Kebab-case
   `^[a-z0-9]+(-[a-z0-9]+)*$`, `<= 64` chars.
2. `description` MUST be `<= 1024` chars, MUST contain no angle brackets, MUST
   list at least one explicit trigger phrase.
3. `version` MUST be SemVer 2.0 (`^\d+\.\d+\.\d+(-[\w.]+)?$`).
4. `author` MUST be a non-empty string.
5. `tags` MUST include `>= 1` role tag (UPPERCASE) AND `>= 1` domain tag
   (lowercase).
6. `requires` MUST exist with keys `skills`, `mcps`, `tools` (empty lists are
   fine).
7. `related` MUST exist with keys `skills`, `commands`, `mcps` (NOT `tools`).
8. `suggests` (optional) MUST have keys `tools`, `runtimes`, `mcps` if present.
   Use it for optional accelerators (e.g., `python >=3.10`) — never put
   required tools here.
9. Dependency strings MUST use pip / PEP 440 style: `name`, `name ==1.0.0`,
   `name >=1.0.0`, `name ~=1.0.0`.
10. `SKILL.md` body MUST be `<= 500` lines.
11. Every skill MUST ship at least one entry in `evals/evals.json` before
      installation.
12. **ALL output MUST be in English.** This includes SKILL.md content, changelog
      entries, reference documents, eval cases, and any generated artifacts.
      The user's natural language for conversation is respected, but all
      deliverables produced by this skill MUST be written in English.
13. **Pre-execution Check is MANDATORY.** Every generated skill MUST include a
      `## Pre-execution Check` section that verifies environment, directory,
      permissions, and state before executing any workflow step.
14. **Safety Boundaries are MANDATORY.** Every generated skill MUST include a
      `## Safety Boundaries` section with Forbidden Operations, Confirmation
      Gates, and Emergency Stop conditions.
15. **Confirmation Gates are MANDATORY.** Any skill that performs destructive
      operations (delete, modify config, elevated privileges) MUST STOP and ask
      for explicit user confirmation before proceeding.

Either path (manual or accelerator) must produce output that satisfies these
rules. If using `scripts/validate_skill.py`, exit 0 == compliant. Without the
script, walk the rules manually against the new SKILL.md.

---

## Quick Reference

| If you need | Read |
|---|---|
| Field-by-field frontmatter rules | `references/frontmatter-spec.md` |
| How Claude Code and OpenCode differ | `references/platform-differences.md` |
| Writing a description that actually triggers | `references/description-patterns.md` |
| How the eval loop works | `references/eval-methodology.md` |
| Pre-publish gate | `assets/pre-publish-checklist.md` |
| Canonical skill template (with pre-check and safety) | `templates/skill-template.md` |

---

## Common Pitfalls

1. **Vague description.** "Helps with code review" triggers nothing. List the
   exact phrases the user would type. See `references/description-patterns.md`.
2. **Skipping evals.** Skills that pass spelling do not pass triggering. The
   eval loop exists because self-generated skills have *negative* utility
   without iteration.
3. **Stuffing the body.** If `SKILL.md` exceeds 500 lines, the agent will not
   read past the top. Move detail into `references/`.
4. **Top-level fields outside the spec.** Anthropic's `quick_validate.py`
   rejects unknown top-level keys. The OpenCode build is fine as-is; for
   Claude install, use the strict path (manual rewrite or `--target
   claude-strict`).
5. **Forgetting `requires.tools`.** If the skill calls `bash`, declare
   `requires.tools: [bash]`. Without this the validator cannot warn when the
   agent lacks `bash`.
6. **Putting required runtimes in `suggests`.** Python is optional for
   create-skill, so it belongs in `suggests.runtimes`. If your skill cannot
   function without Python, put it in `requires.tools` (as a tool dependency)
   or document it in `compatibility`.

---

## Verification Checklist (before declaring done)

- [ ] All Hard Rules above are satisfied (validator exit 0, or manual walk).
- [ ] `evals/evals.json` has at least 3 positive + 2 negative cases.
- [ ] Stage 5 eval shows positive cases trigger `>= 80%` of the time.
- [ ] Stage 5 eval shows negative cases stay below `20%` trigger rate.
- [ ] `SKILL.md` body is under 500 lines.
- [ ] Description is "pushy" (explicit trigger phrases + a "Do NOT use for"
      clause).
- [ ] If installing to claude-strict, `metadata.version` / `metadata.author` /
      `metadata.tags` / `metadata.requires` / `metadata.related` all exist
      after install.
- [ ] Generated skill includes `## Pre-execution Check` section.
- [ ] Generated skill includes `## Safety Boundaries` section with Forbidden
      Operations, Confirmation Gates, and Emergency Stop.
- [ ] Generated skill follows the canonical template in
      `templates/skill-template.md`.

---
name: update-skill
description: >
  Use this skill whenever the user wants to update, version-bump, or release a
  new version of an existing AI agent skill. Triggers include "update my
  skill", "bump version", "release skill", "new changelog entry", "increment
  version", or any request to modify a skill after its initial creation. Also
  use when the user says a skill needs a fix, improvement, or new eval case and
  the change is significant enough to warrant a version change. Do NOT use for
  creating a brand-new skill from scratch - that is create-skill. Do NOT use
  for editing arbitrary markdown files that are not agent skills.
version: 1.2.0
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
  skills: [create-skill]
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

# Update Skill

A meta-skill that updates existing skills. It enforces monotonic version
incrementing and maintains a `changelog.md` in every skill directory.

---

## When to Use

- "Update my skill"
- "Bump the version of `<skill>`"
- "Release a new version of `<skill>`"
- "Add a changelog entry"
- "Increment version after fixing `<skill>`"
- "My skill needs a patch release"

## When NOT to Use

- Creating a new skill from scratch — use `create-skill`
- Editing non-skill markdown files
- One-off fixes that do not change the skill's behaviour (use `edit` directly)

---

## Prerequisites

The skill needs only the agent's built-in tools: `bash`, `read`, `write`, `edit`.
**No external runtime is required**.

If Python 3.10+ is available, optional accelerator scripts under `scripts/`
automate version parsing, bumping, and changelog formatting.

| Environment | Path to use |
|---|---|
| Bare agent (only `bash` / `read` / `write` / `edit`) | Manual path |
| Python 3.10+ available | Either path; accelerators are faster |
| Neither available | This skill cannot run |

---

## Pre-execution Check

Before updating a skill, verify:

1. **Target skill exists**: The skill directory and `SKILL.md` must exist.
2. **Version is parseable**: The current `version` field in frontmatter is valid
   SemVer.
3. **Changelog exists or can be created**: `changelog.md` exists, or the
   template `templates/changelog.md.tmpl` is available.
4. **Working directory is clean**: No uncommitted changes that could interfere.

If any check fails, STOP and report to the user.

---

## Safety Boundaries

### Forbidden Operations

- MUST NEVER downgrade a version (monotonicity is enforced).
- MUST NEVER create a changelog entry without a version bump.
- MUST NEVER modify a skill that fails validation after the update.

### Confirmation Gates

STOP and ask for explicit confirmation before:
- Bumping major version (breaking change)
- Overwriting existing changelog entries
- Updating a skill that is currently installed in production

### Emergency Stop

Immediately abort if:
- The new version is not strictly greater than the current version
- The changelog template is missing and `changelog.md` does not exist
- Validation fails after the update and the user does not want to fix it

---

## 5-Stage Pipeline

| # | Stage | Manual Path | Accelerator |
|---|---|---|---|
| 1 | Capture change intent | conversation | n/a |
| 2 | Determine bump type | conversation | n/a |
| 3 | Bump version + validate monotonicity | `read` + `edit` | `scripts/bump_version.py` |
| 4 | Update changelog | `read` + `write` / `edit` | `scripts/update_changelog.py` |
| 5 | Re-validate | manual rule walk or `bash` | `scripts/validate_skill.py` (from create-skill) |

---

## Stage 1: Capture Change Intent

Ask the user what changed. Write a one-paragraph summary in the chat (do not
write to disk yet).

1. **Which skill?** Directory name (e.g., `create-skill`).
2. **What changed?** Description of the fix, feature, or improvement.
3. **Who made the change?** Human author or agent identifier.
4. **What generated the change?** Tool or model name (e.g., `Claude Code`,
   `OpenCode`, `kwang`).

If the user says "just bump the version" with no change description, refuse.
A version bump without a changelog entry is not allowed.

## Stage 2: Determine Bump Type

Use Semantic Versioning 2.0.0 rules:

| Change type | Bump | Examples |
|---|---|---|
| Breaking change to workflow, removed rule, changed output format | **major** | `1.2.3 → 2.0.0` |
| New feature, new eval case, description improvement that raises trigger rate | **minor** | `1.2.3 → 1.3.0` |
| Bug fix, typo, formatting, non-behavioural tweak | **patch** | `1.2.3 → 1.2.4` |

If unsure, default to **patch**.

## Stage 3: Bump Version

### Manual path

1. `read` `<skill-dir>/SKILL.md`.
2. Find the `version:` line in the frontmatter.
3. Parse the current version `MAJOR.MINOR.PATCH`.
4. Compute the new version using the bump type from Stage 2.
5. **Monotonicity check**: the new version MUST be strictly greater than the
   old version when compared numerically component-by-component. If not, stop
   and report the error.
6. `edit` the `version:` line to the new value.

### Accelerator

```bash
python update-skill/scripts/bump_version.py <skill-dir> --type major|minor|patch
```

The script:
- Parses the current version from frontmatter.
- Computes the new version.
- Enforces monotonicity (refuses to bump to a lower or equal version).
- Edits `SKILL.md` in place.
- Prints old → new version.

## Stage 4: Update Changelog

Every skill MUST maintain a `changelog.md` in its root directory. If absent,
create it from the template.

### Changelog format

```markdown
# Changelog

All notable changes to this skill are documented in this file.

## [1.1.0] - 2024-01-15

### Added
- New eval case for ambiguous trigger wording.

### Changed
- Improved description to include "rate limiting" trigger.

**Changed by**: kwang
**Generated by**: Claude Code / update-skill
**Timestamp**: 2024-01-15T10:30:00Z
```

Sections (use only those that apply):
- `### Added` — new features, eval cases, references.
- `### Changed` — modifications to existing behaviour.
- `### Fixed` — bug fixes.
- `### Removed` — deleted rules, features, or files.
- `### Deprecated` — scheduled for removal.

Each release block ends with three metadata lines:
- `**Changed by**: <author>`
- `**Generated by**: <tool or model>`
- `**Timestamp**: <ISO-8601 UTC>`

### Manual path

1. `read` `<skill-dir>/changelog.md`. If missing, `read`
   `update-skill/templates/changelog.md.tmpl` and `write` it to the skill dir.
2. Insert a new `## [VERSION] - DATE` block **at the top** (after the header
   lines and before the first existing release block).
3. Populate the sections from Stage 1's change summary.
4. Append the three metadata lines.
5. `write` the updated file.

### Accelerator

```bash
python update-skill/scripts/update_changelog.py <skill-dir> \
    --version 1.1.0 \
    --author "kwang" \
    --generated-by "Claude Code / update-skill" \
    --added "New eval case for ambiguous trigger wording" \
    --changed "Improved description to include rate limiting trigger"
```

If `--version` is omitted, the script reads it from `SKILL.md`.

## Stage 5: Re-validate

After any version bump, run the validator to ensure the skill is still
compliant.

```bash
python create-skill/scripts/validate_skill.py <skill-dir>
```

If validation fails, fix the issue before declaring the update complete. Do not
commit a broken skill.

---

## Hard Rules

1. `version` MUST be monotonically increasing. No downgrades, no repeats.
2. Every version bump MUST have a corresponding `changelog.md` entry.
3. `changelog.md` MUST exist in every skill directory after the first release.
4. `changelog.md` MUST use the format defined in Stage 4 (header, release
   blocks, metadata lines).
5. The `## [VERSION] - DATE` block MUST be inserted at the top (newest first).
6. Timestamps MUST be ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`).
7. Only the sections that apply (`Added`, `Changed`, `Fixed`, `Removed`,
    `Deprecated`) may be present. Empty sections are not allowed.
8. **ALL output MUST be in English.** This includes SKILL.md content, changelog
    entries, reference documents, eval cases, and any generated artifacts.
    The user's natural language for conversation is respected, but all
    deliverables produced by this skill MUST be written in English.

---

## Verification Checklist

- [ ] Old version < new version (monotonicity).
- [ ] `changelog.md` exists and contains the new release block.
- [ ] The new release block is at the top of the file.
- [ ] Metadata lines (`Changed by`, `Generated by`, `Timestamp`) are present.
- [ ] Validator passes on the updated skill.
- [ ] No empty sections in the changelog entry.

---

## Common Pitfalls

1. **Forgetting the changelog.** A version bump without a changelog entry is
   incomplete. The user cannot tell what changed.
2. **Wrong bump type.** A description tweak that raises eval scores is a
   **minor** bump, not patch. A removed rule is **major**.
3. **Non-monotonic version.** Editing `version` by hand can produce duplicates.
   Always use the bump script or the manual algorithm.
4. **Missing metadata.** The `Changed by` / `Generated by` / `Timestamp` lines
   are required for auditability.
5. **Appending to the bottom.** Newest release goes at the **top** so the
   changelog reads like a timeline in reverse.

---

## Quick Reference

| If you need | Read |
|---|---|
| Semantic Versioning rules | `references/semver-rules.md` |
| Changelog template | `templates/changelog.md.tmpl` |
| How to create a skill | `create-skill/SKILL.md` |

---

## References

- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)

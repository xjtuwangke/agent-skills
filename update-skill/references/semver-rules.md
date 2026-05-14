# Semantic Versioning Rules for Agent Skills

This document defines how version numbers are incremented when updating a skill.

---

## SemVer 2.0.0 Summary

Given a version number `MAJOR.MINOR.PATCH`, increment the:

1. **MAJOR** version when you make incompatible changes.
2. **MINOR** version when you add functionality in a backward-compatible manner.
3. **PATCH** version when you make backward-compatible bug fixes.

---

## Mapping to Skill Changes

### MAJOR Bump (X.y.z → X+1.0.0)

Use when:
- A rule in `## Hard Rules` is removed or changed incompatibly.
- The skill's output format changes (e.g., used to produce JSON, now produces YAML).
- A required tool is removed from `requires.tools`.
- The trigger conditions are narrowed so prompts that used to match no longer match.

### MINOR Bump (x.Y.z → x.Y+1.0)

Use when:
- A new feature, workflow step, or eval case is added.
- The description is improved and eval scores rise (higher trigger rate).
- A new reference document is added.
- A new optional tool is added to `requires.tools`.

### PATCH Bump (x.y.Z → x.y.Z+1)

Use when:
- A typo or formatting fix in SKILL.md.
- A bug in an accelerator script is fixed.
- A broken link in references is fixed.
- Wording clarification that does not change behaviour.

---

## Monotonicity

Version numbers MUST always increase. The following are forbidden:

- Downgrading: `1.2.0 → 1.1.0`
- Repeating: `1.2.0 → 1.2.0`
- Skipping: `1.0.0 → 1.0.5` without intermediate releases (allowed but discouraged)

The `bump_version.py` script enforces this automatically.

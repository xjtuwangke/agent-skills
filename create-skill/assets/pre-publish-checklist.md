# Pre-Publish Checklist

A skill is not done until every box below is checked. The validator covers
some, but not all, of these.

---

## Structural (automated by `validate_skill.py`)

- [ ] `SKILL.md` exists at `<skill>/SKILL.md`.
- [ ] Frontmatter opens with `---` on line 1 and closes with `---` on its own
      line.
- [ ] `name` matches the directory name and follows kebab-case.
- [ ] `description` is between 30 and 1024 chars and contains no angle
      brackets.
- [ ] `version` is SemVer 2.0.
- [ ] `author` is non-empty.
- [ ] `license` is set.
- [ ] `metadata.tags` has at least one role tag (UPPERCASE) AND one domain tag
      (lowercase).
- [ ] `metadata.requires` has `skills`, `mcps`, `runtimes` keys (empty lists are
      fine).
- [ ] `metadata.suggests` (if present) has `skills`, `mcps`, `runtimes` keys.
- [ ] `SKILL.md` body is under 500 lines.
- [ ] `evals/evals.json` has at least 3 positive and 2 negative cases.

Run: `python create-skill/scripts/validate_skill.py <skill-dir>` -> exit 0.

---

## Description Quality (manual review)

- [ ] Description starts with "Use this skill whenever ...".
- [ ] Description lists at least 5 explicit trigger phrases in quotes.
- [ ] Description includes a "Do NOT use for ..." clause.
- [ ] Description uses user vocabulary (not internal team jargon).
- [ ] If skill targets claude.ai preview, first 200 chars carry the full
      "what + when" intent.

Reference: `create-skill/references/description-patterns.md`.

---

## Eval Quality (manual + `run_eval.py`)

- [ ] `evals/evals.json` has at least 3 positives, 2 negatives, 1 edge case.
- [ ] Positive prompts are realistic user wordings, not paraphrased
      descriptions.
- [ ] Negative prompts share surface vocabulary with positives but should NOT
      trigger.
- [ ] At least one `results-*.json` exists in `evals/`.
- [ ] Latest result: `positive_recall >= 0.80`.
- [ ] Latest result: `negative_precision >= 0.80`.
- [ ] Train / test split (if optimized): test recall is within 0.20 of train
      recall.

Run: `python create-skill/scripts/run_eval.py <skill-dir> --latest --split`.

---

## Body Quality (manual review)

- [ ] `## When to Use` lists at least 3 trigger phrases.
- [ ] `## When NOT to Use` lists at least 2 anti-triggers.
- [ ] Each step in the workflow is a numbered imperative sentence.
- [ ] `## Hard Rules` uses MUST / MUST NOT / SHOULD consistently.
- [ ] `## Verification` has a concrete checklist the agent can run on itself.
- [ ] `## Common Pitfalls` has at least 2 entries with a *Fix*.
- [ ] Any section longer than ~150 lines is split into `references/<topic>.md`.
- [ ] Internal links use relative paths (`references/foo.md`), not absolute.

---

## Dependencies (manual review)

- [ ] Every skill listed in `requires.skills` actually exists at the target
      install location.
- [ ] Every MCP in `requires.mcps` is documented in the team's MCP registry.
- [ ] Every runtime in `metadata.requires.runtimes` is a known name the agent
      recognizes (validator emits warnings for unknowns).
- [ ] No top-level keys outside the spec; platform-specific data lives under
      `metadata.<platform>.*`.

---

## Cross-Platform Sanity

- [ ] If installing to `--target claude-strict`, manually open the resulting
      `~/.claude/skills/<name>/SKILL.md` and confirm `metadata.tags`,
      `metadata.requires`, and `metadata.suggests` are present.
- [ ] If skill references an OpenCode-only feature (`metadata.opencode.*`),
      add a note in `## When NOT to Use` for Claude Code users.

---

## Audit Trail

- [ ] If `install_to_platform.py --skip-eval` was used, the reason is noted
      in `evals/SKIP-EVAL-REASON.md` (single line is enough).
- [ ] Version was bumped if the skill changed since last install.
- [ ] If breaking changes, version bumped to next major.

---

## Final Smoke Test

- [ ] Run the calling agent with a real, fresh prompt that should trigger the
      skill. Confirm it fires.
- [ ] Run the calling agent with a negative prompt. Confirm the skill does NOT
      fire.
- [ ] If either fails, return to the eval loop. Do not declare done.

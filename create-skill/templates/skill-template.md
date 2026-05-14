# Skill Template

This is the canonical template for all skills in this repository. Every skill
MUST follow this structure. Copy this file and replace all `{{PLACEHOLDER}}`
values.

**Size limit**: SKILL.md body <= 500 lines. Spill detail into `references/`.

---

```yaml
---
name: {{NAME}}
description: >
  Use this skill whenever the user wants to {{ACTION_PHRASE}}. Triggers include
  any mention of "{{TRIGGER_1}}", "{{TRIGGER_2}}", "{{TRIGGER_3}}", or requests
  to {{OUTCOME}}. Also use when {{SECONDARY_USE_CASE}}. Do NOT use for
  {{ANTI_TRIGGER_1}} or {{ANTI_TRIGGER_2}} - those are separate workflows.
license: {{LICENSE}}
metadata:
  version: {{VERSION}}
  author: {{AUTHOR}}
  spec: agent-skills-1.0
  lastUpdated: {{LAST_UPDATED}}
  tags:
    - {{ROLE_TAG}}
    - {{DOMAIN_TAG}}
  requires:
    skills: []
    mcps: []
    runtimes: []
  suggests:
    skills: []
    mcps: []
    runtimes: []
  opencode:
    category: unspecified-high
---

# {{TITLE}}

One-paragraph charter: what this skill enables, who it is for, what changes
after the user invokes it.

---

## When to Use

- "{{TRIGGER_1}}"
- "{{TRIGGER_2}}"
- "{{TRIGGER_3}}"
- (add more as discovered)

## When NOT to Use

- {{ANTI_TRIGGER_1}}
- {{ANTI_TRIGGER_2}}

---

## Inputs

### Required

| Name | Type | Description |
|---|---|---|
| {{INPUT_REQUIRED_1}} | {{INPUT_TYPE_1}} | {{INPUT_DESC_1}} |

### Optional

| Name | Type | Default | Description |
|---|---|---|---|
| {{INPUT_OPTIONAL_1}} | {{INPUT_TYPE_2}} | {{INPUT_DEFAULT_1}} | {{INPUT_DESC_2}} |

---

## Output

| Artifact | Format | Description |
|---|---|---|
| {{OUTPUT_1}} | {{OUTPUT_FORMAT_1}} | {{OUTPUT_DESC_1}} |

---

## Pre-execution Check

Before executing any workflow step, verify these conditions. If any check
fails, STOP and report the failure to the user. Do not proceed.

1. **Environment check**: Verify the required tools/runtime are available.
   ```bash
   # Example: check tool availability
   which docker || echo "ERROR: docker not found"
   ```
2. **Directory check**: Verify the working directory is the expected one.
   ```bash
   pwd | grep -q "expected-path" || echo "ERROR: wrong directory"
   ```
3. **Permission check**: Verify the agent has permission to modify the target
   files. Read first, write only after confirmation.
4. **State check**: Verify the system is in the expected state before making
   changes. Do not assume.
5. **Backup check**: If the skill modifies existing files, confirm backups
   exist or create them before proceeding.

---

## Workflow

Step-by-step procedure. Number every step. Keep imperative voice.

1. Run the Pre-execution Check above. STOP if any check fails.
2. Step two.
3. Step three.

---

## Safety Boundaries

This section defines what this skill will NEVER do. It protects the user from
accidental damage.

### Forbidden Operations

- MUST NEVER delete production data.
- MUST NEVER modify files outside the project directory.
- MUST NEVER execute destructive commands without user confirmation.
- MUST NEVER bypass authentication or security controls.
- MUST NEVER commit or push code without explicit user request.

### Confirmation Gates

For any operation that matches the criteria below, STOP and ask the user for
explicit confirmation before proceeding:

- Deletes files or directories
- Modifies files in `.git/` or `.env`
- Runs commands with `sudo` or elevated privileges
- Modifies production configuration
- Changes database schema in production
- Sends data to external services

### Emergency Stop

Immediately abort and report to the user if:

- The user asks to bypass a safety check
- The target system is not in the expected state
- A command returns an unexpected error code
- Data loss is detected or suspected
- The operation would affect more resources than intended

---

## Hard Rules

Constraints that MUST be enforced. Use UPPERCASE for emphasis on the
constraint, not the rule text.

- MUST always {{REQUIREMENT_1}}.
- MUST NEVER {{ANTI_REQUIREMENT_1}}.
- SHOULD {{RECOMMENDATION_1}}.
- **ALL output MUST be in English.** This includes SKILL.md content, changelog
  entries, reference documents, eval cases, and any generated artifacts.

---

## Verification

How the user (or the agent) knows the skill did the right thing.

- [ ] {{CHECK_1}}
- [ ] {{CHECK_2}}
- [ ] {{CHECK_3}}

---

## Common Pitfalls

1. **{{PITFALL_NAME_1}}**. {{DESCRIPTION_1}}.
   *Fix*: {{FIX_1}}.
2. **{{PITFALL_NAME_2}}**. {{DESCRIPTION_2}}.
   *Fix*: {{FIX_2}}.

---

## References

Link to supporting docs in `references/` and external resources here. Keep the
top-level SKILL.md under 500 lines; spill detail into `references/`.
```

---

## Template Rules

1. **Pre-execution Check** is MANDATORY. Every skill must verify conditions
   before acting. Replace the example checks with real ones for your skill.
2. **Safety Boundaries** is MANDATORY. Define what your skill will NEVER do.
   Add skill-specific forbidden operations.
3. **Emergency Stop** conditions are MANDATORY. List scenarios where the skill
   must abort immediately.
4. **English-only output** is MANDATORY. Add this to Hard Rules in every skill.
5. **Confirmation Gates** are MANDATORY. Any destructive operation requires
   explicit user confirmation.
6. **Inputs section** is MANDATORY. Document both required and optional inputs
   with name, type, and description.
7. **Output section** is MANDATORY. Document produced artifacts with format and
   description.

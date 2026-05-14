# Frontmatter Specification

Field-by-field rules for every key allowed in a `SKILL.md` frontmatter. The
validator (`scripts/validate_skill.py`) enforces this document. If you change
this document, change the validator too.

---

## Required Fields

### `name` (string)

The skill's stable identifier. **Must match the directory name** containing
`SKILL.md`.

- Pattern: `^[a-z0-9]+(-[a-z0-9]+)*$`
- Length: 1 - 64 chars
- Cannot start or end with `-`
- Cannot contain `--`

```yaml
name: create-skill              # OK
name: skill_creator             # INVALID - underscore
name: Skill-Creator             # INVALID - uppercase
name: my--skill                 # INVALID - consecutive hyphens
```

### `description` (string)

The single most important field. The agent loads this string into context at
all times, and decides whether to invoke the skill by matching the user's
prompt against this text.

- Length: 1 - 1024 chars (200 chars max for claude.ai preview)
- MUST NOT contain `<` or `>` (Anthropic validator rule)
- MUST list explicit trigger phrases
- SHOULD include a "Do NOT use for ..." clause

See `description-patterns.md` for templates.

```yaml
description: >
  Use this skill whenever the user wants to create or edit a SKILL.md file.
  Triggers include "create a skill", "new skill", "scaffold skill". Do NOT use
  for editing arbitrary markdown files.
```

### `version` (string)

Semantic Version 2.0.0.

- Pattern: `^\d+\.\d+\.\d+(-[\w.]+)?$`
- Examples: `1.0.0`, `0.2.3`, `1.0.0-beta.1`, `2.5.0-rc.4`

```yaml
version: 1.0.0
```

### `author` (string)

Non-empty string. Free-form (handle, real name, team name, email).

```yaml
author: kwang
author: kwang <kwang@example.com>
author: Backend Platform Team
```

### `license` (string)

SPDX identifier (recommended) or free-form license string.

```yaml
license: MIT
license: Apache-2.0
license: Proprietary - Internal use only
```

### `tags` (list)

Categorization labels. Validator enforces a minimum of one **role** tag
(UPPERCASE) and one **domain** tag (lowercase).

**Role tags (UPPERCASE, ≥ 1 required)**:
- `DEV` - developer-facing skills
- `QA` - quality assurance, testing
- `BA` - business analysis, requirements
- `DEVOPS` - infrastructure, CI/CD, deployment

**Domain tags (lowercase, ≥ 1 required)**:
- `api` - HTTP / RPC / GraphQL APIs
- `database` - SQL, NoSQL, schema, migrations
- `backend` - server-side application code
- `infra` - infrastructure, hosting, networking
- `auth` - authentication, authorization
- `cli` - command-line tools
- `data` - data processing, ETL, pipelines
- `ml` - machine learning, model training
- `meta` - tools that produce or modify other skills

**Layer tags (lowercase, optional)**:
- `workflow` - multi-step procedure
- `knowledge` - reference material
- `template` - boilerplate generator
- `eval` - evaluation, testing
- `automation` - self-driving task execution

**Maturity tags (lowercase, optional)**:
- `experimental` - default if unspecified
- `stable` - production-ready
- `deprecated` - scheduled for removal

**Free-form (lowercase, kebab-case, optional)**: any other label.

```yaml
tags:
  - DEV              # role
  - api              # domain
  - workflow         # layer
  - stable           # maturity
  - rate-limiting    # free-form
```

---

## Dependency Fields (Required structure, lists may be empty)

### `requires` (object)

Hard dependencies. If any listed item is missing at install or load time, the
validator fails and the agent should not activate the skill.

Three keys, all required (use `[]` if nothing):

```yaml
requires:
  skills: []                 # other skills this skill calls
  mcps: []                   # MCP servers this skill calls
  tools: []                  # built-in agent tools this skill calls
```

**Dependency string syntax (pip / PEP 440 style)**:

```yaml
requires:
  skills:
    - git-master                 # any version
    - validator ==1.0.0          # exact
    - validator >=1.0.0          # range
    - validator >=1.0.0,<2.0.0   # bounded
    - validator ~=1.2.0          # compatible release (>=1.2.0,<1.3.0)
```

The separator is a single space between name and operator. Whitespace inside
the version spec is not allowed.

`tools` are built-in agent tool names. Examples: `bash`, `read`, `write`,
`edit`, `grep`, `glob`, `webfetch`, `task`. The validator emits a warning if a
tool name is not recognized.

### `related` (object)

Soft references for navigation and discovery. The validator does NOT enforce
presence - missing items are fine.

Three keys, all required (use `[]` if nothing):

```yaml
related:
  skills: []                 # see-also skills
  commands: []               # see-also slash commands (include leading /)
  mcps: []                   # see-also MCP servers
```

Note: `related.tools` does NOT exist. Built-in tools are either needed
(`requires.tools`) or irrelevant. There is no "see also" tool.

```yaml
related:
  skills: [review-work, ai-slop-remover]
  commands: ["/refactor", "/git-master"]
  mcps: [playwright, filesystem]
```

### `suggests` (object, optional)

Optional dependencies that improve the skill but are not required. When these
are available the skill can call scripts or external tools for speed; when
absent the skill falls back to the manual agent-driven path.

Three keys, all optional (omit the whole block or individual keys if nothing):

```yaml
suggests:
  tools: []                  # optional built-in tools (e.g., lsp_diagnostics)
  runtimes: []               # external runtimes (e.g., python>=3.10, node>=18)
  mcps: []                   # optional MCP servers
```

**`suggests.tools`** — Built-in agent tools that are nice-to-have. The skill
works without them but runs faster or produces richer output when present.

**`suggests.runtimes`** — External runtimes the skill can leverage for
accelerator scripts. Use free-form strings with version constraints.

**`suggests.mcps`** — Optional MCP servers that enhance the skill.

```yaml
suggests:
  tools: [lsp_diagnostics]
  runtimes:
    - python >=3.10
    - node >=18.0.0
  mcps: []
```

The validator checks structure (keys must be lists of strings) but does NOT
warn about unknown values — these are optional by definition.

---

## Optional Fields

### `metadata` (object)

Free-form bag for platform-specific or skill-specific data the spec does not
cover. Keys SHOULD be namespaced by platform.

```yaml
metadata:
  spec: agent-skills-1.0           # which spec version this skill follows
  opencode:
    category: deep                 # OpenCode delegation category
  claude:
    disable-model-invocation: false
  custom:
    internal-team-owner: backend-platform
```

### `compatibility` (string, optional)

Anthropic spec field. Free-form note about required runtime / dependencies.

```yaml
compatibility: requires python>=3.10 and pip-installed pyyaml
```

### `allowed-tools` (list, optional, Claude Code only)

Tools the skill is permitted to use without further user prompting. If absent,
the agent's default tool policy applies.

```yaml
allowed-tools:
  - Read
  - Grep
  - Bash(git diff:*)
```

---

## Strict Mode (Claude Code compatibility)

When installing to `.claude/skills/` with `--target claude-strict`,
`install_to_platform.py` rewrites the frontmatter:

```yaml
# Source (this repository)
name: create-skill
version: 1.0.0
author: kwang
tags: [DEV, meta]
license: MIT

# After --target claude-strict install
name: create-skill
license: MIT
metadata:
  version: 1.0.0
  author: kwang
  tags: [DEV, meta]
```

This is because Anthropic's `quick_validate.py` enforces a closed set of
top-level keys: `name`, `description`, `license`, `allowed-tools`,
`compatibility`, `metadata`.

---

## Minimum Valid Frontmatter

The shortest legal SKILL.md frontmatter:

```yaml
---
name: hello
description: >
  Use when the user says hello, hi, or greetings. Do NOT use for general
  conversation.
version: 0.1.0
author: kwang
license: MIT
tags:
  - DEV
  - meta
requires:
  skills: []
  mcps: []
  tools: []
related:
  skills: []
  commands: []
  mcps: []
---

# Hello

Respond with a friendly greeting.
```

# Frontmatter Specification

Field-by-field rules for every key allowed in a `SKILL.md` frontmatter. The
validator (`scripts/validate_skill.py`) enforces this document. If you change
this document, change the validator too.

---

## Required Top-Level Fields

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

### `metadata` (object)

Container for all skill metadata, dependencies, and platform-specific settings.

Required keys under `metadata`:
- `spec` — spec version this skill follows
- `tags` — categorization labels (see below)
- `requires` — hard dependencies (see below)

Optional keys under `metadata`:
- `suggests` — optional dependencies (see below)
- `opencode` — OpenCode-specific settings
- `claude` — Claude Code-specific settings
- `custom` — project-specific settings

```yaml
metadata:
  spec: agent-skills-1.0
  tags:
    - DEV
    - meta
  requires:
    skills: []
    mcps: []
    runtimes: []
  opencode:
    category: deep
```

---

## Metadata Fields

### `metadata.tags` (list)

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
metadata:
  tags:
    - DEV              # role
    - api              # domain
    - workflow         # layer
    - stable           # maturity
    - rate-limiting    # free-form
```

### `metadata.requires` (object)

Hard dependencies. If any listed item is missing at install or load time, the
validator fails and the agent should not activate the skill.

Three keys, all required (use `[]` if nothing):

```yaml
metadata:
  requires:
    skills: []                 # other skills this skill calls
    mcps: []                   # MCP servers this skill calls
    runtimes: []               # runtimes / tools this skill needs
```

**Dependency string syntax (pip / PEP 440 style)**:

```yaml
metadata:
  requires:
    skills:
      - git-master                 # any version
      - validator ==1.0.0          # exact
      - validator >=1.0.0          # range
      - validator >=1.0.0,<2.0.0   # bounded
      - validator ~=1.2.0          # compatible release (>=1.2.0,<1.3.0)
    runtimes:
      - python >=3.10
      - node >=18.0.0
```

The separator is a single space between name and operator. Whitespace inside
the version spec is not allowed.

`runtimes` includes both external runtimes (Python, Node) and built-in agent
tools (`bash`, `read`, `write`, `edit`, etc.). The validator emits a warning
if a runtime name is not recognized.

### `metadata.suggests` (object, optional)

Optional dependencies that improve the skill but are not required. When these
are available the skill can call scripts or external tools for speed; when
absent the skill falls back to the manual agent-driven path.

Three keys, all optional (omit the whole block or individual keys if nothing):

```yaml
metadata:
  suggests:
    skills: []                 # optional skills
    mcps: []                   # optional MCP servers
    runtimes: []               # optional runtimes / tools
```

**`suggests.runtimes`** — External runtimes or tools the skill can leverage.
Use free-form strings with version constraints.

```yaml
metadata:
  suggests:
    runtimes:
      - python >=3.10
      - node >=18.0.0
```

The validator checks structure (keys must be lists of strings) but does NOT
warn about unknown values — these are optional by definition.

---

## Optional Top-Level Fields

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
license: MIT
metadata:
  spec: agent-skills-1.0
  tags: [DEV, meta]

# After --target claude-strict install
name: create-skill
license: MIT
metadata:
  version: 1.0.0
  author: kwang
  spec: agent-skills-1.0
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
metadata:
  spec: agent-skills-1.0
  tags:
    - DEV
    - meta
  requires:
    skills: []
    mcps: []
    runtimes: []
---

# Hello

Respond with a friendly greeting.
```

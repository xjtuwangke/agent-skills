# Frontmatter Specification

Field-by-field rules for every key allowed in a `SKILL.md` frontmatter. The
validator (`scripts/validate_skill.py`) enforces this document. If you change
this document, change the validator too.

---

## Top-Level Fields

The frontmatter has two levels: **top-level** ( Anthropic-compatible keys) and
**metadata** (everything else). This design ensures skills work with Claude
Code's strict validator while remaining extensible.

### `name` (string, required)

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

### `description` (string, required)

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

### `license` (string, required)

SPDX identifier (recommended) or free-form license string.

```yaml
license: MIT
license: Apache-2.0
license: Proprietary - Internal use only
```

### `compatibility` (string, optional)

Free-form note about required runtime / dependencies. Shown in Claude Code's
skill listing.

```yaml
compatibility: requires python>=3.10 and pip-installed pyyaml
```

### Top-level keys that MUST NOT appear

The following keys MUST NOT be at the top level. Put them inside `metadata`:

- `version` → `metadata.version`
- `author` → `metadata.author`
- `tags` → `metadata.tags`
- `requires` → `metadata.requires`
- `suggests` → `metadata.suggests`

---

## `metadata` (object, required)

Container for all skill metadata, dependencies, and platform-specific settings.

```yaml
metadata:
  version: 1.0.0
  author: kwang
  spec: agent-skills-1.0
  lastUpdated: 2024-05-14T10:00:00Z
  tags: [DEV, meta]
  requires:
    skills: []
    mcps: []
    runtimes: []
```

### `metadata.version` (string, required)

Semantic Version 2.0.0.

- Pattern: `^\d+\.\d+\.\d+(-[\w.]+)?$`
- Examples: `1.0.0`, `0.2.3`, `1.0.0-beta.1`

### `metadata.author` (string, required)

Non-empty string. Free-form (handle, real name, team name, email).

```yaml
author: kwang
author: Backend Platform Team
```

### `metadata.spec` (string, required)

Which version of the Agent Skills Specification this skill follows.

```yaml
spec: agent-skills-1.0
```

### `metadata.lastUpdated` (string, required)

ISO-8601 UTC timestamp of the last modification.

```yaml
lastUpdated: 2024-05-14T10:00:00Z
```

### `metadata.tags` (list, required)

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

```yaml
tags:
  - DEV              # role
  - api              # domain
  - workflow         # layer
  - stable           # maturity
```

### `metadata.requires` (object, required)

Hard dependencies. If any listed item is missing at install or load time, the
validator fails and the agent should not activate the skill.

Three keys, all required (use `[]` if nothing):

```yaml
requires:
  skills: []                 # other skills this skill calls
  mcps: []                   # MCP servers this skill calls
  runtimes: []               # runtimes / tools this skill needs
```

**Dependency string syntax (pip / PEP 440 style)**:

```yaml
requires:
  skills:
    - git-master                 # any version
    - validator ==1.0.0          # exact
    - validator >=1.0.0          # range
  runtimes:
    - python >=3.10
    - node >=18.0.0
```

### `metadata.suggests` (object, optional)

Optional dependencies that improve the skill but are not required.

```yaml
suggests:
  skills: []                 # optional skills
  mcps: []                   # optional MCP servers
  runtimes: []               # optional runtimes / tools
```

### `metadata.opencode` / `metadata.claude` (object, optional)

Platform-specific settings.

```yaml
metadata:
  opencode:
    category: deep
  claude:
    disable-model-invocation: false
```

---

## Minimum Valid Frontmatter

```yaml
---
name: hello
description: >
  Use when the user says hello, hi, or greetings. Do NOT use for general
  conversation.
license: MIT
metadata:
  version: 0.1.0
  author: kwang
  spec: agent-skills-1.0
  lastUpdated: 2024-05-14T00:00:00Z
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

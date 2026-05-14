# Platform Differences: Claude Code vs OpenCode

This skill produces output compatible with both Claude Code and OpenCode. The
two platforms read the same `SKILL.md` format with minor differences. This
document is the reference for what those differences are and how
`install_to_platform.py` handles them.

---

## Discovery Locations (Priority Order)

OpenCode walks all of these and merges, with higher priority winning on name
collision:

1. `.opencode/skills/<name>/SKILL.md` (project)
2. `~/.config/opencode/skills/<name>/SKILL.md` (user)
3. `.claude/skills/<name>/SKILL.md` (project, Claude Code compat)
4. `~/.claude/skills/<name>/SKILL.md` (user, Claude Code compat)
5. Plugin-bundled and built-in skills

Claude Code reads only its own paths:

1. `.claude/skills/<name>/SKILL.md` (project)
2. `~/.claude/skills/<name>/SKILL.md` (user)

The implication: **installing to OpenCode only does NOT make the skill
available in Claude Code**. Install to both targets if you want both.

---

## Frontmatter Differences

### Top-Level Keys

| Key | Claude Code (strict) | OpenCode | This Repo |
|---|---|---|---|
| `name` | required | required | required |
| `description` | required | required | required |
| `license` | optional | optional | required |
| `allowed-tools` | optional | optional | optional |
| `compatibility` | optional | optional | optional |
| `metadata` | optional, free-form | optional, namespaced | required |
| `disable-model-invocation` | optional | ignored | use `metadata.claude.*` |
| `user-invocable` | optional | ignored | use `metadata.claude.*` |
| `version` | **rejected by quick_validate.py** | accepted | required |
| `author` | **rejected** | accepted | required |
| `metadata.tags` | accepted inside `metadata` | accepted | required |
| `metadata.requires` | accepted inside `metadata` | accepted | required |
| `metadata.suggests` | accepted inside `metadata` | accepted | optional |

### What `--target claude-strict` Does

When installing to a Claude Code path that runs Anthropic's official validator,
extra top-level fields would trigger warnings. The strict installer rewrites:

```yaml
# Source
name: create-skill
description: "..."
version: 1.0.0
author: kwang
license: MIT
metadata:
  spec: agent-skills-1.0
  tags: [DEV, meta]
  requires:
    skills: []
    mcps: []
    runtimes: [bash]
  suggests:
    skills: []
    mcps: []
    runtimes: []

# After --target claude-strict
name: create-skill
description: "..."
license: MIT
metadata:
  version: 1.0.0
  author: kwang
  spec: agent-skills-1.0
  tags: [DEV, meta]
  requires:
    skills: []
    mcps: []
    runtimes: [bash]
  suggests:
    skills: []
    mcps: []
    runtimes: []
```

OpenCode does not need this rewrite - it accepts extra top-level fields. Use
`--target opencode` for a literal copy.

---

## Invocation Differences

### Claude Code

- Skills are loaded by **description matching** when the agent decides the task
  fits. The user does not invoke them explicitly.
- Skills can also be invoked as slash commands: `/create-skill`.
- Skill loading is implicit; there is no `skill` tool the agent calls.

### OpenCode

- Skills are exposed as `<available_skills>` in the system prompt. The agent
  calls `skill({ name: "..." })` explicitly to load one.
- The `task()` tool's `load_skills=[...]` parameter pre-loads skills into a
  delegated subagent.
- OpenCode honors per-skill permissions configured in `opencode.json`.

---

## Tool Naming Differences

`metadata.requires.runtimes` lists runtimes and built-in agent tools. Names differ:

| Concept | Claude Code | OpenCode |
|---|---|---|
| Read a file | `Read` | `read` |
| Write a file | `Write` | `write` |
| Edit a file | `Edit` | `edit` |
| Run a shell command | `Bash` | `bash` |
| Search file contents | `Grep` | `grep` |
| Find files by glob | `Glob` | `glob` |
| Fetch a URL | `WebFetch` | `webfetch` |
| Spawn a subagent | `Task` | `task` |

This repo uses **lowercase** as the canonical form. On `--target claude-strict`
install, `install_to_platform.py` rewrites tool names to TitleCase
automatically.

---

## MCP Server Integration

### Claude Code

MCP servers are configured globally in `~/.claude/mcp.json` or per-project in
`.mcp.json`. Skills cannot bundle their own MCP server definitions; they can
only reference servers that the user has already configured.

### OpenCode

Skills CAN bundle MCP server definitions inside their frontmatter under
`metadata.opencode.mcp_servers`. OpenCode's `SkillMcpManager` starts these
servers when the skill loads and stops them when the session ends.

Example:

```yaml
metadata:
  opencode:
    mcp_servers:
      - name: github-api
        type: stdio
        command: node
        args: ["github-server.js"]
        env:
          GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

If a skill relies on a bundled MCP, declare it in `requires.mcps` and document
that the OpenCode build is the authoritative target. The Claude install will
not have that MCP available.

---

## Category System (OpenCode-only)

OpenCode's `task()` tool accepts a `category` parameter that selects a
domain-optimized model. Skills can recommend a category via
`metadata.opencode.category`.

Allowed values:

- `visual-engineering` (frontend - **N/A for this repo, backend-only project**)
- `artistry`
- `ultrabrain` (heavy logic)
- `deep` (autonomous research + implementation)
- `quick` (trivial single-file)
- `unspecified-low`, `unspecified-high`
- `writing`

Claude Code ignores this field.

---

## Recommended Install Strategy for This Repo

| Use case | Target |
|---|---|
| Daily use inside OpenCode | `--target opencode` |
| Distribute to teammates who use Claude Code | `--target claude-strict` |
| Both | both flags on the same invocation |

The source of truth always lives in the skill repository. The install command
creates symlinks (`-s` is the default), so any edit to the source file shows up
immediately in both platforms.

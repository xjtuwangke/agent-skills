---
name: database-migration
description: >
  Use this skill whenever the user wants to create, run, roll back, or inspect
  database migrations. Triggers include "create a migration", "run migrations",
  "rollback migration", "db migrate", "schema change", "add a column", or
  "generate migration file". Also use when the user asks about migration status,
  pending migrations, or migration best practices. Do NOT use for general
  database queries, ORM configuration, or database setup from scratch - those
  are separate workflows.
license: MIT
metadata:
  version: 1.0.0
  author: kwang
  spec: agent-skills-1.0
  lastUpdated: 2024-05-14T10:00:00Z
  tags:
    - DEV
    - database
    - backend
    - workflow
  requires:
    skills: []
    mcps: []
    runtimes: [bash, read, write, edit]
  suggests:
    skills: []
    mcps: []
    runtimes:
      - python >=3.10
      - node >=18.0.0
  opencode:
    category: deep
---

# Database Migration

A skill for managing database schema migrations safely. It generates migration
files, runs them in order, handles rollbacks, and verifies migration state.

Works with any migration framework (Alembic, Knex, Flyway, Django Migrations)
by reading the project's existing configuration rather than imposing its own.

---

## When to Use

- "Create a migration to add a users table"
- "Run pending migrations"
- "Rollback the last migration"
- "Check migration status"
- "Generate migration for adding a column"
- "Are there any pending migrations?"

## When NOT to Use

- General SQL queries (use the database client directly)
- Setting up a database from scratch (use infra or setup scripts)
- ORM model definition (use the framework's model generator)
- Data seeding or ETL (use a data pipeline skill)

---

## Prerequisites

The skill needs only the agent's built-in tools: `bash`, `read`, `write`, `edit`.
**No external runtime is required** for the manual path.

If Python 3.10+ or Node >=18 is available, the skill can leverage framework-
specific CLI tools (Alembic, Knex, Prisma) for faster migration generation.

| Environment | Path to use |
|---|---|
| Bare agent (only `bash` / `read` / `write` / `edit`) | Manual path |
| Python 3.10+ or Node >=18 available | Framework CLI path |
| Neither available | Manual path still works |

---

## Inputs

### Required

| Name | Type | Description |
|---|---|---|
| Migration intent | string | What schema change to make (e.g., "add email column to users") |
| Framework | string | `alembic`, `knex`, `prisma`, or `django` |

### Optional

| Name | Type | Default | Description |
|---|---|---|---|
| Database URL | string | `DATABASE_URL` env | Connection string for verification |
| Run immediately | boolean | `false` | Whether to run the migration after creation |
| Environment | string | `development` | `development`, `staging`, or `production` |

---

## Output

| Artifact | Format | Description |
|---|---|---|
| Migration file | SQL / JS / PY | Framework-specific migration with up/down |
| Migration log | Text | Execution status and verification results |

---

## Pre-execution Check

Before executing any migration operation, verify:

1. **Database connectivity**: Can connect to the target database.
   ```bash
   psql $DATABASE_URL -c "SELECT 1" >/dev/null 2>&1 || echo "ERROR: cannot connect"
   ```
2. **Migration framework detected**: Project uses a supported framework.
3. **Working directory correct**: Inside the project root.
4. **Backup available**: For production databases, confirm a recent backup
   exists before running migrations.

If any check fails, STOP and report to the user.

---

## Safety Boundaries

### Forbidden Operations

- MUST NEVER run a migration without first reading the migration file.
- MUST NEVER modify an already-applied migration.
- MUST NEVER run migrations on production without a tested rollback.
- MUST NEVER bypass transaction wrappers.

### Confirmation Gates

STOP and ask for explicit confirmation before:
- Running migrations on a production database
- Rolling back migrations in production
- Deleting migration files
- Modifying the migration history table

### Emergency Stop

Immediately abort if:
- The database connection fails
- A migration returns an error during execution
- The migration file contains destructive operations (DROP, DELETE) without
  explicit user confirmation
- The target database is not the intended one (check `DATABASE_URL`)

---

## Workflow

### 1. Detect Migration Framework

Read the project root to identify the migration framework:

```bash
# Check for common indicators
ls alembic.ini migrations/ knexfile.js prisma/migrations/ 2>/dev/null
```

| Indicator | Framework | Migration Directory |
|---|---|---|
| `alembic.ini` | Alembic (SQLAlchemy) | `alembic/versions/` |
| `knexfile.js` | Knex.js | `migrations/` |
| `prisma/migrations/` | Prisma | `prisma/migrations/` |
| `manage.py` + `*/migrations/` | Django | `*/migrations/` |

If no framework is detected, stop and ask the user which one they use.

### 2. Create Migration

#### Alembic (Python)

```bash
alembic revision -m "add users table"
```

Then `read` the generated file and `edit` the `upgrade()` and `downgrade()`
functions.

#### Knex.js (Node)

```bash
npx knex migrate:make add_users_table
```

Then `read` the generated file and fill in `exports.up` and `exports.down`.

#### Manual Path (No Runtime)

1. `read` an existing migration file to learn the naming convention.
2. `write` a new migration file following the same pattern:
   - Timestamp-prefixed filename (`20240115120000_add_users_table.py`)
   - `upgrade()` / `up()` function with the schema change
   - `downgrade()` / `down()` function with the rollback
3. If the framework maintains a migration registry table, `edit` it to include
the new migration (or ask the user to run the framework's register command).

### 3. Run Migrations

#### With Framework CLI

```bash
# Alembic
alembic upgrade head

# Knex
npx knex migrate:latest

# Prisma
npx prisma migrate deploy

# Django
python manage.py migrate
```

#### Manual Path

1. `read` the migration file to verify it is syntactically valid.
2. `bash` the database client to execute the migration SQL:
   ```bash
   psql $DATABASE_URL -f migrations/20240115120000_add_users_table.sql
   ```
3. Record the execution in a migration log (if the project maintains one).

### 4. Verify Migration

Always verify after running:

```bash
# Check table/column exists
psql $DATABASE_URL -c "\d users"

# Check migration registry
alembic current        # Alembic
npx knex migrate:status # Knex
```

### 5. Rollback (if needed)

```bash
# Alembic - rollback 1 step
alembic downgrade -1

# Knex
npx knex migrate:rollback

# Manual
psql $DATABASE_URL -f migrations/20240115120000_add_users_table_rollback.sql
```

---

## Hard Rules

1. MUST NEVER run a migration without first `read`-ing the migration file to
   verify its contents.
2. MUST ALWAYS create a corresponding rollback before applying a migration in
   production.
3. MUST NEVER edit a migration file that has already been run in production.
   Create a new migration instead.
4. MUST ALWAYS verify the migration ran successfully before declaring done.
5. SHOULD wrap migrations in transactions when the database supports it.

---

## Verification Checklist

- [ ] Migration framework detected correctly.
- [ ] Migration file contents reviewed before execution.
- [ ] Rollback script exists (for production migrations).
- [ ] Migration executed successfully.
- [ ] Schema verified (table/column exists as expected).
- [ ] Migration registry updated (framework tracking table).

---

## Common Pitfalls

1. **Running untrusted migrations.** Always `read` the migration before `bash`
   executes it. A bad migration can drop production data.
2. **Forgetting rollbacks.** In production, every migration needs a tested
   rollback. Test the rollback in a non-production environment first.
3. **Editing applied migrations.** Once a migration has run in any environment,
   treat it as immutable. New changes require a new migration file.
4. **Missing transaction wrappers.** Without transactions, a failed migration
   leaves the database in a half-applied state. Most frameworks handle this
   automatically; verify if using the manual path.
5. **Wrong environment.** Running `alembic upgrade head` against production
   when you meant staging. Check `DATABASE_URL` before every migration command.

---

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [Knex.js Migrations](https://knexjs.org/guide/migrations.html)
- [Prisma Migrate](https://www.prisma.io/docs/concepts/components/prisma-migrate)
- [Django Migrations](https://docs.djangoproject.com/en/stable/topics/migrations/)
- `references/migration-naming-conventions.md` — naming patterns by framework

# Understanding Flask-Migrate (Database Migrations)

> Database migrations are like **Git for your database schema** - they track and apply changes to your database structure.

---

## Table of Contents

1. [What is Flask-Migrate?](#what-is-flask-migrate)
2. [The Problem It Solves](#the-problem-it-solves)
3. [How It Works](#how-it-works)
4. [Commands Reference](#commands-reference)
5. [Real-World Example](#real-world-example)
6. [Migration Files Explained](#migration-files-explained)
7. [Benefits of Migrations](#benefits-of-migrations)

---

## What is Flask-Migrate?

**Flask-Migrate** is an extension that handles database migrations for Flask applications using **Alembic** (a database migration tool for SQLAlchemy).

### Simple Definition

> Migrations = Version control for your database structure

Just like Git tracks changes to your code files, migrations track changes to your database tables and columns.

### The Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FLASK-MIGRATE STACK                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐                                                   │
│  │   Flask-Migrate  │ ← Flask extension (what you import)               │
│  └────────┬─────────┘                                                   │
│           │                                                             │
│           ▼                                                             │
│  ┌──────────────────┐                                                   │
│  │     Alembic      │ ← The actual migration engine                     │
│  └────────┬─────────┘                                                   │
│           │                                                             │
│           ▼                                                             │
│  ┌──────────────────┐                                                   │
│  │   SQLAlchemy     │ ← Compares models to database                     │
│  └────────┬─────────┘                                                   │
│           │                                                             │
│           ▼                                                             │
│  ┌──────────────────┐                                                   │
│  │   PostgreSQL     │ ← Your actual database                            │
│  └──────────────────┘                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The Problem It Solves

### Scenario: Without Migrations 😰

You have this model in your Python code:

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
```

Your PostgreSQL database has a `users` table:

```
users
├── id (INTEGER)
├── username (VARCHAR(80))
└── email (VARCHAR(120))
```

**Now you need to add a phone number:**

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))  # ← NEW!
```

**❌ The Problem:**

-   Your Python code says `phone` exists
-   Your database still has the OLD structure (no `phone` column)
-   When you try to save a phone number → **ERROR!**

**Without migrations, you have to:**

1. Write SQL manually: `ALTER TABLE users ADD COLUMN phone VARCHAR(20);`
2. Run it on your local database
3. Remember to run it on staging database
4. Remember to run it on production database
5. Tell all your teammates to run it
6. Hope nobody forgets
7. 😱 Chaos and errors!

---

### Scenario: With Migrations 😊

```bash
# Step 1: Generate migration (detects the new column automatically)
$ flask db migrate -m "Add phone column to users"

# Step 2: Apply migration (runs the SQL for you)
$ flask db upgrade

# ✅ Done! Database now has the phone column
```

**Benefits:**

-   Automatic detection of model changes
-   SQL is generated for you
-   Same commands work everywhere (local, staging, production)
-   Changes are tracked in files (can be committed to Git)
-   Easy to undo: `flask db downgrade`

---

## How It Works

### Visual Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HOW MIGRATIONS WORK                                  │
└─────────────────────────────────────────────────────────────────────────┘

  STEP 1: You change your model
  ─────────────────────────────

  app/models/user.py:
  ┌───────────────────────────────────────┐
  │ class User(db.Model):                 │
  │     id = ...                          │
  │     username = ...                    │
  │     phone = db.Column(db.String(20))  │ ← NEW LINE
  └───────────────────────────────────────┘


  STEP 2: Generate migration
  ──────────────────────────

  $ flask db migrate -m "Add phone to users"

  Flask-Migrate:
  ┌─────────────────────────────────────────────────────────┐
  │ 1. Reads your Python models                             │
  │ 2. Connects to database, reads current structure        │
  │ 3. Compares them: "Ah! 'phone' column is missing!"      │
  │ 4. Generates migration file with the difference         │
  └─────────────────────────────────────────────────────────┘

  Creates: migrations/versions/abc123_add_phone_to_users.py


  STEP 3: Apply migration
  ───────────────────────

  $ flask db upgrade

  Flask-Migrate:
  ┌─────────────────────────────────────────────────────────┐
  │ 1. Reads migration file                                 │
  │ 2. Runs the upgrade() function                          │
  │ 3. Executes: ALTER TABLE users ADD COLUMN phone ...     │
  │ 4. Records this migration as "applied"                  │
  └─────────────────────────────────────────────────────────┘

  Database now has phone column! ✅
```

### Comparison to Git

| Git (Code Version Control) | Flask-Migrate (Database Version Control) |
| -------------------------- | ---------------------------------------- |
| `git status`               | `flask db current`                       |
| `git diff`                 | (automatic on migrate)                   |
| `git add .`                | (automatic on migrate)                   |
| `git commit -m "message"`  | `flask db migrate -m "message"`          |
| `git push`                 | `flask db upgrade`                       |
| `git revert`               | `flask db downgrade`                     |
| `git log`                  | `flask db history`                       |
| `.git/` folder             | `migrations/` folder                     |

---

## Commands Reference

### Initial Setup (Run Once)

```bash
flask db init
```

**What it does:**

-   Creates the `migrations/` folder
-   Sets up Alembic configuration
-   Only needs to be run once per project

**What it creates:**

```
migrations/
├── alembic.ini          # Alembic configuration
├── env.py               # Environment setup for migrations
├── README               # Basic info
├── script.py.mako       # Template for migration files
└── versions/            # Your migration files go here
    └── (empty initially)
```

---

### Generate Migration

```bash
flask db migrate -m "Description of changes"
```

**What it does:**

-   Compares your Python models to the database
-   Detects differences (new tables, columns, changes, deletions)
-   Creates a migration file in `migrations/versions/`

**Example output:**

```
INFO  [alembic.autogenerate.compare] Detected added column 'users.phone'
  Generating migrations/versions/a1b2c3d4_add_phone_to_users.py ... done
```

**The generated file:**

```python
# migrations/versions/a1b2c3d4_add_phone_to_users.py

"""Add phone to users

Revision ID: a1b2c3d4
Revises: 9z8y7x6w (previous migration)
Create Date: 2024-01-07 15:30:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a1b2c3d4'
down_revision = '9z8y7x6w'

def upgrade():
    """Apply the migration - add the column."""
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))

def downgrade():
    """Undo the migration - remove the column."""
    op.drop_column('users', 'phone')
```

---

### Apply Migrations

```bash
flask db upgrade
```

**What it does:**

-   Runs all pending migrations in order
-   Executes the `upgrade()` function in each
-   Updates `alembic_version` table to track what's applied

**Example:**

```
Database has: migrations 1, 2, 3
Migrations folder has: migrations 1, 2, 3, 4, 5

$ flask db upgrade
Running migration 4... done
Running migration 5... done

Database now has: migrations 1, 2, 3, 4, 5 ✅
```

---

### Undo Migration (Rollback)

```bash
flask db downgrade
```

**What it does:**

-   Reverts the last applied migration
-   Executes the `downgrade()` function

**Example:**

```
Current: migration 5 is applied

$ flask db downgrade
Reverting migration 5... done

Now at: migration 4
```

**Undo multiple:**

```bash
flask db downgrade -1   # Go back 1 migration (same as just downgrade)
flask db downgrade -2   # Go back 2 migrations
flask db downgrade base # Go back to before any migrations
```

---

### View History

```bash
flask db history
```

**Output:**

```
a1b2c3d4 -> (head), Add phone to users
9z8y7x6w -> a1b2c3d4, Add email to users
5e6f7g8h -> 9z8y7x6w, Create users table
<base> -> 5e6f7g8h, Initial migration
```

---

### View Current Version

```bash
flask db current
```

**Output:**

```
a1b2c3d4 (head)
```

This shows which migration your database is currently at.

---

### All Commands Summary

| Command                     | Purpose                               |
| --------------------------- | ------------------------------------- |
| `flask db init`             | Create migrations folder (once)       |
| `flask db migrate -m "msg"` | Generate migration from model changes |
| `flask db upgrade`          | Apply pending migrations              |
| `flask db downgrade`        | Revert last migration                 |
| `flask db history`          | Show all migrations                   |
| `flask db current`          | Show current database version         |
| `flask db heads`            | Show latest migration(s)              |
| `flask db show <revision>`  | Show details of a migration           |

---

## Real-World Example

Let's walk through a complete example of adding a feature:

### Goal: Add user profiles with bio and avatar

**Step 1: Update the model**

```python
# app/models/user.py

class User(db.Model):
    __tablename__ = 'users'

    # Existing columns
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # NEW columns for profile
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
```

**Step 2: Generate migration**

```bash
$ flask db migrate -m "Add profile fields to users"

INFO  [alembic.autogenerate.compare] Detected added column 'users.bio'
INFO  [alembic.autogenerate.compare] Detected added column 'users.avatar_url'
INFO  [alembic.autogenerate.compare] Detected added column 'users.website'
  Generating migrations/versions/abc123_add_profile_fields.py ... done
```

**Step 3: Review the migration file**

```python
# migrations/versions/abc123_add_profile_fields.py

def upgrade():
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('website', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('users', 'website')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'bio')
```

**Step 4: Apply to database**

```bash
$ flask db upgrade

INFO  [alembic.runtime.migration] Running upgrade 9z8y7x6w -> abc123, Add profile fields
```

**Step 5: Verify**

```bash
$ psql -U postgres -d flaskwithpsql -c "\d users"

         Column      |          Type          |
---------------------+------------------------+
 id                  | integer                |
 username            | character varying(80)  |
 email               | character varying(120) |
 password_hash       | character varying(256) |
 bio                 | text                   |  ← NEW
 avatar_url          | character varying(255) |  ← NEW
 website             | character varying(255) |  ← NEW
```

---

## Migration Files Explained

### Structure of a Migration File

```python
"""Add phone column to users

Revision ID: a1b2c3d4e5f6
Revises: 1234567890ab
Create Date: 2024-01-07 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = 'a1b2c3d4e5f6'          # This migration's unique ID
down_revision = '1234567890ab'      # Previous migration's ID (parent)
branch_labels = None
depends_on = None


def upgrade():
    """
    What to do when applying this migration.
    This runs when you execute: flask db upgrade
    """
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))


def downgrade():
    """
    What to do when reverting this migration.
    This runs when you execute: flask db downgrade
    """
    op.drop_column('users', 'phone')
```

### Common Operations in Migrations

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add a column
    op.add_column('users', sa.Column('phone', sa.String(20)))

    # Remove a column
    op.drop_column('users', 'old_column')

    # Rename a column
    op.alter_column('users', 'old_name', new_column_name='new_name')

    # Create a new table
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(200)),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'))
    )

    # Drop a table
    op.drop_table('old_table')

    # Add an index
    op.create_index('idx_users_email', 'users', ['email'])

    # Add a foreign key
    op.create_foreign_key('fk_posts_user', 'posts', 'users', ['user_id'], ['id'])
```

### Migration Chain

Migrations form a linked chain, each pointing to the previous one:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MIGRATION CHAIN                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │ Initial (abc123) │───▶│  Add email       │───▶│  Add phone       │   │
│  │                  │    │  (def456)        │    │  (ghi789)        │   │
│  │ down_revision:   │    │ down_revision:   │    │ down_revision:   │   │
│  │ None (first!)    │    │ abc123           │    │ def456           │   │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘   │
│         ▲                                                    │          │
│         │                                                    │          │
│       base                                                 head         │
│   (starting point)                                       (latest)       │
│                                                                         │
│  flask db downgrade: moves LEFT (reverts)                               │
│  flask db upgrade: moves RIGHT (applies)                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Benefits of Migrations

### 1. Team Collaboration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     TEAM WORKFLOW                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Developer A:                                                           │
│  ├── Adds 'phone' column to User model                                  │
│  ├── Runs: flask db migrate -m "Add phone"                              │
│  ├── Commits migration file to Git                                      │
│  └── Pushes to repository                                               │
│                                                                         │
│  Developer B:                                                           │
│  ├── Pulls from repository                                              │
│  ├── Gets the new migration file                                        │
│  ├── Runs: flask db upgrade                                             │
│  └── Database now has phone column too! ✅                              │
│                                                                         │
│  No manual SQL sharing needed!                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. Safe Deployments

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DEPLOYMENT WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Local Database:          migrations 1, 2, 3, 4, 5                      │
│  Production Database:     migrations 1, 2, 3                            │
│                                                                         │
│  On production server:                                                  │
│  $ flask db upgrade                                                     │
│                                                                         │
│  Result:                                                                │
│  ├── Migration 1, 2, 3: Already applied, skipped                        │
│  ├── Migration 4: Applied ✓                                             │
│  └── Migration 5: Applied ✓                                             │
│                                                                         │
│  Production now matches local! ✅                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Easy Rollback

```bash
# Something went wrong with the latest change?
$ flask db downgrade

# Database reverted to previous state ✅
# Fix your code, then:
$ flask db upgrade
```

### 4. Complete History

```bash
$ flask db history

abc789 -> (head), Add avatar and bio to users
def456 -> abc789, Add phone column
ghi123 -> def456, Add email verification
jkl012 -> ghi123, Create posts table
<base> -> jkl012, Initial migration - users table
```

You can see exactly what changed and when!

---

## Common Pitfalls and Solutions

### Pitfall 1: Forgetting to migrate

```
❌ Error: "Column 'phone' does not exist"

Cause: You added column to model but didn't run migrations

Fix:
$ flask db migrate -m "Add phone"
$ flask db upgrade
```

### Pitfall 2: Migration out of sync

```
❌ Error: "Target database is not up to date"

Cause: Pending migrations haven't been applied

Fix:
$ flask db upgrade
```

### Pitfall 3: Empty migration generated

```
$ flask db migrate -m "Changes"
# Creates empty migration with no changes

Cause:
- Model wasn't saved
- Model wasn't imported in create_app

Fix:
- Make sure model file is saved
- Make sure model is imported somewhere Flask can see it
```

---

## Summary

**Flask-Migrate** provides:

| Feature                 | Description                                         |
| ----------------------- | --------------------------------------------------- |
| **Automatic Detection** | Compares models to database, finds differences      |
| **Generated SQL**       | Creates the SQL for you, no manual writing          |
| **Version Control**     | Tracks all changes in migration files               |
| **Team Friendly**       | Migration files can be committed and shared via Git |
| **Rollback Support**    | Easy to undo migrations with `downgrade`            |
| **Safe Deployments**    | Same commands work on all environments              |

### Quick Reference

```bash
# First time setup
flask db init

# After changing models
flask db migrate -m "Description"
flask db upgrade

# Oops, need to undo
flask db downgrade

# Check status
flask db current
flask db history
```

---

Happy migrating! 🚀

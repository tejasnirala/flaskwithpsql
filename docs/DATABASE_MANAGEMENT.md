# Database Management Guide

> This guide explains how the `db_manage.py` script works, how to use it, and how to extend it for creating new tables, schemas, and performing other database operations.

---

## Table of Contents

1. [Overview](#overview)
2. [Script Commands](#script-commands)
3. [How the Script Works](#how-the-script-works)
4. [First Time Setup](#first-time-setup)
5. [Creating New Tables](#creating-new-tables)
6. [Migration Workflow](#migration-workflow)
7. [Working with Schemas](#working-with-schemas)
8. [Extending the Script](#extending-the-script)
9. [Common Operations](#common-operations)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### What is `db_manage.py`?

`db_manage.py` is a Python script that wraps Flask-Migrate commands and provides additional functionality for database management. It makes it easy to:

- Initialize the migrations system
- Create and apply database migrations
- Seed the database with sample data
- Reset the database (for development)

### How It Relates to Flask-Migrate

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DATABASE MANAGEMENT STACK                                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  db_manage.py     ←── Your custom script (easy to use)                  │
│       │                                                                 │
│       ▼                                                                 │
│  Flask-Migrate    ←── Flask extension that wraps Alembic                │
│       │                                                                 │
│       ▼                                                                 │
│  Alembic          ←── Database migration framework for SQLAlchemy       │
│       │                                                                 │
│       ▼                                                                 │
│  SQLAlchemy       ←── Python ORM (Object-Relational Mapping)            │
│       │                                                                 │
│       ▼                                                                 │
│  PostgreSQL       ←── Your actual database                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Script Commands

### Quick Reference

| Command             | Description                           | When to Use                 |
| ------------------- | ------------------------------------- | --------------------------- |
| `setup`             | Full setup (init + migrate + upgrade) | First time setup            |
| `init`              | Initialize migrations folder          | Only once, at project start |
| `migrate "message"` | Create new migration                  | After changing models       |
| `upgrade`           | Apply pending migrations              | After creating migrations   |
| `downgrade`         | Rollback last migration               | To undo a migration         |
| `reset`             | Drop and recreate all tables          | Development only!           |
| `seed`              | Add sample data                       | After setup, for testing    |
| `help`              | Show help message                     | When you forget commands    |

### Usage Examples

```bash
# First time setup (recommended for new projects)
python db_manage.py setup

# Create a new migration after modifying models
python db_manage.py migrate "Add posts table"

# Apply the migration
python db_manage.py upgrade

# Rollback if something went wrong
python db_manage.py downgrade

# Add sample data for testing
python db_manage.py seed

# Reset everything (CAUTION: deletes all data!)
python db_manage.py reset
```

---

## How the Script Works

### Script Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│  db_manage.py Flow                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  python db_manage.py <command>                                          │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────┐                                                        │
│  │ Parse Args  │                                                        │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Set Environment Variables                                       │   │
│  │  FLASK_APP=run.py                                                │   │
│  │  FLASK_ENV=development                                           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│         │                                                               │
│         ▼                                                               │
│  ┌────────────────────────────────────────────┐                         │
│  │  Command Router                            │                         │
│  ├────────────────────────────────────────────┤                         │
│  │ init     → flask db init                    │                         │
│  │ migrate  → flask db migrate -m "..."        │                         │
│  │ upgrade  → flask db upgrade                 │                         │
│  │ reset    → db.drop_all() + db.create_all() │                         │
│  │ seed     → Insert sample data              │                         │
│  │ setup    → init + migrate + upgrade        │                         │
│  └────────────────────────────────────────────┘                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Functions Explained

#### `run_command(command, description)`

Executes a shell command (like `flask db migrate`):

```python
def run_command(command: str, description: str = "") -> bool:
    """Run a shell command and return success status."""
    print(f"$ {command}")
    result = subprocess.run(command, shell=True, cwd=project_directory)
    return result.returncode == 0
```

#### `check_migrations_folder()`

Checks if the `migrations/` folder exists:

```python
def check_migrations_folder() -> bool:
    """Check if migrations folder exists."""
    migrations_path = os.path.join(project_dir, 'migrations')
    return os.path.exists(migrations_path)
```

#### `reset_database()`

Drops all tables and recreates them (uses app context):

```python
def reset_database():
    from app import create_app, db

    app = create_app('development')
    with app.app_context():
        db.drop_all()   # Delete all tables
        db.create_all() # Recreate from models
```

---

## First Time Setup

### Step-by-Step

```bash
# 1. Make sure PostgreSQL is running
# 2. Create the database (if not exists)
psql -U postgres -c "CREATE DATABASE flaskwithpsql;"

# 3. Update your .env file with correct credentials
# DATABASE_URL=postgresql://user:password@localhost:5432/flaskwithpsql

# 4. Run the setup
python db_manage.py setup
```

### What `setup` Does

```
python db_manage.py setup
       │
       ├── 1. Check if migrations/ exists
       │       └── If not, run: flask db init
       │
       ├── 2. Create initial migration
       │       └── flask db migrate -m "Initial migration"
       │
       └── 3. Apply migrations
               └── flask db upgrade
```

### Expected Output

```
============================================================
  🚀 Full Database Setup
============================================================

============================================================
  Initializing migrations folder
============================================================
$ flask db init

  Creating directory /path/to/migrations ... done
  Creating directory /path/to/migrations/versions ... done
  ...

✅ Initializing migrations folder completed successfully!

============================================================
  Creating migration: Initial migration
============================================================
$ flask db migrate -m "Initial migration"

INFO  [alembic.autogenerate.compare] Detected added table 'users'

✅ Creating migration: Initial migration completed successfully!

============================================================
  Applying migrations to database
============================================================
$ flask db upgrade

INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Initial migration

✅ Applying migrations to database completed successfully!

============================================================
  🎉 Database setup complete!
============================================================
```

---

## Creating New Tables

### Step 1: Create a New Model

Create a new file in `app/models/`:

```python
# app/models/post.py
from app import db
from datetime import datetime


class Post(db.Model):
    """Blog post model."""

    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    published = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign key to User
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationship
    author = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))

    def __repr__(self):
        return f'<Post {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'slug': self.slug,
            'published': self.published,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

### Step 2: Import the Model

Make sure the model is imported when the app starts. Add to `app/models/__init__.py`:

```python
# app/models/__init__.py
from app.models.user import User
from app.models.post import Post  # Add this line
```

### Step 3: Create and Apply Migration

```bash
# Create migration
python db_manage.py migrate "Add posts table"

# Apply migration
python db_manage.py upgrade
```

### Common Column Types

```python
from app import db

class Example(db.Model):
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Strings
    name = db.Column(db.String(100))           # VARCHAR(100)
    description = db.Column(db.Text)            # TEXT (unlimited)

    # Numbers
    count = db.Column(db.Integer)               # INTEGER
    price = db.Column(db.Float)                 # FLOAT
    amount = db.Column(db.Numeric(10, 2))       # DECIMAL(10, 2)

    # Boolean
    is_active = db.Column(db.Boolean, default=True)

    # Dates/Times
    created_at = db.Column(db.DateTime)         # TIMESTAMP
    birth_date = db.Column(db.Date)             # DATE
    start_time = db.Column(db.Time)             # TIME

    # JSON (PostgreSQL)
    metadata = db.Column(db.JSON)               # JSONB

    # Arrays (PostgreSQL)
    tags = db.Column(db.ARRAY(db.String))       # TEXT[]

    # Enum
    status = db.Column(db.Enum('draft', 'published', 'archived', name='status_enum'))
```

### Column Constraints

```python
# Required field
name = db.Column(db.String(100), nullable=False)

# Unique field
email = db.Column(db.String(120), unique=True)

# Default value
is_active = db.Column(db.Boolean, default=True)

# Auto-update timestamp
updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# Index for faster queries
email = db.Column(db.String(120), index=True)

# Composite index
__table_args__ = (
    db.Index('idx_user_email_name', 'email', 'name'),
)
```

---

## Migration Workflow

### The Standard Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MIGRATION WORKFLOW                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. MODIFY MODELS                                                       │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │ Edit app/models/user.py                                     │     │
│     │ Add new column, change type, etc.                           │     │
│     └─────────────────────────────────────────────────────────────┘     │
│                              │                                          │
│                              ▼                                          │
│  2. CREATE MIGRATION                                                    │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │ python db_manage.py migrate "Add phone to users"            │     │
│     │                                                             │     │
│     │ Creates: migrations/versions/abc123_add_phone_to_users.py   │     │
│     └─────────────────────────────────────────────────────────────┘     │
│                              │                                          │
│                              ▼                                          │
│  3. REVIEW MIGRATION (optional but recommended)                         │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │ Open migrations/versions/abc123_add_phone_to_users.py       │     │
│     │ Check upgrade() and downgrade() functions                   │     │
│     └─────────────────────────────────────────────────────────────┘     │
│                              │                                          │
│                              ▼                                          │
│  4. APPLY MIGRATION                                                     │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │ python db_manage.py upgrade                                 │     │
│     │                                                             │     │
│     │ Runs upgrade() → Changes applied to database                │     │
│     └─────────────────────────────────────────────────────────────┘     │
│                              │                                          │
│                              ▼                                          │
│  5. (IF NEEDED) ROLLBACK                                                │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │ python db_manage.py downgrade                               │     │
│     │                                                             │     │
│     │ Runs downgrade() → Changes reverted                         │     │
│     └─────────────────────────────────────────────────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Example: Adding a Column

**Step 1: Modify the model**

```python
# app/models/user.py
class User(db.Model):
    # ... existing columns ...
    phone = db.Column(db.String(20))  # NEW COLUMN
```

**Step 2: Create migration**

```bash
python db_manage.py migrate "Add phone column to users"
```

**Step 3: Check the generated migration**

```python
# migrations/versions/abc123_add_phone_column_to_users.py
def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone')
```

**Step 4: Apply migration**

```bash
python db_manage.py upgrade
```

---

## Working with Schemas

### What are Schemas?

PostgreSQL schemas are like namespaces for tables. The default schema is `public`.

```
Database: flaskwithpsql
├── Schema: public (default)
│   ├── users
│   ├── posts
│   └── comments
├── Schema: analytics
│   ├── page_views
│   └── events
└── Schema: audit
    └── logs
```

### Creating Tables in a Custom Schema

```python
# app/models/analytics.py
from app import db

class PageView(db.Model):
    """Analytics page view model."""

    __tablename__ = 'page_views'
    __table_args__ = {'schema': 'analytics'}  # Custom schema

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=db.func.now())
```

### Creating the Schema

Alembic/Flask-Migrate doesn't auto-create schemas. Add to your migration:

```python
# In a migration file
from alembic import op

def upgrade():
    # Create schema if not exists
    op.execute('CREATE SCHEMA IF NOT EXISTS analytics')

    # Create table in that schema
    op.create_table(
        'page_views',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('url', sa.String(500), nullable=False),
        schema='analytics'
    )

def downgrade():
    op.drop_table('page_views', schema='analytics')
    op.execute('DROP SCHEMA IF EXISTS analytics')
```

---

## Extending the Script

### Adding New Commands

To add a new command to `db_manage.py`:

```python
# 1. Create the function
def my_custom_command():
    """Description of what this does."""
    from app import create_app, db

    app = create_app('development')
    with app.app_context():
        # Your custom logic here
        result = db.session.execute("SELECT version()")
        print(f"PostgreSQL version: {result.fetchone()[0]}")

# 2. Add to the commands dictionary in main()
commands = {
    'init': init_migrations,
    'migrate': lambda: create_migration(...),
    # ... existing commands ...
    'version': my_custom_command,  # ADD THIS
}
```

### Example: Add a `status` Command

```python
def show_status():
    """Show database and migration status."""
    from app import create_app, db

    app = create_app('development')

    print("\n📊 Database Status")
    print("=" * 50)

    with app.app_context():
        # Check connection
        try:
            result = db.session.execute("SELECT 1")
            print("✅ Database connection: OK")
        except Exception as e:
            print(f"❌ Database connection: FAILED ({e})")
            return

        # Get PostgreSQL version
        result = db.session.execute("SELECT version()")
        version = result.fetchone()[0].split(',')[0]
        print(f"📌 {version}")

        # List tables
        result = db.session.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
        """)
        tables = [row[0] for row in result]
        print(f"\n📋 Tables ({len(tables)}):")
        for table in tables:
            count_result = db.session.execute(f"SELECT COUNT(*) FROM {table}")
            count = count_result.fetchone()[0]
            print(f"   • {table}: {count} rows")

    # Check migrations
    if check_migrations_folder():
        print("\n📁 Migrations: Initialized")
        run_command("flask db current", "Current migration")
    else:
        print("\n📁 Migrations: Not initialized")

# Add to commands dictionary:
commands['status'] = show_status
```

### Example: Add a `backup` Command

```python
def backup_database():
    """Create a database backup."""
    import datetime

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backups/backup_{timestamp}.sql"

    # Create backups directory
    os.makedirs('backups', exist_ok=True)

    # Get database URL from environment
    db_url = os.environ.get('DATABASE_URL', '')

    # Parse URL to get connection details
    # For simplicity, using pg_dump with connection string
    run_command(
        f'pg_dump "{db_url}" > {backup_file}',
        f"Creating backup: {backup_file}"
    )

    print(f"\n✅ Backup saved to: {backup_file}")
```

---

## Common Operations

### Check Current Migration

```bash
# Using Flask-Migrate directly
flask db current

# Or add to db_manage.py
python db_manage.py status
```

### View Migration History

```bash
flask db history
```

### Create Empty Migration

For complex changes that auto-detection can't handle:

```bash
flask db revision -m "Custom migration"
```

Then edit the generated file manually.

### Running Raw SQL

```python
def run_sql():
    """Run custom SQL."""
    from app import create_app, db

    app = create_app('development')
    with app.app_context():
        # Example: Add an index
        db.session.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_users_email ON users (email);
        """)
        db.session.commit()
        print("✅ SQL executed successfully")
```

---

## Troubleshooting

### Common Issues

#### 1. "No changes detected"

```bash
$ python db_manage.py migrate "My changes"
INFO  [alembic.autogenerate.compare] No changes in schema detected.
```

**Causes:**

- Model not imported in `app/models/__init__.py`
- No actual changes to the model
- Changes already in a previous migration

**Solution:**

```python
# Make sure model is imported in app/models/__init__.py
from app.models.new_model import NewModel
```

#### 2. "Target database is not up to date"

```bash
ERROR [alembic.util.messaging] Target database is not up to date.
```

**Solution:**

```bash
python db_manage.py upgrade  # Apply pending migrations first
```

#### 3. "Can't locate revision"

```bash
FAILED: Can't locate revision identified by 'abc123'
```

**Solution:**

```bash
# Reset the migration head
flask db stamp head

# Then run upgrade
python db_manage.py upgrade
```

#### 4. Database Connection Error

```bash
sqlalchemy.exc.OperationalError: could not connect to server
```

**Check:**

1. Is PostgreSQL running?
2. Are credentials in `.env` correct?
3. Does the database exist?

```bash
# Check PostgreSQL status
pg_isready

# Connect manually to test
psql -U postgres -d flaskwithpsql
```

### Reset Everything (Nuclear Option)

If migrations are completely broken:

```bash
# 1. Delete migrations folder
rm -rf migrations/

# 2. Drop and recreate database
psql -U postgres -c "DROP DATABASE flaskwithpsql;"
psql -U postgres -c "CREATE DATABASE flaskwithpsql;"

# 3. Start fresh
python db_manage.py setup
```

---

## Summary

### Quick Command Reference

```bash
# First time
python db_manage.py setup

# After changing models
python db_manage.py migrate "Description"
python db_manage.py upgrade

# Rollback
python db_manage.py downgrade

# Development helpers
python db_manage.py seed   # Add sample data
python db_manage.py reset  # Start fresh (deletes data!)
```

### Workflow Checklist

- [ ] Create/modify model in `app/models/`
- [ ] Import model in `app/models/__init__.py`
- [ ] Run `python db_manage.py migrate "Description"`
- [ ] Review generated migration file
- [ ] Run `python db_manage.py upgrade`
- [ ] Test your changes

---

Happy database managing! 🗄️

# Database Reset Functions - Line by Line Explanation

This document provides a detailed, line-by-line explanation of the three reset functions in `db_manage.py`.

---

## Table of Contents

1. [reset_database()](#1-reset_database)
2. [reset_schema()](#2-reset_schema)
3. [reset_table()](#3-reset_table)
4. [Key Concepts](#key-concepts)

---

## 1. `reset_database()`

**Purpose:** Drop ALL tables in the database and recreate them. This is schema-aware, meaning it will also recreate any custom schemas used by your models.

**Usage:**

```bash
python db_manage.py reset
```

### Line-by-Line Breakdown

```python
def reset_database():
```

- Defines the function with no parameters. This function operates on the entire database.

---

```python
    """Drop all tables and recreate (DANGEROUS!).

    This function is schema-aware and will:
    1. Detect all custom schemas used by models
    2. Drop all tables
    3. Recreate schemas (if any were used)
    4. Recreate all tables
    """
```

- **Docstring**: Documents what the function does. This appears when you use `help(reset_database)` or in IDE tooltips.

---

```python
    print("\n" + "!" * 60)
    print("  ⚠️  WARNING: This will DELETE ALL DATA!")
    print("!" * 60)
```

- **Visual Warning**: Prints a prominent warning box made of 60 exclamation marks.
- `"\n"` adds a blank line before the warning.
- `"!" * 60` creates a string of 60 `!` characters (Python string multiplication).

---

```python
    confirm = input("\nType 'yes' to confirm: ")
    if confirm.lower() != "yes":
        print("❌ Aborted.")
        return False
```

- **Safety Confirmation**: Asks the user to type "yes" to proceed.
- `input()` - Built-in Python function that reads user input from the terminal.
- `.lower()` - Converts input to lowercase (so "YES", "Yes", "yes" all work).
- If user doesn't type "yes", the function prints "Aborted" and returns `False` (exits early).

---

```python
    # Import here to avoid circular imports
    from app import create_app, db
```

- **Lazy Import**: Imports Flask app factory and SQLAlchemy `db` object.
- **Why here?** To avoid circular imports. If we import at the top of the file, and `app/__init__.py` imports something from this file, we'd get an import error.

---

```python
    app = create_app("development")
```

- **Creates Flask Application**: Calls the app factory with "development" config.
- This gives us a configured Flask app instance with database connection settings.

---

```python
    with app.app_context():
```

- **Application Context**: Opens a Flask application context.
- **Why needed?** SQLAlchemy operations require an active app context to know which database to connect to.
- `with` statement ensures the context is properly closed when done (even if an error occurs).

---

```python
        # Detect all custom schemas from model metadata
        schemas = set()
```

- **Initialize Empty Set**: `set()` creates an empty set to store unique schema names.
- **Why set?** Sets automatically remove duplicates. If 10 tables use the same schema, it's stored only once.

---

```python
        for table in db.metadata.tables.values():
            if table.schema:
                schemas.add(table.schema)
```

- **Iterate Over All Tables**: `db.metadata.tables` is a dictionary of all tables registered with SQLAlchemy.
- `.values()` returns just the table objects (not the keys).
- `table.schema` - Each table has a `schema` attribute (e.g., `"analytics"` or `None` for public schema).
- `if table.schema:` - Only add if schema is not `None` (i.e., it's a custom schema).
- `.add()` - Adds the schema name to the set.

---

```python
        if schemas:
            print(f"\n📋 Detected custom schemas: {', '.join(schemas)}")
```

- **Display Detected Schemas**: If any custom schemas were found, print them.
- `', '.join(schemas)` - Joins all schema names with comma + space (e.g., `"analytics, reporting"`).

---

```python
        print("\n🗑️  Dropping all tables...")
        db.drop_all()
        print("✅ All tables dropped.")
```

- **Drop All Tables**: `db.drop_all()` is a SQLAlchemy method that:
  - Drops all tables registered in `db.metadata`
  - Drops them in the correct order (respecting foreign key constraints)
  - Works across all schemas

---

```python
        # Recreate custom schemas if any exist
        if schemas:
            print("\n🏗️  Recreating schemas...")
            for schema in schemas:
```

- **Recreate Schemas**: Only runs if custom schemas were detected.
- Iterates over each schema name in the set.

---

```python
                try:
                    db.session.execute(
                        db.text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
                    )
                    print(f"  ✓ Created schema: {schema}")
```

- **Execute Raw SQL**: `db.session.execute()` runs raw SQL commands.
- `db.text()` - Wraps the SQL string, telling SQLAlchemy it's raw SQL (not an ORM operation).
- `CREATE SCHEMA IF NOT EXISTS` - PostgreSQL command to create a schema only if it doesn't already exist.
- `"{schema}"` - Double quotes around schema name handle special characters and reserved words.

---

```python
                except Exception as e:
                    error_msg = str(e).lower()
                    if "already exists" in error_msg:
                        print(f"  ✓ Schema '{schema}' already exists, skipping.")
                    elif "permission" in error_msg or "denied" in error_msg:
                        print(f"  ❌ Permission denied creating schema '{schema}': {e}")
                        db.session.rollback()
                        return False
                    else:
                        print(f"  ❌ Error creating schema '{schema}': {e}")
                        db.session.rollback()
                        return False
```

- **Smart Error Handling**: The error handling now distinguishes between different error types:
  - `str(e).lower()` - Converts the error message to lowercase for case-insensitive matching.
  - `"already exists" in error_msg` - If schema exists, just skip it (not a real error).
  - `"permission" or "denied"` - Permission errors are fatal, so we rollback and exit.
  - All other errors are also treated as fatal.
  - `db.session.rollback()` - Undoes any pending changes to avoid database inconsistency.

**Why this matters**: A generic `except` that always says "might already exist" would hide real errors like permission denied, connection issues, or disk full errors.

---

```python
            db.session.commit()
            print("✅ Schemas recreated.")
```

- **Commit Transaction**: `db.session.commit()` saves all changes to the database.
- Without this, the schema creation wouldn't be persisted.

---

```python
        print("\n🏗️  Creating all tables...")
        db.create_all()
        print("✅ All tables created.")
```

- **Create All Tables**: `db.create_all()` is a SQLAlchemy method that:
  - Creates all tables registered in `db.metadata`
  - Creates them in the correct order (respecting foreign key dependencies)
  - Includes indexes, constraints, etc.

---

```python
    return True
```

- **Return Success**: Returns `True` to indicate the operation completed successfully.

---

## 2. `reset_schema()`

**Purpose:** Drop and recreate a SPECIFIC schema (and all tables within it).

**Usage:**

```bash
python db_manage.py reset-schema analytics
```

### Line-by-Line Breakdown

```python
def reset_schema(schema_name: str):
```

- **Type Hint**: `schema_name: str` indicates this parameter should be a string.
- Type hints are optional in Python but improve code readability and IDE support.

---

```python
    """Drop and recreate a specific schema (DANGEROUS!)."""
```

- **Docstring**: Brief description of the function's purpose.

---

```python
    if not schema_name:
        print("❌ Please provide a schema name.")
        print("Usage: python db_manage.py reset-schema <schema_name>")
        return False
```

- **Input Validation**: Checks if `schema_name` is empty or `None`.
- `if not schema_name:` - In Python, empty strings (`""`) and `None` are "falsy".
- Shows usage help and returns `False` early if no name provided.

---

```python
    print("\n" + "!" * 60)
    print(f"  ⚠️  WARNING: This will DELETE ALL DATA in schema '{schema_name}'!")
    print("!" * 60)
```

- **Dynamic Warning**: Uses f-string to include the schema name in the warning.

---

```python
    confirm = input("\nType 'yes' to confirm: ")
    if confirm.lower() != "yes":
        print("❌ Aborted.")
        return False
```

- **Safety Confirmation**: Same pattern as `reset_database()`.

---

```python
    from app import create_app, db

    app = create_app("development")

    with app.app_context():
```

- **Same setup as reset_database()**: Import, create app, open context.

---

```python
        print(f"\n🗑️  Dropping schema '{schema_name}'...")
        try:
            db.session.execute(
                db.text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            )
            db.session.commit()
            print(f"✅ Schema '{schema_name}' dropped.")
```

- **Drop Schema with CASCADE**:
  - `DROP SCHEMA IF EXISTS` - Delete the schema if it exists (no error if it doesn't).
  - `CASCADE` - Also drops all objects (tables, views, functions) inside the schema.
  - Without `CASCADE`, the command would fail if the schema contains any objects.

---

```python
            print(f"\n🏗️  Creating schema '{schema_name}'...")
            db.session.execute(db.text(f'CREATE SCHEMA "{schema_name}"'))
            db.session.commit()
            print(f"✅ Schema '{schema_name}' created.")
```

- **Create Fresh Schema**: Creates an empty schema with the same name.
- Note: No `IF NOT EXISTS` here because we just dropped it, so we know it doesn't exist.

---

```python
            # Recreate tables in this schema
            print(f"\n🏗️  Recreating tables in schema '{schema_name}'...")
            # Get all tables that belong to this schema and recreate them
            for table in db.metadata.tables.values():
                if table.schema == schema_name:
                    table.create(db.engine, checkfirst=True)
                    print(f"  ✓ Created table: {table.name}")
```

- **Recreate Tables Selectively**:
  - Iterates over all tables in metadata.
  - `if table.schema == schema_name:` - Only process tables that belong to this specific schema.
  - `table.create(db.engine, checkfirst=True)` - Creates the individual table.
    - `db.engine` - The database connection engine.
    - `checkfirst=True` - Only creates if table doesn't exist (safety check).

---

```python
            print(f"\n✅ Schema '{schema_name}' reset complete!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error resetting schema: {e}")
            return False
```

- **Error Handling**:
  - `db.session.rollback()` - Undo any partial changes if an error occurs.
  - This prevents the database from being in an inconsistent state.

---

```python
    return True
```

- **Return Success**: Indicates successful completion.

---

## 3. `reset_table()`

**Purpose:** Drop and recreate a SINGLE table.

**Usage:**

```bash
python db_manage.py reset-table users
```

### Line-by-Line Breakdown

```python
def reset_table(table_name: str):
    """Drop and recreate a specific table (DANGEROUS!)."""
    if not table_name:
        print("❌ Please provide a table name.")
        print("Usage: python db_manage.py reset-table <table_name>")
        return False
```

- **Same pattern**: Input validation with helpful usage message.

---

```python
    print("\n" + "!" * 60)
    print(f"  ⚠️  WARNING: This will DELETE ALL DATA in table '{table_name}'!")
    print("!" * 60)

    confirm = input("\nType 'yes' to confirm: ")
    if confirm.lower() != "yes":
        print("❌ Aborted.")
        return False
```

- **Warning and Confirmation**: Same safety pattern.

---

```python
    from app import create_app, db

    app = create_app("development")

    with app.app_context():
```

- **Standard Setup**: App creation and context.

---

```python
        # Find the table in metadata
        target_table = None
        for table in db.metadata.tables.values():
            if table.name == table_name:
                target_table = table
                break
```

- **Table Lookup**:
  - Initialize `target_table` to `None` (not found yet).
  - Loop through all tables in metadata.
  - `if table.name == table_name:` - Check if this is the table we're looking for.
  - `break` - Stop searching once found (optimization).

---

```python
        if target_table is None:
            print(f"\n❌ Table '{table_name}' not found in the model metadata.")
            print("\nAvailable tables:")
            for table in db.metadata.tables.values():
                schema_prefix = f"{table.schema}." if table.schema else ""
                print(f"  - {schema_prefix}{table.name}")
            return False
```

- **Table Not Found Handling**:
  - If table wasn't found, show an error.
  - **Helpful Feature**: Lists all available tables so user can see correct names.
  - `schema_prefix` - Shows `schema.table` format for tables in custom schemas, just `table` for public schema.
  - Returns `False` early.

---

```python
        try:
            print(f"\n🗑️  Dropping table '{table_name}'...")
            target_table.drop(db.engine, checkfirst=True)
            print(f"✅ Table '{table_name}' dropped.")
```

- **Drop Table**:
  - `target_table.drop()` - SQLAlchemy Table method to drop the table.
  - `db.engine` - Database connection to use.
  - `checkfirst=True` - Only drop if table exists (prevents error if already gone).

---

```python
            print(f"\n🏗️  Creating table '{table_name}'...")
            target_table.create(db.engine, checkfirst=True)
            print(f"✅ Table '{table_name}' created.")

            print(f"\n✅ Table '{table_name}' reset complete!")
```

- **Create Table**:
  - `target_table.create()` - Creates the table using SQLAlchemy's schema definition.
  - Includes all columns, indexes, constraints, etc. from the model.

---

```python
        except Exception as e:
            print(f"\n❌ Error resetting table: {e}")
            return False

    return True
```

- **Error Handling**: Catch and report any errors, return appropriate boolean.

---

## Key Concepts

### 1. SQLAlchemy Metadata (`db.metadata`) - Deep Dive

The **metadata** is a collection of all table definitions registered with SQLAlchemy. When you define a model like:

```python
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
```

SQLAlchemy automatically registers this table in `db.metadata.tables`.

#### Key Insight: Metadata ≠ Database

`db.metadata.tables` is populated from your **Python model definitions**, **NOT** from the actual database!

#### How It Works

**Step 1: You Define Models in Python**

```python
# app/models/user.py
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

# app/models/metric.py
class Metric(db.Model):
    __tablename__ = 'metrics'
    __table_args__ = {'schema': 'analytics'}  # Custom schema
    id = db.Column(db.Integer, primary_key=True)
```

**Step 2: SQLAlchemy Registers Them in Metadata**

When Python **imports** these model files, SQLAlchemy automatically registers the table definitions:

```python
# This happens automatically when models are imported:
db.metadata.tables = {
    'users': Table('users', schema=None, ...),
    'analytics.metrics': Table('metrics', schema='analytics', ...)
}
```

**Step 3: Metadata is the "Blueprint"**

| Component       | What It Contains                         | Source               |
| --------------- | ---------------------------------------- | -------------------- |
| `db.metadata`   | Table **blueprints** (what SHOULD exist) | Python model classes |
| Actual Database | Tables that **actually** exist           | PostgreSQL           |

#### Visual Explanation

```
┌─────────────────────────────────────┐
│         Python Code (Models)        │
│  class User(db.Model): ...          │
│  class Metric(db.Model): ...        │
└──────────────┬──────────────────────┘
               │ (import)
               ▼
┌────────────────────────────────────────┐
│         db.metadata.tables             │
│  'users' → Table blueprint             │
│  'analytics.metrics' → Table blueprint │
│                                        │
│  ⚡ Lives in MEMORY (Python)            │
│  ✅ Always available                   │
│  📋 Knows schema, columns, etc.        │
└──────────────┬─────────────────────────┘
               │
               │ db.create_all() / db.drop_all()
               ▼
┌───────────────────────────────────────┐
│         PostgreSQL Database           │
│                                       │
│  After DROP: Empty! No tables!        │
│  After CREATE: Tables recreated!      │
└───────────────────────────────────────┘
```

#### Why This Matters for Reset Functions

Even after you run:

```python
db.drop_all()  # Deletes all tables from PostgreSQL
```

The `db.metadata.tables` **still contains**:

- Table names
- Column definitions
- Schema names
- Indexes, constraints, etc.

**Because metadata comes from your Python code, not the database!**

#### In `reset_schema()` Example:

```python
# 1. Drop schema from PostgreSQL (tables gone from DB)
db.session.execute(db.text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))

# 2. Create fresh schema in PostgreSQL
db.session.execute(db.text(f'CREATE SCHEMA "{schema_name}"'))

# 3. Recreate tables using the BLUEPRINT from metadata
for table in db.metadata.tables.values():        # ← Still has all table definitions!
    if table.schema == schema_name:              # ← Still knows the schema!
        table.create(db.engine, checkfirst=True)  # ← Creates from blueprint
```

#### Quick Reference

| Question                                 | Answer                                           |
| ---------------------------------------- | ------------------------------------------------ |
| Where does `db.metadata` get table info? | From your Python model classes                   |
| Does dropping tables affect metadata?    | **No!** Metadata is in memory                    |
| Why does reset work after `DROP`?        | Metadata is the blueprint, not the actual tables |
| What if I delete a model class?          | Then it won't be in metadata anymore             |

### 2. Application Context (`app.app_context()`)

Flask uses contexts to manage request-specific and app-specific data. SQLAlchemy needs the app context to:

- Know which database configuration to use
- Access `current_app` and other Flask globals

### 3. Understanding `db.engine` (Deep Dive)

The **Engine** is SQLAlchemy's core component that manages the **database connection**. Think of it as the "gateway" between your Python code and the actual PostgreSQL database.

#### Analogy 🚗

| Component       | Real-World Analogy                                                     |
| --------------- | ---------------------------------------------------------------------- |
| `db.engine`     | The **car engine** - powers everything but you don't drive it directly |
| `db.session`    | The **steering wheel** - what you use day-to-day for driving           |
| Connection Pool | The **fuel tank** - stores and manages available connections           |

#### What `db.engine` Does

**1. Manages the Connection Pool**

```python
# Engine maintains a pool of database connections
# Instead of opening/closing connections for each query,
# connections are reused from the pool
```

| Without Pool                         | With Pool (Engine)                                |
| ------------------------------------ | ------------------------------------------------- |
| Open connection → Query → Close      | Get connection from pool → Query → Return to pool |
| Slow (connection overhead each time) | Fast (connections are reused)                     |

**2. Executes DDL Commands (Schema Operations)**

DDL = Data Definition Language (CREATE, DROP, ALTER)

```python
# These operations use db.engine directly:
table.create(db.engine, checkfirst=True)    # Create a table
table.drop(db.engine, checkfirst=True)      # Drop a table
db.create_all()                            # Internally uses engine
db.drop_all()                              # Internally uses engine
```

**3. Converts SQLAlchemy to Database-Specific SQL**

The engine knows you're using PostgreSQL and translates accordingly:

```python
# SQLAlchemy ORM code:
User.query.filter(User.name == 'John')

# Engine translates to PostgreSQL:
# SELECT * FROM users WHERE name = 'John'

# If you were using MySQL, same Python code would generate MySQL-specific SQL
```

#### `db.engine` vs `db.session` Comparison

| Aspect           | `db.engine`                  | `db.session`                |
| ---------------- | ---------------------------- | --------------------------- |
| **Level**        | Low-level (raw connections)  | High-level (ORM operations) |
| **Use Case**     | DDL, raw SQL, schema changes | CRUD operations on models   |
| **Transaction**  | No automatic transaction     | Auto-manages transactions   |
| **Typical User** | Framework/advanced users     | Regular application code    |

**Example Code:**

```python
# db.session - For everyday ORM operations
user = User(name="John")
db.session.add(user)
db.session.commit()

# db.engine - For schema/DDL operations
from sqlalchemy import inspect
inspector = inspect(db.engine)
tables = inspector.get_table_names()  # List all tables
```

#### Why `db.engine` in `reset_table()`?

```python
target_table.drop(db.engine, checkfirst=True)
target_table.create(db.engine, checkfirst=True)
```

**Why `db.engine` here and not `db.session`?**

1. **DDL operations** (CREATE/DROP TABLE) aren't typical ORM operations
2. The `Table.create()` and `Table.drop()` methods require direct engine access
3. These operations execute **immediately** without needing `commit()`

#### Inside the Engine (Architecture)

```
┌─────────────────────────────────────────────────┐
│                   db.engine                     │
├─────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────────────┐    │
│  │   Dialect   │    │   Connection Pool    │    │
│  │ (PostgreSQL)│    │  ┌────┐ ┌────┐ ┌────┐│    │
│  │             │    │  │conn│ │conn│ │conn││    │
│  └─────────────┘    │  └────┘ └────┘ └────┘│    │
│                     └──────────────────────┘    │
├─────────────────────────────────────────────────┤
│  Connection URL:                                │
│  postgresql://user:pass@localhost:5432/mydb     │
└─────────────────────────────────────────────────┘
```

| Component           | Purpose                                                  |
| ------------------- | -------------------------------------------------------- |
| **Dialect**         | Knows how to "speak" PostgreSQL (vs MySQL, SQLite, etc.) |
| **Connection Pool** | Maintains 5-10 reusable connections                      |
| **URL**             | Contains host, port, database name, credentials          |

#### Quick Summary

| Question                           | Answer                                         |
| ---------------------------------- | ---------------------------------------------- |
| What is `db.engine`?               | The core connection manager to the database    |
| When do I use it?                  | For DDL (CREATE/DROP) and low-level operations |
| Is it required for normal queries? | No, use `db.session` for CRUD                  |
| Why does `table.create()` need it? | DDL operations need direct database access     |

### 4. `checkfirst=True`

This parameter makes operations **idempotent** (safe to run multiple times):

- `table.create(checkfirst=True)` - Only creates if table doesn't exist
- `table.drop(checkfirst=True)` - Only drops if table exists

### 5. CASCADE in PostgreSQL

When dropping a schema:

- **Without CASCADE**: Fails if schema contains any objects
- **With CASCADE**: Drops schema AND all objects inside it

```sql
DROP SCHEMA analytics CASCADE;  -- Drops schema + all tables, views, etc.
```

---

## Summary Table

| Function           | Scope      | Handles Schemas? | Use Case                |
| ------------------ | ---------- | ---------------- | ----------------------- |
| `reset_database()` | Everything | ✅ Yes           | Complete database reset |
| `reset_schema()`   | One schema | ✅ Yes           | Reset specific schema    |
| `reset_table()`    | One table  | N/A              | Reset specific table     |

---

## Frequently Asked Questions (FAQ)

### Q1: Does `reset_database()` handle tables in the public schema?

**Yes, absolutely!** ✅

The `db.drop_all()` and `db.create_all()` methods work on ALL tables in the metadata, regardless of which schema they belong to:

| Table Type                                   | `db.drop_all()` | `db.create_all()` |
| -------------------------------------------- | --------------- | ----------------- |
| Public schema (`table.schema = None`)        | ✅ Drops        | ✅ Creates        |
| Custom schema (`table.schema = "analytics"`) | ✅ Drops        | ✅ Creates        |

The schema detection loop only collects **custom schemas** that need to be recreated:

```python
for table in db.metadata.tables.values():
    if table.schema:  # Only adds if NOT None (custom schemas)
        schemas.add(table.schema)
```

Tables in the public schema have `table.schema = None`, so they aren't added to the `schemas` set. But they're still handled by `db.drop_all()` and `db.create_all()`.

### Q2: What happens if I have both public and custom schema tables?

**Example models:**

```python
class User(db.Model):  # Public schema (table.schema = None)
    __tablename__ = 'users'

class Metric(db.Model):  # Custom schema
    __tablename__ = 'metrics'
    __table_args__ = {'schema': 'analytics'}
```

**What `reset_database()` does:**

| Step | Action            | Tables Affected                       |
| ---- | ----------------- | ------------------------------------- |
| 1    | Detect schemas    | Finds `analytics` only                |
| 2    | `db.drop_all()`   | Drops `users` + `analytics.metrics`   |
| 3    | Create schemas    | Creates `analytics` schema            |
| 4    | `db.create_all()` | Creates `users` + `analytics.metrics` |

### Q3: Why not use a generic error handler?

A generic error handler like this is **dangerous**:

```python
# ❌ BAD: Hides real errors
except Exception as e:
    print(f"Schema might already exist: {e}")
```

This would print "might already exist" even for:

- Permission denied errors
- Connection timeout errors
- Disk full errors
- Invalid schema names

The improved smart error handling **distinguishes between error types**:

| Error Type            | Behavior              |
| --------------------- | --------------------- |
| Schema already exists | ✓ Skip (not an error) |
| Permission denied     | ❌ Stop and rollback  |
| Other errors          | ❌ Stop and rollback  |

---

_Last Updated: January 9, 2026_

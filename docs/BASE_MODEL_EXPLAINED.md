# Base Model Pattern in SQLAlchemy

## Table of Contents

1. [Introduction](#introduction)
2. [Why Use a Base Model?](#why-use-a-base-model)
3. [What We Implemented](#what-we-implemented)
4. [How It Works Internally](#how-it-works-internally)
5. [Code Breakdown](#code-breakdown)
6. [Inheritance Flow Diagram](#inheritance-flow-diagram)
7. [The Abstract Class Concept](#the-abstract-class-concept)
8. [Timestamp Handling Deep Dive](#timestamp-handling-deep-dive)
9. [Soft Delete Pattern](#soft-delete-pattern)
10. [How to Create a New Model](#how-to-create-a-new-model)
11. [Common Pitfalls & Best Practices](#common-pitfalls--best-practices)
12. [Comparison: Before vs After](#comparison-before-vs-after)

---

## Introduction

In production applications, most database tables share common fields like:

- `id` - A unique identifier (primary key)
- `created_at` - When the record was created
- `updated_at` - When the record was last modified
- `is_deleted` - A flag for soft deletion

Instead of defining these fields in **every single model**, we create a **Base Model** that contains these common fields. All other models then **inherit** from this base model.

This is a widely-used pattern in professional codebases called the **Abstract Base Class Pattern** or **Mixin Pattern**.

---

## Why Use a Base Model?

### ✅ Benefits

| Benefit                         | Explanation                                                         |
| ------------------------------- | ------------------------------------------------------------------- |
| **DRY (Don't Repeat Yourself)** | Define common fields ONCE, not in every model                       |
| **Consistency**                 | All tables have the exact same field names, types, and behaviors    |
| **Maintainability**             | Change a common field in ONE place, and it affects ALL models       |
| **Reduced Bugs**                | No risk of typos or slight variations in field definitions          |
| **Cleaner Code**                | Models only contain their unique fields, making them easier to read |
| **Standardization**             | Every developer knows where to find common fields                   |

### ❌ Without Base Model (The Problem)

```python
# user.py
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    # ... user fields

# product.py
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Duplicated!
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    # ... product fields

# order.py - Imagine doing this for 50+ models!
```

### ✅ With Base Model (The Solution)

```python
# base.py
class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, ...)
    updated_at = db.Column(db.DateTime, ...)
    is_deleted = db.Column(db.Boolean, ...)

# user.py - Much cleaner!
class User(BaseModel):
    # id, created_at, updated_at, is_deleted are inherited
    username = db.Column(db.String(80), ...)
    email = db.Column(db.String(120), ...)

# product.py
class Product(BaseModel):
    name = db.Column(db.String(100), ...)
    price = db.Column(db.Numeric, ...)
```

---

## What We Implemented

### File Structure

```
app/
└── models/
    ├── __init__.py      # Exports all models
    ├── base.py          # NEW: BaseModel class
    ├── user.py          # Updated: Inherits from BaseModel
    └── user_temp.py     # Updated: Inherits from BaseModel
```

### BaseModel Fields

| Field        | Type                      | Description                                 |
| ------------ | ------------------------- | ------------------------------------------- |
| `id`         | `Integer`                 | Auto-incrementing primary key               |
| `created_at` | `DateTime(timezone=True)` | UTC timestamp when record was created       |
| `updated_at` | `DateTime(timezone=True)` | UTC timestamp when record was last modified |
| `is_deleted` | `Boolean`                 | Soft delete flag (default: `False`)         |

### BaseModel Methods

| Method           | Description                           |
| ---------------- | ------------------------------------- |
| `soft_delete()`  | Sets `is_deleted = True`              |
| `restore()`      | Sets `is_deleted = False`             |
| `to_base_dict()` | Returns dictionary with common fields |
| `__repr__()`     | Default string representation         |

---

## How It Works Internally

### Python Inheritance Basics

When `class User(BaseModel)` is defined:

1. Python creates a new class called `User`
2. `User` inherits ALL attributes and methods from `BaseModel`
3. `User` can add its own attributes or override inherited ones

```
┌─────────────────────────────────────────────────────────────┐
│                        BaseModel                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Attributes:                                          │  │
│  │    - id                                               │  │
│  │    - created_at                                       │  │
│  │    - updated_at                                       │  │
│  │    - is_deleted                                       │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │  Methods:                                             │  │
│  │    - soft_delete()                                    │  │
│  │    - restore()                                        │  │
│  │    - to_base_dict()                                   │  │
│  │    - __repr__()                                       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ inherits from
                            │
┌─────────────────────────────────────────────────────────────┐
│                          User                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Inherited from BaseModel:                            │  │
│  │    - id, created_at, updated_at, is_deleted           │  │
│  │    - soft_delete(), restore(), to_base_dict()         │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │  Own Attributes:                                      │  │
│  │    - username                                         │  │
│  │    - email                                            │  │
│  │    - password_hash                                    │  │
│  │    - first_name, middle_name, last_name, bio          │  │
│  │    - is_active                                        │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │  Own/Overridden Methods:                              │  │
│  │    - to_dict() (extends to_base_dict)                 │  │
│  │    - __repr__() (overrides parent)                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### SQLAlchemy Table Generation

When Flask-SQLAlchemy creates database tables:

1. It scans all classes that inherit from `db.Model`
2. For each class, it collects all `Column` definitions (including inherited ones)
3. It generates SQL CREATE TABLE statements

```
BaseModel (abstract=True) → NO TABLE CREATED
    │
    ├── User → CREATE TABLE users.users (id, created_at, updated_at, is_deleted, username, email, ...)
    │
    └── UserTemp → CREATE TABLE users.user_temp (id, created_at, updated_at, is_deleted, email, username, ...)
```

---

## Code Breakdown

### BaseModel Class

```python
class BaseModel(db.Model):
    __abstract__ = True  # ← This is CRITICAL
```

#### `__abstract__ = True`

This tells SQLAlchemy: **"Don't create a database table for this class."**

Without this line, SQLAlchemy would try to create a table called `base_model`, which we don't want.

### Column Definitions

```python
id = Column(
    Integer,
    primary_key=True,
    autoincrement=True,
    comment="Unique identifier for the record"
)
```

| Parameter            | Meaning                                                        |
| -------------------- | -------------------------------------------------------------- |
| `Integer`            | PostgreSQL will use `INTEGER` type (4 bytes, max ~2.1 billion) |
| `primary_key=True`   | This is the unique identifier for each row                     |
| `autoincrement=True` | PostgreSQL automatically assigns the next number               |
| `comment="..."`      | Adds documentation to the database schema                      |

### Timestamp Fields

```python
created_at = Column(
    DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc),
    nullable=False,
)
```

#### Why `DateTime(timezone=True)`?

- Stores the timezone info along with the datetime
- PostgreSQL stores this as `TIMESTAMP WITH TIME ZONE`
- Avoids ambiguity when your app runs in different timezones

#### Why `lambda: datetime.now(timezone.utc)` instead of `datetime.utcnow`?

```python
# ❌ BAD: datetime.utcnow is deprecated
default=datetime.utcnow  # Returns a "naive" datetime (no timezone info)

# ✅ GOOD: datetime.now(timezone.utc)
default=lambda: datetime.now(timezone.utc)  # Returns "aware" datetime with UTC timezone
```

The `lambda` is needed because we want the function to be called **when a record is created**, not when the class is defined.

### Updated At Field

```python
updated_at = Column(
    DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc),
    onupdate=lambda: datetime.now(timezone.utc),  # ← Key difference
    nullable=False,
)
```

#### `onupdate` Parameter

This is the magic that automatically updates the timestamp whenever the record is modified:

```python
user = User.query.get(1)
user.email = "newemail@example.com"
db.session.commit()  # ← updated_at is automatically set to current time!
```

**How it works internally:**

1. SQLAlchemy detects that the `user` object was modified
2. Before executing the UPDATE statement, SQLAlchemy calls the `onupdate` function
3. The returned value is set as the new `updated_at` value
4. The UPDATE SQL includes this new timestamp

---

## Inheritance Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLASS DEFINITION TIME                             │
└─────────────────────────────────────────────────────────────────────────────┘

    Python reads: class User(BaseModel):
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │ Python creates "User" class by:                                     │
    │   1. Copy all attributes from BaseModel → User                      │
    │   2. Add all attributes defined in User class                       │
    │   3. If User overrides a BaseModel method, use User's version       │
    └─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │ SQLAlchemy's metaclass kicks in:                                    │
    │   1. Finds all Column() definitions                                 │
    │   2. Registers them in the mapper                                   │
    │   3. Prepares to create the table (when db.create_all() is called)  │
    └─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                           TABLE CREATION TIME                               │
└─────────────────────────────────────────────────────────────────────────────┘

    db.create_all() is called
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │ SQLAlchemy generates SQL:                                           │
    │                                                                     │
    │   CREATE TABLE users.users (                                        │
    │       id SERIAL PRIMARY KEY,               -- From BaseModel        │
    │       created_at TIMESTAMP WITH TIME ZONE, -- From BaseModel        │
    │       updated_at TIMESTAMP WITH TIME ZONE, -- From BaseModel        │
    │       is_deleted BOOLEAN NOT NULL,         -- From BaseModel        │
    │       username VARCHAR(80) NOT NULL,       -- From User             │
    │       email VARCHAR(120) NOT NULL,         -- From User             │
    │       password_hash VARCHAR(256) NOT NULL, -- From User             │
    │       ...                                                           │
    │   );                                                                │
    └─────────────────────────────────────────────────────────────────────┘
```

---

## The Abstract Class Concept

### What is an Abstract Class?

An **abstract class** is a class that:

1. Cannot be instantiated directly
2. Exists only to be inherited by other classes
3. Provides common functionality to child classes

### In Python vs SQLAlchemy

| Context     | How to Mark as Abstract             |
| ----------- | ----------------------------------- |
| Pure Python | Use `abc.ABC` and `@abstractmethod` |
| SQLAlchemy  | Use `__abstract__ = True`           |

```python
# Pure Python abstract class
from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def speak(self):
        pass

# SQLAlchemy abstract model
class BaseModel(db.Model):
    __abstract__ = True  # ← SQLAlchemy's way
```

### Why SQLAlchemy Needs `__abstract__`?

SQLAlchemy uses a **metaclass** that automatically:

1. Inspects each class inheriting from `db.Model`
2. Creates a database table for that class
3. Maps Python columns to SQL columns

Without `__abstract__ = True`, SQLAlchemy would try to:

```sql
CREATE TABLE base_model (
    id INTEGER PRIMARY KEY,
    created_at TIMESTAMP,
    ...
);
```

This would fail because:

- We don't want a "base_model" table
- It would have no meaningful data

---

## Timestamp Handling Deep Dive

### The Problem with Naive Datetimes

```python
# ❌ Naive datetime (no timezone info)
from datetime import datetime
now = datetime.utcnow()  # datetime(2026, 1, 11, 10, 54, 23)
                          # Python doesn't know this is UTC!

# If your app runs in India (UTC+5:30) and USA (UTC-5), you get confusion:
# - India thinks 10:54 UTC is 16:24 IST
# - But if the timezone isn't stored, USA might think it's 10:54 EST
```

### The Solution: Timezone-Aware Datetimes

```python
# ✅ Aware datetime (includes timezone info)
from datetime import datetime, timezone
now = datetime.now(timezone.utc)  # datetime(2026, 1, 11, 10, 54, 23, tzinfo=UTC)
                                   # Python KNOWS this is UTC!
```

### PostgreSQL Storage

```sql
-- With DateTime(timezone=True):
-- PostgreSQL stores as TIMESTAMP WITH TIME ZONE
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()

-- All timestamps are converted to UTC internally
-- Displayed in the session's timezone when queried
```

### Best Practice Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Application   │     │   PostgreSQL    │     │   API Response  │
│                 │     │                 │     │                 │
│  Store in UTC   │────▶│  Store in UTC   │────▶│  Return as ISO  │
│                 │     │                 │     │  8601 string    │
└─────────────────┘     └─────────────────┘     └─────────────────┘

# ISO 8601 format example:
"2026-01-11T10:54:23+00:00"
```

---

## Soft Delete Pattern

### What is Soft Delete?

Instead of actually deleting a record from the database:

```sql
-- Hard delete (data is GONE forever)
DELETE FROM users WHERE id = 1;
```

We set a flag:

```sql
-- Soft delete (data remains, but marked as "deleted")
UPDATE users SET is_deleted = TRUE WHERE id = 1;
```

### Why Use Soft Delete?

| Benefit           | Explanation                                  |
| ----------------- | -------------------------------------------- |
| **Data Recovery** | Can "undelete" records if deleted by mistake |
| **Audit Trail**   | Keep complete history of all data            |
| **Foreign Keys**  | No orphaned references in related tables     |
| **Analytics**     | Can analyze even "deleted" data              |
| **Compliance**    | Some regulations require data retention      |

### Querying with Soft Delete

You need to remember to filter out deleted records:

```python
# ❌ Without filtering - includes "deleted" records
all_users = User.query.all()

# ✅ With filtering - excludes "deleted" records
active_users = User.query.filter_by(is_deleted=False).all()
```

### Pro Tip: Create a Query Helper

```python
# In base.py, you could add:
@classmethod
def active(cls):
    """Return query that excludes soft-deleted records."""
    return cls.query.filter_by(is_deleted=False)

# Usage:
active_users = User.active().all()
active_user = User.active().filter_by(id=1).first()
```

---

## How to Create a New Model

### Step 1: Create the Model File

```python
# app/models/product.py
"""
Product Model
=============
Product model for e-commerce functionality.
"""

from app import db
from app.models.base import BaseModel


class Product(BaseModel):
    """
    Product model.

    Inherits from BaseModel:
        - id (Integer, Primary Key)
        - created_at (DateTime)
        - updated_at (DateTime)
        - is_deleted (Boolean)
    """

    __tablename__ = 'products'
    __table_args__ = {'schema': 'store'}  # Optional: specify schema

    # Product-specific fields
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Product {self.name}>'

    def to_dict(self):
        data = self.to_base_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else None,
            'stock': self.stock,
            'is_active': self.is_active,
        })
        return data
```

### Step 2: Export the Model

```python
# app/models/__init__.py
from app.models.base import BaseModel
from app.models.user import User
from app.models.product import Product  # Add this line

__all__ = ['BaseModel', 'User', 'Product']  # Update this list
```

### Step 3: Create Migration

```bash
flask db migrate -m "Add products table"
flask db upgrade
```

---

## Common Pitfalls & Best Practices

### ❌ Pitfall 1: Forgetting `__abstract__ = True`

```python
# Without __abstract__ = True
class BaseModel(db.Model):
    id = Column(Integer, primary_key=True)
    # ...

# SQLAlchemy will try to create a "base_model" table and FAIL!
```

### ❌ Pitfall 2: Circular Imports

```python
# base.py
from app.models.user import User  # ❌ Don't import child models here!

class BaseModel(db.Model):
    ...

# This causes: ImportError: cannot import name 'User' (circular import)
```

### ❌ Pitfall 3: Overriding Base Columns Incorrectly

```python
class User(BaseModel):
    # ❌ Don't redefine base columns
    id = db.Column(db.String(50), primary_key=True)  # Different type!

    # This might cause conflicts or unexpected behavior
```

### ✅ Best Practice: Use ISO 8601 for API Responses

```python
def to_dict(self):
    return {
        # ✅ Always use .isoformat() for datetime in JSON
        'created_at': self.created_at.isoformat() if self.created_at else None,
    }
```

### ✅ Best Practice: Always Query with is_deleted Filter

```python
# ✅ Good: Explicit filter
users = User.query.filter_by(is_deleted=False).all()

# Even better: Create a helper method
@classmethod
def active(cls):
    return cls.query.filter_by(is_deleted=False)

# Usage
users = User.active().all()
```

---

## Comparison: Before vs After

### Before (Without Base Model)

```python
# user.py - 40 lines
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # ... more fields

# user_temp.py - 21 lines (duplicate definitions!)
class UserTemp(db.Model):
    __tablename__ = 'user_temp'

    id = db.Column(db.Integer, primary_key=True)  # Duplicated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Duplicated
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Duplicated
    is_deleted = db.Column(db.Boolean, default=False)  # Duplicated

    email = db.Column(db.String(100), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
```

### After (With Base Model)

```python
# base.py - Defined ONCE
class BaseModel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=...)
    is_deleted = Column(Boolean, default=False, nullable=False)

# user.py - Cleaner! Only user-specific fields
class User(BaseModel):
    __tablename__ = 'users'

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # ... user-specific fields only

# user_temp.py - Also clean!
class UserTemp(BaseModel):
    __tablename__ = 'user_temp'

    email = db.Column(db.String(100), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    # ... no duplicate field definitions!
```

### Benefits Realized

| Metric                         | Before          | After         |
| ------------------------------ | --------------- | ------------- |
| Lines duplicated per model     | 8+ lines        | 0 lines       |
| Risk of inconsistency          | High            | None          |
| Effort to add new common field | Edit all models | Edit one file |
| Maintenance burden             | High            | Low           |

---

## Summary

The **Base Model Pattern** we implemented:

1. **Eliminates code duplication** across all models
2. **Ensures consistency** - all tables have the same base fields
3. **Simplifies maintenance** - change once, apply everywhere
4. **Provides utility methods** - `soft_delete()`, `restore()`, `to_base_dict()`
5. **Uses modern Python practices** - timezone-aware datetimes, proper inheritance

This is a **production-ready pattern** used by professional teams worldwide!

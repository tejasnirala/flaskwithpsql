# Complete Python & Flask Guide for Node.js Developers

> A comprehensive guide to understand Python, Flask, and how this application works.

---

## Table of Contents

1. [Python vs Node.js - Quick Comparison](#1-python-vs-nodejs---quick-comparison)
2. [Understanding Dunder Methods](#2-understanding-dunder-methods-double-underscore)
3. [What is `__init__.py` and Python Packages](#3-what-is-__init__py-and-python-packages)
4. [Virtual Environments (Like node_modules)](#4-virtual-environments-like-node_modules)
5. [How Flask Works](#5-how-flask-works)
6. [Complete Data Flow - From Start to Response](#6-complete-data-flow---from-start-to-response)
7. [File-by-File Breakdown](#7-file-by-file-breakdown)
8. [Common Python Concepts Used](#8-common-python-concepts-used)

---

## 1. Python vs Node.js - Quick Comparison

| Concept              | Node.js                                         | Python/Flask                      |
| -------------------- | ----------------------------------------------- | --------------------------------- |
| Package manager      | `npm` / `yarn`                                  | `pip`                             |
| Dependencies file     | `package.json`                                  | `requirements.txt`                |
| Install dependencies | `npm install`                                   | `pip install -r requirements.txt` |
| Run dev server       | `npm run dev`                                   | `flask run` or `python run.py`     |
| Import syntax        | `const x = require('x')` or `import x from 'x'` | `import x` or `from x import y`   |
| Entry point          | `app.js` / `index.js`                           | `run.py` / `app.py`               |
| Packages folder      | `node_modules/`                                 | `venv/` (virtual environment)     |
| Export from file      | `module.exports`                                | Just define, then import           |

### Example Comparison

**Node.js:**

```javascript
// Importing
const express = require("express");
const { Router } = require("express");

// Creating app
const app = express();

// Route
app.get("/", (req, res) => {
  res.json({ message: "Hello" });
});

// Start server
app.listen(3000);
```

**Python/Flask:**

```python
# Importing
from flask import Flask, jsonify

# Creating app
app = Flask(__name__)

# Route
@app.route('/')
def index():
    return jsonify({'message': 'Hello'})

# Start server
if __name__ == '__main__':
    app.run(port=5000)
```

---

## 2. Understanding Dunder Methods (Double Underscore)

### What is a "Dunder"?

**Dunder** = **D**ouble **Under**score

In Python, names surrounded by double underscores like `__init__`, `__name__`, `__repr__` are called **dunder methods** (or **magic methods**).

They are special methods that Python calls automatically in certain situations.

### Common Dunder Methods Explained

#### `__name__` - Module Name

```python
# This is a special variable that Python sets automatically
print(__name__)
```

- When you **run a file directly**: `__name__` = `'__main__'`
- When you **import a file**: `__name__` = `'the_module_name'`

**Example:**

```python
# file: run.py

print(f"__name__ is: {__name__}")

if __name__ == '__main__':
    print("This runs ONLY when you execute: python run.py")
    print("This will NOT run if someone imports this file")
```

**Why is this useful?**

```python
# run.py
def some_function():
    return "Hello"

# This code only runs when executing this file directly
# Not when importing it from another file
if __name__ == '__main__':
    app.run()  # Start server only when running directly
```

In Node.js, you might do something similar like:

```javascript
// Node.js equivalent (sort of)
if (require.main === module) {
  // This file is being run directly
}
```

---

#### `__init__` - Constructor Method

This is like the `constructor()` in JavaScript classes.

```python
class User:
    def __init__(self, name, email):
        # This runs when you create a new User
        self.name = name
        self.email = email
        print(f"Created user: {name}")

# Creating an instance (this calls __init__ automatically)
user = User("John", "john@email.com")
# Output: Created user: John
```

**JavaScript equivalent:**

```javascript
class User {
  constructor(name, email) {
    this.name = name;
    this.email = email;
    console.log(`Created user: ${name}`);
  }
}

const user = new User("John", "john@email.com");
```

**Note:** In Python, we use `self` instead of `this`. It's the first parameter of every instance method.

---

#### `__repr__` - String Representation (for Developers)

Defines how an object is displayed when you print it or view it in the debugger.

```python
class User:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'<User {self.name}>'

user = User("John")
print(user)  # Output: <User John>
```

Without `__repr__`:

```python
print(user)  # Output: <__main__.User object at 0x7f9b8c0a3d90>  (not helpful!)
```

---

#### `__str__` - String Representation (for End Users)

Similar to `__repr__`, but meant for user-friendly output.

```python
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return f'<User(name={self.name}, email={self.email})>'  # For developers

    def __str__(self):
        return f'{self.name}'  # For users

user = User("John", "john@email.com")
print(repr(user))  # <User(name=John, email=john@email.com)>
print(str(user))   # John
print(user)        # John (print uses __str__ if available)
```

---

#### `__dict__` - Object as Dictionary

Every Python object has a `__dict__` that contains its attributes.

```python
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

user = User("John", "john@email.com")
print(user.__dict__)
# Output: {'name': 'John', 'email': 'john@email.com'}
```

---

#### Other Common Dunders

| Dunder        | Purpose                            | JavaScript Equivalent |
| ------------- | ---------------------------------- | --------------------- |
| `__init__`    | Constructor                        | `constructor()`       |
| `__str__`     | String conversion                  | `toString()`          |
| `__repr__`    | Debug representation               | -                     |
| `__len__`     | Length of object                   | `length` property     |
| `__getitem__` | Enable `obj[key]` access           | -                     |
| `__setitem__` | Enable `obj[key] = value`          | -                     |
| `__eq__`      | Equality comparison `==`           | -                     |
| `__add__`     | Addition operator `+`              | -                     |
| `__call__`    | Make object callable like function | -                     |

---

## 3. What is `__init__.py` and Python Packages

### The Problem: How Does Python Find Your Code?

In Node.js, you can import any `.js` file:

```javascript
const routes = require("./routes/users"); // Just works
```

In Python, it's a bit different. Python has the concept of **modules** and **packages**.

### Module vs Package

| Term        | What it is                  | Example          |
| ----------- | --------------------------- | ---------------- |
| **Module**  | A single `.py` file         | `user.py`        |
| **Package** | A folder containing modules | `models/` folder |

### The Role of `__init__.py`

**`__init__.py` tells Python: "This folder is a package, you can import from it."**

```
app/
├── __init__.py      ← Makes 'app' a package
├── models/
│   ├── __init__.py  ← Makes 'models' a package
│   └── user.py
└── routes/
    ├── __init__.py  ← Makes 'routes' a package
    └── users.py
```

### Without `__init__.py`

```python
# This would FAIL if models/ doesn't have __init__.py
from app.models.user import User  # ImportError!
```

### With `__init__.py`

```python
# This works!
from app.models.user import User  # ✓
```

### What Goes Inside `__init__.py`?

#### Option 1: Empty File

```python
# app/models/__init__.py
# (empty - just marks this as a package)
```

#### Option 2: Import Shortcuts

```python
# app/models/__init__.py
from app.models.user import User

# Now you can do:
# from app.models import User
# Instead of:
# from app.models.user import User
```

#### Option 3: Package Initialization Code

```python
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    db.init_app(app)
    return app
```

### Node.js Equivalent

In Node.js, you often use `index.js` similarly:

```javascript
// routes/index.js
module.exports = {
  userRoutes: require("./users"),
  mainRoutes: require("./main"),
};

// Then import as:
const { userRoutes } = require("./routes");
```

Python equivalent:

```python
# routes/__init__.py
from routes.users import users_bp
from routes.main import main_bp

# Then import as:
from routes import users_bp, main_bp
```

---

## 4. Virtual Environments (Like node_modules)

### The Problem

In Node.js, each project has its own `node_modules/` folder. Dependencies are isolated per project.

Python, by default, installs packages **globally**. This causes problems:

- Project A needs `flask==2.0`
- Project B needs `flask==3.0`
- 💥 Conflict!

### The Solution: Virtual Environments

A **virtual environment** is an isolated Python environment for your project.

```bash
# Create virtual environment (like npm init)
python3 -m venv venv

# Activate it (must do this every time you open terminal)
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Now pip installs go to venv/, not globally
pip install flask

# Deactivate when done
deactivate
```

### Comparison

| Node.js                  | Python                            |
| ------------------------ | --------------------------------- |
| `node_modules/`          | `venv/`                           |
| Auto-uses local packages | Must **activate** venv first      |
| `package.json`           | `requirements.txt`                |
| `npm install`            | `pip install -r requirements.txt` |
| `npm install flask`      | `pip install flask`               |

### How to Know if venv is Active?

Your terminal prompt will show `(venv)`:

```bash
(venv) user@computer:~/project$
```

---

## 5. How Flask Works

### What is Flask?

Flask is a **micro web framework** for Python. It's similar to Express.js in Node.js.

| Express.js                  | Flask                          |
| --------------------------- | ------------------------------ |
| `const app = express()`     | `app = Flask(__name__)`        |
| `app.get('/path', handler)` | `@app.route('/path')`          |
| `app.use(middleware)`       | Decorators or `before_request` |
| `res.json(data)`            | `return jsonify(data)`         |
| `req.body`                  | `request.get_json()`           |

### Key Flask Concepts

#### 1. Application Instance

```python
from flask import Flask

# __name__ tells Flask where to find templates, static files, etc.
app = Flask(__name__)
```

#### 2. Routes (Endpoints)

```python
# Decorator pattern - very common in Python
@app.route('/users')
def get_users():
    return jsonify({'users': []})

# With methods
@app.route('/users', methods=['GET', 'POST'])
def users():
    if request.method == 'POST':
        # Create user
        pass
    return jsonify({'users': []})
```

#### 3. Blueprints (Like Express Router)

**Express.js:**

```javascript
const router = express.Router();
router.get("/", getUsers);
router.post("/", createUser);

app.use("/api/users", router);
```

**Flask:**

```python
from flask import Blueprint

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
def get_users():
    return jsonify({'users': []})

# In main app
app.register_blueprint(users_bp, url_prefix='/api/users')
```

#### 4. Application Factory Pattern

Instead of creating `app` globally, we use a function:

```python
# Why? For testing, different configs, etc.
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Setup extensions
    db.init_app(app)

    # Register routes
    app.register_blueprint(main_bp)

    return app
```

---

## 6. Complete Data Flow - From Start to Response

Let me walk you through exactly what happens when you run `python run.py` or `flask run`.

### Visual Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         STARTUP FLOW                                     │
└─────────────────────────────────────────────────────────────────────────┘

  python run.py
       │
       ▼
  ┌─────────────┐
  │   run.py    │ ──── Entry point
  └─────────────┘
       │
       │  from app import create_app
       ▼
  ┌─────────────────────┐
  │  app/__init__.py    │ ──── Application factory
  └─────────────────────┘
       │
       │  1. Create Flask instance
       │  2. Load config from config.py
       │  3. Initialize extensions (db, migrate)
       │  4. Register blueprints
       │
       ▼
  ┌─────────────────────┐
  │    Flask App        │ ──── Ready to receive requests!
  │  Running on :5500   │
  └─────────────────────┘
```

### Step-by-Step Startup

#### Step 1: You Run the Command

```bash
python run.py
# or
flask run
```

#### Step 2: Python Executes `run.py`

```python
# run.py

import os
from app import create_app, db    # ← This line triggers app/__init__.py
from app.models import User

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)      # ← Create the Flask application

if __name__ == '__main__':         # ← Only runs if executed directly
    app.run(
        host='0.0.0.0',
        port=5500,
        debug=True
    )
```

#### Step 3: `from app import create_app` Triggers `app/__init__.py`

When Python sees `from app import ...`, it:

1. Looks for folder named `app/`
2. Executes `app/__init__.py`
3. Makes available whatever is defined there

```python
# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from config import config           # ← Imports config.py

# These are created but not connected to any app yet
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    # Step 3a: Create Flask instance
    app = Flask(__name__)

    # Step 3b: Load configuration
    app.config.from_object(config[config_name])
    # This loads DATABASE_URL, SECRET_KEY, etc.

    # Step 3c: Connect extensions to this app
    db.init_app(app)              # SQLAlchemy now knows which app
    migrate.init_app(app, db)     # Alembic migrations
    CORS(app)                     # Allow cross-origin requests

    # Step 3d: Import and register blueprints (routes)
    from app.routes.main import main_bp
    from app.routes.users import users_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp, url_prefix='/api/users')

    # Step 3e: Return the configured app
    return app
```

#### Step 4: `app.run()` Starts the Server

```python
app.run(
    host='0.0.0.0',    # Accept connections from any IP
    port=5500,         # Listen on port 5500
    debug=True         # Enable debug mode (auto-reload)
)
```

Now the server is running and waiting for HTTP requests!

---

### Request Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         REQUEST FLOW                                     │
└─────────────────────────────────────────────────────────────────────────┘

  Browser: GET http://localhost:5500/api/users/
       │
       ▼
  ┌─────────────────┐
  │   Flask App     │
  │  (WSGI Server)  │
  └─────────────────┘
       │
       │ URL matching: /api/users/ → users_bp
       ▼
  ┌─────────────────────────┐
  │  app/routes/users.py    │
  │                         │
  │  @users_bp.route('/')   │
  │  def get_users():       │
  │      ...                │
  └─────────────────────────┘
       │
       │ Query database
       ▼
  ┌─────────────────────────┐
  │  app/models/user.py     │
  │                         │
  │  User.query.all()       │
  └─────────────────────────┘
       │
       │ SQL: SELECT * FROM users
       ▼
  ┌─────────────────────────┐
  │     PostgreSQL          │
  │    (Database)           │
  └─────────────────────────┘
       │
       │ Return rows
       ▼
  ┌─────────────────────────┐
  │  Convert to JSON        │
  │  jsonify(users)         │
  └─────────────────────────┘
       │
       ▼
  Browser receives:
  {
    "success": true,
    "data": [...],
    "count": 5
  }
```

### Detailed Request Example

**Request:** `GET http://localhost:5500/api/users/1`

#### 1. Flask Receives Request

```
Method: GET
Path: /api/users/1
```

#### 2. URL Routing

```python
# Flask checks registered blueprints:
# - main_bp has routes for '/' and '/health'
# - users_bp has routes for '/api/users/...'

# Match found: users_bp with url_prefix='/api/users'
# Remaining path: '/1'
```

#### 3. Route Handler Executes

```python
# app/routes/users.py

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):    # user_id = 1 (extracted from URL)

    # Query database
    user = User.query.get_or_404(user_id)

    # Return JSON response
    return jsonify({
        'success': True,
        'data': user.to_dict()
    })
```

#### 4. Database Query

```python
User.query.get_or_404(1)

# SQLAlchemy generates:
# SELECT * FROM users WHERE id = 1

# If found: returns User object
# If not found: raises 404 error automatically
```

#### 5. Response

```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2024-01-07T10:30:00"
  }
}
```

---

## 7. File-by-File Breakdown

### `run.py` - Entry Point

```python
"""Application entry point."""
import os
from app import create_app, db
from app.models import User

# Get config from environment variable, default to 'development'
config_name = os.environ.get('FLASK_ENV', 'development')

# Create the Flask application using factory function
app = create_app(config_name)

# This block only runs when executing this file directly
# Not when importing it
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',      # Accept connections from any IP
        port=5500,           # Listen on this port
        debug=True           # Auto-reload on code changes
    )
```

**Node.js equivalent:**

```javascript
// app.js
const express = require("express");
const app = express();

// ... setup routes ...

if (require.main === module) {
  app.listen(5500, "0.0.0.0", () => {
    console.log("Server running");
  });
}
```

---

### `config.py` - Configuration

```python
"""Application configuration module."""
import os
from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()


class Config:
    """Base configuration - shared by all environments."""

    # Secret key for sessions, CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'

    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Build database URL from environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"postgresql://{os.environ.get('DB_USER', 'postgres')}:" \
        f"{os.environ.get('DB_PASSWORD', 'password')}@" \
        f"{os.environ.get('DB_HOST', 'localhost')}:" \
        f"{os.environ.get('DB_PORT', '5432')}/" \
        f"{os.environ.get('DB_NAME', 'flaskwithpsql')}"


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Print SQL queries to console


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False


# Dictionary to easily select config by name
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

**Key Concepts:**

- **Classes as Config**: Python uses classes to organize configuration
- **Inheritance**: `DevelopmentConfig(Config)` inherits from `Config`
- `os.environ.get('KEY')` reads environment variables (like `process.env.KEY` in Node)

---

### `app/__init__.py` - Application Factory

```python
"""Flask application factory."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

from config import config

# Create extension instances (not bound to app yet)
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name='default'):
    """
    Factory function to create Flask app.

    Why use a factory?
    - Can create multiple app instances (for testing)
    - Different configs for dev/prod/test
    - Avoid circular imports
    """

    # Create Flask app
    # __name__ = 'app' (the package name)
    app = Flask(__name__)

    # Load configuration from config.py
    app.config.from_object(config[config_name])

    # Bind extensions to this app instance
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Import blueprints (routes)
    from app.routes.main import main_bp
    from app.routes.users import users_bp

    # Register blueprints with URL prefixes
    app.register_blueprint(main_bp)                    # Routes: /, /health
    app.register_blueprint(users_bp, url_prefix='/api/users')  # Routes: /api/users/*

    return app
```

---

### `app/models/user.py` - Database Model

```python
"""User model for the application."""
from datetime import datetime
from app import db  # Import db from app/__init__.py


class User(db.Model):
    """
    User model - represents 'users' table in PostgreSQL.

    db.Model is a base class from SQLAlchemy that:
    - Connects to database
    - Provides query methods
    - Handles table creation
    """

    __tablename__ = 'users'  # Explicit table name (optional)

    # Column definitions
    # db.Column(type, constraints...)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Optional fields
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    bio = db.Column(db.Text, nullable=True)

    # Status and timestamps
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        """How this object appears in console/logs."""
        return f'<User {self.username}>'

    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            # ... other fields
        }
```

**Comparison to Sequelize (Node.js):**

```javascript
// Node.js with Sequelize
const User = sequelize.define("User", {
  username: {
    type: DataTypes.STRING(80),
    unique: true,
    allowNull: false,
  },
  email: {
    type: DataTypes.STRING(120),
    unique: true,
    allowNull: false,
  },
});
```

---

### `app/routes/users.py` - API Routes

```python
"""User routes - CRUD operations."""
from flask import Blueprint, jsonify, request
from app import db
from app.models.user import User

# Create a Blueprint - like Express Router
users_bp = Blueprint('users', __name__)


@users_bp.route('/', methods=['GET'])
def get_users():
    """Get all users."""

    # Query database - like User.findAll() in Sequelize
    users = User.query.all()

    # Return JSON response
    return jsonify({
        'success': True,
        'data': [user.to_dict() for user in users],  # List comprehension!
        'count': len(users)
    })


@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get single user by ID."""

    # Get or return 404 automatically
    user = User.query.get_or_404(user_id)

    return jsonify({
        'success': True,
        'data': user.to_dict()
    })


@users_bp.route('/', methods=['POST'])
def create_user():
    """Create new user."""

    # Get JSON body - like req.body in Express
    data = request.get_json()

    # Validation
    if not data:
        return jsonify({'error': 'No data'}), 400

    # Create instance
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=User.hash_password(data['password'])
    )

    # Save to database
    db.session.add(user)      # Stage for insert
    db.session.commit()       # Execute the insert

    return jsonify({
        'success': True,
        'data': user.to_dict()
    }), 201  # 201 = Created


@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user."""

    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Deleted'})
```

---

## 8. Common Python Concepts Used

### Decorators (@something)

Decorators modify the behavior of functions. They're used extensively in Flask.

```python
# A decorator is a function that wraps another function

@app.route('/users')   # This is a decorator
def get_users():       # This function is being decorated
    return 'users'

# It's equivalent to:
def get_users():
    return 'users'
get_users = app.route('/users')(get_users)
```

**Common Flask decorators:**

- `@app.route('/')` - Define a route
- `@app.before_request` - Run before each request
- `@app.errorhandler(404)` - Handle specific errors

---

### List Comprehensions

Concise way to create lists (like `.map()` in JavaScript).

```python
# Python
users = User.query.all()
user_dicts = [user.to_dict() for user in users]

# Equivalent JavaScript
const users = await User.findAll();
const userDicts = users.map(user => user.toDict());
```

With condition:

```python
# Python
active_users = [u.to_dict() for u in users if u.is_active]

# JavaScript
const activeUsers = users.filter(u => u.isActive).map(u => u.toDict());
```

---

### f-strings (Formatted Strings)

```python
name = "John"
age = 25

# f-string (Python 3.6+)
message = f"Hello, {name}! You are {age} years old."

# Equivalent JavaScript
const message = `Hello, ${name}! You are ${age} years old.`;
```

---

### `self` Keyword

In Python, `self` is equivalent to `this` in JavaScript. It must be explicitly declared as the first parameter of instance methods.

```python
class User:
    def __init__(self, name):
        self.name = name      # Like this.name = name

    def greet(self):          # self is required
        return f"Hello, {self.name}"
```

---

### Dictionary Operations

```python
# Creating
user = {'name': 'John', 'age': 25}

# Accessing
name = user['name']           # Raises error if key missing
name = user.get('name')       # Returns None if missing
name = user.get('name', 'Unknown')  # Default value

# Adding/Updating
user['email'] = 'john@test.com'

# Checking key exists
if 'name' in user:
    print(user['name'])
```

---

### Exception Handling

```python
try:
    user = User.query.get(1)
    if not user:
        raise ValueError("User not found")
except ValueError as e:
    return jsonify({'error': str(e)}), 404
except Exception as e:
    return jsonify({'error': 'Server error'}), 500
finally:
    # Always runs
    pass
```

**JavaScript equivalent:**

```javascript
try {
  const user = await User.findByPk(1);
  if (!user) throw new Error("User not found");
} catch (e) {
  res.status(404).json({ error: e.message });
} finally {
  // Always runs
}
```

---

## Quick Reference Card

| What You Want    | Python/Flask                 | Node.js/Express                  |
| ---------------- | ---------------------------- | -------------------------------- |
| Import module    | `from flask import Flask`    | `const Flask = require('flask')` |
| Create app       | `app = Flask(__name__)`      | `const app = express()`          |
| Define route     | `@app.route('/path')`        | `app.get('/path', handler)`      |
| Get query params | `request.args.get('key')`    | `req.query.key`                  |
| Get body         | `request.get_json()`         | `req.body`                       |
| Send JSON        | `return jsonify(data)`       | `res.json(data)`                 |
| Status code      | `return jsonify(data), 201`  | `res.status(201).json(data)`     |
| URL parameter    | `/<int:id>` → `def func(id)` | `/:id` → `req.params.id`         |
| Environment var  | `os.environ.get('KEY')`      | `process.env.KEY`                |
| Console log      | `print('message')`           | `console.log('message')`         |

---

## Next Steps

1. **Run the server** and test the API with curl or Postman
2. **Add a new model** (e.g., `Post` with a relationship to `User`)
3. **Add authentication** using Flask-JWT-Extended
4. **Write tests** using pytest
5. **Explore Flask documentation**: https://flask.palletsprojects.com/

Happy learning! 🐍🚀

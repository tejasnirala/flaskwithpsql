# Understanding Flask Blueprints

> Blueprints are Flask's way to **organize your application into reusable components** - like Express Router in Node.js.

---

## Table of Contents

1. [What are Blueprints?](#what-are-blueprints)
2. [The Problem They Solve](#the-problem-they-solve)
3. [Blueprint vs Express Router](#blueprint-vs-express-router)
4. [Creating a Blueprint](#creating-a-blueprint)
5. [Registering Blueprints](#registering-blueprints)
6. [URL Prefixes](#url-prefixes)
7. [Blueprint Structure in Your Project](#blueprint-structure-in-your-project)
8. [Complete Example](#complete-example)
9. [Advanced Features](#advanced-features)
10. [Best Practices](#best-practices)

---

## What are Blueprints?

### Simple Definition

> A **Blueprint** is a way to organize a group of related routes, templates, and static files into a reusable component.

Think of it like this:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Without Blueprints: Everything in one file 😰                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  app.py (500+ lines!)                                                   │
│  ├── @app.route('/')                                                    │
│  ├── @app.route('/about')                                               │
│  ├── @app.route('/api/users')                                           │
│  ├── @app.route('/api/users/<id>')                                      │
│  ├── @app.route('/api/posts')                                           │
│  ├── @app.route('/api/posts/<id>')                                      │
│  ├── @app.route('/api/comments')                                        │
│  ├── @app.route('/admin/dashboard')                                     │
│  ├── @app.route('/admin/users')                                         │
│  └── ... 50 more routes ...                                             │
│                                                                         │
│  😱 Unmaintainable mess!                                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│  With Blueprints: Organized by feature 😊                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  app/                                                                   │
│  ├── routes/                                                            │
│  │   ├── main.py      → main_bp (/, /about)                             │
│  │   ├── users.py     → users_bp (/api/users/...)                       │
│  │   ├── posts.py     → posts_bp (/api/posts/...)                       │
│  │   ├── comments.py  → comments_bp (/api/comments/...)                 │
│  │   └── admin.py     → admin_bp (/admin/...)                           │
│  └── __init__.py      → registers all blueprints                        │
│                                                                         │
│  ✅ Clean, organized, maintainable!                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Characteristics

| Feature            | Description                           |
| ------------------ | ------------------------------------- |
| **Modular**        | Group related routes together         |
| **Reusable**       | Can be used across different apps     |
| **URL Prefixes**    | Add common prefix to all routes        |
| **Separate Files** | Keep code organized in multiple files  |
| **Lazy Loading**   | Routes only loaded when needed        |

---

## The Problem They Solve

### Problem 1: Giant Single File

Without blueprints, all routes go in one file:

```python
# app.py - This file grows HUGE!

from flask import Flask
app = Flask(__name__)

# Main routes
@app.route('/')
def home():
    return 'Home'

@app.route('/about')
def about():
    return 'About'

# User routes
@app.route('/api/users')
def get_users():
    return 'Users'

@app.route('/api/users/<int:id>')
def get_user(id):
    return f'User {id}'

@app.route('/api/users', methods=['POST'])
def create_user():
    return 'Created'

# Post routes
@app.route('/api/posts')
def get_posts():
    return 'Posts'

# ... 100 more routes ...
# 😱 File is now 2000 lines!
```

### Problem 2: No Organization

- Hard to find specific routes
- Related routes scattered everywhere
- Multiple developers can't work on different features easily
- Testing becomes difficult

### Solution: Blueprints!

```python
# app/routes/users.py - Only user routes
from flask import Blueprint

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
def get_users():
    return 'Users'

@users_bp.route('/<int:id>')
def get_user(id):
    return f'User {id}'
```

```python
# app/routes/posts.py - Only post routes
from flask import Blueprint

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/')
def get_posts():
    return 'Posts'
```

```python
# app/__init__.py - Register all blueprints
from flask import Flask

def create_app():
    app = Flask(__name__)

    from app.routes.users import users_bp
    from app.routes.posts import posts_bp

    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(posts_bp, url_prefix='/api/posts')

    return app
```

---

## Blueprint vs Express Router

If you know Express.js, Blueprints are very similar to Express Router!

### Express Router (Node.js)

```javascript
// routes/users.js
const express = require("express");
const router = express.Router();

router.get("/", (req, res) => {
  res.json({ users: [] });
});

router.get("/:id", (req, res) => {
  res.json({ user: req.params.id });
});

router.post("/", (req, res) => {
  res.json({ message: "Created" });
});

module.exports = router;
```

```javascript
// app.js
const express = require("express");
const app = express();

const usersRouter = require("./routes/users");

app.use("/api/users", usersRouter); // Mount with prefix

app.listen(3000);
```

### Flask Blueprint (Python)

```python
# app/routes/users.py
from flask import Blueprint, jsonify

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
def get_users():
    return jsonify({'users': []})

@users_bp.route('/<int:id>')
def get_user(id):
    return jsonify({'user': id})

@users_bp.route('/', methods=['POST'])
def create_user():
    return jsonify({'message': 'Created'})
```

```python
# app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)

    from app.routes.users import users_bp

    app.register_blueprint(users_bp, url_prefix='/api/users')

    return app
```

### Side-by-Side Comparison

| Express.js                        | Flask                                                    |
| --------------------------------- | -------------------------------------------------------- |
| `const router = express.Router()` | `users_bp = Blueprint('users', __name__)`                |
| `router.get('/path', handler)`    | `@users_bp.route('/path')`                               |
| `router.post('/path', handler)`   | `@users_bp.route('/path', methods=['POST'])`             |
| `app.use('/prefix', router)`       | `app.register_blueprint(users_bp, url_prefix='/prefix')`   |
| `module.exports = router`         | (just import the blueprint)                              |

---

## Creating a Blueprint

### Basic Syntax

```python
from flask import Blueprint

# Blueprint(name, import_name, **options)
users_bp = Blueprint('users', __name__)
```

### Parameters Explained

```python
users_bp = Blueprint(
    'users',      # 1. Name - unique identifier for this blueprint
    __name__,     # 2. Import name - helps Flask find resources
)
```

#### Parameter 1: `name` (Required)

The blueprint's name - must be unique across your app.

```python
# Used for:
# 1. URL generation with url_for()
url_for('users.get_user', id=1)  # 'users' is the blueprint name
#        ↑ blueprint.function

# 2. Identifying the blueprint internally
```

#### Parameter 2: `__name__` (Required)

Tells Flask where this blueprint's resources are located.

```python
# In app/routes/users.py:
users_bp = Blueprint('users', __name__)
# __name__ = 'app.routes.users'

# Flask can now find:
# - Templates in app/routes/templates/
# - Static files in app/routes/static/
```

### Adding Routes to a Blueprint

```python
from flask import Blueprint, jsonify, request

users_bp = Blueprint('users', __name__)

# GET request
@users_bp.route('/')
def get_all_users():
    return jsonify({'users': []})

# GET with parameter
@users_bp.route('/<int:user_id>')
def get_user(user_id):
    return jsonify({'user_id': user_id})

# POST request
@users_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()
    return jsonify({'created': data}), 201

# PUT request
@users_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    return jsonify({'updated': user_id})

# DELETE request
@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    return jsonify({'deleted': user_id})
```

---

## Registering Blueprints

### Basic Registration

```python
# app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)

    # Import blueprint
    from app.routes.users import users_bp

    # Register it
    app.register_blueprint(users_bp)

    return app
```

### With URL Prefix

```python
app.register_blueprint(users_bp, url_prefix='/api/users')
```

**Result:**

```
Blueprint route: @users_bp.route('/')       → /api/users/
Blueprint route: @users_bp.route('/<id>')   → /api/users/<id>
Blueprint route: @users_bp.route('/active') → /api/users/active
```

### Multiple Blueprints

```python
def create_app():
    app = Flask(__name__)

    # Import blueprints
    from app.routes.main import main_bp
    from app.routes.users import users_bp
    from app.routes.posts import posts_bp
    from app.routes.admin import admin_bp

    # Register with different prefixes
    app.register_blueprint(main_bp)                           # /
    app.register_blueprint(users_bp, url_prefix='/api/users') # /api/users
    app.register_blueprint(posts_bp, url_prefix='/api/posts') # /api/posts
    app.register_blueprint(admin_bp, url_prefix='/admin')     # /admin

    return app
```

### Visual Representation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BLUEPRINT REGISTRATION                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  app.register_blueprint(main_bp)                                        │
│  ├── @main_bp.route('/')       → GET  /                                 │
│  ├── @main_bp.route('/about')  → GET  /about                            │
│  └── @main_bp.route('/health') → GET  /health                           │
│                                                                         │
│  app.register_blueprint(users_bp, url_prefix='/api/users')               │
│  ├── @users_bp.route('/')      → GET  /api/users/                       │
│  ├── @users_bp.route('/<id>')  → GET  /api/users/1                      │
│  └── @users_bp.route('/')      → POST /api/users/                       │
│                                                                         │
│  app.register_blueprint(posts_bp, url_prefix='/api/posts')               │
│  ├── @posts_bp.route('/')      → GET  /api/posts/                       │
│  └── @posts_bp.route('/<id>')  → GET  /api/posts/1                      │
│                                                                         │
│  app.register_blueprint(admin_bp, url_prefix='/admin')                   │
│  ├── @admin_bp.route('/')           → GET /admin/                       │
│  └── @admin_bp.route('/dashboard')  → GET /admin/dashboard              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## URL Prefixes

### How URL Prefixes Work

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    URL PREFIX EXPLAINED                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  In users.py:                                                           │
│  @users_bp.route('/profile')                                             │
│                  └── route path: '/profile'                              │
│                                                                         │
│  In __init__.py:                                                        │
│  app.register_blueprint(users_bp, url_prefix='/api/users')               │
│                                               └── prefix: '/api/users'   │
│                                                                         │
│  Final URL:                                                             │
│  prefix     + route    = final                                            │
│  /api/users + /profile = /api/users/profile                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Examples

| Blueprint Route           | URL Prefix    | Final URL           |
| ------------------------- | ------------ | ------------------- |
| `@bp.route('/')`          | `/api/users` | `/api/users/`       |
| `@bp.route('/<id>')`      | `/api/users` | `/api/users/123`    |
| `@bp.route('/search')`    | `/api/users` | `/api/users/search` |
| `@bp.route('/')`          | `/admin`     | `/admin/`           |
| `@bp.route('/dashboard')` | `/admin`     | `/admin/dashboard`  |
| `@bp.route('/')`          | (none)       | `/`                 |

### No Prefix (Root Blueprint)

```python
# Main routes at root level
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return 'Home'

@main_bp.route('/about')
def about():
    return 'About'

# Register without prefix
app.register_blueprint(main_bp)
# Routes: /, /about
```

---

## Blueprint Structure in Your Project

### Your Current Project Structure

```
flaskwithpsql/
├── app/
│   ├── __init__.py           ← Application factory + registers blueprints
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── routes/
│   │   ├── __init__.py       ← (optional) Package marker
│   │   ├── main.py           ← main_bp blueprint
│   │   └── users.py          ← users_bp blueprint
│   └── templates/
│       └── test.html
├── config.py
└── run.py
```

### How They Connect

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION FLOW                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  run.py                                                                 │
│     │                                                                   │
│     │ from app import create_app                                        │
│     ▼                                                                   │
│  app/__init__.py                                                        │
│     │                                                                   │
│     │ def create_app():                                                 │
│     │     app = Flask(__name__)                                         │
│     │                                                                   │
│     │     from app.routes.main import main_bp                           │
│     │     from app.routes.users import users_bp                         │
│     │          │                    │                                   │
│     │          ▼                    ▼                                   │
│     │   ┌──────────────┐    ┌──────────────┐                            │
│     │   │   main.py    │    │   users.py   │                            │
│     │   │   main_bp    │    │   users_bp   │                            │
│     │   └──────────────┘    └──────────────┘                            │
│     │                                                                   │
│     │     app.register_blueprint(main_bp)                               │
│     │     app.register_blueprint(users_bp, url_prefix='/api/users')      │
│     │                                                                   │
│     │     return app                                                    │
│     │                                                                   │
│     ▼                                                                   │
│  Flask App with all routes registered!                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Your Actual Files

**app/routes/main.py:**

```python
"""Main routes for the application."""
from flask import Blueprint, jsonify, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return jsonify({
        'message': 'Welcome to Flask with PostgreSQL!',
        'status': 'running',
        'version': '1.0.0'
    })

@main_bp.route('/template')
def test_template():
    return render_template('test.html')

@main_bp.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'database': 'connected'
    })
```

**app/routes/users.py:**

```python
"""User routes - CRUD operations for users."""
from flask import Blueprint, jsonify, request
from app import db
from app.models.user import User

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify({
        'success': True,
        'data': [user.to_dict() for user in users],
        'count': len(users)
    })

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'success': True,
        'data': user.to_dict()
    })

# ... more routes
```

**app/**init**.py (relevant part):**

```python
def create_app(config_name='default'):
    app = Flask(__name__)

    # ... config and extensions ...

    # Import and register blueprints
    from app.routes.main import main_bp
    from app.routes.users import users_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp, url_prefix='/api/users')

    return app
```

---

## Complete Example

Let's create a complete example with multiple blueprints:

### Folder Structure

```
app/
├── __init__.py
├── routes/
│   ├── __init__.py
│   ├── main.py        # Public routes
│   ├── auth.py        # Authentication routes
│   ├── users.py       # User API routes
│   └── admin.py       # Admin routes
└── models/
    └── user.py
```

### 1. Main Blueprint (Public Pages)

```python
# app/routes/main.py
from flask import Blueprint, jsonify, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Public home page."""
    return render_template('home.html')

@main_bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@main_bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})
```

### 2. Auth Blueprint (Authentication)

```python
# app/routes/auth.py
from flask import Blueprint, jsonify, request

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login."""
    data = request.get_json()
    # ... validate credentials ...
    return jsonify({'token': 'jwt-token-here'})

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration."""
    data = request.get_json()
    # ... create user ...
    return jsonify({'message': 'User created'}), 201

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout."""
    return jsonify({'message': 'Logged out'})
```

### 3. Users Blueprint (User API)

```python
# app/routes/users.py
from flask import Blueprint, jsonify, request
from app import db
from app.models.user import User

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
def get_users():
    """Get all users."""
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@users_bp.route('/<int:id>', methods=['GET'])
def get_user(id):
    """Get single user."""
    user = User.query.get_or_404(id)
    return jsonify(user.to_dict())

@users_bp.route('/', methods=['POST'])
def create_user():
    """Create new user."""
    data = request.get_json()
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@users_bp.route('/<int:id>', methods=['PUT'])
def update_user(id):
    """Update user."""
    user = User.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        setattr(user, key, value)
    db.session.commit()
    return jsonify(user.to_dict())

@users_bp.route('/<int:id>', methods=['DELETE'])
def delete_user(id):
    """Delete user."""
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'deleted': id})
```

### 4. Admin Blueprint (Admin Panel)

```python
# app/routes/admin.py
from flask import Blueprint, jsonify, render_template

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def dashboard():
    """Admin dashboard."""
    return render_template('admin/dashboard.html')

@admin_bp.route('/users')
def manage_users():
    """User management page."""
    return render_template('admin/users.html')

@admin_bp.route('/stats')
def stats():
    """Statistics API."""
    return jsonify({
        'total_users': 100,
        'active_users': 75,
        'new_today': 5
    })
```

### 5. Register All Blueprints

```python
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.DevelopmentConfig')

    db.init_app(app)

    # Import blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.admin import admin_bp

    # Register blueprints with prefixes
    app.register_blueprint(main_bp)                          # /
    app.register_blueprint(auth_bp, url_prefix='/auth')       # /auth
    app.register_blueprint(users_bp, url_prefix='/api/users') # /api/users
    app.register_blueprint(admin_bp, url_prefix='/admin')     # /admin

    return app
```

### Final URL Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE URL MAP                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  main_bp (no prefix)                                                     │
│  ├── GET    /                     → home page                           │
│  ├── GET    /about                → about page                          │
│  └── GET    /health               → health check                        │
│                                                                         │
│  auth_bp (prefix: /auth)                                                 │
│  ├── POST   /auth/login           → login                               │
│  ├── POST   /auth/register        → register                            │
│  └── POST   /auth/logout          → logout                              │
│                                                                         │
│  users_bp (prefix: /api/users)                                           │
│  ├── GET    /api/users/           → list all users                      │
│  ├── GET    /api/users/1          → get user 1                          │
│  ├── POST   /api/users/           → create user                         │
│  ├── PUT    /api/users/1          → update user 1                       │
│  └── DELETE /api/users/1          → delete user 1                       │
│                                                                         │
│  admin_bp (prefix: /admin)                                               │
│  ├── GET    /admin/               → dashboard                           │
│  ├── GET    /admin/users          → user management                     │
│  └── GET    /admin/stats          → statistics                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Advanced Features

### 1. Blueprint-Specific Templates

Each blueprint can have its own templates folder:

```python
# Create blueprint with custom template folder
admin_bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates'  # app/routes/templates/
)
```

**Structure:**

```
app/
├── routes/
│   ├── admin.py
│   └── templates/         ← Blueprint-specific templates
│       └── dashboard.html
└── templates/             ← Main app templates
    └── base.html
```

### 2. Blueprint-Specific Static Files

```python
admin_bp = Blueprint(
    'admin',
    __name__,
    static_folder='static',
    static_url_path='/admin/static'
)
```

**Structure:**

```
app/
├── routes/
│   ├── admin.py
│   └── static/            ← Blueprint-specific static files
│       ├── admin.css
│       └── admin.js
└── static/                ← Main app static files
    └── style.css
```

### 3. Before/After Request Hooks

```python
users_bp = Blueprint('users', __name__)

@users_bp.before_request
def before_user_request():
    """Runs before every request to users blueprint."""
    print('About to handle a user request')
    # Check authentication, log request, etc.

@users_bp.after_request
def after_user_request(response):
    """Runs after every request to users blueprint."""
    print('Finished handling user request')
    return response
```

### 4. Error Handlers per Blueprint

```python
users_bp = Blueprint('users', __name__)

@users_bp.errorhandler(404)
def user_not_found(error):
    """Handle 404 errors in users blueprint."""
    return jsonify({'error': 'User not found'}), 404

@users_bp.errorhandler(400)
def bad_request(error):
    """Handle 400 errors in users blueprint."""
    return jsonify({'error': 'Bad request'}), 400
```

### 5. URL Building with url_for

```python
from flask import url_for

# Build URLs for blueprint routes
# Format: url_for('blueprint_name.function_name')

url_for('main.home')            # → '/'
url_for('users.get_user', id=1) # → '/api/users/1'
url_for('admin.dashboard')      # → '/admin/'
url_for('auth.login')           # → '/auth/login'
```

**In templates:**

```html
<a href="{{ url_for('main.home') }}">Home</a>
<a href="{{ url_for('users.get_user', id=1) }}">User Profile</a>
<a href="{{ url_for('admin.dashboard') }}">Admin Panel</a>
```

---

## Best Practices

### 1. One Blueprint Per Feature

```
✅ Good:
routes/
├── users.py      # All user-related routes
├── posts.py      # All post-related routes
├── comments.py   # All comment-related routes
└── auth.py       # All authentication routes

❌ Bad:
routes/
├── api.py        # 50 different routes mixed together
└── other.py      # Random routes
```

### 2. Use URL Prefixes for APIs

```python
# ✅ Good: Clear API structure
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(posts_bp, url_prefix='/api/posts')

# ❌ Bad: Unclear structure
app.register_blueprint(users_bp)  # Routes at /users
app.register_blueprint(posts_bp)  # Routes at /posts
```

### 3. Import Blueprints Inside create_app

```python
# ✅ Good: Avoids circular imports
def create_app():
    app = Flask(__name__)

    from app.routes.users import users_bp  # Import inside
    app.register_blueprint(users_bp)

    return app

# ❌ Bad: Can cause circular imports
from app.routes.users import users_bp  # Import at top

def create_app():
    app = Flask(__name__)
    app.register_blueprint(users_bp)
    return app
```

### 4. Use Descriptive Blueprint Names

```python
# ✅ Good: Clear names
users_bp = Blueprint('users', __name__)
posts_bp = Blueprint('posts', __name__)
auth_bp = Blueprint('auth', __name__)

# ❌ Bad: Confusing names
bp1 = Blueprint('bp1', __name__)
my_bp = Blueprint('my_bp', __name__)
```

### 5. Keep Route Functions Focused

```python
# ✅ Good: One function does one thing
@users_bp.route('/')
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@users_bp.route('/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_dict())

# ❌ Bad: One function does everything
@users_bp.route('/', defaults={'id': None})
@users_bp.route('/<int:id>')
def get_users_or_user(id):
    if id:
        return get_single_user(id)
    else:
        return get_all_users()
```

---

## Summary

### What are Blueprints?

- **Modular components** for organizing Flask routes
- Like **Express Router** in Node.js
- Allow you to **split your app** into multiple files
- Support **URL prefixes** for route grouping

### Key Commands

```python
# Create a blueprint
my_bp = Blueprint('name', __name__)

# Add routes
@my_bp.route('/path')
def handler():
    return 'Response'

# Register in app
app.register_blueprint(my_bp, url_prefix='/prefix')
```

### Benefits

| Benefit             | Description                                      |
| ------------------- | ----------------------------------------------- |
| **Organization**    | Group related routes together                   |
| **Maintainability** | Smaller, focused files                           |
| **Reusability**     | Blueprints can be shared between apps           |
| **Team Work**       | Different devs can work on different blueprints |
| **Testing**         | Easier to test isolated components              |

### Quick Reference

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BLUEPRINT CHEAT SHEET                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Create:     bp = Blueprint('name', __name__)                           │
│  Route:      @bp.route('/path')                                         │
│  Register:   app.register_blueprint(bp, url_prefix='/prefix')             │
│  URL for:    url_for('blueprint_name.function_name')                    │
│                                                                         │
│  Express equivalent:                                                    │
│  Create:     router = express.Router()                                  │
│  Route:      router.get('/path', handler)                               │
│  Register:   app.use('/prefix', router)                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

Happy coding! 🚀

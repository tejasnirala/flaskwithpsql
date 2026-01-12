# Complete Flask Server Setup Commands

> A step-by-step guide to set up a Flask server from an empty folder.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Setup (TL;DR)](#2-quick-setup-tldr)
3. [Detailed Setup with Explanations](#3-detailed-setup-with-explanations)
4. [PostgreSQL Database Setup](#4-postgresql-database-setup)
5. [Running the Server](#5-running-the-server)
6. [Common Commands Reference](#6-common-commands-reference)

---

## 1. Prerequisites

Before starting, make sure you have these installed:

### Check Python Installation

```bash
python3 --version
# Expected output: Python 3.8.x or higher

# If not installed (macOS):
brew install python3
```

### Check pip (Python Package Manager)

```bash
pip3 --version
# Expected output: pip 21.x.x or higher

# pip comes with Python, but if missing:
python3 -m ensurepip --upgrade
```

### Check PostgreSQL (if using database)

```bash
psql --version
# Expected output: psql (PostgreSQL) 14.x or higher

# If not installed (macOS):
brew install postgresql@15
brew services start postgresql@15
```

---

## 2. Quick Setup (TL;DR)

If you just want the commands without explanations:

```bash
# 1. Create and enter project folder
mkdir my-flask-app && cd my-flask-app

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install Flask
pip install flask flask-sqlalchemy flask-migrate psycopg2-binary python-dotenv flask-cors

# 5. Save dependencies
pip freeze > requirements.txt

# 6. Create folder structure
mkdir -p app/routes app/models app/templates app/static

# 7. Create essential files
touch app/__init__.py app/routes/__init__.py app/models/__init__.py
touch config.py run.py .env .gitignore

# 8. Run the server (after adding code)
python run.py
# or
flask run
```

---

## 3. Detailed Setup with Explanations

### Step 1: Create Project Directory

```bash
mkdir my-flask-app
```

**What it does:**

- `mkdir` = "make directory"
- Creates a new folder named `my-flask-app`

```bash
cd my-flask-app
```

**What it does:**

- `cd` = "change directory"
- Moves your terminal into the newly created folder
- All subsequent commands will run inside this folder

---

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
```

**What it does:**

- `python3` - Uses Python 3 interpreter
- `-m venv` - Runs the built-in `venv` module
- `venv` - Name of the virtual environment folder (can be any name, but `venv` is convention)

**Why do we need this?**

- Isolates project dependencies from global Python packages
- Prevents conflicts between different projects
- Like having a separate `node_modules` for each project

**What gets created:**

```
venv/
├── bin/           # Executable scripts (activate, pip, python)
├── include/       # C headers for compiling packages
├── lib/           # Installed packages go here
└── pyvenv.cfg     # Configuration file
```

---

### Step 3: Activate Virtual Environment

**macOS / Linux:**

```bash
source venv/bin/activate
```

**Windows (Command Prompt):**

```cmd
venv\Scripts\activate.bat
```

**Windows (PowerShell):**

```powershell
venv\Scripts\Activate.ps1
```

**What it does:**

- `source` - Executes the script in the current shell
- `venv/bin/activate` - Script that modifies your shell environment

**How to know it's activated:**
Your terminal prompt changes from:

```
user@computer:~/my-flask-app$
```

To:

```
(venv) user@computer:~/my-flask-app$
```

**Important:** You must activate venv every time you open a new terminal!

---

### Step 4: Upgrade pip (Optional but Recommended)

```bash
pip install --upgrade pip
```

**What it does:**

- `pip install` - Install a package
- `--upgrade` - Update to latest version if already installed
- `pip` - The package to upgrade (pip itself)

**Why:**

- Newer pip versions have bug fixes and better dependency resolution
- Avoids "pip version outdated" warnings

---

### Step 5: Install Flask and Extensions

#### Option A: Install Packages One by One

```bash
pip install flask
```

**What it does:** Installs Flask web framework (core package)

```bash
pip install flask-sqlalchemy
```

**What it does:** Installs SQLAlchemy ORM integration for Flask (database operations)

```bash
pip install flask-migrate
```

**What it does:** Installs Alembic-based database migration tool (like versioning for your database schema)

```bash
pip install psycopg2-binary
```

**What it does:** Installs PostgreSQL database adapter (allows Python to talk to PostgreSQL)

```bash
pip install python-dotenv
```

**What it does:** Installs library to load `.env` files (environment variables)

```bash
pip install flask-cors
```

**What it does:** Installs CORS support (allows frontend from different domain to access API)

#### Option B: Install All at Once

```bash
pip install flask flask-sqlalchemy flask-migrate psycopg2-binary python-dotenv flask-cors
```

**What it does:**

- Installs all packages in one command
- pip automatically resolves dependencies between packages

---

### Step 6: Save Dependencies to requirements.txt

```bash
pip freeze > requirements.txt
```

**What it does:**

- `pip freeze` - Lists all installed packages with exact versions
- `>` - Redirects output to a file (overwrites if exists)
- `requirements.txt` - The output file

**Output example (requirements.txt):**

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
psycopg2-binary==2.9.9
...
```

**Why is this important?**

- Other developers can install same exact versions
- Ensures consistent environment across machines
- Like `package-lock.json` in Node.js

---

### Step 7: Create Folder Structure

```bash
mkdir -p app/routes app/models app/templates app/static
```

**What it does:**

- `mkdir` - Make directory
- `-p` - Create parent directories as needed (doesn't error if exists)
- Creates this structure:

```
app/
├── routes/      # API route handlers (like Express routers)
├── models/      # Database models (like Sequelize models)
├── templates/   # HTML templates (Jinja2)
└── static/      # Static files (CSS, JS, images)
```

---

### Step 8: Create **init**.py Files

```bash
touch app/__init__.py
touch app/routes/__init__.py
touch app/models/__init__.py
```

**What it does:**

- `touch` - Creates an empty file (or updates timestamp if exists)
- `__init__.py` - Marks directories as Python packages

**Why needed:**
Without `__init__.py`, Python won't recognize these folders as packages:

```python
# This would FAIL without __init__.py:
from app.models import User
```

---

### Step 9: Create Configuration Files

```bash
touch config.py run.py .env .gitignore
```

**What it does:**
Creates these empty files:

| File         | Purpose                                               |
| ------------ | ----------------------------------------------------- |
| `config.py`  | Application configuration (database URL, secret keys) |
| `run.py`     | Entry point to start the server                       |
| `.env`       | Environment variables (secrets, not committed to git) |
| `.gitignore` | Files/folders to exclude from git                     |

---

### Step 10: Set Up .gitignore

```bash
cat > .gitignore << 'EOF'
# Virtual environment
venv/
.venv/
env/

# Environment variables
.env

# Python cache
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python

# IDE
.idea/
.vscode/
*.swp

# OS files
.DS_Store
Thumbs.db

# Flask
instance/

# Database
*.db
*.sqlite3
migrations/
EOF
```

**What it does:**

- `cat > file << 'EOF'` - Creates file with content until EOF marker
- Lists patterns for files that should NOT be tracked by git

**Why ignore these?**

- `venv/` - Too large, can be recreated with `pip install`
- `.env` - Contains secrets (passwords, API keys)
- `__pycache__/` - Auto-generated, not needed

---

### Step 11: Set Up .env File

```bash
cat > .env << 'EOF'
# Flask settings
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-change-this

# Database settings
DATABASE_URL=postgresql://username:password@localhost:5432/mydatabase
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydatabase
EOF
```

**What it does:**
Creates environment variables file.

**Variables explained:**

| Variable       | Purpose                                               |
| -------------- | ----------------------------------------------------- |
| `FLASK_APP`    | Tells Flask which file is the application entry point |
| `FLASK_ENV`    | Environment mode (development/production)             |
| `FLASK_DEBUG`  | Enable debug mode (1=on, 0=off)                       |
| `SECRET_KEY`   | Used for session encryption, CSRF protection          |
| `DATABASE_URL` | Full PostgreSQL connection string                     |

---

### Step 12: Verify Installation

```bash
pip list
```

**What it does:**

- Shows all installed packages in current environment
- Should list Flask and all extensions you installed

```bash
python -c "import flask; print(flask.__version__)"
```

**What it does:**

- `python -c "..."` - Run Python code directly from command line
- Imports Flask and prints its version
- Verifies Flask is correctly installed

---

## 4. PostgreSQL Database Setup

### Step 1: Start PostgreSQL Service

**macOS (with Homebrew):**

```bash
brew services start postgresql@15
```

**Linux (Ubuntu/Debian):**

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Start on boot
```

**What it does:**

- Starts the PostgreSQL database server as a background service

---

### Step 2: Access PostgreSQL Shell

```bash
psql -U postgres
```

**What it does:**

- `psql` - PostgreSQL interactive terminal
- `-U postgres` - Connect as user "postgres" (default superuser)

**If you get an error:**

```bash
# macOS - might need to create the postgres user database first
createdb postgres

# Or connect to default database
psql postgres
```

---

### Step 3: Create Database

```sql
CREATE DATABASE mydatabase;
```

**What it does:**

- Creates a new empty database named "mydatabase"

**Verify it was created:**

```sql
\l
```

Lists all databases.

---

### Step 4: Create User (Optional)

```sql
CREATE USER myuser WITH PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE mydatabase TO myuser;
```

**What it does:**

- Creates a new database user
- Grants full access to the database

---

### Step 5: Exit PostgreSQL Shell

```sql
\q
```

**What it does:**

- Quits/exits the psql shell
- Returns to normal terminal

---

### Step 6: Initialize Flask-Migrate

```bash
flask db init
```

**What it does:**

- Creates a `migrations/` folder in your project
- Sets up Alembic for database migrations

**What gets created:**

```
migrations/
├── alembic.ini          # Alembic configuration
├── env.py               # Migration environment
├── README
├── script.py.mako       # Template for migrations
└── versions/            # Your migration files go here
```

---

### Step 7: Create Initial Migration

```bash
flask db migrate -m "Initial migration"
```

**What it does:**

- `-m "..."` - Message describing the migration
- Scans your models and generates migration script
- Creates a new file in `migrations/versions/`

**Example output:**

```
INFO  [alembic.autogenerate.compare] Detected added table 'users'
Generating /path/to/migrations/versions/abc123_initial_migration.py
```

---

### Step 8: Apply Migration to Database

```bash
flask db upgrade
```

**What it does:**

- Runs all pending migrations
- Creates actual tables in PostgreSQL database

**Verify tables were created:**

```bash
psql -U postgres -d mydatabase -c "\dt"
```

Lists all tables in the database.

---

## 5. Running the Server

### Method 1: Using Python Directly

```bash
python run.py
```

**What it does:**

- Executes `run.py` with Python interpreter
- Starts the Flask development server

---

### Method 2: Using Flask CLI

```bash
flask run
```

**What it does:**

- Uses Flask's built-in CLI
- Reads `FLASK_APP` from environment to find app

**With options:**

```bash
flask run --host=0.0.0.0 --port=5000 --debug
```

| Option           | Purpose                                             |
| ---------------- | --------------------------------------------------- |
| `--host=0.0.0.0` | Accept connections from any IP (not just localhost) |
| `--port=5000`    | Listen on port 5000                                 |
| `--debug`        | Enable debug mode (auto-reload, detailed errors)    |

---

### Method 3: With Environment Variables

```bash
FLASK_DEBUG=1 flask run
```

**What it does:**

- Sets environment variable just for this command
- Enables debug mode

---

## 6. Common Commands Reference

### Virtual Environment Commands

| Command                    | Purpose                         |
| -------------------------- | ------------------------------- |
| `python3 -m venv venv`     | Create virtual environment      |
| `source venv/bin/activate` | Activate venv (macOS/Linux)     |
| `venv\Scripts\activate`    | Activate venv (Windows)         |
| `deactivate`               | Exit virtual environment        |
| `which python`             | Show which Python is being used |

---

### pip Commands

| Command                           | Purpose                               |
| --------------------------------- | ------------------------------------- |
| `pip install package`             | Install a package                     |
| `pip install -r requirements.txt` | Install from requirements file        |
| `pip uninstall package`           | Remove a package                      |
| `pip freeze`                      | List installed packages with versions |
| `pip freeze > requirements.txt`   | Save dependencies to file             |
| `pip list`                        | List installed packages (formatted)   |
| `pip show package`                | Show package details                  |
| `pip install --upgrade package`   | Update a package                      |

---

### Flask CLI Commands

| Command                         | Purpose                                        |
| ------------------------------- | ---------------------------------------------- |
| `flask run`                     | Start development server                       |
| `flask shell`                   | Open interactive Python shell with app context |
| `flask routes`                  | Show all registered routes                     |
| `flask db init`                 | Initialize migrations folder                   |
| `flask db migrate -m "message"` | Create new migration                           |
| `flask db upgrade`              | Apply pending migrations                       |
| `flask db downgrade`            | Revert last migration                          |
| `flask db history`              | Show migration history                         |

---

### PostgreSQL Commands

| Command                 | Purpose                  |
| ----------------------- | ------------------------ |
| `psql -U postgres`      | Connect to PostgreSQL    |
| `\l`                    | List all databases       |
| `\c dbname`             | Connect to database      |
| `\dt`                   | List all tables          |
| `\d tablename`          | Describe table structure |
| `\q`                    | Quit psql                |
| `CREATE DATABASE name;` | Create new database      |
| `DROP DATABASE name;`   | Delete database          |

---

## Complete Setup Script

Here's a bash script that does everything automatically:

```bash
#!/bin/bash

# Flask Project Setup Script
# Usage: bash setup.sh project-name

PROJECT_NAME=${1:-my-flask-app}

echo "🚀 Creating Flask project: $PROJECT_NAME"

# Create and enter directory
mkdir -p $PROJECT_NAME && cd $PROJECT_NAME

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "📥 Installing Flask and extensions..."
pip install flask flask-sqlalchemy flask-migrate psycopg2-binary python-dotenv flask-cors

# Save requirements
pip freeze > requirements.txt

# Create folder structure
echo "📁 Creating project structure..."
mkdir -p app/routes app/models app/templates app/static

# Create __init__.py files
touch app/__init__.py
touch app/routes/__init__.py
touch app/models/__init__.py

# Create other files
touch config.py run.py .env

# Create .gitignore
cat > .gitignore << 'GITIGNORE'
venv/
.env
__pycache__/
*.pyc
.DS_Store
instance/
migrations/
GITIGNORE

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. cd $PROJECT_NAME"
echo "  2. source venv/bin/activate"
echo "  3. Add your code to app/__init__.py and run.py"
echo "  4. python run.py"
```

Save this as `setup.sh` and run with:

```bash
bash setup.sh my-project-name
```

---

## Summary Flowchart

```
┌─────────────────────────────────────────────────────────────┐
│                    FLASK SETUP FLOW                         │
└─────────────────────────────────────────────────────────────┘

     mkdir project && cd project
                 │
                 ▼
     python3 -m venv venv
                 │
                 ▼
     source venv/bin/activate
                 │
                 ▼
     pip install flask ...
                 │
                 ▼
     pip freeze > requirements.txt
                 │
                 ▼
     Create folder structure
     (app/, routes/, models/, templates/)
                 │
                 ▼
     Create __init__.py files
                 │
                 ▼
     Write application code
                 │
                 ▼
     Configure .env
                 │
                 ▼
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
flask db init          python run.py
flask db migrate        (without DB)
flask db upgrade
    │
    ▼
python run.py
    │
    ▼
🎉 Server running at http://localhost:5000
```

---

Happy Coding! 🐍🚀

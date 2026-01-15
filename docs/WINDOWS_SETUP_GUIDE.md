# Windows Setup Guide

This guide will help you set up the Flask with PostgreSQL project on a Windows machine from scratch.

---

## 📋 Prerequisites

Before starting, ensure you have the following installed on your Windows machine:

| Software       | Required Version | Download Link                                                         |
| -------------- | ---------------- | --------------------------------------------------------------------- |
| **Python**     | 3.9 or higher    | [python.org](https://www.python.org/downloads/windows/)               |
| **PostgreSQL** | 13 or higher     | [postgresql.org](https://www.postgresql.org/download/windows/)        |
| **Git**        | Latest           | [git-scm.com](https://git-scm.com/download/win)                       |
| **VS Code**    | Latest           | [code.visualstudio.com](https://code.visualstudio.com/) (Recommended) |

---

## 🐍 Step 1: Install Python

### 1.1 Download Python

1. Go to [python.org/downloads](https://www.python.org/downloads/windows/)
2. Download Python **3.13.5** (or any version ≥3.9)
3. Run the installer

### 1.2 During Installation (CRITICAL!)

> ⚠️ **IMPORTANT**: Check these boxes during installation!

```
☑️ Add python.exe to PATH
☑️ Use admin privileges when installing py.exe
```

Then click **"Customize installation"** and ensure these are selected:

-   ☑️ pip
-   ☑️ py launcher
-   ☑️ Add Python to environment variables

### 1.3 Verify Installation

Open **Command Prompt** (Win + R → type `cmd` → Enter) or **PowerShell**:

```powershell
python --version
# Expected output: Python 3.13.5

pip --version
# Expected output: pip 25.3 from ... (python 3.13)
```

---

## 🐘 Step 2: Install PostgreSQL

### 2.1 Download and Install

1. Go to [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)
2. Click **Download the installer**
3. Download the installer for Windows x86-64
4. Run the installer
5. During installation:
    - Set a password for the `postgres` user (remember this!)
    - Keep the default port: `5432`
    - Select your locale
    - Launch Stack Builder at the end (optional)

### 2.2 Add PostgreSQL to PATH

1. Press `Win + S` → search for "Environment Variables"
2. Click **"Edit the system environment variables"**
3. Click **"Environment Variables..."** button
4. Under "System variables", find and select `Path`
5. Click **"Edit..."**
6. Click **"New"**
7. Add: `C:\Program Files\PostgreSQL\16\bin` (adjust version number if different)
8. Click **OK** on all dialogs

### 2.3 Verify Installation

Open a **new** Command Prompt (to reload PATH):

```powershell
psql --version
# Expected output: psql (PostgreSQL) 16.x
```

### 2.4 Create the Database

Open Command Prompt and run:

```powershell
# Connect to PostgreSQL as the postgres user
psql -U postgres

# Enter your password when prompted

# Create the database
CREATE DATABASE flaskwithpsql;

# Verify the database was created
\l

# Exit psql
\q
```

---

## 📦 Step 3: Clone the Repository

### 3.1 Open Terminal

Open **Command Prompt** or **PowerShell** and navigate to your desired location:

```powershell
# Example: Navigate to your projects folder
cd C:\Users\YourUsername\Projects

# Or create a new folder
mkdir C:\Projects
cd C:\Projects
```

### 3.2 Clone the Repo

```powershell
git clone https://github.com/tejasnirala/flaskwithpsql.git
cd flaskwithpsql
```

---

## 🔧 Step 4: Create Virtual Environment

### 4.1 Create the Virtual Environment

> **Why use a virtual environment?**
> It isolates project dependencies from your global Python installation, preventing conflicts between different projects.

```powershell
# Create a virtual environment named "venv"
python -m venv venv
```

### 4.2 Activate the Virtual Environment

```powershell
# Windows Command Prompt
venv\Scripts\activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

> 💡 **PowerShell Execution Policy**: If you get an error in PowerShell, run this first:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4.3 Verify Activation

Your prompt should now show `(venv)` at the beginning:

```
(venv) C:\Projects\flaskwithpsql>
```

Verify Python is using the venv:

```powershell
# Should point to the venv folder
where python
# C:\Projects\flaskwithpsql\venv\Scripts\python.exe

python --version
# Python 3.13.5

pip --version
# pip 25.3 from ...\venv\lib\site-packages\pip (python 3.13)
```

### 4.4 Upgrade pip (Recommended)

```powershell
python -m pip install --upgrade pip
```

---

## 📥 Step 5: Install Dependencies

With your virtual environment activated:

```powershell
# Install all project dependencies
pip install -r requirements.txt
```

This will install:

-   Flask 3.0.0 (web framework)
-   Flask-SQLAlchemy 3.1.1 (database ORM)
-   Flask-Migrate 4.0.5 (database migrations)
-   Flask-JWT-Extended 4.6.0 (JWT authentication)
-   Flask-Limiter 3.5.0 (rate limiting)
-   Flask-CORS 4.0.0 (cross-origin requests)
-   flask-openapi3 3.1.3 (OpenAPI/Swagger documentation)
-   psycopg2-binary 2.9.9 (PostgreSQL driver)
-   pydantic 2.10.0 (input validation)
-   gunicorn 21.2.0 (production server)
-   pytest 8.0.0 (testing)
-   python-dotenv 1.0.0 (environment variables)

### 5.1 Install Development Dependencies (Optional)

If you want to contribute or run code quality tools:

```powershell
pip install -e ".[dev]"
```

---

## ⚙️ Step 6: Configure Environment Variables

### 6.1 Create the `.env` File

```powershell
# Copy the example file
copy .env.example .env

# Or use xcopy
xcopy .env.example .env
```

### 6.2 Edit the `.env` File

Open `.env` in your editor and update:

```env
# Flask Configuration
FLASK_PORT=5000
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-super-secret-key-change-to-something-random

# Database Configuration
# Option 1: Full connection string (recommended)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/flaskwithpsql

# Option 2: Individual variables
DB_USER=postgres
DB_PASSWORD=YOUR_PASSWORD
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flaskwithpsql

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Content-Type,Authorization
CORS_EXPOSE_HEADERS=Content-Type,Authorization
CORS_CREDENTIALS=true
CORS_MAX_AGE=3600
```

> ⚠️ **Replace `YOUR_PASSWORD`** with the password you set for the `postgres` user during PostgreSQL installation.

---

## 🗃️ Step 7: Initialize the Database

### 7.1 Run Database Setup

The project includes a `db_manage.py` script that handles database setup:

```powershell
# This will create tables and run migrations
python db_manage.py setup
```

### 7.2 Manual Migration Commands (Alternative)

If you prefer manual control:

```powershell
# Initialize migrations (only if migrations folder doesn't exist)
flask db init

# Create a migration
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade
```

---

## 🚀 Step 8: Run the Application

### 8.1 Start the Development Server

```powershell
python run.py
```

You should see output like:

```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to stop
```

### 8.2 Access the Application

Open your browser and visit:

| URL                                | Description               |
| ---------------------------------- | ------------------------- |
| http://localhost:5000              | Welcome page              |
| http://localhost:5000/health       | Health check endpoint     |
| http://localhost:5000/docs         | Swagger API documentation |
| http://localhost:5000/redoc        | ReDoc API documentation   |
| http://localhost:5000/openapi.json | OpenAPI specification     |

---

## 🧪 Step 9: Run Tests (Optional)

```powershell
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html
```

---

## 🛠️ Step 10: Install Pre-commit Hooks (IMPORTANT)

Pre-commit hooks are **essential** for maintaining code quality. They run automatically before each commit to check formatting, linting, and validate commit messages.

> ⚠️ **CRITICAL**: You MUST install hooks for both `pre-commit` AND `commit-msg` types!

### Option 1: Use the Cross-Platform Setup Script (Recommended)

```powershell
# Run the setup script (works on Windows, Mac, and Linux)
python scripts/setup_hooks.py
```

This script will:

-   Install the `pre-commit` package if needed
-   Set up both `pre-commit` and `commit-msg` hooks
-   Pre-install hook environments for faster first commit
-   Verify the installation

### Option 2: Manual Installation

```powershell
# Install pre-commit package
pip install pre-commit

# Install the pre-commit hooks (for linting, formatting, etc.)
pre-commit install

# IMPORTANT: Install commit-msg hook (for conventional commit validation)
pre-commit install --hook-type commit-msg

# Pre-install hook environments (optional, speeds up first commit)
pre-commit install-hooks

# Run hooks manually on all files (to verify they work)
pre-commit run --all-files
```

### What the Hooks Enforce

| Hook Type      | What It Does                                                                                                                             |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **pre-commit** | Code formatting (Black), import sorting (isort), linting (Flake8), type checking (MyPy), security scans (Bandit), blocks commits to main |
| **commit-msg** | Validates commit message follows [Conventional Commits](https://www.conventionalcommits.org/) format                                     |

### Valid Commit Message Examples

```bash
# Feature
feat: add user authentication

# Bug fix with scope
fix(auth): resolve token expiration issue

# Documentation
docs: update API setup guide

# Chore
chore(deps): update dependencies
```

### Verifying Hooks Are Installed

```powershell
# Check if hook files exist
dir .git\hooks\pre-commit
dir .git\hooks\commit-msg

# Both should show the hook files (not .sample files)
```

---

## 📝 Common Windows-Specific Issues & Solutions

### Issue 1: `python` command not found

**Solution**: Python wasn't added to PATH during installation.

1. Reinstall Python and check "Add to PATH"
2. Or manually add to PATH:
    - `C:\Users\YourUsername\AppData\Local\Programs\Python\Python313`
    - `C:\Users\YourUsername\AppData\Local\Programs\Python\Python313\Scripts`

### Issue 2: PowerShell Execution Policy Error

**Error**: `running scripts is disabled on this system`

**Solution**:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 3: Pydantic/Rust Compilation Error

**Error**: `Cargo, the Rust package manager, is not installed` or `pydantic_core` build fails

**Cause**: This happens when using an older pydantic version (< 2.10.0) with Python 3.13+. The older versions don't have pre-built wheels for Python 3.13, so pip tries to compile from source, which requires Rust.

**Solution**: Update to pydantic 2.10.0 or higher which has pre-built wheels for Python 3.13:

```powershell
# Update pydantic directly
pip install pydantic>=2.10.0

# Or if requirements.txt is already updated, reinstall
pip install -r requirements.txt
```

### Issue 4: `psycopg2-binary` Installation Fails

**Error**: Microsoft Visual C++ build tools required

**Solution**: Install pre-built wheel:

```powershell
pip install psycopg2-binary --only-binary :all:
```

Or install Visual C++ Build Tools from [Microsoft](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

### Issue 5: PostgreSQL Connection Refused

**Error**: `connection refused` or `could not connect to server`

**Solutions**:

1. Ensure PostgreSQL service is running:
    - Press `Win + R` → type `services.msc`
    - Find "postgresql-x64-16" (or similar)
    - Right-click → Start
2. Check your `.env` credentials match what you set during PostgreSQL installation
3. Verify PostgreSQL is listening on port 5432

### Issue 6: Port Already in Use

**Error**: `Address already in use` or `Port 5000 is in use`

**Solution**: Use a different port:

```powershell
# Method 1: Change in .env
FLASK_PORT=5500

# Method 2: Command line
set FLASK_RUN_PORT=5500
python run.py
```

### Issue 7: Long Path Names

**Error**: Path too long on Windows

**Solution**: Enable long paths:

1. Run `regedit` as Administrator
2. Navigate to `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`
3. Set `LongPathsEnabled` to `1`
4. Restart your computer

### Issue 8: Pre-commit Hooks Not Running

**Symptoms**:

-   Commits go through without any checks
-   Can commit to main branch (should be blocked)
-   Commit messages not validated

**Possible Causes & Solutions**:

#### Cause A: Hooks not installed

```powershell
# Check if hooks exist
dir .git\hooks\pre-commit
dir .git\hooks\commit-msg

# If they don't exist or are .sample files, install them:
python scripts/setup_hooks.py

# Or manually:
pre-commit install
pre-commit install --hook-type commit-msg
```

#### Cause B: Bash not available

The default pre-commit hooks use bash shebang (`#!/usr/bin/env bash`). If bash is not in your PATH:

**Solution 1**: Install Git Bash and add to PATH

```powershell
# Add Git's bin directory to PATH (adjust version if needed)
# C:\Program Files\Git\bin
```

**Solution 2**: Use Git Bash terminal instead of CMD/PowerShell for git commands

**Solution 3**: Set Git to use Git Bash for hooks

```powershell
git config --global core.autocrlf true
git config --global core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe"
```

#### Cause C: Hardcoded Mac/Linux paths in hooks

If you cloned from a Mac user's repo, the hook files might contain hardcoded paths like:

```
INSTALL_PYTHON=/Users/username/project/venv/bin/python3
```

**Solution**: Regenerate the hooks

```powershell
# Remove existing hooks
del .git\hooks\pre-commit
del .git\hooks\commit-msg

# Reinstall
pre-commit install
pre-commit install --hook-type commit-msg
```

#### Cause D: Virtual environment not activated

Hooks need access to pre-commit package.

```powershell
# Activate venv first
venv\Scripts\activate

# Then reinstall hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### Issue 9: Commit Message Rejected

**Error**: Hook failed with message about conventional commits

**Cause**: Your commit message doesn't follow the required format.

**Solution**: Use the correct format:

```bash
<type>(<optional scope>): <description>

# Examples:
feat: add user login
fix(auth): resolve token issue
docs: update README
chore(deps): update dependencies
```

**Valid types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

---

## 🔄 Daily Workflow

After initial setup, your daily workflow will be:

```powershell
# Navigate to project
cd C:\Projects\flaskwithpsql

# Activate virtual environment
venv\Scripts\activate

# Pull latest changes (if working with a team)
git pull

# Run the server
python run.py
```

---

## 🆚 Mac vs Windows: Key Differences

| Action               | Mac                        | Windows                 |
| -------------------- | -------------------------- | ----------------------- |
| Create venv          | `python3 -m venv venv`     | `python -m venv venv`   |
| Activate venv        | `source venv/bin/activate` | `venv\Scripts\activate` |
| Deactivate venv      | `deactivate`               | `deactivate`            |
| Python command       | `python3`                  | `python`                |
| pip command          | `pip3`                     | `pip`                   |
| Copy file            | `cp source dest`           | `copy source dest`      |
| Environment variable | `export VAR=value`         | `set VAR=value`         |
| Path separator       | `/`                        | `\`                     |

---

## 📚 Additional Resources

-   [Python on Windows FAQ](https://docs.python.org/3/faq/windows.html)
-   [PostgreSQL Windows Installation Guide](https://www.postgresql.org/docs/current/install-windows.html)
-   [Git for Windows](https://gitforwindows.org/)
-   [VS Code Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

---

## ❓ Need Help?

If you encounter issues:

1. Check the [Common Issues](#-common-windows-specific-issues--solutions) section above
2. Read the error message carefully
3. Search the error in the project's documentation (`docs/` folder)
4. Open an issue on the GitHub repository

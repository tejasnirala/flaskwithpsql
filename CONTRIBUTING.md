# Contributing to Flask with PostgreSQL

Thank you for your interest in contributing! This document provides guidelines
and instructions for contributing to this project.

## 📋 Table of Contents

-   [Code of Conduct](#code-of-conduct)
-   [Getting Started](#getting-started)
-   [Development Setup](#development-setup)
-   [Making Changes](#making-changes)
-   [Commit Guidelines](#commit-guidelines)
-   [Pull Request Process](#pull-request-process)
-   [Code Style](#code-style)
-   [Testing](#testing)
-   [Documentation](#documentation)

## 📜 Code of Conduct

-   Be respectful and inclusive
-   Be constructive in feedback
-   Focus on the issue, not the person
-   Help others learn and grow

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/flaskwithpsql.git
    cd flaskwithpsql
    ```
3. **Add upstream remote**:
    ```bash
    git remote add upstream https://github.com/ORIGINAL_OWNER/flaskwithpsql.git
    ```

## 🛠️ Development Setup

### Option 1: Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
make install-dev

# Set up pre-commit hooks
pre-commit install

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Set up database
make db-setup

# Run the application
make run
```

### Option 2: Docker Development

```bash
# Start all services
make docker-up

# Run tests
make docker-test

# View logs
make docker-logs
```

## ✏️ Making Changes

1. **Create a feature branch**:

    ```bash
    git checkout -b feature/your-feature-name
    # or
    git checkout -b fix/your-bug-fix
    ```

2. **Make your changes** following the [code style](#code-style) guidelines

3. **Write/update tests** for your changes

4. **Run checks**:

    ```bash
    make check  # Runs lint, type-check, security, and tests
    ```

5. **Commit your changes** following [commit guidelines](#commit-guidelines)

## 📝 Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type       | Description                |
| ---------- | -------------------------- |
| `feat`     | New feature                |
| `fix`      | Bug fix                    |
| `docs`     | Documentation only         |
| `style`    | Formatting, no code change |
| `refactor` | Code restructuring         |
| `test`     | Adding/updating tests      |
| `chore`    | Maintenance tasks          |

### Examples

```bash
# Feature
git commit -m "feat(auth): add password reset endpoint"

# Bug fix
git commit -m "fix(users): handle duplicate email error"

# Documentation
git commit -m "docs: update API documentation"

# Tests
git commit -m "test(services): add user service tests"
```

## 🔄 Pull Request Process

1. **Update your branch** with the latest upstream changes:

    ```bash
    git fetch upstream
    git rebase upstream/main
    ```

2. **Push your branch**:

    ```bash
    git push origin feature/your-feature-name
    ```

3. **Create a Pull Request** on GitHub with:

    - Clear title (following commit format)
    - Description of changes
    - Link to related issues
    - Screenshots (if UI changes)

4. **Address review feedback** by pushing additional commits

5. **Squash commits** if requested before merge

### PR Checklist

-   [ ] Code follows the style guidelines
-   [ ] Tests added/updated and passing
-   [ ] Documentation updated
-   [ ] No linting errors
-   [ ] No type errors
-   [ ] Pre-commit hooks pass

## 🎨 Code Style

### Python Style

We follow [PEP 8](https://pep8.org/) with some modifications:

-   **Line length**: 100 characters
-   **Formatter**: Black
-   **Import sorting**: isort (black-compatible)
-   **Quotes**: Double quotes
-   **Type hints**: Required for public functions

### Format Code

```bash
# Format all code
make format

# Check without modifying
black --check app/ tests/
isort --check-only app/ tests/
```

### Docstrings

Use Google-style docstrings:

```python
def create_user(data: UserCreateSchema) -> User:
    """
    Create a new user in the database.

    Args:
        data: Validated user creation data

    Returns:
        The newly created User object

    Raises:
        UserAlreadyExistsError: If username or email exists
    """
```

## 🧪 Testing

### Running Tests

```bash
# All tests
make test

# With coverage
make coverage

# Specific file
pytest tests/test_routes/test_users.py -v

# Specific test
pytest tests/test_routes/test_users.py::TestUserRegistration -v
```

### Writing Tests

-   Place tests in `tests/` directory
-   Mirror the `app/` structure
-   Use descriptive test names
-   One assertion per test (when practical)
-   Use fixtures for common setup

```python
class TestUserRegistration:
    def test_register_user_with_valid_data_returns_201(self, client):
        """Test successful user registration."""
        response = client.post("/api/users/register", json={...})
        assert response.status_code == 201

    def test_register_user_with_duplicate_email_returns_409(self, client, sample_user):
        """Test duplicate email error."""
        ...
```

## 📖 Documentation

-   Update `README.md` for user-facing changes
-   Add/update docs in `docs/` for features
-   Include docstrings for new functions/classes
-   Add inline comments for complex logic

### Building Docs

If we add documentation building in the future:

```bash
make docs
```

## 🐛 Reporting Bugs

1. Check if the issue already exists
2. Create a new issue with:
    - Clear title
    - Steps to reproduce
    - Expected vs actual behavior
    - Environment details (Python version, OS, etc.)
    - Error messages/logs

## 💡 Suggesting Features

1. Check existing issues/discussions
2. Create a new issue with:
    - Clear description of the feature
    - Use case / motivation
    - Proposed implementation (if any)
    - Willingness to implement

## ❓ Questions

-   Check existing documentation
-   Search closed issues
-   Open a new issue with the `question` label

---

Thank you for contributing! 🎉

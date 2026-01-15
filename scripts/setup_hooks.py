#!/usr/bin/env python3
"""
Cross-Platform Git Hooks Setup Script
======================================

This script sets up pre-commit hooks in a cross-platform manner.
Works on Windows, macOS, and Linux without requiring bash.

Usage:
    python scripts/setup_hooks.py

Or via Makefile:
    make setup-hooks
"""

import subprocess
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    # This script is in scripts/, so parent is project root
    return Path(__file__).parent.parent.resolve()


def check_pre_commit_installed() -> bool:
    """Check if pre-commit is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pre_commit", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def install_pre_commit() -> bool:
    """Install pre-commit package."""
    print("📦 Installing pre-commit...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pre-commit"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✅ pre-commit installed successfully")
            return True
        else:
            print(f"❌ Failed to install pre-commit: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing pre-commit: {e}")
        return False


def install_hooks() -> bool:
    """Install all pre-commit hooks."""
    project_root = get_project_root()

    hooks_to_install = [
        ("pre-commit", "Pre-commit hooks (linting, formatting)"),
        ("commit-msg", "Commit message validation (conventional commits)"),
    ]

    success = True

    for hook_type, description in hooks_to_install:
        print(f"\n🔧 Installing {description}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pre_commit", "install", "--hook-type", hook_type],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"✅ {hook_type} hook installed successfully")
            else:
                print(f"❌ Failed to install {hook_type} hook: {result.stderr}")
                success = False
        except Exception as e:
            print(f"❌ Error installing {hook_type} hook: {e}")
            success = False

    return success


def install_hook_environments() -> bool:
    """Pre-install hook environments to avoid delays on first commit."""
    project_root = get_project_root()

    print("\n📥 Pre-installing hook environments (this may take a moment)...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pre_commit", "install-hooks"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✅ Hook environments installed successfully")
            return True
        else:
            print(f"⚠️ Warning: Could not pre-install environments: {result.stderr}")
            print("   (Hooks will still work, but first run may be slower)")
            return True  # Not a critical failure
    except Exception as e:
        print(f"⚠️ Warning: Could not pre-install environments: {e}")
        return True  # Not a critical failure


def verify_hooks() -> bool:
    """Verify that hooks are properly installed."""
    project_root = get_project_root()
    git_hooks_dir = project_root / ".git" / "hooks"

    if not git_hooks_dir.exists():
        print("❌ .git/hooks directory not found. Is this a git repository?")
        return False

    hooks_to_check = ["pre-commit", "commit-msg"]
    all_present = True

    print("\n🔍 Verifying hook installation...")

    for hook in hooks_to_check:
        hook_path = git_hooks_dir / hook
        if hook_path.exists():
            print(f"  ✅ {hook} hook is installed")
        else:
            print(f"  ❌ {hook} hook is NOT installed")
            all_present = False

    return all_present


def run_test() -> bool:
    """Run a quick test of the hooks."""
    project_root = get_project_root()

    print("\n🧪 Running hook test...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pre_commit", "run", "--all-files"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        # Exit code 0 = all passed, 1 = some failed (but hooks work)
        if result.returncode in [0, 1]:
            print("✅ Hooks are working correctly")
            if result.returncode == 1:
                print("   (Some checks failed, but that's normal - hooks are functional)")
            return True
        else:
            print(f"⚠️ Unexpected result: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️ Could not run test: {e}")
        return False


def main():
    """Main entry point."""
    print("=" * 60)
    print("🔧 Cross-Platform Git Hooks Setup")
    print("=" * 60)
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print(f"Project root: {get_project_root()}")
    print("=" * 60)

    # Step 1: Check/install pre-commit
    if not check_pre_commit_installed():
        if not install_pre_commit():
            print("\n❌ Setup failed: Could not install pre-commit")
            sys.exit(1)
    else:
        print("✅ pre-commit is already installed")

    # Step 2: Install hooks
    if not install_hooks():
        print("\n❌ Setup failed: Could not install hooks")
        sys.exit(1)

    # Step 3: Pre-install environments
    install_hook_environments()

    # Step 4: Verify installation
    if not verify_hooks():
        print("\n⚠️ Warning: Hook verification failed")
        print("   Please try running this script again or install manually:")
        print("   pre-commit install")
        print("   pre-commit install --hook-type commit-msg")

    # Step 5: Run test
    run_test()

    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print(
        """
The following hooks are now active:

📋 Pre-commit (runs on every commit):
   • Code formatting (Black)
   • Import sorting (isort)
   • Linting (Flake8)
   • Type checking (MyPy)
   • Security scanning (Bandit)
   • Branch protection (blocks commits to main/master)

📝 Commit-msg (validates commit messages):
   • Enforces conventional commit format
   • Valid types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

Example valid commit messages:
   feat: add user authentication
   fix(auth): resolve token expiration issue
   docs: update API documentation
   chore(deps): update dependencies
"""
    )


if __name__ == "__main__":
    main()

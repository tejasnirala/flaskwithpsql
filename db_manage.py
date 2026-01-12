#!/usr/bin/env python
"""
Database management script.

This script provides commands for managing the database:
- init: Initialize migrations folder (first time setup)
- migrate: Create a new migration based on model changes
- upgrade: Apply pending migrations to the database
- reset: Drop all tables and recreate (DANGEROUS - dev only)
- reset-schema: Drop and recreate a specific schema (DANGEROUS - dev only)
- reset-table: Drop and recreate a specific table (DANGEROUS - dev only)
- seed: Populate database with sample data

Usage:
    python db_manage.py init
    python db_manage.py migrate "Add user table"
    python db_manage.py upgrade
    python db_manage.py reset
    python db_manage.py reset-schema <schema_name>
    python db_manage.py reset-table <table_name>
    python db_manage.py seed
    python db_manage.py setup  # Combined: init + migrate + upgrade
"""

import os
import subprocess
import sys


def run_command(command: str, description: str = "") -> bool:
    """Run a shell command and return success status."""
    if description:
        print(f"\n{'='*60}")
        print(f"  {description}")
        print(f"{'='*60}")

    print(f"$ {command}\n")
    result = subprocess.run(command, shell=True, cwd=os.path.dirname(os.path.abspath(__file__)))

    if result.returncode != 0:
        print(f"\n❌ Command failed with exit code {result.returncode}")
        return False

    print(f"\n✅ {description or 'Command'} completed successfully!")
    return True


def check_migrations_folder() -> bool:
    """Check if migrations folder exists."""
    migrations_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations")
    return os.path.exists(migrations_path)


def init_migrations():
    """Initialize the migrations folder."""
    if check_migrations_folder():
        print("⚠️  Migrations folder already exists. Skipping init.")
        return True

    return run_command("flask db init", "Initializing migrations folder")


def create_migration(message: str = "Auto migration"):
    """Create a new migration based on model changes."""
    if not check_migrations_folder():
        print("❌ Migrations folder not found. Run 'python db_manage.py init' first.")
        return False

    return run_command(f'flask db migrate -m "{message}"', f"Creating migration: {message}")


def upgrade_database():
    """Apply pending migrations to the database."""
    if not check_migrations_folder():
        print("❌ Migrations folder not found. Run 'python db_manage.py init' first.")
        return False

    return run_command("flask db upgrade", "Applying migrations to database")


def downgrade_database():
    """Rollback the last migration."""
    if not check_migrations_folder():
        print("❌ Migrations folder not found.")
        return False

    return run_command("flask db downgrade", "Rolling back last migration")


def reset_database():
    """Drop all tables and recreate (DANGEROUS!).

    This function is schema-aware and will:
    1. Detect all custom schemas used by models
    2. Drop all tables
    3. Recreate schemas (if any were used)
    4. Recreate all tables
    """
    print("\n" + "!" * 60)
    print("  ⚠️  WARNING: This will DELETE ALL DATA!")
    print("!" * 60)

    confirm = input("\nType 'yes' to confirm: ")
    if confirm.lower() != "yes":
        print("❌ Aborted.")
        return False

    # Import here to avoid circular imports
    from app import create_app, db

    app = create_app("development")

    with app.app_context():
        # Detect all custom schemas from model metadata
        schemas = set()
        for table in db.metadata.tables.values():
            if table.schema:
                schemas.add(table.schema)

        if schemas:
            print(f"\n📋 Detected custom schemas: {', '.join(schemas)}")

        print("\n🗑️  Dropping all tables...")
        db.drop_all()
        print("✅ All tables dropped.")

        # Recreate custom schemas if any exist
        if schemas:
            print("\n🏗️  Recreating schemas...")
            for schema in schemas:
                try:
                    db.session.execute(db.text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
                    print(f"  ✓ Created schema: {schema}")
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
            db.session.commit()
            print("✅ Schemas recreated.")

        print("\n🏗️  Creating all tables...")
        db.create_all()
        print("✅ All tables created.")

    return True


def reset_schema(schema_name: str):
    """Drop and recreate a specific schema (DANGEROUS!)."""
    if not schema_name:
        print("❌ Please provide a schema name.")
        print("Usage: python db_manage.py reset-schema <schema_name>")
        return False

    print("\n" + "!" * 60)
    print(f"  ⚠️  WARNING: This will DELETE ALL DATA in schema '{schema_name}'!")
    print("!" * 60)

    confirm = input("\nType 'yes' to confirm: ")
    if confirm.lower() != "yes":
        print("❌ Aborted.")
        return False

    from app import create_app, db

    app = create_app("development")

    with app.app_context():
        print(f"\n🗑️  Dropping schema '{schema_name}'...")
        try:
            db.session.execute(db.text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
            db.session.commit()
            print(f"✅ Schema '{schema_name}' dropped.")

            print(f"\n🏗️  Creating schema '{schema_name}'...")
            db.session.execute(db.text(f'CREATE SCHEMA "{schema_name}"'))
            db.session.commit()
            print(f"✅ Schema '{schema_name}' created.")

            # Recreate tables in this schema
            print(f"\n🏗️  Recreating tables in schema '{schema_name}'...")
            # Get all tables that belong to this schema and recreate them
            for table in db.metadata.tables.values():
                if table.schema == schema_name:
                    table.create(db.engine, checkfirst=True)
                    print(f"  ✓ Created table: {table.name}")

            print(f"\n✅ Schema '{schema_name}' reset complete!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error resetting schema: {e}")
            return False

    return True


def reset_table(table_name: str):
    """Drop and recreate a specific table (DANGEROUS!)."""
    if not table_name:
        print("❌ Please provide a table name.")
        print("Usage: python db_manage.py reset-table <table_name>")
        return False

    print("\n" + "!" * 60)
    print(f"  ⚠️  WARNING: This will DELETE ALL DATA in table '{table_name}'!")
    print("!" * 60)

    confirm = input("\nType 'yes' to confirm: ")
    if confirm.lower() != "yes":
        print("❌ Aborted.")
        return False

    from app import create_app, db

    app = create_app("development")

    with app.app_context():
        # Find the table in metadata
        target_table = None
        for table in db.metadata.tables.values():
            if table.name == table_name:
                target_table = table
                break

        if target_table is None:
            print(f"\n❌ Table '{table_name}' not found in the model metadata.")
            print("\nAvailable tables:")
            for table in db.metadata.tables.values():
                schema_prefix = f"{table.schema}." if table.schema else ""
                print(f"  - {schema_prefix}{table.name}")
            return False

        try:
            print(f"\n🗑️  Dropping table '{table_name}'...")
            target_table.drop(db.engine, checkfirst=True)
            print(f"✅ Table '{table_name}' dropped.")

            print(f"\n🏗️  Creating table '{table_name}'...")
            target_table.create(db.engine, checkfirst=True)
            print(f"✅ Table '{table_name}' created.")

            print(f"\n✅ Table '{table_name}' reset complete!")
        except Exception as e:
            print(f"\n❌ Error resetting table: {e}")
            return False

    return True


def seed_database():
    """Populate database with sample data."""
    from app import create_app, db
    from app.models.user import User

    app = create_app("development")

    with app.app_context():
        # Check if users already exist
        if User.query.first():
            print("⚠️  Database already has data. Skipping seed.")
            return True

        print("\n🌱 Seeding database with sample data...")

        # Create sample users with all required fields
        sample_users = [
            {
                "username": "admin",
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "bio": "System administrator",
            },
            {
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "bio": "Software developer",
            },
            {
                "username": "jane_smith",
                "email": "jane@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "bio": "Product manager",
            },
            {
                "username": "test_user",
                "email": "test@example.com",
                "first_name": "Test",
                "bio": "Test account for development",
            },
        ]

        for user_data in sample_users:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data.get("last_name"),
                bio=user_data.get("bio"),
            )
            user.set_password("Password123!")  # Meets password strength requirements
            db.session.add(user)
            print(f"  ✓ Created user: {user_data['username']}")

        db.session.commit()
        print(f"\n✅ Created {len(sample_users)} sample users.")

    return True


def setup_database():
    """Full setup: init + migrate + upgrade."""
    print("\n" + "=" * 60)
    print("  🚀 Full Database Setup")
    print("=" * 60)

    # Step 1: Initialize migrations if needed
    if not check_migrations_folder():
        if not init_migrations():
            return False
    else:
        print("\n✓ Migrations folder already exists.")

    # Step 2: Create initial migration
    if not create_migration("Initial migration"):
        return False

    # Step 3: Apply migrations
    if not upgrade_database():
        return False

    print("\n" + "=" * 60)
    print("  🎉 Database setup complete!")
    print("=" * 60)
    return True


def show_help():
    """Show help message."""
    print(__doc__)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    # Set Flask app environment variable
    os.environ.setdefault("FLASK_APP", "run.py")
    os.environ.setdefault("FLASK_ENV", "development")

    commands = {
        "init": init_migrations,
        "migrate": lambda: create_migration(sys.argv[2] if len(sys.argv) > 2 else "Auto migration"),
        "upgrade": upgrade_database,
        "downgrade": downgrade_database,
        "reset": reset_database,
        "reset-schema": lambda: reset_schema(sys.argv[2] if len(sys.argv) > 2 else ""),
        "reset-table": lambda: reset_table(sys.argv[2] if len(sys.argv) > 2 else ""),
        "seed": seed_database,
        "setup": setup_database,
        "help": show_help,
        "-h": show_help,
        "--help": show_help,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()


if __name__ == "__main__":
    main()

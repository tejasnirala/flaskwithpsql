-- =============================================================================
-- Database Initialization Script
-- =============================================================================
-- This script runs when the PostgreSQL container is first created.
-- It creates the required schema for the application.
-- =============================================================================

-- Create the users schema (used by the User model)
CREATE SCHEMA IF NOT EXISTS users;

-- Grant permissions
GRANT ALL ON SCHEMA users TO postgres;

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'Database initialization complete. Schema "users" created.';
END $$;

-- ==============================================================================
-- DocPilot — Postgres local dev initializer
-- ==============================================================================
-- This script bootstraps the local development database.
-- In production, Supabase manages this automatically.
--
-- IMPORTANT: The auth schema and auth.uid() function defined here are LOCAL
-- DEVELOPMENT STUBS ONLY. Supabase replaces them with its real implementation
-- in all non-local environments. See SCHEMA_DEVIATION.md §Local Auth Stub.
--
-- Run automatically by Docker on first container start (entrypoint-initdb.d).
-- To re-run manually: make db-reset
-- ==============================================================================

-- ─── Extensions ──────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;           -- pgvector: HNSW / IVFFlat indexes
CREATE EXTENSION IF NOT EXISTS pg_trgm;          -- trigram similarity for fuzzy text search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- uuid_generate_v4() fallback
-- btree_gin for compound indexes (used for workspace_id + tsvector)
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- ─── Auth schema stub (local dev only) ───────────────────────────────────────
-- Supabase provides this in production. We stub it here so local dev works
-- without a full Supabase stack while the RLS policies remain identical.
CREATE SCHEMA IF NOT EXISTS auth;

-- Stub user table so foreign keys referencing auth.users compile
CREATE TABLE IF NOT EXISTS auth.users (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  email       text        UNIQUE NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

-- auth.uid() — returns the current user ID from the application-set session var.
-- FastAPI sets `SET LOCAL app.current_user_id = '<uuid>'` at the start of each
-- request after verifying the JWT. Supabase's real auth.uid() reads from the
-- JWT claims instead, but the interface is identical.
CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid
  LANGUAGE sql STABLE SECURITY DEFINER AS
$$
  SELECT NULLIF(current_setting('app.current_user_id', true), '')::uuid;
$$;

-- Convenience alias matching Supabase's auth.role()
CREATE OR REPLACE FUNCTION auth.role() RETURNS text
  LANGUAGE sql STABLE SECURITY DEFINER AS
$$
  SELECT NULLIF(current_setting('app.current_user_role', true), '');
$$;

-- ─── Application roles ────────────────────────────────────────────────────────
-- docpilot_api: used by FastAPI for request-scoped queries; subject to RLS
-- docpilot_worker: used by ARQ workers; bypasses RLS (explicit workspace_id filter)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'docpilot_api') THEN
    CREATE ROLE docpilot_api NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'docpilot_worker') THEN
    CREATE ROLE docpilot_worker NOLOGIN;
  END IF;
END
$$;

-- Grant schema access
GRANT USAGE ON SCHEMA public TO docpilot_api, docpilot_worker;
GRANT USAGE ON SCHEMA auth   TO docpilot_api, docpilot_worker;

-- ─── Core tables ─────────────────────────────────────────────────────────────
-- NOTE: The full schema is managed by Alembic migrations (apps/api/db/migrations/).
-- This init script only creates what's needed for the very first migration to
-- succeed, plus the auth stub above.
--
-- The complete DDL is in Architecture.md §4, reproduced here for reference only.
-- Alembic is the single source of truth for schema state.

-- Grant future-created tables automatically
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO docpilot_api;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO docpilot_worker;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO docpilot_api, docpilot_worker;

-- ─── Alembic version table (allows first migration to run cleanly) ─────────
-- Alembic creates this on first `alembic upgrade head`; pre-creating avoids
-- a race condition when Alembic and docker-entrypoint run simultaneously.
CREATE TABLE IF NOT EXISTS alembic_version (
  version_num varchar(32) NOT NULL,
  CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- ─── Done ─────────────────────────────────────────────────────────────────────
DO $$ BEGIN
  RAISE NOTICE 'DocPilot local dev database initialized successfully.';
  RAISE NOTICE '  Extensions: vector, pg_trgm, uuid-ossp, btree_gin';
  RAISE NOTICE '  Auth stub: auth.uid(), auth.users';
  RAISE NOTICE '  Roles: docpilot_api, docpilot_worker';
  RAISE NOTICE '  Run `make db-migrate` to apply Alembic migrations.';
END $$;

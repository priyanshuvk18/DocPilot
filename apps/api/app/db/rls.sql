-- ==============================================================================
-- DocPilot — Row-Level Security Policies
-- ==============================================================================
-- Applied to every tenant-owned table.
-- Pattern: users can only see rows where workspace_id is in their memberships.
-- Writes (INSERT/UPDATE/DELETE) additionally require role owner or member.
--
-- These policies are created by Alembic migrations after each table is created.
-- This file is the canonical reference; the Alembic migration is the source of
-- truth for what is actually applied to the database.
--
-- local dev: auth.uid() reads from SET LOCAL app.current_user_id
-- production: auth.uid() reads from Supabase JWT claims (same interface)
-- ==============================================================================

-- ─── Helper: is_workspace_member ─────────────────────────────────────────────
-- Called from every RLS policy — returns TRUE if the current user belongs
-- to the workspace. Defined as SECURITY DEFINER so it can read memberships
-- even when RLS on memberships itself would block the check.
CREATE OR REPLACE FUNCTION public.is_workspace_member(ws_id uuid)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER AS
$$
  SELECT EXISTS (
    SELECT 1 FROM memberships
    WHERE workspace_id = ws_id
      AND user_id = auth.uid()
  );
$$;

-- ─── Helper: workspace_role ───────────────────────────────────────────────────
-- Returns the current user's role in the given workspace (or NULL if not a member).
CREATE OR REPLACE FUNCTION public.workspace_role(ws_id uuid)
RETURNS text
LANGUAGE sql STABLE SECURITY DEFINER AS
$$
  SELECT role FROM memberships
  WHERE workspace_id = ws_id
    AND user_id = auth.uid()
  LIMIT 1;
$$;

-- ─── Template: apply these to every tenant table ──────────────────────────────
-- Replace <table> and <workspace_col> for each table.
--
-- ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE <table> FORCE ROW LEVEL SECURITY;
--
-- -- SELECT / read
-- CREATE POLICY "tenant_read" ON <table>
--   FOR SELECT
--   USING (public.is_workspace_member(<workspace_col>));
--
-- -- INSERT: owner or member only
-- CREATE POLICY "tenant_insert" ON <table>
--   FOR INSERT
--   WITH CHECK (
--     public.workspace_role(<workspace_col>) IN ('owner', 'member')
--   );
--
-- -- UPDATE: owner or member only
-- CREATE POLICY "tenant_update" ON <table>
--   FOR UPDATE
--   USING (public.is_workspace_member(<workspace_col>))
--   WITH CHECK (
--     public.workspace_role(<workspace_col>) IN ('owner', 'member')
--   );
--
-- -- DELETE: owner only
-- CREATE POLICY "tenant_delete" ON <table>
--   FOR DELETE
--   USING (public.workspace_role(<workspace_col>) = 'owner');

-- ─── Actual policies (applied by Alembic migrations, listed here for reference)
-- See apps/api/app/db/migrations/ for the authoritative SQL.

-- chunks (most performance-critical: workspace_id is denormalized for speed)
-- ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "tenant_read" ON chunks FOR SELECT
--   USING (workspace_id IN (
--     SELECT workspace_id FROM memberships WHERE user_id = auth.uid()
--   ));
-- Note: the above is equivalent to is_workspace_member() but avoids a function
-- call in the hot retrieval path. Both forms are valid.

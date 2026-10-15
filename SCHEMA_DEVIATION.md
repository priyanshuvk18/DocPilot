# Schema & Spec Deviations

Differences between this implementation and `Architecture.md` / `Techstack.md`, with
rationale. Priority order when docs conflict: PRD > Architecture > Techstack > UI-UX.
Anything below is an approved deviation — do not "fix" it back without asking.

---

## D1 — Vector dimension: `vector(512)` instead of `vector(1024)`

| | Spec | Implementation |
|---|---|---|
| Column | `chunks.embedding vector(1024)` (Architecture.md §4) | `chunks.embedding vector(512)` |
| Embedding model | `voyage-3` (1024 dims) | `voyage-3-lite` (512 dims) |

**Rationale:** `voyage-3-lite` produces 512-dimension vectors. It is cheaper and
faster for MVP-scale corpora (< 1M chunks) while staying well above the quality bar
for retrieval evals. The model is configurable (`VOYAGE_EMBEDDING_MODEL`,
`VOYAGE_EMBEDDING_DIM`), so upgrading to `voyage-3` (1024) requires:

1. Change `VOYAGE_EMBEDDING_MODEL=voyage-3`, `VOYAGE_EMBEDDING_DIM=1024`
2. New Alembic migration altering `chunks.embedding` to `vector(1024)` and
   dropping/recreating the HNSW index
3. Full re-embed of all chunks (background job — see Architecture.md §10 P12)

The dimension is stored with each document's ingestion metadata, so a dual-write
migration can embed with both models during cutover.

---

## D2 — Local auth stub in `infra/postgres/init.sql`

Architecture assumes Supabase Auth provides the `auth` schema, `auth.users`, and
`auth.uid()`. Local docker-compose runs plain Postgres, so `init.sql` creates:

- `auth.users` (stub table so FKs from `memberships`, `documents`, `messages` compile)
- `auth.uid()` / `auth.role()` reading `SET LOCAL app.current_user_id` /
  `app.current_user_role` session variables set by FastAPI after JWT verification

**Rationale:** identical RLS policies run unchanged locally and on Supabase; no need
to run the full Supabase stack locally. In production, Supabase's real `auth.uid()`
reads the JWT claims injected through PgBouncer — same call signature, same policies.

---

## D3 — API-issued roles instead of Supabase connection

Architecture.md §4: "API connects with a restricted role and sets `request.jwt.claims`
per request." The API instead sets `app.current_user_id` via `SET LOCAL` inside the
request transaction (see D2), and connects as a normal user in local dev.

**Rationale:** `request.jwt.claims` is a Supabase-specific GUC. The session-variable
approach works on both Supabase and vanilla Postgres. Production hardening (Phase 1)
grants the API role `docpilot_api` (no superuser, RLS enforced, `FORCE ROW LEVEL
SECURITY` on tenant tables).

---

## D4 — Product name

None. The product is **DocPilot** everywhere (docs, UI copy, code identifiers).
The repository folder may be named differently locally — that has no effect on the build.

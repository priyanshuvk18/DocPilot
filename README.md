# DocPilot — AI Workspace Assistant

Answers questions from **your own documents** with verified citations (RAG), proposes and
executes actions through tools with human confirmation (agent), and measures its own
quality with evals, traces, and monitoring.

See [SCHEMA_DEVIATION.md](./SCHEMA_DEVIATION.md) for all approved deviations from the
spec docs (e.g. 512-dim voyage-3-lite embeddings).

---

## Architecture

```
Browser -- Next.js (App Router, TS) --> FastAPI (Python 3.12)
   |  Supabase Auth (JWT)                | JWT verify (JWKS) + RBAC
   |                                     |- Postgres 16 + pgvector (relational + vector + FTS, RLS)
   |                                     |- Redis (queue, rate limits, idempotency)
   |                                     |- MinIO / S3 (original files, signed URLs)
   |                                     |- Anthropic Claude (generation, tool use)
   |                                     |- Voyage AI (embeddings + rerank)
   |                                     |- ARQ workers (ingest, embed, evals)
   +-- SSE streaming <-------------------+  (token, status, citation, action_proposed, done)
```

**Request path (chat):** auth -> rate limit -> input guardrails -> query rewrite -> hybrid
retrieval (vector + keyword, RRF) -> rerank -> confidence check -> prompt assembly
(retrieved text fenced as untrusted data) -> Claude stream -> citation validation ->
persist -> SSE.

**Security model — three layers:** route dependency (JWT + role) -> service logic
(resource ownership) -> Postgres RLS (tenant isolation even if the first two have bugs).
Document text is always treated as untrusted input; it can never trigger a tool call on
its own — every side effect requires explicit user confirmation.

Full details: [Architecture.md](./Architecture.md), [PRD.md](./PRD.md).

---

## Repository layout

```
docpilot/
├── apps/
│   ├── web/                  # Next.js 15 (App Router) + TS + Tailwind + shadcn/ui
│   │   ├── app/              #   routes: (marketing), (auth), (app) shell
│   │   ├── components/       #   chat/, documents/, motion/, ui/
│   │   ├── hooks/            #   useChatStream, useUpload, useReducedMotion
│   │   ├── lib/              #   typed API client, SSE, supabase, utils
│   │   └── tests/            #   Vitest unit + Playwright e2e
│   │
│   └── api/                  # FastAPI backend
│       ├── app/
│       │   ├── api/v1/       #   routes (auth-protected, RFC 7807 errors)
│       │   ├── core/         #   config, security (JWT/JWKS), rate limit, logging
│       │   ├── services/     #   ingestion, retrieval, generation, agent, guardrails, evals
│       │   ├── models/       #   SQLAlchemy 2 models
│       │   ├── schemas/      #   Pydantic v2 request/response schemas
│       │   ├── db/           #   session, RLS SQL, Alembic migrations
│       │   ├── workers/      #   ARQ tasks (ingest, eval)
│       │   └── providers/    #   swappable LLM / embedding interfaces
│       └── tests/            #   pytest: unit, integration, evals (golden/*.jsonl), security
│
├── packages/
│   └── api-types/            # TS types generated from FastAPI OpenAPI (no hand-written dupes)
├── infra/                    # docker-compose (Postgres+pgvector, Redis, MinIO), fly.toml
├── scripts/                  # generate-types, reset-db, dev helpers
├── .github/workflows/        # ci.yml (lint, type-check, test), evals.yml gate
├── PRD.md · Architecture.md · Techstack.md · UI-UX.md · SCHEMA_DEVIATION.md
└── Makefile
```

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Node.js | >= 20 | frontend |
| pnpm | >= 9 | `corepack enable pnpm` |
| Python | 3.12 | backend (uv manages it automatically) |
| [uv](https://docs.astral.sh/uv/) | latest | Python env + deps: `python -m pip install uv` |
| Docker | >= 24 | Postgres, Redis, MinIO |
| make | any | task runner (Git Bash / WSL2 on Windows) |

---

## Quick start (< 10 minutes)

```bash
# 1. Install everything
git clone <repo> && cd docpilot
pnpm install
cd apps/api && uv sync --all-extras && cd ../..

# 2. Configure environment (safe placeholders only)
cp .env.example .env
cp .env.example apps/api/.env

# 3. Start infrastructure (Postgres+pgvector, Redis, MinIO)
make infra-up

# 4. Apply database migrations
make db-migrate

# 5. Start API (http://localhost:8000) and web (http://localhost:3000)
make api-dev      # terminal 1
make web-dev      # terminal 2
```

Local dev ships with `AUTH_DISABLED=true` (mock user, no JWT). Local RLS uses the
`auth.uid()` stub in `infra/postgres/init.sql` (SCHEMA_DEVIATION.md D2) — policies are
identical to production Supabase.

**Windows:** run `make` targets from Git Bash or WSL2. Equivalent PowerShell one-liners:

```powershell
docker compose -f infra/docker-compose.yml up -d
cd apps/api; uv sync --all-extras; uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000     # API
cd ..\..; pnpm --filter web dev                      # web
```

---

## Environment variables

All config comes from env — **never commit `.env`**, only `.env.example` is tracked.
Full annotated list: [`.env.example`](./.env.example).

| Group | Key vars | Notes |
|---|---|---|
| App | `ENVIRONMENT`, `LOG_LEVEL` | `development` / `staging` / `production` / `test` |
| Database | `DATABASE_URL` | asyncpg URL; local Postgres from docker-compose |
| Queue/cache | `REDIS_URL` | ARQ jobs, rate limits, idempotency |
| Auth | `SUPABASE_URL`, `SUPABASE_JWKS_URL`, `SUPABASE_JWT_SECRET`, `AUTH_DISABLED` | `AUTH_DISABLED=true` **never** in prod |
| LLM | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL_ANSWER`, `ANTHROPIC_MODEL_CHEAP` | server-side only |
| Embeddings | `VOYAGE_API_KEY`, `VOYAGE_EMBEDDING_MODEL`, `VOYAGE_EMBEDDING_DIM` | 512-dim voyage-3-lite (SCHEMA_DEVIATION.md D1) |
| Storage | `STORAGE_ENDPOINT_URL`, `STORAGE_ACCESS_KEY_ID`, ... | MinIO locally, S3/Supabase in prod |
| Obs | `SENTRY_DSN`, `LANGFUSE_*` | empty = disabled |
| Frontend | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_API_BASE_URL` | safe to expose |

---

## Scripts

```bash
make help              # all targets
make infra-up|down     # docker: Postgres + Redis + MinIO
make db-migrate        # alembic upgrade head
make db-reset          # wipe + recreate local DB
make api-dev           # uvicorn :8000 with reload
make api-worker        # ARQ worker (ingest / eval jobs)
make api-test          # pytest -m unit
make api-lint          # ruff check
make api-type-check    # mypy --strict
make web-dev           # next dev :3000
make web-test          # vitest
make web-lint          # eslint
make web-e2e           # playwright
make generate-types    # OpenAPI -> packages/api-types/src/generated.ts
make ci-check          # lint + type-check + tests (what CI runs)
```

---

## Testing & quality gates

| Layer | Tool | Command |
|---|---|---|
| Unit (API) | pytest | `make api-test` |
| Unit (web) | Vitest | `make web-test` |
| E2E | Playwright (sign up -> upload -> ask -> cite -> confirm action) | `make web-e2e` |
| Tenant isolation | pytest integration (workspace A vs workspace B) | `make api-test-integration` |
| LLM evals | Ragas/DeepEval on golden set — **CI gate: faithfulness >= 0.90** | Phase 5 (`make api-eval`) |
| Lint / types | ruff, mypy --strict, eslint, tsc | `make ci-check` |

CI (`.github/workflows/ci.yml`) runs lint -> type-check -> unit tests on every PR; the
eval workflow additionally gates merges on golden-set regression.

---

## MVP status

Phased delivery — each phase gated by tests + review:

- [x] **Phase 0 — Foundation:** monorepo, docker-compose, env templates, CI, Makefile
- [ ] Phase 1 — Auth & tenancy (JWT/JWKS, RBAC, RLS + cross-tenant test)
- [ ] Phase 2 — Document ingestion (signed upload, async pipeline, status, dedupe)
- [ ] Phase 3 — RAG chat (hybrid retrieval, rerank, SSE, verified citations)
- [ ] Phase 4 — Agent-lite (2 tools, confirmation cards, audit log)
- [ ] Phase 5 — Evals & monitoring (golden set CI gate, dashboard, traces)
- [ ] Phase 6 — Guardrails & hardening
- [ ] Phase 7 — UI/UX polish (per UI-UX.md)

# DocPilot — Tech Stack

**Guiding priorities:** 1) Simplicity · 2) Security · 3) Scalability
**Principle:** Use as few moving parts as possible. One database (Postgres) does relational data, vectors, keyword search, and auth-aware row security. Add infrastructure only when a metric demands it.

---

## Summary

| Layer | Choice | Runner-up |
|---|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui + Framer Motion | Vite + React |
| Backend | FastAPI (Python 3.12) + Pydantic v2 | NestJS |
| Database | PostgreSQL + pgvector (managed on Supabase) | Pinecone / Qdrant + Postgres |
| Auth | Supabase Auth (JWT) + Postgres Row-Level Security | Clerk, Auth0 |
| Object storage | Supabase Storage (S3-compatible) | AWS S3 |
| Queue / cache | Redis (Upstash) + ARQ workers | Celery, Postgres queue |
| LLM / Embeddings | Anthropic Claude API (Sonnet-class for answers, Haiku-class for cheap tasks) + Voyage AI embeddings & reranker | OpenAI, open-source models |
| RAG framework | LlamaIndex (ingestion/retrieval) + thin custom agent loop | LangChain |
| Agent tools | Native tool use + MCP client | LangGraph |
| Observability | Langfuse (traces/evals) + Sentry + OpenTelemetry | Helicone, Datadog |
| Evals | Ragas + DeepEval, run with pytest in CI | Promptfoo |
| Testing | Vitest, React Testing Library, Playwright, pytest, Schemathesis | Jest, Cypress |
| Deployment | Vercel (web) + Fly.io or Render (API + workers, Docker) + Supabase (DB) | AWS ECS, Kubernetes |
| CI/CD | GitHub Actions | GitLab CI |

---

## 1. Frontend

**Choice:** Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui (Radix), Framer Motion, TanStack Query, Zustand (light UI state), React Three Fiber (optional, 3D hero only).

**Why**
- **Simplicity:** One framework gives routing, SSR, API proxying, and image optimization. shadcn/ui gives accessible, copy-paste components you own, with no heavy UI library lock-in.
- **Security:** Server Components keep secrets off the client; built-in CSRF-safe patterns for Server Actions; strict CSP configurable in middleware. TypeScript catches contract errors early.
- **Scalability:** Vercel edge/CDN scales static and SSR traffic with no ops. Streaming (SSE via `fetch` + `ReadableStream`) fits token-by-token chat.
- **UX fit:** Framer Motion handles entrance reveals, micro-interactions, and parallax declaratively with `prefers-reduced-motion` support. See `UI-UX.md`.
- **Types shared with backend:** generate TypeScript client from FastAPI's OpenAPI schema (`openapi-typescript`), so API changes break the build, not production.

## 2. Backend

**Choice:** FastAPI (Python 3.12), Pydantic v2, SQLAlchemy 2 + Alembic, ARQ background workers, `httpx`, Uvicorn/Gunicorn in Docker.

**Why**
- **Python is where the AI ecosystem lives:** LlamaIndex, Ragas, DeepEval, document parsers (PyMuPDF, `unstructured`), and the Anthropic/Voyage SDKs are first-class. Using Python avoids glue code and version lag.
- **Simplicity:** FastAPI auto-generates OpenAPI docs and validates every request with Pydantic. Async-native, ideal for streaming LLM responses.
- **Security:** Strong input validation by default; dependency-injected auth guard on every route; easy to centralize rate limiting, guardrails, and audit logging as middleware.
- **Scalability:** Stateless API containers scale horizontally; heavy work (parsing, embedding, evals) runs in separate worker processes so chat latency is unaffected.
- **Separation:** API (request/response, streaming) and workers (ingestion, evals) share code but scale independently.

*Why not a single TypeScript stack?* It would be simpler to hire for, but the evaluation and document-processing tooling is materially stronger in Python. If your team is TypeScript-only, NestJS + LangChain.js is the fallback; expect to write more custom eval and parsing code.

## 3. Database

**Choice:** PostgreSQL 16 with `pgvector` (HNSW index) and built-in full-text search (`tsvector`), hosted on Supabase. Redis (Upstash) for rate limits, job queue, and cache.

**Why**
- **Simplicity:** One datastore for users, documents, chunks, embeddings, chats, traces, and eval results. No separate vector DB to sync, secure, or pay for.
- **Hybrid search in one query:** combine vector similarity with keyword rank (Reciprocal Rank Fusion) in SQL, with metadata filters (workspace, collection) applied in the same query.
- **Security:** **Row-Level Security** enforces tenant isolation in the database itself, so a backend bug cannot easily leak another tenant's chunks. Encryption at rest, point-in-time recovery.
- **Scalability:** pgvector HNSW comfortably handles several million chunks. Migration path: read replicas → partition by workspace → move vectors to Qdrant/Pinecone only if p95 retrieval exceeds budget (monitored via traces).

## 4. Authentication

**Choice:** Supabase Auth (email + password, Google OAuth, optional TOTP MFA) issuing short-lived JWTs; FastAPI verifies JWT signature (JWKS) and loads workspace membership; Postgres RLS uses the same claims.

**Why**
- **Simplicity:** No custom password storage, email verification, or OAuth plumbing to build.
- **Security:** Argon2/bcrypt hashing, rotating refresh tokens, httpOnly secure cookies via `@supabase/ssr`, MFA support, breached-password checks. Defense in depth: API-level RBAC (Owner/Member/Viewer) **plus** RLS.
- **Scalability:** Stateless JWT verification means no session store lookups on every request.
- **Upgrade path:** Enterprise SSO (SAML/OIDC) can be added via Supabase or by swapping to Clerk/WorkOS without changing the RBAC model.

## 5. APIs

**Choice:** REST + JSON (OpenAPI 3.1) for CRUD; Server-Sent Events for chat streaming; webhooks for async job status (or Supabase Realtime for UI updates); MCP for external tool servers.

**Why**
- **Simplicity:** REST is universally understood, cacheable, and easy to test. SSE is simpler than WebSockets for one-way token streaming and works through proxies.
- **Security:** Versioned routes (`/v1`), schema validation, idempotency keys on mutating/agent endpoints, per-user rate limits, request size caps, signed upload URLs.
- **Scalability:** Stateless endpoints behind a load balancer; long operations return `202 Accepted` + job ID.
- **Agent integration:** Tools are defined as JSON-schema functions; external systems connect through MCP servers with allowlisted scopes and per-tool permission checks.

**AI layer details**
- **Retrieval:** hybrid (vector + BM25-style) → Voyage rerank → top 5–8 chunks.
- **Generation:** Claude with a system prompt that mandates citations; low temperature; structured output for citations.
- **Agent:** custom tool-use loop (max 5 steps, budget cap, confirmation required for side effects). Add LangGraph later only if workflows become multi-branch.
- **Provider abstraction:** a small `LLMClient` interface so models can be swapped or failed over.

## 6. Testing

| Level | Tools | What it covers |
|---|---|---|
| Unit (frontend) | Vitest + React Testing Library | Components, hooks, stream parser |
| Unit (backend) | pytest, pytest-asyncio | Chunking, retrieval fusion, guardrails, tool schemas |
| API contract | Schemathesis (OpenAPI fuzzing) | Schema conformance, input validation, 5xx detection |
| Integration | pytest + Testcontainers (Postgres+pgvector, Redis) | Ingestion pipeline, RLS isolation, auth |
| End-to-end | Playwright | Sign up → upload → ask → cite → confirm action |
| **LLM evals** | Ragas + DeepEval via pytest, golden dataset | Faithfulness, relevance, context precision/recall, citation validity; **CI gate** on regression (e.g., faithfulness drop > 3%) |
| Security | Bandit, `pip-audit`, `npm audit`, Semgrep, Trivy, ZAP baseline; prompt-injection test suite | Dependency CVEs, SAST, container scan, LLM-specific attacks |
| Load | k6 | Chat streaming concurrency, ingestion throughput |
| Accessibility | axe-core in Playwright, Lighthouse CI | WCAG 2.2 AA, performance budgets |

**Why:** Tests mirror the three product layers. The eval suite treats prompts and retrieval settings as code, so any change is measured before release.

## 7. Deployment

**Choice**
- **Web:** Vercel (preview deploys per PR, edge CDN)
- **API + workers:** Docker containers on Fly.io (or Render/Railway) — separate `api` and `worker` processes, autoscaling on CPU/queue depth
- **Data:** Supabase (Postgres, Auth, Storage) with daily backups + PITR
- **Cache/queue:** Upstash Redis
- **Secrets:** platform secret stores (never in repo); rotate LLM keys quarterly
- **CI/CD:** GitHub Actions: lint → type-check → unit → integration → evals → security scans → build → deploy (staging auto, production on approval)
- **IaC:** Terraform for non-trivial infra later; `fly.toml`/`vercel.json` for MVP
- **Monitoring:** Sentry (errors), Langfuse (LLM traces, cost), OpenTelemetry → Grafana Cloud (metrics), uptime checks

**Why**
- **Simplicity:** managed platforms mean no Kubernetes or server patching for the MVP; a 2–3 person team can ship and operate it.
- **Security:** private networking between API and DB, WAF/CDN protection via Vercel/Cloudflare, least-privilege service keys, automated image scanning.
- **Scalability:** containers scale horizontally; workers scale by queue depth; clear migration path to AWS ECS/Kubernetes when needed because everything is already containerized and 12-factor.

---

## Security Baseline (cross-cutting)

- Enforce HTTPS/HSTS, strict CSP, secure cookies, CORS allowlist.
- RLS on every tenant-owned table; automated test that a user from workspace A cannot read workspace B.
- Treat retrieved document text as **untrusted input** (prompt-injection defense); gate tool calls.
- Validate file type by content (magic bytes), cap size, scan for malware, store outside web root with signed URLs.
- Rate limits + token budgets per user and workspace.
- PII redaction in logs; audit log for auth events and agent actions.
- Dependency pinning, Dependabot, SBOM generation.
- Map to OWASP Top 10 and OWASP Top 10 for LLM Applications.

## Scaling Path (only when metrics demand)

| Trigger | Action |
|---|---|
| API CPU high | Add API replicas |
| Ingestion backlog | Add workers |
| Retrieval p95 > 300 ms or > 5M chunks | Read replica → partition → dedicated vector DB |
| LLM cost climbing | Semantic cache, model routing, prompt caching |
| Enterprise demand | SSO, dedicated tenancy, regional hosting |

## Estimated Cost (MVP, early stage)

Roughly $60–$150/month infrastructure (Vercel, Fly, Supabase, Upstash, Sentry/Langfuse free-to-low tiers) plus usage-based LLM/embedding spend. Treat these as ballpark figures and verify current pricing before budgeting.

# DocPilot — Product Requirements Document

**Version:** 1.0  **Date:** 2026-10-09  **Owner:** Product

> **One-liner:** DocPilot is an AI workspace assistant that answers questions from your own documents with citations (RAG), takes actions on your behalf through connected tools (agent), and proves its own quality through built-in evaluation and monitoring.

This PRD merges three ideas into one product with a clear build order:

| Layer | Idea | Release |
|---|---|---|
| 1 | RAG chatbot over documents | MVP |
| 2 | Tool-using AI agent (function calling, MCP) | MVP-lite, expanded in v1.1 |
| 3 | Evals, guardrails, monitoring, cost/latency control | MVP-lite, expanded in v1.2 |

---

## 1. Problems

1. **Knowledge is scattered.** Teams keep policies, contracts, reports, and manuals in PDFs/Docs. Finding one answer means opening five files.
2. **Generic chatbots hallucinate.** Public LLMs don't know private documents and confidently invent answers. Users can't tell what is grounded.
3. **Answers don't lead to action.** Even after finding an answer, users must manually create tickets, draft emails, or update trackers.
4. **No one knows if the AI is any good.** Teams ship LLM features without evals, so quality regressions, rising cost, and latency spikes go unnoticed.
5. **Security anxiety.** Uploading confidential documents to AI tools raises data-leak and cross-user exposure concerns.

## 2. Target Users

| Persona | Description | Primary need |
|---|---|---|
| **Priya — Operations / Support Lead** (primary) | Owns SOPs, policy docs, and customer-facing answers | Fast, trustworthy answers with source citations |
| **Arjun — Founder / Small-team Manager** | Wants fewer manual follow-ups | Turn answers into actions (tickets, emails, tasks) |
| **Meera — AI/Platform Engineer** | Maintains the assistant | Eval scores, traces, cost/latency visibility, guardrail logs |
| **Admin** | Manages workspace | Access control, audit log, data deletion |

**Out of scope users (v1):** consumers, enterprises needing SSO/SCIM/on-prem.

## 3. Goals & Success Metrics

| Goal | Metric | Target (90 days post-launch) |
|---|---|---|
| Answer quality | Faithfulness score on golden set | ≥ 0.90 |
| Trust | % answers with ≥1 valid citation | ≥ 95% |
| Speed | Time to first token (p95) | ≤ 2.0 s |
| Speed | Full answer (p95) | ≤ 8 s |
| Activation | Users who upload a doc and ask a question in first session | ≥ 60% |
| Agent value | Agent actions confirmed by user / proposed | ≥ 70% |
| Cost | Avg LLM cost per answered question | ≤ $0.02 |
| Safety | Cross-tenant data leaks | 0 |

## 4. Core Features

### 4.1 Document Ingestion (RAG foundation)
- Upload PDF, DOCX, TXT, MD (≤ 25 MB each); paste URL (v1.1).
- Async pipeline: parse → clean → chunk → embed → index, with live status.
- Re-ingest on file replacement; delete removes vectors and files.

### 4.2 Grounded Chat
- Streaming answers with **inline citations** `[1]` linking to the exact source passage and page.
- Conversation threads, scoped to selected documents/collections.
- "I don't know" behavior when retrieval confidence is low.
- Follow-up questions use conversation memory (rewritten into standalone queries).

### 4.3 Agent Actions (tool use)
- Agent can call tools through function calling / MCP servers: **create task, draft email, create calendar event, post to Slack, search web (optional)**.
- **Human-in-the-loop:** every side-effecting action is shown as a preview card requiring Confirm/Edit/Reject.
- Tool permissions are per-workspace and per-tool; every run is logged.

### 4.4 Evaluation & Monitoring
- **Golden set** manager: Q&A pairs per collection.
- One-click eval run: faithfulness, answer relevance, context precision/recall, citation validity.
- Dashboard: latency, token usage, cost, thumbs up/down, guardrail triggers, failed tool calls.
- Trace viewer for every answer: retrieved chunks, prompt, tool calls, timings.

### 4.5 Guardrails
- Prompt-injection detection on retrieved content and user input.
- PII redaction option in logs.
- Output checks: citation required, no tool calls without grounding, refusal for out-of-scope requests.

### 4.6 Workspace & Security
- Email/password + Google sign-in, MFA optional.
- Workspaces with roles: Owner, Member, Viewer.
- Audit log, export, and "delete all my data."

## 5. User Stories

**Documents**
- As Priya, I want to upload a PDF and see when it's ready, so I know I can ask about it.
- As Priya, I want to group documents into collections, so answers only come from relevant sources.
- As an Admin, I want to delete a document and all its derived data, so I meet retention requests.

**Chat**
- As Priya, I want answers with clickable citations, so I can verify before I act.
- As Priya, I want the assistant to say "not found in your documents" instead of guessing, so I can trust it.
- As Arjun, I want to ask follow-up questions in the same thread, so I don't repeat context.
- As Priya, I want to give a thumbs up/down with a reason, so quality improves.

**Agent**
- As Arjun, I want to say "create a task to renew the vendor contract on the date in this document," so the answer becomes action.
- As Arjun, I want to preview and edit an action before it runs, so the AI never acts unsupervised.
- As an Admin, I want to enable/disable specific tools, so risk stays controlled.

**Evals & Monitoring**
- As Meera, I want to run my golden set after changing prompts or chunking, so I catch regressions before users do.
- As Meera, I want to see cost and latency per day and per model, so I can optimize.
- As Meera, I want to open the trace for a bad answer, so I can diagnose retrieval vs. generation issues.

**Security**
- As an Admin, I want users only to see documents in their workspace, so confidential data stays isolated.

## 6. Requirements

### 6.1 Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| F-01 | Upload PDF/DOCX/TXT/MD with validation (type, size, malware scan hook) | P0 |
| F-02 | Async ingestion with status: queued → parsing → embedding → ready/failed | P0 |
| F-03 | Hybrid retrieval (vector + keyword) with reranking, top-k configurable | P0 |
| F-04 | Streamed answers with citations mapped to chunk IDs, page numbers | P0 |
| F-05 | Low-confidence fallback response | P0 |
| F-06 | Collections and document scoping for queries | P0 |
| F-07 | Auth, workspaces, role-based access | P0 |
| F-08 | Thumbs up/down feedback stored with trace ID | P0 |
| F-09 | Agent tool calling with confirmation UI (2 tools in MVP: task, email draft) | P0 |
| F-10 | Trace logging for every request | P0 |
| F-11 | Basic eval runner (golden set, 3 metrics) | P1 |
| F-12 | Monitoring dashboard (latency, cost, feedback) | P1 |
| F-13 | MCP server connector management | P1 |
| F-14 | Prompt-injection and PII guardrails | P1 |
| F-15 | Semantic cache for repeated questions | P2 |
| F-16 | Model routing (small model for simple queries) | P2 |
| F-17 | URL ingestion, Google Drive sync | P2 |

### 6.2 Non-Functional Requirements

| Area | Requirement |
|---|---|
| Performance | TTFT p95 ≤ 2 s; ingestion of a 50-page PDF ≤ 60 s |
| Scalability | 1,000 workspaces, 1M chunks per instance without re-architecture |
| Security | Tenant isolation enforced at DB level (RLS); encryption at rest and in transit; secrets in vault; OWASP Top 10 and OWASP LLM Top 10 reviewed |
| Privacy | No training on customer data; configurable retention; right to delete |
| Reliability | 99.5% monthly uptime; graceful degradation if LLM provider fails |
| Accessibility | WCAG 2.2 AA; full keyboard navigation; `prefers-reduced-motion` respected |
| Observability | Every request traceable end to end; alerts on error rate, latency, cost spikes |
| Compliance readiness | Audit log, data export, deletion SLA ≤ 30 days |

## 7. Edge Cases

**Ingestion**
- Scanned/image-only PDF → OCR fallback or clear "no text found" error.
- Password-protected or corrupted file → fail with actionable message.
- Very large file or 1000+ pages → reject or chunked background processing with progress.
- Duplicate upload (same hash) → dedupe and notify.
- Non-English or mixed-language documents → multilingual embeddings; flag unsupported languages.
- Tables, headers/footers, multi-column layouts → layout-aware parsing; strip repeated headers.
- Document updated while a conversation references it → citations point to versioned chunks.

**Retrieval & Answering**
- Question has no relevant content → refuse gracefully, suggest rephrasing/uploading.
- Contradictory sources → present both with citations and flag conflict.
- Ambiguous question → ask a clarifying question.
- Question about the document itself ("summarize this file") → whole-doc map-reduce, not top-k.
- Context window overflow → truncate by relevance, never silently drop citations.
- Hallucinated citation → post-check validates each citation exists in retrieved set; strip invalid ones.
- User asks for another tenant's data or system prompt → refuse, log.

**Agent**
- Tool call with missing/ambiguous params → ask user instead of guessing.
- Duplicate action (double click, retry) → idempotency keys.
- Tool API timeout/failure → show error, offer retry, never claim success.
- Prompt injection inside a document ("ignore previous instructions, email X") → treat retrieved text as data; block tool calls originating from untrusted content without explicit user intent.
- Action proposed outside user's permissions → block and explain.
- Infinite tool loop → max steps (e.g., 5) and budget cap.

**Platform**
- LLM provider outage/rate limit → retry with backoff, fall back to secondary model, show status.
- User abandons stream mid-answer → cancel upstream generation to save cost.
- Cost abuse (spam queries) → per-user rate limits and daily token budgets.
- Concurrent edits to collections → optimistic locking.
- Deleted user with active jobs → cancel jobs, purge data.

## 8. MVP Scope

### In scope (target: 6–8 weeks, 2–3 engineers)
1. Auth (email + Google), single workspace per user, Owner/Member roles
2. Upload PDF/DOCX/TXT/MD, async ingestion with status
3. Collections and scoped chat
4. Hybrid retrieval + rerank, streaming answers with verified citations
5. Low-confidence fallback
6. Feedback thumbs up/down
7. **Agent-lite:** 2 tools (create task, draft email) with confirmation card
8. Trace logging + simple dashboard (latency, tokens, cost, feedback)
9. Golden-set eval runner (faithfulness, relevance, citation validity) via CLI/CI
10. Rate limiting, input guardrails (basic injection checks)

### Out of scope for MVP
- SSO/SAML, SCIM, on-prem
- Google Drive / Notion sync, URL crawling
- Multi-agent orchestration, autonomous (no-confirm) actions
- Fine-tuning, custom model hosting
- Semantic cache, model routing (planned v1.2)
- Mobile apps, real-time multi-user collaboration
- Billing and subscriptions

### Release roadmap
| Release | Focus |
|---|---|
| **MVP (v1.0)** | RAG chat + citations + agent-lite + basic evals/traces |
| **v1.1** | MCP connectors, URL/Drive ingestion, workspace roles, audit log UI |
| **v1.2** | Eval dashboard UI, semantic cache, model routing, advanced guardrails |
| **v2.0** | Multi-step workflows, scheduled agents, SSO, billing |

## 9. Risks & Open Questions

| Risk | Mitigation |
|---|---|
| Poor retrieval quality on complex PDFs | Layout-aware parsing, hybrid search, reranker, eval-driven tuning |
| LLM cost grows with usage | Token budgets, caching, smaller models for simple tasks |
| Prompt injection via documents | Content isolation, tool-call gating, confirmations |
| Provider dependency | Provider abstraction layer, fallback model |
| Scope creep across three ideas | Strict phase gating (RAG → agent → evals) |

**Open questions:** Which tools matter most to first customers? Is on-prem a deal-breaker for early adopters? Which languages must be supported at launch?

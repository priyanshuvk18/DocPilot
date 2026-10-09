"""
Application configuration — loaded from environment variables only.

Rules:
  - NEVER hardcode secrets. All sensitive values come from env or vault.
  - SecretStr values are never serialized to logs or responses.
  - Changing these settings requires a restart (they are read at import time).

Usage:
  from app.core.config import settings
  print(settings.environment)
"""
from __future__ import annotations

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application settings, loaded from environment variables.
    Supports .env files for local development.
    In production, variables are injected by the deployment platform.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    # CORS — comma-separated list of allowed origins
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"]
    )

    # ── Database (Postgres + pgvector) ─────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://docpilot:docpilot_dev@localhost:5432/docpilot",
        description="Async SQLAlchemy database URL (asyncpg driver)",
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30

    # ── Redis ──────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Supabase Auth ──────────────────────────────────────────────────────
    supabase_url: str = "https://placeholder.supabase.co"
    supabase_anon_key: SecretStr = SecretStr("placeholder-anon-key")
    supabase_service_role_key: SecretStr = SecretStr("placeholder-service-role-key")
    supabase_jwt_secret: SecretStr = SecretStr("placeholder-jwt-secret")
    supabase_jwks_url: str = (
        "https://placeholder.supabase.co/auth/v1/.well-known/jwks.json"
    )

    # Local dev flag — skips JWT verification and uses a mock user.
    # MUST be false in staging and production.
    auth_disabled: bool = False

    # ── LLM — Anthropic Claude ──────────────────────────────────────────────
    anthropic_api_key: SecretStr = SecretStr("placeholder-anthropic-key")
    # Claude Sonnet-class: high-quality answers
    anthropic_model_answer: str = "claude-sonnet-4-5"
    # Claude Haiku-class: cheap tasks (query rewrite, classification)
    anthropic_model_cheap: str = "claude-haiku-4-5"
    anthropic_max_tokens: int = 2048

    # ── Embeddings — Voyage AI ─────────────────────────────────────────────
    # NOTE: voyage-3-lite produces 512-dim vectors.
    # The database schema uses vector(512) — see SCHEMA_DEVIATION.md.
    # Architecture.md specified vector(1024) (voyage-3); we deviated on request.
    voyage_api_key: SecretStr = SecretStr("placeholder-voyage-key")
    voyage_embedding_model: str = "voyage-3-lite"
    voyage_rerank_model: str = "rerank-2"
    voyage_embedding_dim: int = 512  # DEVIATION: was 1024 per Architecture.md

    # ── Object Storage (S3-compatible) ─────────────────────────────────────
    storage_endpoint_url: str = "http://localhost:9000"
    storage_access_key_id: SecretStr = SecretStr("minioadmin")
    storage_secret_access_key: SecretStr = SecretStr("minioadmin_dev")
    storage_bucket_name: str = "docpilot-documents"
    storage_region: str = "us-east-1"
    storage_signed_url_expiry_seconds: int = 3600

    # ── Observability ──────────────────────────────────────────────────────
    sentry_dsn: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: SecretStr = SecretStr("")
    langfuse_host: str = "https://cloud.langfuse.com"

    # ── Rate limits ────────────────────────────────────────────────────────
    rate_limit_requests_per_minute: int = 60
    rate_limit_tokens_per_day: int = 500_000
    rate_limit_burst: int = 20

    # ── RAG parameters ─────────────────────────────────────────────────────
    retrieval_top_k: int = 20            # candidates from vector + keyword search
    retrieval_rerank_top_k: int = 6      # final chunks sent to LLM after rerank
    retrieval_confidence_threshold: float = 0.3  # RRF score below → "not found"
    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 80
    max_document_size_bytes: int = 25 * 1024 * 1024  # 25 MB

    # ── Agent ──────────────────────────────────────────────────────────────
    agent_max_steps: int = 5
    agent_max_cost_usd: float = 0.10  # per agent run budget cap


# Singleton — imported by all modules
settings = Settings()

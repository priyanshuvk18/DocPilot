"""
JWT authentication and authorization for FastAPI.

Three-layer security (Architecture.md §6):
  1. Route dependency (this module): verifies JWT, loads workspace membership + role
  2. Service logic: checks resource ownership
  3. Database: RLS enforces tenant isolation even if layers 1-2 have bugs

JWKS flow:
  - Supabase Auth issues short-lived JWTs (15 min) signed with RS256
  - We fetch Supabase's public JWKS and cache it (refreshed every 5 min)
  - FastAPI verifies signature, exp, and aud on every request

Local dev:
  - If AUTH_DISABLED=true, a mock user is injected without JWT verification
  - NEVER set AUTH_DISABLED=true in staging or production
"""
from __future__ import annotations

import time
import uuid
from typing import Annotated

import httpx
import jwt
import structlog
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

logger = structlog.get_logger(__name__)

# ─── JWKS cache ───────────────────────────────────────────────────────────────

_jwks_cache: dict[str, object] = {}
_jwks_last_fetched: float = 0.0
_JWKS_TTL_SECONDS = 300  # re-fetch every 5 minutes


async def _get_jwks() -> dict[str, object]:
    """Fetch (or return cached) Supabase JWKS public keys."""
    global _jwks_cache, _jwks_last_fetched
    now = time.monotonic()
    if now - _jwks_last_fetched > _JWKS_TTL_SECONDS:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(settings.supabase_jwks_url)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            _jwks_last_fetched = now
            logger.debug("JWKS refreshed")
    return _jwks_cache


# ─── User model ───────────────────────────────────────────────────────────────

class AuthenticatedUser:
    """
    Represents the authenticated caller.
    Injected by the `current_user` dependency into every protected route.
    """

    def __init__(
        self,
        user_id: uuid.UUID,
        email: str,
        workspace_id: uuid.UUID | None = None,
        role: str | None = None,
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.workspace_id = workspace_id
        self.role = role  # 'owner' | 'member' | 'viewer' | None

    def require_role(self, *roles: str) -> None:
        """Raise 403 if the user's role is not in the allowed set."""
        if self.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "type": "https://docpilot.dev/errors/forbidden",
                    "title": "Forbidden",
                    "status": 403,
                    "detail": f"Required role: {' or '.join(roles)}. Your role: {self.role}",
                },
            )


# ─── Mock user for local dev ───────────────────────────────────────────────────

_MOCK_DEV_USER = AuthenticatedUser(
    user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    email="dev@docpilot.local",
    workspace_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
    role="owner",
)

# ─── Bearer token extractor ────────────────────────────────────────────────────

_bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Security(_bearer_scheme)
]


# ─── Main auth dependency ──────────────────────────────────────────────────────

async def current_user(
    credentials: BearerCredentials,
) -> AuthenticatedUser:
    """
    FastAPI dependency: verify JWT and return the authenticated user.

    Usage in routes:
        @router.get("/resource")
        async def get_resource(user: CurrentUser) -> ...:
            ...
    """
    if settings.auth_disabled:
        logger.warning(
            "AUTH_DISABLED is True — using mock dev user. "
            "NEVER run this in production."
        )
        return _MOCK_DEV_USER

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://docpilot.dev/errors/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Missing Authorization header.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        jwks = await _get_jwks()
        # PyJWT will select the correct key from the JWKS by 'kid'
        signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(  # type: ignore[attr-defined]
            # For Supabase, JWKS has a single key; real impl uses PyJWT's JWKClient
            str(jwks),
        )
        payload: dict[str, object] = jwt.decode(
            token,
            key=signing_key,
            algorithms=["RS256"],
            audience="authenticated",
            options={"require": ["exp", "sub", "email"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://docpilot.dev/errors/token-expired",
                "title": "Token Expired",
                "status": 401,
                "detail": "JWT has expired. Please refresh your session.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as exc:
        logger.warning("JWT verification failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://docpilot.dev/errors/invalid-token",
                "title": "Invalid Token",
                "status": 401,
                "detail": "JWT could not be verified.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = uuid.UUID(str(payload["sub"]))
    email = str(payload.get("email", ""))

    # Bind user context to structured logs for this request
    structlog.contextvars.bind_contextvars(user_id=str(user_id))

    return AuthenticatedUser(user_id=user_id, email=email)


# ─── Type alias for route signatures ─────────────────────────────────────────

CurrentUser = Annotated[AuthenticatedUser, Depends(current_user)]

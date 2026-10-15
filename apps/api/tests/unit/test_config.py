"""
Unit tests for core configuration.
Validates that Settings loads correctly from env vars.
"""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_settings_loads_without_error() -> None:
    """Settings can be imported and instantiated without crashing."""
    from app.core.config import Settings
    s = Settings()
    assert s.environment in {"development", "staging", "production", "test"}


@pytest.mark.unit
def test_settings_default_embedding_dim() -> None:
    """voyage-3-lite embedding dim is 512 (SCHEMA DEVIATION from Architecture.md)."""
    from app.core.config import Settings
    s = Settings()
    assert s.voyage_embedding_dim == 512
    assert s.voyage_embedding_model == "voyage-3-lite"


@pytest.mark.unit
def test_settings_auth_disabled_false_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """AUTH_DISABLED defaults to False (safe default)."""
    monkeypatch.delenv("AUTH_DISABLED", raising=False)
    from importlib import reload

    from app.core import config
    reload(config)
    assert config.Settings(_env_file=None).auth_disabled is False


@pytest.mark.unit
def test_settings_invalid_environment_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings rejects invalid environment values."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        from app.core.config import Settings
        Settings(environment="invalid_env")


@pytest.mark.unit
def test_secret_str_not_in_repr() -> None:
    """SecretStr values are not exposed in string representations."""
    from app.core.config import Settings
    s = Settings(anthropic_api_key="sk-secret-12345")  # type: ignore[arg-type]
    assert "sk-secret-12345" not in repr(s)
    assert "sk-secret-12345" not in str(s)

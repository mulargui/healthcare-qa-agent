"""Runtime environment configuration."""

import os

_VALID_ENVS = {"production", "development", "test"}
_DEFAULT_ENV = "development"


def _resolve_env(raw: str | None) -> str:
    """Normalize APP_ENV; unknown values fall back to development (never production)."""
    val = (raw or _DEFAULT_ENV).lower()
    return val if val in _VALID_ENVS else _DEFAULT_ENV


APP_ENV: str = _resolve_env(os.environ.get("APP_ENV"))
IS_PRODUCTION: bool = APP_ENV == "production"

AWS_REGION: str = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

# Agent model: Sonnet in prod, Haiku in dev/test
AGENT_MODEL_ID: str = (
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0" if IS_PRODUCTION
    else "us.anthropic.claude-haiku-4-5-20251001"
)

# Judge model: Opus in prod, Sonnet in dev/test
JUDGE_MODEL_ID: str = (
    "us.anthropic.claude-opus-4-6-v1" if IS_PRODUCTION
    else "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
)

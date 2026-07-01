"""Unit tests — validates agent input validation logic and config module."""

import asyncio

import pytest

from agent import run_agent
from config import IS_PRODUCTION, _resolve_env


class TestEnvVarValidation:
    """Validates that run_agent raises clear errors for missing or empty env vars."""

    def test_missing_healthylinkx_url(self, monkeypatch):
        monkeypatch.delenv("HEALTHYLINKX_MCP_URL", raising=False)
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        with pytest.raises(RuntimeError, match="HEALTHYLINKX_MCP_URL"):
            asyncio.run(run_agent("test question"))

    def test_empty_healthylinkx_url(self, monkeypatch):
        monkeypatch.setenv("HEALTHYLINKX_MCP_URL", "")
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        with pytest.raises(RuntimeError, match="HEALTHYLINKX_MCP_URL"):
            asyncio.run(run_agent("test question"))

    def test_missing_tavily_api_key(self, monkeypatch):
        monkeypatch.setenv("HEALTHYLINKX_MCP_URL", "https://example.com/mcp")
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="TAVILY_API_KEY"):
            asyncio.run(run_agent("test question"))

    def test_empty_tavily_api_key(self, monkeypatch):
        monkeypatch.setenv("HEALTHYLINKX_MCP_URL", "https://example.com/mcp")
        monkeypatch.setenv("TAVILY_API_KEY", "")
        with pytest.raises(RuntimeError, match="TAVILY_API_KEY"):
            asyncio.run(run_agent("test question"))


class TestConfig:
    def test_default_when_unset(self):
        assert _resolve_env(None) == "development"

    def test_default_when_empty(self):
        assert _resolve_env("") == "development"

    def test_production(self):
        assert _resolve_env("production") == "production"

    def test_development(self):
        assert _resolve_env("development") == "development"

    def test_test(self):
        assert _resolve_env("test") == "test"

    def test_case_insensitive(self):
        assert _resolve_env("Production") == "production"
        assert _resolve_env("TEST") == "test"

    def test_invalid_falls_back_to_development(self):
        assert _resolve_env("staging") == "development"
        assert _resolve_env("PROD") == "development"

    def test_is_production_false_in_test_env(self):
        # test.sh injects APP_ENV=test, so IS_PRODUCTION must be False
        assert IS_PRODUCTION is False

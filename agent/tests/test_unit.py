"""Unit tests — validates agent input validation logic."""

import asyncio

import pytest

from agent import run_agent


class TestEnvVarValidation:
    """Validates that run_agent raises clear errors for missing or empty env vars."""

    def test_missing_healthylinkx_url(self, monkeypatch):
        monkeypatch.delenv("HEALTHYLINKX_MCP_URL", raising=False)
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        with pytest.raises(ValueError, match="HEALTHYLINKX_MCP_URL"):
            asyncio.run(run_agent("test question"))

    def test_empty_healthylinkx_url(self, monkeypatch):
        monkeypatch.setenv("HEALTHYLINKX_MCP_URL", "")
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        with pytest.raises(ValueError, match="HEALTHYLINKX_MCP_URL"):
            asyncio.run(run_agent("test question"))

    def test_missing_tavily_api_key(self, monkeypatch):
        monkeypatch.setenv("HEALTHYLINKX_MCP_URL", "https://example.com/mcp")
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            asyncio.run(run_agent("test question"))

    def test_empty_tavily_api_key(self, monkeypatch):
        monkeypatch.setenv("HEALTHYLINKX_MCP_URL", "https://example.com/mcp")
        monkeypatch.setenv("TAVILY_API_KEY", "")
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            asyncio.run(run_agent("test question"))

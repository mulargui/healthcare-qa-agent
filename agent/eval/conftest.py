"""Pytest configuration for evals — adds src/ and tests/ to path, provides mock tools."""

import sys
import os
import json

import pytest
from langchain_core.tools import tool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tests"))

from mock_data import MOCK_DOCTORS, MOCK_SEARCH_RESULTS


def pytest_addoption(parser):
    parser.addoption("--mock-healthylinkx", action="store_true", help="Mock HealthyLinkx MCP server")
    parser.addoption("--mock-tavily", action="store_true", help="Mock Tavily MCP server")


def is_mock_healthylinkx(request):
    return request.config.getoption("--mock-healthylinkx")


def is_mock_tavily(request):
    return request.config.getoption("--mock-tavily")


@pytest.fixture(autouse=True)
def mock_env_vars(request, monkeypatch):
    """Set dummy env vars for mocked services so validation passes."""
    if is_mock_healthylinkx(request) and not os.environ.get("HEALTHYLINKX_MCP_URL"):
        monkeypatch.setenv("HEALTHYLINKX_MCP_URL", "http://mock-healthylinkx")
    if is_mock_tavily(request) and not os.environ.get("TAVILY_API_KEY"):
        monkeypatch.setenv("TAVILY_API_KEY", "mock-tavily-key")


@tool
def mock_SearchDoctors(zipcode: int, lastname: str, specialty: str = "", gender: str = "") -> str:
    """Search for doctors by zipcode, lastname, specialty, and gender."""
    results = MOCK_DOCTORS
    if specialty:
        results = [d for d in results if specialty.lower() in d["Classification"].lower()]
    return json.dumps(results if results else MOCK_DOCTORS[:2])


@tool
def mock_tavily_search(query: str) -> str:
    """Search the web for information."""
    return json.dumps(MOCK_SEARCH_RESULTS)


def get_mock_tools(request):
    """Return mock tools for mocked services."""
    tools = []
    if is_mock_healthylinkx(request):
        t = mock_SearchDoctors
        t.name = "SearchDoctors"
        tools.append(t)
    if is_mock_tavily(request):
        t = mock_tavily_search
        t.name = "tavily_search"
        tools.append(t)
    return tools if tools else None

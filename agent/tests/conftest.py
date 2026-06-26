"""Pytest configuration — adds src/ to the Python path and provides mock fixtures."""

import sys
import os
import json
from contextlib import asynccontextmanager
from unittest.mock import patch
from functools import partial

import pytest
from langchain_core.tools import tool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ---------------------------------------------------------------------------
# CLI flags
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption("--mock-healthylinkx", action="store_true", help="Mock HealthyLinkx MCP server")
    parser.addoption("--mock-tavily", action="store_true", help="Mock Tavily MCP server")
    parser.addoption("--mock-bedrock", action="store_true", help="Mock AWS Bedrock LLM")


def is_mock_healthylinkx(request):
    return request.config.getoption("--mock-healthylinkx")


def is_mock_tavily(request):
    return request.config.getoption("--mock-tavily")


def is_mock_bedrock(request):
    return request.config.getoption("--mock-bedrock")


def is_any_mock(request):
    return is_mock_healthylinkx(request) or is_mock_tavily(request) or is_mock_bedrock(request)


def is_all_mocked(request):
    return is_mock_healthylinkx(request) and is_mock_tavily(request) and is_mock_bedrock(request)


def is_only_bedrock_mocked(request):
    return is_mock_bedrock(request) and not is_mock_healthylinkx(request) and not is_mock_tavily(request)


# ---------------------------------------------------------------------------
# Env var fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_env_vars(request, monkeypatch):
    """Set dummy env vars for mocked services so validation passes."""
    if is_mock_healthylinkx(request) and not os.environ.get("HEALTHYLINKX_MCP_URL"):
        monkeypatch.setenv("HEALTHYLINKX_MCP_URL", "http://mock-healthylinkx")
    if is_mock_tavily(request) and not os.environ.get("TAVILY_API_KEY"):
        monkeypatch.setenv("TAVILY_API_KEY", "mock-tavily-key")
    if is_mock_bedrock(request):
        monkeypatch.setenv("AWS_DEFAULT_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))


# ---------------------------------------------------------------------------
# Mock MCP tools
# ---------------------------------------------------------------------------

MOCK_DOCTORS = [
    {"Name": "Dr. Sarah Johnson, MD", "Address": "1234 Medical Ave", "City": "Seattle", "Classification": "Neurology"},
    {"Name": "Dr. Michael Chen, MD", "Address": "5678 Vision Blvd", "City": "Seattle", "Classification": "Ophthalmology"},
    {"Name": "Tana Anderson, MA, LMHC", "Address": "15600 Redmond Ave, Suite 101", "City": "Redmond", "Classification": "Counselor"},
    {"Name": "Dr. Robert Kim, MD", "Address": "300 Bone St", "City": "Redmond", "Classification": "Orthopedist"},
    {"Name": "Dr. Lisa Martinez, MD", "Address": "400 Heart Rd", "City": "Seattle", "Classification": "Cardiology"},
    {"Name": "Dr. David Brown, MD", "Address": "500 Cardiac Ave", "City": "Tacoma", "Classification": "Cardiology"},
]

MOCK_SEARCH_RESULTS = [
    {
        "title": "Common Cold vs Flu - Health Guide",
        "url": "https://example.com/cold-vs-flu",
        "content": "The common cold and flu are both respiratory illnesses caused by different viruses. "
                   "Flu symptoms are more severe: high fever, body aches, fatigue. Cold symptoms are milder: "
                   "runny nose, sneezing, sore throat.",
    },
    {
        "title": "Headache and Dizziness Causes",
        "url": "https://example.com/headache-dizziness",
        "content": "Recurring headaches combined with dizziness may indicate neurological conditions. "
                   "Common causes include migraines, vestibular disorders, or hypertension.",
    },
]


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


def _get_mock_tools(request):
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
    return tools


# ---------------------------------------------------------------------------
# Canned responses (for fully-mocked mode)
# ---------------------------------------------------------------------------

CANNED_RESPONSES = {
    "headaches": (
        "Based on your symptoms of recurring headaches and blurred vision, these could be "
        "neurological or vision-related conditions. I'd recommend seeing a Neurologist or "
        "Ophthalmologist. Here are specialists in Seattle from the HealthyLinkx directory:\n\n"
        "1. Dr. Sarah Johnson, MD - Neurology\n"
        "   Address: 1234 Medical Ave, Seattle, WA 98101\n"
        "   Dr. Johnson is a board-certified neurologist with 15 years of experience.\n\n"
        "2. Dr. Michael Chen, MD - Ophthalmology\n"
        "   Address: 5678 Vision Blvd, Seattle, WA 98102\n"
        "   Dr. Chen specializes in neuro-ophthalmology and has published extensively.\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
    "counselor in redmond": (
        "Here are counselors in the Redmond, WA area from the HealthyLinkx directory:\n\n"
        "1. Tana Anderson, MA, LMHC - Counselor\n"
        "   Address: 15600 Redmond Ave, Suite 101, Redmond, WA 98052\n"
        "   Tana specializes in cognitive behavioral therapy with 10 years of experience.\n\n"
        "2. Dr. James Park, MD - Counselor\n"
        "   Address: 200 Oak Ave, Redmond, WA 98053\n"
        "   Dr. Park focuses on anxiety and depression treatment.\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
    "cold and the flu": (
        "The common cold and the flu (influenza) are both respiratory illnesses but are caused "
        "by different viruses. The flu tends to be more severe with high fever, body aches, and "
        "fatigue, while a cold usually presents with milder symptoms like a runny nose, sneezing, "
        "and sore throat. The flu can lead to serious complications like pneumonia, especially in "
        "vulnerable populations.\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
    "chest pains": (
        "Sharp chest pains could indicate several cardiovascular or heart-related conditions. "
        "These symptoms should be taken seriously. I'd recommend seeing a Cardiologist or visiting "
        "the emergency room if symptoms are severe. Would you like me to find a specialist in your "
        "area? If so, please provide your location.\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
    "what about orthopedists": (
        "I'd be happy to help find orthopedists, but I need a location. Could you provide "
        "a city, state, or zipcode so I can search the HealthyLinkx directory?\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
    "tell me more about the first doctor": (
        "Tana Anderson is a licensed mental health counselor (LMHC) based in Redmond, WA. She received "
        "her MA from Seattle University and has over 10 years of experience in cognitive behavioral "
        "therapy. She specializes in treating anxiety disorders, depression, and stress management. "
        "Tana is a member of the American Counseling Association.\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
    "cardiologist in seattle": (
        "Here are cardiologists in the Seattle, WA area from the HealthyLinkx directory:\n\n"
        "1. Dr. Lisa Martinez, MD - Cardiology\n"
        "   Address: 400 Heart Rd, Seattle, WA 98101\n"
        "   Dr. Martinez is a board-certified cardiologist.\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
    "actually i meant tacoma": (
        "Here are cardiologists in the Tacoma, WA area from the HealthyLinkx directory:\n\n"
        "1. Dr. David Brown, MD - Cardiology\n"
        "   Address: 500 Cardiac Ave, Tacoma, WA 98401\n"
        "   Dr. Brown specializes in interventional cardiology.\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
    "i don't feel well": (
        "I'm sorry to hear you're not feeling well. Could you describe your symptoms in more "
        "detail? For example, are you experiencing any pain, fatigue, nausea, fever, or other "
        "specific symptoms? This will help me provide more relevant information and guidance."
    ),
    "bad headaches": (
        "Headaches can have many causes including tension, migraines, dehydration, or stress. "
        "If they are recurring or severe, it's worth discussing with a healthcare provider.\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
    "feeling dizzy": (
        "Dizziness combined with your headaches could suggest several conditions. The combination "
        "of headaches and dizziness may point to neurological causes. I'd recommend monitoring your "
        "symptoms and considering seeing a specialist.\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
    "who should i see": (
        "Given your combination of headaches and dizziness, I'd recommend seeing a Neurologist. "
        "Here are neurologists in the Seattle, WA area from the HealthyLinkx directory:\n\n"
        "1. Dr. Anna Lee, MD - Neurology\n"
        "   Address: 600 Brain Ave, Seattle, WA 98101\n"
        "   Dr. Lee specializes in headache disorders and vestibular neurology.\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
}


def _find_response(question):
    q = question.lower()
    for key, response in CANNED_RESPONSES.items():
        if key in q:
            return response
    return (
        "I can help with health questions and finding doctors. "
        "Could you provide more details about your symptoms or what type of doctor you're looking for?"
    )


SESSION_CONTEXTUAL_RESPONSES = {
    ("redmond", "orthopedists"): (
        "Here are orthopedists in the Redmond, WA area from the HealthyLinkx directory:\n\n"
        "1. Dr. Robert Kim, MD - Orthopedist\n"
        "   Address: 300 Bone St, Redmond, WA 98052\n"
        "   Dr. Kim specializes in sports medicine and joint replacement.\n\n"
        "This information is for educational purposes only and is not a substitute for "
        "professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
    ),
}


@asynccontextmanager
async def _mock_agent_session():
    history = []

    async def ask(question):
        q = question.lower()
        for (ctx_key, q_key), response in SESSION_CONTEXTUAL_RESPONSES.items():
            if q_key in q and any(ctx_key in prev for prev in history):
                history.append(q)
                return response
        history.append(q)
        return _find_response(question)

    yield ask


# ---------------------------------------------------------------------------
# Partial mock: wrap real agent_session with tool overrides
# ---------------------------------------------------------------------------

def _build_live_mcp_config(request):
    """Build MCP client config for non-mocked servers only."""
    import os
    config = {}
    if not is_mock_healthylinkx(request):
        config["healthylinkx"] = {
            "url": os.environ["HEALTHYLINKX_MCP_URL"],
            "transport": "streamable_http",
        }
    if not is_mock_tavily(request):
        tavily_api_key = os.environ["TAVILY_API_KEY"]
        config["tavily"] = {
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_api_key}",
            "transport": "streamable_http",
        }
    return config


def _make_partial_mock_session(mock_tools, live_mcp_config, real_agent_session):
    """Create an agent_session wrapper that combines live MCP tools with mock tools."""
    @asynccontextmanager
    async def _patched_session(tools_override=None, llm_override=None):
        combined_tools = list(mock_tools)
        if live_mcp_config:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            client = MultiServerMCPClient(live_mcp_config)
            live_tools = await client.get_tools()
            combined_tools.extend(live_tools)
        async with real_agent_session(tools_override=combined_tools, llm_override=llm_override) as ask:
            yield ask
    return _patched_session


# ---------------------------------------------------------------------------
# Main mock fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_agent_session(request):
    """Three-tier mocking for acceptance tests.

    Tier 1 (all mocked): Replace agent_session/run_agent with canned responses.
    Tier 2 (partial MCP mock, live Bedrock): Inject mock tools into real agent_session.
    Tier 3 (only Bedrock mocked): Skip acceptance tests.
    """
    if not is_any_mock(request):
        yield
        return

    if request.fspath.basename == "test_unit.py":
        yield
        return

    if request.fspath.basename == "test_integration.py":
        yield
        return

    import agent as agent_module

    # Tier 1: all mocked — fast canned responses
    if is_all_mocked(request):
        async def mock_run_agent(question):
            return _find_response(question)

        with patch.object(agent_module, "agent_session", _mock_agent_session), \
             patch.object(agent_module, "run_agent", mock_run_agent):
            yield
        return

    # Tier 3: bedrock mocked (but not all three) — can't run acceptance tests
    if is_mock_bedrock(request):
        pytest.skip("Acceptance tests require a live LLM unless all services are mocked")
        return

    # Tier 2: partial MCP mock with live Bedrock
    mock_tools = _get_mock_tools(request)
    live_mcp_config = _build_live_mcp_config(request)
    real_session = agent_module.agent_session
    patched_session = _make_partial_mock_session(mock_tools, live_mcp_config, real_session)

    with patch.object(agent_module, "agent_session", patched_session):
        yield

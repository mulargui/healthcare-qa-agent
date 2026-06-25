"""Pytest configuration — adds src/ to the Python path and provides mock fixtures."""

import sys
import os
from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


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


@pytest.fixture(autouse=True)
def mock_env_vars(request, monkeypatch):
    """Set dummy env vars for mocked services so validation passes."""
    if is_mock_healthylinkx(request) and not os.environ.get("HEALTHYLINKX_MCP_URL"):
        monkeypatch.setenv("HEALTHYLINKX_MCP_URL", "http://mock-healthylinkx")
    if is_mock_tavily(request) and not os.environ.get("TAVILY_API_KEY"):
        monkeypatch.setenv("TAVILY_API_KEY", "mock-tavily-key")
    if is_mock_bedrock(request):
        monkeypatch.setenv("AWS_DEFAULT_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))


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
        "1. Dr. Emily Watson, MD - Counselor\n"
        "   Address: 100 Main Street, Redmond, WA 98052\n"
        "   Dr. Watson specializes in cognitive behavioral therapy with 10 years of experience.\n\n"
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
        "Dr. Emily Watson is a licensed counselor based in Redmond, WA. She received her MD from "
        "the University of Washington and has over 10 years of experience in cognitive behavioral "
        "therapy. She specializes in treating anxiety disorders, depression, and stress management. "
        "Dr. Watson is board-certified and a member of the American Counseling Association.\n\n"
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


@pytest.fixture(autouse=True)
def mock_agent_session(request):
    """Patch agent_session and run_agent with canned responses when any mock flag is set.

    Skips patching for unit tests (test_unit.py) since they test env var validation
    and need the real run_agent to raise before reaching external services.
    """
    if not is_any_mock(request):
        yield
        return

    if request.fspath.basename == "test_unit.py":
        yield
        return

    import agent as agent_module

    async def mock_run_agent(question):
        return _find_response(question)

    with patch.object(agent_module, "agent_session", _mock_agent_session), \
         patch.object(agent_module, "run_agent", mock_run_agent):
        yield

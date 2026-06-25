"""Integration tests — validates connectivity between agent components (from architecture doc)."""

import asyncio
import os
import time

import pytest

import agent
from agent import BEDROCK_MODEL_ID
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_aws import ChatBedrockConverse
from conftest import is_mock_healthylinkx, is_mock_tavily, is_mock_bedrock, is_any_mock


class TestAgentConnectsToHealthyLinkxMCPServer:
    """Spec: docs/architecture.md > System and Integration Tests > Agent Core connects to HealthyLinkx MCP server."""

    @pytest.fixture(autouse=True)
    def skip_if_mocked(self, request):
        if is_mock_healthylinkx(request):
            pytest.skip("HealthyLinkx MCP server is mocked")

    def test_search_doctors_returns_results(self):
        async def _test():
            url = os.environ["HEALTHYLINKX_MCP_URL"]
            client = MultiServerMCPClient(
                {"healthylinkx": {"url": url, "transport": "streamable_http"}}
            )
            tools = await client.get_tools()
            tool_names = [t.name for t in tools]
            assert "SearchDoctors" in tool_names

            search_tool = next(t for t in tools if t.name == "SearchDoctors")
            result = await search_tool.ainvoke(
                {"zipcode": 98101, "lastname": "", "specialty": "Cardiology"}
            )
            assert result is not None
            assert len(str(result)) > 0

        asyncio.run(_test())


class TestAgentConnectsToBedrock:
    """Spec: docs/architecture.md > System and Integration Tests > Agent Core connects to Bedrock."""

    @pytest.fixture(autouse=True)
    def skip_if_mocked(self, request):
        if is_mock_bedrock(request):
            pytest.skip("Bedrock is mocked")

    def test_bedrock_returns_response(self):
        async def _test():
            llm = ChatBedrockConverse(
                model=BEDROCK_MODEL_ID,
                region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            )
            start = time.time()
            response = await llm.ainvoke("Say hello in one word.")
            elapsed = time.time() - start
            assert response.content is not None
            assert len(response.content) > 0
            assert elapsed < 15, f"Bedrock response took {elapsed:.1f}s, expected under 15s"

        asyncio.run(_test())


class TestAgentConnectsToTavilyMCPServer:
    """Spec: docs/architecture.md > System and Integration Tests > Agent Core connects to Tavily MCP server."""

    @pytest.fixture(autouse=True)
    def skip_if_mocked(self, request):
        if is_mock_tavily(request):
            pytest.skip("Tavily MCP server is mocked")

    def test_tavily_search_returns_results(self):
        async def _test():
            tavily_api_key = os.environ["TAVILY_API_KEY"]
            tavily_url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_api_key}"
            client = MultiServerMCPClient(
                {"tavily": {"url": tavily_url, "transport": "streamable_http"}}
            )
            tools = await client.get_tools()
            tool_names = [t.name for t in tools]
            assert "tavily_search" in tool_names

            search_tool = next(t for t in tools if t.name == "tavily_search")
            result = await search_tool.ainvoke({"query": "common cold symptoms"})
            assert result is not None
            assert len(str(result)) > 0

        asyncio.run(_test())


class TestConversationHistorySentToBedrock:
    """Spec: docs/architecture.md > System and Integration Tests > Conversation history is sent to Bedrock across turns."""

    @pytest.fixture(autouse=True)
    def skip_if_mocked(self, request):
        if is_any_mock(request):
            pytest.skip("Requires all live services")

    def test_follow_up_reflects_prior_context(self):
        async def _test():
            async with agent.agent_session() as ask:
                await ask("Find me a counselor in Redmond, WA")
                second = (await ask("What about orthopedists?")).lower()
                assert "redmond" in second, "Follow-up should reflect location from prior turn"

        asyncio.run(_test())


class TestConversationHistoryNotPersistedToDisk:
    """Spec: docs/architecture.md > System and Integration Tests > Conversation history is not persisted to disk."""

    @pytest.fixture(autouse=True)
    def skip_if_mocked(self, request):
        if is_any_mock(request):
            pytest.skip("Requires all live services")

    def test_new_session_has_no_prior_history(self):
        async def _test():
            async with agent.agent_session() as ask:
                await ask("Find me a counselor in Redmond, WA")

            async with agent.agent_session() as ask:
                response = (await ask("What about orthopedists?")).lower()
                assert "redmond" not in response, "New session should not remember prior session"

        asyncio.run(_test())

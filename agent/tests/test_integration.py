"""Integration tests — validates connectivity between agent components (from architecture doc)."""

import asyncio
import os

import pytest

from agent import run_agent, BEDROCK_MODEL_ID
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_aws import ChatBedrockConverse


class TestAgentConnectsToHealthyLinkxMCPServer:
    """Spec: docs/architecture.md > System and Integration Tests > Agent Core connects to HealthyLinkx MCP server."""

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

    def test_bedrock_returns_response(self):
        async def _test():
            llm = ChatBedrockConverse(
                model=BEDROCK_MODEL_ID,
                region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            )
            response = await llm.ainvoke("Say hello in one word.")
            assert response.content is not None
            assert len(response.content) > 0

        asyncio.run(_test())


class TestAgentConnectsToTavilyMCPServer:
    """Spec: docs/architecture.md > System and Integration Tests > Agent Core connects to Tavily MCP server."""

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

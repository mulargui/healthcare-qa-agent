"""Agent Core — connects to HealthyLinkx and Tavily MCP servers, runs a LangChain ReAct agent on Bedrock."""

import os
from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_aws import ChatBedrockConverse
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from prompts import SYSTEM_PROMPT
from logging_config import get_logger, AgentLoggingCallback

logger = get_logger(__name__)

BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


def _validate_env():
    healthylinkx_url = os.environ.get("HEALTHYLINKX_MCP_URL", "")
    tavily_api_key = os.environ.get("TAVILY_API_KEY", "")

    if not healthylinkx_url:
        raise ValueError("HEALTHYLINKX_MCP_URL environment variable is not set")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY environment variable is not set")

    return healthylinkx_url, tavily_api_key


@asynccontextmanager
async def agent_session(tools_override=None, llm_override=None):
    """Create a session that maintains conversation history across turns.

    Args:
        tools_override: Optional list of LangChain tools to use instead of MCP tools.
        llm_override: Optional LLM instance to use instead of Bedrock.

    Usage:
        async with agent_session() as ask:
            answer1 = await ask("Find me a cardiologist in Seattle")
            answer2 = await ask("What about neurologists?")  # remembers Seattle
    """
    healthylinkx_url, tavily_api_key = _validate_env()

    if tools_override is not None:
        tools = tools_override
        logger.info("Using %d overridden tools", len(tools))
    else:
        tavily_url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_api_key}"

        logger.info("Connecting to MCP servers")
        logger.info("HealthyLinkx MCP: %s", healthylinkx_url)
        logger.info("Tavily MCP: %s", "https://mcp.tavily.com/mcp/")

        client = MultiServerMCPClient(
            {
                "healthylinkx": {
                    "url": healthylinkx_url,
                    "transport": "streamable_http",
                },
                "tavily": {
                    "url": tavily_url,
                    "transport": "streamable_http",
                },
            }
        )

        tools = await client.get_tools()
        logger.info("Loaded %d tools from MCP servers", len(tools))

    if llm_override is not None:
        llm = llm_override
        logger.info("Using overridden LLM")
    else:
        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        logger.info("Creating LLM: %s in %s", BEDROCK_MODEL_ID, region)
        llm = ChatBedrockConverse(model=BEDROCK_MODEL_ID, region_name=region)

    checkpointer = MemorySaver()
    agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT, checkpointer=checkpointer)
    config = {
        "configurable": {"thread_id": "session"},
        "callbacks": [AgentLoggingCallback()],
    }

    async def ask(question: str) -> str:
        logger.info("Invoking agent")
        result = await agent.ainvoke(
            {"messages": [("user", question)]},
            config=config,
        )
        logger.info("Agent invocation complete")
        return result["messages"][-1].content

    yield ask


async def run_agent(question: str) -> str:
    """One-shot API — backwards compatible with single-question mode and tests."""
    try:
        async with agent_session() as ask:
            return await ask(question)
    except Exception as e:
        raise RuntimeError(str(e)) from None

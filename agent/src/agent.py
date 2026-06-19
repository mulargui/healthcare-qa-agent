"""Agent Core — connects to HealthyLinkx and Tavily MCP servers, runs a LangChain ReAct agent on Bedrock."""

import os

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_aws import ChatBedrockConverse
from langgraph.prebuilt import create_react_agent

from prompts import SYSTEM_PROMPT
from logging_config import get_logger, AgentLoggingCallback

logger = get_logger(__name__)

BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


async def run_agent(question: str) -> str:
    healthylinkx_url = os.environ.get("HEALTHYLINKX_MCP_URL", "")
    tavily_api_key = os.environ.get("TAVILY_API_KEY", "")

    if not healthylinkx_url:
        raise ValueError("HEALTHYLINKX_MCP_URL environment variable is not set")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY environment variable is not set")

    tavily_url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_api_key}"

    logger.info("Connecting to MCP servers")
    logger.info("HealthyLinkx MCP: %s", healthylinkx_url)
    logger.info("Tavily MCP: %s", "https://mcp.tavily.com/mcp/")

    try:
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

        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        logger.info("Creating LLM: %s in %s", BEDROCK_MODEL_ID, region)

        llm = ChatBedrockConverse(model=BEDROCK_MODEL_ID, region_name=region)

        agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

        logger.info("Invoking agent")
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"callbacks": [AgentLoggingCallback()]},
        )
        logger.info("Agent invocation complete")

        return result["messages"][-1].content
    except Exception as e:
        raise RuntimeError(str(e)) from None

# Healthcare Q&A Agent

An interactive AI agent that answers healthcare questions and helps users find the right doctor through multi-turn conversations. Describe your symptoms, ask follow-up questions, refine your search — the agent remembers context from earlier in the conversation. It explains conditions, finds relevant specialists in your area using the HealthyLinkx doctor directory, and provides a brief summary of each recommended doctor's background.

## How It Works

1. Start an interactive session or ask a single question via the CLI
2. The agent uses Claude (via AWS Bedrock) to understand your question
3. It searches for health information (via Tavily MCP server) and doctors (via HealthyLinkx MCP server) as needed
4. You get a response combining health guidance and doctor recommendations
5. Ask follow-up questions — the agent remembers your location, symptoms, and prior results
6. Conversation history is kept in memory for the session and discarded on exit

## Motivation

This is my first attempt to build an AI agent harness (with Claude Code help) and understand its intricancies and potential. I plan to add more features in the future and make it more sophisticated.

## Tech Stack

- **Agent**: Python, LangChain, Docker
- **LLM**: Claude via AWS Bedrock
- **Doctor search**: HealthyLinkx MCP server (JavaScript, Lambda)
- **Web search**: Tavily MCP server

## Prerequisites

- AWS account with Bedrock access (Claude model enabled)
- Tavily API key
- Docker
- HealthyLinkx MCP server (https://github.com/mulargui/healthylinkx-mcp-server)

## Quick Start

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
export TAVILY_API_KEY=...
export HEALTHYLINKX_MCP_URL=...

# Interactive session
./infra/run.sh
# > I have chest pain and I'm in Seattle, WA
# (agent explains possible causes, lists cardiologists in Seattle)
# > What about neurologists?
# (agent lists neurologists in Seattle — location carried over)
# > exit

# Single-question mode (backwards compatible)
./infra/run.sh "What's the difference between a cold and the flu?"
```

## Project Structure

```
agent/src/          CLI entry point, agent core, system prompt
agent/tests/        Acceptance, integration, and unit tests
infra/              Dockerfile, requirements.txt, run and test scripts
docs/               Product spec and architecture documents
```

## Testing

```bash
# Fully mocked (no credentials needed)
./infra/test.sh --mock-healthylinkx --mock-tavily --mock-bedrock

# All live (requires credentials)
./infra/test.sh

# See all options
./infra/test.sh --help
```

## Existing Work

This project reuses components from repositories at https://github.com/mulargui, including the HealthyLinkx MCP server, datastore, and infrastructure tooling. See [docs/architecture.md](docs/architecture.md) for details.

## Documentation

- [Product Spec](docs/product%20spec.md) — what the agent does, scope, and acceptance tests
- [Architecture](docs/architecture.md) — components, deployment, tech stack, and integration tests

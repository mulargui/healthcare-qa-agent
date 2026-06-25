# AGENTS.md

## Project Overview

Healthcare Q&A Agent — an interactive CLI tool that answers health questions and recommends doctors through multi-turn conversations. Uses Claude (AWS Bedrock), Tavily for web search, and the HealthyLinkx MCP server for doctor lookups. Supports follow-up questions with context carryover (in-memory, session-scoped). Also supports single-question mode for backwards compatibility.

## Architecture

- **CLI + Agent Core**: Python, LangChain, packaged in Docker
- **LLM**: Claude via AWS Bedrock (Converse API, `ChatBedrockConverse`)
- **Tools**:
  - `tavily_search` — Tavily MCP server (health questions and doctor background lookups)
  - `SearchDoctors` — HealthyLinkx MCP server (JavaScript, Lambda Function URL, queries RDS MySQL)

## Key Design Decisions

- All tools accessed via MCP with streaming support — HealthyLinkx MCP server for doctor search, Tavily MCP server for web search and doctor background lookups
- HealthyLinkx MCP server is external, deployed separately (Lambda Function URL)
- Tavily MCP server for web search — purpose-built for LLM agents, clean structured results
- Doctor summaries via `tavily_search` per doctor (no separate tool or pre-enriched database in v1)
- Interactive multi-turn conversations with in-memory conversation history (discarded on exit)
- Context carryover is always-on — location, symptoms, and doctor lists carry forward unless the user corrects them
- Conversation history via LangGraph's `MemorySaver` checkpointer (no truncation in v1 — known limitation)
- Two CLI modes: interactive prompt loop (no argument) and single-question (with argument, backwards compatible)
- Agent may proactively recommend doctors when clinically appropriate

## Repo Layout

```
CLAUDE.md                  Points here
AGENTS.md                  Project context for AI agents
README.md                  Project overview and quick start
docs/product spec.md       Product requirements, scope, acceptance tests
docs/architecture.md       Components, deployment, tech stack, integration tests
agent/src/main.py               CLI entry point
agent/src/agent.py              Agent Core (LangChain orchestrator, MCP client)
agent/src/prompts.py            System prompt
agent/src/logging_config.py     Logging setup (format with filename and line number)
agent/tests/test_acceptance.py  Acceptance tests (from product spec)
agent/tests/test_integration.py Integration tests (from architecture doc)
agent/tests/test_unit.py        Unit tests (env var validation)
agent/tests/conftest.py         Pytest config, mock fixtures
infra/Dockerfile                Docker image for CLI + Agent Core
infra/requirements.txt          Python dependencies
infra/run.sh                    Build, test, and run script
infra/test.sh                   Run tests with optional mock flags
```

## Reused Repositories

Components from https://github.com/mulargui are reused:
- **healthylinkx-mcp-server** — MCP server for doctor search (primary reuse target)
- **healthylinkx-chat-app** — Bedrock + tool use integration pattern
- **healthylinkx-chat-mcp** — MCP client integration pattern
- **healthylinkx-serverless-node** — datastore schema and seed data
- **healthylinkx-a2a-server** — A2A protocol interface to HealthyLinkx
- **healthylinkx-cdk** — AWS CDK infrastructure reference
- **bedrock-chat-app** — Bedrock configuration patterns

## Coding Conventions

- Agent code: Python
- MCP server / Lambda / infrastructure: JavaScript
- CLI and Agent Core are packaged together in a Docker container
- In-memory conversation history within a session; no persistence across sessions

## Key Docs

- [docs/product spec.md](docs/product%20spec.md) — what the agent does, scope, acceptance tests
- [docs/architecture.md](docs/architecture.md) — components, deployment, tech stack, integration tests

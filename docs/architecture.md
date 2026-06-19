# Healthcare Q&A Agent - Architecture

## Existing Work

Many components needed for this product already exist across repositories at **https://github.com/mulargui**. The architecture reuses them where possible rather than building from scratch.

Key repositories:
- **healthylinkx-mcp-server** — MCP server exposing HealthyLinkx doctor search as tools for LLM agents. TypeScript, AWS Lambda, RDS MySQL.

## High-Level Architecture

```
┌─────────────────┐
│   CLI (stdin)    │
└────────┬────────┘
         │ user question
         ▼
┌─────────────────┐       ┌─────────────────┐
│   Agent Core    │◀────▶│  Claude (LLM)   │
│  (orchestrator) │       │  AWS Bedrock    │
└────────┬────────┘       └─────────────────┘
         │ executes tool calls
         ▼
┌───────────────────────┐  ┌───────────────────────────┐
│  Tavily MCP Server    │  │  HealthyLinkx MCP Server  │
│  - tavily_search      │  │  - SearchDoctors          │
└───────────────────────┘  │  (Lambda, Function URL)   │
                           └───────────────────────────┘
```

## Components

### 1. CLI Interface

A command-line application that takes a user question as input and prints the agent's response.

- Reads the user's question from stdin or command-line argument
- Sends the question to the Agent Core
- Prints the formatted response to stdout
- No conversation history — each invocation is independent
- Packaged with the Agent Core in a Docker container for easy deployment

### 2. Agent Core (Orchestrator)

Sends the user's question to Claude on AWS Bedrock. All tools are accessed via MCP, keeping the orchestrator simple — it is just an MCP client.

- Constructs the system prompt with health Q&A guidelines
- Calls Claude via the AWS Bedrock Converse or InvokeModel API
- Connects to MCP servers for all tools:
  - HealthyLinkx MCP server for `SearchDoctors`
  - Tavily MCP server for `tavily_search` (health questions and doctor background lookups)
- Supports MCP streaming — works with servers that support streaming (Tavily) and those that don't (HealthyLinkx)
- Handles the tool-use loop (call LLM → execute MCP tool → return result → repeat)
- Assembles the final response

### 3. LLM — Claude via AWS Bedrock

Claude handles reasoning: understanding the user's question, deciding which tools to invoke, interpreting results, and composing the final answer.

- Model: Claude (latest available on Bedrock — currently Claude 4 Sonnet or similar)
- System prompt instructs Claude to:
  - Answer health questions using its knowledge and web search
  - Determine the appropriate specialist type from symptoms
  - Search for doctors when a location is provided or the question warrants it
  - Summarize each recommended doctor's background
  - Be proactive about recommending doctors when clinically appropriate

### 4. Tools

#### tavily_search (Tavily MCP server)
Performs a web search to answer general health questions and look up doctor backgrounds.

- Input: search query (string), plus optional parameters (search_depth, max_results)
- Output: search results with snippets
- Used for health Q&A (symptoms, conditions, treatments) and doctor background summaries

**Implementation:** Tavily MCP server — purpose-built for LLM agents, returns clean structured results. Accessed via MCP like all other tools, keeping the Agent Core simple. Requires a Tavily API key. The system prompt instructs Claude to use this tool for both health questions and looking up each recommended doctor's background.

#### SearchDoctors (HealthyLinkx MCP server)
Searches the HealthyLinkx directory for doctors matching specialty and location.

- Input: zipcode (number, required), lastname (string, required), specialty (string, optional), gender (string, optional)
- Output: list of matching doctors (Name, Address, City, Classification)

**Reuse:** This is the core query already implemented in **healthylinkx-mcp-server** (`/mcp/src/`). The MCP server runs in a Lambda and queries RDS directly.

## File Structure

```
CLAUDE.md                  Points to AGENTS.md
AGENTS.md                  Project context for AI agents
README.md                  Project overview and quick start
docs/
  product spec.md          Product requirements, scope, acceptance tests
  architecture.md          Components, deployment, tech stack, integration tests
agent/
  src/
    main.py                CLI entry point
    agent.py               Agent Core (LangChain orchestrator, MCP client)
    prompts.py             System prompt
    logging_config.py      Logging setup (format with filename and line number)
  tests/
    test_acceptance.py     Acceptance tests (from product spec)
    test_integration.py    Integration tests (from architecture doc)
    test_unit.py           Unit tests (env var validation)
infra/
  Dockerfile               Docker image for CLI + Agent Core
  requirements.txt         Python dependencies
  run.sh                   Build, test, and run script
```

The MCP servers are external to this repo — HealthyLinkx is deployed from its own repo, Tavily is a third-party package. The agent only needs their connection configuration.

## Deployment Architecture

The CLI and Agent Core run locally in a Docker container. The LLM is accessed via AWS Bedrock. Doctor search goes through the HealthyLinkx MCP server (Lambda Function URL). Web search goes through the Tavily MCP server (hosted by Tavily).

```
Local machine                    AWS / External
┌──────────────┐        ┌─────────────────────────────┐
│  CLI + Agent │───────▶│  AWS Bedrock (Claude)        │
│  Core        │        ├─────────────────────────────┤
│  (Python,    │───────▶│  HealthyLinkx MCP Server    │
│   Docker)    │        │  (Lambda, Function URL)      │
└──────┬───────┘        └─────────────────────────────┘
       │                ┌─────────────────────────────┐
       └───────────────▶│  Tavily MCP Server          │
                        │  (hosted by Tavily)          │
                        └─────────────────────────────┘
```

- Agent Core runs in a Docker container
- Calls Bedrock directly using AWS SDK credentials
- Doctor queries go through the HealthyLinkx MCP server (Lambda Function URL)
- Web search and doctor background lookups go through the Tavily MCP server

Both MCP servers are external to this repo and assumed to be already deployed. The agent only needs their connection URLs.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| CLI | Python (argparse or similar) |
| Agent Core | Python, LangChain |
| Client container | Docker (CLI + Agent Core) |
| LLM | Claude via AWS Bedrock |
| tavily_search | Tavily MCP server (health questions and doctor background lookups) |
| SearchDoctors | HealthyLinkx MCP server, JavaScript, Lambda Function URL (from healthylinkx-mcp-server) |

## Data Flow

1. User enters a question via the CLI
2. Agent Core sends the question to Claude on Bedrock with the system prompt and tool definitions
3. Claude analyzes the question and decides which tools to call (if any)
4. For health questions: Claude calls `tavily_search` → receives results → incorporates into answer
5. For doctor searches: Claude calls `SearchDoctors` with zipcode and specialty → receives doctor list
6. For doctor backgrounds: Claude calls `tavily_search` for each recommended doctor → receives background info
7. Claude composes a final response combining health information, doctor recommendations, and summaries
8. Agent Core prints the response to stdout

## Technical Decisions Log

1. **Web search provider** — Tavily MCP server. Purpose-built for LLM agents, clean structured results. All tools accessed uniformly via MCP.
2. **Doctor summary source** — Claude uses `tavily_search` to look up each doctor's background. No separate tool needed. Avoids building a data enrichment pipeline for v1; pre-enriched database can be revisited if latency becomes a concern.
3. **Doctor search** — HealthyLinkx MCP server (Lambda Function URL), deployed and managed separately from this repo.

## System and Integration Tests

### Agent Core connects to HealthyLinkx MCP server
- **Given** the Agent Core is running in the Docker container and the HealthyLinkx MCP server is deployed
- **When** the Agent Core invokes the `SearchDoctors` MCP tool
- **Then** it receives a valid response with doctor data

### Agent Core connects to Bedrock
- **Given** the Agent Core is running with valid AWS credentials
- **When** a user question is sent to Claude via Bedrock
- **Then** a response is returned within the expected time

### Agent Core connects to Tavily MCP server
- **Given** the Agent Core is running with a valid Tavily API key and the Tavily MCP server is configured
- **When** the `tavily_search` tool is called with a health-related query via MCP
- **Then** the Tavily MCP server returns structured search results


# Healthcare Q&A Agent - Architecture

## Existing Work

Many components needed for this product already exist across repositories at **https://github.com/mulargui**. The architecture reuses them where possible rather than building from scratch.

Key repositories:
- **healthylinkx-mcp-server** — MCP server exposing HealthyLinkx doctor search as tools for LLM agents. TypeScript, AWS Lambda, RDS MySQL.

## High-Level Architecture

```
┌──────────────────────┐
│   CLI (interactive)  │
│   prompt loop or     │
│   single-question    │
└────────┬─────────────┘
         │ user question + conversation history
         ▼
┌─────────────────┐       ┌─────────────────┐
│   Agent Core    │◀────▶│  Claude (LLM)   │
│  (orchestrator) │       │  AWS Bedrock    │
│                 │       └─────────────────┘
│  conversation   │
│  history        │
│  (in-memory)    │
└────────┬────────┘
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

A command-line application that supports interactive multi-turn conversations and single-question mode.

**Interactive mode** (no argument):
- Displays a welcome message explaining what the agent does and how to exit
- Runs a prompt loop with `> ` indicator
- Reads user input, sends it to the Agent Core, prints the response, and repeats
- Exits on "exit", "quit", Ctrl+C, or EOF
- Ignores empty input (re-displays the prompt)

**Single-question mode** (with argument):
- `./infra/run.sh "question"` — sends the question, prints the answer, and exits
- Backwards compatible with previous behavior

- Packaged with the Agent Core in a Docker container for easy deployment

### 2. Agent Core (Orchestrator)

Sends the user's question and conversation history to Claude on AWS Bedrock. All tools are accessed via MCP, keeping the orchestrator simple — it is just an MCP client.

- Conversation history managed by LangGraph's `MemorySaver` checkpointer — accumulates messages automatically across turns within a session
- History is discarded when the session ends — no persistence to disk
- Constructs the system prompt with health Q&A guidelines
- Calls Claude via the AWS Bedrock Converse API (`ChatBedrockConverse`)
- Connects to MCP servers for all tools:
  - HealthyLinkx MCP server for `SearchDoctors`
  - Tavily MCP server for `tavily_search` (health questions and doctor background lookups)
- Supports MCP streaming — works with servers that support streaming (Tavily) and those that don't (HealthyLinkx)
- Handles the tool-use loop (call LLM → execute MCP tool → return result → repeat)
- Assembles the final response

### 3. LLM — Claude via AWS Bedrock

Claude handles reasoning: understanding the user's question, deciding which tools to invoke, interpreting results, and composing the final answer.

- Model: `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (Bedrock cross-region inference)
- System prompt instructs Claude to:
  - Answer health questions using its knowledge and web search
  - Determine the appropriate specialist type from symptoms
  - Search for doctors when a location is provided or the question warrants it
  - Summarize each recommended doctor's background
  - Be proactive about recommending doctors when clinically appropriate
  - Use context from prior conversation turns without asking the user to repeat themselves

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
  test.sh                  Run tests with optional mock flags
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
| CLI | Python (sys.argv) |
| Agent Core | Python, LangChain |
| Client container | Docker (CLI + Agent Core) |
| LLM | Claude via AWS Bedrock |
| tavily_search | Tavily MCP server (health questions and doctor background lookups) |
| SearchDoctors | HealthyLinkx MCP server, JavaScript, Lambda Function URL (from healthylinkx-mcp-server) |

## Data Flow

**Interactive mode:**
1. CLI displays welcome message and `> ` prompt
2. User enters a question
3. CLI sends the question to the Agent Core
4. Agent Core sends the user message to Claude on Bedrock with the system prompt, tool definitions, and conversation history (managed automatically by LangGraph's `MemorySaver` checkpointer)
5. Claude analyzes the question (with context from prior turns) and decides which tools to call (if any)
6. For health questions: Claude calls `tavily_search` → receives results → incorporates into answer
7. For doctor searches: Claude calls `SearchDoctors` with zipcode and specialty → receives doctor list
8. For doctor backgrounds: Claude calls `tavily_search` for each recommended doctor → receives background info
9. Claude composes a final response combining health information, doctor recommendations, and summaries
10. Agent Core returns the response to the CLI, which prints it to stdout
11. CLI displays `> ` prompt again — repeat from step 2 until the user exits

**Single-question mode:**
- Steps 4–10 execute once, then the process exits

## Technical Decisions Log

1. **Web search provider** — Tavily MCP server. Purpose-built for LLM agents, clean structured results. All tools accessed uniformly via MCP.
2. **Doctor summary source** — Claude uses `tavily_search` to look up each doctor's background. No separate tool needed. Avoids building a data enrichment pipeline for v1; pre-enriched database can be revisited if latency becomes a concern.
3. **Doctor search** — HealthyLinkx MCP server (Lambda Function URL), deployed and managed separately from this repo.
4. **Conversation history** — in-memory via LangGraph's `MemorySaver` checkpointer. No persistence to disk. **Known limitation:** conversation history is not truncated — very long sessions may exceed Bedrock's context window and fail. LangGraph supports truncation via `trim_messages` + `pre_model_hook` on `create_react_agent`, but this is not wired up in v1. For typical CLI usage (under ~20 turns) this is unlikely to be an issue.
5. **CLI modes** — interactive prompt loop (no argument) and single-question mode (with argument). Single-question mode preserves backwards compatibility with previous scripts and automation.

## Test Mocking

Tests depend on three external services: HealthyLinkx MCP server, Tavily MCP server, and AWS Bedrock. Each can be independently mocked via pytest flags:

| Flag | Effect |
|------|--------|
| `--mock-healthylinkx` | Mock the HealthyLinkx MCP server |
| `--mock-tavily` | Mock the Tavily MCP server |
| `--mock-bedrock` | Mock the AWS Bedrock LLM |

No flags = all live (requires credentials). Any combination works. All three = fully local.

**How mocking works by test type:**

- **Acceptance tests** — three tiers based on which flags are set:
  - All three flags: `agent_session`/`run_agent` replaced with canned responses (fast, no external calls). The mock tracks conversation history for multi-turn tests.
  - Partial MCP mock with live Bedrock (e.g. `--mock-healthylinkx --mock-tavily`): mock tools injected into the real `agent_session` via `tools_override`. The real LLM orchestrates with mock tool data.
  - Only Bedrock mocked: acceptance tests skip (a fake LLM can't intelligently call real MCP tools).
- **Integration tests** — skipped when their service is mocked. Mocking a connectivity test defeats its purpose. Session-level integration tests skip when any flag is set.
- **Unit tests** — unaffected by mock flags. They test env var validation and never reach external services.

**Running tests:**

```bash
./infra/test.sh --mock-healthylinkx --mock-tavily --mock-bedrock  # fully mocked
./infra/test.sh --mock-healthylinkx --mock-tavily                 # mock MCP, live Bedrock
./infra/test.sh                                                   # all live
```

`run.sh` runs tests with all mocks on image build to validate the container without credentials.

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

### Conversation history is sent to Bedrock across turns
- **Given** the Agent Core has processed at least one prior turn
- **When** a follow-up question is sent to Claude via Bedrock
- **Then** the request includes the full conversation history and Claude's response reflects prior context

### Conversation history is not persisted to disk
- **Given** the Agent Core has processed a multi-turn conversation
- **When** the session ends
- **Then** no conversation history is written to disk — a new session starts with empty history


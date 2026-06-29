#!/bin/bash
# Run tests for the Healthcare Q&A Agent with optional mocking of external services.

set -e

IMAGE_NAME="healthcare-agent"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
    cat <<EOF
Usage: test.sh [OPTIONS]

Run tests inside the Docker container. Pass mock flags to skip external services.

Mock flags:
  --mock-healthylinkx   Mock the HealthyLinkx MCP server
  --mock-tavily         Mock the Tavily MCP server
  --mock-bedrock        Mock the AWS Bedrock LLM

Other options:
  --help, -h            Show this help message

Examples:
  ./infra/test.sh                                                  # All live (requires credentials)
  ./infra/test.sh --mock-healthylinkx --mock-tavily --mock-bedrock # All mocked (no credentials needed)
  ./infra/test.sh --mock-healthylinkx --mock-tavily                # Mock MCP, live Bedrock
  ./infra/test.sh --mock-bedrock                                   # Mock Bedrock, only integration tests will run (requires credentials for MCP)
EOF
    exit 0
}

for arg in "$@"; do
    case "$arg" in
        --help|-h) usage ;;
    esac
done

echo "Building Docker image..."
docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile" "$PROJECT_DIR"

# Validate env vars for live (non-mocked) services
mock_args="$*"
missing=()
if [[ "$mock_args" != *"--mock-healthylinkx"* ]]; then
    [ -z "$HEALTHYLINKX_MCP_URL" ] && missing+=("HEALTHYLINKX_MCP_URL")
fi
if [[ "$mock_args" != *"--mock-tavily"* ]]; then
    [ -z "$TAVILY_API_KEY" ] && missing+=("TAVILY_API_KEY")
fi
if [[ "$mock_args" != *"--mock-bedrock"* ]]; then
    [ -z "$AWS_ACCESS_KEY_ID" ] && missing+=("AWS_ACCESS_KEY_ID")
    [ -z "$AWS_SECRET_ACCESS_KEY" ] && missing+=("AWS_SECRET_ACCESS_KEY")
    [ -z "$AWS_DEFAULT_REGION" ] && missing+=("AWS_DEFAULT_REGION")
fi

if [ ${#missing[@]} -gt 0 ]; then
    echo "Error: missing environment variables for live services: ${missing[*]}"
    echo "Use --mock-healthylinkx, --mock-tavily, --mock-bedrock to skip, or run with --help"
    exit 1
fi

echo "Running tests..."
docker run --rm \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e AWS_DEFAULT_REGION \
    -e TAVILY_API_KEY \
    -e HEALTHYLINKX_MCP_URL \
    --entrypoint pytest \
    "$IMAGE_NAME" tests/ -v "$@"

#!/bin/bash
# Run evals for the Healthcare Q&A Agent.

set -e

IMAGE_NAME="healthcare-agent"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
    cat <<EOF
Usage: eval.sh [OPTIONS]

Run evals inside the Docker container. Requires a live LLM (Bedrock).

Mock flags:
  --mock-healthylinkx   Mock the HealthyLinkx MCP server
  --mock-tavily         Mock the Tavily MCP server

Other options:
  --help, -h            Show this help message

Examples:
  ./infra/eval.sh --mock-healthylinkx --mock-tavily   # Mock MCP, live Bedrock + judge
  ./infra/eval.sh                                      # All live
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

# Validate env vars — Bedrock is always required for evals
missing=()
[ -z "$AWS_ACCESS_KEY_ID" ] && missing+=("AWS_ACCESS_KEY_ID")
[ -z "$AWS_SECRET_ACCESS_KEY" ] && missing+=("AWS_SECRET_ACCESS_KEY")
[ -z "$AWS_DEFAULT_REGION" ] && missing+=("AWS_DEFAULT_REGION")

mock_args="$*"
if [[ "$mock_args" != *"--mock-healthylinkx"* ]]; then
    [ -z "$HEALTHYLINKX_MCP_URL" ] && missing+=("HEALTHYLINKX_MCP_URL")
fi
if [[ "$mock_args" != *"--mock-tavily"* ]]; then
    [ -z "$TAVILY_API_KEY" ] && missing+=("TAVILY_API_KEY")
fi

if [ ${#missing[@]} -gt 0 ]; then
    echo "Error: missing environment variables: ${missing[*]}"
    echo "Use --mock-healthylinkx, --mock-tavily to skip MCP services, or run with --help"
    exit 1
fi

echo "Running evals..."
docker run --rm \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e AWS_DEFAULT_REGION \
    -e TAVILY_API_KEY \
    -e HEALTHYLINKX_MCP_URL \
    -v "$PROJECT_DIR/logs:/output" \
    --entrypoint pytest \
    "$IMAGE_NAME" eval/run_evals.py -v "$@"

LATEST=$(ls -t "$PROJECT_DIR/logs"/eval_results_*.json 2>/dev/null | head -1)
[ -n "$LATEST" ] && echo "Last results saved to: $LATEST"

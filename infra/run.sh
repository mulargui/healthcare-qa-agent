#!/bin/bash
# Run the Healthcare Q&A Agent — builds the image if needed, runs tests, then runs the question.

set -e

IMAGE_NAME="healthcare-agent"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Validate required env vars
missing=()
[ -z "$AWS_ACCESS_KEY_ID" ] && missing+=("AWS_ACCESS_KEY_ID")
[ -z "$AWS_SECRET_ACCESS_KEY" ] && missing+=("AWS_SECRET_ACCESS_KEY")
[ -z "$AWS_DEFAULT_REGION" ] && missing+=("AWS_DEFAULT_REGION")
[ -z "$TAVILY_API_KEY" ] && missing+=("TAVILY_API_KEY")
[ -z "$HEALTHYLINKX_MCP_URL" ] && missing+=("HEALTHYLINKX_MCP_URL")

if [ ${#missing[@]} -gt 0 ]; then
    echo "Error: missing environment variables: ${missing[*]}"
    exit 1
fi

# Validate question argument
if [ $# -eq 0 ]; then
    echo "Usage: run.sh \"your health question\""
    exit 1
fi

# Build image and run tests if image doesn't exist
if ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo "Building Docker image..."
    docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile" "$PROJECT_DIR"

    echo "Running tests..."
    docker run --rm \
        -e AWS_ACCESS_KEY_ID \
        -e AWS_SECRET_ACCESS_KEY \
        -e AWS_DEFAULT_REGION \
        -e TAVILY_API_KEY \
        -e HEALTHYLINKX_MCP_URL \
        --entrypoint pytest \
        "$IMAGE_NAME" tests/ -v
fi

# Run the agent with the question
echo "Running agent..."
docker run --rm \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e AWS_DEFAULT_REGION \
    -e TAVILY_API_KEY \
    -e HEALTHYLINKX_MCP_URL \
    "$IMAGE_NAME" "$@"

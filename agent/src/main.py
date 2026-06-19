"""CLI entry point — takes a health question as argument, runs the agent, prints the response."""

import sys
import asyncio

from logging_config import get_logger

logger = get_logger(__name__)


def main():
    if len(sys.argv) < 2:
        print('Usage: python main.py "your health question"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    logger.info("Question: %s", question)

    from agent import run_agent

    try:
        answer = asyncio.run(run_agent(question))
        print(answer)
    except Exception:
        logger.exception("Failed to process question")
        sys.exit(1)


if __name__ == "__main__":
    main()

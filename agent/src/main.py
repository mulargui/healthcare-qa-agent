"""CLI entry point — interactive prompt loop or single-question mode."""

import sys
import asyncio

from logging_config import get_logger

logger = get_logger(__name__)

WELCOME_MESSAGE = """Healthcare Q&A Agent
Ask health questions, find specialists, and get doctor recommendations.
Type "exit" or "quit" to end the session.
"""


def run_interactive():
    from agent import agent_session

    async def _session():
        async with agent_session() as ask:
            print(WELCOME_MESSAGE)
            while True:
                try:
                    question = input("> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

                if not question:
                    continue
                if question.lower() in ("exit", "quit"):
                    break

                logger.info("Question: %s", question)
                try:
                    answer = await ask(question)
                    print(answer)
                    print()
                except Exception:
                    logger.exception("Failed to process question")
                    print("Sorry, something went wrong. Please try again.")
                    print()

    asyncio.run(_session())


def run_single(question: str):
    from agent import run_agent

    logger.info("Question: %s", question)
    try:
        answer = asyncio.run(run_agent(question))
        print(answer)
    except Exception:
        logger.exception("Failed to process question")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        run_interactive()
    else:
        run_single(" ".join(sys.argv[1:]))


if __name__ == "__main__":
    main()

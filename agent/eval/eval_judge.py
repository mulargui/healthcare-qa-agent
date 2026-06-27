"""LLM-as-judge — scores agent responses using a separate Claude model."""

import json
import os

from langchain_aws import ChatBedrockConverse

JUDGE_MODEL_ID = "us.anthropic.claude-opus-4-8-v1:0"

JUDGE_SYSTEM_PROMPT = """\
You are an expert evaluator for a healthcare Q&A agent. \
Your job is to score the agent's response on specific quality dimensions.

You will be given:
1. The user's question to the agent
2. The agent's response
3. A set of scoring dimensions with specific criteria for this case

For each dimension, provide:
- A score from 1 to 5 (1=poor, 2=below average, 3=adequate, 4=good, 5=excellent)
- A one-sentence justification

Respond in JSON format only:
{
  "scores": {
    "<dimension_name>": {
      "score": <1-5>,
      "justification": "<one sentence>"
    }
  }
}

Scoring guidelines:
- 5: Exceptional — exceeds what a thoughtful healthcare professional would write
- 4: Good — covers the key points with appropriate nuance and tone
- 3: Adequate — acceptable but missing some important aspects
- 2: Below average — significant gaps in accuracy, empathy, or completeness
- 1: Poor — incorrect, harmful, or completely misses the point

Be strict but fair. A score of 3 should be the baseline for a competent response."""

JUDGE_USER_TEMPLATE = """\
## User Question
{question}

## Agent Response
{response}

## Scoring Dimensions
{dimensions}

Score each dimension above. Respond in JSON only."""


def _format_dimensions(judge_criteria: dict) -> str:
    lines = []
    for dim, criteria in judge_criteria.items():
        lines.append(f"- **{dim}**: {criteria}")
    return "\n".join(lines)


async def judge_response(question: str, response: str, judge_criteria: dict) -> dict:
    """Score a response using the judge model.

    Returns:
        {"scores": {"dim": {"score": int, "justification": str}}, "average_score": float, "raw_output": str}
    """
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    llm = ChatBedrockConverse(model=JUDGE_MODEL_ID, region_name=region)

    user_message = JUDGE_USER_TEMPLATE.format(
        question=question,
        response=response,
        dimensions=_format_dimensions(judge_criteria),
    )

    result = await llm.ainvoke([
        ("system", JUDGE_SYSTEM_PROMPT),
        ("user", user_message),
    ])

    raw = result.content
    json_str = raw.strip()
    if json_str.startswith("```"):
        json_str = json_str.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    parsed = json.loads(json_str)
    scores = parsed["scores"]
    score_values = [s["score"] for s in scores.values()]
    avg = sum(score_values) / len(score_values) if score_values else 0

    return {
        "scores": scores,
        "average_score": round(avg, 2),
        "raw_output": raw,
    }

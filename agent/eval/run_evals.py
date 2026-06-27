"""Eval runner — scores agent response quality using heuristics + LLM-as-judge."""

import asyncio
import json
import os
import time
from datetime import datetime, timezone

import pytest

import agent
from conftest import get_mock_tools
from eval_cases import EVAL_CASES
from eval_scoring import run_heuristics
from eval_judge import judge_response, JUDGE_MODEL_ID

EVAL_OUTPUT = "eval_results.json"

_eval_results = []


@pytest.fixture(scope="session", autouse=True)
def eval_report():
    """After all evals run, print summary and write JSON."""
    yield
    if not _eval_results:
        return

    heuristic_scores = [r["heuristics"]["score"] for r in _eval_results]
    judge_scores = [r["judge"]["average_score"] for r in _eval_results if r["judge"]]
    combined_scores = [r["combined_score"] for r in _eval_results]

    report = {
        "run_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "eval_model": agent.BEDROCK_MODEL_ID,
            "judge_model": JUDGE_MODEL_ID,
            "total_cases": len(_eval_results),
        },
        "summary": {
            "avg_heuristic_score": round(sum(heuristic_scores) / len(heuristic_scores), 2),
            "avg_judge_score": round(sum(judge_scores) / len(judge_scores), 2) if judge_scores else None,
            "avg_combined_score": round(sum(combined_scores) / len(combined_scores), 2),
        },
        "cases": _eval_results,
    }

    out_path = EVAL_OUTPUT
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    _print_summary(report, out_path)


def _print_summary(report, out_path):
    from tabulate import tabulate

    rows = []
    for c in report["cases"]:
        h = c["heuristics"]
        j = c["judge"]
        passed = sum(1 for ch in h["checks"] if ch["passed"])
        total = len(h["checks"])
        rows.append([
            c["id"],
            c["category"],
            f"{passed}/{total}",
            f"{j['average_score']:.1f}" if j else "N/A",
            f"{c['combined_score']:.1f}",
            f"{c['elapsed_seconds']:.1f}",
        ])

    headers = ["ID", "Category", "Heuristic", "Judge", "Combined", "Time(s)"]
    print(f"\nEval Results — {report['run_metadata']['timestamp']}")
    print(f"Eval model:  {report['run_metadata']['eval_model']}")
    print(f"Judge model: {report['run_metadata']['judge_model']}")
    print()
    print(tabulate(rows, headers=headers, tablefmt="simple"))

    s = report["summary"]
    print(f"\nAvg Heuristic: {s['avg_heuristic_score']:.2f}")
    if s["avg_judge_score"] is not None:
        print(f"Avg Judge:     {s['avg_judge_score']:.1f} / 5.0")
    print(f"Avg Combined:  {s['avg_combined_score']:.1f} / 5.0")
    print(f"\nResults saved to: {out_path}")


class TestEvalCase:

    @pytest.mark.parametrize("case", EVAL_CASES, ids=[c["id"] for c in EVAL_CASES])
    def test_case(self, case, request):
        async def _run():
            mock_tools = get_mock_tools(request)

            start = time.time()
            async with agent.agent_session(tools_override=mock_tools) as ask:
                response = await ask(case["question"])
            elapsed = time.time() - start

            heuristic_results = run_heuristics(response, elapsed, case.get("expected_traits", {}))
            h_passed = sum(1 for h in heuristic_results if h.passed)
            h_total = len(heuristic_results)
            h_score = h_passed / h_total if h_total > 0 else 1.0

            judge_result = None
            judge_avg = 3.0
            if case.get("judge_criteria"):
                judge_result = await judge_response(
                    question=case["question"],
                    response=response,
                    judge_criteria=case["judge_criteria"],
                )
                judge_avg = judge_result["average_score"]

            combined = (h_score * 5.0) * 0.2 + judge_avg * 0.8

            result = {
                "id": case["id"],
                "category": case["category"],
                "question": case["question"],
                "response": response,
                "elapsed_seconds": round(elapsed, 1),
                "heuristics": {
                    "score": round(h_score, 2),
                    "checks": [
                        {"name": h.name, "passed": h.passed, "detail": h.detail}
                        for h in heuristic_results
                    ],
                },
                "judge": {
                    "average_score": judge_result["average_score"],
                    "scores": judge_result["scores"],
                    "raw_output": judge_result["raw_output"],
                } if judge_result else None,
                "combined_score": round(combined, 1),
            }
            _eval_results.append(result)

            assert combined >= 2.0, (
                f"Eval case '{case['id']}' scored {combined:.1f}/5.0 "
                f"(below minimum threshold of 2.0)"
            )

        asyncio.run(_run())

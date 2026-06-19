"""Acceptance tests — validates the agent end-to-end against the product spec."""

import time
import asyncio

import pytest

from agent import run_agent


def ask(question):
    """Run the agent with a question and return the lowercase response."""
    return asyncio.run(run_agent(question)).lower()


class TestSymptomBasedDoctorRecommendation:
    """Spec: docs/product spec.md > Acceptance Tests > Symptom-based doctor recommendation."""

    def test_symptom_based_recommendation(self):
        response = ask(
            "I've been having recurring headaches and blurred vision. I'm in Seattle, WA."
        )
        assert any(
            term in response
            for term in ["neurolog", "vision", "ophthalmol", "migraine"]
        ), "Should mention possible conditions"
        assert any(
            term in response
            for term in ["neurologist", "ophthalmologist", "specialist"]
        ), "Should suggest a specialist type"
        assert any(
            term in response for term in ["dr.", "dr ", "doctor", "md"]
        ), "Should list doctors"
        assert len(response) > 200, "Should include background summaries"


class TestDirectDoctorSearch:
    """Spec: docs/product spec.md > Acceptance Tests > Direct doctor search."""

    def test_direct_doctor_search(self):
        response = ask("Find me a counselor in Redmond, WA")
        assert "counselor" in response, "Should mention counseling"
        assert "redmond" in response, "Should mention Redmond"
        assert any(
            term in response for term in ["dr.", "dr ", "doctor", "md"]
        ), "Should list doctors"


class TestGeneralHealthQuestion:
    """Spec: docs/product spec.md > Acceptance Tests > General health question."""

    def test_general_health_question(self):
        response = ask("What's the difference between a cold and the flu?")
        assert "cold" in response, "Should mention cold"
        assert "flu" in response, "Should mention flu"
        assert "searchdoctors" not in response, "Should not invoke doctor search"


class TestProactiveDoctorRecommendation:
    """Spec: docs/product spec.md > Acceptance Tests > Proactive doctor recommendation."""

    def test_proactive_recommendation(self):
        response = ask("I've been having sharp chest pains for the past week")
        assert any(
            term in response
            for term in ["heart", "cardiac", "chest", "cardiovascular"]
        ), "Should explain possible causes"
        assert any(
            term in response
            for term in ["cardiologist", "specialist", "doctor", "emergency", "er"]
        ), "Should recommend seeing a specialist"


class TestNoFollowUpQuestions:
    """Spec: docs/product spec.md > Acceptance Tests > No follow-up questions."""

    def test_second_invocation_is_independent(self):
        ask("Find me a counselor in Redmond, WA")
        second_response = ask("What about orthopedists?")
        assert "redmond" not in second_response, "Should not reference prior location"
        assert "counselor" not in second_response, "Should not reference prior specialty"


class TestResponseTime:
    """Spec: docs/product spec.md > Acceptance Tests > Response time."""

    @pytest.mark.parametrize(
        "question,max_seconds",
        [
            ("What's the difference between a cold and the flu?", 15),
            ("Find me a counselor in Redmond, WA", 30),
        ],
    )
    def test_response_time(self, question, max_seconds):
        start = time.time()
        asyncio.run(run_agent(question))
        elapsed = time.time() - start
        assert elapsed < max_seconds, f"Response took {elapsed:.1f}s, expected under {max_seconds}s"

"""Acceptance tests — validates the agent end-to-end against the product spec."""

import time
import asyncio

import pytest

import agent


def ask(question):
    """Run the agent with a question and return the lowercase response."""
    return asyncio.run(agent.run_agent(question)).lower()


def ask_session(questions):
    """Run multiple questions in a single session and return lowercase responses."""
    async def _run():
        async with agent.agent_session() as ask:
            return [(await ask(q)).lower() for q in questions]
    return asyncio.run(_run())


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
            term in response for term in ["dr.", "dr ", "doctor", "md", "lmhc", "phd", "ma,"]
        ), "Should list practitioners"
        assert len(response) > 200, "Should include background summaries"


class TestDirectDoctorSearch:
    """Spec: docs/product spec.md > Acceptance Tests > Direct doctor search."""

    def test_direct_doctor_search(self):
        response = ask("Find me a counselor in Redmond, WA")
        assert "counselor" in response, "Should mention counseling"
        assert "redmond" in response, "Should mention Redmond"
        assert any(
            term in response for term in ["dr.", "dr ", "doctor", "md", "lmhc", "phd", "ma,"]
        ), "Should list practitioners"
        assert any(
            term in response for term in ["address", "street", "ave", "blvd", "rd", "wa 9"]
        ), "Should include addresses"
        assert len(response) > 200, "Should include background info"


class TestGeneralHealthQuestion:
    """Spec: docs/product spec.md > Acceptance Tests > General health question."""

    def test_general_health_question(self):
        response = ask("What's the difference between a cold and the flu?")
        assert "cold" in response, "Should mention cold"
        assert "flu" in response, "Should mention flu"
        assert not any(
            term in response for term in ["dr.", "dr ", "md,"]
        ), "Should not list specific doctors"


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
        assert any(
            term in response for term in ["location", "area", "where", "city", "zip"]
        ), "Should offer to search if a location is provided"


class TestFollowUpWithContextCarryover:
    """Spec: docs/product spec.md > Acceptance Tests > Follow-up with context carryover."""

    def test_location_carries_over(self):
        responses = ask_session([
            "Find me a counselor in Redmond, WA",
            "What about orthopedists?",
        ])
        assert "redmond" in responses[1], "Should use Redmond from prior turn"
        assert any(
            term in responses[1] for term in ["orthoped", "orthopedist"]
        ), "Should mention orthopedists"


class TestFollowUpReferencingPriorResults:
    """Spec: docs/product spec.md > Acceptance Tests > Follow-up referencing prior results."""

    def test_reference_prior_doctor_list(self):
        responses = ask_session([
            "Find me a counselor in Redmond, WA",
            "Tell me more about the first doctor",
        ])
        assert any(
            term in responses[1] for term in ["dr.", "dr ", "doctor", "md", "lmhc", "phd", "ma,"]
        ), "Should provide detail about a practitioner from the previous list"
        assert len(responses[1]) > 100, "Should include substantive detail"


class TestNoContextLeaksAcrossSessions:
    """Spec: docs/product spec.md > Acceptance Tests > No context leaks across sessions."""

    def test_separate_sessions_are_independent(self):
        ask("Find me a counselor in Redmond, WA")
        second_response = ask("What about orthopedists?")
        assert "redmond" not in second_response, "Should not reference prior session's location"
        assert "counselor" not in second_response, "Should not reference prior session's specialty"


class TestUserCorrectionUpdatesContext:
    """Spec: docs/product spec.md > Acceptance Tests > User correction updates context."""

    def test_correction_updates_location(self):
        responses = ask_session([
            "Find me a cardiologist in Seattle, WA",
            "Actually I meant Tacoma, not Seattle",
        ])
        assert "tacoma" in responses[1], "Should use corrected location"
        assert any(
            term in responses[1] for term in ["cardiolog", "heart"]
        ), "Should list cardiologists"


class TestProgressiveSymptomDisclosure:
    """Spec: docs/product spec.md > Acceptance Tests > Progressive symptom disclosure across turns."""

    def test_accumulates_symptoms_across_turns(self):
        responses = ask_session([
            "I've been having bad headaches",
            "Also I've been feeling dizzy lately",
            "Who should I see? I'm in Seattle, WA.",
        ])
        assert any(
            term in responses[2]
            for term in ["headache", "head", "neurolog"]
        ), "Should consider headaches from earlier turns, not just dizziness"
        assert any(
            term in responses[2] for term in ["dr.", "dr ", "doctor", "md", "lmhc", "phd", "ma,"]
        ), "Should list practitioners"


class TestClarifyingQuestionForVagueSymptoms:
    """Spec: docs/product spec.md > Acceptance Tests > Clarifying question for vague symptoms."""

    def test_vague_symptoms_trigger_clarifying_question(self):
        response = ask("I don't feel well.")
        assert "?" in response, "Should ask a clarifying question"
        assert not any(
            term in response for term in ["dr.", "dr ", "md,"]
        ), "Should not list specific doctors"


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
        asyncio.run(agent.run_agent(question))
        elapsed = time.time() - start
        assert elapsed < max_seconds, f"Response took {elapsed:.1f}s, expected under {max_seconds}s"

    def test_follow_up_response_time(self):
        async def _run():
            async with agent.agent_session() as ask:
                await ask("Find me a counselor in Redmond, WA")
                start = time.time()
                await ask("What about orthopedists?")
                return time.time() - start

        elapsed = asyncio.run(_run())
        assert elapsed < 30, f"Follow-up took {elapsed:.1f}s, expected under 30s"

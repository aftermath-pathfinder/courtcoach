"""Unit tests for coaching_service.py — InferenceClient is fully mocked."""

import json
import os
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from app.services.angle_service import Angles
from app.services.coaching_service import (
    FALLBACK,
    STRUCTURED_FALLBACK,
    CoachingTip,
    get_coaching_feedback,
    get_structured_coaching_feedback,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_angles(
    elbow: float = 165.0,
    shoulder: float = 90.0,
    hip: float = 80.0,
    knee: float = 30.0,
    follow: float = 195.0,
) -> Angles:
    return Angles(
        elbow_angle=elbow,
        shoulder_rotation=shoulder,
        hip_turn=hip,
        knee_flex=knee,
        follow_through=follow,
    )


def _make_chat_response(content: str) -> MagicMock:
    """Build a mock InferenceClient chat_completion response object."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetCoachingFeedback:
    """Tests for coaching_service.get_coaching_feedback."""

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_happy_path_returns_parsed_observations(self, MockInferenceClient):
        """Happy path: valid JSON array of 3 strings is returned as-is."""
        observations = ["obs1", "obs2", "obs3"]
        response = _make_chat_response(json.dumps(observations))

        mock_client = MagicMock()
        mock_client.chat_completion.return_value = response
        MockInferenceClient.return_value = mock_client

        result = get_coaching_feedback(_make_angles())

        assert result == observations
        mock_client.chat_completion.assert_called_once()

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_returns_fallback_when_api_raises(self, MockInferenceClient):
        """Returns FALLBACK list when chat_completion raises any exception."""
        mock_client = MagicMock()
        mock_client.chat_completion.side_effect = RuntimeError("API error")
        MockInferenceClient.return_value = mock_client

        result = get_coaching_feedback(_make_angles())

        assert result == FALLBACK

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_returns_fallback_when_response_not_valid_json(self, MockInferenceClient):
        """Returns FALLBACK when the model returns non-JSON text."""
        response = _make_chat_response("This is not JSON at all.")
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = response
        MockInferenceClient.return_value = mock_client

        result = get_coaching_feedback(_make_angles())

        assert result == FALLBACK

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_returns_fallback_when_json_has_wrong_count(self, MockInferenceClient):
        """Returns FALLBACK when JSON parses but contains != 3 items."""
        for bad_list in [[], ["only one"], ["a", "b", "c", "d"]]:
            response = _make_chat_response(json.dumps(bad_list))
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = response
            MockInferenceClient.return_value = mock_client

            result = get_coaching_feedback(_make_angles())
            assert result == FALLBACK, f"Expected FALLBACK for input {bad_list}, got {result}"

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_returns_fallback_when_json_is_not_a_list(self, MockInferenceClient):
        """Returns FALLBACK when JSON is valid but not a list (e.g. a dict)."""
        response = _make_chat_response(json.dumps({"key": "value"}))
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = response
        MockInferenceClient.return_value = mock_client

        result = get_coaching_feedback(_make_angles())

        assert result == FALLBACK

    @patch.dict(os.environ, {}, clear=True)
    def test_raises_runtime_error_when_token_missing(self):
        """Raises RuntimeError with a clear message when HF_API_TOKEN is absent."""
        # Ensure the key is not set
        os.environ.pop("HF_API_TOKEN", None)

        with pytest.raises(RuntimeError, match="HF_API_TOKEN"):
            get_coaching_feedback(_make_angles())

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_returned_list_contains_strings(self, MockInferenceClient):
        """All items in the returned list are strings even when model returns non-string JSON."""
        observations = [1, 2, 3]  # ints, not strings
        response = _make_chat_response(json.dumps(observations))
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = response
        MockInferenceClient.return_value = mock_client

        result = get_coaching_feedback(_make_angles())

        assert all(isinstance(item, str) for item in result)

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_client_called_with_correct_model(self, MockInferenceClient):
        """InferenceClient.chat_completion is called with the correct model name."""
        observations = ["a", "b", "c"]
        response = _make_chat_response(json.dumps(observations))
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = response
        MockInferenceClient.return_value = mock_client

        get_coaching_feedback(_make_angles())

        call_kwargs = mock_client.chat_completion.call_args
        assert call_kwargs is not None
        # model can be in args or kwargs
        all_args = list(call_kwargs.args) + list(call_kwargs.kwargs.values())
        assert any("gemma" in str(arg).lower() or "google" in str(arg).lower() for arg in all_args), (
            f"Expected gemma model in call args, got: {call_kwargs}"
        )

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_fallback_constants_are_exactly_3_items(self, MockInferenceClient):
        """FALLBACK list always has exactly 3 string items."""
        assert len(FALLBACK) == 3
        assert all(isinstance(s, str) for s in FALLBACK)


# ---------------------------------------------------------------------------
# TestGetStructuredCoachingFeedback
# ---------------------------------------------------------------------------


def _make_structured_response(angles: Angles) -> str:
    return json.dumps({
        "elbow_angle":       {"observation": "Good elbow extension.", "drill": "Shadow swing drill."},
        "shoulder_rotation": {"observation": "Full shoulder turn.", "drill": "Unit turn drill."},
        "hip_turn":          {"observation": "Good hip rotation.", "drill": "Hip separation drill."},
        "knee_flex":         {"observation": "Nice knee bend.", "drill": "Wall sit drill."},
        "follow_through":    {"observation": "High finish achieved.", "drill": "High finish drill."},
    })


class TestGetStructuredCoachingFeedback:

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_returns_list_of_coaching_tips(self, MockInferenceClient):
        angles = _make_angles()
        response = _make_chat_response(_make_structured_response(angles))
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = response
        MockInferenceClient.return_value = mock_client

        result = get_structured_coaching_feedback(angles)

        assert isinstance(result, list)
        assert all(isinstance(t, CoachingTip) for t in result)
        assert len(result) == 5

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_severity_is_computed_locally_not_from_llm(self, MockInferenceClient):
        """LLM response contains no severity field — it must be computed from IDEAL_RANGES."""
        angles = _make_angles(elbow=165.0)  # within ideal range → "good"
        response = _make_chat_response(_make_structured_response(angles))
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = response
        MockInferenceClient.return_value = mock_client

        result = get_structured_coaching_feedback(angles)
        elbow_tip = next(t for t in result if t.angle_name == "elbow_angle")

        assert elbow_tip.severity == "good"

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_critical_severity_for_out_of_range_angle(self, MockInferenceClient):
        angles = _make_angles(elbow=100.0)  # far outside 160-170 → "critical"
        response = _make_chat_response(_make_structured_response(angles))
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = response
        MockInferenceClient.return_value = mock_client

        result = get_structured_coaching_feedback(angles)
        elbow_tip = next(t for t in result if t.angle_name == "elbow_angle")

        assert elbow_tip.severity == "critical"

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_returns_structured_fallback_on_api_error(self, MockInferenceClient):
        mock_client = MagicMock()
        mock_client.chat_completion.side_effect = RuntimeError("API down")
        MockInferenceClient.return_value = mock_client

        result = get_structured_coaching_feedback(_make_angles())

        assert result == STRUCTURED_FALLBACK

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_returns_structured_fallback_on_bad_json(self, MockInferenceClient):
        response = _make_chat_response("not json at all")
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = response
        MockInferenceClient.return_value = mock_client

        result = get_structured_coaching_feedback(_make_angles())

        assert result == STRUCTURED_FALLBACK

    @patch.dict(os.environ, {}, clear=True)
    def test_raises_runtime_error_when_token_missing(self):
        os.environ.pop("HF_API_TOKEN", None)

        with pytest.raises(RuntimeError, match="HF_API_TOKEN"):
            get_structured_coaching_feedback(_make_angles())

    @patch.dict(os.environ, {"HF_API_TOKEN": "test-token"})
    @patch("app.services.coaching_service.InferenceClient")
    def test_structured_fallback_has_5_items_one_per_angle(self, MockInferenceClient):
        assert len(STRUCTURED_FALLBACK) == 5
        expected_angles = {"elbow_angle", "shoulder_rotation", "hip_turn", "knee_flex", "follow_through"}
        assert {t.angle_name for t in STRUCTURED_FALLBACK} == expected_angles

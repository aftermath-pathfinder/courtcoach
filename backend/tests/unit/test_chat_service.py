"""Unit tests for chat_service.py — OpenAI client is fully mocked."""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.services.chat_service import FALLBACK_REPLY, get_chat_reply


def _make_openai_response(content: str) -> MagicMock:
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


_MESSAGES = [{"role": "user", "content": "Why is my elbow bent?"}]

_CONTEXT = {
    "angles": {
        "elbow_angle": 147.0,
        "shoulder_rotation": 88.0,
        "hip_turn": 80.0,
        "knee_flex": 28.0,
        "follow_through": 177.0,
    },
    "tips": [
        {
            "angle_name": "elbow_angle",
            "severity": "critical",
            "observation": "Elbow too bent at contact.",
            "drill": "Shadow swing drill.",
        }
    ],
    "key_frames": [
        {
            "label": "contact",
            "angles": {"elbow_angle": 147.0, "knee_flex": 28.0},
        }
    ],
}


class TestGetChatReply:

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.chat_service.OpenAI")
    def test_happy_path_returns_reply(self, MockOpenAI):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_openai_response("Great question!")
        MockOpenAI.return_value = mock_client

        result = get_chat_reply(_MESSAGES, _CONTEXT)

        assert result == "Great question!"
        mock_client.chat.completions.create.assert_called_once()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.chat_service.OpenAI")
    def test_system_message_is_prepended(self, MockOpenAI):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_openai_response("reply")
        MockOpenAI.return_value = mock_client

        get_chat_reply(_MESSAGES, _CONTEXT)

        call_kwargs = mock_client.chat.completions.create.call_args
        messages_sent = call_kwargs.kwargs.get("messages") or call_kwargs.args[1]
        assert messages_sent[0]["role"] == "system"
        assert messages_sent[1]["role"] == "user"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.chat_service.OpenAI")
    def test_system_prompt_contains_angle_data(self, MockOpenAI):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_openai_response("reply")
        MockOpenAI.return_value = mock_client

        get_chat_reply(_MESSAGES, _CONTEXT)

        call_kwargs = mock_client.chat.completions.create.call_args
        messages_sent = call_kwargs.kwargs.get("messages") or call_kwargs.args[1]
        system_content = messages_sent[0]["content"]
        assert "147" in system_content      # elbow angle value
        assert "160" in system_content      # ideal range min
        assert "CRITICAL" in system_content

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.chat_service.OpenAI")
    def test_returns_fallback_when_api_raises(self, MockOpenAI):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("network error")
        MockOpenAI.return_value = mock_client

        result = get_chat_reply(_MESSAGES)

        assert result == FALLBACK_REPLY

    @patch.dict(os.environ, {}, clear=True)
    def test_raises_runtime_error_when_key_missing(self):
        os.environ.pop("OPENAI_API_KEY", None)
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            get_chat_reply(_MESSAGES)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.chat_service.OpenAI")
    def test_no_context_uses_generic_system_prompt(self, MockOpenAI):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_openai_response("reply")
        MockOpenAI.return_value = mock_client

        get_chat_reply(_MESSAGES, analysis_context=None)

        call_kwargs = mock_client.chat.completions.create.call_args
        messages_sent = call_kwargs.kwargs.get("messages") or call_kwargs.args[1]
        system_content = messages_sent[0]["content"]
        assert "No analysis data" in system_content

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.chat_service.OpenAI")
    def test_multi_turn_messages_preserved(self, MockOpenAI):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_openai_response("reply")
        MockOpenAI.return_value = mock_client

        convo = [
            {"role": "user", "content": "first message"},
            {"role": "assistant", "content": "first reply"},
            {"role": "user", "content": "follow-up"},
        ]
        get_chat_reply(convo, _CONTEXT)

        call_kwargs = mock_client.chat.completions.create.call_args
        messages_sent = call_kwargs.kwargs.get("messages") or call_kwargs.args[1]
        # system + 3 conversation messages
        assert len(messages_sent) == 4
        assert messages_sent[-1]["content"] == "follow-up"

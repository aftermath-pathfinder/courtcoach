import io
import json
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.coaching_service import CoachingTip, STRUCTURED_FALLBACK

client = TestClient(app)

FIXTURES = Path(__file__).parent.parent / "fixtures"
VIDEO = FIXTURES / "videoplayback.mp4"

_MOCK_TIPS = STRUCTURED_FALLBACK
_ANGLE_KEYS = {"elbow_angle", "shoulder_rotation", "knee_flex", "hip_turn", "follow_through"}


def _make_video(size_bytes: int = 1024) -> tuple[str, bytes, str]:
    return ("test.mp4", b"0" * size_bytes, "video/mp4")


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.skipif(not VIDEO.exists(), reason="fixture missing")
def test_analyze_returns_success_shape() -> None:
    video_bytes = VIDEO.read_bytes()
    with patch("app.routes.analyze.get_structured_coaching_feedback", return_value=_MOCK_TIPS):
        response = client.post(
            "/api/analyze",
            files={"video": ("videoplayback.mp4", io.BytesIO(video_bytes), "video/mp4")},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert set(body["angles"].keys()) == _ANGLE_KEYS
    assert len(body["tips"]) == 5
    assert all("severity" in t and "observation" in t and "drill" in t for t in body["tips"])
    assert isinstance(body["key_frames"], list)
    assert body["keypoints_extracted"] == 10
    assert body["processing_time_seconds"] > 0


@pytest.mark.skipif(not VIDEO.exists(), reason="fixture missing")
def test_analyze_stream_emits_sse_events() -> None:
    video_bytes = VIDEO.read_bytes()
    with patch("app.routes.analyze.get_structured_coaching_feedback", return_value=_MOCK_TIPS):
        response = client.post(
            "/api/analyze/stream",
            files={"video": ("videoplayback.mp4", io.BytesIO(video_bytes), "video/mp4")},
        )
    assert response.status_code == 200

    raw = response.text
    events: list[dict] = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            payload = json.loads(line[len("data: "):])
            events.append(payload)

    stages_seen = {e["stage"] for e in events}
    assert {"extracting", "angles", "coaching", "keyframes", "done"}.issubset(stages_seen)

    done_events = [e for e in events if e["stage"] == "done"]
    assert len(done_events) == 1
    result = done_events[0]["data"]
    assert result["status"] == "success"
    assert set(result["angles"].keys()) == _ANGLE_KEYS
    assert len(result["tips"]) == 5
    assert isinstance(result["key_frames"], list)
    assert result["keypoints_extracted"] == 10
    assert result["processing_time_seconds"] > 0


def test_analyze_rejects_oversized_file() -> None:
    oversized = 101 * 1024 * 1024  # 101 MB
    filename, content, mime = _make_video(oversized)
    response = client.post(
        "/api/analyze",
        files={"video": (filename, io.BytesIO(content), mime)},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["status"] == "error"
    assert "100MB" in body["detail"]["message"]


def test_analyze_requires_video_field() -> None:
    response = client.post("/api/analyze")
    assert response.status_code == 422

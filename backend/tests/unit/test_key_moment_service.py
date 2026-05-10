"""Unit tests for key_moment_service.py — cv2 is mocked."""

import base64
import sys
import types
from typing import Dict, List, Tuple
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Stub cv2 before importing the module under test
_cv2_mod = types.ModuleType("cv2")
_cv2_mod.VideoCapture = MagicMock()
_cv2_mod.cvtColor = MagicMock()
_cv2_mod.COLOR_BGR2RGB = 4
_cv2_mod.imencode = MagicMock(return_value=(True, np.array([1, 2, 3], dtype=np.uint8)))
_cv2_mod.line = MagicMock()
_cv2_mod.circle = MagicMock()
_cv2_mod.putText = MagicMock()
_cv2_mod.IMWRITE_JPEG_QUALITY = 1
_cv2_mod.FONT_HERSHEY_SIMPLEX = 0
_cv2_mod.LINE_AA = 16
sys.modules.setdefault("cv2", _cv2_mod)

from app.services.key_moment_service import KeyFrame, extract_key_frames  # noqa: E402

REQUIRED_INDICES = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26]


def _make_keypoints(x: float = 0.5, y: float = 0.5) -> Dict[int, Tuple[float, float]]:
    return {idx: (x, y) for idx in REQUIRED_INDICES}


def _make_angles(
    elbow: float = 165.0,
    shoulder: float = 90.0,
    hip: float = 80.0,
    knee: float = 30.0,
    follow: float = 195.0,
) -> Dict[str, float]:
    return {
        "elbow_angle": elbow,
        "shoulder_rotation": shoulder,
        "hip_turn": hip,
        "knee_flex": knee,
        "follow_through": follow,
    }


def _make_frames(n: int) -> List[np.ndarray]:
    return [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(n)]


def _make_valid_frames(n: int):
    return [(i, _make_keypoints()) for i in range(n)]


class TestExtractKeyFrames:

    def test_returns_up_to_three_key_frames(self):
        frames = _make_frames(6)
        valid = _make_valid_frames(6)
        angles = [_make_angles() for _ in range(6)]

        result = extract_key_frames(frames, valid, angles)

        assert len(result) <= 3
        assert len(result) >= 1

    def test_contact_frame_has_elbow_closest_to_165(self):
        frames = _make_frames(3)
        valid = _make_valid_frames(3)
        # Frame 0: elbow=180 (far), frame 1: elbow=163 (closest), frame 2: elbow=150 (far)
        angles = [
            _make_angles(elbow=180.0, shoulder=60.0, follow=160.0),
            _make_angles(elbow=163.0, shoulder=50.0, follow=150.0),
            _make_angles(elbow=150.0, shoulder=40.0, follow=140.0),
        ]

        result = extract_key_frames(frames, valid, angles)
        contact = next((kf for kf in result if kf.label == "contact"), None)

        assert contact is not None
        assert contact.frame_index == 1

    def test_windup_frame_has_max_shoulder_rotation(self):
        frames = _make_frames(3)
        valid = _make_valid_frames(3)
        angles = [
            _make_angles(elbow=180.0, shoulder=120.0, follow=160.0),
            _make_angles(elbow=163.0, shoulder=80.0, follow=150.0),
            _make_angles(elbow=150.0, shoulder=95.0, follow=140.0),
        ]

        result = extract_key_frames(frames, valid, angles)
        windup = next((kf for kf in result if kf.label == "windup"), None)

        assert windup is not None
        assert windup.frame_index == 0  # max shoulder_rotation=120

    def test_follow_through_frame_has_max_follow_through(self):
        frames = _make_frames(3)
        valid = _make_valid_frames(3)
        # Frame 0: max shoulder (windup), Frame 1: closest elbow to 165 (contact), Frame 2: max follow
        angles = [
            _make_angles(elbow=180.0, shoulder=120.0, follow=160.0),
            _make_angles(elbow=163.0, shoulder=80.0, follow=150.0),
            _make_angles(elbow=150.0, shoulder=95.0, follow=210.0),
        ]

        result = extract_key_frames(frames, valid, angles)
        follow = next((kf for kf in result if kf.label == "follow_through"), None)

        assert follow is not None
        assert follow.frame_index == 2  # max follow_through=210

    def test_deduplication_emits_fewer_frames_when_same_index_selected(self):
        # All three criteria point to index 0
        frames = _make_frames(1)
        valid = _make_valid_frames(1)
        angles = [_make_angles()]

        result = extract_key_frames(frames, valid, angles)

        # Only one frame in input → only 1 KeyFrame regardless of 3 criteria
        assert len(result) == 1
        labels = {kf.label for kf in result}
        assert "contact" in labels  # contact has highest priority

    def test_image_b64_is_valid_base64(self):
        frames = _make_frames(3)
        valid = _make_valid_frames(3)
        angles = [_make_angles() for _ in range(3)]

        result = extract_key_frames(frames, valid, angles)

        for kf in result:
            decoded = base64.b64decode(kf.image_b64)
            assert len(decoded) > 0

    def test_annotated_image_b64_is_valid_base64(self):
        frames = _make_frames(3)
        valid = _make_valid_frames(3)
        angles = [_make_angles() for _ in range(3)]

        result = extract_key_frames(frames, valid, angles)

        for kf in result:
            decoded = base64.b64decode(kf.annotated_image_b64)
            assert len(decoded) > 0

    def test_returns_empty_list_for_empty_valid_frames(self):
        result = extract_key_frames([], [], [])
        assert result == []

    def test_keyframe_labels_are_valid_strings(self):
        frames = _make_frames(3)
        valid = _make_valid_frames(3)
        angles = [_make_angles() for _ in range(3)]

        result = extract_key_frames(frames, valid, angles)

        valid_labels = {"contact", "windup", "follow_through"}
        for kf in result:
            assert kf.label in valid_labels

    def test_no_duplicate_labels_in_result(self):
        frames = _make_frames(6)
        valid = _make_valid_frames(6)
        angles = [_make_angles() for _ in range(6)]

        result = extract_key_frames(frames, valid, angles)

        labels = [kf.label for kf in result]
        assert len(labels) == len(set(labels))

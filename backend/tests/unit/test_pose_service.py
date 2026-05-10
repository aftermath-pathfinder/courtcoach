"""Unit tests for pose_service.py — cv2 is mocked, PoseLandmarker is mocked."""

import sys
import types
from typing import Dict, List, Tuple
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Pre-stub cv2 only (mediapipe.tasks works fine without native X11 libs).
_cv2_mod = types.ModuleType("cv2")
_cv2_mod.VideoCapture = MagicMock()
_cv2_mod.cvtColor = MagicMock()
_cv2_mod.COLOR_BGR2RGB = 4
sys.modules.setdefault("cv2", _cv2_mod)

import app.services.pose_service as pose_service_module  # noqa: E402
from app.services.pose_service import average_keypoints, extract_keypoints, extract_keypoints_per_frame  # noqa: E402

REQUIRED_INDICES = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26]


def _make_landmark(x: float, y: float, visibility: float) -> MagicMock:
    lm = MagicMock()
    lm.x = x
    lm.y = y
    lm.visibility = visibility
    return lm


def _make_detection_result(visible: bool = True, x: float = 0.5, y: float = 0.5) -> MagicMock:
    result = MagicMock()
    if visible:
        landmarks = []
        for i in range(33):
            if i in REQUIRED_INDICES:
                landmarks.append(_make_landmark(x, y, 0.9))
            else:
                landmarks.append(_make_landmark(0.0, 0.0, 0.1))
        result.pose_landmarks = [landmarks]
    else:
        result.pose_landmarks = []
    return result


def _make_cap_mock(num_frames: int) -> MagicMock:
    cap = MagicMock()
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    cap.read.side_effect = [(True, frame)] * num_frames + [(False, None)]
    cap.release = MagicMock()
    return cap


def _setup_landmarker_mock(MockLandmarker, results_value=None, results_side_effect=None):
    mock_landmarker = MagicMock()
    if results_side_effect is not None:
        mock_landmarker.detect.side_effect = results_side_effect
    else:
        mock_landmarker.detect.return_value = results_value
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=mock_landmarker)
    ctx.__exit__ = MagicMock(return_value=False)
    MockLandmarker.create_from_options.return_value = ctx
    return mock_landmarker


class TestExtractKeypoints:

    @patch("app.services.pose_service.os.unlink")
    @patch("app.services.pose_service.mp.Image")
    @patch("app.services.pose_service.cv2.VideoCapture")
    @patch("app.services.pose_service.cv2.cvtColor")
    @patch("app.services.pose_service.PoseLandmarker")
    @patch("app.services.pose_service._write_temp_video", return_value="/tmp/fake.mp4")
    def test_happy_path_returns_correct_keys(self, mock_write, MockLandmarker, mock_cvt, MockCap, mock_img, mock_unlink):
        MockCap.return_value = _make_cap_mock(10)
        mock_cvt.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        _setup_landmarker_mock(MockLandmarker, results_value=_make_detection_result(True, 0.4, 0.6))

        result = extract_keypoints(b"fake-video-bytes")

        assert set(result.keys()) == set(REQUIRED_INDICES)
        for idx in REQUIRED_INDICES:
            x_val, y_val = result[idx]
            assert abs(x_val - 0.4) < 1e-6
            assert abs(y_val - 0.6) < 1e-6

    @patch("app.services.pose_service.os.unlink")
    @patch("app.services.pose_service.mp.Image")
    @patch("app.services.pose_service.cv2.VideoCapture")
    @patch("app.services.pose_service.cv2.cvtColor")
    @patch("app.services.pose_service.PoseLandmarker")
    @patch("app.services.pose_service._write_temp_video", return_value="/tmp/fake.mp4")
    def test_raises_value_error_when_fewer_than_3_valid_frames(self, mock_write, MockLandmarker, mock_cvt, MockCap, mock_img, mock_unlink):
        MockCap.return_value = _make_cap_mock(10)
        mock_cvt.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        _setup_landmarker_mock(MockLandmarker, results_value=_make_detection_result(False))

        with pytest.raises(ValueError, match="valid frames"):
            extract_keypoints(b"fake-video-bytes")

    @patch("app.services.pose_service.os.unlink")
    @patch("app.services.pose_service.mp.Image")
    @patch("app.services.pose_service.cv2.VideoCapture")
    @patch("app.services.pose_service.cv2.cvtColor")
    @patch("app.services.pose_service.PoseLandmarker")
    @patch("app.services.pose_service._write_temp_video", return_value="/tmp/fake.mp4")
    def test_middle_60_percent_frame_selection(self, mock_write, MockLandmarker, mock_cvt, MockCap, mock_img, mock_unlink):
        MockCap.return_value = _make_cap_mock(10)
        mock_cvt.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_landmarker = _setup_landmarker_mock(MockLandmarker, results_value=_make_detection_result(True))

        extract_keypoints(b"fake-video-bytes")

        assert mock_landmarker.detect.call_count == 6  # middle 60% of 10 frames

    @patch("app.services.pose_service.os.unlink")
    @patch("app.services.pose_service.mp.Image")
    @patch("app.services.pose_service.cv2.VideoCapture")
    @patch("app.services.pose_service.cv2.cvtColor")
    @patch("app.services.pose_service.PoseLandmarker")
    @patch("app.services.pose_service._write_temp_video", return_value="/tmp/fake.mp4")
    def test_low_visibility_frames_excluded(self, mock_write, MockLandmarker, mock_cvt, MockCap, mock_img, mock_unlink):
        MockCap.return_value = _make_cap_mock(10)
        mock_cvt.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        good = _make_detection_result(True, 0.8, 0.8)
        bad = _make_detection_result(False)
        _setup_landmarker_mock(MockLandmarker, results_side_effect=[good, bad] * 5)

        result = extract_keypoints(b"fake-video-bytes")

        for idx in REQUIRED_INDICES:
            x_val, y_val = result[idx]
            assert abs(x_val - 0.8) < 1e-5
            assert abs(y_val - 0.8) < 1e-5

    @patch("app.services.pose_service.os.unlink")
    @patch("app.services.pose_service.mp.Image")
    @patch("app.services.pose_service.cv2.VideoCapture")
    @patch("app.services.pose_service.cv2.cvtColor")
    @patch("app.services.pose_service.PoseLandmarker")
    @patch("app.services.pose_service._write_temp_video", return_value="/tmp/fake.mp4")
    def test_landmarks_with_low_visibility_cause_frame_exclusion(self, mock_write, MockLandmarker, mock_cvt, MockCap, mock_img, mock_unlink):
        MockCap.return_value = _make_cap_mock(10)
        mock_cvt.return_value = np.zeros((100, 100, 3), dtype=np.uint8)

        result = MagicMock()
        landmarks = []
        for i in range(33):
            if i in REQUIRED_INDICES[:-1]:
                landmarks.append(_make_landmark(0.5, 0.5, 0.9))
            elif i == REQUIRED_INDICES[-1]:
                landmarks.append(_make_landmark(0.5, 0.5, 0.3))  # below threshold
            else:
                landmarks.append(_make_landmark(0.0, 0.0, 0.1))
        result.pose_landmarks = [landmarks]
        _setup_landmarker_mock(MockLandmarker, results_value=result)

        with pytest.raises(ValueError, match="valid frames"):
            extract_keypoints(b"fake-video-bytes")


class TestExtractKeypointsPerFrame:

    @patch("app.services.pose_service.os.unlink")
    @patch("app.services.pose_service.mp.Image")
    @patch("app.services.pose_service.cv2.VideoCapture")
    @patch("app.services.pose_service.cv2.cvtColor")
    @patch("app.services.pose_service.PoseLandmarker")
    @patch("app.services.pose_service._write_temp_video", return_value="/tmp/fake.mp4")
    def test_returns_tuple_of_frames_and_indexed_keypoints(self, mock_write, MockLandmarker, mock_cvt, MockCap, mock_img, mock_unlink):
        MockCap.return_value = _make_cap_mock(10)
        mock_cvt.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        _setup_landmarker_mock(MockLandmarker, results_value=_make_detection_result(True, 0.5, 0.5))

        frames, valid_data = extract_keypoints_per_frame(b"fake-video-bytes")

        assert isinstance(frames, list)
        assert len(frames) == 6  # middle 60% of 10 frames
        assert isinstance(valid_data, list)
        assert len(valid_data) > 0
        for frame_idx, kp in valid_data:
            assert isinstance(frame_idx, int)
            assert set(kp.keys()) == set(REQUIRED_INDICES)

    @patch("app.services.pose_service.os.unlink")
    @patch("app.services.pose_service.mp.Image")
    @patch("app.services.pose_service.cv2.VideoCapture")
    @patch("app.services.pose_service.cv2.cvtColor")
    @patch("app.services.pose_service.PoseLandmarker")
    @patch("app.services.pose_service._write_temp_video", return_value="/tmp/fake.mp4")
    def test_raises_value_error_when_fewer_than_3_valid_frames(self, mock_write, MockLandmarker, mock_cvt, MockCap, mock_img, mock_unlink):
        MockCap.return_value = _make_cap_mock(10)
        mock_cvt.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        _setup_landmarker_mock(MockLandmarker, results_value=_make_detection_result(False))

        with pytest.raises(ValueError, match="valid frames"):
            extract_keypoints_per_frame(b"fake-video-bytes")

    @patch("app.services.pose_service.os.unlink")
    @patch("app.services.pose_service.mp.Image")
    @patch("app.services.pose_service.cv2.VideoCapture")
    @patch("app.services.pose_service.cv2.cvtColor")
    @patch("app.services.pose_service.PoseLandmarker")
    @patch("app.services.pose_service._write_temp_video", return_value="/tmp/fake.mp4")
    def test_frame_indices_are_within_middle_frames_bounds(self, mock_write, MockLandmarker, mock_cvt, MockCap, mock_img, mock_unlink):
        MockCap.return_value = _make_cap_mock(10)
        mock_cvt.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        _setup_landmarker_mock(MockLandmarker, results_value=_make_detection_result(True))

        frames, valid_data = extract_keypoints_per_frame(b"fake-video-bytes")

        for frame_idx, _ in valid_data:
            assert 0 <= frame_idx < len(frames)

    @patch("app.services.pose_service.os.unlink")
    @patch("app.services.pose_service.mp.Image")
    @patch("app.services.pose_service.cv2.VideoCapture")
    @patch("app.services.pose_service.cv2.cvtColor")
    @patch("app.services.pose_service.PoseLandmarker")
    @patch("app.services.pose_service._write_temp_video", return_value="/tmp/fake.mp4")
    def test_average_keypoints_wrapper_produces_correct_average(self, mock_write, MockLandmarker, mock_cvt, MockCap, mock_img, mock_unlink):
        MockCap.return_value = _make_cap_mock(10)
        mock_cvt.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        _setup_landmarker_mock(MockLandmarker, results_value=_make_detection_result(True, 0.3, 0.7))

        _, valid_data = extract_keypoints_per_frame(b"fake-video-bytes")
        averaged = average_keypoints(valid_data)

        assert set(averaged.keys()) == set(REQUIRED_INDICES)
        for idx in REQUIRED_INDICES:
            x, y = averaged[idx]
            assert abs(x - 0.3) < 1e-5
            assert abs(y - 0.7) < 1e-5

"""Unit tests for angle_service.py — pure math, no mocking needed."""

from typing import Dict, Tuple

import numpy as np
import pytest

from app.services.angle_service import (
    Angles,
    REQUIRED_INDICES,
    calculate_angle,
    compute_angles,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _full_keypoints(
    x: float = 0.5,
    y: float = 0.5,
) -> Dict[int, Tuple[float, float]]:
    """Return a keypoints dict with all required indices set to (x, y)."""
    return {idx: (x, y) for idx in REQUIRED_INDICES}


def _keypoints_with_offsets() -> Dict[int, Tuple[float, float]]:
    """Return a keypoints dict with geometrically distinct positions so angles are non-trivial."""
    # Shoulders
    kp = {
        11: (0.3, 0.3),   # left shoulder
        12: (0.7, 0.3),   # right shoulder
        13: (0.2, 0.5),   # left elbow
        14: (0.8, 0.5),   # right elbow
        15: (0.1, 0.4),   # left wrist
        16: (0.9, 0.4),   # right wrist
        23: (0.35, 0.6),  # left hip
        24: (0.65, 0.6),  # right hip
        25: (0.35, 0.8),  # left knee
        26: (0.65, 0.8),  # right knee
    }
    return kp


# ---------------------------------------------------------------------------
# calculate_angle — unit tests
# ---------------------------------------------------------------------------


class TestCalculateAngle:
    def test_straight_arm_returns_180(self):
        """Collinear points should give 180 degrees."""
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 0.0])
        c = np.array([2.0, 0.0])
        angle = calculate_angle(a, b, c)
        assert abs(angle - 180.0) < 1e-6, f"Expected 180°, got {angle}"

    def test_perpendicular_vectors_return_90(self):
        """Perpendicular rays from vertex should give 90 degrees."""
        a = np.array([0.0, 1.0])
        b = np.array([0.0, 0.0])
        c = np.array([1.0, 0.0])
        angle = calculate_angle(a, b, c)
        assert abs(angle - 90.0) < 1e-6, f"Expected 90°, got {angle}"

    def test_same_direction_returns_0(self):
        """Rays pointing in the same direction should give 0 degrees."""
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 0.0])
        c = np.array([2.0, 0.0])  # same direction as b->a but further
        # a and c are on the same side of b — angle is 0
        # Actually: ba = a-b = (1,0), bc = c-b = (2,0) → same direction → 0°
        angle = calculate_angle(a, b, c)
        assert abs(angle - 0.0) < 1e-6, f"Expected 0°, got {angle}"

    def test_45_degree_angle(self):
        """Vectors at 45° to each other should yield 45°."""
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 0.0])
        c = np.array([1.0, 1.0])  # 45° from positive x-axis
        angle = calculate_angle(a, b, c)
        assert abs(angle - 45.0) < 1e-5, f"Expected 45°, got {angle}"

    def test_returns_float(self):
        """calculate_angle always returns a Python float."""
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 0.0])
        c = np.array([0.0, 1.0])
        angle = calculate_angle(a, b, c)
        assert isinstance(angle, float)

    def test_cosine_clamp_no_error(self):
        """Floating point precision near ±1 should not raise due to arccos domain."""
        # Parallel vectors: may produce cosine slightly > 1 without clamp
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 0.0])
        c = np.array([1.0, 1e-15])  # Nearly parallel
        angle = calculate_angle(a, b, c)
        assert 0.0 <= angle <= 180.0


# ---------------------------------------------------------------------------
# compute_angles — unit tests
# ---------------------------------------------------------------------------


class TestComputeAngles:
    def test_happy_path_returns_angles_instance(self):
        """Happy path: complete keypoints dict returns an Angles instance."""
        kp = _keypoints_with_offsets()
        result = compute_angles(kp)
        assert isinstance(result, Angles)

    def test_all_five_angles_are_floats(self):
        """All five angle attributes should be Python floats."""
        kp = _keypoints_with_offsets()
        result = compute_angles(kp)
        assert isinstance(result.elbow_angle, float)
        assert isinstance(result.shoulder_rotation, float)
        assert isinstance(result.hip_turn, float)
        assert isinstance(result.knee_flex, float)
        assert isinstance(result.follow_through, float)

    def test_all_angles_in_valid_range(self):
        """All computed angles should be in [0, 360) degrees."""
        kp = _keypoints_with_offsets()
        result = compute_angles(kp)
        for name, value in result.as_dict().items():
            assert 0.0 <= value < 360.0, f"{name}={value} is out of expected range"

    def test_follow_through_is_elbow_plus_30(self):
        """follow_through is always elbow_angle + 30 per the stub formula."""
        kp = _keypoints_with_offsets()
        result = compute_angles(kp)
        assert abs(result.follow_through - (result.elbow_angle + 30.0)) < 1e-6

    def test_raises_value_error_when_landmark_missing(self):
        """Raises ValueError when any required landmark is absent."""
        kp = _keypoints_with_offsets()
        del kp[11]  # Remove left shoulder
        with pytest.raises(ValueError, match="11"):
            compute_angles(kp)

    def test_raises_value_error_when_multiple_landmarks_missing(self):
        """Raises ValueError listing all missing indices."""
        kp = _keypoints_with_offsets()
        del kp[11]
        del kp[25]
        with pytest.raises(ValueError):
            compute_angles(kp)

    def test_raises_value_error_on_empty_keypoints(self):
        """Empty keypoints dict raises ValueError."""
        with pytest.raises(ValueError):
            compute_angles({})

    def test_shoulder_rotation_and_hip_turn_are_equal(self):
        """shoulder_rotation and hip_turn use the same formula, so they must be equal."""
        kp = _keypoints_with_offsets()
        result = compute_angles(kp)
        assert abs(result.shoulder_rotation - result.hip_turn) < 1e-10

    def test_as_dict_has_all_five_keys(self):
        """as_dict() returns exactly the five expected keys."""
        kp = _keypoints_with_offsets()
        result = compute_angles(kp)
        expected_keys = {
            "elbow_angle",
            "shoulder_rotation",
            "hip_turn",
            "knee_flex",
            "follow_through",
        }
        assert set(result.as_dict().keys()) == expected_keys

    def test_symmetric_keypoints_give_non_zero_angles(self):
        """Symmetric keypoints still produce meaningful (non-zero) angles."""
        kp = _keypoints_with_offsets()
        result = compute_angles(kp)
        # Knee flex should be non-trivial because of the ankle proxy offset
        assert result.knee_flex > 0.0

    def test_collinear_hip_knee_returns_near_180_knee_flex(self):
        """When hip, knee, and ankle proxy are collinear, knee flex should approach 180°."""
        kp = _keypoints_with_offsets()
        # Place left hip directly above left knee with no horizontal offset so
        # the ankle proxy (below knee) is collinear
        kp[23] = (0.35, 0.50)  # left hip — same x as knee
        kp[25] = (0.35, 0.70)  # left knee — same x
        # Ankle proxy = (0.35, 0.70 + 0.15) = (0.35, 0.85) → same x → collinear
        result = compute_angles(kp)
        assert abs(result.knee_flex - 180.0) < 1e-5, (
            f"Expected ~180° for collinear knee, got {result.knee_flex}"
        )

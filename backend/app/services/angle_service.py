"""AngleService: compute 5 joint angles from averaged MediaPipe keypoints."""

import logging
import math
from typing import Dict, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Landmark index constants (MediaPipe BlazePose)
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26

# All indices that must be present in keypoints
REQUIRED_INDICES = [
    LEFT_SHOULDER,
    RIGHT_SHOULDER,
    LEFT_ELBOW,
    RIGHT_ELBOW,
    LEFT_WRIST,
    RIGHT_WRIST,
    LEFT_HIP,
    RIGHT_HIP,
    LEFT_KNEE,
    RIGHT_KNEE,
]

# Approximate knee-to-ankle distance as a fraction of the image height.
# Used to synthesise an ankle proxy since ankle landmarks are not in the
# required set.  0.15 is a conservative estimate for a normalised frame.
KNEE_TO_ANKLE_PROXY_OFFSET = 0.15


class Angles:
    """Container for the 5 computed joint angles."""

    def __init__(
        self,
        elbow_angle: float,
        shoulder_rotation: float,
        hip_turn: float,
        knee_flex: float,
        follow_through: float,
    ) -> None:
        self.elbow_angle = elbow_angle
        self.shoulder_rotation = shoulder_rotation
        self.hip_turn = hip_turn
        self.knee_flex = knee_flex
        self.follow_through = follow_through

    def as_dict(self) -> Dict[str, float]:
        return {
            "elbow_angle": self.elbow_angle,
            "shoulder_rotation": self.shoulder_rotation,
            "hip_turn": self.hip_turn,
            "knee_flex": self.knee_flex,
            "follow_through": self.follow_through,
        }


def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Return the angle at vertex b formed by rays b->a and b->c, in degrees.

    Args:
        a: 2-D point (x, y) as ndarray.
        b: Vertex point.
        c: 2-D point (x, y) as ndarray.

    Returns:
        Angle in degrees in [0, 180].
    """
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    cosine = np.clip(cosine, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def compute_angles(keypoints: Dict[int, Tuple[float, float]]) -> Angles:
    """Compute the 5 tennis-swing angles from averaged keypoints.

    Args:
        keypoints: Mapping of landmark index -> (x, y) averaged over valid frames.

    Returns:
        An Angles instance with all five angle values.

    Raises:
        ValueError: If any required landmark index is missing from keypoints.
    """
    _validate_keypoints(keypoints)

    elbow_angle = _compute_elbow_angle(keypoints)
    shoulder_rotation = _compute_shoulder_rotation(keypoints)
    hip_turn = _compute_hip_turn(keypoints)
    knee_flex = _compute_knee_flex(keypoints)
    follow_through = _compute_follow_through(elbow_angle)

    angles = Angles(
        elbow_angle=elbow_angle,
        shoulder_rotation=shoulder_rotation,
        hip_turn=hip_turn,
        knee_flex=knee_flex,
        follow_through=follow_through,
    )
    logger.debug("Computed angles: %s", angles.as_dict())
    return angles


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _validate_keypoints(keypoints: Dict[int, Tuple[float, float]]) -> None:
    missing = [idx for idx in REQUIRED_INDICES if idx not in keypoints]
    if missing:
        raise ValueError(f"Missing required landmark indices: {missing}")


def _pt(keypoints: Dict[int, Tuple[float, float]], idx: int) -> np.ndarray:
    """Return the (x, y) point for a landmark as a float64 ndarray."""
    return np.array(keypoints[idx], dtype=np.float64)


def _compute_elbow_angle(keypoints: Dict[int, Tuple[float, float]]) -> float:
    """3-point angle at the elbow of the dominant arm.

    Dominant arm = whichever shoulder has the higher average visibility proxy.
    Since visibility is not stored in averaged keypoints we fall back to using
    the shoulder whose wrist has a higher Y value (lower in the frame, i.e.
    the hitting arm which is more extended).
    """
    left_wrist_y = keypoints[LEFT_WRIST][1]
    right_wrist_y = keypoints[RIGHT_WRIST][1]

    if left_wrist_y >= right_wrist_y:
        shoulder, elbow, wrist = LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST
    else:
        shoulder, elbow, wrist = RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST

    return calculate_angle(
        _pt(keypoints, shoulder),
        _pt(keypoints, elbow),
        _pt(keypoints, wrist),
    )


def _line_angle_deg(p1: np.ndarray, p2: np.ndarray) -> float:
    """Return the angle of the line from p1 to p2 relative to the horizontal, in degrees."""
    delta = p2 - p1
    return float(math.degrees(math.atan2(float(delta[1]), float(delta[0]))))


def _compute_shoulder_rotation(keypoints: Dict[int, Tuple[float, float]]) -> float:
    """Absolute angular difference between the shoulder line and hip line."""
    shoulder_angle = _line_angle_deg(_pt(keypoints, LEFT_SHOULDER), _pt(keypoints, RIGHT_SHOULDER))
    hip_angle = _line_angle_deg(_pt(keypoints, LEFT_HIP), _pt(keypoints, RIGHT_HIP))
    return float(abs(shoulder_angle - hip_angle))


def _compute_hip_turn(keypoints: Dict[int, Tuple[float, float]]) -> float:
    """Absolute angular difference between the hip line and the shoulder line.

    This is the complement view of shoulder_rotation — how much the hips have
    turned relative to the shoulders.  For convenience it is computed
    identically to shoulder_rotation (same magnitude, different semantic).
    """
    hip_angle = _line_angle_deg(_pt(keypoints, LEFT_HIP), _pt(keypoints, RIGHT_HIP))
    shoulder_angle = _line_angle_deg(_pt(keypoints, LEFT_SHOULDER), _pt(keypoints, RIGHT_SHOULDER))
    return float(abs(hip_angle - shoulder_angle))


def _compute_knee_flex(keypoints: Dict[int, Tuple[float, float]]) -> float:
    """3-point angle at the knee using an estimated ankle position.

    Ankle landmarks are not in the required set so we synthesise a proxy
    by moving the knee landmark downward by KNEE_TO_ANKLE_PROXY_OFFSET in
    normalised coordinates.  We use the left knee as the primary measurement.
    """
    hip_pt = _pt(keypoints, LEFT_HIP)
    knee_pt = _pt(keypoints, LEFT_KNEE)
    ankle_proxy = np.array(
        [knee_pt[0], knee_pt[1] + KNEE_TO_ANKLE_PROXY_OFFSET],
        dtype=np.float64,
    )
    return calculate_angle(hip_pt, knee_pt, ankle_proxy)


def _compute_follow_through(elbow_angle: float) -> float:
    """Estimated follow-through arc.

    Spec note: until frame-level tracking is wired, compute elbow angle from
    averaged keypoints and add a 30° offset as a placeholder.
    """
    return elbow_angle + 30.0

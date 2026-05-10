"""KeyMomentService: select key swing frames, encode as JPEG, draw skeleton overlays."""

import base64
import copy
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.services.constants import BOUNDARY_TOLERANCE, IDEAL_RANGES
from app.services.pose_service import PerFrameKeypoints

logger = logging.getLogger(__name__)

# Skeleton connections using REQUIRED_LANDMARKS indices only
_CONNECTIONS = [
    (11, 12),  # shoulders
    (11, 13),  # L shoulder → elbow
    (13, 15),  # L elbow → wrist
    (12, 14),  # R shoulder → elbow
    (14, 16),  # R elbow → wrist
    (11, 23),  # L shoulder → hip
    (12, 24),  # R shoulder → hip
    (23, 24),  # hips
    (23, 25),  # L hip → knee
    (24, 26),  # R hip → knee
]

# Maps landmark indices to the angle name used for severity coloring
_LANDMARK_ANGLE: Dict[int, str] = {
    13: "elbow_angle",
    14: "elbow_angle",
    11: "shoulder_rotation",
    12: "shoulder_rotation",
    23: "hip_turn",
    24: "hip_turn",
    25: "knee_flex",
    26: "knee_flex",
    # 15, 16 (wrists) intentionally absent → white
}

_COLOR_GOOD = (0, 200, 0)       # green
_COLOR_WARNING = (0, 165, 255)  # orange
_COLOR_CRITICAL = (0, 0, 220)   # red
_COLOR_NEUTRAL = (255, 255, 255)  # white


@dataclass
class KeyFrame:
    label: str                              # "contact" | "windup" | "follow_through"
    frame_index: int                        # index into middle_frames list
    keypoints: Dict[int, Tuple[float, float]]
    image_b64: str                          # raw JPEG, base64
    annotated_image_b64: str               # skeleton-overlaid JPEG, base64


def extract_key_frames(
    middle_frames: List[np.ndarray],
    valid_frames_data: PerFrameKeypoints,
    angles_per_frame: List[Dict[str, float]],
) -> List[KeyFrame]:
    """Select up to 3 key swing frames and return them with skeleton overlays.

    Args:
        middle_frames: All BGR frames from the middle-60% slice of the video.
        valid_frames_data: (frame_index, keypoints) for each valid pose frame.
        angles_per_frame: Computed angle dict for each entry in valid_frames_data,
                          in the same order.

    Returns:
        List of 1–3 KeyFrame objects. Fewer than 3 if duplicate frames are selected.
    """
    if not valid_frames_data:
        return []

    contact_idx = _find_contact_frame(angles_per_frame)
    windup_idx = _find_windup_frame(angles_per_frame)
    follow_idx = _find_follow_through_frame(angles_per_frame)

    # Deduplicate: keep first label that claims each valid_frames_data index
    seen_valid_indices: set[int] = set()
    candidates = [
        ("contact", contact_idx),
        ("windup", windup_idx),
        ("follow_through", follow_idx),
    ]

    key_frames: List[KeyFrame] = []
    for label, vi in candidates:
        if vi is None or vi in seen_valid_indices:
            continue
        seen_valid_indices.add(vi)

        frame_idx, keypoints = valid_frames_data[vi]
        frame_angles = angles_per_frame[vi]

        if frame_idx >= len(middle_frames):
            logger.warning("frame_index %d out of range for middle_frames", frame_idx)
            continue

        bgr = middle_frames[frame_idx]
        image_b64 = _encode_frame(bgr)
        annotated = _draw_overlay(bgr, keypoints, frame_angles)
        annotated_b64 = _encode_frame(annotated)

        key_frames.append(
            KeyFrame(
                label=label,
                frame_index=frame_idx,
                keypoints=keypoints,
                image_b64=image_b64,
                annotated_image_b64=annotated_b64,
            )
        )

    return key_frames


# ---------------------------------------------------------------------------
# Frame selection helpers
# ---------------------------------------------------------------------------


def _find_contact_frame(angles_per_frame: List[Dict[str, float]]) -> Optional[int]:
    """Return index of the frame with elbow_angle closest to 165° (ideal midpoint)."""
    target = 165.0
    return min(
        range(len(angles_per_frame)),
        key=lambda i: abs(angles_per_frame[i].get("elbow_angle", float("inf")) - target),
        default=None,
    )


def _find_windup_frame(angles_per_frame: List[Dict[str, float]]) -> Optional[int]:
    """Return index of the frame with maximum shoulder_rotation."""
    return max(
        range(len(angles_per_frame)),
        key=lambda i: angles_per_frame[i].get("shoulder_rotation", -1.0),
        default=None,
    )


def _find_follow_through_frame(angles_per_frame: List[Dict[str, float]]) -> Optional[int]:
    """Return index of the frame with maximum follow_through."""
    return max(
        range(len(angles_per_frame)),
        key=lambda i: angles_per_frame[i].get("follow_through", -1.0),
        default=None,
    )


# ---------------------------------------------------------------------------
# Encoding + overlay helpers
# ---------------------------------------------------------------------------


def _encode_frame(frame_bgr: np.ndarray, quality: int = 50) -> str:
    _, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def _draw_overlay(
    frame_bgr: np.ndarray,
    keypoints: Dict[int, Tuple[float, float]],
    frame_angles: Dict[str, float],
) -> np.ndarray:
    """Return a copy of frame_bgr with a color-coded skeleton overlay drawn on it."""
    out = copy.deepcopy(frame_bgr)
    h, w = out.shape[:2]

    def to_px(lm_idx: int) -> Optional[Tuple[int, int]]:
        if lm_idx not in keypoints:
            return None
        x, y = keypoints[lm_idx]
        return (int(x * w), int(y * h))

    # Draw connections
    for a, b in _CONNECTIONS:
        pa, pb = to_px(a), to_px(b)
        if pa and pb:
            cv2.line(out, pa, pb, _COLOR_NEUTRAL, 2)

    # Draw joints
    for lm_idx in keypoints:
        pt = to_px(lm_idx)
        if pt is None:
            continue
        angle_name = _LANDMARK_ANGLE.get(lm_idx)
        color = _joint_severity_color(angle_name, frame_angles) if angle_name else _COLOR_NEUTRAL
        cv2.circle(out, pt, 5, color, -1)

    # Annotate elbow, shoulder, hip, knee with value + goal
    _annotate_joint(out, keypoints, frame_angles, 13, "elbow", "elbow_angle", w, h)
    _annotate_joint(out, keypoints, frame_angles, 11, "shoulder", "shoulder_rotation", w, h)
    _annotate_joint(out, keypoints, frame_angles, 23, "hip", "hip_turn", w, h)
    _annotate_joint(out, keypoints, frame_angles, 25, "knee", "knee_flex", w, h)

    return out


def _annotate_joint(
    frame: np.ndarray,
    keypoints: Dict[int, Tuple[float, float]],
    frame_angles: Dict[str, float],
    lm_idx: int,
    short_name: str,
    angle_key: str,
    w: int,
    h: int,
) -> None:
    if lm_idx not in keypoints or angle_key not in frame_angles:
        return
    x, y = keypoints[lm_idx]
    px, py = int(x * w), int(y * h)
    value = frame_angles[angle_key]
    r = IDEAL_RANGES[angle_key]
    label = f"{short_name}: {value:.0f}deg ({r.min_deg:.0f}-{r.max_deg:.0f})"
    cv2.putText(
        frame, label, (px + 7, py),
        cv2.FONT_HERSHEY_SIMPLEX, 0.35, _COLOR_NEUTRAL, 1, cv2.LINE_AA,
    )


def _joint_severity_color(
    angle_name: str,
    frame_angles: Dict[str, float],
) -> Tuple[int, int, int]:
    if angle_name not in IDEAL_RANGES or angle_name not in frame_angles:
        return _COLOR_NEUTRAL
    value = frame_angles[angle_name]
    r = IDEAL_RANGES[angle_name]
    if r.min_deg <= value <= r.max_deg:
        return _COLOR_GOOD
    dist = min(abs(value - r.min_deg), abs(value - r.max_deg))
    if dist <= BOUNDARY_TOLERANCE:
        return _COLOR_WARNING
    return _COLOR_CRITICAL

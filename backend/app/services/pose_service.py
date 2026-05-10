"""PoseService: extract averaged MediaPipe BlazePose keypoints from in-memory video bytes."""

import logging
import os
import tempfile
import time
from typing import Dict, List, Tuple

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode
import numpy as np

logger = logging.getLogger(__name__)

# Type alias: list of (frame_index_in_middle_frames, {landmark_idx: (x, y)})
PerFrameKeypoints = List[Tuple[int, Dict[int, Tuple[float, float]]]]

MODEL_PATH = "/models/pose_landmarker_full.task"

# Required landmark indices: shoulders, elbows, wrists, hips, knees
REQUIRED_LANDMARKS = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26]
VISIBILITY_THRESHOLD = 0.5
MIN_VALID_FRAMES = 3


def extract_keypoints(video_bytes: bytes) -> Dict[int, Tuple[float, float]]:
    """Extract averaged BlazePose keypoints from in-memory video bytes.

    Args:
        video_bytes: Raw video file content in memory.

    Returns:
        A dict mapping landmark index -> (avg_x, avg_y) averaged across valid frames.

    Raises:
        ValueError: If fewer than MIN_VALID_FRAMES valid frames are detected.
    """
    start_time = time.perf_counter()

    tmp_path = _write_temp_video(video_bytes)
    try:
        keypoints = _process_video(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError as exc:
            logger.warning("Could not delete temp file %s: %s", tmp_path, exc)

    elapsed = time.perf_counter() - start_time
    logger.info("Pose extraction completed in %.2fs, %d landmarks extracted", elapsed, len(keypoints))
    return keypoints


def extract_keypoints_per_frame(
    video_bytes: bytes,
) -> tuple[list[np.ndarray], PerFrameKeypoints]:
    """Return (middle_frames_bgr, valid_frames_with_indices).

    Unlike extract_keypoints(), this does not average — it returns every valid
    frame's keypoints together with its index into middle_frames, so callers
    can retrieve the corresponding BGR frame for rendering.

    Raises:
        ValueError: If fewer than MIN_VALID_FRAMES valid frames are detected.
    """
    start_time = time.perf_counter()

    tmp_path = _write_temp_video(video_bytes)
    try:
        cap = cv2.VideoCapture(tmp_path)
        try:
            all_frames = _read_all_frames(cap)
        finally:
            cap.release()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError as exc:
            logger.warning("Could not delete temp file %s: %s", tmp_path, exc)

    total = len(all_frames)
    if total == 0:
        raise ValueError("Could not decode any frames from video.")

    start_idx = int(total * 0.20)
    end_idx = int(total * 0.80)
    middle_frames = all_frames[start_idx:end_idx]

    valid_frames_data = _run_mediapipe_indexed(middle_frames)

    if len(valid_frames_data) < MIN_VALID_FRAMES:
        raise ValueError(
            f"Only {len(valid_frames_data)} valid frames detected; "
            f"minimum required is {MIN_VALID_FRAMES}."
        )

    elapsed = time.perf_counter() - start_time
    logger.info(
        "Per-frame extraction completed in %.2fs, %d valid frames",
        elapsed,
        len(valid_frames_data),
    )
    return middle_frames, valid_frames_data


def average_keypoints(
    valid_frames_data: PerFrameKeypoints,
) -> Dict[int, Tuple[float, float]]:
    """Average keypoints across all valid frames. Thin public wrapper over _average_keypoints."""
    return _average_keypoints([kp for _, kp in valid_frames_data])


def _write_temp_video(video_bytes: bytes) -> str:
    """Write video bytes to a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_bytes)
        return tmp.name


def _process_video(tmp_path: str) -> Dict[int, Tuple[float, float]]:
    """Open the video at tmp_path, extract middle 60% frames, return averaged keypoints."""
    cap = cv2.VideoCapture(tmp_path)
    try:
        all_frames = _read_all_frames(cap)
    finally:
        cap.release()

    total = len(all_frames)
    if total == 0:
        raise ValueError("Could not decode any frames from video.")

    # Select middle 60%: skip first 20% and last 20%
    start_idx = int(total * 0.20)
    end_idx = int(total * 0.80)
    middle_frames = all_frames[start_idx:end_idx]

    logger.debug(
        "Total frames: %d, middle 60%% range: [%d, %d) = %d frames",
        total,
        start_idx,
        end_idx,
        len(middle_frames),
    )

    valid_keypoints = _run_mediapipe(middle_frames)

    if len(valid_keypoints) < MIN_VALID_FRAMES:
        raise ValueError(
            f"Only {len(valid_keypoints)} valid frames detected; "
            f"minimum required is {MIN_VALID_FRAMES}."
        )

    return _average_keypoints(valid_keypoints)


def _read_all_frames(cap: cv2.VideoCapture) -> list:
    """Read all frames from a VideoCapture into memory as a list of BGR ndarrays."""
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    return frames


def _run_mediapipe(frames: list) -> list:
    """Run PoseLandmarker on each frame; return list of per-frame landmark dicts for valid frames."""
    base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
    options = PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=RunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    valid_frames: list = []
    with PoseLandmarker.create_from_options(options) as landmarker:
        for frame in frames:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            result = landmarker.detect(mp_image)

            if not result.pose_landmarks:
                continue

            landmarks = result.pose_landmarks[0]  # first person only
            frame_data: Dict[int, Tuple[float, float]] = {}
            all_visible = True

            for idx in REQUIRED_LANDMARKS:
                lm = landmarks[idx]
                if lm.visibility <= VISIBILITY_THRESHOLD:
                    all_visible = False
                    break
                frame_data[idx] = (lm.x, lm.y)

            if all_visible:
                valid_frames.append(frame_data)

    return valid_frames


def _run_mediapipe_indexed(frames: list) -> PerFrameKeypoints:
    """Same as _run_mediapipe but returns (frame_index, keypoints) pairs."""
    base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
    options = PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=RunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    valid_frames: PerFrameKeypoints = []
    with PoseLandmarker.create_from_options(options) as landmarker:
        for frame_idx, frame in enumerate(frames):
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            result = landmarker.detect(mp_image)

            if not result.pose_landmarks:
                continue

            landmarks = result.pose_landmarks[0]
            frame_data: Dict[int, Tuple[float, float]] = {}
            all_visible = True

            for idx in REQUIRED_LANDMARKS:
                lm = landmarks[idx]
                if lm.visibility <= VISIBILITY_THRESHOLD:
                    all_visible = False
                    break
                frame_data[idx] = (lm.x, lm.y)

            if all_visible:
                valid_frames.append((frame_idx, frame_data))

    return valid_frames


def _average_keypoints(
    valid_frames: list,
) -> Dict[int, Tuple[float, float]]:
    """Average x, y coordinates across all valid frames per landmark."""
    accum: Dict[int, list] = {idx: [] for idx in REQUIRED_LANDMARKS}

    for frame_data in valid_frames:
        for idx, (x, y) in frame_data.items():
            accum[idx].append((x, y))

    result: Dict[int, Tuple[float, float]] = {}
    for idx, coords in accum.items():
        if coords:
            avg_x = float(np.mean([c[0] for c in coords]))
            avg_y = float(np.mean([c[1] for c in coords]))
            result[idx] = (avg_x, avg_y)

    return result

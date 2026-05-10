import asyncio
import json
import logging
import time
from dataclasses import asdict
from typing import AsyncGenerator

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.services.angle_service import compute_angles
from app.services.coaching_service import get_structured_coaching_feedback
from app.services.key_moment_service import extract_key_frames
from app.services.pose_service import average_keypoints, extract_keypoints_per_frame

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_BYTES = 100 * 1024 * 1024  # 100 MB


def _sse(stage: str, message: str, data: dict | None = None) -> str:
    payload: dict = {"stage": stage, "message": message}
    if data is not None:
        payload["data"] = data
    return f"data: {json.dumps(payload)}\n\n"


def _key_frame_wire(kf) -> dict:
    """Serialize a KeyFrame for the wire format, omitting internal fields."""
    return {
        "label": kf.label,
        "angles": kf.angles,
        "image_b64": kf.image_b64,
        "annotated_image_b64": kf.annotated_image_b64,
    }


@router.post("/analyze/stream")
async def analyze_stream(video: UploadFile = File(...)) -> StreamingResponse:
    content = await video.read()

    async def event_stream() -> AsyncGenerator[str, None]:
        if len(content) > MAX_BYTES:
            yield _sse("error", "Video file too large. Maximum size is 100MB.")
            return

        start = time.perf_counter()

        yield _sse("extracting", "Extracting pose keypoints with BlazePose…")
        try:
            middle_frames, valid_frames_data = await asyncio.to_thread(
                extract_keypoints_per_frame, content
            )
        except ValueError as exc:
            yield _sse("error", str(exc))
            return

        yield _sse("angles", f"Detected {len(valid_frames_data)} valid frames. Computing joint angles…")
        averaged_kp = await asyncio.to_thread(average_keypoints, valid_frames_data)
        angles = await asyncio.to_thread(compute_angles, averaged_kp)

        per_frame_angles = [
            compute_angles(kp).as_dict() for _, kp in valid_frames_data
        ]

        yield _sse("coaching", "Computing angles done. Generating structured coaching tips…")
        tips = await asyncio.to_thread(get_structured_coaching_feedback, angles)

        yield _sse("keyframes", "Identifying key swing moments and drawing overlays…")
        key_frames = await asyncio.to_thread(
            extract_key_frames, middle_frames, valid_frames_data, per_frame_angles
        )

        elapsed = round(time.perf_counter() - start, 2)
        result = {
            "status": "success",
            "processing_time_seconds": elapsed,
            "keypoints_extracted": len(averaged_kp),
            "angles": angles.as_dict(),
            "tips": [asdict(t) for t in tips],
            "key_frames": [_key_frame_wire(kf) for kf in key_frames],
        }
        yield _sse("done", f"Analysis complete in {elapsed}s.", result)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/analyze")
async def analyze(video: UploadFile = File(...)) -> dict:
    content = await video.read()

    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=422,
            detail={"status": "error", "message": "Video file too large. Maximum size is 100MB."},
        )

    start = time.perf_counter()

    try:
        middle_frames, valid_frames_data = extract_keypoints_per_frame(content)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"status": "error", "message": str(exc)},
        ) from exc

    averaged_kp = average_keypoints(valid_frames_data)
    angles = compute_angles(averaged_kp)

    per_frame_angles = [
        compute_angles(kp).as_dict() for _, kp in valid_frames_data
    ]

    tips = get_structured_coaching_feedback(angles)
    key_frames = extract_key_frames(middle_frames, valid_frames_data, per_frame_angles)

    elapsed = round(time.perf_counter() - start, 2)
    logger.info("analyze completed in %.2fs", elapsed)

    return {
        "status": "success",
        "processing_time_seconds": elapsed,
        "keypoints_extracted": len(averaged_kp),
        "angles": angles.as_dict(),
        "tips": [asdict(t) for t in tips],
        "key_frames": [_key_frame_wire(kf) for kf in key_frames],
    }

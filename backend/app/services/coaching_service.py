"""CoachingService: call HuggingFace Inference API and return coaching feedback."""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import List

from huggingface_hub import InferenceClient

from app.services.angle_service import Angles
from app.services.constants import BOUNDARY_TOLERANCE, IDEAL_RANGES

logger = logging.getLogger(__name__)

HF_MODEL = "google/gemma-2-2b-it"
HF_TIMEOUT = 30  # seconds

FALLBACK: List[str] = [
    "Ensure your elbow is near-straight at contact (160-170°) for maximum power transfer.",
    "Focus on a full shoulder rotation (80-100°) initiated from the split step.",
    "Maintain knee flex (20-35°) throughout the swing to drive power from the ground up.",
]

COACHING_PROMPT = """You are an expert tennis coach analyzing a forehand swing.

Biomechanical measurements from the swing:
- Elbow angle at contact: {elbow_angle:.1f}°
- Shoulder rotation: {shoulder_rotation:.1f}°
- Hip turn: {hip_turn:.1f}°
- Knee flex: {knee_flex:.1f}°
- Follow-through arc: {follow_through:.1f}°

Ideal forehand ranges:
- Elbow: 160-170° at contact (near-straight arm)
- Shoulder rotation: 80-100° (full unit turn)
- Hip turn: 70-90° (drives power from ground up)
- Knee flex: 20-35° (athletic stance)
- Follow-through: >180° (racket finishes over opposite shoulder)

Give exactly 3 coaching observations. Format as a JSON array of strings:
["observation 1", "observation 2", "observation 3"]
Respond with only the JSON array, nothing else."""


def get_coaching_feedback(angles: Angles) -> List[str]:
    """Call HuggingFace and return a list of exactly 3 coaching observation strings.

    Falls back to FALLBACK on any error without re-raising.

    Args:
        angles: The computed Angles object from angle_service.

    Returns:
        A list of exactly 3 coaching strings.

    Raises:
        RuntimeError: If HF_API_TOKEN is not set in the environment.
    """
    token = os.environ.get("HF_API_TOKEN")
    if not token:
        raise RuntimeError(
            "HF_API_TOKEN environment variable is not set. "
            "Add it to your .env file."
        )

    prompt = COACHING_PROMPT.format(
        elbow_angle=angles.elbow_angle,
        shoulder_rotation=angles.shoulder_rotation,
        hip_turn=angles.hip_turn,
        knee_flex=angles.knee_flex,
        follow_through=angles.follow_through,
    )

    client = InferenceClient(token=token, timeout=HF_TIMEOUT)
    start = time.perf_counter()
    used_fallback = False

    try:
        response = client.chat_completion(
            model=HF_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        observations = _parse_observations(content)
    except Exception as exc:
        logger.warning("HuggingFace call failed (%s); using fallback.", exc)
        used_fallback = True
        observations = FALLBACK

    elapsed = time.perf_counter() - start
    logger.info(
        "Coaching service completed in %.2fs (fallback=%s)",
        elapsed,
        used_fallback,
    )
    return observations


# ---------------------------------------------------------------------------
# Structured coaching (v0.2)
# ---------------------------------------------------------------------------


@dataclass
class CoachingTip:
    angle_name: str
    severity: str   # "good" | "warning" | "critical"
    observation: str
    drill: str


STRUCTURED_COACHING_PROMPT = """You are an expert tennis coach analyzing a forehand swing.

Biomechanical measurements:
- Elbow angle at contact: {elbow_angle:.1f}°
- Shoulder rotation: {shoulder_rotation:.1f}°
- Hip turn: {hip_turn:.1f}°
- Knee flex: {knee_flex:.1f}°
- Follow-through arc: {follow_through:.1f}°

Ideal forehand ranges:
- Elbow: 160-170° (near-straight arm at contact)
- Shoulder rotation: 80-100° (full unit turn)
- Hip turn: 70-90° (drives power from ground up)
- Knee flex: 20-35° (athletic stance)
- Follow-through: >180° (racket finishes over opposite shoulder)

For each of the 5 angles, provide a one-sentence observation and one specific drill.
Respond ONLY with a JSON object in this exact format:
{{
  "elbow_angle":       {{"observation": "...", "drill": "..."}},
  "shoulder_rotation": {{"observation": "...", "drill": "..."}},
  "hip_turn":          {{"observation": "...", "drill": "..."}},
  "knee_flex":         {{"observation": "...", "drill": "..."}},
  "follow_through":    {{"observation": "...", "drill": "..."}}
}}"""

STRUCTURED_FALLBACK: List[CoachingTip] = [
    CoachingTip(
        angle_name="elbow_angle",
        severity="warning",
        observation="Keep your elbow near-straight (160-170°) at contact for maximum power transfer.",
        drill="Shadow swing drill: freeze at the contact point and check elbow extension. 3 sets of 10 reps.",
    ),
    CoachingTip(
        angle_name="shoulder_rotation",
        severity="warning",
        observation="Initiate a full shoulder rotation (80-100°) from the split step.",
        drill="Unit turn drill: stand sideways, rotate shoulders fully until your back faces the net. 20 reps.",
    ),
    CoachingTip(
        angle_name="hip_turn",
        severity="warning",
        observation="Drive power from the ground up with a 70-90° hip turn.",
        drill="Hip separation drill: hold a racket across your hips, rotate hips before shoulders. 15 reps.",
    ),
    CoachingTip(
        angle_name="knee_flex",
        severity="warning",
        observation="Maintain a 20-35° knee flex throughout the swing for a stable athletic stance.",
        drill="Wall sit at 30° for 30 seconds, then shadow swing maintaining that same flex. 5 sets.",
    ),
    CoachingTip(
        angle_name="follow_through",
        severity="warning",
        observation="Finish with the racket over your opposite shoulder (>180°) for full follow-through.",
        drill="High finish drill: exaggerate the follow-through so the racket touches your non-dominant shoulder. 15 reps.",
    ),
]


def get_structured_coaching_feedback(angles: Angles) -> List[CoachingTip]:
    """Return structured coaching tips with locally-computed severity.

    Severity is determined by comparing each angle against IDEAL_RANGES — the
    LLM only provides observation text and drill instructions, never severity.

    Falls back to STRUCTURED_FALLBACK on any error without re-raising.

    Raises:
        RuntimeError: If HF_API_TOKEN is not set in the environment.
    """
    token = os.environ.get("HF_API_TOKEN")
    if not token:
        raise RuntimeError(
            "HF_API_TOKEN environment variable is not set. "
            "Add it to your .env file."
        )

    prompt = STRUCTURED_COACHING_PROMPT.format(
        elbow_angle=angles.elbow_angle,
        shoulder_rotation=angles.shoulder_rotation,
        hip_turn=angles.hip_turn,
        knee_flex=angles.knee_flex,
        follow_through=angles.follow_through,
    )

    client = InferenceClient(token=token, timeout=HF_TIMEOUT)
    start = time.perf_counter()
    used_fallback = False

    try:
        response = client.chat_completion(
            model=HF_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        tips = _parse_structured_tips(content, angles)
    except Exception as exc:
        logger.warning("HuggingFace structured call failed (%s); using fallback.", exc)
        used_fallback = True
        tips = STRUCTURED_FALLBACK

    elapsed = time.perf_counter() - start
    logger.info(
        "Structured coaching completed in %.2fs (fallback=%s)",
        elapsed,
        used_fallback,
    )
    return tips


def _compute_severity(angle_name: str, value: float) -> str:
    """Compute severity locally from IDEAL_RANGES — never delegated to the LLM."""
    if angle_name not in IDEAL_RANGES:
        return "warning"
    r = IDEAL_RANGES[angle_name]
    if r.min_deg <= value <= r.max_deg:
        return "good"
    dist = min(abs(value - r.min_deg), abs(value - r.max_deg))
    if dist <= BOUNDARY_TOLERANCE:
        return "warning"
    return "critical"


def _parse_structured_tips(content: str, angles: Angles) -> List[CoachingTip]:
    """Parse LLM response into CoachingTip list; falls back to STRUCTURED_FALLBACK on any issue."""
    angle_values = angles.as_dict()
    expected_keys = set(angle_values.keys())

    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Could not parse structured response as JSON (%s); using fallback.", exc)
        return STRUCTURED_FALLBACK

    if not isinstance(parsed, dict) or not expected_keys.issubset(parsed.keys()):
        logger.warning("Structured response missing expected keys; using fallback.")
        return STRUCTURED_FALLBACK

    tips: List[CoachingTip] = []
    for angle_name in expected_keys:
        entry = parsed[angle_name]
        if not isinstance(entry, dict) or "observation" not in entry or "drill" not in entry:
            logger.warning("Missing observation/drill for %s; using fallback.", angle_name)
            return STRUCTURED_FALLBACK
        tips.append(
            CoachingTip(
                angle_name=angle_name,
                severity=_compute_severity(angle_name, angle_values[angle_name]),
                observation=str(entry["observation"]),
                drill=str(entry["drill"]),
            )
        )

    return tips


def _parse_observations(content: str) -> List[str]:
    """Parse model response content into a list of exactly 3 strings.

    Falls back to FALLBACK if parsing fails or count != 3.
    """
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Could not parse HuggingFace response as JSON (%s); using fallback.", exc)
        return FALLBACK

    if not isinstance(parsed, list) or len(parsed) != 3:
        logger.warning(
            "HuggingFace response has %s items (expected 3); using fallback.",
            len(parsed) if isinstance(parsed, list) else "non-list",
        )
        return FALLBACK

    return [str(item) for item in parsed]

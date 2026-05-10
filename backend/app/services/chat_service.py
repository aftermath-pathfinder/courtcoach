"""ChatService: multi-turn coaching chat powered by OpenAI Chat Completions."""

import logging
import os
from typing import Any

from openai import OpenAI

from app.services.constants import BOUNDARY_TOLERANCE, IDEAL_RANGES

logger = logging.getLogger(__name__)

OPENAI_MODEL = "gpt-4o-mini"

FALLBACK_REPLY = (
    "I'm having trouble connecting to the coaching service right now. "
    "Please check your analysis results above and try again in a moment."
)


def get_chat_reply(
    messages: list[dict[str, str]],
    analysis_context: dict[str, Any] | None = None,
) -> str:
    """Send a conversation to OpenAI and return the assistant reply.

    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."} dicts,
                  representing the full conversation so far (newest last).
        analysis_context: Optional dict with keys "angles", "tips", "key_frames"
                          from a completed analysis. Used to build the system prompt.

    Returns:
        The assistant's reply string.

    Raises:
        RuntimeError: If OPENAI_API_KEY is not set.
    """
    token = os.environ.get("OPENAI_API_KEY")
    if not token:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Add it to your .env file."
        )

    system_prompt = _build_system_prompt(analysis_context)
    openai_messages = [{"role": "system", "content": system_prompt}] + messages

    client = OpenAI(api_key=token)
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=openai_messages,
            max_tokens=400,
            temperature=0.7,
        )
        reply = response.choices[0].message.content or FALLBACK_REPLY
    except Exception as exc:
        logger.warning("OpenAI chat call failed (%s); using fallback reply.", exc)
        reply = FALLBACK_REPLY

    logger.info("Chat reply generated (%d chars)", len(reply))
    return reply


def _build_system_prompt(analysis_context: dict[str, Any] | None) -> str:
    base = (
        "You are an expert tennis coach having a follow-up conversation after "
        "analyzing a player's forehand swing. Be specific, encouraging, and concise "
        "(2-4 sentences unless the player explicitly asks for more detail). "
        "Reference the biomechanical data when relevant. "
        "If asked about something unrelated to tennis, politely redirect."
    )

    if not analysis_context:
        return base + "\n\nNo analysis data is available for this session."

    lines = [base, "\n--- BIOMECHANICAL ANALYSIS ---"]

    angles = analysis_context.get("angles", {})
    for key, value in angles.items():
        if key not in IDEAL_RANGES:
            continue
        r = IDEAL_RANGES[key]
        if r.min_deg <= value <= r.max_deg:
            sev = "GOOD"
        else:
            dist = min(abs(value - r.min_deg), abs(value - r.max_deg))
            sev = "WARNING" if dist <= BOUNDARY_TOLERANCE else "CRITICAL"
        label = key.replace("_", " ").title()
        lines.append(f"- {label}: {value:.1f}° (ideal {r.min_deg:.0f}–{r.max_deg:.0f}°) [{sev}]")

    tips = analysis_context.get("tips", [])
    if tips:
        lines.append("\n--- COACHING OBSERVATIONS ---")
        for i, tip in enumerate(tips, 1):
            obs = tip.get("observation", "")
            drill = tip.get("drill", "")
            sev = tip.get("severity", "").upper()
            lines.append(f"{i}. [{sev}] {obs}")
            if drill:
                lines.append(f"   Drill: {drill}")

    key_frames = analysis_context.get("key_frames", [])
    if key_frames:
        lines.append("\n--- KEY SWING MOMENTS ---")
        for kf in key_frames:
            phase = kf.get("label", "").replace("_", " ").title()
            kf_angles = kf.get("angles", {})
            angle_strs = [
                f"{k.replace('_', ' ')}: {v:.0f}°"
                for k, v in kf_angles.items()
            ]
            lines.append(f"- {phase}: {', '.join(angle_strs)}")

    return "\n".join(lines)

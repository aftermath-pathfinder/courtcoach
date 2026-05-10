"""Shared constants for ideal tennis swing angle ranges."""

from typing import NamedTuple


class AngleRange(NamedTuple):
    min_deg: float
    max_deg: float


IDEAL_RANGES: dict[str, AngleRange] = {
    "elbow_angle":       AngleRange(160.0, 170.0),
    "shoulder_rotation": AngleRange(80.0,  100.0),
    "hip_turn":          AngleRange(70.0,  90.0),
    "knee_flex":         AngleRange(20.0,  35.0),
    "follow_through":    AngleRange(180.0, 360.0),
}

BOUNDARY_TOLERANCE = 10.0  # degrees; within this of a boundary → "warning"

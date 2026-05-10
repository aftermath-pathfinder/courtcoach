import { useState } from "react";
import type { AnalysisAngles, KeyFrame } from "../../types/analysis";

const LABEL_MAP: Record<KeyFrame["label"], string> = {
  contact:        "Contact Point",
  windup:         "Wind-up",
  follow_through: "Follow-Through",
};

const PHASE_ANGLES: Record<KeyFrame["label"], (keyof AnalysisAngles)[]> = {
  contact:        ["elbow_angle", "knee_flex"],
  windup:         ["shoulder_rotation", "hip_turn"],
  follow_through: ["follow_through", "shoulder_rotation"],
};

interface AngleMeta {
  label: string;
  ideal: [number, number];
  displayIdeal: string;
  describe: (v: number) => string;
}

const ANGLE_META: Record<keyof AnalysisAngles, AngleMeta> = {
  elbow_angle: {
    label: "Elbow",
    ideal: [160, 170],
    displayIdeal: "160–170°",
    describe: (v) =>
      v >= 160 && v <= 170
        ? "near-straight arm — ideal for power transfer"
        : v >= 145
          ? "slightly bent — extend a little more at contact"
          : "too bent — losing power at contact",
  },
  shoulder_rotation: {
    label: "Shoulder rotation",
    ideal: [80, 100],
    displayIdeal: "80–100°",
    describe: (v) =>
      v >= 80 && v <= 100
        ? "full unit turn — excellent rotation"
        : v < 80
          ? "not rotating enough — turn your shoulders more through the ball"
          : "over-rotated — pull back slightly for better control",
  },
  hip_turn: {
    label: "Hip turn",
    ideal: [70, 90],
    displayIdeal: "70–90°",
    describe: (v) =>
      v >= 70 && v <= 90
        ? "good hip drive — hips leading the kinetic chain"
        : v < 70
          ? "hips not engaging — let hips initiate the swing"
          : "over-rotating hips — stay balanced through contact",
  },
  knee_flex: {
    label: "Knee flex",
    ideal: [20, 35],
    displayIdeal: "20–35°",
    describe: (v) =>
      v >= 20 && v <= 35
        ? "athletic stance — good ground connection"
        : v < 20
          ? "too upright — bend knees more for stability and power"
          : "too deep — lighten up for quicker weight transfer",
  },
  follow_through: {
    label: "Follow-through arc",
    ideal: [180, 360],
    displayIdeal: ">180°",
    describe: (v) =>
      v >= 180
        ? "racket finishes over opposite shoulder — great extension"
        : "incomplete follow-through — swing all the way through the ball",
  },
};

const TOLERANCE = 10;

function getSeverity(ideal: [number, number], value: number): "good" | "warning" | "critical" {
  const [min, max] = ideal;
  if (value >= min && value <= max) return "good";
  const dist = Math.min(Math.abs(value - min), Math.abs(value - max));
  return dist <= TOLERANCE ? "warning" : "critical";
}

const BADGE_COLORS = {
  good:     "bg-green-100 text-green-800",
  warning:  "bg-yellow-100 text-yellow-800",
  critical: "bg-red-100 text-red-800",
};

const DOT_COLORS = {
  good:     "bg-green-500",
  warning:  "bg-yellow-500",
  critical: "bg-red-500",
};

function AngleRow({ name, value }: { name: keyof AnalysisAngles; value: number }) {
  const meta = ANGLE_META[name];
  const sev = getSeverity(meta.ideal, value);

  return (
    <div className="flex items-start gap-2">
      <span className={`mt-1.5 h-2 w-2 rounded-full flex-shrink-0 ${DOT_COLORS[sev]}`} />
      <div className="min-w-0">
        <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${BADGE_COLORS[sev]}`}>
          {meta.label}: {value.toFixed(0)}°
        </span>
        <span className="ml-1.5 text-xs text-gray-400">ideal {meta.displayIdeal}</span>
        <p className="text-xs text-gray-600 mt-0.5">{meta.describe(value)}</p>
      </div>
    </div>
  );
}

interface Props {
  frames: KeyFrame[];
}

export function KeyFramePanel({ frames }: Props) {
  const [showAnnotated, setShowAnnotated] = useState<Record<string, boolean>>({});

  if (frames.length === 0) return null;

  function toggle(label: string) {
    setShowAnnotated((prev) => ({ ...prev, [label]: !prev[label] }));
  }

  return (
    <section aria-label="Key swing frames" className="space-y-4">
      <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Key Frames</h2>
      {frames.map((frame) => {
        const annotated = showAnnotated[frame.label] ?? false;
        const src = annotated ? frame.annotated_image_b64 : frame.image_b64;
        const humanLabel = LABEL_MAP[frame.label];
        const angleNames = PHASE_ANGLES[frame.label];

        return (
          <div key={frame.label} className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
            <img
              src={`data:image/jpeg;base64,${src}`}
              alt={humanLabel}
              className="w-full object-contain"
            />
            <div className="px-4 py-3 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-800">{humanLabel}</span>
                <button
                  onClick={() => toggle(frame.label)}
                  className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  aria-label={`${annotated ? "Hide" : "Show"} overlay for ${humanLabel}`}
                >
                  {annotated ? "Hide overlay" : "Show overlay"}
                </button>
              </div>
              <div className="space-y-2 pt-2 border-t border-gray-100">
                {angleNames.map((name) => (
                  <AngleRow key={name} name={name} value={frame.angles[name]} />
                ))}
              </div>
            </div>
          </div>
        );
      })}
    </section>
  );
}

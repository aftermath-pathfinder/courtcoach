import { useState } from "react";
import type { KeyFrame } from "../../types/analysis";

const LABEL_MAP: Record<KeyFrame["label"], string> = {
  contact:       "Contact Point",
  windup:        "Wind-up",
  follow_through: "Follow-Through",
};

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
    <section aria-label="Key swing frames" className="space-y-3">
      <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Key Frames</h2>
      <div className="flex flex-col sm:flex-row gap-3">
        {frames.map((frame) => {
          const annotated = showAnnotated[frame.label] ?? false;
          const src = annotated ? frame.annotated_image_b64 : frame.image_b64;
          const humanLabel = LABEL_MAP[frame.label];

          return (
            <div key={frame.label} className="flex-1 rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
              <img
                src={`data:image/jpeg;base64,${src}`}
                alt={humanLabel}
                className="w-full object-cover"
              />
              <div className="px-3 py-2 flex items-center justify-between">
                <span className="text-xs font-medium text-gray-600">{humanLabel}</span>
                <button
                  onClick={() => toggle(frame.label)}
                  className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  aria-label={`${annotated ? "Hide" : "Show"} overlay for ${humanLabel}`}
                >
                  {annotated ? "Hide overlay" : "Show overlay"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

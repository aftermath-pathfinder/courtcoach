import type { CoachingTip } from "../../types/analysis";

const SEVERITY_BADGE: Record<CoachingTip["severity"], string> = {
  good:     "bg-green-100 text-green-700",
  warning:  "bg-amber-100 text-amber-700",
  critical: "bg-red-100 text-red-700",
};

const SEVERITY_LABEL: Record<CoachingTip["severity"], string> = {
  good:     "Good",
  warning:  "Warning",
  critical: "Critical",
};

interface Props {
  tip: CoachingTip;
}

export function CoachingCard({ tip }: Props) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm space-y-2">
      <div className="flex items-center gap-2">
        <span
          aria-label={`Severity: ${tip.severity}`}
          className={`px-2 py-0.5 rounded-full text-xs font-semibold ${SEVERITY_BADGE[tip.severity]}`}
        >
          {SEVERITY_LABEL[tip.severity]}
        </span>
        <span className="text-xs text-gray-400 font-medium uppercase tracking-wide">
          {tip.angle_name.replace(/_/g, " ")}
        </span>
      </div>
      <p className="text-gray-700 text-sm leading-relaxed">{tip.observation}</p>
      <p className="text-gray-500 text-sm italic leading-relaxed">
        <span className="font-medium not-italic text-gray-600">Drill: </span>
        {tip.drill}
      </p>
    </div>
  );
}

import type { AnalysisState } from "../../types/analysis";

interface Props {
  state: AnalysisState;
  logs?: string[];
}

export function AnalysisStatus({ state, logs = [] }: Props) {
  if (state.phase === "idle") return null;

  if (state.phase === "uploading") {
    return (
      <p role="status" className="text-gray-600 text-sm text-center">
        Uploading video…
      </p>
    );
  }

  if (state.phase === "processing") {
    return (
      <div role="status" className="space-y-3">
        <div className="text-center space-y-1">
          <p className="text-gray-700 text-sm font-medium">Analysing your swing…</p>
          <p className="text-gray-400 text-xs">This takes 10–20 seconds</p>
        </div>
        {logs.length > 0 && (
          <div className="rounded-lg bg-gray-950 text-green-400 font-mono text-xs p-3 space-y-1">
            {logs.map((log, i) => (
              <p key={i}>
                <span className="text-gray-600">{">"}</span> {log}
              </p>
            ))}
            <p className="animate-pulse text-gray-600">{">"} _</p>
          </div>
        )}
      </div>
    );
  }

  if (state.phase === "done") {
    return (
      <p role="status" className="text-green-700 text-sm text-center">
        Analysis complete in {state.result.processing_time_seconds}s
      </p>
    );
  }

  // phase === "error"
  return (
    <p role="alert" className="text-red-600 text-sm text-center">
      {state.message}
    </p>
  );
}

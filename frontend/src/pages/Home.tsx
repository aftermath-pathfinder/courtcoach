import { useState } from "react";
import { analyzeSwingStream } from "../api/client";
import { VideoUploader } from "../components/VideoUploader/VideoUploader";
import { AnalysisStatus } from "../components/AnalysisStatus/AnalysisStatus";
import { CoachingCard } from "../components/CoachingCard/CoachingCard";
import { KeyFramePanel } from "../components/KeyFramePanel/KeyFramePanel";
import { ChatSidebar } from "../components/ChatSidebar/ChatSidebar";
import type { AnalysisResult, AnalysisState, ChatContext } from "../types/analysis";

export function Home() {
  const [state, setState] = useState<AnalysisState>({ phase: "idle" });
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  async function handleFileSelect(file: File) {
    setResult(null);
    setLogs([]);
    setState({ phase: "uploading" });

    try {
      setState({ phase: "processing" });
      const data = await analyzeSwingStream(file, (message) => {
        setLogs((prev) => [...prev, message]);
      });
      setResult(data);
      setState({ phase: "done", result: data });
    } catch (err) {
      setState({
        phase: "error",
        message: err instanceof Error ? err.message : "Something went wrong.",
      });
    }
  }

  const isBusy = state.phase === "uploading" || state.phase === "processing";

  function resultToChatContext(r: AnalysisResult): ChatContext {
    return {
      angles: r.angles,
      tips: r.tips,
      key_frames: r.key_frames.map((kf) => ({ label: kf.label, angles: kf.angles })),
    };
  }

  return (
    <main className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-lg mx-auto space-y-8">
        <header className="text-center space-y-1">
          <h1 className="text-3xl font-bold text-gray-900">CourtCoach</h1>
          <p className="text-gray-500 text-sm">Upload a forehand swing video to get AI coaching</p>
        </header>

        <VideoUploader onFileSelect={handleFileSelect} disabled={isBusy} />

        <AnalysisStatus state={state} logs={logs} />

        {result && (
          <>
            {result.key_frames.length > 0 && (
              <KeyFramePanel frames={result.key_frames} />
            )}
            <section aria-label="Coaching tips" className="space-y-3">
              {result.tips.map((tip, i) => (
                <CoachingCard key={i} tip={tip} />
              ))}
            </section>
            <ChatSidebar context={resultToChatContext(result)} />
          </>
        )}
      </div>
    </main>
  );
}

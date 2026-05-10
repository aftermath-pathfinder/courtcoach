import type { AnalysisResult, ApiError } from "../types/analysis";

const BASE_URL = "/api";

export async function analyzeSwing(file: File): Promise<AnalysisResult> {
  const body = new FormData();
  body.append("video", file);

  const response = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      status: "error",
      message: `Request failed with status ${response.status}`,
    }));
    throw new Error(error.message);
  }

  const data: AnalysisResult = await response.json();
  return data;
}

export async function analyzeSwingStream(
  file: File,
  onProgress: (message: string) => void
): Promise<AnalysisResult> {
  const body = new FormData();
  body.append("video", file);

  const response = await fetch(`${BASE_URL}/analyze/stream`, {
    method: "POST",
    body,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: AnalysisResult | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      if (!part.startsWith("data: ")) continue;
      const payload = JSON.parse(part.slice(6)) as {
        stage: string;
        message: string;
        data?: AnalysisResult;
      };

      if (payload.stage === "error") throw new Error(payload.message);
      onProgress(payload.message);
      if (payload.stage === "done" && payload.data) result = payload.data;
    }
  }

  if (!result) throw new Error("No result received from server.");
  return result;
}

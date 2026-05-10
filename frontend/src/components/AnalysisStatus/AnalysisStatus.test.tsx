import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { AnalysisStatus } from "./AnalysisStatus";
import type { AnalysisState } from "../../types/analysis";

const doneResult: AnalysisState = {
  phase: "done",
  result: {
    status: "success",
    processing_time_seconds: 14.3,
    keypoints_extracted: 42,
    angles: {
      elbow_angle: 162.4,
      shoulder_rotation: 87.1,
      knee_flex: 28.6,
      hip_turn: 76.3,
      follow_through: 195.2,
    },
    tips: [],
    key_frames: [],
  },
};

describe("AnalysisStatus", () => {
  it("renders nothing in idle state", () => {
    const { container } = render(<AnalysisStatus state={{ phase: "idle" }} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows uploading message", () => {
    render(<AnalysisStatus state={{ phase: "uploading" }} />);
    expect(screen.getByRole("status")).toHaveTextContent(/uploading/i);
  });

  it("shows processing message with expected wait time", () => {
    render(<AnalysisStatus state={{ phase: "processing" }} />);
    expect(screen.getByRole("status")).toHaveTextContent(/analysing/i);
    expect(screen.getByRole("status")).toHaveTextContent(/10.20 seconds/i);
  });

  it("shows completion message with elapsed time", () => {
    render(<AnalysisStatus state={doneResult} />);
    expect(screen.getByRole("status")).toHaveTextContent(/14.3s/);
  });

  it("shows error message as alert", () => {
    render(<AnalysisStatus state={{ phase: "error", message: "Pose estimation failed." }} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/pose estimation failed/i);
  });
});

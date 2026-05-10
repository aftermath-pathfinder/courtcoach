import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { KeyFramePanel } from "./KeyFramePanel";
import type { KeyFrame } from "../../types/analysis";

const RAW_B64 = "cmF3";       // base64 for "raw"
const ANNOTATED_B64 = "YW5u"; // base64 for "ann"

const makeFrame = (label: KeyFrame["label"]): KeyFrame => ({
  label,
  angles: {
    elbow_angle: 165.0,
    shoulder_rotation: 90.0,
    knee_flex: 28.0,
    hip_turn: 80.0,
    follow_through: 195.0,
  },
  image_b64: RAW_B64,
  annotated_image_b64: ANNOTATED_B64,
});

const FRAMES: KeyFrame[] = [
  makeFrame("contact"),
  makeFrame("windup"),
  makeFrame("follow_through"),
];

describe("KeyFramePanel", () => {
  it("renders human-readable labels for all frames", () => {
    render(<KeyFramePanel frames={FRAMES} />);
    expect(screen.getByText("Contact Point")).toBeInTheDocument();
    expect(screen.getByText("Wind-up")).toBeInTheDocument();
    expect(screen.getByText("Follow-Through")).toBeInTheDocument();
  });

  it("sets img src to raw base64 by default", () => {
    render(<KeyFramePanel frames={[makeFrame("contact")]} />);
    const img = screen.getByAltText("Contact Point") as HTMLImageElement;
    expect(img.src).toContain(RAW_B64);
  });

  it("toggles to annotated image when overlay button is clicked", () => {
    render(<KeyFramePanel frames={[makeFrame("contact")]} />);
    const btn = screen.getByLabelText("Show overlay for Contact Point");
    fireEvent.click(btn);
    const img = screen.getByAltText("Contact Point") as HTMLImageElement;
    expect(img.src).toContain(ANNOTATED_B64);
    expect(screen.getByLabelText("Hide overlay for Contact Point")).toBeInTheDocument();
  });

  it("renders nothing when frames array is empty", () => {
    const { container } = render(<KeyFramePanel frames={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});

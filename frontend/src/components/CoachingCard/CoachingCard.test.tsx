import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { CoachingCard } from "./CoachingCard";
import type { CoachingTip } from "../../types/analysis";

const makeTip = (overrides: Partial<CoachingTip> = {}): CoachingTip => ({
  angle_name: "elbow_angle",
  severity: "warning",
  observation: "Keep your elbow near-straight at contact.",
  drill: "Shadow swing drill: freeze at contact and check elbow extension. 3 sets of 10.",
  ...overrides,
});

describe("CoachingCard", () => {
  it("renders the observation text", () => {
    render(<CoachingCard tip={makeTip()} />);
    expect(screen.getByText("Keep your elbow near-straight at contact.")).toBeInTheDocument();
  });

  it("renders the drill text with Drill prefix", () => {
    render(<CoachingCard tip={makeTip()} />);
    expect(screen.getByText(/Shadow swing drill/)).toBeInTheDocument();
    expect(screen.getByText("Drill:")).toBeInTheDocument();
  });

  it("renders a good severity badge in green", () => {
    render(<CoachingCard tip={makeTip({ severity: "good" })} />);
    const badge = screen.getByLabelText("Severity: good");
    expect(badge).toHaveTextContent("Good");
    expect(badge.className).toContain("bg-green-100");
  });

  it("renders a warning severity badge in amber", () => {
    render(<CoachingCard tip={makeTip({ severity: "warning" })} />);
    const badge = screen.getByLabelText("Severity: warning");
    expect(badge).toHaveTextContent("Warning");
    expect(badge.className).toContain("bg-amber-100");
  });

  it("renders a critical severity badge in red", () => {
    render(<CoachingCard tip={makeTip({ severity: "critical" })} />);
    const badge = screen.getByLabelText("Severity: critical");
    expect(badge).toHaveTextContent("Critical");
    expect(badge.className).toContain("bg-red-100");
  });

  it("renders the angle name as a readable label", () => {
    render(<CoachingCard tip={makeTip({ angle_name: "shoulder_rotation" })} />);
    expect(screen.getByText("shoulder rotation")).toBeInTheDocument();
  });
});

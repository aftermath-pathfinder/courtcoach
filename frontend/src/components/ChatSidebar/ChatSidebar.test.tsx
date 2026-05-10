import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ChatSidebar } from "./ChatSidebar";
import * as client from "../../api/client";
import type { ChatContext } from "../../types/analysis";

vi.mock("../../api/client", () => ({
  sendChatMessage: vi.fn(),
}));

const mockSend = vi.mocked(client.sendChatMessage);

const CONTEXT: ChatContext = {
  angles: {
    elbow_angle: 147,
    shoulder_rotation: 88,
    knee_flex: 28,
    hip_turn: 80,
    follow_through: 177,
  },
  tips: [],
  key_frames: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  Element.prototype.scrollIntoView = vi.fn();
});

describe("ChatSidebar", () => {
  it("renders empty state prompt", () => {
    render(<ChatSidebar context={CONTEXT} />);
    expect(screen.getByText(/Ask anything about your swing/i)).toBeInTheDocument();
  });

  it("sends message and displays reply", async () => {
    mockSend.mockResolvedValueOnce("Great question! Focus on extending your arm.");

    render(<ChatSidebar context={CONTEXT} />);

    const input = screen.getByLabelText("Message input");
    fireEvent.change(input, { target: { value: "Why is my elbow bent?" } });
    fireEvent.click(screen.getByLabelText("Send message"));

    expect(await screen.findByText("Why is my elbow bent?")).toBeInTheDocument();
    expect(await screen.findByText("Great question! Focus on extending your arm.")).toBeInTheDocument();
  });

  it("disables send button when input is empty", () => {
    render(<ChatSidebar context={null} />);
    expect(screen.getByLabelText("Send message")).toBeDisabled();
  });

  it("shows error message when API call fails", async () => {
    mockSend.mockRejectedValueOnce(new Error("network"));

    render(<ChatSidebar context={CONTEXT} />);
    const input = screen.getByLabelText("Message input");
    fireEvent.change(input, { target: { value: "Hello?" } });
    fireEvent.click(screen.getByLabelText("Send message"));

    await waitFor(() => {
      expect(screen.getByText(/Couldn't reach the coach/i)).toBeInTheDocument();
    });
  });

  it("submits on Enter key", async () => {
    mockSend.mockResolvedValueOnce("reply");

    render(<ChatSidebar context={CONTEXT} />);
    const input = screen.getByLabelText("Message input");
    fireEvent.change(input, { target: { value: "test message" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: false });

    await waitFor(() => {
      expect(mockSend).toHaveBeenCalledOnce();
    });
  });

  it("does not submit on Shift+Enter", () => {
    render(<ChatSidebar context={CONTEXT} />);
    const input = screen.getByLabelText("Message input");
    fireEvent.change(input, { target: { value: "test" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
    expect(mockSend).not.toHaveBeenCalled();
  });
});

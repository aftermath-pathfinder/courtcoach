import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { VideoUploader } from "./VideoUploader";

function makeFile(name: string, type: string, sizeBytes: number): File {
  return new File([new ArrayBuffer(sizeBytes)], name, { type });
}

describe("VideoUploader", () => {
  it("renders the upload area", () => {
    render(<VideoUploader onFileSelect={vi.fn()} />);
    expect(screen.getByRole("button", { name: /upload video/i })).toBeInTheDocument();
    expect(screen.getByText(/mp4 or mov/i)).toBeInTheDocument();
  });

  it("calls onFileSelect with a valid MP4 file", async () => {
    const onFileSelect = vi.fn();
    render(<VideoUploader onFileSelect={onFileSelect} />);

    const file = makeFile("swing.mp4", "video/mp4", 1024);
    const input = screen.getByTestId("file-input");
    await userEvent.upload(input, file);

    expect(onFileSelect).toHaveBeenCalledOnce();
    expect(onFileSelect).toHaveBeenCalledWith(file);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("calls onFileSelect with a valid MOV file", async () => {
    const onFileSelect = vi.fn();
    render(<VideoUploader onFileSelect={onFileSelect} />);

    const file = makeFile("swing.mov", "video/quicktime", 1024);
    const input = screen.getByTestId("file-input");
    await userEvent.upload(input, file);

    expect(onFileSelect).toHaveBeenCalledOnce();
  });

  it("rejects a file over 100 MB", async () => {
    const onFileSelect = vi.fn();
    render(<VideoUploader onFileSelect={onFileSelect} />);

    const oversized = makeFile("big.mp4", "video/mp4", 101 * 1024 * 1024);
    const input = screen.getByTestId("file-input");
    await userEvent.upload(input, oversized);

    expect(onFileSelect).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/100 MB/i);
  });

  it("rejects an unsupported file type", async () => {
    const onFileSelect = vi.fn();
    render(<VideoUploader onFileSelect={onFileSelect} />);

    const bad = makeFile("clip.avi", "video/avi", 1024);
    const input = screen.getByTestId("file-input");
    // applyAccept: false bypasses the <input accept> filter so our JS validation runs
    await userEvent.upload(input, bad, { applyAccept: false });

    expect(onFileSelect).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/mp4 and mov/i);
  });

  it("is non-interactive when disabled", () => {
    render(<VideoUploader onFileSelect={vi.fn()} disabled />);
    const button = screen.getByRole("button", { name: /upload video/i });
    expect(button).toHaveAttribute("aria-disabled", "true");
    expect(button).toHaveAttribute("tabindex", "-1");
  });

  it("shows drag-over style on dragover and clears on dragleave", () => {
    render(<VideoUploader onFileSelect={vi.fn()} />);
    const button = screen.getByRole("button", { name: /upload video/i });
    fireEvent.dragOver(button);
    expect(button.className).toMatch(/border-blue-500/);
    fireEvent.dragLeave(button);
    expect(button.className).not.toMatch(/border-blue-500/);
  });
});

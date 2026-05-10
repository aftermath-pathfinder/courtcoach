import { useRef, useState } from "react";

const MAX_BYTES = 100 * 1024 * 1024; // 100 MB
const ACCEPTED = ["video/mp4", "video/quicktime"];

interface Props {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export function VideoUploader({ onFileSelect, disabled = false }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function validate(file: File): string | null {
    if (!ACCEPTED.includes(file.type)) return "Only MP4 and MOV files are supported.";
    if (file.size > MAX_BYTES) return "File exceeds the 100 MB limit.";
    return null;
  }

  function handleFile(file: File) {
    const msg = validate(file);
    if (msg) {
      setError(msg);
      return;
    }
    setError(null);
    onFileSelect(file);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Upload video"
        aria-disabled={disabled}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && !disabled && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={[
          "w-full max-w-md rounded-xl border-2 border-dashed px-8 py-12 text-center transition-colors",
          dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-white",
          disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer hover:border-blue-400",
        ].join(" ")}
      >
        <p className="text-gray-600 text-sm">
          Drag and drop your swing video here, or{" "}
          <span className="text-blue-600 font-medium">browse</span>
        </p>
        <p className="text-gray-400 text-xs mt-1">MP4 or MOV · max 100 MB</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="video/mp4,video/quicktime"
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
        data-testid="file-input"
      />

      {error && (
        <p role="alert" className="text-red-600 text-sm">
          {error}
        </p>
      )}
    </div>
  );
}

import { useRef, useState } from "react";
import { Upload, Camera, X } from "lucide-react";
import { scannerApi } from "../services/api.js";

const STAGE_MESSAGES = [
  "Uploading image…",
  "Detecting text on spines…",
  "Matching against the catalog…",
  "Wrapping up…",
];

export default function ScannerUploader({ onResult }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [stageIndex, setStageIndex] = useState(0);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);
  const stageTimerRef = useRef(null);

  function handleFileChange(e) {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    setError(null);
  }

  function clearFile() {
    setFile(null);
    setPreviewUrl(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  async function handleScan() {
    if (!file) return;
    setIsScanning(true);
    setError(null);
    setStageIndex(0);

    stageTimerRef.current = setInterval(() => {
      setStageIndex((i) => Math.min(i + 1, STAGE_MESSAGES.length - 1));
    }, 1500);

    try {
      const res = await scannerApi.upload(file);
      onResult(res.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Something went wrong scanning your shelf. Please try again."
      );
    } finally {
      clearInterval(stageTimerRef.current);
      setIsScanning(false);
    }
  }

  return (
    <div className="catalog-card p-6">
      {!previewUrl && (
        <label className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed border-parchment-ink/20 py-16 text-center hover:border-brass/50">
          <Upload className="h-8 w-8 text-parchment-ink/40" strokeWidth={1.5} />
          <span className="text-sm text-parchment-ink/60">
            Click to upload a bookshelf photo
          </span>
          <span className="text-xs text-parchment-ink/40">JPEG, PNG, or WEBP — up to 8MB</span>
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={handleFileChange}
          />
        </label>
      )}

      {previewUrl && (
        <div>
          <div className="relative overflow-hidden rounded-lg">
            <img
              src={previewUrl}
              alt="Bookshelf preview"
              className="max-h-80 w-full bg-parchment-ink/5 object-contain"
            />
            {!isScanning && (
              <button
                onClick={clearFile}
                className="absolute right-2 top-2 rounded-full bg-ink/80 p-1.5 text-parchment hover:bg-ink"
                aria-label="Remove image"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <div className="mt-4 flex items-center justify-between gap-4">
            {isScanning ? (
              <p className="flex items-center gap-2 text-sm text-parchment-ink/60">
                <Camera className="h-4 w-4 animate-pulse" strokeWidth={1.5} />
                {STAGE_MESSAGES[stageIndex]}
              </p>
            ) : (
              <button onClick={handleScan} className="brass-btn">
                Scan My Shelf
              </button>
            )}
          </div>
        </div>
      )}

      {error && <p className="mt-3 text-sm text-brass-dark">{error}</p>}
    </div>
  );
}

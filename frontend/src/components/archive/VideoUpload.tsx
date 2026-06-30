"use client";

import { useCallback, useRef, useState } from "react";
import { Button } from "@/components/Button";
import { UploadState } from "@/lib/useVideoProcessing";

interface VideoUploadProps {
  uploadState: UploadState;
  uploadProgress: number;
  fileName: string | null;
  fileSize: number | null;
  error: string | null;
  onUpload: (file: File) => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

const ACCEPTED_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/avi"];
const ACCEPTED_EXTENSIONS = ".mp4,.mov,.avi";

export default function VideoUpload({
  uploadState,
  uploadProgress,
  fileName,
  fileSize,
  error,
  onUpload,
}: VideoUploadProps) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    if (!ACCEPTED_TYPES.includes(file.type) && !file.name.match(/\.(mp4|mov|avi)$/i)) {
      return;
    }
    setSelectedFile(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleUpload = useCallback(() => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  }, [selectedFile, onUpload]);

  const isUploading = uploadState === "uploading";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <div
        className={`relative border-2 border-dashed rounded-lg p-12 text-center transition-all duration-200 ${
          dragOver
            ? "border-primary-400 bg-primary-50 scale-[1.01]"
            : "border-gray-300 hover:border-gray-400"
        } ${isUploading ? "pointer-events-none opacity-60" : "cursor-pointer"}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !isUploading && inputRef.current?.click()}
      >
        {/* Film/Camera Icon */}
        <div className="mx-auto w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
          <svg
            className="w-8 h-8 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
            />
          </svg>
        </div>

        <p className="text-base font-medium text-gray-700">
          Drop your archive video here
        </p>
        <p className="mt-1 text-sm text-gray-500">
          or click to browse your files
        </p>
        <p className="mt-2 text-xs text-gray-400">
          Supports MP4, MOV, AVI — up to 2GB
        </p>

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          onChange={handleInputChange}
          className="hidden"
        />
      </div>

      {/* Selected file info */}
      {selectedFile && uploadState === "idle" && (
        <div className="mt-4 flex items-center justify-between bg-gray-50 rounded-lg px-4 py-3">
          <div className="flex items-center gap-3">
            <svg
              className="w-5 h-5 text-primary-500"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h1.5C5.496 19.5 6 18.996 6 18.375m-2.625 0V6.375c0-.621.504-1.125 1.125-1.125h17.25c.621 0 1.125.504 1.125 1.125v12c0 .621-.504 1.125-1.125 1.125m-17.25 0h1.5m14.25 0h1.5"
              />
            </svg>
            <div>
              <p className="text-sm font-medium text-gray-900">
                {selectedFile.name}
              </p>
              <p className="text-xs text-gray-500">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
          </div>
          <Button onClick={handleUpload}>Upload & Process</Button>
        </div>
      )}

      {/* Upload progress */}
      {isUploading && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <svg
                className="w-4 h-4 text-primary-500 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              <span className="text-sm text-gray-700">
                Uploading {fileName}...
              </span>
            </div>
            <span className="text-sm font-medium text-primary-600">
              {uploadProgress}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          {fileSize && (
            <p className="mt-1 text-xs text-gray-500">
              {formatFileSize(fileSize)}
            </p>
          )}
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="mt-4 flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          <svg
            className="w-5 h-5 text-red-500 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z"
            />
          </svg>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
}

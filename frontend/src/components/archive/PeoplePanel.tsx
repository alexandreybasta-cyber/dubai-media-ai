"use client";

import { useState } from "react";
import { DetectedFace } from "@/lib/useVideoProcessing";

interface PeoplePanelProps {
  faces: DetectedFace[];
  duration: number;
  onSeek: (time: number) => void;
  onRename: (
    faceIndex: number,
    data: { name_en: string; name_ar?: string; role?: string; add_to_reference?: boolean }
  ) => Promise<unknown>;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const SOURCE_LABELS: Record<string, { label: string; className: string }> = {
  reference_db: { label: "AI match", className: "bg-blue-50 text-blue-700" },
  ocr: { label: "On-screen text", className: "bg-teal-50 text-teal-700" },
  transcript: { label: "Spoken intro", className: "bg-indigo-50 text-indigo-700" },
  ai_suggestion: { label: "AI suggestion — verify", className: "bg-amber-50 text-amber-700" },
  manual: { label: "Named by you", className: "bg-green-50 text-green-700" },
};

function NameEditor({
  face,
  onCancel,
  onSave,
}: {
  face: DetectedFace;
  onCancel: () => void;
  onSave: (data: { name_en: string; name_ar?: string; role?: string; add_to_reference?: boolean }) => Promise<void>;
}) {
  const [nameEn, setNameEn] = useState(face.identified ? face.name : "");
  const [role, setRole] = useState(face.role || "");
  const [addToReference, setAddToReference] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    if (!nameEn.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await onSave({
        name_en: nameEn.trim(),
        role: role.trim() || undefined,
        add_to_reference: addToReference,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save name");
      setSaving(false);
    }
  };

  return (
    <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-2">
      <input
        type="text"
        value={nameEn}
        onChange={(e) => setNameEn(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSave()}
        placeholder="Person's name"
        autoFocus
        className="w-full px-2.5 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      />
      <input
        type="text"
        value={role}
        onChange={(e) => setRole(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSave()}
        placeholder="Role / title (optional)"
        className="w-full px-2.5 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      />
      <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
        <input
          type="checkbox"
          checked={addToReference}
          onChange={(e) => setAddToReference(e.target.checked)}
          className="rounded border-gray-300 text-primary-500 focus:ring-primary-500"
        />
        Remember this person for future videos
      </label>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex gap-2 pt-1">
        <button
          onClick={handleSave}
          disabled={saving || !nameEn.trim()}
          className="px-3 py-1.5 text-xs font-medium text-white bg-primary-500 hover:bg-primary-600 disabled:opacity-50 rounded-md transition-colors"
        >
          {saving ? "Saving…" : "Save"}
        </button>
        <button
          onClick={onCancel}
          disabled={saving}
          className="px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

export default function PeoplePanel({ faces, duration, onSeek, onRename }: PeoplePanelProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [savedIndex, setSavedIndex] = useState<number | null>(null);

  if (!faces || faces.length === 0) return null;

  const identifiedCount = faces.filter((f) => f.identified).length;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
        <svg className="w-5 h-5 text-primary-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
        </svg>
        <h3 className="text-sm font-semibold text-gray-900">People</h3>
        <span className="ml-auto text-xs text-gray-500">
          {identifiedCount}/{faces.length} identified
        </span>
      </div>

      <div className="p-4 space-y-3 max-h-[420px] overflow-y-auto">
        {faces.map((face) => {
          const source = face.source ? SOURCE_LABELS[face.source] : undefined;
          const isEditing = editingIndex === face.index;

          return (
            <div
              key={face.index}
              className="p-3 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
            >
              <div className="flex items-start gap-3">
                {/* Avatar dot */}
                <div
                  className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-semibold"
                  style={{ backgroundColor: face.color || "#9CA3AF" }}
                >
                  {(face.identified ? face.name : "?").charAt(0).toUpperCase()}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className={`text-sm font-medium truncate ${face.identified ? "text-gray-900" : "text-gray-500 italic"}`}>
                      {face.name}
                    </p>
                    {face.name_ar && (
                      <span className="text-xs text-gray-400" dir="rtl">{face.name_ar}</span>
                    )}
                    {source && (
                      <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${source.className}`}>
                        {source.label}
                      </span>
                    )}
                    {face.identified && typeof face.confidence === "number" && face.source !== "manual" && (
                      <span className="text-[10px] text-gray-400">
                        {Math.round(face.confidence * 100)}% confidence
                      </span>
                    )}
                  </div>
                  {face.role && (
                    <p className="text-xs text-gray-500 mt-0.5 truncate">{face.role}</p>
                  )}
                  {!face.identified && face.description && (
                    <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{face.description}</p>
                  )}

                  {/* Appearance chips */}
                  {face.appearances.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {face.appearances.map((app, j) => (
                        <button
                          key={j}
                          onClick={() => onSeek(app.start)}
                          className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 hover:bg-primary-50 hover:text-primary-700 transition-colors"
                          title={`Jump to ${formatTime(app.start)}`}
                        >
                          {formatTime(app.start)}–{formatTime(Math.min(app.end, duration || app.end))}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <button
                  onClick={() => setEditingIndex(isEditing ? null : face.index)}
                  className={`flex-shrink-0 text-xs font-medium px-2.5 py-1.5 rounded-md transition-colors ${
                    face.identified
                      ? "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                      : "text-primary-600 bg-primary-50 hover:bg-primary-100"
                  }`}
                >
                  {face.identified ? "Edit" : "Name person"}
                </button>
              </div>

              {isEditing && (
                <NameEditor
                  face={face}
                  onCancel={() => setEditingIndex(null)}
                  onSave={async (data) => {
                    await onRename(face.index, data);
                    setEditingIndex(null);
                    setSavedIndex(face.index);
                    setTimeout(() => setSavedIndex(null), 2500);
                  }}
                />
              )}
              {savedIndex === face.index && !isEditing && (
                <p className="mt-2 text-xs text-green-600">✓ Saved</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

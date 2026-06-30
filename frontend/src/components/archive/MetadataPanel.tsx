"use client";

import { useState, useCallback } from "react";
import { VideoMetadata } from "@/lib/useVideoProcessing";

interface MetadataPanelProps {
  metadata: VideoMetadata | null;
}

type Tab = "summary" | "ebucore" | "iptc" | "raw";

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m ${s}s`;
  return `${m}m ${s}s`;
}

function JsonTree({ data, depth = 0 }: { data: unknown; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 2);

  if (data === null || data === undefined) {
    return <span className="text-gray-400">null</span>;
  }

  if (typeof data === "string") {
    return <span className="text-green-400">&quot;{data}&quot;</span>;
  }

  if (typeof data === "number" || typeof data === "boolean") {
    return <span className="text-blue-400">{String(data)}</span>;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-gray-400">[]</span>;
    return (
      <div className="ml-4">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-400 hover:text-gray-200 text-xs"
        >
          {expanded ? "▼" : "▶"} Array[{data.length}]
        </button>
        {expanded && (
          <div className="ml-2 border-l border-gray-700 pl-2">
            {data.map((item, i) => (
              <div key={i} className="my-0.5">
                <span className="text-gray-500 text-xs">{i}: </span>
                <JsonTree data={item} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (typeof data === "object") {
    const entries = Object.entries(data as Record<string, unknown>);
    if (entries.length === 0) return <span className="text-gray-400">{"{}"}</span>;
    return (
      <div className="ml-4">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-400 hover:text-gray-200 text-xs"
        >
          {expanded ? "▼" : "▶"} Object{`{${entries.length}}`}
        </button>
        {expanded && (
          <div className="ml-2 border-l border-gray-700 pl-2">
            {entries.map(([key, value]) => (
              <div key={key} className="my-0.5">
                <span className="text-purple-400 text-xs">{key}: </span>
                <JsonTree data={value} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return <span className="text-gray-400">{String(data)}</span>;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
    >
      {copied ? (
        <>
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
          </svg>
          Copied
        </>
      ) : (
        <>
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9.75a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184" />
          </svg>
          Copy
        </>
      )}
    </button>
  );
}

function DownloadButton({ content, filename, label }: { content: string; filename: string; label: string }) {
  const handleDownload = useCallback(() => {
    const blob = new Blob([content], { type: "application/xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }, [content, filename]);

  return (
    <button
      onClick={handleDownload}
      className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
    >
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
      </svg>
      {label}
    </button>
  );
}

// ─── Summary Tab ──────────────────────────────────────────────────────

function SummaryTab({ metadata }: { metadata: VideoMetadata }) {
  return (
    <div className="space-y-4">
      {/* Key-value pairs */}
      <div className="grid grid-cols-2 gap-3">
        {metadata.topic && (
          <div>
            <p className="text-xs text-gray-500">Topic</p>
            <p className="text-sm font-medium text-gray-900">{metadata.topic}</p>
          </div>
        )}
        {metadata.sentiment && (
          <div>
            <p className="text-xs text-gray-500">Sentiment</p>
            <p className="text-sm font-medium text-gray-900">{metadata.sentiment}</p>
          </div>
        )}
        {metadata.era && (
          <div>
            <p className="text-xs text-gray-500">Era</p>
            <p className="text-sm font-medium text-gray-900">{metadata.era}</p>
          </div>
        )}
        {metadata.duration > 0 && (
          <div>
            <p className="text-xs text-gray-500">Duration</p>
            <p className="text-sm font-medium text-gray-900">
              {formatDuration(metadata.duration)}
            </p>
          </div>
        )}
      </div>

      {/* Detected Persons */}
      {metadata.faces && metadata.faces.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Detected Persons</p>
          <div className="flex flex-wrap gap-2">
            {metadata.faces.map((face, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700"
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: face.color }}
                />
                <span>{face.name || "Unknown"}</span>
                {face.name_ar && (
                  <span className="text-gray-400" dir="rtl">
                    ({face.name_ar})
                  </span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Landmarks */}
      {metadata.landmarks && metadata.landmarks.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Detected Landmarks</p>
          <div className="flex flex-wrap gap-2">
            {metadata.landmarks.map((lm, i) => (
              <span
                key={i}
                className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700"
              >
                📍 {lm.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Sensitive Content */}
      {metadata.sensitive_content && metadata.sensitive_content.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Sensitive Content Flags</p>
          <div className="flex flex-wrap gap-2">
            {metadata.sensitive_content.map((flag, i) => (
              <span
                key={i}
                className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-red-50 text-red-700"
              >
                ⚠️ {flag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Scenes count */}
      {metadata.scenes && metadata.scenes.length > 0 && (
        <div>
          <p className="text-xs text-gray-500">Scenes Detected</p>
          <p className="text-sm font-medium text-gray-900">
            {metadata.scenes.length} scenes
          </p>
        </div>
      )}
    </div>
  );
}

// ─── EBUCore Tab ──────────────────────────────────────────────────────

function EBUCoreTab({ xml }: { xml: string }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <CopyButton text={xml} />
        <DownloadButton content={xml} filename="ebucore_metadata.xml" label="Download XML" />
      </div>
      <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto max-h-[400px] overflow-y-auto">
        <pre className="text-xs text-gray-200 font-mono whitespace-pre-wrap">
          {xml}
        </pre>
      </div>
    </div>
  );
}

// ─── IPTC Tab ─────────────────────────────────────────────────────────

function IPTCTab({ data }: { data: Record<string, unknown> }) {
  const jsonStr = JSON.stringify(data, null, 2);
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <CopyButton text={jsonStr} />
      </div>
      <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto max-h-[400px] overflow-y-auto">
        <JsonTree data={data} />
      </div>
    </div>
  );
}

// ─── Raw Tab ──────────────────────────────────────────────────────────

function RawTab({ data }: { data: Record<string, unknown> }) {
  const jsonStr = JSON.stringify(data, null, 2);
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <CopyButton text={jsonStr} />
      </div>
      <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto max-h-[400px] overflow-y-auto">
        <JsonTree data={data} />
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────

export default function MetadataPanel({ metadata }: MetadataPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("summary");

  if (!metadata) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm h-full flex items-center justify-center">
        <div className="text-center">
          <svg
            className="w-10 h-10 text-gray-300 mx-auto mb-2"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
            />
          </svg>
          <p className="text-sm text-gray-500">Metadata will appear here</p>
          <p className="text-xs text-gray-400 mt-1">
            After processing completes
          </p>
        </div>
      </div>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "summary", label: "Summary" },
    { id: "ebucore", label: "EBUCore" },
    { id: "iptc", label: "IPTC" },
    { id: "raw", label: "Raw JSON" },
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col h-full">
      {/* Tabs */}
      <div className="border-b border-gray-200 px-4">
        <div className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 p-4 overflow-y-auto">
        {activeTab === "summary" && <SummaryTab metadata={metadata} />}
        {activeTab === "ebucore" && (
          <EBUCoreTab xml={metadata.ebucore_xml || "<!-- No EBUCore data available -->"} />
        )}
        {activeTab === "iptc" && (
          <IPTCTab data={metadata.iptc_json || {}} />
        )}
        {activeTab === "raw" && (
          <RawTab data={(metadata.raw || metadata) as Record<string, unknown>} />
        )}
      </div>
    </div>
  );
}

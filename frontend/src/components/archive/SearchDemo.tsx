"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/Button";
import { SearchResult } from "@/lib/useVideoProcessing";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Convert a raw thumbnail path (filesystem or relative) to a browser-accessible URL.
 * Handles formats: "./uploads/...", "uploads/...", "/uploads/..."
 */
function resolveThumbnailUrl(raw: string | undefined): string | undefined {
  if (!raw) return undefined;
  // Already a full URL
  if (raw.startsWith("http://") || raw.startsWith("https://")) return raw;
  // Strip leading "./" or ensure leading "/"
  let path = raw.replace(/^\.?\//, "/");
  if (!path.startsWith("/")) path = "/" + path;
  return `${API_BASE_URL}${path}`;
}

interface SearchDemoProps {
  searchResults: SearchResult[];
  isSearching: boolean;
  searchQuery: string;
  onSearch: (query: string) => void;
  onResultClick?: (result: SearchResult) => void;
}

function formatTimestamp(value: unknown): string {
  // Handle string timestamps (e.g., "00:15", "1:30", "01:02:03")
  if (typeof value === "string") {
    if (/^\d{1,2}(:\d{2}){1,2}$/.test(value)) {
      return value;
    }
    // Try parsing as a number string
    const parsed = parseFloat(value);
    if (!isNaN(parsed)) {
      const m = Math.floor(parsed / 60);
      const s = Math.floor(parsed % 60);
      return `${m}:${s.toString().padStart(2, "0")}`;
    }
    return "0:00";
  }
  // Handle numeric seconds
  if (typeof value === "number" && !isNaN(value)) {
    const m = Math.floor(value / 60);
    const s = Math.floor(value % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  }
  // Fallback for NaN, undefined, null, etc.
  return "0:00";
}

export default function SearchDemo({
  searchResults,
  isSearching,
  searchQuery,
  onSearch,
  onResultClick,
}: SearchDemoProps) {
  const [query, setQuery] = useState(searchQuery);

  const handleSearch = useCallback(() => {
    if (query.trim()) {
      onSearch(query.trim());
    }
  }, [query, onSearch]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        handleSearch();
      }
    },
    [handleSearch]
  );

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
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
            d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
          />
        </svg>
        <h2 className="text-lg font-semibold text-gray-900">
          Semantic Search
        </h2>
      </div>

      {/* Search input */}
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <svg
            className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
            />
          </svg>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search archive... e.g., 'sunset over Dubai Marina with no people'"
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-shadow"
          />
        </div>
        <Button onClick={handleSearch} disabled={isSearching || !query.trim()}>
          {isSearching ? (
            <span className="flex items-center gap-2">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Searching
            </span>
          ) : (
            "Search"
          )}
        </Button>
      </div>

      {/* Results */}
      {searchResults.length > 0 && (
        <div className="mt-4 space-y-3">
          <p className="text-xs text-gray-500">
            {searchResults.length} result{searchResults.length !== 1 ? "s" : ""} found
          </p>
          {searchResults.map((result, index) => (
            <div
              key={index}
              className="flex gap-4 p-3 rounded-lg border border-gray-100 hover:border-primary-200 hover:bg-primary-50/30 cursor-pointer transition-all"
              onClick={() => onResultClick?.(result)}
            >
              {/* Thumbnail placeholder */}
              <div className="flex-shrink-0 w-24 h-16 bg-gray-200 rounded overflow-hidden flex items-center justify-center">
                {resolveThumbnailUrl(result.thumbnail) ? (
                  <img
                    src={resolveThumbnailUrl(result.thumbnail)}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <svg
                    className="w-6 h-6 text-gray-400"
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
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {result.title || result.description?.slice(0, 40) || "Untitled"}
                  </p>
                  <span className="text-xs text-gray-400 font-mono flex-shrink-0">
                    @{formatTimestamp(result.timestamp)}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                  {result.description}
                </p>
                {(result as unknown as { persons?: string[] }).persons &&
                  (result as unknown as { persons: string[] }).persons.length > 0 && (
                  <p className="text-xs text-primary-600 mt-1">
                    {(result as unknown as { persons: string[] }).persons.join(", ")}
                  </p>
                )}
              </div>

              {/* Score */}
              <div className="flex-shrink-0 flex items-center">
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-primary-100 text-primary-700">
                  {Math.round(result.score * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {searchResults.length === 0 && !isSearching && searchQuery && (
        <div className="mt-4 text-center py-6">
          <p className="text-sm text-gray-500">
            No results found for &ldquo;{searchQuery}&rdquo;
          </p>
        </div>
      )}

      {/* Initial empty state */}
      {searchResults.length === 0 && !searchQuery && (
        <div className="mt-4 text-center py-6">
          <p className="text-sm text-gray-400">
            Process videos to enable semantic search across your archive
          </p>
        </div>
      )}
    </div>
  );
}

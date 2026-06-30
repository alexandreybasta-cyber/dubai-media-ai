"use client";

import { useState } from "react";
import { ArrowUpTrayIcon, MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";

export default function ArchivePage() {
  const [dragOver, setDragOver] = useState(false);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Archive Metadata</h1>
        <p className="mt-1 text-sm text-gray-500">
          Upload videos to extract metadata, transcripts, and scene descriptions
          using AI
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <div
              className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                dragOver
                  ? "border-primary-400 bg-primary-50"
                  : "border-gray-300 hover:border-gray-400"
              }`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
              }}
            >
              <ArrowUpTrayIcon className="w-12 h-12 text-gray-400 mx-auto" />
              <p className="mt-4 text-sm text-gray-600">
                Drag and drop a video file here, or click to browse
              </p>
              <p className="mt-1 text-xs text-gray-400">
                Supports MP4, MOV, AVI, MKV up to 2GB
              </p>
              <Button className="mt-4">Select Video File</Button>
            </div>
          </Card>

          <Card className="mt-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Search Archive
            </h2>
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search with natural language, e.g. 'aerial shot of Dubai skyline'"
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
              <Button>Search</Button>
            </div>
          </Card>
        </div>

        <div>
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Recent Uploads
            </h2>
            <p className="text-sm text-gray-500 text-center py-8">
              No videos uploaded yet. Upload a video to get started.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}

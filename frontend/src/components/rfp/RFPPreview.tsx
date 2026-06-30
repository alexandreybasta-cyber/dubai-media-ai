"use client";

import { useState } from "react";
import { ArrowPathIcon, DocumentArrowDownIcon } from "@heroicons/react/24/outline";
import { RFPSection } from "@/lib/api";

interface RFPPreviewProps {
  rfpId: string;
  title: string;
  sections: RFPSection[];
  language: string;
  onRegenerateSection: (sectionName: string, instructions: string) => Promise<void>;
  onExportDocx: () => void;
  onExportPdf: () => void;
  regeneratingSection: string | null;
}

export function RFPPreview({
  rfpId,
  title,
  sections,
  language,
  onRegenerateSection,
  onExportDocx,
  onExportPdf,
  regeneratingSection,
}: RFPPreviewProps) {
  const [activeLanguage, setActiveLanguage] = useState<"en" | "ar">("en");
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [regenerateInstructions, setRegenerateInstructions] = useState("");
  const [showRegenerateFor, setShowRegenerateFor] = useState<string | null>(null);

  const isBilingual = language === "both";

  const getContent = (section: RFPSection) => {
    if (activeLanguage === "ar" && section.content_ar) {
      return section.content_ar;
    }
    return section.content_en || section.content_ar || "";
  };

  const handleRegenerate = async (sectionName: string) => {
    await onRegenerateSection(sectionName, regenerateInstructions);
    setShowRegenerateFor(null);
    setRegenerateInstructions("");
  };

  return (
    <div className="space-y-4">
      {/* Export Bar */}
      <div className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
        <div className="flex items-center gap-3">
          <DocumentArrowDownIcon className="w-5 h-5 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Export</span>
        </div>
        <div className="flex items-center gap-2">
          {isBilingual && (
            <div className="flex items-center bg-white border border-gray-200 rounded-md mr-3">
              <button
                type="button"
                onClick={() => setActiveLanguage("en")}
                className={`px-3 py-1 text-xs font-medium rounded-l-md transition-colors ${
                  activeLanguage === "en"
                    ? "bg-primary-500 text-white"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                EN
              </button>
              <button
                type="button"
                onClick={() => setActiveLanguage("ar")}
                className={`px-3 py-1 text-xs font-medium rounded-r-md transition-colors ${
                  activeLanguage === "ar"
                    ? "bg-primary-500 text-white"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                AR
              </button>
            </div>
          )}
          <button
            type="button"
            onClick={onExportDocx}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            <DocumentArrowDownIcon className="w-4 h-4" />
            DOCX
          </button>
          <button
            type="button"
            onClick={onExportPdf}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            <DocumentArrowDownIcon className="w-4 h-4" />
            PDF
          </button>
        </div>
      </div>

      {/* Document Preview */}
      <div className="border border-gray-300 rounded-lg bg-white shadow-sm">
        {/* Document Header */}
        <div className="border-b border-gray-200 px-8 py-6 text-center">
          <p className="text-xs font-bold text-primary-500 tracking-widest uppercase mb-2">
            Dubai Media Incorporated
          </p>
          <h1 className="text-xl font-bold text-gray-900 mb-1">
            Request for Proposal
          </h1>
          <h2 className="text-lg text-gray-700">{title}</h2>
          <p className="text-xs text-gray-400 mt-2">
            Generated on {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
          </p>
        </div>

        {/* Sections */}
        <div className="divide-y divide-gray-100">
          {sections.map((section, index) => (
            <div key={section.name} className="px-8 py-5 group relative">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-bold text-gray-900">
                  {index + 1}. {section.name}
                </h3>
                <button
                  type="button"
                  onClick={() => {
                    if (showRegenerateFor === section.name) {
                      setShowRegenerateFor(null);
                    } else {
                      setShowRegenerateFor(section.name);
                    }
                  }}
                  disabled={regeneratingSection !== null}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-primary-500 transition-all disabled:opacity-50"
                  title="Regenerate section"
                >
                  <ArrowPathIcon className={`w-4 h-4 ${regeneratingSection === section.name ? "animate-spin" : ""}`} />
                </button>
              </div>

              {/* Regenerate instructions */}
              {showRegenerateFor === section.name && (
                <div className="mb-3 flex gap-2">
                  <input
                    type="text"
                    value={regenerateInstructions}
                    onChange={(e) => setRegenerateInstructions(e.target.value)}
                    placeholder="Optional: instructions for regeneration..."
                    className="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-xs focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleRegenerate(section.name);
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => handleRegenerate(section.name)}
                    disabled={regeneratingSection !== null}
                    className="px-3 py-1.5 text-xs font-medium text-white bg-primary-500 rounded-md hover:bg-primary-600 disabled:opacity-50 transition-colors"
                  >
                    {regeneratingSection === section.name ? "..." : "Regenerate"}
                  </button>
                </div>
              )}

              {regeneratingSection === section.name ? (
                <div className="animate-pulse space-y-2">
                  <div className="h-3 bg-gray-200 rounded w-full"></div>
                  <div className="h-3 bg-gray-200 rounded w-5/6"></div>
                  <div className="h-3 bg-gray-200 rounded w-4/6"></div>
                </div>
              ) : (
                <div
                  className={`text-sm text-gray-700 leading-relaxed whitespace-pre-wrap ${
                    activeLanguage === "ar" ? "text-right direction-rtl" : ""
                  }`}
                  dir={activeLanguage === "ar" ? "rtl" : "ltr"}
                >
                  {getContent(section)}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Document Footer */}
        <div className="border-t border-gray-200 px-8 py-3 text-center">
          <p className="text-xs text-gray-400">
            Dubai Media Incorporated &mdash; Confidential | RFP ID: {rfpId.slice(0, 8)}
          </p>
        </div>
      </div>
    </div>
  );
}

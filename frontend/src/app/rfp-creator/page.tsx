"use client";

import { useState } from "react";
import { RFPForm } from "@/components/rfp/RFPForm";
import { RFPPreview } from "@/components/rfp/RFPPreview";
import { api, RFPCreatePayload, RFPSection, RFPCreateResponse } from "@/lib/api";

export default function RFPCreatorPage() {
  const [rfpId, setRfpId] = useState<string | null>(null);
  const [rfpTitle, setRfpTitle] = useState("");
  const [sections, setSections] = useState<RFPSection[]>([]);
  const [language, setLanguage] = useState("en");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [regeneratingSection, setRegeneratingSection] = useState<string | null>(null);

  const handleGenerate = async (data: RFPCreatePayload) => {
    setIsLoading(true);
    setError(null);
    try {
      const response: RFPCreateResponse = await api.rfp.create(data);
      setRfpId(response.rfp_id);
      setRfpTitle(response.title);
      setSections(response.sections);
      setLanguage(response.language);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to generate RFP";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerateSection = async (sectionName: string, instructions: string) => {
    if (!rfpId) return;
    setRegeneratingSection(sectionName);
    try {
      const response = await api.rfp.regenerateSection({
        rfp_id: rfpId,
        section_name: sectionName,
        instructions: instructions || undefined,
      });
      setSections((prev) =>
        prev.map((s) => {
          if (s.name === sectionName) {
            const content = response.content;
            if (language === "both" && content.includes("---AR---")) {
              const parts = content.split("---AR---");
              return { ...s, content_en: parts[0].trim(), content_ar: parts[1].trim() };
            }
            if (language === "ar") {
              return { ...s, content_ar: content };
            }
            return { ...s, content_en: content };
          }
          return s;
        })
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to regenerate section";
      setError(message);
    } finally {
      setRegeneratingSection(null);
    }
  };

  const handleExportDocx = () => {
    if (rfpId) api.rfp.exportDocx(rfpId);
  };

  const handleExportPdf = () => {
    if (rfpId) api.rfp.exportPdf(rfpId);
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">RFP Creator</h1>
        <p className="mt-1 text-sm text-gray-500">
          Generate professional Request for Proposal documents powered by AI
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 text-red-500 hover:text-red-700 font-medium"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel: Input Form */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 overflow-y-auto max-h-[calc(100vh-180px)]">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Project Details
          </h2>
          <RFPForm onSubmit={handleGenerate} isLoading={isLoading} />
        </div>

        {/* Right Panel: Preview & Export */}
        <div className="overflow-y-auto max-h-[calc(100vh-180px)]">
          {isLoading ? (
            <div className="bg-white rounded-xl border border-gray-200 p-8">
              <div className="flex flex-col items-center justify-center py-12">
                <svg className="animate-spin h-8 w-8 text-primary-500 mb-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <p className="text-sm font-medium text-gray-700">Generating with Qwen...</p>
                <p className="text-xs text-gray-500 mt-1">This may take a minute for all 10 sections</p>
                {/* Skeleton */}
                <div className="w-full mt-8 space-y-4">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="animate-pulse space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                      <div className="h-3 bg-gray-100 rounded w-full"></div>
                      <div className="h-3 bg-gray-100 rounded w-5/6"></div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : rfpId && sections.length > 0 ? (
            <RFPPreview
              rfpId={rfpId}
              title={rfpTitle}
              sections={sections}
              language={language}
              onRegenerateSection={handleRegenerateSection}
              onExportDocx={handleExportDocx}
              onExportPdf={handleExportPdf}
              regeneratingSection={regeneratingSection}
            />
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 p-8">
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-16 h-16 bg-primary-50 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-8 h-8 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <h3 className="text-sm font-medium text-gray-900 mb-1">No RFP Generated Yet</h3>
                <p className="text-xs text-gray-500 max-w-xs">
                  Fill in the project details on the left and click &quot;Generate RFP&quot; to create your professional document.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState, useRef } from "react";
import {
  ArrowUpTrayIcon,
  PlusIcon,
  TrashIcon,
  DocumentTextIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";

export interface Criterion {
  name: string;
  weight: number;
  description: string;
  mandatory: boolean;
}

export interface VendorFileEntry {
  name: string;
  file: File | null;
}

interface EvaluationSetupProps {
  onEvaluate: (data: {
    rfpFile: File;
    vendors: { name: string; file: File }[];
    criteria: Criterion[];
  }) => Promise<void>;
  isEvaluating: boolean;
  progressMessage: string;
}

const PRESET_TEMPLATES: Record<string, Criterion[]> = {
  "Media & Broadcasting": [
    { name: "Technical Capability", weight: 25, description: "AI/ML, video processing, broadcast tech", mandatory: true },
    { name: "Media Industry Experience", weight: 20, description: "Track record in media/broadcasting", mandatory: false },
    { name: "Cost Effectiveness", weight: 20, description: "Pricing, total cost of ownership", mandatory: false },
    { name: "Timeline & Delivery", weight: 15, description: "Realistic schedule and milestones", mandatory: false },
    { name: "Innovation", weight: 10, description: "Novel AI features, IP, R&D", mandatory: false },
    { name: "Compliance & Localization", weight: 10, description: "UAE regulations, Arabic support", mandatory: true },
  ],
  Technology: [
    { name: "Technical Architecture", weight: 30, description: "Solution design, scalability", mandatory: true },
    { name: "Security & Compliance", weight: 20, description: "Data protection, certifications", mandatory: true },
    { name: "Cost", weight: 20, description: "Total cost of ownership", mandatory: false },
    { name: "Team Experience", weight: 15, description: "Qualifications, similar projects", mandatory: false },
    { name: "Support & Maintenance", weight: 15, description: "SLAs, post-deployment support", mandatory: false },
  ],
  General: [
    { name: "Technical Capability", weight: 30, description: "Ability to deliver requirements", mandatory: true },
    { name: "Cost Effectiveness", weight: 25, description: "Value for money", mandatory: false },
    { name: "Timeline", weight: 20, description: "Schedule feasibility", mandatory: false },
    { name: "Team Experience", weight: 15, description: "Team qualifications", mandatory: false },
    { name: "Innovation", weight: 10, description: "Creative approach", mandatory: false },
  ],
};

export function EvaluationSetup({
  onEvaluate,
  isEvaluating,
  progressMessage,
}: EvaluationSetupProps) {
  const [rfpFile, setRfpFile] = useState<File | null>(null);
  const [rfpPreview, setRfpPreview] = useState<string>("");
  const [vendors, setVendors] = useState<VendorFileEntry[]>([
    { name: "Vendor A", file: null },
    { name: "Vendor B", file: null },
  ]);
  const [criteria, setCriteria] = useState<Criterion[]>(
    PRESET_TEMPLATES["Media & Broadcasting"]
  );
  const [error, setError] = useState<string>("");

  const rfpInputRef = useRef<HTMLInputElement>(null);
  const vendorInputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const totalWeight = criteria.reduce((sum, c) => sum + c.weight, 0);

  const handleRfpUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setRfpFile(file);
    // Try to preview first 200 chars (works for text files only)
    try {
      const text = await file.text();
      setRfpPreview(text.substring(0, 200));
    } catch {
      setRfpPreview(`[Binary file: ${file.name}]`);
    }
  };

  const handleVendorFileChange = (
    idx: number,
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setVendors((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], file };
      return next;
    });
  };

  const handleVendorNameChange = (idx: number, name: string) => {
    setVendors((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], name };
      return next;
    });
  };

  const addVendor = () => {
    setVendors((prev) => [
      ...prev,
      { name: `Vendor ${String.fromCharCode(65 + prev.length)}`, file: null },
    ]);
  };

  const removeVendor = (idx: number) => {
    setVendors((prev) => prev.filter((_, i) => i !== idx));
  };

  const addCriterion = () => {
    setCriteria((prev) => [
      ...prev,
      { name: "New Criterion", weight: 10, description: "", mandatory: false },
    ]);
  };

  const removeCriterion = (idx: number) => {
    setCriteria((prev) => prev.filter((_, i) => i !== idx));
  };

  const updateCriterion = <K extends keyof Criterion>(
    idx: number,
    key: K,
    value: Criterion[K]
  ) => {
    setCriteria((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], [key]: value };
      return next;
    });
  };

  const applyTemplate = (name: string) => {
    if (PRESET_TEMPLATES[name]) {
      setCriteria([...PRESET_TEMPLATES[name]]);
    }
  };

  const handleSubmit = async () => {
    setError("");
    if (!rfpFile) {
      setError("Please upload the original RFP document.");
      return;
    }
    if (vendors.length < 2) {
      setError("At least 2 vendors are required.");
      return;
    }
    const incompleteVendors = vendors.filter((v) => !v.file || !v.name.trim());
    if (incompleteVendors.length > 0) {
      setError("Each vendor must have a name and a file uploaded.");
      return;
    }
    if (criteria.length === 0) {
      setError("Please define at least one evaluation criterion.");
      return;
    }
    if (Math.abs(totalWeight - 100) > 0.1) {
      setError(`Total weight must equal 100% (currently ${totalWeight}%).`);
      return;
    }

    try {
      await onEvaluate({
        rfpFile,
        vendors: vendors.map((v) => ({ name: v.name, file: v.file! })),
        criteria,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed.");
    }
  };

  return (
    <div className="space-y-6">
      {/* ─── Section 1: Original RFP ──────────────────────────────────── */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          1. Original RFP Document
        </h2>
        <input
          type="file"
          ref={rfpInputRef}
          onChange={handleRfpUpload}
          accept=".pdf,.docx"
          className="hidden"
        />
        {!rfpFile ? (
          <div
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-400 transition-colors cursor-pointer"
            onClick={() => rfpInputRef.current?.click()}
          >
            <ArrowUpTrayIcon className="w-10 h-10 text-gray-400 mx-auto" />
            <p className="mt-3 text-sm text-gray-600">
              Upload the original RFP (PDF or DOCX)
            </p>
            <p className="mt-1 text-xs text-gray-400">
              The vendor responses will be evaluated against this document.
            </p>
            <Button className="mt-4">Select RFP File</Button>
          </div>
        ) : (
          <div className="flex items-start gap-3 p-4 bg-orange-50 rounded-lg border border-orange-200">
            <DocumentTextIcon className="w-6 h-6 text-primary-500 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-gray-900">{rfpFile.name}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {(rfpFile.size / 1024).toFixed(1)} KB
              </p>
              {rfpPreview && (
                <p className="mt-2 text-xs text-gray-600 italic line-clamp-3">
                  {rfpPreview}…
                </p>
              )}
            </div>
            <button
              onClick={() => {
                setRfpFile(null);
                setRfpPreview("");
              }}
              className="text-gray-400 hover:text-red-500"
            >
              <TrashIcon className="w-5 h-5" />
            </button>
          </div>
        )}
      </Card>

      {/* ─── Section 2: Vendor Responses ─────────────────────────────── */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            2. Vendor Responses
            <span className="ml-2 text-sm font-normal text-gray-500">
              (minimum 2)
            </span>
          </h2>
          <Button variant="secondary" onClick={addVendor}>
            <PlusIcon className="w-4 h-4 mr-1" />
            Add Vendor
          </Button>
        </div>

        <div className="space-y-3">
          {vendors.map((vendor, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <input
                type="text"
                value={vendor.name}
                onChange={(e) => handleVendorNameChange(idx, e.target.value)}
                placeholder="Vendor name"
                className="flex-shrink-0 w-40 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <input
                type="file"
                ref={(el) => {
                  vendorInputRefs.current[idx] = el;
                }}
                onChange={(e) => handleVendorFileChange(idx, e)}
                accept=".pdf,.docx"
                className="hidden"
              />
              <button
                onClick={() => vendorInputRefs.current[idx]?.click()}
                className="flex-1 text-left px-3 py-2 text-sm bg-white border border-gray-300 rounded-md hover:border-primary-400 transition-colors"
              >
                {vendor.file ? (
                  <span className="flex items-center gap-2">
                    <DocumentTextIcon className="w-4 h-4 text-primary-500" />
                    <span className="truncate">{vendor.file.name}</span>
                  </span>
                ) : (
                  <span className="text-gray-400">Choose PDF/DOCX file…</span>
                )}
              </button>
              {vendors.length > 2 && (
                <button
                  onClick={() => removeVendor(idx)}
                  className="text-gray-400 hover:text-red-500 p-1"
                >
                  <TrashIcon className="w-5 h-5" />
                </button>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* ─── Section 3: Evaluation Criteria ───────────────────────────── */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            3. Evaluation Criteria
          </h2>
          <div className="flex items-center gap-2">
            <span
              className={`text-sm font-medium ${
                Math.abs(totalWeight - 100) < 0.1
                  ? "text-emerald-600"
                  : "text-amber-600"
              }`}
            >
              Total: {totalWeight}%
            </span>
            <Button variant="secondary" onClick={addCriterion}>
              <PlusIcon className="w-4 h-4 mr-1" />
              Add
            </Button>
          </div>
        </div>

        <div className="flex gap-2 mb-4 flex-wrap">
          <span className="text-xs text-gray-500 self-center">Templates:</span>
          {Object.keys(PRESET_TEMPLATES).map((name) => (
            <button
              key={name}
              onClick={() => applyTemplate(name)}
              className="text-xs px-3 py-1 bg-orange-50 text-primary-600 border border-orange-200 rounded-full hover:bg-orange-100"
            >
              {name}
            </button>
          ))}
        </div>

        <div className="space-y-2">
          {criteria.map((c, idx) => (
            <div
              key={idx}
              className="grid grid-cols-12 gap-2 items-center p-3 bg-gray-50 rounded-lg"
            >
              <input
                type="text"
                value={c.name}
                onChange={(e) => updateCriterion(idx, "name", e.target.value)}
                placeholder="Criterion name"
                className="col-span-3 px-2 py-1.5 text-sm text-gray-900 placeholder:text-gray-500 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <div className="col-span-3 flex items-center gap-2">
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={c.weight}
                  onChange={(e) =>
                    updateCriterion(idx, "weight", parseInt(e.target.value))
                  }
                  className="flex-1 accent-primary-500"
                />
                <span className="w-12 text-sm text-right font-medium text-primary-600">
                  {c.weight}%
                </span>
              </div>
              <input
                type="text"
                value={c.description}
                onChange={(e) =>
                  updateCriterion(idx, "description", e.target.value)
                }
                placeholder="Description"
                className="col-span-4 px-2 py-1.5 text-sm text-gray-900 placeholder:text-gray-500 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <label className="col-span-1 flex items-center justify-center text-xs gap-1">
                <input
                  type="checkbox"
                  checked={c.mandatory}
                  onChange={(e) =>
                    updateCriterion(idx, "mandatory", e.target.checked)
                  }
                  className="accent-primary-500"
                />
                <span className="text-gray-600">Mand.</span>
              </label>
              <button
                onClick={() => removeCriterion(idx)}
                className="col-span-1 text-gray-400 hover:text-red-500 flex justify-center"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* ─── Submit ─────────────────────────────────────────────────── */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex flex-col items-center gap-3">
        <Button
          onClick={handleSubmit}
          disabled={isEvaluating}
          className="!px-10 !py-3 !text-base"
        >
          <SparklesIcon className="w-5 h-5 mr-2" />
          {isEvaluating ? "Evaluating…" : "Run AI Evaluation"}
        </Button>
        {isEvaluating && progressMessage && (
          <p className="text-sm text-gray-600 animate-pulse">
            {progressMessage}
          </p>
        )}
      </div>
    </div>
  );
}

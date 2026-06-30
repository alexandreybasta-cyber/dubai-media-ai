"use client";

import { useState } from "react";
import { TrashIcon, PlusIcon } from "@heroicons/react/24/outline";
import { CriteriaEditor, Criterion } from "./CriteriaEditor";
import { TimelineEditor, Milestone } from "./TimelineEditor";
import { Button } from "@/components/Button";
import { RFPCreatePayload } from "@/lib/api";

interface RFPFormProps {
  onSubmit: (data: RFPCreatePayload) => void;
  isLoading: boolean;
}

const COMPLIANCE_OPTIONS = [
  "UAE Data Protection Law",
  "UAE Media Regulatory Office standards",
  "Cybersecurity compliance",
  "Arabic language support required",
  "Local data residency",
];

const INDUSTRY_OPTIONS = [
  "Broadcasting",
  "Technology",
  "Media Production",
  "Digital Services",
  "AI/ML",
];

export function RFPForm({ onSubmit, isLoading }: RFPFormProps) {
  const [projectTitle, setProjectTitle] = useState("");
  const [projectOverview, setProjectOverview] = useState("");
  const [scopeOfWork, setScopeOfWork] = useState("");
  const [technicalRequirements, setTechnicalRequirements] = useState<string[]>([""]);
  const [criteria, setCriteria] = useState<Criterion[]>([
    { id: crypto.randomUUID(), name: "Technical Capability", weight: 30, description: "Technical solution quality and innovation" },
    { id: crypto.randomUUID(), name: "Cost Effectiveness", weight: 25, description: "Value for money and pricing structure" },
    { id: crypto.randomUUID(), name: "Timeline", weight: 20, description: "Ability to deliver within schedule" },
    { id: crypto.randomUUID(), name: "Team Experience", weight: 15, description: "Relevant experience and qualifications" },
    { id: crypto.randomUUID(), name: "Innovation", weight: 10, description: "Novel approaches and future-readiness" },
  ]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [showBudget, setShowBudget] = useState(false);
  const [budgetMin, setBudgetMin] = useState("");
  const [budgetMax, setBudgetMax] = useState("");
  const [budgetCurrency, setBudgetCurrency] = useState("AED");
  const [compliance, setCompliance] = useState<string[]>([]);
  const [customCompliance, setCustomCompliance] = useState("");
  const [industry, setIndustry] = useState("Broadcasting");
  const [language, setLanguage] = useState("en");
  const [tone, setTone] = useState("formal");

  const addRequirement = () => setTechnicalRequirements([...technicalRequirements, ""]);
  const removeRequirement = (index: number) =>
    setTechnicalRequirements(technicalRequirements.filter((_, i) => i !== index));
  const updateRequirement = (index: number, value: string) =>
    setTechnicalRequirements(technicalRequirements.map((r, i) => (i === index ? value : r)));

  const toggleCompliance = (item: string) => {
    setCompliance((prev) =>
      prev.includes(item) ? prev.filter((c) => c !== item) : [...prev, item]
    );
  };

  const addCustomCompliance = () => {
    if (customCompliance.trim() && !compliance.includes(customCompliance.trim())) {
      setCompliance([...compliance, customCompliance.trim()]);
      setCustomCompliance("");
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: RFPCreatePayload = {
      project_title: projectTitle,
      project_overview: projectOverview,
      scope_of_work: scopeOfWork,
      technical_requirements: technicalRequirements.filter((r) => r.trim()),
      evaluation_criteria: criteria
        .filter((c) => c.name.trim())
        .map((c) => ({ name: c.name, weight: c.weight, description: c.description })),
      timeline:
        startDate || endDate
          ? {
              start_date: startDate,
              end_date: endDate,
              milestones: milestones
                .filter((m) => m.name.trim())
                .map((m) => ({ name: m.name, date: m.date })),
            }
          : undefined,
      budget_range: showBudget
        ? { min: parseFloat(budgetMin) || 0, max: parseFloat(budgetMax) || 0, currency: budgetCurrency }
        : null,
      compliance_requirements: compliance,
      industry,
      language,
      tone,
    };
    onSubmit(payload);
  };

  const handleReset = () => {
    setProjectTitle("");
    setProjectOverview("");
    setScopeOfWork("");
    setTechnicalRequirements([""]);
    setCriteria([{ id: crypto.randomUUID(), name: "", weight: 0, description: "" }]);
    setStartDate("");
    setEndDate("");
    setMilestones([]);
    setShowBudget(false);
    setBudgetMin("");
    setBudgetMax("");
    setCompliance([]);
    setIndustry("Broadcasting");
    setLanguage("en");
    setTone("formal");
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Project Title */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Project Title *
        </label>
        <input
          type="text"
          value={projectTitle}
          onChange={(e) => setProjectTitle(e.target.value)}
          placeholder="e.g., AI-Powered Media Asset Management System"
          required
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        />
      </div>

      {/* Project Overview */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Project Overview *
        </label>
        <textarea
          value={projectOverview}
          onChange={(e) => setProjectOverview(e.target.value)}
          rows={3}
          required
          placeholder="Briefly describe the project goals, context, and expected outcomes..."
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none resize-none"
        />
      </div>

      {/* Scope of Work */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Scope of Work
        </label>
        <textarea
          value={scopeOfWork}
          onChange={(e) => setScopeOfWork(e.target.value)}
          rows={5}
          placeholder="Describe the scope of work in detail. You can use markdown/bullet points..."
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none resize-y font-mono"
        />
      </div>

      {/* Technical Requirements */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Technical Requirements
        </label>
        {technicalRequirements.map((req, index) => (
          <div key={index} className="flex gap-2 items-center">
            <input
              type="text"
              value={req}
              onChange={(e) => updateRequirement(index, e.target.value)}
              placeholder={`Requirement ${index + 1}`}
              className="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
            {technicalRequirements.length > 1 && (
              <button
                type="button"
                onClick={() => removeRequirement(index)}
                className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={addRequirement}
          className="flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium"
        >
          <PlusIcon className="w-4 h-4" />
          Add Requirement
        </button>
      </div>

      {/* Evaluation Criteria */}
      <CriteriaEditor criteria={criteria} onChange={setCriteria} />

      {/* Timeline */}
      <TimelineEditor
        startDate={startDate}
        endDate={endDate}
        milestones={milestones}
        onStartDateChange={setStartDate}
        onEndDateChange={setEndDate}
        onMilestonesChange={setMilestones}
      />

      {/* Budget Range */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <label className="block text-sm font-medium text-gray-700">
            Budget Range
          </label>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={showBudget}
              onChange={(e) => setShowBudget(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-500"></div>
          </label>
          <span className="text-xs text-gray-500">(optional)</span>
        </div>
        {showBudget && (
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Min</label>
              <input
                type="number"
                value={budgetMin}
                onChange={(e) => setBudgetMin(e.target.value)}
                placeholder="0"
                className="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Max</label>
              <input
                type="number"
                value={budgetMax}
                onChange={(e) => setBudgetMax(e.target.value)}
                placeholder="0"
                className="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Currency</label>
              <select
                value={budgetCurrency}
                onChange={(e) => setBudgetCurrency(e.target.value)}
                className="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              >
                <option value="AED">AED</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Compliance Requirements */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Compliance Requirements
        </label>
        <div className="space-y-1.5">
          {COMPLIANCE_OPTIONS.map((item) => (
            <label key={item} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={compliance.includes(item)}
                onChange={() => toggleCompliance(item)}
                className="w-4 h-4 text-primary-500 border-gray-300 rounded focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">{item}</span>
            </label>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={customCompliance}
            onChange={(e) => setCustomCompliance(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addCustomCompliance())}
            placeholder="Add custom requirement..."
            className="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
          <button
            type="button"
            onClick={addCustomCompliance}
            className="px-3 py-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            Add
          </button>
        </div>
        {compliance.filter((c) => !COMPLIANCE_OPTIONS.includes(c)).length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {compliance
              .filter((c) => !COMPLIANCE_OPTIONS.includes(c))
              .map((c) => (
                <span
                  key={c}
                  className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary-50 text-primary-700 text-xs rounded-full"
                >
                  {c}
                  <button type="button" onClick={() => toggleCompliance(c)} className="hover:text-red-500">
                    &times;
                  </button>
                </span>
              ))}
          </div>
        )}
      </div>

      {/* Industry */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
        <select
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        >
          {INDUSTRY_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </div>

      {/* Language & Tone */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
          <div className="space-y-1.5">
            {[
              { value: "en", label: "English" },
              { value: "ar", label: "Arabic" },
              { value: "both", label: "Bilingual" },
            ].map((opt) => (
              <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="language"
                  value={opt.value}
                  checked={language === opt.value}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-4 h-4 text-primary-500 border-gray-300 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Tone</label>
          <div className="space-y-1.5">
            {[
              { value: "formal", label: "Formal" },
              { value: "technical", label: "Technical" },
              { value: "concise", label: "Concise" },
            ].map((opt) => (
              <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="tone"
                  value={opt.value}
                  checked={tone === opt.value}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-4 h-4 text-primary-500 border-gray-300 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Submit */}
      <div className="flex gap-3 pt-2 sticky bottom-0 bg-white pb-2">
        <Button type="submit" disabled={isLoading || !projectTitle.trim() || !projectOverview.trim()}>
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Generating...
            </span>
          ) : (
            "Generate RFP"
          )}
        </Button>
        <Button type="button" variant="secondary" onClick={handleReset} disabled={isLoading}>
          Reset
        </Button>
      </div>
    </form>
  );
}

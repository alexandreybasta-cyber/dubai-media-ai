"use client";

import { useState } from "react";
import {
  ChevronDownIcon,
  ChevronRightIcon,
  CheckBadgeIcon,
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
} from "@heroicons/react/24/outline";
import { Card } from "@/components/Card";
import type { VendorResult } from "@/lib/api";

interface VendorScorecardProps {
  vendors: VendorResult[];
}

function scoreColor(score: number): string {
  if (score >= 8) return "text-emerald-600 bg-emerald-50 border-emerald-200";
  if (score >= 5) return "text-amber-600 bg-amber-50 border-amber-200";
  return "text-red-600 bg-red-50 border-red-200";
}

function progressRingColor(score: number): string {
  if (score >= 80) return "#10B981";
  if (score >= 50) return "#F59E0B";
  return "#EF4444";
}

function RadialProgress({ value }: { value: number }) {
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;
  const color = progressRingColor(value);

  return (
    <div className="relative w-32 h-32">
      <svg width="128" height="128" className="transform -rotate-90">
        <circle
          cx="64"
          cy="64"
          r={radius}
          stroke="#F3F4F6"
          strokeWidth="10"
          fill="none"
        />
        <circle
          cx="64"
          cy="64"
          r={radius}
          stroke={color}
          strokeWidth="10"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-gray-900">
          {value.toFixed(0)}
        </span>
        <span className="text-xs text-gray-500">/ 100</span>
      </div>
    </div>
  );
}

export function VendorScorecard({ vendors }: VendorScorecardProps) {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  if (vendors.length === 0) {
    return null;
  }

  const active = vendors[activeTab];

  const toggle = (key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 overflow-x-auto">
        {vendors.map((v, idx) => (
          <button
            key={v.vendor_name}
            onClick={() => setActiveTab(idx)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              idx === activeTab
                ? "border-primary-500 text-primary-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {v.vendor_name}
            <span className="ml-2 text-xs text-gray-400">
              {v.weighted_total.toFixed(1)}
            </span>
          </button>
        ))}
      </div>

      <Card>
        {/* Header with overall score */}
        <div className="flex items-center gap-6 mb-6">
          <RadialProgress value={active.weighted_total} />
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900">
              {active.vendor_name}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Overall weighted evaluation score
            </p>
          </div>
        </div>

        {/* Strengths / Gaps / Risks */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-emerald-700 mb-2">
              <CheckBadgeIcon className="w-5 h-5" />
              Strengths
            </h3>
            <ul className="space-y-1 text-sm text-emerald-900">
              {active.strengths.length === 0 ? (
                <li className="text-emerald-600 italic">No strengths listed</li>
              ) : (
                active.strengths.map((s, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-emerald-500">•</span>
                    <span>{s}</span>
                  </li>
                ))
              )}
            </ul>
          </div>

          <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-700 mb-2">
              <ExclamationTriangleIcon className="w-5 h-5" />
              Gaps
            </h3>
            <ul className="space-y-1 text-sm text-amber-900">
              {active.gaps.length === 0 ? (
                <li className="text-amber-600 italic">No gaps identified</li>
              ) : (
                active.gaps.map((g, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-amber-500">•</span>
                    <span>{g}</span>
                  </li>
                ))
              )}
            </ul>
          </div>

          <div className="p-4 bg-red-50 rounded-lg border border-red-200">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-red-700 mb-2">
              <ShieldExclamationIcon className="w-5 h-5" />
              Risks
            </h3>
            <ul className="space-y-1 text-sm text-red-900">
              {active.risks.length === 0 ? (
                <li className="text-red-600 italic">No risks identified</li>
              ) : (
                active.risks.map((r, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-red-500">•</span>
                    <span>{r}</span>
                  </li>
                ))
              )}
            </ul>
          </div>
        </div>

        {/* Detailed criterion table */}
        <h3 className="text-base font-semibold text-gray-900 mb-3">
          Detailed Criterion Scores
        </h3>
        <div className="space-y-2">
          {active.scores.map((s, i) => {
            const key = `${active.vendor_name}-${i}`;
            const isExpanded = expanded[key];
            return (
              <div
                key={key}
                className="border border-gray-200 rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => toggle(key)}
                  className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 transition-colors text-left"
                >
                  {isExpanded ? (
                    <ChevronDownIcon className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronRightIcon className="w-4 h-4 text-gray-400" />
                  )}
                  <span className="flex-1 font-medium text-gray-800">
                    {s.criterion}
                  </span>
                  <span
                    className={`px-3 py-1 rounded-md border text-sm font-bold ${scoreColor(
                      s.score
                    )}`}
                  >
                    {s.score}/10
                  </span>
                </button>
                {isExpanded && (
                  <div className="px-4 pb-4 pt-1 bg-gray-50 border-t border-gray-200 space-y-2">
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                        Justification
                      </p>
                      <p className="text-sm text-gray-700 mt-1">
                        {s.justification}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                        Evidence
                      </p>
                      <p className="text-sm text-gray-600 italic mt-1 border-l-2 border-primary-300 pl-3">
                        &ldquo;{s.evidence}&rdquo;
                      </p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

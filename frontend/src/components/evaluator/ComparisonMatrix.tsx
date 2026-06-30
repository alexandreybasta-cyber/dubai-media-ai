"use client";

import {
  ArrowDownTrayIcon,
  CheckCircleIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import type { EvaluationResults } from "@/lib/api";

interface ComparisonMatrixProps {
  results: EvaluationResults;
  criteriaWeights: Record<string, number>;
  onExportXlsx: () => void;
  onExportPdf: () => void;
}

const COLORS = ["#F97316", "#10B981", "#3B82F6", "#A855F7", "#EC4899", "#EAB308"];

function scoreColor(score: number): string {
  if (score >= 8) return "bg-emerald-500";
  if (score >= 5) return "bg-amber-500";
  return "bg-red-500";
}

function scoreBadgeClass(score: number): string {
  if (score >= 8) return "bg-emerald-100 text-emerald-700 border-emerald-300";
  if (score >= 5) return "bg-amber-100 text-amber-700 border-amber-300";
  return "bg-red-100 text-red-700 border-red-300";
}

export function ComparisonMatrix({
  results,
  criteriaWeights,
  onExportXlsx,
  onExportPdf,
}: ComparisonMatrixProps) {
  const vendors = results.vendors;
  if (vendors.length === 0) {
    return (
      <Card>
        <p className="text-center text-gray-500 py-8">
          No evaluation data available.
        </p>
      </Card>
    );
  }

  // Use the first vendor's criteria list as reference
  const allCriteria = vendors[0].scores.map((s) => s.criterion);

  // Build radar data
  const radarData = allCriteria.map((criterion) => {
    const entry: Record<string, string | number> = { criterion };
    vendors.forEach((v) => {
      const score = v.scores.find((s) => s.criterion === criterion)?.score ?? 0;
      entry[v.vendor_name] = score;
    });
    return entry;
  });

  // Sort vendors by weighted total for the totals row
  const sortedVendors = [...vendors].sort(
    (a, b) => b.weighted_total - a.weighted_total
  );
  const topVendor = sortedVendors[0];

  return (
    <div className="space-y-6">
      {/* ─── Export Buttons ─────────────────────────────────────────── */}
      <div className="flex justify-end gap-3">
        <Button variant="secondary" onClick={onExportXlsx}>
          <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
          Download XLSX
        </Button>
        <Button variant="secondary" onClick={onExportPdf}>
          <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
          Download PDF Report
        </Button>
      </div>

      {/* ─── Top-line summary ───────────────────────────────────────── */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Weighted Total Scores
        </h2>
        <div
          className="grid gap-4"
          style={{
            gridTemplateColumns: `repeat(${vendors.length}, minmax(0, 1fr))`,
          }}
        >
          {sortedVendors.map((v, idx) => (
            <div
              key={v.vendor_name}
              className={`p-4 rounded-xl text-center border-2 ${
                idx === 0
                  ? "border-primary-500 bg-orange-50"
                  : "border-gray-200 bg-white"
              }`}
            >
              <p className="text-xs text-gray-500 uppercase tracking-wide">
                {idx === 0 ? "Top Score" : `Rank #${idx + 1}`}
              </p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {v.weighted_total.toFixed(1)}
              </p>
              <p className="text-xs text-gray-500 mb-2">/ 100</p>
              <p className="text-sm font-medium text-gray-700 truncate">
                {v.vendor_name}
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* ─── Comparison Matrix Table ───────────────────────────────── */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Score Comparison Matrix
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-gray-200">
                <th className="text-left py-2 px-3 font-semibold text-gray-700">
                  Criterion
                </th>
                <th className="text-center py-2 px-3 font-semibold text-gray-700 w-20">
                  Weight
                </th>
                {vendors.map((v) => (
                  <th
                    key={v.vendor_name}
                    className="text-center py-2 px-3 font-semibold text-gray-700"
                  >
                    {v.vendor_name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allCriteria.map((criterion) => (
                <tr key={criterion} className="border-b border-gray-100">
                  <td className="py-3 px-3 text-gray-800">{criterion}</td>
                  <td className="text-center py-3 px-3 text-gray-500">
                    {criteriaWeights[criterion] ?? "—"}%
                  </td>
                  {vendors.map((v) => {
                    const scoreItem = v.scores.find(
                      (s) => s.criterion === criterion
                    );
                    const score = scoreItem?.score ?? 0;
                    return (
                      <td
                        key={v.vendor_name}
                        className="text-center py-3 px-3"
                      >
                        <span
                          className={`inline-flex items-center justify-center w-10 h-10 rounded-lg text-white font-bold ${scoreColor(
                            score
                          )}`}
                          title={scoreItem?.justification}
                        >
                          {score}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
              <tr className="border-t-2 border-gray-300 bg-orange-50">
                <td className="py-3 px-3 font-bold text-gray-900">
                  WEIGHTED TOTAL
                </td>
                <td className="text-center py-3 px-3 font-bold text-gray-700">
                  100%
                </td>
                {vendors.map((v) => (
                  <td
                    key={v.vendor_name}
                    className="text-center py-3 px-3 font-bold text-lg text-primary-600"
                  >
                    {v.weighted_total.toFixed(1)}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      {/* ─── Radar Chart ───────────────────────────────────────────── */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Vendor Profile Comparison
        </h2>
        <div className="w-full h-96">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid stroke="#E5E7EB" />
              <PolarAngleAxis
                dataKey="criterion"
                tick={{ fill: "#374151", fontSize: 12 }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 10]}
                tick={{ fill: "#9CA3AF", fontSize: 10 }}
              />
              {vendors.map((v, idx) => (
                <Radar
                  key={v.vendor_name}
                  name={v.vendor_name}
                  dataKey={v.vendor_name}
                  stroke={COLORS[idx % COLORS.length]}
                  fill={COLORS[idx % COLORS.length]}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              ))}
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* ─── Mandatory Requirements ────────────────────────────────── */}
      {vendors.some((v) => v.mandatory_compliance.length > 0) && (
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Mandatory Requirements Compliance
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">
                    Requirement
                  </th>
                  {vendors.map((v) => (
                    <th
                      key={v.vendor_name}
                      className="text-center py-2 px-3 font-semibold text-gray-700"
                    >
                      {v.vendor_name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(() => {
                  const allReqs = new Set<string>();
                  vendors.forEach((v) =>
                    v.mandatory_compliance.forEach((m) =>
                      allReqs.add(m.requirement)
                    )
                  );
                  return Array.from(allReqs).map((req) => (
                    <tr key={req} className="border-b border-gray-100">
                      <td className="py-3 px-3 text-gray-800">{req}</td>
                      {vendors.map((v) => {
                        const compliance = v.mandatory_compliance.find(
                          (m) => m.requirement === req
                        );
                        const pass =
                          compliance?.status?.toLowerCase() === "pass";
                        return (
                          <td
                            key={v.vendor_name}
                            className="text-center py-3 px-3"
                          >
                            {compliance ? (
                              pass ? (
                                <CheckCircleIcon
                                  className="w-6 h-6 text-emerald-500 inline-block"
                                  title={compliance.note}
                                />
                              ) : (
                                <XCircleIcon
                                  className="w-6 h-6 text-red-500 inline-block"
                                  title={compliance.note}
                                />
                              )
                            ) : (
                              <span className="text-gray-300">—</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ));
                })()}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Suppress unused warnings */}
      <span className="hidden">
        {topVendor.vendor_name}
        {scoreBadgeClass(0)}
      </span>
    </div>
  );
}

"use client";

import { ArrowUpTrayIcon } from "@heroicons/react/24/outline";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";

export default function RFPEvaluatorPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">RFP Evaluator</h1>
        <p className="mt-1 text-sm text-gray-500">
          Evaluate and compare vendor proposals with AI-powered scoring and
          analysis
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Upload Proposals
            </h2>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors">
              <ArrowUpTrayIcon className="w-10 h-10 text-gray-400 mx-auto" />
              <p className="mt-3 text-sm text-gray-600">
                Upload vendor proposal documents (PDF, DOCX)
              </p>
              <p className="mt-1 text-xs text-gray-400">
                You can upload multiple proposals for comparative evaluation
              </p>
              <Button className="mt-4">Select Files</Button>
            </div>
          </Card>

          <Card className="mt-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Evaluation Criteria
            </h2>
            <div className="space-y-3">
              {[
                { name: "Technical Capability", weight: 30 },
                { name: "Cost Effectiveness", weight: 25 },
                { name: "Timeline", weight: 20 },
                { name: "Team Experience", weight: 15 },
                { name: "Innovation", weight: 10 },
              ].map((criterion) => (
                <div
                  key={criterion.name}
                  className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg"
                >
                  <span className="text-sm text-gray-700">
                    {criterion.name}
                  </span>
                  <span className="text-sm font-medium text-primary-600">
                    {criterion.weight}%
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-4">
              <Button>Start Evaluation</Button>
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Evaluation Results
            </h2>
            <p className="text-sm text-gray-500 text-center py-8">
              Upload proposals and run an evaluation to see results here.
            </p>
          </Card>

          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Export Results
            </h2>
            <div className="space-y-2">
              <Button variant="secondary" className="w-full">
                Export as Excel
              </Button>
              <Button variant="secondary" className="w-full">
                Export as PDF Report
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

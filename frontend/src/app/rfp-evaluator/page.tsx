"use client";

import { useState, useEffect, useRef } from "react";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import {
  EvaluationSetup,
  Criterion,
} from "@/components/evaluator/EvaluationSetup";
import { ComparisonMatrix } from "@/components/evaluator/ComparisonMatrix";
import { VendorScorecard } from "@/components/evaluator/VendorScorecard";
import { RecommendationPanel } from "@/components/evaluator/RecommendationPanel";
import { api, type EvaluationResults } from "@/lib/api";

type Phase = "setup" | "evaluating" | "results";

export default function RFPEvaluatorPage() {
  const [phase, setPhase] = useState<Phase>("setup");
  const [evalId, setEvalId] = useState<string>("");
  const [results, setResults] = useState<EvaluationResults | null>(null);
  const [criteriaWeights, setCriteriaWeights] = useState<Record<string, number>>({});
  const [progressMessage, setProgressMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startEvaluation = async ({
    rfpFile,
    vendors,
    criteria,
  }: {
    rfpFile: File;
    vendors: { name: string; file: File }[];
    criteria: Criterion[];
  }) => {
    setError("");
    setProgressMessage("Uploading files...");

    // Build weights map for the results UI
    const weights: Record<string, number> = {};
    criteria.forEach((c) => {
      weights[c.name] = c.weight;
    });
    setCriteriaWeights(weights);

    // Build FormData
    const formData = new FormData();
    formData.append("rfp_file", rfpFile);
    vendors.forEach((v) => formData.append("vendor_files", v.file));
    formData.append("vendor_names", JSON.stringify(vendors.map((v) => v.name)));
    formData.append("criteria", JSON.stringify(criteria));

    try {
      const response = (await api.rfp.evaluate(formData)) as {
        eval_id: string;
        status: string;
      };
      setEvalId(response.eval_id);
      setPhase("evaluating");
      setProgressMessage("Evaluating with Qwen AI...");

      // Begin polling
      pollRef.current = setInterval(async () => {
        try {
          const status = await api.rfp.getEvaluationStatus(response.eval_id);
          setProgressMessage(status.message);

          if (status.status === "completed") {
            if (pollRef.current) clearInterval(pollRef.current);
            const resultsResponse = await api.rfp.getEvaluationResults(
              response.eval_id
            );
            setResults(resultsResponse.results);
            setPhase("results");
          } else if (status.status === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
            setError(`Evaluation failed: ${status.error || "Unknown error"}`);
            setPhase("setup");
          }
        } catch (err) {
          if (pollRef.current) clearInterval(pollRef.current);
          setError(
            err instanceof Error ? err.message : "Failed to poll evaluation status"
          );
          setPhase("setup");
        }
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start evaluation");
      throw err;
    }
  };

  const resetToSetup = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setPhase("setup");
    setResults(null);
    setEvalId("");
    setProgressMessage("");
    setError("");
  };

  return (
    <div>
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">RFP Evaluator</h1>
          <p className="mt-1 text-sm text-gray-500">
            Evaluate and compare vendor proposals with AI-powered scoring and
            analysis
          </p>
        </div>
        {phase === "results" && (
          <Button variant="secondary" onClick={resetToSetup}>
            <ArrowLeftIcon className="w-4 h-4 mr-2" />
            New Evaluation
          </Button>
        )}
      </div>

      {error && phase === "setup" && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {phase === "setup" && (
        <EvaluationSetup
          onEvaluate={startEvaluation}
          isEvaluating={false}
          progressMessage=""
        />
      )}

      {phase === "evaluating" && (
        <Card>
          <div className="py-16 text-center">
            <div className="inline-block w-16 h-16 border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin mb-6" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Evaluating with Qwen AI
            </h2>
            <p className="text-sm text-gray-600">{progressMessage}</p>
            <p className="text-xs text-gray-400 mt-4">
              Evaluation ID: {evalId.substring(0, 8)}…
            </p>
          </div>
        </Card>
      )}

      {phase === "results" && results && (
        <div className="space-y-8">
          <ComparisonMatrix
            results={results}
            criteriaWeights={criteriaWeights}
            onExportXlsx={() => api.rfp.exportEvaluationXlsx(evalId)}
            onExportPdf={() => api.rfp.exportEvaluationPdf(evalId)}
          />

          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Vendor Scorecards
            </h2>
            <VendorScorecard vendors={results.vendors} />
          </div>

          <RecommendationPanel results={results} />
        </div>
      )}
    </div>
  );
}

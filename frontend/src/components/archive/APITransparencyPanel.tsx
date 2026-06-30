"use client";

import { useState } from "react";
import { APICallLog } from "@/lib/useVideoProcessing";

interface APITransparencyPanelProps {
  apiCalls: APICallLog[];
}

function formatLatency(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function formatCost(cost: number): string {
  if (cost < 0.01) return `<$0.01`;
  return `$${cost.toFixed(3)}`;
}

export default function APITransparencyPanel({
  apiCalls,
}: APITransparencyPanelProps) {
  const [expanded, setExpanded] = useState(false);

  if (apiCalls.length === 0) return null;

  const totalTokens = apiCalls.reduce(
    (sum, c) => sum + c.inputTokens + c.outputTokens,
    0
  );
  const totalLatency = apiCalls.reduce((sum, c) => sum + c.latencyMs, 0);
  const totalCost = apiCalls.reduce((sum, c) => sum + c.estimatedCost, 0);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header / Toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg
            className="w-5 h-5 text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5"
            />
          </svg>
          <span className="text-sm font-semibold text-gray-900">
            API Calls & Performance
          </span>
          <span className="text-xs text-gray-400 ml-2">
            {apiCalls.length} calls • {totalTokens.toLocaleString()} tokens •{" "}
            {formatLatency(totalLatency)} • {formatCost(totalCost)}
          </span>
        </div>
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform ${
            expanded ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="m19.5 8.25-7.5 7.5-7.5-7.5"
          />
        </svg>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-gray-100">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">
                    Stage
                  </th>
                  <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">
                    Model
                  </th>
                  <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">
                    Endpoint
                  </th>
                  <th className="text-right px-4 py-2 text-xs font-medium text-gray-500">
                    Input Tokens
                  </th>
                  <th className="text-right px-4 py-2 text-xs font-medium text-gray-500">
                    Output Tokens
                  </th>
                  <th className="text-right px-4 py-2 text-xs font-medium text-gray-500">
                    Latency
                  </th>
                  <th className="text-right px-4 py-2 text-xs font-medium text-gray-500">
                    Est. Cost
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {apiCalls.map((call, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-2 text-gray-900 font-medium">
                      {call.stage}
                    </td>
                    <td className="px-4 py-2">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-gray-100 text-gray-700">
                        {call.model}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-500 text-xs font-mono truncate max-w-[200px]">
                      {call.endpoint}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-600 font-mono">
                      {call.inputTokens.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-600 font-mono">
                      {call.outputTokens.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-600 font-mono">
                      {formatLatency(call.latencyMs)}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-600 font-mono">
                      {formatCost(call.estimatedCost)}
                    </td>
                  </tr>
                ))}
              </tbody>
              {/* Summary row */}
              <tfoot>
                <tr className="bg-gray-50 font-medium">
                  <td className="px-4 py-2 text-gray-900" colSpan={3}>
                    Total ({apiCalls.length} API calls)
                  </td>
                  <td className="px-4 py-2 text-right text-gray-900 font-mono">
                    {apiCalls
                      .reduce((s, c) => s + c.inputTokens, 0)
                      .toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-900 font-mono">
                    {apiCalls
                      .reduce((s, c) => s + c.outputTokens, 0)
                      .toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-900 font-mono">
                    {formatLatency(totalLatency)}
                  </td>
                  <td className="px-4 py-2 text-right text-primary-600 font-mono font-semibold">
                    {formatCost(totalCost)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { TrashIcon, PlusIcon } from "@heroicons/react/24/outline";

export interface Criterion {
  id: string;
  name: string;
  weight: number;
  description: string;
}

interface CriteriaEditorProps {
  criteria: Criterion[];
  onChange: (criteria: Criterion[]) => void;
}

export function CriteriaEditor({ criteria, onChange }: CriteriaEditorProps) {
  const totalWeight = criteria.reduce((sum, c) => sum + c.weight, 0);

  const addCriterion = () => {
    onChange([
      ...criteria,
      { id: crypto.randomUUID(), name: "", weight: 0, description: "" },
    ]);
  };

  const removeCriterion = (id: string) => {
    onChange(criteria.filter((c) => c.id !== id));
  };

  const updateCriterion = (id: string, field: keyof Criterion, value: string | number) => {
    onChange(
      criteria.map((c) => (c.id === id ? { ...c, [field]: value } : c))
    );
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">
          Evaluation Criteria
        </label>
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full ${
            totalWeight === 100
              ? "bg-green-100 text-green-700"
              : "bg-amber-100 text-amber-700"
          }`}
        >
          Total: {totalWeight}%{totalWeight !== 100 && " (should be 100%)"}
        </span>
      </div>

      {criteria.map((criterion) => (
        <div
          key={criterion.id}
          className="border border-gray-200 rounded-lg p-3 space-y-2 bg-gray-50"
        >
          <div className="flex gap-2 items-start">
            <div className="flex-1">
              <input
                type="text"
                value={criterion.name}
                onChange={(e) =>
                  updateCriterion(criterion.id, "name", e.target.value)
                }
                placeholder="Criterion name"
                className="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
            </div>
            <div className="w-24 flex items-center gap-1">
              <input
                type="number"
                min={0}
                max={100}
                value={criterion.weight}
                onChange={(e) =>
                  updateCriterion(criterion.id, "weight", parseInt(e.target.value) || 0)
                }
                className="w-16 px-2 py-1.5 border border-gray-300 rounded-md text-sm text-center focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
              <span className="text-xs text-gray-500">%</span>
            </div>
            <button
              type="button"
              onClick={() => removeCriterion(criterion.id)}
              className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
            >
              <TrashIcon className="w-4 h-4" />
            </button>
          </div>
          <input
            type="text"
            value={criterion.description}
            onChange={(e) =>
              updateCriterion(criterion.id, "description", e.target.value)
            }
            placeholder="Brief description of this criterion"
            className="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
          <div className="px-1">
            <input
              type="range"
              min={0}
              max={100}
              value={criterion.weight}
              onChange={(e) =>
                updateCriterion(criterion.id, "weight", parseInt(e.target.value))
              }
              className="w-full h-1.5 bg-gray-200 rounded-full appearance-none cursor-pointer accent-primary-500"
            />
          </div>
        </div>
      ))}

      <button
        type="button"
        onClick={addCriterion}
        className="flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium"
      >
        <PlusIcon className="w-4 h-4" />
        Add Criterion
      </button>
    </div>
  );
}

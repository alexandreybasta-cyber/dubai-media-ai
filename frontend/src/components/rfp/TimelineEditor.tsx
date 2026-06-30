"use client";

import { TrashIcon, PlusIcon } from "@heroicons/react/24/outline";

export interface Milestone {
  id: string;
  name: string;
  date: string;
}

interface TimelineEditorProps {
  startDate: string;
  endDate: string;
  milestones: Milestone[];
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  onMilestonesChange: (milestones: Milestone[]) => void;
}

export function TimelineEditor({
  startDate,
  endDate,
  milestones,
  onStartDateChange,
  onEndDateChange,
  onMilestonesChange,
}: TimelineEditorProps) {
  const addMilestone = () => {
    onMilestonesChange([
      ...milestones,
      { id: crypto.randomUUID(), name: "", date: "" },
    ]);
  };

  const removeMilestone = (id: string) => {
    onMilestonesChange(milestones.filter((m) => m.id !== id));
  };

  const updateMilestone = (id: string, field: "name" | "date", value: string) => {
    onMilestonesChange(
      milestones.map((m) => (m.id === id ? { ...m, [field]: value } : m))
    );
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700">
        Timeline & Milestones
      </label>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => onStartDateChange(e.target.value)}
            className="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm text-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => onEndDateChange(e.target.value)}
            className="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm text-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="block text-xs text-gray-500">Milestones</label>
        {milestones.map((milestone) => (
          <div key={milestone.id} className="flex gap-2 items-center">
            <input
              type="text"
              value={milestone.name}
              onChange={(e) => updateMilestone(milestone.id, "name", e.target.value)}
              placeholder="Milestone name"
              className="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm text-gray-900 placeholder:text-gray-500 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
            <input
              type="date"
              value={milestone.date}
              onChange={(e) => updateMilestone(milestone.id, "date", e.target.value)}
              className="w-40 px-3 py-1.5 border border-gray-300 rounded-md text-sm text-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
            <button
              type="button"
              onClick={() => removeMilestone(milestone.id)}
              className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
            >
              <TrashIcon className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      <button
        type="button"
        onClick={addMilestone}
        className="flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium"
      >
        <PlusIcon className="w-4 h-4" />
        Add Milestone
      </button>
    </div>
  );
}

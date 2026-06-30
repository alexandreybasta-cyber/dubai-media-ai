import Link from "next/link";
import {
  FilmIcon,
  DocumentTextIcon,
  ChartBarIcon,
} from "@heroicons/react/24/outline";

const tools = [
  {
    name: "Archive Metadata",
    description:
      "Upload videos and extract rich metadata using AI-powered scene detection, ASR transcription, and visual analysis. Search your archive with natural language.",
    href: "/archive",
    icon: FilmIcon,
    color: "bg-blue-50 text-blue-600",
    borderColor: "border-blue-200 hover:border-blue-300",
  },
  {
    name: "RFP Creator",
    description:
      "Generate professional Request for Proposal documents with AI assistance. Customize sections, tone, and export to DOCX or PDF.",
    href: "/rfp-creator",
    icon: DocumentTextIcon,
    color: "bg-primary-50 text-primary-600",
    borderColor: "border-primary-200 hover:border-primary-300",
  },
  {
    name: "RFP Evaluator",
    description:
      "Evaluate and compare vendor proposals against your RFP criteria. Get AI-powered scoring, rankings, and exportable reports.",
    href: "/rfp-evaluator",
    icon: ChartBarIcon,
    color: "bg-emerald-50 text-emerald-600",
    borderColor: "border-emerald-200 hover:border-emerald-300",
  },
];

export default function HomePage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          AI-powered tools for Dubai Media Incorporated
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tools.map((tool) => (
          <Link
            key={tool.name}
            href={tool.href}
            className={`block rounded-xl border bg-white p-6 transition-all hover:shadow-md ${tool.borderColor}`}
          >
            <div className={`inline-flex p-3 rounded-lg ${tool.color}`}>
              <tool.icon className="w-6 h-6" />
            </div>
            <h2 className="mt-4 text-lg font-semibold text-gray-900">
              {tool.name}
            </h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              {tool.description}
            </p>
            <div className="mt-4 text-sm font-medium text-primary-500 flex items-center gap-1">
              Open tool
              <span aria-hidden="true">&rarr;</span>
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-10 rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900">Quick Stats</h2>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Videos Processed", value: "0" },
            { label: "RFPs Created", value: "0" },
            { label: "Evaluations Run", value: "0" },
            { label: "API Status", value: "Online" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

import Link from "next/link";
import {
  FilmIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  CpuChipIcon,
} from "@heroicons/react/24/outline";

const tools = [
  {
    name: "Video Archive Metadata",
    description:
      "Upload videos and extract rich, broadcast-standard metadata using a 6-stage AI pipeline.",
    href: "/archive",
    icon: FilmIcon,
    color: "bg-blue-50 text-blue-600",
    borderColor: "border-blue-200 hover:border-blue-300",
    capabilities: [
      "Arabic + English speech-to-text (Paraformer)",
      "Scene detection & visual analysis (Qwen-VL)",
      "Face recognition against reference DB",
      "EBUCore XML & IPTC Video Metadata export",
      "Semantic vector search across archive",
    ],
  },
];

const models = [
  { name: "Qwen-VL Max", role: "Video & image understanding" },
  { name: "Paraformer v2", role: "Arabic + English ASR" },
  { name: "Qwen-Max", role: "Text generation & analysis" },
  { name: "Text Embedding v3", role: "Semantic vector search" },
];

export default function HomePage() {
  return (
    <div className="max-w-6xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12 pt-4">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-orange-50 border border-orange-200 text-sm text-orange-700 font-medium mb-6">
          <CpuChipIcon className="w-4 h-4" />
          Powered by Qwen models on Alibaba Cloud
        </div>
        <h1 className="text-4xl font-bold text-gray-900 tracking-tight">
          Prototype : Media
        </h1>
        <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed">
          An AI-powered MVP demonstrating intelligent media archive management
          — purpose-built for Dubai Media Incorporated.
        </p>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
        {tools.map((tool) => (
          <div
            key={tool.name}
            className={`rounded-xl border bg-white p-6 transition-all hover:shadow-md ${tool.borderColor} flex flex-col`}
          >
            <div className={`inline-flex p-3 rounded-lg ${tool.color} w-fit`}>
              <tool.icon className="w-6 h-6" />
            </div>
            <h2 className="mt-4 text-lg font-semibold text-gray-900">
              {tool.name}
            </h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              {tool.description}
            </p>
            <ul className="mt-4 space-y-1.5 flex-1">
              {tool.capabilities.map((cap) => (
                <li
                  key={cap}
                  className="text-xs text-gray-600 flex items-start gap-2"
                >
                  <span className="text-green-500 mt-0.5 flex-shrink-0">✓</span>
                  {cap}
                </li>
              ))}
            </ul>
            <Link
              href={tool.href}
              className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-orange-600 hover:text-orange-700 transition-colors"
            >
              Open tool <span aria-hidden="true">&rarr;</span>
            </Link>
          </div>
        ))}
      </div>

      {/* Tech Stack Badges */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 mb-8">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
          Models & Technology
        </h2>
        <div className="flex flex-wrap gap-3">
          {models.map((m) => (
            <div
              key={m.name}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-50 border border-gray-200"
            >
              <span className="font-semibold text-sm text-gray-900">
                {m.name}
              </span>
              <span className="text-xs text-gray-500">{m.role}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Why Alibaba Cloud */}
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Why Alibaba Cloud
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-blue-50">
              <GlobeAltIcon className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                Arabic-First AI
              </h3>
              <p className="mt-1 text-xs text-gray-500 leading-relaxed">
                Qwen models excel at Arabic language understanding,
                transcription, and generation — critical for UAE media workflows.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-emerald-50">
              <ShieldCheckIcon className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                Data Sovereignty (UAE Region)
              </h3>
              <p className="mt-1 text-xs text-gray-500 leading-relaxed">
                DashScope can be deployed in the UAE region, ensuring
                compliance with local data residency and sovereignty regulations.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-orange-50">
              <CpuChipIcon className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                Unified Vendor
              </h3>
              <p className="mt-1 text-xs text-gray-500 leading-relaxed">
                One platform for vision, speech, text generation, and embeddings
                — simplifying procurement, billing, and support.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

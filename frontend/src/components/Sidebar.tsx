"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FilmIcon,
  DocumentTextIcon,
  ChartBarIcon,
} from "@heroicons/react/24/outline";

const navigation = [
  { name: "Archive Metadata", href: "/archive", icon: FilmIcon },
  { name: "RFP Creator", href: "/rfp-creator", icon: DocumentTextIcon },
  { name: "RFP Evaluator", href: "/rfp-evaluator", icon: ChartBarIcon },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <Link href="/" className="block">
          <h1 className="text-lg font-bold text-gray-900 leading-tight">
            Dubai Media
          </h1>
          <p className="text-xs text-primary-500 font-medium mt-0.5">
            × Alibaba Cloud AI
          </p>
        </Link>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-primary-50 text-primary-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <item.icon
                className={`w-5 h-5 flex-shrink-0 ${
                  isActive ? "text-primary-500" : "text-gray-400"
                }`}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-400 rounded-full" />
          <span className="text-xs text-gray-500">API Connected</span>
        </div>
      </div>
    </aside>
  );
}

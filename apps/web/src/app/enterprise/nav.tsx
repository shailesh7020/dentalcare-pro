"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Building2,
  GitBranch,
  Globe2,
  ShieldAlert,
  ArrowLeftRight,
  Boxes,
  CircleDollarSign,
  TrendingUp,
  Megaphone,
  Sparkles,
  Smartphone,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { name: "Corporate Hub", href: "/enterprise", icon: Building2 },
  { name: "Organizations", href: "/enterprise/organizations", icon: Globe2 },
  { name: "Branches", href: "/enterprise/branches", icon: GitBranch },
  { name: "Regions", href: "/enterprise/regions", icon: Building2 },
  { name: "Roles & Matrix", href: "/enterprise/permissions", icon: ShieldAlert },
  { name: "Patient Transfers", href: "/enterprise/transfers/patients", icon: ArrowLeftRight },
  { name: "Inventory Stock", href: "/enterprise/transfers/inventory", icon: Boxes },
  { name: "Consolidated Financials", href: "/enterprise/financials", icon: CircleDollarSign },
  { name: "AI Benchmark Analytics", href: "/enterprise/analytics", icon: TrendingUp },
  { name: "Announcements", href: "/enterprise/announcements", icon: Megaphone },
  { name: "Remote & Mobile Access", href: "/enterprise/remote", icon: Smartphone },
];

export function EnterpriseNav() {
  const pathname = usePathname();

  return (
    <div className="bg-white border-b border-slate-200 sticky top-0 z-20 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-200">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 text-lg tracking-tight">Enterprise Network</span>
                <span className="inline-flex items-center gap-1 text-[11px] font-medium bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full border border-purple-200">
                  <Sparkles className="w-3 h-3" /> Corporate Tier
                </span>
              </div>
              <p className="text-xs text-slate-500">Multi-clinic hierarchy, consolidated rollups & inter-branch logistics</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/enterprise/branches"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm transition-colors"
            >
              <GitBranch className="w-3.5 h-3.5" />
              Branch Directory
            </Link>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 overflow-x-auto scrollbar-none py-1 border-t border-slate-100">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`inline-flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${
                  isActive
                    ? "bg-indigo-50 text-indigo-700 font-semibold"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-indigo-600" : "text-slate-400"}`} />
                {item.name}
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

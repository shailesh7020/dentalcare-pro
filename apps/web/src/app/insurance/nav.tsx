"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShieldCheck,
  FileSpreadsheet,
  FileCheck2,
  Building2,
  ListTree,
  UserCheck,
  Receipt,
  BarChart3,
  Sparkles,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { name: "Dashboard", href: "/insurance", icon: ShieldCheck },
  { name: "Claims", href: "/insurance/claims", icon: FileSpreadsheet },
  { name: "Pre-Auth", href: "/insurance/preauth", icon: FileCheck2 },
  { name: "Providers & TPAs", href: "/insurance/providers", icon: Building2 },
  { name: "Plans & Rules", href: "/insurance/plans", icon: ListTree },
  { name: "Patient Policies", href: "/insurance/policies", icon: UserCheck },
  { name: "Reconciliation", href: "/insurance/reconciliation", icon: Receipt },
  { name: "Reports & Analytics", href: "/insurance/reports", icon: BarChart3 },
];

export function InsuranceNav() {
  const pathname = usePathname();

  return (
    <div className="bg-white border-b border-slate-200 sticky top-0 z-20 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-teal-50 text-teal-700 rounded-lg border border-teal-200">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 text-lg tracking-tight">Insurance & Claims</span>
                <span className="inline-flex items-center gap-1 text-[11px] font-medium bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full border border-emerald-200">
                  <Sparkles className="w-3 h-3" /> AI Audit Active
                </span>
              </div>
              <p className="text-xs text-slate-500">Payer integration, pre-authorizations, claim tracking & remittance</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/insurance/claims"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-teal-600 text-white hover:bg-teal-700 shadow-sm transition-colors"
            >
              Claims Directory
            </Link>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex gap-1 overflow-x-auto no-scrollbar pt-1">
          {navItems.map((item) => {
            const isActive =
              item.href === "/insurance"
                ? pathname === "/insurance"
                : pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`inline-flex items-center gap-2 px-3.5 py-2.5 text-xs font-semibold rounded-t-lg transition-colors border-b-2 whitespace-nowrap ${
                  isActive
                    ? "border-teal-600 text-teal-700 bg-teal-50/50"
                    : "border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-teal-600" : "text-slate-400"}`} />
                {item.name}
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { Building2, Plus, GitBranch, Users2, MapPin } from "lucide-react";
import { EnterpriseNav } from "../nav";
import { Region } from "../types";

const INITIAL_REGIONS: Region[] = [
  {
    id: "reg-1",
    organization_id: "org-1",
    name: "North India Regional Hub",
    code: "REG-NORTH",
    description: "Covers Delhi NCR, Chandigarh, and Punjab practices",
    is_active: true,
    branch_count: 5,
    created_at: "2026-01-10T10:00:00Z",
    updated_at: "2026-09-01T10:00:00Z",
  },
  {
    id: "reg-2",
    organization_id: "org-1",
    name: "South Karnataka Hub",
    code: "REG-SOUTH-KA",
    description: "Covers Bengaluru Metro and Mysuru clinical facilities",
    is_active: true,
    branch_count: 4,
    created_at: "2026-01-12T10:00:00Z",
    updated_at: "2026-09-01T10:00:00Z",
  },
  {
    id: "reg-3",
    organization_id: "org-1",
    name: "Western Coastal Hub",
    code: "REG-WEST",
    description: "Covers Greater Mumbai and Pune practice locations",
    is_active: true,
    branch_count: 3,
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-09-01T10:00:00Z",
  },
];

export default function RegionsPage() {
  const [regions] = useState<Region[]>(INITIAL_REGIONS);

  return (
    <div className="min-h-screen bg-slate-50">
      <EnterpriseNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Regional Administration</h1>
            <p className="text-xs text-slate-500 mt-1">
              Group clinics by geographical territories, assign regional directors, and consolidate reporting.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {regions.map((region) => (
            <div
              key={region.id}
              className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4 hover:border-slate-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="font-bold text-slate-900 text-base">{region.name}</h2>
                  <span className="text-xs font-mono font-semibold text-indigo-600">
                    {region.code}
                  </span>
                </div>
                <span className="px-2 py-0.5 text-[11px] font-semibold bg-indigo-50 text-indigo-700 rounded-md border border-indigo-200">
                  {region.branch_count} Branches
                </span>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">
                {region.description || "Operational regional territory"}
              </p>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1.5">
                  <GitBranch className="w-3.5 h-3.5 text-slate-400" />
                  Active Network Area
                </span>
                <span className="text-emerald-600 font-medium">Operational</span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

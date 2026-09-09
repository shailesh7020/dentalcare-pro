"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Building2,
  GitBranch,
  Users2,
  TrendingUp,
  ArrowRight,
  ShieldCheck,
  Boxes,
  ArrowLeftRight,
  Sparkles,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { EnterpriseNav } from "./nav";

export default function EnterpriseDashboardPage() {
  const [selectedOrg] = useState("Apollo Dental Network");

  return (
    <div className="min-h-screen bg-slate-50">
      <EnterpriseNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header with Organization Selector */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-900">Corporate Administration</h1>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                Network Online
              </span>
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Global multi-clinic hierarchy, consolidated financial rollups, and inter-branch operational health.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-slate-500">Active Organization:</span>
            <div className="px-3 py-1.5 bg-indigo-50 text-indigo-700 text-sm font-semibold rounded-lg border border-indigo-200">
              {selectedOrg}
            </div>
            <Link
              href="/enterprise/organizations"
              className="text-xs text-slate-500 hover:text-indigo-600 underline font-medium"
            >
              Switch
            </Link>
          </div>
        </div>

        {/* Corporate Network KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Total Branches</span>
              <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                <GitBranch className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-slate-900">12</div>
              <p className="text-xs text-emerald-600 mt-1 font-medium">Across 4 Regions</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Network Revenue</span>
              <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                <TrendingUp className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-slate-900">₹42.8 Lakh</div>
              <p className="text-xs text-emerald-600 mt-1 font-medium">+14.2% MoM rollup</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Roaming Staff</span>
              <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                <Users2 className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-slate-900">18</div>
              <p className="text-xs text-slate-500 mt-1">Multi-branch doctors</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Patient Transfers</span>
              <div className="p-2 bg-teal-50 text-teal-600 rounded-lg">
                <ArrowLeftRight className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-slate-900">24</div>
              <p className="text-xs text-slate-500 mt-1">3 pending approval</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Stock In-Transit</span>
              <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                <Boxes className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-slate-900">₹1.85 Lakh</div>
              <p className="text-xs text-amber-600 mt-1 font-medium">6 active dispatches</p>
            </div>
          </div>
        </div>

        {/* AI Network Benchmark & Operational Health */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-purple-50 text-purple-700 rounded-lg">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">AI Branch Benchmark Rankings</h2>
                  <p className="text-xs text-slate-500">Algorithmic scoring based on revenue yield, chair occupancy, and collection velocity</p>
                </div>
              </div>
              <Link
                href="/enterprise/analytics"
                className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1"
              >
                Deep Analytics <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-500 font-semibold uppercase">
                    <th className="py-2.5 px-3">Rank</th>
                    <th className="py-2.5 px-3">Branch Clinic</th>
                    <th className="py-2.5 px-3">Region</th>
                    <th className="py-2.5 px-3">Occupancy</th>
                    <th className="py-2.5 px-3">Collection</th>
                    <th className="py-2.5 px-3">Overall Score</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3 font-bold text-indigo-600">#1</td>
                    <td className="py-3 px-3 font-semibold text-slate-900">Central Flagship Clinic</td>
                    <td className="py-3 px-3 text-slate-600">North Hub</td>
                    <td className="py-3 px-3 font-medium text-slate-900">92%</td>
                    <td className="py-3 px-3 font-medium text-emerald-600">96.5%</td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-100 rounded-full h-2">
                          <div className="bg-indigo-600 h-2 rounded-full" style={{ width: "94%" }} />
                        </div>
                        <span className="font-bold text-slate-900">94/100</span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 text-[11px] font-medium bg-emerald-50 text-emerald-700 rounded-md border border-emerald-200">
                        Exemplary
                      </span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3 font-bold text-indigo-600">#2</td>
                    <td className="py-3 px-3 font-semibold text-slate-900">Indiranagar Dental Lounge</td>
                    <td className="py-3 px-3 text-slate-600">South Hub</td>
                    <td className="py-3 px-3 font-medium text-slate-900">88%</td>
                    <td className="py-3 px-3 font-medium text-emerald-600">91.0%</td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-100 rounded-full h-2">
                          <div className="bg-indigo-600 h-2 rounded-full" style={{ width: "88%" }} />
                        </div>
                        <span className="font-bold text-slate-900">88/100</span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 text-[11px] font-medium bg-indigo-50 text-indigo-700 rounded-md border border-indigo-200">
                        High Yield
                      </span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3 font-bold text-indigo-600">#3</td>
                    <td className="py-3 px-3 font-semibold text-slate-900">Whitefield Specialty Wing</td>
                    <td className="py-3 px-3 text-slate-600">South Hub</td>
                    <td className="py-3 px-3 font-medium text-slate-900">76%</td>
                    <td className="py-3 px-3 font-medium text-amber-600">81.2%</td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-100 rounded-full h-2">
                          <div className="bg-amber-500 h-2 rounded-full" style={{ width: "79%" }} />
                        </div>
                        <span className="font-bold text-slate-900">79/100</span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 text-[11px] font-medium bg-amber-50 text-amber-700 rounded-md border border-amber-200">
                        Stable
                      </span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3 font-bold text-slate-400">#4</td>
                    <td className="py-3 px-3 font-semibold text-slate-900">Suburban East Clinic</td>
                    <td className="py-3 px-3 text-slate-600">East Hub</td>
                    <td className="py-3 px-3 font-medium text-slate-900">54%</td>
                    <td className="py-3 px-3 font-medium text-rose-600">68.0%</td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-100 rounded-full h-2">
                          <div className="bg-rose-500 h-2 rounded-full" style={{ width: "58%" }} />
                        </div>
                        <span className="font-bold text-slate-900">58/100</span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 text-[11px] font-medium bg-rose-50 text-rose-700 rounded-md border border-rose-200">
                        Attention Req.
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Quick Management Shortcuts */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4 flex flex-col justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900">Enterprise Workflows</h2>
              <p className="text-xs text-slate-500 mt-0.5">Corporate actions requiring executive review</p>

              <div className="mt-4 space-y-2.5">
                <Link
                  href="/enterprise/transfers/patients"
                  className="p-3 bg-slate-50 hover:bg-indigo-50/50 rounded-lg border border-slate-100 flex items-center justify-between group transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-100 text-indigo-700 rounded-md">
                      <ArrowLeftRight className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
                        Patient Relocation Queue
                      </div>
                      <div className="text-[11px] text-slate-500">3 cross-branch requests awaiting approval</div>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 transition-colors" />
                </Link>

                <Link
                  href="/enterprise/transfers/inventory"
                  className="p-3 bg-slate-50 hover:bg-indigo-50/50 rounded-lg border border-slate-100 flex items-center justify-between group transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-amber-100 text-amber-700 rounded-md">
                      <Boxes className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
                        Consumable Dispatch Review
                      </div>
                      <div className="text-[11px] text-slate-500">Composite resin batch transfer in transit</div>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 transition-colors" />
                </Link>

                <Link
                  href="/enterprise/permissions"
                  className="p-3 bg-slate-50 hover:bg-indigo-50/50 rounded-lg border border-slate-100 flex items-center justify-between group transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 text-purple-700 rounded-md">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
                        Permission Matrix
                      </div>
                      <div className="text-[11px] text-slate-500">Manage 10 roles and per-dentist roaming overrides</div>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 transition-colors" />
                </Link>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100">
              <Link
                href="/enterprise/financials"
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors"
              >
                <BarChart3 className="w-4 h-4" />
                Open Consolidated Financial Report
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

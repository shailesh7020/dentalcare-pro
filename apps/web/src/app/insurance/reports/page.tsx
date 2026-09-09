"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  Calendar,
  Download,
  Building2,
  TrendingUp,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { InsuranceNav } from "../nav";
import type { ClaimsReportResponse, ProviderPerformanceResponse } from "../types";

export default function InsuranceReportsPage() {
  const [activeTab, setActiveTab] = useState<"CLAIMS" | "PERFORMANCE">("CLAIMS");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const { data: claimsReport, isLoading: isLoadingClaims } = useQuery<ClaimsReportResponse>({
    queryKey: ["insurance-claims-report", statusFilter],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (statusFilter !== "ALL") params.status = statusFilter;
      const res = await api.get<ClaimsReportResponse>("/insurance/reports/claims", { params });
      return res.data;
    },
  });

  const { data: providerReport, isLoading: isLoadingProviders } = useQuery<ProviderPerformanceResponse>({
    queryKey: ["insurance-provider-performance-report"],
    queryFn: async () => {
      const res = await api.get<ProviderPerformanceResponse>("/insurance/reports/provider-performance");
      return res.data;
    },
  });

  return (
    <div className="min-h-screen bg-slate-50/50">
      <InsuranceNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Insurance & Claims Analytics</h1>
            <p className="text-sm text-slate-600 mt-1">
              Adjudication volume, payer performance scorecards, approval ratios, and turnaround times.
            </p>
          </div>
          {/* Subtabs */}
          <div className="flex bg-slate-200/80 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab("CLAIMS")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === "CLAIMS" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Claims Report
            </button>
            <button
              onClick={() => setActiveTab("PERFORMANCE")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === "PERFORMANCE" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Provider Scorecard
            </button>
          </div>
        </div>

        {activeTab === "CLAIMS" ? (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500 uppercase">Total Claims</span>
                <p className="text-2xl font-bold text-slate-900 mt-1">
                  {claimsReport?.total_claims ?? 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500 uppercase">Claimed Value</span>
                <p className="text-2xl font-bold text-slate-900 mt-1">
                  ₹{(claimsReport?.total_claimed_sum ?? 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500 uppercase">Approved Value</span>
                <p className="text-2xl font-bold text-emerald-600 mt-1">
                  ₹{(claimsReport?.total_approved_sum ?? 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500 uppercase">Paid / Settled</span>
                <p className="text-2xl font-bold text-teal-600 mt-1">
                  ₹{(claimsReport?.total_paid_sum ?? 0).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Claims Table */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4">Claim #</th>
                      <th className="py-3 px-4">Submission Date</th>
                      <th className="py-3 px-4">Claimed Value</th>
                      <th className="py-3 px-4">Approved Value</th>
                      <th className="py-3 px-4">Paid Value</th>
                      <th className="py-3 px-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {claimsReport && claimsReport.claims.length > 0 ? (
                      claimsReport.claims.map((cl) => (
                        <tr key={cl.id} className="hover:bg-slate-50/50">
                          <td className="py-3 px-4 font-mono font-bold text-slate-900">{cl.claim_number}</td>
                          <td className="py-3 px-4 text-slate-600">{cl.submission_date || "Draft"}</td>
                          <td className="py-3 px-4 font-semibold text-slate-900">
                            ₹{cl.total_claimed_amount.toLocaleString()}
                          </td>
                          <td className="py-3 px-4 font-semibold text-emerald-700">
                            {cl.approved_amount ? `₹${cl.approved_amount.toLocaleString()}` : "—"}
                          </td>
                          <td className="py-3 px-4 text-slate-700">
                            {cl.paid_amount ? `₹${cl.paid_amount.toLocaleString()}` : "₹0"}
                          </td>
                          <td className="py-3 px-4">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                              {cl.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="text-center py-8 text-slate-400">
                          No claims recorded for this report.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          /* Provider Scorecard */
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Insurance Company / TPA</th>
                    <th className="py-3 px-4">Total Submissions</th>
                    <th className="py-3 px-4">Approved</th>
                    <th className="py-3 px-4">Denied</th>
                    <th className="py-3 px-4">Approval Rate</th>
                    <th className="py-3 px-4">Avg. Turnaround</th>
                    <th className="py-3 px-4">Settled Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {providerReport && providerReport.providers.length > 0 ? (
                    providerReport.providers.map((prov, i) => (
                      <tr key={i} className="hover:bg-slate-50/50">
                        <td className="py-3 px-4 font-bold text-slate-900">{prov.provider_name}</td>
                        <td className="py-3 px-4 font-semibold text-slate-800">{prov.total_claims}</td>
                        <td className="py-3 px-4 text-emerald-700 font-medium">{prov.approved_claims}</td>
                        <td className="py-3 px-4 text-rose-700 font-medium">{prov.rejected_claims}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                              prov.approval_rate >= 80
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                : "bg-amber-50 text-amber-700 border border-amber-200"
                            }`}
                          >
                            {prov.approval_rate}%
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-700">{prov.average_turnaround_days} days</td>
                        <td className="py-3 px-4 font-bold text-slate-900">
                          ₹{prov.total_settled_amount.toLocaleString()}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-slate-400">
                        No provider scorecard metrics available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

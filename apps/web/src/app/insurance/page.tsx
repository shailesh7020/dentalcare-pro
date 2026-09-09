"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  Clock,
  CheckCircle2,
  XCircle,
  FileSpreadsheet,
  Building2,
  Receipt,
  ArrowUpRight,
  Sparkles,
  TrendingUp,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import { api } from "@/lib/api";
import { InsuranceNav } from "./nav";
import type { InsuranceDashboardStats } from "./types";

export default function InsuranceDashboardPage() {
  const { data: stats, isLoading, refetch } = useQuery<InsuranceDashboardStats>({
    queryKey: ["insurance-dashboard-stats"],
    queryFn: async () => {
      const res = await api.get<InsuranceDashboardStats>("/insurance/dashboard");
      return res.data;
    },
  });

  return (
    <div className="min-h-screen bg-slate-50/50">
      <InsuranceNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header & Quick Action */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Insurance Operations Dashboard</h1>
            <p className="text-sm text-slate-600 mt-1">
              Real-time adjudications, claims volume, denial analysis, and automated remittance reconciliation.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => refetch()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 shadow-xs cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>
            <Link
              href="/insurance/claims"
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-teal-600 rounded-md hover:bg-teal-700 shadow-sm transition-colors"
            >
              Submit New Claim <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* KPI Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Pending Adjudication</span>
              <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                <Clock className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-slate-900">
                {isLoading ? "..." : stats?.pending_claims_count ?? 0}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                <span className="text-amber-600 font-medium">Requires payer follow-up</span>
              </p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Approved Claims</span>
              <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-emerald-700">
                {isLoading ? "..." : stats?.approved_claims_count ?? 0}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                ₹{(stats?.total_approved_amount ?? 0).toLocaleString()} approved
              </p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Rejected / Denied</span>
              <div className="p-2 bg-rose-50 text-rose-600 rounded-lg">
                <XCircle className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-rose-600">
                {isLoading ? "..." : stats?.rejected_claims_count ?? 0}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                <Link href="/insurance/claims" className="text-teal-600 hover:underline">
                  AI Appeal available
                </Link>
              </p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Avg. Turnaround Time</span>
              <div className="p-2 bg-teal-50 text-teal-600 rounded-lg">
                <TrendingUp className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-slate-900">
                {isLoading ? "..." : `${stats?.average_turnaround_days ?? 0} days`}
              </div>
              <p className="text-xs text-slate-500 mt-1">Submission to payer settlement</p>
            </div>
          </div>
        </div>

        {/* Financial Settlement Overview */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
          <h2 className="text-base font-semibold text-slate-900 mb-4">Financial Settlements Summary</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 divide-y sm:divide-y-0 sm:divide-x divide-slate-200">
            <div className="pt-4 sm:pt-0 sm:px-4 first:pl-0">
              <p className="text-xs font-medium text-slate-500 uppercase">Total Claimed Value</p>
              <p className="text-2xl font-bold text-slate-900 mt-2">
                ₹{(stats?.total_claimed_amount ?? 0).toLocaleString()}
              </p>
              <p className="text-xs text-slate-400 mt-1">Cumulative submissions</p>
            </div>
            <div className="pt-4 sm:pt-0 sm:px-4">
              <p className="text-xs font-medium text-slate-500 uppercase">Settled (Remittance Received)</p>
              <p className="text-2xl font-bold text-emerald-600 mt-2">
                ₹{(stats?.total_settled_amount ?? 0).toLocaleString()}
              </p>
              <p className="text-xs text-slate-400 mt-1">Posted to billing ledger</p>
            </div>
            <div className="pt-4 sm:pt-0 sm:px-4">
              <p className="text-xs font-medium text-slate-500 uppercase">Outstanding Insurance AR</p>
              <p className="text-2xl font-bold text-amber-600 mt-2">
                ₹{(stats?.total_outstanding_amount ?? 0).toLocaleString()}
              </p>
              <p className="text-xs text-slate-400 mt-1">Pending payer adjudication</p>
            </div>
          </div>
        </div>

        {/* AI Insurance Assistant Banner */}
        <div className="bg-gradient-to-r from-teal-900 via-teal-800 to-slate-900 rounded-xl p-6 text-white shadow-md relative overflow-hidden">
          <div className="relative z-10 max-w-2xl">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-teal-500/20 text-teal-200 border border-teal-400/30 text-xs font-medium mb-3">
              <Sparkles className="w-3.5 h-3.5 text-teal-300" /> AI Clinical Insurance Specialist
            </div>
            <h3 className="text-lg font-bold text-white">
              Pre-Submission Completeness Audits & Automated Appeal Letters
            </h3>
            <p className="text-sm text-teal-100/90 mt-2 leading-relaxed">
              DentalCare Pro AI evaluates claims before transmission to prevent denials. It verifies mandatory radiographs
              (e.g., peri-apical for endodontics), checks pre-authorization validity, matches CDT procedure codes, and
              instantly drafts formal clinical appeal letters for denied claims.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                href="/insurance/claims"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-teal-400 text-slate-950 text-xs font-semibold hover:bg-teal-300 transition-colors"
              >
                Audit Claim in Claims Manager <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href="/insurance/plans"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-white/10 text-white text-xs font-medium hover:bg-white/20 border border-white/20 transition-colors"
              >
                View Plan Coverage Matrix
              </Link>
            </div>
          </div>
        </div>

        {/* Quick Access Modules Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <Link
            href="/insurance/claims"
            className="group bg-white p-5 rounded-xl border border-slate-200 hover:border-teal-400 hover:shadow-md transition-all"
          >
            <div className="p-3 bg-teal-50 text-teal-700 rounded-lg w-fit group-hover:scale-105 transition-transform">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 mt-4 text-sm">Claims Management</h3>
            <p className="text-xs text-slate-500 mt-1">Create, submit, track and appeal claims through payers.</p>
          </Link>

          <Link
            href="/insurance/preauth"
            className="group bg-white p-5 rounded-xl border border-slate-200 hover:border-teal-400 hover:shadow-md transition-all"
          >
            <div className="p-3 bg-blue-50 text-blue-700 rounded-lg w-fit group-hover:scale-105 transition-transform">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 mt-4 text-sm">Pre-Authorizations</h3>
            <p className="text-xs text-slate-500 mt-1">Prior approvals for major treatments and surgical procedures.</p>
          </Link>

          <Link
            href="/insurance/providers"
            className="group bg-white p-5 rounded-xl border border-slate-200 hover:border-teal-400 hover:shadow-md transition-all"
          >
            <div className="p-3 bg-purple-50 text-purple-700 rounded-lg w-fit group-hover:scale-105 transition-transform">
              <Building2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 mt-4 text-sm">Providers & TPAs</h3>
            <p className="text-xs text-slate-500 mt-1">Manage insurance companies, TPAs, portals and contacts.</p>
          </Link>

          <Link
            href="/insurance/reconciliation"
            className="group bg-white p-5 rounded-xl border border-slate-200 hover:border-teal-400 hover:shadow-md transition-all"
          >
            <div className="p-3 bg-emerald-50 text-emerald-700 rounded-lg w-fit group-hover:scale-105 transition-transform">
              <Receipt className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 mt-4 text-sm">Payment Reconciliation</h3>
            <p className="text-xs text-slate-500 mt-1">Post remittance advice, balance adjustments and copay dues.</p>
          </Link>
        </div>
      </main>
    </div>
  );
}

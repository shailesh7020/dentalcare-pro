"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowLeft,
  Banknote,
  Calendar,
  CheckCircle2,
  Clock,
  CreditCard,
  Download,
  FileSpreadsheet,
  FileText,
  Filter,
  IndianRupee,
  PieChart,
  Printer,
  Stethoscope,
  TrendingUp,
  User,
  Wallet,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { RevenueReport } from "../types";

export default function RevenueReportsPage() {
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  const reportQuery = useQuery({
    queryKey: ["billing-revenue-report", dateFrom, dateTo],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await api.get<RevenueReport>("/billing/reports/revenue", {
        params,
      });
      return res.data;
    },
  });

  const report = reportQuery.data;

  return (
    <div className="min-h-screen bg-slate-50/50 p-6 md:p-8 space-y-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Navigation Top Bar */}
        <div className="flex items-center justify-between">
          <Link
            href="/billing"
            className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Invoices
          </Link>
          <div className="flex items-center gap-2">
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 shadow-xs"
            >
              <Printer className="w-3.5 h-3.5" />
              Print Report
            </button>
          </div>
        </div>

        {/* Page Header */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-emerald-600 text-xs font-bold uppercase tracking-wider">
              <TrendingUp className="w-4 h-4" />
              Financial Intelligence
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mt-1">
              Revenue & Collections Analytics
            </h1>
            <p className="text-sm text-slate-500">
              Accounts receivable, payment method distribution, and clinician production insights
            </p>
          </div>

          {/* Date Filter Bar */}
          <div className="flex items-center gap-2 bg-slate-50 p-2 rounded-xl border border-slate-200">
            <Calendar className="w-4 h-4 text-slate-400 ml-1" />
            <div className="flex items-center gap-2 text-xs">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="px-2 py-1 bg-white border border-slate-200 rounded-lg text-slate-700 focus:outline-none"
                placeholder="From"
              />
              <span className="text-slate-400">to</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="px-2 py-1 bg-white border border-slate-200 rounded-lg text-slate-700 focus:outline-none"
                placeholder="To"
              />
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Total Invoiced
            </span>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {reportQuery.isLoading ? (
                <Skeleton className="h-7 w-24" />
              ) : (
                `₹${(report?.total_invoiced ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">Gross clinical billing</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
            <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider block">
              Total Collected
            </span>
            <div className="text-2xl font-bold text-emerald-600 mt-2">
              {reportQuery.isLoading ? (
                <Skeleton className="h-7 w-24" />
              ) : (
                `₹${(report?.total_collected ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">Realized liquid revenue</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
            <span className="text-xs font-semibold text-amber-600 uppercase tracking-wider block">
              Accounts Receivable
            </span>
            <div className="text-2xl font-bold text-amber-600 mt-2">
              {reportQuery.isLoading ? (
                <Skeleton className="h-7 w-24" />
              ) : (
                `₹${(report?.total_outstanding ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">Outstanding patient balances</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
            <span className="text-xs font-semibold text-blue-600 uppercase tracking-wider block">
              Collection Efficiency
            </span>
            <div className="text-2xl font-bold text-blue-600 mt-2">
              {reportQuery.isLoading ? (
                <Skeleton className="h-7 w-20" />
              ) : report && report.total_invoiced > 0 ? (
                `${Math.round((report.total_collected / report.total_invoiced) * 100)}%`
              ) : (
                "0%"
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">Realization against billed</p>
          </div>
        </div>

        {/* Detailed Breakdowns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Payment Method Distribution */}
          <div className="bg-white rounded-xl p-6 border border-slate-200/80 shadow-xs space-y-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-blue-600" />
              Collections by Payment Method
            </h3>

            {reportQuery.isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-full" />
              </div>
            ) : !report || Object.keys(report.collections_by_method).length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No collections recorded in this period.
              </div>
            ) : (
              <div className="space-y-3">
                {Object.entries(report.collections_by_method).map(
                  ([method, amount]) => {
                    const pct =
                      report.total_collected > 0
                        ? Math.round((amount / report.total_collected) * 100)
                        : 0;
                    return (
                      <div key={method} className="space-y-1">
                        <div className="flex justify-between text-xs font-medium">
                          <span className="text-slate-700">{method}</span>
                          <span className="font-bold text-slate-900">
                            ₹{amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })} ({pct}%)
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full bg-blue-600 rounded-full transition-all duration-300"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  }
                )}
              </div>
            )}
          </div>

          {/* Clinician Production Breakdown */}
          <div className="bg-white rounded-xl p-6 border border-slate-200/80 shadow-xs space-y-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Stethoscope className="w-4 h-4 text-emerald-600" />
              Clinician Production
            </h3>

            {reportQuery.isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-full" />
              </div>
            ) : !report || Object.keys(report.dentist_revenue).length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No clinician production data available.
              </div>
            ) : (
              <div className="space-y-3">
                {Object.entries(report.dentist_revenue).map(
                  ([dentistName, revenue]) => {
                    const pct =
                      report.total_invoiced > 0
                        ? Math.round((revenue / report.total_invoiced) * 100)
                        : 0;
                    return (
                      <div key={dentistName} className="space-y-1">
                        <div className="flex justify-between text-xs font-medium">
                          <span className="text-slate-700">{dentistName}</span>
                          <span className="font-bold text-slate-900">
                            ₹{revenue.toLocaleString("en-IN", { minimumFractionDigits: 2 })} ({pct}%)
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full bg-emerald-600 rounded-full transition-all duration-300"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  }
                )}
              </div>
            )}
          </div>
        </div>

        {/* Timeline Breakdown Table */}
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-indigo-600" />
              Period Breakdown
            </h3>
            <span className="text-xs text-slate-400">
              {report?.items.length || 0} periods tracked
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Period</th>
                  <th className="py-3 px-4 text-center">Invoices</th>
                  <th className="py-3 px-4 text-right">Invoiced (₹)</th>
                  <th className="py-3 px-4 text-right">Collected (₹)</th>
                  <th className="py-3 px-4 text-right">Outstanding (₹)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {report?.items.map((item) => (
                  <tr key={item.period} className="hover:bg-slate-50/50">
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      {item.period}
                    </td>
                    <td className="py-3 px-4 text-center text-slate-600 font-medium">
                      {item.invoices_count}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-slate-900">
                      ₹{item.total_invoiced.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-emerald-600">
                      ₹{item.total_collected.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-amber-600">
                      ₹{item.balance_outstanding.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowLeft,
  DollarSign,
  FileSpreadsheet,
  IndianRupee,
  Layers,
  PieChart,
  Printer,
  RefreshCw,
  Stethoscope,
} from "lucide-react";
import { api } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  ProcedureConsumptionReport,
  StockValuationReport,
} from "../types";

export default function InventoryReportsPage() {
  const valuationQuery = useQuery({
    queryKey: ["inventory-valuation-report"],
    queryFn: async () => {
      const res = await api.get<StockValuationReport>("/inventory/reports/valuation");
      return res.data;
    },
  });

  const procedureReportQuery = useQuery({
    queryKey: ["inventory-procedure-consumption-report"],
    queryFn: async () => {
      const res = await api.get<ProcedureConsumptionReport>("/inventory/reports/procedure-consumption");
      return res.data;
    },
  });

  const valReport = valuationQuery.data;
  const procReport = procedureReportQuery.data;

  return (
    <div className="space-y-8 pb-16">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/inventory" className="hover:text-slate-900 dark:hover:text-slate-100 flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Back to Inventory Hub
        </Link>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-400">
              <FileSpreadsheet className="h-6 w-6" />
            </span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Inventory & Consumption Intelligence</h1>
              <p className="text-sm text-muted-foreground">
                Stock asset valuation across 12 clinical categories and procedure material cost consumption analysis.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 transition"
        >
          <Printer className="h-4 w-4" />
          Print / Export Report
        </button>
      </div>

      {/* Stock Valuation Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold">Stock Asset Valuation by Category</h2>
            <p className="text-xs text-muted-foreground">
              Total warehouse and operatory material assets evaluated at current purchase costs.
            </p>
          </div>
        </div>

        {/* Valuation KPI cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <span className="text-xs font-medium text-muted-foreground uppercase">Total Stock Asset Valuation</span>
            <div className="mt-2 text-3xl font-bold text-teal-600 dark:text-teal-400">
              {valuationQuery.isLoading ? (
                <Skeleton className="h-9 w-32" />
              ) : (
                `₹${(valReport?.total_valuation ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Across all stocked categories</p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <span className="text-xs font-medium text-muted-foreground uppercase">Total Material SKUs</span>
            <div className="mt-2 text-3xl font-bold">
              {valuationQuery.isLoading ? <Skeleton className="h-9 w-20" /> : (valReport?.total_items ?? 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Active inventory master items</p>
          </div>
        </div>

        {/* Categories Valuation Table */}
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-slate-50/75 text-xs uppercase font-semibold text-slate-500 dark:bg-slate-800/50">
                <tr>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Item Count</th>
                  <th className="px-4 py-3">Total Units On Hand</th>
                  <th className="px-4 py-3">Category Valuation</th>
                  <th className="px-4 py-3 text-right">Share of Asset</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {valuationQuery.isLoading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <tr key={i}>
                      <td colSpan={5} className="px-4 py-3">
                        <Skeleton className="h-6 w-full" />
                      </td>
                    </tr>
                  ))
                ) : !valReport?.by_category || valReport.by_category.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground text-xs">
                      No stock valuation data available.
                    </td>
                  </tr>
                ) : (
                  valReport.by_category.map((cat) => {
                    const percent =
                      valReport.total_valuation > 0
                        ? ((cat.valuation / valReport.total_valuation) * 100).toFixed(1)
                        : "0.0";
                    return (
                      <tr key={cat.category} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                        <td className="px-4 py-3 font-semibold text-slate-900 dark:text-slate-100">
                          {cat.category}
                        </td>
                        <td className="px-4 py-3">{cat.item_count} items</td>
                        <td className="px-4 py-3 font-medium">{cat.total_quantity}</td>
                        <td className="px-4 py-3 font-bold text-teal-600 dark:text-teal-400">
                          ₹{cat.valuation.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className="inline-block rounded bg-slate-100 px-2 py-0.5 text-xs font-medium dark:bg-slate-800">
                            {percent}%
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Procedure Consumption Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-t pt-6">
          <div>
            <h2 className="text-lg font-bold">Procedure Material Consumption Analysis</h2>
            <p className="text-xs text-muted-foreground">
              Direct clinical material consumption costs automatically deducted during treatment appointments.
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Total Procedural Material Cost</span>
          <div className="mt-2 text-3xl font-bold text-rose-600 dark:text-rose-400">
            {procedureReportQuery.isLoading ? (
              <Skeleton className="h-9 w-32" />
            ) : (
              `₹${(procReport?.overall_cost ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-1">Direct clinical COGS (Cost of Goods Sold)</p>
        </div>

        {/* Procedures Breakdown Table */}
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-slate-50/75 text-xs uppercase font-semibold text-slate-500 dark:bg-slate-800/50">
                <tr>
                  <th className="px-4 py-3">Dental Procedure</th>
                  <th className="px-4 py-3">Completed Procedures</th>
                  <th className="px-4 py-3">Total Material Cost</th>
                  <th className="px-4 py-3 text-right">Average Cost / Treatment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {procedureReportQuery.isLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <tr key={i}>
                      <td colSpan={4} className="px-4 py-3">
                        <Skeleton className="h-6 w-full" />
                      </td>
                    </tr>
                  ))
                ) : !procReport?.procedures || procReport.procedures.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground text-xs">
                      No procedural consumption recorded yet. Material consumption recipes will reflect here when treatments are rendered.
                    </td>
                  </tr>
                ) : (
                  procReport.procedures.map((proc) => {
                    const avg =
                      proc.consumption_count > 0 ? proc.total_cost / proc.consumption_count : 0;
                    return (
                      <tr key={proc.procedure_name} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                        <td className="px-4 py-3 font-semibold text-slate-900 dark:text-slate-100">
                          {proc.procedure_name}
                        </td>
                        <td className="px-4 py-3">{proc.consumption_count} case(s)</td>
                        <td className="px-4 py-3 font-bold text-rose-600 dark:text-rose-400">
                          ₹{proc.total_cost.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-right font-medium">
                          ₹{avg.toFixed(2)}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}

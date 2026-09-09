"use client";

import { useState } from "react";
import {
  CircleDollarSign,
  TrendingUp,
  CreditCard,
  Building2,
  FileSpreadsheet,
  Download,
} from "lucide-react";
import { EnterpriseNav } from "../nav";

export default function ConsolidatedFinancialsPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <EnterpriseNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Consolidated Financial Rollups</h1>
            <p className="text-xs text-slate-500 mt-1">
              Multi-branch revenue totals, regional revenue distribution, insurance payouts, and tax aggregations.
            </p>
          </div>
          <button className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-xs transition-colors">
            <Download className="w-4 h-4" />
            Export Rollup (CSV)
          </button>
        </div>

        {/* High-level KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-medium text-slate-500">Total Network Invoiced</span>
            <div className="text-2xl font-bold text-slate-900 mt-2">₹42,85,000</div>
            <p className="text-xs text-emerald-600 mt-1 font-medium">+14.2% vs previous period</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-medium text-slate-500">Total Collected Revenue</span>
            <div className="text-2xl font-bold text-emerald-600 mt-2">₹38,40,000</div>
            <p className="text-xs text-slate-500 mt-1">89.6% collection velocity</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-medium text-slate-500">Insurance Remittance</span>
            <div className="text-2xl font-bold text-indigo-600 mt-2">₹12,20,000</div>
            <p className="text-xs text-slate-500 mt-1">From 4 primary TPAs</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-medium text-slate-500">Total GST Liability</span>
            <div className="text-2xl font-bold text-amber-600 mt-2">₹6,53,000</div>
            <p className="text-xs text-slate-500 mt-1">Consolidated 18% tax</p>
          </div>
        </div>

        {/* Branch Rollup Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="px-6 py-4 bg-slate-50/70 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Branch Performance Rollup
            </h2>
            <span className="text-xs text-slate-500">Currency: INR</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-500 font-semibold uppercase">
                  <th className="py-3 px-4">Clinic Branch</th>
                  <th className="py-3 px-4">Invoiced</th>
                  <th className="py-3 px-4">Collected</th>
                  <th className="py-3 px-4">Insurance Share</th>
                  <th className="py-3 px-4">Outstanding</th>
                  <th className="py-3 px-4">Tax (GST)</th>
                  <th className="py-3 px-4 text-right">Invoices</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-900">Central Flagship Clinic</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-900">₹18,50,000</td>
                  <td className="py-3.5 px-4 font-semibold text-emerald-600">₹17,20,000</td>
                  <td className="py-3.5 px-4 text-indigo-600">₹5,40,000</td>
                  <td className="py-3.5 px-4 text-slate-600">₹1,30,000</td>
                  <td className="py-3.5 px-4 text-slate-600">₹2,82,000</td>
                  <td className="py-3.5 px-4 text-right font-medium">184</td>
                </tr>

                <tr className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-900">Indiranagar Dental Lounge</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-900">₹14,20,000</td>
                  <td className="py-3.5 px-4 font-semibold text-emerald-600">₹12,80,000</td>
                  <td className="py-3.5 px-4 text-indigo-600">₹4,10,000</td>
                  <td className="py-3.5 px-4 text-slate-600">₹1,40,000</td>
                  <td className="py-3.5 px-4 text-slate-600">₹2,16,000</td>
                  <td className="py-3.5 px-4 text-right font-medium">142</td>
                </tr>

                <tr className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-900">Whitefield Specialty Wing</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-900">₹10,15,000</td>
                  <td className="py-3.5 px-4 font-semibold text-emerald-600">₹8,40,000</td>
                  <td className="py-3.5 px-4 text-indigo-600">₹2,70,000</td>
                  <td className="py-3.5 px-4 text-slate-600">₹1,75,000</td>
                  <td className="py-3.5 px-4 text-slate-600">₹1,55,000</td>
                  <td className="py-3.5 px-4 text-right font-medium">96</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

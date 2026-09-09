"use client";

import { useState } from "react";
import {
  DollarSign,
  Plus,
  CheckCircle2,
  FileText,
  Download,
  AlertCircle,
  Building,
  Calendar,
  X,
} from "lucide-react";
import { HRNav } from "../nav";
import { PayrollRun, Payslip } from "../types";

const mockRuns: PayrollRun[] = [
  {
    id: "pr-1",
    run_number: "PR-2026-08-4491",
    period_month: 8,
    period_year: 2026,
    status: "PAID",
    total_gross: 2980000,
    total_deductions: 312000,
    total_net: 2668000,
    total_employees: 44,
    created_at: "2026-08-31T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
  {
    id: "pr-2",
    run_number: "PR-2026-07-3912",
    period_month: 7,
    period_year: 2026,
    status: "PAID",
    total_gross: 2950000,
    total_deductions: 308000,
    total_net: 2642000,
    total_employees: 43,
    created_at: "2026-07-31T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
  },
];

export default function PayrollPage() {
  const [runs] = useState<PayrollRun[]>(mockRuns);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [month, setMonth] = useState(9);
  const [year, setYear] = useState(2026);

  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Payroll & Remuneration Engine</h1>
            <p className="text-sm text-slate-500 mt-1">
              Configurable salary calculations: Basic + HRA + Incentives + Overtime − PF − Prof. Tax − TDS − Unpaid Leaves
            </p>
          </div>
          <button
            onClick={() => setShowGenerateModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-semibold shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" /> Run Payroll Batch
          </button>
        </div>

        {/* Current Payroll Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-xs text-slate-500 font-semibold uppercase">Total Gross Billings</span>
            <div className="text-2xl font-bold text-slate-900 mt-1">₹29.80 Lakhs</div>
            <span className="text-xs text-emerald-600">44 Employees processed</span>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-xs text-slate-500 font-semibold uppercase">Statutory Deductions (PF/Tax)</span>
            <div className="text-2xl font-bold text-rose-600 mt-1">₹3.12 Lakhs</div>
            <span className="text-xs text-slate-400">PF + PT + TDS Withholding</span>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-xs text-slate-500 font-semibold uppercase">Total Net Disbursed</span>
            <div className="text-2xl font-bold text-teal-700 mt-1">₹26.68 Lakhs</div>
            <span className="text-xs text-slate-400">Direct Bank NEFT / RTGS</span>
          </div>
        </div>

        {/* Payroll Runs History */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-bold text-slate-900 text-sm">Historical Payroll Batches</h2>
          </div>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">Batch Number</th>
                <th className="py-3 px-4">Period</th>
                <th className="py-3 px-4">Headcount</th>
                <th className="py-3 px-4">Gross Disbursed</th>
                <th className="py-3 px-4">Deductions</th>
                <th className="py-3 px-4">Net Salary</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Register</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {runs.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-mono font-semibold text-slate-800">{r.run_number}</td>
                  <td className="py-3 px-4 text-slate-700 font-semibold">
                    {new Date(r.period_year, r.period_month - 1).toLocaleString("default", { month: "long" })}{" "}
                    {r.period_year}
                  </td>
                  <td className="py-3 px-4 text-slate-700">{r.total_employees} staff</td>
                  <td className="py-3 px-4 text-slate-900 font-medium">₹{r.total_gross.toLocaleString()}</td>
                  <td className="py-3 px-4 text-rose-600">₹{r.total_deductions.toLocaleString()}</td>
                  <td className="py-3 px-4 text-teal-800 font-bold">₹{r.total_net.toLocaleString()}</td>
                  <td className="py-3 px-4">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {r.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button className="inline-flex items-center gap-1 text-teal-600 hover:text-teal-700 font-semibold">
                      <Download className="w-3.5 h-3.5" /> Payslips
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Generate Modal */}
        {showGenerateModal && (
          <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200 relative">
              <button
                onClick={() => setShowGenerateModal(false)}
                className="absolute right-4 top-4 text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
              <h2 className="text-base font-bold text-slate-900 mb-2">Generate Monthly Payroll Batch</h2>
              <p className="text-xs text-slate-500 mb-4">
                The engine will aggregate approved attendance hours, calculate statutory PF and tax withholding, factor in approved procedure incentives, and deduct unpaid leaves.
              </p>
              <div className="grid grid-cols-2 gap-3 text-xs mb-4">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Month</label>
                  <select
                    value={month}
                    onChange={(e) => setMonth(Number(e.target.value))}
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                  >
                    <option value={8}>August</option>
                    <option value={9}>September</option>
                    <option value={10}>October</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Year</label>
                  <input
                    type="number"
                    value={year}
                    onChange={(e) => setYear(Number(e.target.value))}
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setShowGenerateModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    alert("Payroll batch generated successfully!");
                    setShowGenerateModal(false);
                  }}
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold text-xs"
                >
                  Calculate & Finalize Batch
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

"use client";

import { useState } from "react";
import {
  PlaneTakeoff,
  Plus,
  CheckCircle2,
  XCircle,
  Clock,
  Filter,
  UserCheck,
  Check,
  X,
} from "lucide-react";
import { HRNav } from "../nav";
import { LeaveRequest, LeaveStatus, LeaveType } from "../types";

const mockRequests: LeaveRequest[] = [
  {
    id: "req-1",
    clinic_id: "c1",
    employee_id: "e1",
    leave_type: "CASUAL",
    start_date: "2026-09-14",
    end_date: "2026-09-15",
    days_count: 2,
    reason: "Personal family event in Pune",
    status: "SUBMITTED",
    created_at: "2026-09-08T00:00:00Z",
    updated_at: "2026-09-08T00:00:00Z",
  },
  {
    id: "req-2",
    clinic_id: "c1",
    employee_id: "e2",
    leave_type: "SICK",
    start_date: "2026-09-11",
    end_date: "2026-09-12",
    days_count: 2,
    reason: "Viral flu, doctor prescribed rest",
    status: "MANAGER_APPROVED",
    manager_notes: "Recommended approval by Dr. Shah",
    manager_reviewed_at: "2026-09-08T15:00:00Z",
    created_at: "2026-09-08T00:00:00Z",
    updated_at: "2026-09-08T15:00:00Z",
  },
  {
    id: "req-3",
    clinic_id: "c1",
    employee_id: "e3",
    leave_type: "ANNUAL",
    start_date: "2026-09-20",
    end_date: "2026-09-25",
    days_count: 5,
    reason: "Annual vacation sanctioned earlier",
    status: "HR_APPROVED",
    manager_notes: "Approved",
    hr_notes: "Balance deducted from annual quota",
    created_at: "2026-09-01T00:00:00Z",
    updated_at: "2026-09-02T00:00:00Z",
  },
];

export default function LeaveManagementPage() {
  const [requests, setRequests] = useState<LeaveRequest[]>(mockRequests);
  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  const handleAction = (id: string, newStatus: LeaveStatus) => {
    setRequests(
      requests.map((r) => (r.id === id ? { ...r, status: newStatus } : r))
    );
  };

  const filtered = requests.filter((r) => filterStatus === "ALL" || r.status === filterStatus);

  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Two-Tier Leave Management Desk</h1>
            <p className="text-sm text-slate-500 mt-1">
              Workflow: Draft &rarr; Submitted &rarr; Manager Review &rarr; HR Approval &rarr; Automated Quota Deduction
            </p>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500 font-semibold">Filter:</span>
            <button
              onClick={() => setFilterStatus("ALL")}
              className={`px-3 py-1 rounded-md font-semibold transition-colors ${
                filterStatus === "ALL" ? "bg-teal-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterStatus("SUBMITTED")}
              className={`px-3 py-1 rounded-md font-semibold transition-colors ${
                filterStatus === "SUBMITTED" ? "bg-amber-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              Submitted
            </button>
            <button
              onClick={() => setFilterStatus("MANAGER_APPROVED")}
              className={`px-3 py-1 rounded-md font-semibold transition-colors ${
                filterStatus === "MANAGER_APPROVED" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              Manager Approved
            </button>
            <button
              onClick={() => setFilterStatus("HR_APPROVED")}
              className={`px-3 py-1 rounded-md font-semibold transition-colors ${
                filterStatus === "HR_APPROVED" ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              Sanctioned
            </button>
          </div>
        </div>

        {/* Requests Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">Staff Member</th>
                <th className="py-3 px-4">Leave Type</th>
                <th className="py-3 px-4">Dates & Duration</th>
                <th className="py-3 px-4">Reason</th>
                <th className="py-3 px-4">Workflow Status</th>
                <th className="py-3 px-4 text-right">Approval Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/50">
                  <td className="py-3.5 px-4 font-semibold text-slate-800">
                    Dr. Member #{r.employee_id.slice(0, 5)}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                      {r.leave_type}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-700">
                    {r.start_date} to {r.end_date} ({r.days_count} days)
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 max-w-xs truncate">{r.reason}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        r.status === "HR_APPROVED"
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : r.status === "MANAGER_APPROVED"
                          ? "bg-blue-50 text-blue-700 border border-blue-200"
                          : r.status === "REJECTED"
                          ? "bg-rose-50 text-rose-700 border border-rose-200"
                          : "bg-amber-50 text-amber-700 border border-amber-200"
                      }`}
                    >
                      {r.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    {r.status === "SUBMITTED" && (
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleAction(r.id, "MANAGER_APPROVED")}
                          className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold text-[11px]"
                        >
                          Manager Sign-off
                        </button>
                        <button
                          onClick={() => handleAction(r.id, "REJECTED")}
                          className="px-2 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded font-semibold text-[11px]"
                        >
                          Reject
                        </button>
                      </div>
                    )}
                    {r.status === "MANAGER_APPROVED" && (
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleAction(r.id, "HR_APPROVED")}
                          className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-semibold text-[11px]"
                        >
                          HR Sanction & Deduct
                        </button>
                        <button
                          onClick={() => handleAction(r.id, "REJECTED")}
                          className="px-2 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded font-semibold text-[11px]"
                        >
                          Reject
                        </button>
                      </div>
                    )}
                    {(r.status === "HR_APPROVED" || r.status === "REJECTED") && (
                      <span className="text-slate-400 italic">Action Complete</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}

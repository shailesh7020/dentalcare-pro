"use client";

import { useState } from "react";
import {
  Clock,
  Calendar,
  CheckCircle2,
  AlertCircle,
  QrCode,
  Search,
  Filter,
  ArrowRight,
  UserCheck,
} from "lucide-react";
import { HRNav } from "../nav";
import { AttendanceRecord } from "../types";

const mockRecords: AttendanceRecord[] = [
  {
    id: "att-1",
    clinic_id: "c1",
    employee_id: "e1",
    date: "2026-09-09",
    check_in_time: "2026-09-09T08:55:00Z",
    check_out_time: null,
    entry_method: "QR_CODE",
    status: "PRESENT",
    break_minutes: 0,
    overtime_minutes: 0,
    is_late: false,
    late_minutes: 0,
    is_early_departure: false,
    early_departure_minutes: 0,
    created_at: "2026-09-09T08:55:00Z",
    updated_at: "2026-09-09T08:55:00Z",
  },
  {
    id: "att-2",
    clinic_id: "c1",
    employee_id: "e2",
    date: "2026-09-09",
    check_in_time: "2026-09-09T09:25:00Z", // Late
    check_out_time: null,
    entry_method: "BIOMETRIC",
    status: "LATE",
    break_minutes: 0,
    overtime_minutes: 0,
    is_late: true,
    late_minutes: 25,
    is_early_departure: false,
    early_departure_minutes: 0,
    created_at: "2026-09-09T09:25:00Z",
    updated_at: "2026-09-09T09:25:00Z",
  },
  {
    id: "att-3",
    clinic_id: "c1",
    employee_id: "e3",
    date: "2026-09-09",
    check_in_time: "2026-09-09T08:50:00Z",
    check_out_time: "2026-09-09T18:00:00Z",
    entry_method: "MANUAL",
    status: "PRESENT",
    break_minutes: 45,
    overtime_minutes: 60,
    is_late: false,
    late_minutes: 0,
    is_early_departure: false,
    early_departure_minutes: 0,
    created_at: "2026-09-09T08:50:00Z",
    updated_at: "2026-09-09T18:00:00Z",
  },
];

export default function AttendancePage() {
  const [records] = useState<AttendanceRecord[]>(mockRecords);
  const [showQrModal, setShowQrModal] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Real-Time Attendance & Biometrics</h1>
            <p className="text-sm text-slate-500 mt-1">
              Live check-ins, QR code scans, biometric synchronizer & overtime logs
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowQrModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-semibold shadow-xs transition-colors"
            >
              <QrCode className="w-4 h-4" /> Generate Clinic QR Scanner
            </button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-xs text-slate-500 font-semibold uppercase">Present Today</span>
            <div className="text-2xl font-bold text-slate-900 mt-1">30 Clinicians</div>
            <span className="text-xs text-emerald-600">93.8% on-time attendance</span>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-xs text-slate-500 font-semibold uppercase">Late Arrivals</span>
            <div className="text-2xl font-bold text-amber-600 mt-1">2 Staff</div>
            <span className="text-xs text-slate-400">Avg delay: 20 mins</span>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-xs text-slate-500 font-semibold uppercase">Overtime Accumulated</span>
            <div className="text-2xl font-bold text-indigo-600 mt-1">14.5 Hours</div>
            <span className="text-xs text-slate-400">Past 7 days across 4 staff</span>
          </div>
        </div>

        {/* Attendance Log Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-bold text-slate-900 text-sm">Today&apos;s Clock-In Roster</h2>
            <span className="text-xs text-slate-500">Auto-synced with Clinic Biometrics</span>
          </div>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">Staff Member</th>
                <th className="py-3 px-4">Clock In</th>
                <th className="py-3 px-4">Clock Out</th>
                <th className="py-3 px-4">Entry Device</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Overtime</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {records.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-semibold text-slate-800">
                    Dr. Member #{r.employee_id.slice(0, 5)}
                  </td>
                  <td className="py-3 px-4 text-slate-700">
                    {r.check_in_time ? new Date(r.check_in_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—"}
                  </td>
                  <td className="py-3 px-4 text-slate-700">
                    {r.check_out_time ? new Date(r.check_out_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Active"}
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono text-[10px]">
                      {r.entry_method}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        r.status === "PRESENT"
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : "bg-amber-50 text-amber-700 border border-amber-200"
                      }`}
                    >
                      {r.status} {r.is_late ? `(+${r.late_minutes}m)` : ""}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-medium text-slate-700">
                    {r.overtime_minutes > 0 ? `${r.overtime_minutes} mins` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* QR Scanner Modal */}
        {showQrModal && (
          <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl max-w-sm w-full p-6 text-center shadow-xl border border-slate-200">
              <h3 className="text-base font-bold text-slate-900 mb-2">Clinic Clock-In QR Code</h3>
              <p className="text-xs text-slate-500 mb-4">
                Staff can scan this code using their mobile Employee Self-Service portal to punch in.
              </p>
              <div className="w-48 h-48 mx-auto bg-slate-100 border-2 border-dashed border-teal-500 rounded-xl flex items-center justify-center text-teal-600 mb-4">
                <QrCode className="w-32 h-32" />
              </div>
              <span className="text-[11px] font-mono text-slate-400 block mb-4">CLINIC-ID: BRIGHTSMILE-MAIN</span>
              <button
                onClick={() => setShowQrModal(false)}
                className="w-full py-2 bg-slate-800 text-white rounded-lg text-xs font-semibold hover:bg-slate-700"
              >
                Close QR Display
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

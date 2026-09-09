"use client";

import { useState } from "react";
import {
  UserCheck,
  Clock,
  PlaneTakeoff,
  DollarSign,
  Download,
  Calendar,
  CheckCircle2,
  QrCode,
  ShieldCheck,
  FileText,
} from "lucide-react";
import { HRNav } from "../nav";

export default function EmployeeSelfServicePage() {
  const [clockedIn, setClockedIn] = useState(false);
  const [clockTime, setClockTime] = useState<string | null>(null);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [leaveType, setLeaveType] = useState("CASUAL");
  const [leaveDays, setLeaveDays] = useState(1);
  const [reason, setReason] = useState("");

  const handleClockIn = () => {
    const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    setClockedIn(true);
    setClockTime(timeStr);
  };

  const handleClockOut = () => {
    setClockedIn(false);
    setClockTime(null);
    alert("Successfully clocked out for the day!");
  };

  const handleLeaveSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    alert(`Leave request for ${leaveDays} day(s) submitted to your clinic manager!`);
    setShowLeaveModal(false);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Profile Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs mb-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-teal-600 text-white font-bold text-xl flex items-center justify-center shadow-sm">
                AS
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Dr. Ananya Shah</h1>
                <p className="text-xs text-slate-500">
                  Chief Prosthodontist & Clinic Admin · <span className="font-mono text-slate-400">EMP-1001</span>
                </p>
                <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Staff Self-Service Active
                </span>
              </div>
            </div>

            {/* Quick Clock-In Widget */}
            <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl text-xs space-y-2 w-full sm:w-72">
              <span className="font-semibold text-slate-700 block">Today&apos;s Attendance Punch</span>
              {clockedIn ? (
                <div>
                  <div className="flex items-center gap-1.5 text-emerald-700 font-bold mb-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Clocked In at {clockTime}
                  </div>
                  <button
                    onClick={handleClockOut}
                    className="w-full py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg font-semibold"
                  >
                    Punch Clock Out
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleClockIn}
                  className="w-full py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold shadow-xs"
                >
                  Punch Clock In (Mobile / GPS)
                </button>
              )}
            </div>
          </div>
        </div>

        {/* ESS Actions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 text-xs">
          {/* Leave Quota Card */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <PlaneTakeoff className="w-4 h-4 text-teal-600" /> My Leave Quota
              </h2>
              <button
                onClick={() => setShowLeaveModal(true)}
                className="text-teal-600 font-semibold hover:underline"
              >
                + Apply Leave
              </button>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center pt-2">
              <div className="p-2.5 bg-slate-50 rounded-lg">
                <span className="text-slate-400 block text-[10px]">Casual</span>
                <span className="font-bold text-slate-900 text-base">8</span>
                <span className="text-[10px] text-slate-400 block">left</span>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-lg">
                <span className="text-slate-400 block text-[10px]">Sick</span>
                <span className="font-bold text-slate-900 text-base">9</span>
                <span className="text-[10px] text-slate-400 block">left</span>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-lg">
                <span className="text-slate-400 block text-[10px]">Annual</span>
                <span className="font-bold text-slate-900 text-base">12</span>
                <span className="text-[10px] text-slate-400 block">left</span>
              </div>
            </div>
          </div>

          {/* Payslips Card */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-teal-600" /> Recent Payslips
            </h2>
            <div className="divide-y divide-slate-100">
              <div className="py-2 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-800 block">August 2026</span>
                  <span className="text-[11px] text-slate-400">Net: ₹1,90,300</span>
                </div>
                <button className="inline-flex items-center gap-1 text-teal-600 font-semibold">
                  <Download className="w-3.5 h-3.5" /> PDF
                </button>
              </div>
              <div className="py-2 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-800 block">July 2026</span>
                  <span className="text-[11px] text-slate-400">Net: ₹1,87,800</span>
                </div>
                <button className="inline-flex items-center gap-1 text-teal-600 font-semibold">
                  <Download className="w-3.5 h-3.5" /> PDF
                </button>
              </div>
            </div>
          </div>

          {/* Credentials Status */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-teal-600" /> My Dental License
            </h2>
            <div className="p-3 bg-emerald-50/50 border border-emerald-200 rounded-lg">
              <span className="font-bold text-emerald-900 block">DCI Registration Verified</span>
              <span className="font-mono text-emerald-700">DCI-MH-44821</span>
              <p className="text-[11px] text-emerald-600 mt-1">Valid until April 2027 · No immediate action needed</p>
            </div>
          </div>
        </div>

        {/* Modal: Apply Leave */}
        {showLeaveModal && (
          <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200 text-xs">
              <h2 className="text-base font-bold text-slate-900 mb-3">Apply for Sanctioned Leave</h2>
              <form onSubmit={handleLeaveSubmit} className="space-y-3">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Leave Category</label>
                  <select
                    value={leaveType}
                    onChange={(e) => setLeaveType(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                  >
                    <option value="CASUAL">Casual Leave (8 available)</option>
                    <option value="SICK">Sick Leave (9 available)</option>
                    <option value="ANNUAL">Annual Leave (12 available)</option>
                    <option value="UNPAID">Unpaid Leave</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Duration (Days)</label>
                  <input
                    required
                    type="number"
                    min={1}
                    max={15}
                    value={leaveDays}
                    onChange={(e) => setLeaveDays(Number(e.target.value))}
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Reason</label>
                  <textarea
                    required
                    rows={3}
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                    placeholder="Brief description for manager approval..."
                  />
                </div>
                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowLeaveModal(false)}
                    className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold"
                  >
                    Submit Request
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

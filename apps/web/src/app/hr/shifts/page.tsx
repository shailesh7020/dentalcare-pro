"use client";

import { useState } from "react";
import {
  CalendarDays,
  Plus,
  Clock,
  AlertTriangle,
  Users,
  CheckCircle2,
  X,
} from "lucide-react";
import { HRNav } from "../nav";
import { StaffSchedule, WorkShift } from "../types";

const mockShifts: WorkShift[] = [
  { id: "s1", name: "Morning General", code: "MORN", start_time: "09:00", end_time: "14:00", break_minutes: 30, shift_type: "REGULAR", is_active: true, created_at: "", updated_at: "" },
  { id: "s2", name: "Evening Ortho & Implants", code: "EVE", start_time: "14:30", end_time: "20:30", break_minutes: 30, shift_type: "REGULAR", is_active: true, created_at: "", updated_at: "" },
  { id: "s3", name: "Full Day Operatory", code: "FULL", start_time: "09:00", end_time: "18:00", break_minutes: 60, shift_type: "REGULAR", is_active: true, created_at: "", updated_at: "" },
  { id: "s4", name: "Emergency On-Call", code: "EMERG", start_time: "20:00", end_time: "08:00", break_minutes: 60, shift_type: "EMERGENCY", is_active: true, created_at: "", updated_at: "" },
];

export default function ShiftPlannerPage() {
  const [shifts] = useState<WorkShift[]>(mockShifts);
  const [showModal, setShowModal] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Workforce Shift Planner & Rostering</h1>
            <p className="text-sm text-slate-500 mt-1">
              Chair assignments, rotating shifts, split shifts & automated double-booking prevention
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-semibold shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" /> Schedule Shift
          </button>
        </div>

        {/* Shift Templates Card */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {shifts.map((s) => (
            <div key={s.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-slate-900 text-xs">{s.name}</span>
                <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-teal-50 text-teal-700 font-bold">
                  {s.code}
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-600 text-xs">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>{s.start_time} – {s.end_time}</span>
              </div>
              <div className="mt-2 text-[11px] text-slate-400">
                Break: {s.break_minutes} mins · {s.shift_type}
              </div>
            </div>
          ))}
        </div>

        {/* Weekly Operatory Matrix */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <CalendarDays className="w-4 h-4 text-teal-600" /> Operatory Chair Schedule (This Week)
            </h2>
            <span className="text-xs text-slate-400">3 Operatory Chairs Active</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3 border border-slate-100 rounded-lg bg-slate-50/50 flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-800 block">Operatory Chair 1 (Prostho / Surgery)</span>
                <span className="text-slate-500">09:00 - 14:00: Dr. Ananya Shah (Confirmed)</span>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                OPTIMAL
              </span>
            </div>

            <div className="p-3 border border-slate-100 rounded-lg bg-slate-50/50 flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-800 block">Operatory Chair 2 (Endodontics)</span>
                <span className="text-slate-500">09:00 - 14:00: Dr. Rohan Verma (Confirmed)</span>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                OPTIMAL
              </span>
            </div>

            <div className="p-3 border border-slate-100 rounded-lg bg-slate-50/50 flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-800 block">Operatory Chair 3 (Orthodontics)</span>
                <span className="text-slate-500">14:30 - 20:30: Dr. Kavita Rao (Roaming Visit)</span>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                SPECIALIST
              </span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

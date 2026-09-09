"use client";

import React, { useState } from "react";
import {
  Smile,
  CheckCircle2,
  Clock,
  Calendar,
  User,
  ShieldCheck,
  Info,
} from "lucide-react";
import { PortalShell } from "../portal-shell";
import type { PortalToothRead, PortalTreatmentRead } from "../types";

const mockTreatments: PortalTreatmentRead[] = [
  {
    id: "trt-1",
    treatment_plan_name: "Comprehensive Restorative Plan - Quadrant 1 & 2",
    status: "IN_PROGRESS",
    start_date: "2026-08-15",
    dentist_name: "Dr. David Tennant",
    notes: "Composite restorations on #14 and #24. Follow-up review scheduled.",
  },
  {
    id: "trt-2",
    treatment_plan_name: "Periodontal Prophylaxis & Ultrasonic Scaling",
    status: "COMPLETED",
    start_date: "2026-02-10",
    completion_date: "2026-02-10",
    dentist_name: "Dr. David Tennant",
    notes: "Supragingival scaling completed. Oral hygiene instructions demonstrated.",
  },
];

const mockTeeth: PortalToothRead[] = [
  { tooth_number: "18", condition: "HEALTHY", color: "#10B981" },
  { tooth_number: "17", condition: "HEALTHY", color: "#10B981" },
  { tooth_number: "16", condition: "FILLING", color: "#3B82F6", notes: "MOD Composite Restoration" },
  { tooth_number: "15", condition: "HEALTHY", color: "#10B981" },
  { tooth_number: "14", condition: "FILLING", color: "#3B82F6", notes: "DO Resin Composite" },
  { tooth_number: "13", condition: "HEALTHY", color: "#10B981" },
  { tooth_number: "12", condition: "HEALTHY", color: "#10B981" },
  { tooth_number: "11", condition: "HEALTHY", color: "#10B981" },
  { tooth_number: "21", condition: "HEALTHY", color: "#10B981" },
  { tooth_number: "22", condition: "HEALTHY", color: "#10B981" },
  { tooth_number: "23", condition: "HEALTHY", color: "#10B981" },
  { tooth_number: "24", condition: "ROOT_CANAL", color: "#8B5CF6", notes: "Obturated canal + Core build-up" },
  { tooth_number: "25", condition: "HEALTHY", color: "#10B981" },
  { tooth_number: "26", condition: "CROWN", color: "#F59E0B", notes: "Zirconia Porcelain Crown" },
  { tooth_number: "27", condition: "HEALTHY", color: "#10B981" },
  { tooth_number: "28", condition: "MISSING", color: "#64748B" },
];

export default function PortalTreatmentsPage() {
  const [treatments] = useState(mockTreatments);
  const [teeth] = useState(mockTeeth);
  const [selectedTooth, setSelectedTooth] = useState<PortalToothRead | null>(null);

  return (
    <PortalShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Treatments & Interactive Odontogram</h1>
          <p className="text-xs text-slate-500">Track treatment plans and explore your complete dental chart</p>
        </div>
      </div>

      {/* Odontogram Visual Card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Your Dental Chart (FDI Numbering)</h2>
            <p className="text-xs text-slate-500">Click any tooth to view diagnosis and restorations</p>
          </div>
          <div className="flex items-center gap-3 text-xs flex-wrap">
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-emerald-500" /> Healthy</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-blue-500" /> Filled</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-purple-500" /> Root Canal</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-amber-500" /> Crown</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-slate-500" /> Missing</span>
          </div>
        </div>

        {/* Teeth Grid Upper Arch */}
        <div className="bg-slate-50 p-6 rounded-xl border border-slate-100 flex flex-wrap justify-center gap-2">
          {teeth.map((t) => {
            const isSelected = selectedTooth?.tooth_number === t.tooth_number;
            return (
              <button
                key={t.tooth_number}
                onClick={() => setSelectedTooth(t)}
                className={`p-3 rounded-xl border flex flex-col items-center justify-center min-w-[54px] transition ${
                  isSelected
                    ? "border-teal-600 bg-teal-50 ring-2 ring-teal-500/20"
                    : "border-slate-200 bg-white hover:bg-slate-100"
                }`}
              >
                <div
                  className="w-5 h-5 rounded-full mb-1 flex items-center justify-center text-[10px] text-white font-bold"
                  style={{ backgroundColor: t.color || "#10B981" }}
                >
                  🦷
                </div>
                <span className="text-xs font-bold text-slate-900">#{t.tooth_number}</span>
                <span className="text-[9px] text-slate-400 truncate max-w-[48px]">{t.condition}</span>
              </button>
            );
          })}
        </div>

        {/* Selected Tooth Detail Panel */}
        {selectedTooth && (
          <div className="mt-4 p-4 bg-teal-50/60 border border-teal-200 rounded-xl text-xs flex items-center justify-between">
            <div>
              <strong className="text-teal-900 text-sm">Tooth #{selectedTooth.tooth_number}</strong>
              <span className="ml-2 font-semibold text-slate-700">Status: {selectedTooth.condition}</span>
              {selectedTooth.notes && <p className="text-slate-600 mt-1">{selectedTooth.notes}</p>}
            </div>
            <button
              onClick={() => setSelectedTooth(null)}
              className="text-xs text-teal-700 font-bold hover:underline"
            >
              Close
            </button>
          </div>
        )}
      </div>

      {/* Treatments List */}
      <div className="space-y-4">
        <h2 className="text-base font-bold text-slate-900">Clinical Treatment History</h2>
        {treatments.map((t) => (
          <div key={t.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">{t.treatment_plan_name}</h3>
              <span
                className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold ${
                  t.status === "COMPLETED" ? "bg-emerald-100 text-emerald-800" : "bg-blue-100 text-blue-800"
                }`}
              >
                {t.status}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span>Attending: <strong>{t.dentist_name}</strong></span>
              <span>Started: {t.start_date}</span>
              {t.completion_date && <span>Completed: {t.completion_date}</span>}
            </div>
            {t.notes && <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg">{t.notes}</p>}
          </div>
        ))}
      </div>
    </PortalShell>
  );
}

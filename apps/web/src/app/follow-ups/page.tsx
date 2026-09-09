"use client";

import Link from "next/link";
import React, { useState } from "react";
import {
  CalendarClock,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
  Phone,
  Send,
  Calendar,
  Filter,
  RefreshCw,
  Clock,
  Sparkles,
} from "lucide-react";

interface RecallItem {
  id: string;
  patient_name: string;
  patient_phone: string;
  procedure_type: "ROOT_CANAL" | "EXTRACTION" | "SCALING" | "IMPLANT" | "CROWN" | "ORTHODONTICS";
  tooth_number?: string;
  completed_date: string;
  recall_due_date: string;
  days_overdue: number;
  status: "DUE" | "CONTACTED" | "BOOKED" | "OVERDUE";
  recommended_action: string;
}

const mockRecalls: RecallItem[] = [
  {
    id: "rc-1",
    patient_name: "Donna Noble",
    patient_phone: "+91 99112 23344",
    procedure_type: "ROOT_CANAL",
    tooth_number: "14",
    completed_date: "2026-03-08",
    recall_due_date: "2026-09-08",
    days_overdue: 0,
    status: "DUE",
    recommended_action: "6-Month Endodontic periapical radiograph review",
  },
  {
    id: "rc-2",
    patient_name: "Wilfred Mott",
    patient_phone: "+91 99887 66554",
    procedure_type: "EXTRACTION",
    tooth_number: "38",
    completed_date: "2026-09-01",
    recall_due_date: "2026-09-08",
    days_overdue: 0,
    status: "DUE",
    recommended_action: "7-Day Post-op suture removal & dry socket check",
  },
  {
    id: "rc-3",
    patient_name: "Rose Tyler",
    patient_phone: "+91 98765 43210",
    procedure_type: "SCALING",
    completed_date: "2026-02-15",
    recall_due_date: "2026-08-15",
    days_overdue: 24,
    status: "OVERDUE",
    recommended_action: "6-Month Dental Prophylaxis & Calculus Debridement",
  },
  {
    id: "rc-4",
    patient_name: "Martha Jones",
    patient_phone: "+91 91234 56789",
    procedure_type: "IMPLANT",
    tooth_number: "19",
    completed_date: "2026-06-08",
    recall_due_date: "2026-09-08",
    days_overdue: 0,
    status: "CONTACTED",
    recommended_action: "3-Month Osseointegration torque test & impression",
  },
];

export default function FollowUpsPage() {
  const [recalls, setRecalls] = useState(mockRecalls);
  const [filterType, setFilterType] = useState<string>("ALL");
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const handleSendReminder = (id: string, name: string) => {
    setRecalls(
      recalls.map((r) => (r.id === id ? { ...r, status: "CONTACTED" } : r))
    );
    setActionNotice(`WhatsApp recall notice dispatched to ${name}.`);
    setTimeout(() => setActionNotice(null), 3500);
  };

  const handleBookVisit = (id: string, name: string) => {
    setRecalls(
      recalls.map((r) => (r.id === id ? { ...r, status: "BOOKED" } : r))
    );
    setActionNotice(`Recall consultation appointment booked for ${name}.`);
    setTimeout(() => setActionNotice(null), 3500);
  };

  const filtered = recalls.filter((r) => {
    if (filterType !== "ALL" && r.procedure_type !== filterType) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-sm font-medium text-slate-500 hover:text-slate-900">
              ← Dashboard
            </Link>
            <span className="text-slate-300">/</span>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-teal-50 text-teal-700 rounded-lg">
                <CalendarClock className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-900">Procedure Recall & Retention Engine</h1>
                <p className="text-xs text-slate-500">
                  Automated post-treatment follow-up scheduler across RCT, Extractions, Implants, and Scaling
                </p>
              </div>
            </div>
          </div>

          <Link
            href="/notifications"
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-lg transition"
          >
            <Send className="w-3.5 h-3.5" /> Broadcast Center
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {actionNotice && (
          <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl flex items-center gap-2 text-sm font-medium animate-fade-in">
            <CheckCircle2 className="w-4 h-4" /> {actionNotice}
          </div>
        )}

        {/* Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-medium text-slate-500">Due Recalls This Week</span>
            <div className="text-2xl font-bold text-slate-900 mt-1">12</div>
            <span className="text-[11px] text-teal-600 font-semibold">4 Root Canal · 5 Scaling</span>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-medium text-slate-500">Overdue Follow-ups</span>
            <div className="text-2xl font-bold text-rose-600 mt-1">3</div>
            <span className="text-[11px] text-rose-500 font-semibold">&gt; 14 days overdue</span>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-medium text-slate-500">Contacted / In-Progress</span>
            <div className="text-2xl font-bold text-amber-600 mt-1">8</div>
            <span className="text-[11px] text-amber-600 font-semibold">WhatsApp messages sent</span>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-medium text-slate-500">Conversion Rate</span>
            <div className="text-2xl font-bold text-emerald-600 mt-1">78%</div>
            <span className="text-[11px] text-emerald-600 font-semibold">Recall to booked chair</span>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm mb-6 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-semibold text-slate-700">Filter Procedure:</span>
            {(["ALL", "ROOT_CANAL", "EXTRACTION", "SCALING", "IMPLANT"] as const).map((proc) => (
              <button
                key={proc}
                onClick={() => setFilterType(proc)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
                  filterType === proc
                    ? "bg-slate-900 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {proc.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>

        {/* Recalls Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
          <div className="p-4 bg-slate-50 flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <span>Patient & Procedure</span>
            <span>Due Date</span>
            <span>Recommended Clinical Action</span>
            <span>Status</span>
            <span className="text-right">Actions</span>
          </div>

          {filtered.map((r) => (
            <div key={r.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition gap-4">
              <div className="w-64 shrink-0">
                <h4 className="text-sm font-bold text-slate-900">{r.patient_name}</h4>
                <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
                  <span className="font-semibold text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded">
                    {r.procedure_type.replace("_", " ")}
                  </span>
                  {r.tooth_number && <span>Tooth #{r.tooth_number}</span>}
                </div>
              </div>

              <div className="text-xs text-slate-600 shrink-0 w-32">
                <span className="font-semibold">{r.recall_due_date}</span>
                {r.days_overdue > 0 && (
                  <p className="text-rose-600 font-bold text-[11px] mt-0.5">
                    {r.days_overdue} days overdue
                  </p>
                )}
              </div>

              <div className="text-xs text-slate-700 flex-1">
                {r.recommended_action}
              </div>

              <div className="shrink-0 w-24">
                <span
                  className={`text-xs px-2.5 py-1 rounded-full font-semibold ${
                    r.status === "BOOKED"
                      ? "bg-emerald-100 text-emerald-800"
                      : r.status === "OVERDUE"
                      ? "bg-rose-100 text-rose-800"
                      : r.status === "CONTACTED"
                      ? "bg-blue-100 text-blue-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {r.status}
                </span>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {r.status !== "BOOKED" && (
                  <>
                    <button
                      onClick={() => handleSendReminder(r.id, r.patient_name)}
                      className="px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-lg transition flex items-center gap-1"
                      title="Send WhatsApp Recall Message"
                    >
                      <MessageSquare className="w-3.5 h-3.5" /> Remind
                    </button>
                    <button
                      onClick={() => handleBookVisit(r.id, r.patient_name)}
                      className="px-3 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm transition flex items-center gap-1"
                    >
                      <Calendar className="w-3.5 h-3.5" /> Book Chair
                    </button>
                  </>
                )}
                {r.status === "BOOKED" && (
                  <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" /> Booked
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

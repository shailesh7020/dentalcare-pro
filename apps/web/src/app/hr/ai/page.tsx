"use client";

import { useState } from "react";
import {
  Sparkles,
  Users,
  AlertTriangle,
  Clock,
  CheckCircle2,
  TrendingUp,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";
import { HRNav } from "../nav";

export default function AIWorkforceInsightsPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200 mb-2">
              <Sparkles className="w-3.5 h-3.5" /> AI Workforce Assistant
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Predictive Workforce & Staffing Intelligence</h1>
            <p className="text-sm text-slate-500 mt-1">
              Automated chairside staffing recommendations, clinician burnout indicators, schedule audits & credential alerts
            </p>
          </div>
        </div>

        {/* AI Insight Modules */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          {/* Staffing Recommendation */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Users className="w-4 h-4 text-teal-600" /> Operatory Staffing Optimization
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                Action Advised
              </span>
            </div>
            <p className="text-slate-600">
              AI compared booked patient procedures against rostered dentists for Saturday, 12 September:
            </p>
            <div className="p-3 bg-amber-50/60 border border-amber-200 rounded-lg space-y-1">
              <span className="font-bold text-amber-900 block">Morning Slot: 14 Bookings across 3 Chairs</span>
              <p className="text-amber-800">Only 1 dentist rostered. Understaffing ratio detected. Recommend rostering at least 2 dentists and 2 assistants to prevent patient wait times.</p>
            </div>
          </div>

          {/* Clinician Burnout Radar */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-600" /> Clinician Burnout Radar
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                1 Clinician Flagged
              </span>
            </div>
            <p className="text-slate-600">
              Evaluates overtime accumulation, high-volume surgical density, and lack of consecutive rest intervals:
            </p>
            <div className="p-3 bg-rose-50/60 border border-rose-200 rounded-lg space-y-1">
              <span className="font-bold text-rose-900 block">Dr. Rohan Verma (Endodontist)</span>
              <p className="text-rose-800">Accumulated 28 overtime hours in past 30 days with 6 consecutive clinic days. Recommended to reassign Sunday on-call shifts.</p>
            </div>
          </div>

          {/* Specialty Leave Conflict */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Clock className="w-4 h-4 text-indigo-600" /> Specialty Overlap Auditor
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                Resolved
              </span>
            </div>
            <p className="text-slate-600">
              Cross-references simultaneous leave requests in the same dental specialty:
            </p>
            <div className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-lg space-y-1">
              <span className="font-bold text-emerald-900 block">Orthodontics & Pedodontics Coverage Stable</span>
              <p className="text-emerald-800">No overlapping leaves among solo specialists. Adequate clinical coverage confirmed.</p>
            </div>
          </div>

          {/* License & Credential Radar */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" /> Credential Expiration Radar
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                1 Renewal Due
              </span>
            </div>
            <p className="text-slate-600">
              Tracks Dental Council registrations and mandatory CE certifications:
            </p>
            <div className="p-3 bg-amber-50/60 border border-amber-200 rounded-lg space-y-1">
              <span className="font-bold text-amber-900 block">Dr. Rohan Verma · License DCI-MH-51209</span>
              <p className="text-amber-800">State council license expires in 36 days (15 Oct 2026). Renewal reminder dispatched.</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

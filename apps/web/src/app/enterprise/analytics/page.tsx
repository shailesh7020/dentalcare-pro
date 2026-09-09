"use client";

import { useState } from "react";
import {
  TrendingUp,
  Sparkles,
  Award,
  Users2,
  BrainCircuit,
  ArrowUpRight,
  Target,
  CheckCircle2,
} from "lucide-react";
import { EnterpriseNav } from "../nav";

export default function AIAnalyticsPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <EnterpriseNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-900">AI Enterprise Analytics & Benchmarking</h1>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 border border-purple-200">
                AI Advisory Engine
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Objective multi-clinic benchmarking, dentist chairside yield analysis, and quarterly revenue forecasting.
            </p>
          </div>
        </div>

        {/* AI Network Health Summary */}
        <div className="p-6 bg-gradient-to-r from-indigo-900 via-indigo-800 to-purple-900 text-white rounded-2xl shadow-md space-y-3">
          <div className="flex items-center gap-2 text-indigo-200">
            <BrainCircuit className="w-5 h-5" />
            <span className="text-xs font-semibold uppercase tracking-wider">Corporate Health Synthesis</span>
          </div>
          <p className="text-sm font-medium leading-relaxed max-w-4xl">
            Enterprise network encompasses 12 branches with a network average benchmark efficiency of 87.4/100.
            Top performers Central Flagship and Indiranagar exhibit superior collection velocity and high treatment acceptance rates.
            Consolidated consumable pooling has saved an estimated 11.4% in procurement costs this quarter.
          </p>
        </div>

        {/* 3-Month AI Revenue Forecasts */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
              <h2 className="text-sm font-bold text-slate-900">Forward Revenue Projections (Q4 2026)</h2>
            </div>
            <span className="text-xs text-slate-500">Linear Trend + Seasonal Weighting</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 text-xs space-y-2">
              <div className="text-slate-500 font-medium">Month 1 (October 2026)</div>
              <div className="text-xl font-bold text-slate-900">₹45.2 Lakh</div>
              <div className="text-[11px] text-emerald-600 font-semibold">+5.5% Projected Growth</div>
              <div className="text-[10px] text-slate-400">Confidence Band: ₹42.8L - ₹48.0L</div>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 text-xs space-y-2">
              <div className="text-slate-500 font-medium">Month 2 (November 2026)</div>
              <div className="text-xl font-bold text-slate-900">₹48.6 Lakh</div>
              <div className="text-[11px] text-emerald-600 font-semibold">+13.4% Projected Growth</div>
              <div className="text-[10px] text-slate-400">Confidence Band: ₹45.5L - ₹51.8L</div>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 text-xs space-y-2">
              <div className="text-slate-500 font-medium">Month 3 (December 2026)</div>
              <div className="text-xl font-bold text-slate-900">₹52.4 Lakh</div>
              <div className="text-[11px] text-emerald-600 font-semibold">+22.3% Projected Growth</div>
              <div className="text-[10px] text-slate-400">Confidence Band: ₹48.2L - ₹56.5L</div>
            </div>
          </div>
        </div>

        {/* Strategic AI Recommendations */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-purple-600" />
            <h2 className="text-sm font-bold text-slate-900">Strategic Executive Directives</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-purple-50/50 rounded-xl border border-purple-100 text-xs space-y-1.5">
              <div className="font-bold text-purple-900">Cross-Branch Specialist Rotation</div>
              <p className="text-slate-600 leading-relaxed">
                Deploy traveling Orthodontists to Whitefield and Suburban clinics on alternate Saturdays to capture high-margin aligner demand.
              </p>
            </div>

            <div className="p-4 bg-indigo-50/50 rounded-xl border border-indigo-100 text-xs space-y-1.5">
              <div className="font-bold text-indigo-900">Consolidated Purchasing Advantage</div>
              <p className="text-slate-600 leading-relaxed">
                Execute quarterly group purchase order for composite resins and titanium implant fixtures to unlock 12% bulk supplier rebate.
              </p>
            </div>

            <div className="p-4 bg-emerald-50/50 rounded-xl border border-emerald-100 text-xs space-y-1.5">
              <div className="font-bold text-emerald-900">Recall Automation Campaign</div>
              <p className="text-slate-600 leading-relaxed">
                Trigger corporate hygiene recall reminders across all clinics to fill 28 open weekday morning chair slots.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

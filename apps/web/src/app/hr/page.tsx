"use client";

import Link from "next/link";
import { useState } from "react";
import {
  Users,
  Clock,
  PlaneTakeoff,
  DollarSign,
  Briefcase,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Calendar,
  Sparkles,
  TrendingUp,
  GraduationCap,
} from "lucide-react";
import { HRNav } from "./nav";
import { HRDashboardMetrics } from "./types";

const initialMetrics: HRDashboardMetrics = {
  total_headcount: 48,
  active_employees: 44,
  on_leave_employees: 4,
  today_scheduled: 32,
  today_present: 30,
  today_late: 2,
  attendance_rate: 93.8,
  pending_leaves: 6,
  current_month_payroll_total: 2840000,
  open_job_positions: 5,
  licenses_expiring_soon: 3,
};

export default function HRDashboardPage() {
  const [metrics] = useState<HRDashboardMetrics>(initialMetrics);

  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome & Context Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Workforce & Human Resources Hub</h1>
            <p className="text-sm text-slate-500 mt-1">
              Centralized staff administration, automated gross-to-net payroll, attendance tracking & clinical credentialing
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/hr/attendance"
              className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-sm font-semibold shadow-xs hover:bg-slate-50 transition-colors"
            >
              <Clock className="w-4 h-4 text-teal-600" /> Today&apos;s Punches
            </Link>
            <Link
              href="/hr/payroll"
              className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-semibold shadow-xs transition-colors"
            >
              <DollarSign className="w-4 h-4" /> Run Monthly Payroll
            </Link>
          </div>
        </div>

        {/* Top KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Workforce</span>
              <div className="p-2 bg-teal-50 text-teal-600 rounded-lg">
                <Users className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-slate-900">{metrics.total_headcount}</span>
              <span className="text-xs font-medium text-emerald-600">
                {metrics.active_employees} Active
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-2">{metrics.on_leave_employees} staff currently on sanctioned leave</p>
          </div>

          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Today&apos;s Attendance</span>
              <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-slate-900">{metrics.attendance_rate}%</span>
              <span className="text-xs font-medium text-amber-600">
                {metrics.today_late} Late
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-2">{metrics.today_present} of {metrics.today_scheduled} scheduled clinicians present</p>
          </div>

          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Pending Leave Approvals</span>
              <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                <PlaneTakeoff className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-slate-900">{metrics.pending_leaves}</span>
              <span className="text-xs font-medium text-amber-600">Requires Action</span>
            </div>
            <p className="text-xs text-slate-400 mt-2">Manager review & HR approval queue</p>
          </div>

          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Est. Monthly Payroll</span>
              <div className="p-2 bg-purple-50 text-purple-600 rounded-lg">
                <DollarSign className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-slate-900">₹{(metrics.current_month_payroll_total / 100000).toFixed(2)}L</span>
              <span className="text-xs font-medium text-purple-600">Net Est.</span>
            </div>
            <p className="text-xs text-slate-400 mt-2">Includes Basic, HRA, incentives & PF</p>
          </div>
        </div>

        {/* AI Workforce Radar Banner */}
        <div className="bg-gradient-to-r from-teal-900 via-slate-900 to-indigo-950 rounded-2xl p-6 text-white mb-8 shadow-md">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 bg-teal-500/20 text-teal-300 rounded-full text-xs font-semibold border border-teal-500/30">
                <Sparkles className="w-3.5 h-3.5" /> AI Workforce Intelligence Active
              </div>
              <h2 className="text-xl font-bold tracking-tight">3 Compliance & Staffing Alerts Detected</h2>
              <p className="text-sm text-slate-300 max-w-2xl">
                2 Doctor Dental Council licenses expire within 45 days. 1 specialty leave conflict identified in Endodontics for upcoming Saturday.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="/hr/ai"
                className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 rounded-lg text-xs font-bold transition-colors inline-flex items-center gap-1.5 shadow-sm"
              >
                View AI Radar <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href="/hr/training"
                className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-xs font-semibold transition-colors border border-white/10"
              >
                License Vault
              </Link>
            </div>
          </div>
        </div>

        {/* Quick Operations Matrix */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Operations Shortcuts */}
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs md:col-span-2">
            <h3 className="font-bold text-slate-900 text-base mb-4 flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-teal-600" /> Key HR Modules
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link
                href="/hr/employees"
                className="p-4 rounded-lg border border-slate-100 hover:border-teal-200 hover:bg-teal-50/30 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800 text-sm group-hover:text-teal-700">Staff Directory</span>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="text-xs text-slate-500 mt-1.5">Profiles, qualifications, designations, and emergency contacts</p>
              </Link>

              <Link
                href="/hr/shifts"
                className="p-4 rounded-lg border border-slate-100 hover:border-teal-200 hover:bg-teal-50/30 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800 text-sm group-hover:text-teal-700">Weekly Shift Planner</span>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="text-xs text-slate-500 mt-1.5">Chair assignments, split shifts & scheduling conflict prevention</p>
              </Link>

              <Link
                href="/hr/leave"
                className="p-4 rounded-lg border border-slate-100 hover:border-teal-200 hover:bg-teal-50/30 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800 text-sm group-hover:text-teal-700">Two-Tier Leave Desk</span>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="text-xs text-slate-500 mt-1.5">Manager review, HR sanctioning & automated balance deduction</p>
              </Link>

              <Link
                href="/hr/payroll"
                className="p-4 rounded-lg border border-slate-100 hover:border-teal-200 hover:bg-teal-50/30 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800 text-sm group-hover:text-teal-700">Payroll & Payslips</span>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="text-xs text-slate-500 mt-1.5">Gross earnings, statutory deductions, incentives & itemized payslips</p>
              </Link>

              <Link
                href="/hr/training"
                className="p-4 rounded-lg border border-slate-100 hover:border-teal-200 hover:bg-teal-50/30 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800 text-sm group-hover:text-teal-700">Credentialing & CE</span>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="text-xs text-slate-500 mt-1.5">Dental council licenses, CPR/BLS certifications & radiation compliance</p>
              </Link>

              <Link
                href="/hr/recruitment"
                className="p-4 rounded-lg border border-slate-100 hover:border-teal-200 hover:bg-teal-50/30 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800 text-sm group-hover:text-teal-700">Talent Acquisition</span>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="text-xs text-slate-500 mt-1.5">Job vacancies, applicant interview stages & offer letters</p>
              </Link>
            </div>
          </div>

          {/* Quick Notice Panel */}
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs space-y-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" /> Action Items
            </h3>

            <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg text-xs space-y-1">
              <span className="font-bold text-amber-900 block">6 Leave Requests Pending</span>
              <p className="text-amber-800">4 Casual and 2 Sick leaves pending Clinic Manager sign-off.</p>
              <Link href="/hr/leave" className="text-teal-700 font-semibold inline-block pt-1 hover:underline">
                Review queue &rarr;
              </Link>
            </div>

            <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-lg text-xs space-y-1">
              <span className="font-bold text-blue-900 block">Payroll Run Ready</span>
              <p className="text-blue-800">September 2026 payroll ready for review and disbursement.</p>
              <Link href="/hr/payroll" className="text-teal-700 font-semibold inline-block pt-1 hover:underline">
                Generate payslips &rarr;
              </Link>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
              <span className="font-bold text-slate-800 block">Staff Self-Service Ready</span>
              <p className="text-slate-600">Doctors and assistants can clock in, request leave, and download payslips directly.</p>
              <Link href="/hr/self-service" className="text-teal-700 font-semibold inline-block pt-1 hover:underline">
                Open ESS portal &rarr;
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

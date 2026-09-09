"use client";

import { useState } from "react";
import {
  Briefcase,
  Plus,
  Search,
  Filter,
  Users,
  Calendar,
  CheckCircle2,
  Clock,
  ArrowRight,
} from "lucide-react";
import { HRNav } from "../nav";
import { JobOpening } from "../types";

const mockJobs: JobOpening[] = [
  {
    id: "job-1",
    title: "Associate Endodontist",
    employment_type: "FULL_TIME",
    open_positions: 1,
    experience_years_min: 2,
    status: "OPEN",
    description: "Manage complex root canal treatments, apical surgeries, and emergency pulp therapies.",
    requirements: "MDS in Endodontics, DCI registration mandatory.",
    created_at: "2026-08-20T00:00:00Z",
    updated_at: "2026-08-20T00:00:00Z",
  },
  {
    id: "job-2",
    title: "Lead Chairside Dental Assistant",
    employment_type: "FULL_TIME",
    open_positions: 2,
    experience_years_min: 1,
    status: "OPEN",
    description: "Four-handed dentistry assistance, sterilization autoclaving, and digital imaging setup.",
    requirements: "Dental Assistant certification, CPR/BLS preferred.",
    created_at: "2026-08-25T00:00:00Z",
    updated_at: "2026-08-25T00:00:00Z",
  },
  {
    id: "job-3",
    title: "Front Desk Executive & Patient Concierge",
    employment_type: "FULL_TIME",
    open_positions: 1,
    experience_years_min: 1,
    status: "ON_HOLD",
    description: "Patient check-in, appointment booking, insurance claims pre-auth verification.",
    requirements: "Bachelor degree, fluent English and Hindi, healthcare experience.",
    created_at: "2026-08-10T00:00:00Z",
    updated_at: "2026-08-15T00:00:00Z",
  },
];

export default function RecruitmentPage() {
  const [jobs] = useState<JobOpening[]>(mockJobs);

  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Talent Acquisition & Hiring Pipeline</h1>
            <p className="text-sm text-slate-500 mt-1">
              Active job requisitions, applicant screening, clinical demo scheduling & interview scorecards
            </p>
          </div>
        </div>

        {/* Pipeline Stages Overview */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-8 text-center text-xs">
          <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-slate-400 block font-semibold">Applied</span>
            <span className="text-xl font-bold text-slate-900 mt-1 block">18</span>
            <span className="text-[10px] text-teal-600">New resumes</span>
          </div>
          <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-slate-400 block font-semibold">Screening</span>
            <span className="text-xl font-bold text-slate-900 mt-1 block">6</span>
            <span className="text-[10px] text-blue-600">Phone screen</span>
          </div>
          <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-slate-400 block font-semibold">Interview</span>
            <span className="text-xl font-bold text-slate-900 mt-1 block">4</span>
            <span className="text-[10px] text-purple-600">Clinical Demo</span>
          </div>
          <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-slate-400 block font-semibold">Offered</span>
            <span className="text-xl font-bold text-slate-900 mt-1 block">2</span>
            <span className="text-[10px] text-amber-600">Pending accept</span>
          </div>
          <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-slate-400 block font-semibold">Hired (MTD)</span>
            <span className="text-xl font-bold text-emerald-600 mt-1 block">3</span>
            <span className="text-[10px] text-emerald-700 font-semibold">Onboarded</span>
          </div>
        </div>

        {/* Requisitions List */}
        <div className="space-y-4">
          <h2 className="text-base font-bold text-slate-900">Active Job Requisitions</h2>
          {jobs.map((j) => (
            <div key={j.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs">
              <div className="space-y-1 max-w-xl">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-900 text-sm">{j.title}</span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      j.status === "OPEN"
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {j.status}
                  </span>
                </div>
                <p className="text-slate-600">{j.description}</p>
                <div className="text-slate-400 text-[11px] pt-1">
                  Positions: {j.open_positions} · Min Experience: {j.experience_years_min}+ yrs · {j.employment_type}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button className="px-3 py-1.5 border border-slate-200 text-slate-700 font-semibold rounded-lg hover:bg-slate-50">
                  Applicants (6)
                </button>
                <button className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg">
                  Schedule Demo
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

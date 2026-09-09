"use client";

import { useState } from "react";
import {
  Award,
  Star,
  Plus,
  TrendingUp,
  Target,
  UserCheck,
  CheckCircle2,
} from "lucide-react";
import { HRNav } from "../nav";
import { PerformanceReview } from "../types";

const mockReviews: PerformanceReview[] = [
  {
    id: "rev-1",
    clinic_id: "c1",
    employee_id: "e1",
    review_cycle: "QUARTERLY",
    review_period: "2026-Q2",
    clinical_skills_rating: 5.0,
    patient_satisfaction_rating: 4.8,
    punctuality_rating: 4.5,
    teamwork_rating: 4.9,
    protocol_adherence_rating: 5.0,
    overall_rating: 4.8,
    strengths: "Exceptional clinical precision in full-arch rehabilitation; stellar patient rapport.",
    areas_of_improvement: "Delegate preliminary impressions to chairside assistant to improve turnover.",
    goals_next_period: "Lead digital workflow pilot for CBCT implant planning.",
    status: "COMPLETED",
    created_at: "",
    updated_at: "",
  },
  {
    id: "rev-2",
    clinic_id: "c1",
    employee_id: "e2",
    review_cycle: "QUARTERLY",
    review_period: "2026-Q2",
    clinical_skills_rating: 4.9,
    patient_satisfaction_rating: 4.7,
    punctuality_rating: 4.2,
    teamwork_rating: 4.6,
    protocol_adherence_rating: 4.8,
    overall_rating: 4.6,
    strengths: "Rapid and painless endodontic treatments with zero post-op flare-ups.",
    areas_of_improvement: "Punctuality on morning 09:00 emergency slots.",
    goals_next_period: "Mentor junior residents on rotary canal instrumentation.",
    status: "ACKNOWLEDGED",
    created_at: "",
    updated_at: "",
  },
];

export default function PerformanceReviewsPage() {
  const [reviews] = useState<PerformanceReview[]>(mockReviews);

  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Performance Appraisals & KPIs</h1>
            <p className="text-sm text-slate-500 mt-1">
              Clinical skill ratings, patient satisfaction index, hygiene compliance & goal tracking
            </p>
          </div>
        </div>

        {/* Review Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {reviews.map((rev) => (
            <div key={rev.id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4 text-xs">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-bold text-slate-900 text-sm">Clinician Review #{rev.employee_id}</h2>
                  <span className="text-slate-400">{rev.review_cycle} · {rev.review_period}</span>
                </div>
                <div className="flex items-center gap-1 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-lg">
                  <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                  <span className="font-bold text-amber-900 text-sm">{rev.overall_rating} / 5.0</span>
                </div>
              </div>

              {/* Rating Bars */}
              <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100">
                <div>
                  <div className="flex justify-between text-slate-500 mb-1">
                    <span>Clinical Skills</span>
                    <span className="font-semibold text-slate-800">{rev.clinical_skills_rating}</span>
                  </div>
                  <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-teal-500 h-full rounded-full" style={{ width: `${(rev.clinical_skills_rating / 5) * 100}%` }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-500 mb-1">
                    <span>Patient Satisfaction</span>
                    <span className="font-semibold text-slate-800">{rev.patient_satisfaction_rating}</span>
                  </div>
                  <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-teal-500 h-full rounded-full" style={{ width: `${(rev.patient_satisfaction_rating / 5) * 100}%` }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-500 mb-1">
                    <span>Protocol Adherence</span>
                    <span className="font-semibold text-slate-800">{rev.protocol_adherence_rating}</span>
                  </div>
                  <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-teal-500 h-full rounded-full" style={{ width: `${(rev.protocol_adherence_rating / 5) * 100}%` }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-500 mb-1">
                    <span>Teamwork</span>
                    <span className="font-semibold text-slate-800">{rev.teamwork_rating}</span>
                  </div>
                  <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-teal-500 h-full rounded-full" style={{ width: `${(rev.teamwork_rating / 5) * 100}%` }} />
                  </div>
                </div>
              </div>

              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 space-y-1">
                <span className="font-semibold text-slate-800 block">Strengths:</span>
                <p className="text-slate-600">{rev.strengths}</p>
                <span className="font-semibold text-slate-800 block pt-1">Target Goals:</span>
                <p className="text-slate-600">{rev.goals_next_period}</p>
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Status: <b className="text-teal-700">{rev.status}</b></span>
                <span className="text-slate-500 font-medium">Acknowledged by Clinician</span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

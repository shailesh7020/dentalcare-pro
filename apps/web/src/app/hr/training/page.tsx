"use client";

import { useState } from "react";
import {
  GraduationCap,
  ShieldCheck,
  AlertTriangle,
  Plus,
  CheckCircle2,
  Calendar,
  ExternalLink,
} from "lucide-react";
import { HRNav } from "../nav";
import { TrainingCourse } from "../types";

const mockCourses: TrainingCourse[] = [
  { id: "c1", title: "Radiation Safety & CBCT Protocols", provider: "AERB Compliance Board", course_type: "RADIATION_SAFETY", credits_hours: 4.0, is_mandatory: true, validity_months: 12, created_at: "", updated_at: "" },
  { id: "c2", title: "CPR & Basic Life Support (BLS)", provider: "American Heart Association", course_type: "CPR_BLS", credits_hours: 8.0, is_mandatory: true, validity_months: 24, created_at: "", updated_at: "" },
  { id: "c3", title: "Infection Control & Sterilization Protocols", provider: "Dental Council Academy", course_type: "INFECTION_CONTROL", credits_hours: 3.0, is_mandatory: true, validity_months: 12, created_at: "", updated_at: "" },
  { id: "c4", title: "Digital Impression & CAD/CAM Milling", provider: "Internal Clinical Academy", course_type: "CLINICAL_SPECIALTY", credits_hours: 6.0, is_mandatory: false, validity_months: 24, created_at: "", updated_at: "" },
];

export default function TrainingCompliancePage() {
  const [courses] = useState<TrainingCourse[]>(mockCourses);

  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Doctor Credentialing & Continuing Education</h1>
            <p className="text-sm text-slate-500 mt-1">
              State council registrations, mandatory certifications (BLS, Radiation), CE credits & automated expiry radar
            </p>
          </div>
        </div>

        {/* Mandatory Courses List */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden mb-8">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <GraduationCap className="w-4 h-4 text-teal-600" /> Mandatory Compliance Modules & CE Courses
            </h2>
          </div>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">Course Title & Provider</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">CE Credits</th>
                <th className="py-3 px-4">Validity</th>
                <th className="py-3 px-4">Compliance Requirement</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {courses.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50/50">
                  <td className="py-3 px-4">
                    <span className="font-semibold text-slate-800 block">{c.title}</span>
                    <span className="text-[11px] text-slate-400">{c.provider}</span>
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                    {c.course_type.replace("_", " ")}
                  </td>
                  <td className="py-3 px-4 font-bold text-teal-700">{c.credits_hours} CE Points</td>
                  <td className="py-3 px-4 text-slate-600">{c.validity_months} Months</td>
                  <td className="py-3 px-4">
                    {c.is_mandatory ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                        MANDATORY
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600">
                        OPTIONAL
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button className="text-teal-600 hover:text-teal-700 font-semibold text-xs">
                      Enroll Staff &rarr;
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}

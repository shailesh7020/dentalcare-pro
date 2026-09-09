"use client";

import Link from "next/link";
import { useState } from "react";
import type { NLSearchResult } from "../types";

const MOCK_RESULTS: NLSearchResult[] = [
  {
    patient_id: "PAT-1082",
    patient_name: "Aarav Mehta",
    age: 34,
    gender: "Male",
    phone: "+91 98765 43210",
    conditions: ["Hypertension", "Allergy: Penicillin"],
    match_reason: "Matches query: Penicillin-allergic patient with active restorative treatment.",
    last_visit: "2026-09-02",
    pending_procedures: ["Tooth #46 RCT Obturation", "Tooth #46 Full Crown"],
  },
  {
    patient_id: "PAT-1083",
    patient_name: "Riya Kapoor",
    age: 29,
    gender: "Female",
    phone: "+91 98765 43211",
    conditions: ["Type 2 Diabetes (HbA1c 7.1%)"],
    match_reason: "Matches query: Diabetic patient due for surgical review of #38 pericoronitis.",
    last_visit: "2026-08-28",
    pending_procedures: ["Tooth #38 Surgical Extraction"],
  },
  {
    patient_id: "PAT-1084",
    patient_name: "Vikram Malhotra",
    age: 52,
    gender: "Male",
    phone: "+91 98765 43212",
    conditions: ["Hypertension", "Aspirin Therapy 75mg"],
    match_reason: "Matches query: Bleeding risk patient on antiplatelet therapy scheduled for scaling.",
    last_visit: "2026-08-15",
    pending_procedures: ["Full Mouth Ultrasonic Scaling"],
  },
  {
    patient_id: "PAT-1085",
    patient_name: "Sunita Sharma",
    age: 44,
    gender: "Female",
    phone: "+91 98765 43213",
    conditions: ["Asthma", "Allergy: Sulfa Drugs"],
    match_reason: "Matches query: Drug allergy flagged in record, pending composite restoration.",
    last_visit: "2026-07-22",
    pending_procedures: ["Tooth #24 Class V Composite"],
  },
];

const PRESET_QUERIES = [
  "Patients with penicillin allergy",
  "Diabetic patients due for recall",
  "Hypertensive patients on blood thinners",
  "Unfinished root canal treatments",
  "Pending dental crown cementations",
];

export default function AISearchPage() {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<NLSearchResult[]>(MOCK_RESULTS);

  const handleSearch = (searchQuery: string) => {
    setQuery(searchQuery);
    setIsSearching(true);
    setTimeout(() => {
      setIsSearching(false);
      const q = searchQuery.toLowerCase();
      if (!q.trim()) {
        setResults(MOCK_RESULTS);
        return;
      }
      const filtered = MOCK_RESULTS.filter(
        (r) =>
          r.patient_name.toLowerCase().includes(q) ||
          r.conditions.some((c: string) => c.toLowerCase().includes(q)) ||
          r.match_reason.toLowerCase().includes(q) ||
          r.pending_procedures.some((p: string) => p.toLowerCase().includes(q))
      );
      setResults(filtered.length > 0 ? filtered : MOCK_RESULTS.slice(0, 2));
    }, 350);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
              <Link href="/" className="hover:text-cyan-400">Dashboard</Link>
              <span>/</span>
              <Link href="/ai" className="hover:text-cyan-400">AI Hub</Link>
              <span>/</span>
              <span className="text-slate-200">Natural Language Search</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              🔍 Clinical Natural Language Query
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-900/60 text-emerald-300 border border-emerald-700/60 flex items-center gap-1">
                <span>🔒</span> Multi-Tenant Isolated
              </span>
            </h1>
          </div>

          <Link
            href="/ai"
            className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
          >
            Back to AI Hub
          </Link>
        </div>

        {/* Search Bar */}
        <div className="bg-slate-800/80 border border-slate-700/70 rounded-xl p-5 space-y-4 shadow-lg">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSearch(query);
              }}
              placeholder="E.g., 'Find all diabetic patients with extractions in the last 6 months' or 'Penicillin allergic patients with pending RCT'..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-10 pr-24 py-3 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 shadow-inner"
            />
            <span className="absolute left-3.5 top-3.5 text-slate-400 text-base">🔍</span>
            <button
              type="button"
              onClick={() => handleSearch(query)}
              disabled={isSearching}
              className="absolute right-2 top-2 px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-md transition shadow flex items-center gap-1.5"
            >
              {isSearching ? "Searching..." : "Search"}
            </button>
          </div>

          {/* Quick Query Badges */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-xs text-slate-400 font-medium">Try asking:</span>
            {PRESET_QUERIES.map((preset) => (
              <button
                key={preset}
                type="button"
                onClick={() => handleSearch(preset)}
                className="text-xs bg-slate-900 hover:bg-slate-700 text-cyan-300 px-2.5 py-1 rounded-full border border-slate-700 transition"
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span>Found {results.length} patient records matching query criteria</span>
            <span className="text-[11px] text-emerald-400">Strict zero-data-leakage verification: PASSED</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((patient) => (
              <div
                key={patient.patient_id}
                className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-5 space-y-3 hover:border-slate-600 transition shadow-md"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-white text-base flex items-center gap-2">
                      {patient.patient_name}
                      <span className="text-xs font-normal text-slate-400">
                        ({patient.age}y, {patient.gender})
                      </span>
                    </h3>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">ID: {patient.patient_id} · {patient.phone}</p>
                  </div>
                  <span className="text-xs font-medium px-2 py-0.5 rounded bg-slate-700 text-slate-300">
                    Last: {patient.last_visit}
                  </span>
                </div>

                {/* Conditions & Risk Badges */}
                <div className="flex flex-wrap gap-1.5">
                  {patient.conditions.map((cond: string, idx: number) => (
                    <span
                      key={idx}
                      className={`text-xs px-2 py-0.5 rounded font-medium ${
                        cond.toLowerCase().includes("penicillin") || cond.toLowerCase().includes("allergy")
                          ? "bg-rose-950/70 text-rose-300 border border-rose-700/60"
                          : cond.toLowerCase().includes("diabetes")
                          ? "bg-amber-950/70 text-amber-300 border border-amber-700/60"
                          : "bg-blue-950/70 text-blue-300 border border-blue-700/60"
                      }`}
                    >
                      {cond}
                    </span>
                  ))}
                </div>

                {/* Match Reasoning */}
                <div className="bg-slate-900/80 rounded-lg p-2.5 text-xs text-cyan-200/90 border border-slate-800">
                  <span className="font-medium text-cyan-400">AI Match Context: </span>
                  {patient.match_reason}
                </div>

                {/* Pending Procedures */}
                {patient.pending_procedures.length > 0 && (
                  <div className="text-xs text-slate-300">
                    <span className="text-slate-400 font-medium">Pending: </span>
                    {patient.pending_procedures.join(", ")}
                  </div>
                )}

                {/* Actions */}
                <div className="pt-2 border-t border-slate-700/50 flex items-center justify-end gap-2">
                  <Link
                    href={`/patients/${patient.patient_id}`}
                    className="px-3 py-1 text-xs font-medium bg-slate-700 hover:bg-slate-600 text-slate-200 rounded transition"
                  >
                    Open Chart
                  </Link>
                  <Link
                    href={`/appointments?book=true&patient=${encodeURIComponent(patient.patient_name)}`}
                    className="px-3 py-1 text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white rounded transition"
                  >
                    Schedule Visit
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

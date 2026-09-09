"use client";

import Link from "next/link";
import { useState } from "react";
import type { AIProviderType, AIRecommendationRead, RiskAlert } from "./types";

interface AIModuleCard {
  title: string;
  description: string;
  href: string;
  badge: string;
  icon: string;
}

const MODULES: AIModuleCard[] = [
  {
    title: "AI SOAP Note Studio",
    description: "Generate comprehensive ADA/AAOMS clinical notes from appointment context, odontogram status, and exam findings.",
    href: "/ai/soap",
    badge: "Clinical CDS",
    icon: "📋",
  },
  {
    title: "Clinical Documentation",
    description: "Produce specialist referral letters, medical leave certificates, post-op instructions, and discharge summaries.",
    href: "/ai/documents",
    badge: "Documentation",
    icon: "✍️",
  },
  {
    title: "Natural Language Search",
    description: "Query patients by medical conditions (diabetic, hypertensive, allergic), procedure history, and recall intervals.",
    href: "/ai/search",
    badge: "Smart Query",
    icon: "🔍",
  },
  {
    title: "Practice Analytics & Stock Forecast",
    description: "Natural language business intelligence, operatory chair utilization, and inventory depletion date forecasting.",
    href: "/ai/analytics",
    badge: "Operations",
    icon: "📈",
  },
];

const INITIAL_RECOMMENDATIONS: AIRecommendationRead[] = [
  {
    id: "rec-01",
    clinic_id: "clinic-main",
    patient_id: "p-1002",
    dentist_id: "dentist-01",
    recommendation_type: "SOAP_NOTE",
    status: "PENDING_REVIEW",
    input_context_json: { patient: "Anita Sharma", tooth: "16", complaint: "Throbbing pain" },
    generated_output_json: {
      diagnosis: "Symptomatic Irreversible Pulpitis",
      suggested_procedure: "Root Canal Therapy & Core Buildup",
      antibiotic: "Clindamycin 300mg (Penicillin Allergic)",
    },
    created_at: new Date().toISOString(),
  },
  {
    id: "rec-02",
    clinic_id: "clinic-main",
    patient_id: "p-2005",
    dentist_id: "dentist-01",
    recommendation_type: "BILLING_AUDIT",
    status: "PENDING_REVIEW",
    input_context_json: { patient: "Rajesh Kumar", treatment: "Zirconia Crown" },
    generated_output_json: {
      unbilled_items: ["Gingival retraction cord", "Final bite registration impression"],
      potential_recovery: "₹1,800",
    },
    created_at: new Date().toISOString(),
  },
];

export default function AIHubPage() {
  const [provider, setProvider] = useState<AIProviderType>("MOCK");
  const [guardrailsEnabled, setGuardrailsEnabled] = useState(true);
  const [recommendations, setRecommendations] = useState<AIRecommendationRead[]>(INITIAL_RECOMMENDATIONS);
  const [patientIdInput, setPatientIdInput] = useState("P-1002");
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [quickSummary, setQuickSummary] = useState<{
    name: string;
    text: string;
    recall: number;
    risks: RiskAlert[];
  } | null>({
    name: "Anita Sharma (Age: 34)",
    text: "Patient under active restorative care. Completed distal composite on 15 last month. Medical history significant for documented penicillin hypersensitivity and Type 2 Diabetes (HbA1c 7.1%).",
    recall: 6,
    risks: [
      {
        category: "ALLERGY",
        severity: "HIGH",
        title: "Penicillin Allergy Documented",
        details: "Avoid Amoxicillin, Augmentin, and beta-lactam antibiotics. Lincosamides (Clindamycin) indicated.",
      },
      {
        category: "SYSTEMIC_DISEASE",
        severity: "MEDIUM",
        title: "Type 2 Diabetes Mellitus Protocol",
        details: "Monitor blood glucose before surgical procedures. Increased risk of delayed healing.",
      },
    ],
  });

  const handleApprove = (id: string) => {
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: "APPROVED" as const, reviewed_at: new Date().toISOString() } : r))
    );
  };

  const handleReject = (id: string) => {
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: "REJECTED" as const, reviewed_at: new Date().toISOString() } : r))
    );
  };

  const runQuickSummary = () => {
    setIsSummarizing(true);
    setTimeout(() => {
      setIsSummarizing(false);
      setQuickSummary({
        name: `Patient ${patientIdInput}`,
        text: "Clinical records retrieved: 3 completed restorative treatments, 0 active periodontal pockets > 4mm. No pending billing balances. Recall due in 6 months.",
        recall: 6,
        risks: [
          {
            category: "PREVENTIVE",
            severity: "LOW",
            title: "Hygiene Recall Due",
            details: "Scheduled scaling and prophylaxis recommended within 6 months.",
          },
        ],
      });
    }, 600);
  };

  return (
    <main className="min-h-screen bg-slate-900 text-slate-100 p-6 md:p-10 font-sans">
      {/* Header Banner */}
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-3xl">✨</span>
              <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-teal-400 via-cyan-400 to-blue-500 bg-clip-text text-transparent">
                AI Clinical Assistant & Intelligent Automation
              </h1>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Phase 11 Enterprise Decision Support · Pluggable LLMs · Zero Data Leakage Multi-Tenancy
            </p>
          </div>

          {/* Provider & Guardrails Controls */}
          <div className="flex items-center gap-3 bg-slate-800/80 p-2 rounded-xl border border-slate-700/60 text-xs">
            <label className="text-slate-400 font-medium">Provider:</label>
            <select
              aria-label="AI Provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value as AIProviderType)}
              className="bg-slate-900 text-teal-400 font-semibold px-2.5 py-1 rounded border border-slate-700 focus:outline-none focus:border-teal-500"
            >
              <option value="MOCK">Mock Clinical (Air-Gapped)</option>
              <option value="OPENAI">OpenAI (GPT-4o-mini)</option>
              <option value="ANTHROPIC">Anthropic (Claude 3.5)</option>
              <option value="OLLAMA">Ollama Local (llama3)</option>
            </select>
            <button
              onClick={() => setGuardrailsEnabled(!guardrailsEnabled)}
              className={`px-3 py-1 rounded font-medium transition-colors ${
                guardrailsEnabled ? "bg-teal-500/20 text-teal-300 border border-teal-500/40" : "bg-red-500/20 text-red-300 border border-red-500/40"
              }`}
            >
              Guardrails: {guardrailsEnabled ? "ACTIVE" : "OFF"}
            </button>
          </div>
        </header>

        {/* Advisory Safety Disclaimer */}
        <aside className="bg-amber-950/40 border border-amber-500/40 rounded-xl p-4 flex items-start gap-3">
          <span className="text-amber-400 text-xl font-bold">⚠️</span>
          <div className="text-xs text-amber-200/90 leading-relaxed">
            <strong className="font-semibold text-amber-300">Mandatory Clinical Decision Support Notice:</strong> All AI-generated SOAP drafts, prescription suggestions, and risk alerts are purely advisory. A licensed clinician must review, verify, and edit all clinical information prior to patient application or permanent medical chart entry.
          </div>
        </aside>

        {/* AI Modules Grid */}
        <section aria-labelledby="ai-modules-heading">
          <h2 id="ai-modules-heading" className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <span>🚀</span> Core Clinical AI Capabilities
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {MODULES.map((m) => (
              <Link
                key={m.title}
                href={m.href}
                className="group bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-teal-500/60 rounded-2xl p-5 transition-all duration-200 flex flex-col justify-between shadow-sm hover:shadow-teal-900/20"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-2xl">{m.icon}</span>
                    <span className="text-[11px] font-medium tracking-wide uppercase px-2 py-0.5 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">
                      {m.badge}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-slate-100 group-hover:text-teal-300 transition-colors">
                    {m.title}
                  </h3>
                  <p className="text-xs text-slate-400 mt-2 line-clamp-3 leading-relaxed">
                    {m.description}
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-700/40 flex items-center text-xs text-teal-400 font-medium group-hover:translate-x-1 transition-transform">
                  Launch Studio &rarr;
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* 2-Column Split: Quick Patient Summarizer & Recommendations Queue */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Patient Clinical Context & Risk Engine */}
          <div className="lg:col-span-6 bg-slate-800/40 border border-slate-700/60 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
                <span>🛡️</span> Patient Clinical Risk & Summary
              </h2>
              <div className="flex items-center gap-2">
                <input
                  aria-label="Patient ID"
                  value={patientIdInput}
                  onChange={(e) => setPatientIdInput(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs w-28 text-slate-200"
                  placeholder="Patient ID"
                />
                <button
                  onClick={runQuickSummary}
                  disabled={isSummarizing}
                  className="bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white text-xs px-3 py-1 rounded font-medium transition-colors"
                >
                  {isSummarizing ? "Auditing..." : "Audit Patient"}
                </button>
              </div>
            </div>

            {quickSummary && (
              <div className="space-y-4">
                <div className="bg-slate-900/80 rounded-xl p-4 border border-slate-700/50">
                  <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2 mb-2">
                    <span className="font-semibold text-slate-200">{quickSummary.name}</span>
                    <span className="text-teal-400">Recall: Every {quickSummary.recall} Months</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{quickSummary.text}</p>
                </div>

                {/* Risk Alerts */}
                <div className="space-y-2">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Identified Clinical Risk Alerts ({quickSummary.risks.length})
                  </h3>
                  {quickSummary.risks.map((risk, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-xl border text-xs flex items-start gap-2.5 ${
                        risk.severity === "HIGH"
                          ? "bg-red-950/30 border-red-500/40 text-red-200"
                          : risk.severity === "MEDIUM"
                          ? "bg-amber-950/30 border-amber-500/40 text-amber-200"
                          : "bg-blue-950/30 border-blue-500/40 text-blue-200"
                      }`}
                    >
                      <span className="text-sm font-bold">
                        {risk.severity === "HIGH" ? "⛔" : risk.severity === "MEDIUM" ? "⚠️" : "ℹ️"}
                      </span>
                      <div>
                        <strong className="font-semibold block">{risk.title}</strong>
                        <span className="text-slate-300 leading-snug">{risk.details}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Clinician Approval Queue */}
          <div className="lg:col-span-6 bg-slate-800/40 border border-slate-700/60 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
                <span>⚖️</span> AI Recommendations Approval Queue
              </h2>
              <span className="text-xs text-slate-400 font-medium">
                Pending: {recommendations.filter((r) => r.status === "PENDING_REVIEW").length}
              </span>
            </div>

            <div className="space-y-3">
              {recommendations.map((rec) => (
                <article
                  key={rec.id}
                  className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-4 text-xs space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-teal-300 bg-teal-950/60 px-2 py-0.5 rounded border border-teal-800">
                        {rec.recommendation_type}
                      </span>
                      <span className="text-slate-400">ID: {rec.id}</span>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded font-medium ${
                        rec.status === "APPROVED"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : rec.status === "REJECTED"
                          ? "bg-rose-950 text-rose-400 border border-rose-800"
                          : "bg-amber-950 text-amber-400 border border-amber-800"
                      }`}
                    >
                      {rec.status}
                    </span>
                  </div>

                  <div className="bg-slate-950/60 p-2.5 rounded font-mono text-[11px] text-slate-300 space-y-1">
                    {Object.entries(rec.generated_output_json).map(([k, v]) => (
                      <div key={k} className="flex gap-2">
                        <span className="text-slate-500">{k}:</span>
                        <span className="text-slate-200 truncate">{Array.isArray(v) ? v.join(", ") : String(v)}</span>
                      </div>
                    ))}
                  </div>

                  {rec.status === "PENDING_REVIEW" && (
                    <div className="flex items-center justify-end gap-2 pt-1">
                      <button
                        onClick={() => handleReject(rec.id)}
                        className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-rose-400 border border-slate-700 rounded transition-colors"
                      >
                        Reject
                      </button>
                      <button
                        onClick={() => handleApprove(rec.id)}
                        className="px-3 py-1 bg-emerald-700 hover:bg-emerald-600 text-white rounded font-medium transition-colors"
                      >
                        Approve & Apply
                      </button>
                    </div>
                  )}
                </article>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

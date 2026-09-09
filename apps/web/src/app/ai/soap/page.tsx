"use client";

import Link from "next/link";
import { useState } from "react";

export default function AISoapStudioPage() {
  const [patientName, setPatientName] = useState("Aarav Mehta (34M)");
  const [toothNumber, setToothNumber] = useState("46 (FDI) / #30 (Universal)");
  const [chiefComplaint, setChiefComplaint] = useState(
    "Severe throbbing pain in lower right jaw for 3 days, aggravated by cold water and biting. Sleep disrupted."
  );
  const [clinicalFindings, setClinicalFindings] = useState(
    "Deep disto-occlusal caries on tooth #46. Extreme sensitivity to cold with lingering pain (>15s). Tender to vertical percussion (+3). Palpation normal. Probing depth 2-3mm. Radiograph reveals deep radiolucency approaching pulp chamber with early apical PDL widening."
  );
  const [proceduresPerformed, setProceduresPerformed] = useState(
    "Inferior alveolar nerve block with 2% Lignocaine + 1:80,000 Adrenaline. Rubber dam isolation. Caries excavation, pulpectomy, canal disinfection with 3% NaOCl and saline. Intracanal calcium hydroxide medicament placed. Cavit temporary restoration."
  );

  const [isGenerating, setIsGenerating] = useState(false);
  const [isApproved, setIsApproved] = useState(false);
  const [activeTab, setActiveTab] = useState<"all" | "s" | "o" | "a" | "p">("all");
  const [copied, setCopied] = useState(false);

  // Editable SOAP fields
  const [subjective, setSubjective] = useState(
    "Patient presents with severe, throbbing pain in the mandibular right posterior region (tooth #46) persisting for 3 days. Pain rated 8/10 on NRS. Aggravated by cold liquids and mastication; radiates to right preauricular region. Sleep disrupted. No swelling, fever, or trismus reported. Medical history: Denies systemic conditions; no known drug allergies (NKDA)."
  );
  const [objective, setObjective] = useState(
    "Extraoral: Symmetrical, no cervical lymphadenopathy.\nIntraoral: Tooth #46 exhibits extensive disto-occlusal caries with marginal breakdown. Cold test (Endo-Ice): Exaggerated, lingering response (>15s). Electric pulp test: Positive at low threshold (12/80). Percussion: Tender to vertical percussion (+3). Palpation: Non-tender. Periodontal probing: 2-3mm circumferential. Normal physiological mobility.\nRadiographic: Periapical radiograph indicates radiolucency approximating pulp horn; PDL widening at mesial root apex."
  );
  const [assessment, setAssessment] = useState(
    "1. Symptomatic Irreversible Pulpitis - Tooth #46 (ICD-10: K04.0)\n2. Symptomatic Apical Periodontitis - Tooth #46 (ICD-10: K04.4)\nPrognosis: Favorable with complete endodontic therapy followed by full-coverage crown."
  );
  const [plan, setPlan] = useState(
    "Completed Today:\n1. Administered local anesthesia: 1.8 mL 2% Lignocaine with 1:80,000 Adrenaline (IANB + long buccal). Profound anesthesia achieved.\n2. Rubber dam isolation placed and disinfected.\n3. Complete caries excavation, access cavity preparation, and pulpectomy.\n4. Working lengths determined with electronic apex locator (Root ZX) and verified radiographically: MB=20.5mm, ML=20.0mm, D=21.0mm.\n5. Canals copiously irrigated with 3% NaOCl and 17% EDTA.\n6. Non-setting Calcium Hydroxide paste placed intracanal.\n7. Sterile cotton pellet placed, sealed with Cavit temporary filling (>=3.5mm thickness). Occlusion verified and relieved.\n\nPost-Op Instructions & Next Steps:\n- Rx: Ibuprofen 400mg PO q6h PRN pain (max 3 days). Patient instructed on avoiding hard foods on right side.\n- Recall: Appointment scheduled in 7-10 days for root canal instrumentation and gutta-percha obturation."
  );

  const handleGenerate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
      setIsApproved(false);
    }, 600);
  };

  const handleApprove = () => {
    setIsApproved(true);
  };

  const fullNoteText = `SOAP CLINICAL NOTE\nPatient: ${patientName}\nTooth: ${toothNumber}\nStatus: ${isApproved ? "Clinician Approved & Signed" : "Pending Review"}\n\n[SUBJECTIVE]\n${subjective}\n\n[OBJECTIVE]\n${objective}\n\n[ASSESSMENT]\n${assessment}\n\n[PLAN]\n${plan}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(fullNoteText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Top Breadcrumb & Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
              <Link href="/" className="hover:text-cyan-400">Dashboard</Link>
              <span>/</span>
              <Link href="/ai" className="hover:text-cyan-400">AI Hub</Link>
              <span>/</span>
              <span className="text-slate-200">SOAP Studio</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              📋 AI SOAP Note Studio
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-900/60 text-cyan-300 border border-cyan-700/60">
                ADA / AAOMS Compliant
              </span>
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleCopy}
              className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition flex items-center gap-1.5"
            >
              {copied ? "✓ Copied" : "📋 Copy Full Note"}
            </button>
            <Link
              href="/ai"
              className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
            >
              Back to AI Hub
            </Link>
          </div>
        </div>

        {/* CDS Disclaimer Banner */}
        <div className="bg-amber-950/40 border border-amber-600/40 rounded-lg p-3 text-amber-200/90 text-xs flex items-center gap-2">
          <span className="text-base">⚠️</span>
          <span>
            <strong>Clinical Decision Support Guardrail:</strong> AI-generated SOAP drafts are strictly advisory. Clinicians must review, edit, and formally approve the text before saving to the medical record.
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Encounter Inputs */}
          <div className="lg:col-span-5 space-y-4">
            <div className="bg-slate-800/80 border border-slate-700/70 rounded-xl p-5 space-y-4 shadow-lg">
              <h2 className="text-base font-semibold text-slate-200 border-b border-slate-700/60 pb-2 flex items-center justify-between">
                <span>Encounter Context</span>
                <span className="text-xs font-normal text-slate-400">Input data for AI</span>
              </h2>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Patient</label>
                <input
                  type="text"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Tooth / Region</label>
                <input
                  type="text"
                  value={toothNumber}
                  onChange={(e) => setToothNumber(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Chief Complaint (Patient Words)</label>
                <textarea
                  rows={3}
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Clinical & Radiographic Findings</label>
                <textarea
                  rows={4}
                  value={clinicalFindings}
                  onChange={(e) => setClinicalFindings(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Procedures & Materials Used</label>
                <textarea
                  rows={4}
                  value={proceduresPerformed}
                  onChange={(e) => setProceduresPerformed(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <button
                type="button"
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium rounded-lg text-sm transition shadow-md flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                    Drafting SOAP Note...
                  </>
                ) : (
                  <>⚡ Regenerate SOAP Draft</>
                )}
              </button>
            </div>
          </div>

          {/* Right Column: Editable SOAP Sections */}
          <div className="lg:col-span-7 space-y-4">
            <div className="bg-slate-800/80 border border-slate-700/70 rounded-xl p-5 space-y-4 shadow-lg">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-700/60 pb-3">
                <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-700/70 text-xs">
                  {(["all", "s", "o", "a", "p"] as const).map((tab) => (
                    <button
                      key={tab}
                      type="button"
                      onClick={() => setActiveTab(tab)}
                      className={`px-3 py-1 rounded font-medium transition ${
                        activeTab === tab
                          ? "bg-cyan-600 text-white"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      {tab === "all" ? "All Sections" : tab.toUpperCase()}
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-2">
                  {isApproved ? (
                    <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-900/60 text-emerald-300 border border-emerald-700/60 flex items-center gap-1.5">
                      <span>✓</span> Approved & Signed
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={handleApprove}
                      className="px-3 py-1 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded shadow transition flex items-center gap-1"
                    >
                      <span>✓</span> Sign & Approve Note
                    </button>
                  )}
                </div>
              </div>

              {isApproved && (
                <div className="bg-emerald-950/40 border border-emerald-600/40 rounded-lg p-2.5 text-emerald-200/90 text-xs flex items-center justify-between">
                  <span>Note signed by attending clinician. Added to treatment record with cryptographic audit trail.</span>
                  <span className="text-[11px] text-emerald-400 font-mono">ID: REC-SOAP-2026</span>
                </div>
              )}

              {/* SOAP Body Cards */}
              <div className="space-y-4">
                {(activeTab === "all" || activeTab === "s") && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-semibold text-cyan-400 uppercase tracking-wider">
                      <span>[S] Subjective</span>
                      <span className="text-[11px] text-slate-500 font-normal">Patient history, onset, symptoms</span>
                    </div>
                    <textarea
                      rows={4}
                      value={subjective}
                      onChange={(e) => setSubjective(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 leading-relaxed font-sans"
                    />
                  </div>
                )}

                {(activeTab === "all" || activeTab === "o") && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-semibold text-cyan-400 uppercase tracking-wider">
                      <span>[O] Objective</span>
                      <span className="text-[11px] text-slate-500 font-normal">Extraoral, intraoral, tests, imaging</span>
                    </div>
                    <textarea
                      rows={5}
                      value={objective}
                      onChange={(e) => setObjective(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 leading-relaxed font-sans"
                    />
                  </div>
                )}

                {(activeTab === "all" || activeTab === "a") && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-semibold text-cyan-400 uppercase tracking-wider">
                      <span>[A] Assessment</span>
                      <span className="text-[11px] text-slate-500 font-normal">Differential/definitive diagnosis, ICD-10</span>
                    </div>
                    <textarea
                      rows={3}
                      value={assessment}
                      onChange={(e) => setAssessment(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 leading-relaxed font-sans"
                    />
                  </div>
                )}

                {(activeTab === "all" || activeTab === "p") && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-semibold text-cyan-400 uppercase tracking-wider">
                      <span>[P] Plan</span>
                      <span className="text-[11px] text-slate-500 font-normal">Procedures executed, Rx, instructions, recall</span>
                    </div>
                    <textarea
                      rows={6}
                      value={plan}
                      onChange={(e) => setPlan(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 leading-relaxed font-sans"
                    />
                  </div>
                )}
              </div>

              {/* Action Bar */}
              <div className="pt-3 border-t border-slate-700/60 flex items-center justify-between">
                <div className="text-xs text-slate-400">
                  {isApproved ? (
                    <span className="text-emerald-400 font-medium">Ready to sync to Treatment Records</span>
                  ) : (
                    <span>Review all 4 sections before clinician signoff</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setSubjective("");
                      setObjective("");
                      setAssessment("");
                      setPlan("");
                      setIsApproved(false);
                    }}
                    className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
                  >
                    Clear
                  </button>
                  <button
                    type="button"
                    onClick={handleApprove}
                    disabled={isApproved}
                    className="px-4 py-1.5 text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 text-white rounded-lg transition shadow"
                  >
                    {isApproved ? "Note Saved & Linked" : "Approve Note"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import Link from "next/link";

interface AIAssistantDrawerProps {
  patientId?: string;
  patientName?: string;
}

export function AIAssistantDrawer({
  patientId = "PAT-1082",
  patientName = "Aarav Mehta",
}: AIAssistantDrawerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"alerts" | "missing" | "ask">("alerts");
  const [askQuery, setAskQuery] = useState("");
  const [chatLog, setChatLog] = useState<{ role: "user" | "ai"; text: string }[]>([
    {
      role: "ai",
      text: "Hello Doctor! I am your DentalCare Pro Clinical Assistant. How can I assist you with this patient encounter today?",
    },
  ]);

  const handleSendQuery = () => {
    if (!askQuery.trim()) return;
    const userMsg = askQuery;
    setChatLog((prev) => [...prev, { role: "user", text: userMsg }]);
    setAskQuery("");

    setTimeout(() => {
      let aiReply = "I have checked the ADA clinical guidelines and practice records for this query.";
      if (userMsg.toLowerCase().includes("allergy") || userMsg.toLowerCase().includes("penicillin")) {
        aiReply = "CRITICAL ALERT: Patient is ALLERGIC to Penicillin. Do NOT prescribe Amoxicillin or Augmentin. Recommended dental alternatives: Clindamycin 300mg PO q6h or Azithromycin 500mg loading followed by 250mg q24h.";
      } else if (userMsg.toLowerCase().includes("anesthesia") || userMsg.toLowerCase().includes("dosage")) {
        aiReply = "Max recommended dose of 2% Lignocaine with 1:80,000 Adrenaline is 4.4 mg/kg (up to 300mg max). For a 70kg adult, maximum is approx. 8.3 standard 1.8mL cartridges.";
      } else {
        aiReply = `For ${patientName}, clinical documentation shows incomplete root canal therapy on tooth #46. Suggested next step: Instrumentation to working length and calcium hydroxide intracanal dressing.`;
      }
      setChatLog((prev) => [...prev, { role: "ai", text: aiReply }]);
    }, 450);
  };

  return (
    <>
      {/* Floating Toggle Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-full p-3.5 shadow-2xl flex items-center gap-2 border border-cyan-400/40 transition hover:scale-105"
        aria-label="Toggle AI Clinical Assistant"
      >
        <span className="text-xl">✨</span>
        <span className="text-xs font-semibold hidden md:inline">AI Assistant</span>
      </button>

      {/* Slide-out Drawer */}
      {isOpen && (
        <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-slate-900 border-l border-slate-700 shadow-2xl flex flex-col justify-between text-slate-100 animate-in slide-in-from-right duration-200">
          {/* Header */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg">✨</span>
                <h3 className="text-sm font-bold text-white">AI Clinical Assistant</h3>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">Active Context: {patientName}</p>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 text-sm"
            >
              ✕
            </button>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 text-xs bg-slate-950/40 p-1">
            <button
              type="button"
              onClick={() => setActiveTab("alerts")}
              className={`flex-1 py-1.5 rounded text-center font-medium transition ${
                activeTab === "alerts" ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              ⚠️ Risk Alerts
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("missing")}
              className={`flex-1 py-1.5 rounded text-center font-medium transition ${
                activeTab === "missing" ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              📋 Missing Docs
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("ask")}
              className={`flex-1 py-1.5 rounded text-center font-medium transition ${
                activeTab === "ask" ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              💬 Ask AI
            </button>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {activeTab === "alerts" && (
              <div className="space-y-3">
                <div className="bg-rose-950/50 border border-rose-600/50 rounded-lg p-3 text-xs space-y-1">
                  <div className="flex items-center gap-1.5 text-rose-300 font-bold">
                    <span>🛑</span> ALLERGY WARNING: Penicillin
                  </div>
                  <p className="text-slate-300">
                    Patient has documented anaphylactoid reaction to Penicillin and Beta-lactams. Use Clindamycin or Macrolides.
                  </p>
                </div>

                <div className="bg-amber-950/50 border border-amber-600/50 rounded-lg p-3 text-xs space-y-1">
                  <div className="flex items-center gap-1.5 text-amber-300 font-bold">
                    <span>⚠️</span> Bleeding Risk: Hypertension
                  </div>
                  <p className="text-slate-300">
                    Last recorded BP: 142/90 mmHg. Aspirin therapy noted. Maintain local hemostasis with resorbable gelatin sponges if surgical extractions performed.
                  </p>
                </div>

                <div className="pt-2">
                  <Link
                    href="/ai/soap"
                    className="block text-center py-2 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded border border-slate-700 text-xs font-semibold transition"
                  >
                    Open AI SOAP Studio for this Patient →
                  </Link>
                </div>
              </div>
            )}

            {activeTab === "missing" && (
              <div className="space-y-3">
                <div className="text-xs text-slate-400 mb-2">
                  Auditing chart against ADA quality assurance documentation standards:
                </div>

                <div className="bg-slate-800/80 rounded-lg p-3 border border-slate-700 text-xs space-y-1">
                  <div className="flex items-center justify-between text-amber-400 font-semibold">
                    <span>⚠️ Unsigned Consent Form</span>
                    <span className="text-[10px] bg-amber-900/60 px-1.5 py-0.5 rounded">Action Required</span>
                  </div>
                  <p className="text-slate-300">Endodontic informed consent form not yet signed for tooth #46.</p>
                  <Link href="/consents" className="text-cyan-400 hover:underline text-[11px] block mt-1">
                    Open Consent Portal →
                  </Link>
                </div>

                <div className="bg-slate-800/80 rounded-lg p-3 border border-slate-700 text-xs space-y-1">
                  <div className="flex items-center justify-between text-cyan-400 font-semibold">
                    <span>ℹ️ Periodontal Charting Due</span>
                    <span className="text-[10px] bg-cyan-900/60 px-1.5 py-0.5 rounded">6-Mo Recur</span>
                  </div>
                  <p className="text-slate-300">Full mouth 6-point probing last updated 8 months ago.</p>
                </div>

                <div className="bg-slate-800/80 rounded-lg p-3 border border-slate-700 text-xs space-y-1">
                  <div className="flex items-center justify-between text-emerald-400 font-semibold">
                    <span>✓ Radiographs</span>
                    <span className="text-[10px] bg-emerald-900/60 px-1.5 py-0.5 rounded">Complete</span>
                  </div>
                  <p className="text-slate-300">Periapical digital radiograph on record (02-Sep-2026).</p>
                </div>
              </div>
            )}

            {activeTab === "ask" && (
              <div className="space-y-3 flex flex-col h-full">
                <div className="flex-1 space-y-2 overflow-y-auto max-h-[380px] pr-1">
                  {chatLog.map((msg, i) => (
                    <div
                      key={i}
                      className={`text-xs p-2.5 rounded-lg leading-relaxed ${
                        msg.role === "user"
                          ? "bg-cyan-900/40 text-cyan-100 border border-cyan-700/50 ml-6"
                          : "bg-slate-800 text-slate-200 border border-slate-700 mr-4"
                      }`}
                    >
                      <span className="block font-semibold text-[10px] text-slate-400 mb-0.5 uppercase">
                        {msg.role === "user" ? "You" : "Dental AI"}
                      </span>
                      {msg.text}
                    </div>
                  ))}
                </div>

                <div className="pt-2 flex gap-1.5">
                  <input
                    type="text"
                    value={askQuery}
                    onChange={(e) => setAskQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSendQuery();
                    }}
                    placeholder="Ask drug dosage, guidelines..."
                    className="flex-1 bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                  <button
                    type="button"
                    onClick={handleSendQuery}
                    className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-semibold transition"
                  >
                    Send
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Footer Disclaimer */}
          <div className="p-3 border-t border-slate-800 bg-slate-950 text-[10px] text-slate-400 text-center">
            Advisory Clinical Decision Support. Clinician judgment supercedes AI recommendations.
          </div>
        </div>
      )}
    </>
  );
}

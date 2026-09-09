"use client";

import React, { useState } from "react";
import {
  FileSignature,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Download,
  PenTool,
  Lock,
} from "lucide-react";
import { PortalShell } from "../portal-shell";

interface PortalFormItem {
  id: string;
  title: string;
  code: string;
  status: "PENDING" | "SUBMITTED" | "APPROVED";
  due_date: string;
  description: string;
  legal_text: string;
}

const mockForms: PortalFormItem[] = [
  {
    id: "pf-1",
    title: "Informed Consent for Surgical Extraction",
    code: "CONSENT-EXT-01",
    status: "PENDING",
    due_date: "2026-10-15",
    description: "Informed consent detailing potential risks, dry socket prevention, and post-op care.",
    legal_text: "I hereby confirm that Dr. David Tennant has explained the planned extraction procedure, alternative options, and possible risks including nerve paresthesia, alveolar osteitis, and post-surgical discomfort. I acknowledge all pre-op guidelines.",
  },
  {
    id: "pf-2",
    title: "Annual Medical & Allergy History Update",
    code: "MED-HIST-2026",
    status: "APPROVED",
    due_date: "2026-08-01",
    description: "Annual health survey verifying cardiovascular conditions, diabetes, medications, and latex allergies.",
    legal_text: "I certify that all medical and medication disclosures provided are accurate and complete.",
  },
];

export default function PortalFormsPage() {
  const [forms, setForms] = useState(mockForms);
  const [signingTarget, setSigningTarget] = useState<PortalFormItem | null>(null);
  const [signedName, setSignedName] = useState("Donna Noble");
  const [hasAgreed, setHasAgreed] = useState(false);
  const [signSuccess, setSignSuccess] = useState(false);

  const handleSubmitSignature = (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasAgreed || !signingTarget) return;

    setForms(
      forms.map((f) => (f.id === signingTarget.id ? { ...f, status: "SUBMITTED" } : f))
    );
    setSignSuccess(true);
    setTimeout(() => {
      setSignSuccess(false);
      setSigningTarget(null);
      setHasAgreed(false);
    }, 1800);
  };

  return (
    <PortalShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Digital Consent & Questionnaires</h1>
          <p className="text-xs text-slate-500">Complete clinical consent records before your dental visits</p>
        </div>
      </div>

      <div className="space-y-4">
        {forms.map((f) => (
          <div key={f.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                  {f.code}
                </span>
                <h3 className="text-sm font-bold text-slate-900">{f.title}</h3>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                    f.status === "APPROVED"
                      ? "bg-emerald-100 text-emerald-800"
                      : f.status === "SUBMITTED"
                      ? "bg-blue-100 text-blue-800"
                      : "bg-rose-100 text-rose-800"
                  }`}
                >
                  {f.status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">{f.description}</p>
            </div>

            <div className="flex items-center gap-3">
              {f.status === "PENDING" ? (
                <button
                  onClick={() => setSigningTarget(f)}
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5"
                >
                  <PenTool className="w-3.5 h-3.5" /> Sign Document
                </button>
              ) : (
                <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-4 h-4" /> Signed & Verified
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Signature Modal */}
      {signingTarget && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 animate-scale-up">
            <h3 className="text-base font-bold text-slate-900 mb-1">{signingTarget.title}</h3>
            <p className="text-xs text-slate-500 mb-4">Please read carefully before affixing your electronic signature</p>

            {signSuccess ? (
              <div className="p-6 text-center space-y-2">
                <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
                <h4 className="text-sm font-bold text-slate-900">Signed & Submitted!</h4>
                <p className="text-xs text-slate-500">A SHA-256 encrypted audit record has been dispatched to clinic doctors.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmitSignature} className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 max-h-48 overflow-y-auto leading-relaxed font-serif">
                  {signingTarget.legal_text}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Legal Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={signedName}
                    onChange={(e) => setSignedName(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                {/* Digital Signature Canvas Simulator */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Draw Signature (or type your legal initials)
                  </label>
                  <div className="h-24 bg-slate-50 border-2 border-dashed border-slate-200 rounded-xl flex items-center justify-center text-slate-400 font-serif italic text-lg select-none">
                    {signedName}
                  </div>
                </div>

                <div className="flex items-start gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="consent-check"
                    required
                    checked={hasAgreed}
                    onChange={(e) => setHasAgreed(e.target.checked)}
                    className="mt-0.5 rounded text-teal-600 focus:ring-teal-500"
                  />
                  <label htmlFor="consent-check" className="text-xs text-slate-600 leading-tight">
                    I agree to sign this medical record electronically under the Uniform Electronic Transactions Act.
                  </label>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setSigningTarget(null)}
                    className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!hasAgreed}
                    className="px-5 py-2 text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-50 rounded-xl shadow-xs transition"
                  >
                    Affix Signature
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </PortalShell>
  );
}

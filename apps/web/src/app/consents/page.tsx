"use client";

import Link from "next/link";
import React, { useState } from "react";
import {
  FileText,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertCircle,
  Eye,
  Plus,
  Search,
  Filter,
  UserCheck,
  Hash,
  Download,
} from "lucide-react";
import type { FormTemplateRead, PatientFormRead, ConsentRecordRead } from "./types";

const mockTemplates: FormTemplateRead[] = [
  {
    id: "tmpl-1",
    clinic_id: "clinic-1",
    title: "Informed Consent for Surgical Tooth Extraction",
    code: "CONSENT-EXT-01",
    version: 2,
    consent_type: "PROCEDURE",
    description: "Standard surgical consent covering local anesthesia, risks of alveolar osteitis, nerve paresthesia, and sinus involvement.",
    content_markdown: "I authorize Dr. David Tennant to perform the extraction of tooth/teeth indicated...",
    schema_json: { questions: [{ id: "q1", label: "Are you taking blood thinners?", type: "boolean" }] },
    requires_signature: true,
    requires_witness: true,
    is_active: true,
    created_at: "2026-08-01T10:00:00Z",
  },
  {
    id: "tmpl-2",
    clinic_id: "clinic-1",
    title: "Root Canal Therapy (Endodontics) Consent",
    code: "CONSENT-RCT-01",
    version: 1,
    consent_type: "PROCEDURE",
    description: "Informed consent covering procedural steps, canal anatomy variations, post-op flare-ups, and obligatory crown restoration.",
    content_markdown: "I understand that root canal treatment is intended to save a damaged or infected tooth...",
    schema_json: { questions: [] },
    requires_signature: true,
    requires_witness: false,
    is_active: true,
    created_at: "2026-08-05T10:00:00Z",
  },
  {
    id: "tmpl-3",
    clinic_id: "clinic-1",
    title: "Adult Dental Implant Placement Consent",
    code: "CONSENT-IMP-01",
    version: 1,
    consent_type: "PROCEDURE",
    description: "Covers titanium fixture placement, bone grafting risks, osseointegration failure probability, and maintenance protocol.",
    content_markdown: "I understand that dental implants require surgical placement in jawbone...",
    schema_json: { questions: [] },
    requires_signature: true,
    requires_witness: true,
    is_active: true,
    created_at: "2026-08-10T10:00:00Z",
  },
];

const mockPatientForms: PatientFormRead[] = [
  {
    id: "pf-1",
    clinic_id: "clinic-1",
    patient_id: "p-1",
    patient_name: "Donna Noble",
    template_id: "tmpl-1",
    template_title: "Informed Consent for Surgical Tooth Extraction",
    status: "SUBMITTED",
    responses_json: { q1: false },
    patient_signature: "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
    submitted_at: "2026-09-08T09:30:00Z",
    created_at: "2026-09-07T14:00:00Z",
  },
  {
    id: "pf-2",
    clinic_id: "clinic-1",
    patient_id: "p-2",
    patient_name: "Rose Tyler",
    template_id: "tmpl-2",
    template_title: "Root Canal Therapy (Endodontics) Consent",
    status: "APPROVED",
    patient_signature: "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
    submitted_at: "2026-09-06T11:00:00Z",
    reviewed_by_name: "Dr. David Tennant",
    reviewed_at: "2026-09-06T11:30:00Z",
    review_notes: "Patient signed prior to obturation visit. All risks discussed.",
    created_at: "2026-09-05T10:00:00Z",
  },
];

const mockSignedConsents: ConsentRecordRead[] = [
  {
    id: "cr-1",
    clinic_id: "clinic-1",
    patient_id: "p-2",
    patient_name: "Rose Tyler",
    consent_type: "PROCEDURE",
    title: "Root Canal Therapy Consent - Tooth #19",
    legal_text: "I hereby consent to endodontic therapy on tooth #19...",
    signed_by_name: "Rose Tyler",
    signer_relationship: "SELF",
    witness_name: "Nurse Sarah Jane",
    ip_address: "192.168.1.45",
    audit_hash: "a4f8803bc398c8de1512dbb83e6022e37452d3a3d5e2195f2a1b9e879a952627",
    signed_at: "2026-09-06T11:00:00Z",
    created_at: "2026-09-06T11:00:00Z",
  },
];

export default function ConsentsPage() {
  const [tab, setTab] = useState<"queue" | "templates" | "audit">("queue");
  const [forms, setForms] = useState(mockPatientForms);
  const [selectedForm, setSelectedForm] = useState<PatientFormRead | null>(null);
  const [reviewNote, setReviewNote] = useState("");

  const handleApprove = (id: string) => {
    setForms(
      forms.map((f) =>
        f.id === id
          ? {
              ...f,
              status: "APPROVED",
              reviewed_by_name: "Dr. David Tennant",
              reviewed_at: new Date().toISOString(),
              review_notes: reviewNote || "Clinically verified and countersigned.",
            }
          : f
      )
    );
    setSelectedForm(null);
    setReviewNote("");
  };

  const handleReject = (id: string) => {
    setForms(
      forms.map((f) =>
        f.id === id
          ? {
              ...f,
              status: "REJECTED",
              reviewed_by_name: "Dr. David Tennant",
              reviewed_at: new Date().toISOString(),
              review_notes: reviewNote || "Form missing mandatory answers.",
            }
          : f
      )
    );
    setSelectedForm(null);
    setReviewNote("");
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-sm font-medium text-slate-500 hover:text-slate-900">
              ← Dashboard
            </Link>
            <span className="text-slate-300">/</span>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-teal-50 text-teal-700 rounded-lg">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-900">Digital Consent & Legal Forms</h1>
                <p className="text-xs text-slate-500">
                  Electronic patient signatures, doctor reviews & SHA-256 audit integrity logs
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm transition">
              <Plus className="w-4 h-4" /> New Form Template
            </button>
          </div>
        </div>

        {/* Tab Strip */}
        <div className="max-w-7xl mx-auto mt-4 flex gap-2 border-b border-slate-200 text-sm">
          <button
            onClick={() => setTab("queue")}
            className={`pb-2.5 px-3 font-medium border-b-2 flex items-center gap-1.5 ${
              tab === "queue"
                ? "border-teal-600 text-teal-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <Clock className="w-4 h-4" /> Patient Submissions Queue
            <span className="px-1.5 py-0.5 text-xs bg-amber-100 text-amber-800 rounded-full font-bold">
              {forms.filter((f) => f.status === "SUBMITTED").length}
            </span>
          </button>
          <button
            onClick={() => setTab("templates")}
            className={`pb-2.5 px-3 font-medium border-b-2 flex items-center gap-1.5 ${
              tab === "templates"
                ? "border-teal-600 text-teal-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <FileText className="w-4 h-4" /> Consent Templates ({mockTemplates.length})
          </button>
          <button
            onClick={() => setTab("audit")}
            className={`pb-2.5 px-3 font-medium border-b-2 flex items-center gap-1.5 ${
              tab === "audit"
                ? "border-teal-600 text-teal-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <ShieldCheck className="w-4 h-4" /> Signed Audit Vault
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* TAB 1: SUBMISSIONS QUEUE */}
        {tab === "queue" && (
          <div className="space-y-4">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
              <div className="p-4 bg-slate-50 flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <span>Patient & Template</span>
                <span>Submission Date</span>
                <span>Status</span>
                <span className="text-right">Action</span>
              </div>

              {forms.map((f) => (
                <div key={f.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{f.patient_name}</h4>
                    <p className="text-xs text-slate-500 mt-0.5">{f.template_title}</p>
                    {f.review_notes && (
                      <p className="text-xs text-slate-600 mt-1 italic bg-slate-50 p-1.5 rounded">
                        Note: {f.review_notes}
                      </p>
                    )}
                  </div>

                  <div className="text-xs text-slate-500">
                    {f.submitted_at ? new Date(f.submitted_at).toLocaleDateString() : "Pending"}
                  </div>

                  <div>
                    <span
                      className={`text-xs px-2.5 py-1 rounded-full font-semibold ${
                        f.status === "APPROVED"
                          ? "bg-emerald-100 text-emerald-800"
                          : f.status === "REJECTED"
                          ? "bg-rose-100 text-rose-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {f.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {f.status === "SUBMITTED" ? (
                      <button
                        onClick={() => setSelectedForm(f)}
                        className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold transition"
                      >
                        Review & Countersign
                      </button>
                    ) : (
                      <span className="text-xs text-slate-400 font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Reviewed
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 2: TEMPLATES */}
        {tab === "templates" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {mockTemplates.map((t) => (
              <div key={t.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                      {t.code}
                    </span>
                    <span className="text-xs text-slate-400 font-semibold">v{t.version}.0</span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 mb-2">{t.title}</h3>
                  <p className="text-xs text-slate-600 mb-4 leading-relaxed">{t.description}</p>
                </div>

                <div className="pt-3 border-t border-slate-100 space-y-2 text-xs text-slate-500">
                  <div className="flex justify-between">
                    <span>Type:</span>
                    <strong className="text-slate-700">{t.consent_type}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Requires Witness:</span>
                    <strong className="text-slate-700">{t.requires_witness ? "Yes" : "No"}</strong>
                  </div>
                  <button className="w-full mt-2 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition">
                    Assign to Patient
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TAB 3: SIGNED AUDIT VAULT */}
        {tab === "audit" && (
          <div className="space-y-4">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="p-4 bg-teal-900 text-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  <span className="text-sm font-bold">Cryptographically Verified Consent Records</span>
                </div>
                <span className="text-xs text-teal-200">SHA-256 Tamper-Proof Audit Trail</span>
              </div>

              <div className="divide-y divide-slate-100">
                {mockSignedConsents.map((c) => (
                  <div key={c.id} className="p-5 hover:bg-slate-50 transition space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">{c.title}</h4>
                        <p className="text-xs text-slate-500">
                          Signer: <strong className="text-slate-800">{c.signed_by_name}</strong> (Relationship: {c.signer_relationship})
                        </p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-slate-400">Signed Timestamp</span>
                        <p className="text-xs font-semibold text-slate-700">
                          {new Date(c.signed_at).toLocaleString()}
                        </p>
                      </div>
                    </div>

                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs font-mono text-slate-600 flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2 truncate">
                        <Hash className="w-4 h-4 text-slate-400 shrink-0" />
                        <span className="truncate">Hash: {c.audit_hash}</span>
                      </div>
                      <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-bold shrink-0">
                        VERIFIED
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                      <span>Witness: {c.witness_name || "N/A"} · IP: {c.ip_address}</span>
                      <button className="text-teal-600 hover:text-teal-800 font-semibold flex items-center gap-1">
                        <Download className="w-3.5 h-3.5" /> Download Legal PDF
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Modal: Review & Countersign */}
        {selectedForm && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 animate-scale-up">
              <h3 className="text-base font-bold text-slate-900 mb-1">Doctor Review & Countersign</h3>
              <p className="text-xs text-slate-500 mb-4">{selectedForm.template_title}</p>

              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-4 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Patient:</span>
                  <strong className="text-slate-800">{selectedForm.patient_name}</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Submitted:</span>
                  <span className="text-slate-800">{new Date(selectedForm.submitted_at || "").toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Patient Digital Signature:</span>
                  <span className="text-emerald-700 font-mono font-bold bg-emerald-50 px-2 py-0.5 rounded">
                    CAPTURED
                  </span>
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Doctor Clinical Review Notes
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Procedure explained, questions answered, countersigned."
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  className="w-full p-3 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setSelectedForm(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleReject(selectedForm.id)}
                  className="px-4 py-2 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 rounded-lg transition"
                >
                  Reject Form
                </button>
                <button
                  onClick={() => handleApprove(selectedForm.id)}
                  className="px-5 py-2 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm transition"
                >
                  Approve & Countersign
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

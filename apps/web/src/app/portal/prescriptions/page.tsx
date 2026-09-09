"use client";

import React, { useState } from "react";
import {
  Pill,
  Download,
  Calendar,
  User,
  Clock,
  CheckCircle2,
  FileText,
} from "lucide-react";
import { PortalShell } from "../portal-shell";
import type { PortalPrescriptionRead } from "../types";

const mockPrescriptions: PortalPrescriptionRead[] = [
  {
    id: "rx-1",
    prescription_number: "RX-2026-0001",
    date: "2026-09-05",
    dentist_name: "Dr. David Tennant",
    diagnosis: "Acute periapical periodontitis & deep restoration",
    notes: "Take amoxicillin after food. Complete the full 5-day antibiotic course.",
    items: [
      {
        id: "rxi-1",
        medicine_name: "Amoxicillin 500mg",
        dosage: "1 capsule",
        frequency: "TDS (Thrice daily)",
        duration: "5 days",
        instructions: "Take with full glass of water after food",
      },
      {
        id: "rxi-2",
        medicine_name: "Ibuprofen + Paracetamol 400/325mg",
        dosage: "1 tablet",
        frequency: "SOS (As needed for pain)",
        duration: "3 days",
        instructions: "Maximum 3 doses in 24 hours",
      },
    ],
  },
];

export default function PortalPrescriptionsPage() {
  const [prescriptions] = useState(mockPrescriptions);
  const [downloadMsg, setDownloadMsg] = useState<string | null>(null);

  const handleDownloadPDF = (rxNum: string) => {
    setDownloadMsg(`Downloading certified digital prescription ${rxNum}.pdf...`);
    setTimeout(() => setDownloadMsg(null), 3500);
  };

  return (
    <PortalShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Your Prescriptions</h1>
          <p className="text-xs text-slate-500">Official digital prescriptions issued by your clinic dentist</p>
        </div>
      </div>

      {downloadMsg && (
        <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> {downloadMsg}
        </div>
      )}

      <div className="space-y-6">
        {prescriptions.map((rx) => (
          <div key={rx.id} className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            {/* Rx Header */}
            <div className="p-5 bg-slate-50 border-b border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="p-1 bg-teal-100 text-teal-800 rounded font-mono text-xs font-bold">℞</span>
                  <h3 className="text-sm font-bold text-slate-900">{rx.prescription_number}</h3>
                  <span className="text-xs text-slate-400">· {rx.date}</span>
                </div>
                <p className="text-xs text-slate-600 mt-1">
                  Issued by: <strong className="text-slate-800">{rx.dentist_name}</strong>
                </p>
                {rx.diagnosis && (
                  <p className="text-xs text-slate-500 mt-0.5">
                    Clinical Diagnosis: <span className="italic">{rx.diagnosis}</span>
                  </p>
                )}
              </div>

              <button
                onClick={() => handleDownloadPDF(rx.prescription_number)}
                className="px-3.5 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5"
              >
                <Download className="w-4 h-4" /> Download PDF
              </button>
            </div>

            {/* Medicines List */}
            <div className="p-5 space-y-4">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Prescribed Medicines</h4>
              <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl overflow-hidden">
                {rx.items.map((item, idx) => (
                  <div key={item.id} className="p-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 hover:bg-slate-50/50">
                    <div>
                      <span className="text-xs font-bold text-slate-900">
                        {idx + 1}. {item.medicine_name}
                      </span>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Instructions: {item.instructions || "As directed"}
                      </p>
                    </div>
                    <div className="text-left sm:text-right text-xs">
                      <span className="font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                        {item.dosage} · {item.frequency}
                      </span>
                      <span className="block text-slate-400 mt-0.5">Duration: {item.duration}</span>
                    </div>
                  </div>
                ))}
              </div>

              {rx.notes && (
                <div className="p-3 bg-teal-50/50 rounded-xl text-xs text-slate-600 border border-teal-100/60">
                  <strong>Doctor Advice:</strong> {rx.notes}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </PortalShell>
  );
}

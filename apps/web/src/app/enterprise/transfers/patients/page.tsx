"use client";

import { useState } from "react";
import {
  ArrowLeftRight,
  Plus,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  UserCheck,
  AlertTriangle,
  Merge,
  Sparkles,
} from "lucide-react";
import { EnterpriseNav } from "../../nav";
import { DuplicatePatientMatch, PatientTransfer, TransferStatus } from "../../types";

const INITIAL_TRANSFERS: PatientTransfer[] = [
  {
    id: "tr-1",
    organization_id: "org-1",
    patient_id: "p-101",
    patient_name: "Rahul Mehra",
    from_clinic_id: "br-2",
    from_clinic_name: "Indiranagar Dental Lounge",
    to_clinic_id: "br-1",
    to_clinic_name: "Central Flagship Clinic",
    status: "PENDING",
    transfer_reason: "Referred for full-mouth digital implant rehabilitation",
    notes: "Patient moving to Delhi for work",
    created_at: "2026-09-08T08:00:00Z",
    updated_at: "2026-09-08T08:00:00Z",
  },
  {
    id: "tr-2",
    organization_id: "org-1",
    patient_id: "p-102",
    patient_name: "Kavita Rao",
    from_clinic_id: "br-3",
    from_clinic_name: "Whitefield Specialty Wing",
    to_clinic_id: "br-2",
    to_clinic_name: "Indiranagar Dental Lounge",
    status: "APPROVED",
    transfer_reason: "Closer to new residence",
    created_at: "2026-09-07T11:30:00Z",
    updated_at: "2026-09-07T14:20:00Z",
  },
];

const INITIAL_DUPLICATES: DuplicatePatientMatch[] = [
  {
    patient_id: "dup-1",
    clinic_id: "br-2",
    clinic_name: "Indiranagar Dental Lounge",
    full_name: "Amitabh Kumar",
    phone: "+91 98765 43210",
    email: "amitabh.k@gmail.com",
    date_of_birth: "1988-04-14",
    similarity_score: 0.95,
    matched_fields: ["phone", "email", "name"],
  },
  {
    patient_id: "dup-2",
    clinic_id: "br-1",
    clinic_name: "Central Flagship Clinic",
    full_name: "Amitabh Kumar",
    phone: "+91 98765 43210",
    email: "amitabh.k@gmail.com",
    date_of_birth: "1988-04-14",
    similarity_score: 0.95,
    matched_fields: ["phone", "email", "name"],
  },
];

export default function PatientTransfersPage() {
  const [transfers, setTransfers] = useState<PatientTransfer[]>(INITIAL_TRANSFERS);
  const [activeTab, setActiveTab] = useState<"transfers" | "duplicates">("transfers");
  const [duplicateSearch, setDuplicateSearch] = useState("9876543210");
  const [merged, setMerged] = useState(false);

  const handleAction = (id: string, newStatus: TransferStatus) => {
    setTransfers(
      transfers.map((t) => (t.id === id ? { ...t, status: newStatus, updated_at: new Date().toISOString() } : t))
    );
  };

  const handleMerge = () => {
    setMerged(true);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <EnterpriseNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Cross-Branch Patient Management</h1>
            <p className="text-xs text-slate-500 mt-1">
              Transfer patient medical charts between branches, or detect & merge duplicate network profiles.
            </p>
          </div>

          <div className="flex items-center gap-1 bg-slate-200/70 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab("transfers")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === "transfers" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Transfer Queue ({transfers.filter((t) => t.status === "PENDING").length})
            </button>
            <button
              onClick={() => setActiveTab("duplicates")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === "duplicates" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Duplicate Detector & Merge
            </button>
          </div>
        </div>

        {activeTab === "transfers" ? (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-500 font-semibold uppercase bg-slate-50/70">
                    <th className="py-3 px-4">Patient</th>
                    <th className="py-3 px-4">From Branch</th>
                    <th className="py-3 px-4">To Branch</th>
                    <th className="py-3 px-4">Clinical Reason</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {transfers.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-slate-900">{t.patient_name}</td>
                      <td className="py-3.5 px-4 text-slate-600">{t.from_clinic_name}</td>
                      <td className="py-3.5 px-4 font-medium text-indigo-600">{t.to_clinic_name}</td>
                      <td className="py-3.5 px-4 text-slate-600 max-w-xs truncate">{t.transfer_reason}</td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${
                            t.status === "PENDING"
                              ? "bg-amber-50 text-amber-700 border-amber-200"
                              : t.status === "APPROVED"
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                              : "bg-rose-50 text-rose-700 border-rose-200"
                          }`}
                        >
                          {t.status === "PENDING" && <Clock className="w-3 h-3" />}
                          {t.status === "APPROVED" && <CheckCircle2 className="w-3 h-3" />}
                          {t.status === "REJECTED" && <XCircle className="w-3 h-3" />}
                          {t.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {t.status === "PENDING" ? (
                          <div className="inline-flex items-center gap-1.5">
                            <button
                              onClick={() => handleAction(t.id, "APPROVED")}
                              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-medium shadow-xs"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleAction(t.id, "REJECTED")}
                              className="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded font-medium"
                            >
                              Reject
                            </button>
                          </div>
                        ) : (
                          <span className="text-slate-400">Processed</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center gap-2 text-indigo-700">
                <Sparkles className="w-4 h-4" />
                <h2 className="text-sm font-bold text-slate-900">AI Cross-Clinic Duplicate Resolution</h2>
              </div>
              <p className="text-xs text-slate-500">
                Identifies duplicate patient records created at different branches using phone, email, and name phonetics.
              </p>

              <div className="flex items-center gap-3 pt-2">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-2.5" />
                  <input
                    type="text"
                    value={duplicateSearch}
                    onChange={(e) => setDuplicateSearch(e.target.value)}
                    placeholder="Search by phone, email, or patient name across network..."
                    className="w-full pl-10 pr-4 py-2 bg-slate-50 text-xs border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <button className="px-4 py-2 text-xs font-semibold bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 shadow-xs">
                  Scan Network
                </button>
              </div>
            </div>

            {merged ? (
              <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-xl text-center space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                <h3 className="font-bold text-emerald-900 text-sm">Patients Successfully Merged</h3>
                <p className="text-xs text-emerald-700">
                  Appointments, odontogram charts, invoices, and treatments have been consolidated under primary profile.
                </p>
              </div>
            ) : (
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    <h3 className="font-bold text-slate-900 text-sm">Duplicate Candidate Match (95% Confidence)</h3>
                  </div>
                  <button
                    onClick={handleMerge}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-700 rounded-lg shadow-xs"
                  >
                    <Merge className="w-3.5 h-3.5" />
                    Execute Clinical Merge
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {INITIAL_DUPLICATES.map((item, idx) => (
                    <div
                      key={item.patient_id}
                      className={`p-4 rounded-xl border ${
                        idx === 0 ? "border-indigo-300 bg-indigo-50/20" : "border-slate-200 bg-slate-50/40"
                      } space-y-2 text-xs`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900">{item.full_name}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                          {idx === 0 ? "PRIMARY PROFILE" : "DUPLICATE FILE"}
                        </span>
                      </div>
                      <div className="text-slate-600">Branch: {item.clinic_name}</div>
                      <div className="text-slate-600">Phone: {item.phone}</div>
                      <div className="text-slate-600">Email: {item.email}</div>
                      <div className="text-slate-600">DOB: {item.date_of_birth}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

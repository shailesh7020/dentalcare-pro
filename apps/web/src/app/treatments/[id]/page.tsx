"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  Edit2,
  FileCheck,
  FileText,
  Lock,
  Pill,
  Printer,
  RotateCcw,
  Stethoscope,
  Trash2,
  User,
  XCircle,
  IndianRupee,
  Receipt,
  Boxes,
  Package,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import type { TreatmentDetail, TreatmentStatus } from "../types";

export default function TreatmentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();

  const [isCompleteOpen, setIsCompleteOpen] = useState(false);
  const [completeNotes, setCompleteNotes] = useState("");
  const [completeAppointment, setCompleteAppointment] = useState(true);

  const [isCancelOpen, setIsCancelOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("");

  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Fetch Treatment Detail
  const treatmentQuery = useQuery({
    queryKey: ["treatment-detail", id],
    queryFn: async () => {
      const res = await api.get<TreatmentDetail>(`/treatments/${id}`);
      return res.data;
    },
  });

  const treatmentPrescriptionsQuery = useQuery({
    queryKey: ["treatment-prescriptions", id],
    queryFn: async () => {
      const res = await api.get<any[]>(`/prescriptions/treatment/${id}`);
      return res.data;
    },
  });

  const treatmentInvoicesQuery = useQuery({
    queryKey: ["treatment-invoices", id],
    queryFn: async () => {
      const res = await api.get<any[]>(`/billing/treatment/${id}`);
      return res.data;
    },
  });

  const treatmentMaterialsQuery = useQuery({
    queryKey: ["treatment-consumed-materials", id],
    queryFn: async () => {
      const res = await api.get<{
        treatment_id: string;
        consumed_items: Array<{
          item_id: string;
          item_name: string;
          item_sku: string;
          quantity: number;
          unit: string;
          unit_cost: number;
          total_cost: number;
          batch_number?: string | null;
        }>;
        total_material_cost: number;
      }>(`/inventory/treatments/${id}/consumed-materials`);
      return res.data;
    },
  });

  const invalidateData = () => {
    void queryClient.invalidateQueries({ queryKey: ["treatment-detail", id] });
    void queryClient.invalidateQueries({ queryKey: ["treatments-list"] });
    void queryClient.invalidateQueries({ queryKey: ["treatment-dashboard-stats"] });
    void queryClient.invalidateQueries({ queryKey: ["appointments"] });
  };

  // Complete Treatment Mutation
  const completeMutation = useMutation({
    mutationFn: async () => {
      setActionError(null);
      const res = await api.post(`/treatments/${id}/complete`, {
        notes: completeNotes.trim() || undefined,
        complete_appointment: completeAppointment,
      });
      return res.data;
    },
    onSuccess: () => {
      setIsCompleteOpen(false);
      invalidateData();
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || "Failed to complete treatment.");
    },
  });

  // Cancel Treatment Mutation
  const cancelMutation = useMutation({
    mutationFn: async () => {
      setActionError(null);
      if (!cancelReason.trim()) throw new Error("Please provide a reason for cancellation.");
      const res = await api.post(`/treatments/${id}/cancel`, {
        reason: cancelReason.trim(),
      });
      return res.data;
    },
    onSuccess: () => {
      setIsCancelOpen(false);
      invalidateData();
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || "Failed to cancel treatment.");
    },
  });

  // Delete Treatment Mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      setActionError(null);
      const res = await api.delete(`/treatments/${id}`);
      return res.data;
    },
    onSuccess: () => {
      setIsDeleteOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["treatments-list"] });
      void queryClient.invalidateQueries({ queryKey: ["treatment-dashboard-stats"] });
      router.push("/treatments");
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || "Failed to delete treatment.");
    },
  });

  if (treatmentQuery.isLoading) {
    return (
      <main className="min-h-screen bg-slate-50/60 p-8 max-w-6xl mx-auto space-y-6">
        <Skeleton className="h-12 w-1/3" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }

  const treatment = treatmentQuery.data;
  if (!treatment) {
    return (
      <main className="min-h-screen bg-slate-50/60 flex items-center justify-center p-6 text-center">
        <div>
          <AlertCircle size={40} className="text-slate-400 mx-auto mb-2" />
          <h2 className="text-base font-bold text-slate-800">Treatment Record Not Found</h2>
          <p className="text-xs text-slate-500 mt-1 mb-4">
            The requested treatment record may have been archived or deleted.
          </p>
          <Link
            href="/treatments"
            className="px-3.5 py-2 text-xs font-semibold bg-teal-700 text-white rounded-md"
          >
            Back to Treatments
          </Link>
        </div>
      </main>
    );
  }

  const isCompleted = treatment.status === "COMPLETED";
  const isCancelled = treatment.status === "CANCELLED";

  const getStatusBadge = (st: TreatmentStatus) => {
    switch (st) {
      case "COMPLETED":
        return <Badge variant="success">Completed</Badge>;
      case "IN_PROGRESS":
        return <Badge variant="warning">In Progress</Badge>;
      case "PLANNED":
        return <Badge variant="info">Planned</Badge>;
      case "CANCELLED":
        return <Badge variant="destructive">Cancelled</Badge>;
      default:
        return <Badge variant="secondary">{st}</Badge>;
    }
  };

  return (
    <main className="min-h-screen bg-slate-50/60 pb-24">
      {/* Top Breadcrumb & Action Bar */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/treatments"
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
              title="Back to Treatments Directory"
            >
              <ArrowLeft size={18} />
            </Link>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl font-bold font-mono text-slate-900">
                  {treatment.treatment_number}
                </h1>
                {getStatusBadge(treatment.status)}
                {treatment.is_override && (
                  <span className="text-[10px] font-bold px-2 py-0.5 bg-purple-50 text-purple-700 border border-purple-200 rounded uppercase">
                    Admin Override
                  </span>
                )}
                {isCompleted && (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                    <Lock size={12} /> Permanent Clinical Record
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Recorded on {new Date(treatment.created_at).toLocaleString()}
                {treatment.completed_at &&
                  ` · Completed on ${new Date(treatment.completed_at).toLocaleString()}`}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <Link
              href={`/billing/new?patient_id=${treatment.patient_id}&treatment_id=${treatment.id}&appointment_id=${treatment.appointment_id || ""}`}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-md shadow-2xs transition-colors"
            >
              <IndianRupee size={13} /> Generate Invoice
            </Link>

            {!isCompleted && !isCancelled && (
              <>
                <Link
                  href={`/prescriptions/new?patient_id=${treatment.patient_id}&treatment_id=${treatment.id}&appointment_id=${treatment.appointment_id}`}
                  className="inline-flex items-center gap-1.5 px-3 py-2 bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 font-semibold text-xs rounded-md shadow-2xs transition-colors"
                >
                  <Pill size={13} /> Issue Prescription
                </Link>

                <Link
                  href={`/treatments/${id}/edit`}
                  className="inline-flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-md shadow-2xs transition-colors"
                >
                  <Edit2 size={13} /> Edit Record
                </Link>

                <button
                  type="button"
                  onClick={() => setIsCancelOpen(true)}
                  className="inline-flex items-center gap-1.5 px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-semibold text-xs rounded-md transition-colors"
                >
                  <XCircle size={13} /> Cancel
                </button>

                <button
                  type="button"
                  onClick={() => setIsCompleteOpen(true)}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs rounded-md shadow-2xs transition-colors"
                >
                  <CheckCircle2 size={14} /> Complete Treatment
                </button>
              </>
            )}

            {!isCompleted && (
              <button
                type="button"
                onClick={() => setIsDeleteOpen(true)}
                className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                title="Delete Treatment (Admin only)"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* Error Alert Bar */}
        {actionError && (
          <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-3 text-xs text-rose-900 animate-in fade-in">
            <AlertCircle size={18} className="text-rose-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Error:</span> {actionError}
            </div>
          </div>
        )}

        {/* Completed Lock Banner */}
        {isCompleted && (
          <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs text-emerald-900">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 size={18} className="text-emerald-600 shrink-0" />
              <span>
                <b>Treatment Completed & Locked:</b> This clinical record is finalized. Any subsequent
                treatments require opening a new clinical entry.
              </span>
            </div>
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white border border-emerald-300 text-emerald-800 rounded font-medium text-xs hover:bg-emerald-100"
            >
              <Printer size={13} /> Print Chart
            </button>
          </div>
        )}

        {/* Cancelled Banner */}
        {isCancelled && (
          <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-2.5 text-xs text-rose-900">
            <AlertCircle size={18} className="text-rose-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Treatment Cancelled:</span>{" "}
              {treatment.cancellation_reason || "No cancellation reason provided."}
            </div>
          </div>
        )}

        {/* Patient & Clinician Overview Card */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-xs p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Patient Info */}
            <div className="flex items-start gap-3.5">
              <div className="w-12 h-12 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-base border border-teal-300">
                {treatment.patient_name
                  ? treatment.patient_name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                      .slice(0, 2)
                      .toUpperCase()
                  : "PT"}
              </div>
              <div>
                <span className="text-[11px] uppercase tracking-wider font-bold text-slate-400 block mb-0.5">
                  Patient
                </span>
                <Link
                  href={`/patients/${treatment.patient_id}`}
                  className="text-base font-bold text-slate-900 hover:text-teal-700 hover:underline"
                >
                  {treatment.patient_name || "Unknown Patient"}
                </Link>
                <div className="text-xs text-slate-500 mt-0.5 font-mono">
                  {treatment.patient_number} · {treatment.patient_phone}
                </div>
              </div>
            </div>

            {/* Clinician Info */}
            <div>
              <span className="text-[11px] uppercase tracking-wider font-bold text-slate-400 block mb-0.5">
                Attending Clinician
              </span>
              <div className="text-base font-bold text-slate-900">
                Dr. {treatment.dentist_name || "Unassigned"}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">Licensed Dental Practitioner</p>
            </div>

            {/* Appointment Reference */}
            <div>
              <span className="text-[11px] uppercase tracking-wider font-bold text-slate-400 block mb-0.5">
                Clinical Visit Linkage
              </span>
              <div className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                <Calendar size={13} className="text-teal-700" />
                Appointment #{treatment.appointment_number || "APT"}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Session Date: {treatment.appointment_date || "N/A"}
              </p>
            </div>
          </div>

          {/* Medical Alerts Bar */}
          {treatment.patient_medical_alerts && treatment.patient_medical_alerts.length > 0 && (
            <div className="mt-5 pt-4 border-t border-slate-100 flex items-center gap-2 flex-wrap">
              <span className="text-xs font-bold text-rose-800 flex items-center gap-1">
                <AlertTriangle size={14} className="text-rose-600" /> Medical Alerts:
              </span>
              {treatment.patient_medical_alerts.map((alert, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-0.5 bg-rose-50 text-rose-700 border border-rose-200 rounded-full text-xs font-semibold"
                >
                  {alert}
                </span>
              ))}
            </div>
          )}
        </section>

        {/* Clinical Diagnosis & Findings Card */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-xs p-6">
          <h2 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
            <Stethoscope size={16} className="text-teal-700" /> Clinical Diagnosis & Findings
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-xs">
            <div className="sm:col-span-3">
              <span className="text-slate-400 block font-medium mb-1">Primary Diagnosis</span>
              <div className="text-sm font-bold text-slate-900 bg-slate-50 p-3 rounded border border-slate-200">
                {treatment.diagnosis}
              </div>
            </div>

            <div>
              <span className="text-slate-400 block font-medium mb-1">Chief Complaint</span>
              <p className="text-slate-800 bg-slate-50/60 p-3 rounded border border-slate-100">
                {treatment.chief_complaint || "None recorded"}
              </p>
            </div>

            <div>
              <span className="text-slate-400 block font-medium mb-1">Clinical Findings</span>
              <p className="text-slate-800 bg-slate-50/60 p-3 rounded border border-slate-100">
                {treatment.clinical_findings || "None recorded"}
              </p>
            </div>

            <div>
              <span className="text-slate-400 block font-medium mb-1">Staged Treatment Plan</span>
              <p className="text-slate-800 bg-slate-50/60 p-3 rounded border border-slate-100">
                {treatment.treatment_plan || "None recorded"}
              </p>
            </div>
          </div>
        </section>

        {/* Procedures Table Card */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                Dental Procedures ({treatment.procedures.length})
              </h2>
              <p className="text-xs text-slate-500">
                Individual clinical procedures charted and performed.
              </p>
            </div>

            <div className="text-right">
              <span className="text-xs text-slate-400 block">Total Clinical Cost</span>
              <span className="text-base font-bold font-mono text-slate-900">
                ₹{treatment.total_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-6">Procedure Name</th>
                  <th className="py-3 px-4">Tooth #</th>
                  <th className="py-3 px-4 text-center">Qty</th>
                  <th className="py-3 px-4 text-center">Duration</th>
                  <th className="py-3 px-4 text-right">Unit Cost</th>
                  <th className="py-3 px-6 text-right">Line Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {treatment.procedures.map((p, idx) => (
                  <tr key={p.id || idx} className="hover:bg-slate-50/60">
                    <td className="py-3 px-6">
                      <div className="font-semibold text-slate-900">{p.procedure_name}</div>
                      {p.notes && <p className="text-[11px] text-slate-400 mt-0.5">{p.notes}</p>}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-slate-700">
                      {p.tooth_number ? `#${p.tooth_number}` : "—"}
                    </td>
                    <td className="py-3 px-4 text-center">{p.quantity}</td>
                    <td className="py-3 px-4 text-center text-slate-500">{p.duration} min</td>
                    <td className="py-3 px-4 text-right font-mono text-slate-600">
                      ₹{Number(p.cost).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-6 text-right font-mono font-bold text-slate-900">
                      ₹
                      {(Number(p.cost) * Number(p.quantity)).toLocaleString("en-IN", {
                        minimumFractionDigits: 2,
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* SOAP Notes Card */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-xs p-6">
          <h2 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
            <Activity size={16} className="text-teal-700" /> Longitudinal SOAP Notes
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="bg-slate-50/70 p-4 rounded-lg border border-slate-200">
              <span className="font-bold text-teal-800 text-[11px] uppercase tracking-wider block mb-1">
                [S] Subjective History
              </span>
              <p className="text-slate-700 whitespace-pre-wrap">
                {treatment.soap_subjective || "No subjective notes recorded."}
              </p>
            </div>

            <div className="bg-slate-50/70 p-4 rounded-lg border border-slate-200">
              <span className="font-bold text-teal-800 text-[11px] uppercase tracking-wider block mb-1">
                [O] Objective Examination
              </span>
              <p className="text-slate-700 whitespace-pre-wrap">
                {treatment.soap_objective || "No objective findings recorded."}
              </p>
            </div>

            <div className="bg-slate-50/70 p-4 rounded-lg border border-slate-200">
              <span className="font-bold text-teal-800 text-[11px] uppercase tracking-wider block mb-1">
                [A] Assessment & Staging
              </span>
              <p className="text-slate-700 whitespace-pre-wrap">
                {treatment.soap_assessment || "No assessment notes recorded."}
              </p>
            </div>

            <div className="bg-slate-50/70 p-4 rounded-lg border border-slate-200">
              <span className="font-bold text-teal-800 text-[11px] uppercase tracking-wider block mb-1">
                [P] Plan & Prescriptions
              </span>
              <p className="text-slate-700 whitespace-pre-wrap">
                {treatment.soap_plan || "No plan recorded."}
              </p>
            </div>
          </div>
        </section>

        {/* Anaesthesia, Medicines & Clinical Notes */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-xs p-6">
          <h2 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
            <Pill size={16} className="text-teal-700" /> Pharmacology & Session Notes
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
            <div>
              <span className="text-slate-400 font-medium block mb-1">Local Anaesthesia</span>
              <p className="text-slate-800 bg-slate-50 p-3 rounded border border-slate-100">
                {treatment.local_anaesthesia_used || "None administered"}
              </p>
            </div>

            <div>
              <span className="text-slate-400 font-medium block mb-1">
                Medicines Prescribed / Dispensed
              </span>
              <p className="text-slate-800 bg-slate-50 p-3 rounded border border-slate-100">
                {treatment.medicines_used || "None prescribed"}
              </p>
            </div>

            <div className="sm:col-span-2">
              <span className="text-slate-400 font-medium block mb-1">General Clinical Notes</span>
              <p className="text-slate-800 bg-slate-50 p-3 rounded border border-slate-100 whitespace-pre-wrap">
                {treatment.clinical_notes || "No additional notes recorded."}
              </p>
            </div>
          </div>
        </section>

        {/* Linked Prescriptions Card */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Pill size={16} className="text-teal-700" /> Prescriptions & Medication Orders ({treatmentPrescriptionsQuery.data?.length ?? 0})
            </h2>
            <Link
              href={`/prescriptions/new?patient_id=${treatment.patient_id}&treatment_id=${treatment.id}&appointment_id=${treatment.appointment_id}`}
              className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800 bg-teal-50 hover:bg-teal-100 px-3 py-1.5 rounded-md transition-colors"
            >
              + Write Prescription
            </Link>
          </div>

          {treatmentPrescriptionsQuery.isLoading ? (
            <Skeleton className="h-14 w-full" />
          ) : treatmentPrescriptionsQuery.data && treatmentPrescriptionsQuery.data.length > 0 ? (
            <div className="divide-y divide-slate-100 text-xs">
              {treatmentPrescriptionsQuery.data.map((rx: any) => (
                <div key={rx.id} className="py-3 flex items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <Link
                        href={`/prescriptions/${rx.id}`}
                        className="font-mono font-bold text-teal-800 hover:underline"
                      >
                        {rx.prescription_number}
                      </Link>
                      <span
                        className={`text-[10px] font-semibold px-1.5 py-0.2 rounded ${
                          rx.status === "ISSUED"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {rx.status}
                      </span>
                    </div>
                    <p className="text-slate-700 mt-0.5 font-medium">{rx.diagnosis}</p>
                    <p className="text-[11px] text-slate-500">
                      {rx.items_count} item(s): {rx.items?.map((it: any) => it.medicine_name).join(", ")}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/prescriptions/${rx.id}`}
                      className="px-2.5 py-1 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded"
                    >
                      View Details &rarr;
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No prescriptions issued for this treatment record yet.</p>
          )}
        </section>

        {/* Linked Invoices Card */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Receipt size={16} className="text-blue-600" /> Invoices & Billing ({treatmentInvoicesQuery.data?.length ?? 0})
            </h2>
            <Link
              href={`/billing/new?patient_id=${treatment.patient_id}&treatment_id=${treatment.id}&appointment_id=${treatment.appointment_id || ""}`}
              className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-md transition-colors"
            >
              + Create Invoice
            </Link>
          </div>

          {treatmentInvoicesQuery.isLoading ? (
            <Skeleton className="h-14 w-full" />
          ) : treatmentInvoicesQuery.data && treatmentInvoicesQuery.data.length > 0 ? (
            <div className="divide-y divide-slate-100 text-xs">
              {treatmentInvoicesQuery.data.map((inv: any) => (
                <div key={inv.id} className="py-3 flex items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <Link
                        href={`/billing/${inv.id}`}
                        className="font-mono font-bold text-blue-600 hover:underline"
                      >
                        {inv.invoice_number}
                      </Link>
                      <span
                        className={`text-[10px] font-semibold px-1.5 py-0.2 rounded ${
                          inv.status === "PAID"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : inv.status === "PARTIALLY_PAID"
                            ? "bg-amber-50 text-amber-700 border border-amber-200"
                            : "bg-rose-50 text-rose-700 border border-rose-200"
                        }`}
                      >
                        {inv.status}
                      </span>
                    </div>
                    <p className="text-slate-700 mt-0.5 font-medium">
                      Total: ₹{inv.grand_total.toLocaleString("en-IN", { minimumFractionDigits: 2 })} • Paid: ₹{inv.amount_paid.toLocaleString("en-IN", { minimumFractionDigits: 2 })} • Balance: ₹{inv.balance_due.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/billing/${inv.id}`}
                      className="px-2.5 py-1 text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded"
                    >
                      View Invoice &rarr;
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No invoices generated for this treatment record yet.</p>
          )}
        </section>

        {/* Consumed Clinical Materials Card */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Boxes size={16} className="text-teal-600" /> Consumed Clinical Materials & Stock
              </h2>
              <p className="text-[11px] text-slate-500">
                Procedural supplies and medications deducted from operatory stock ledger.
              </p>
            </div>
            <Link
              href="/inventory"
              className="text-xs font-semibold text-teal-600 hover:text-teal-700 bg-teal-50 hover:bg-teal-100 px-3 py-1.5 rounded-md transition-colors"
            >
              View Inventory
            </Link>
          </div>

          {treatmentMaterialsQuery.isLoading ? (
            <Skeleton className="h-16 w-full" />
          ) : treatmentMaterialsQuery.data?.consumed_items && treatmentMaterialsQuery.data.consumed_items.length > 0 ? (
            <div className="space-y-3">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b bg-slate-50 text-slate-500">
                    <tr>
                      <th className="py-2 px-3">Item Name / SKU</th>
                      <th className="py-2 px-3">Batch #</th>
                      <th className="py-2 px-3">Quantity Consumed</th>
                      <th className="py-2 px-3">Unit Cost</th>
                      <th className="py-2 px-3 text-right">Material Cost</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {treatmentMaterialsQuery.data.consumed_items.map((mat) => (
                      <tr key={mat.item_id}>
                        <td className="py-2.5 px-3">
                          <p className="font-semibold text-slate-800">{mat.item_name}</p>
                          <span className="font-mono text-[10px] text-slate-400">{mat.item_sku}</span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[11px] text-slate-600">
                          {mat.batch_number || "FIFO Auto"}
                        </td>
                        <td className="py-2.5 px-3 font-bold">
                          {mat.quantity} <span className="font-normal text-slate-500">{mat.unit}</span>
                        </td>
                        <td className="py-2.5 px-3">₹{mat.unit_cost.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-semibold text-teal-700">
                          ₹{mat.total_cost.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex justify-end pt-2 border-t text-xs">
                <span className="font-semibold text-slate-700">
                  Total Material Cost: <b className="text-teal-700">₹{treatmentMaterialsQuery.data.total_material_cost.toFixed(2)}</b>
                </span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">
              No materials consumed yet. Material consumption recipes are automatically recorded during treatment execution.
            </p>
          )}
        </section>

        {/* Follow-Up Card */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-xs p-6">
          <h2 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
            <Calendar size={16} className="text-teal-700" /> Post-Operative Follow-Up & Home Care
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
            <div>
              <span className="text-slate-400 font-medium block mb-1">Post-Op Patient Instructions</span>
              <p className="text-slate-800 bg-slate-50 p-3 rounded border border-slate-100">
                {treatment.follow_up_instructions || "Standard post-operative care."}
              </p>
            </div>

            <div>
              <span className="text-slate-400 font-medium block mb-1">Follow-Up Schedule</span>
              {treatment.follow_ups && treatment.follow_ups.length > 0 ? (
                <div className="space-y-2">
                  {treatment.follow_ups.map((f, idx) => (
                    <div
                      key={f.id || idx}
                      className="p-3 bg-teal-50/50 border border-teal-200 rounded-md flex items-center justify-between"
                    >
                      <div>
                        <div className="font-semibold text-teal-900">
                          Due Date: {f.follow_up_date}
                        </div>
                        <div className="text-[11px] text-teal-700 mt-0.5">{f.reason}</div>
                      </div>
                      <Badge variant="default">{f.status}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 bg-slate-50 p-3 rounded border border-slate-100">
                  No follow-up visits scheduled for this treatment.
                </p>
              )}
            </div>
          </div>
        </section>
      </div>

      {/* Complete Treatment Dialog */}
      <Dialog
        open={isCompleteOpen}
        onOpenChange={setIsCompleteOpen}
        title="Complete Clinical Treatment"
        description="Finalize this treatment session. Completed records are permanently locked."
      >
        <div className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-700 font-semibold mb-1">
              Final Session Notes / Completion Summary
            </label>
            <textarea
              rows={3}
              value={completeNotes}
              onChange={(e) => setCompleteNotes(e.target.value)}
              placeholder="e.g. Procedure successfully completed. Patient tolerated well. Next recall in 6 months."
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
            />
          </div>

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="completeAppointment"
              checked={completeAppointment}
              onChange={(e) => setCompleteAppointment(e.target.checked)}
              className="w-4 h-4 text-teal-600 border-slate-300 rounded focus:ring-teal-500"
            />
            <label htmlFor="completeAppointment" className="font-semibold text-slate-800 cursor-pointer">
              Also mark linked Appointment as COMPLETED
            </label>
          </div>

          <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsCompleteOpen(false)}
              className="px-3 py-2 text-slate-600 hover:bg-slate-100 rounded-md"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => completeMutation.mutate()}
              disabled={completeMutation.isPending}
              className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold rounded-md shadow-2xs disabled:opacity-50"
            >
              {completeMutation.isPending ? "Completing..." : "Confirm & Lock Record"}
            </button>
          </div>
        </div>
      </Dialog>

      {/* Cancel Treatment Dialog */}
      <Dialog
        open={isCancelOpen}
        onOpenChange={setIsCancelOpen}
        title="Cancel Treatment Record"
        description="Provide a clinical reason for cancelling this treatment session."
      >
        <div className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-700 font-semibold mb-1">
              Reason for Cancellation <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="e.g. Patient experienced severe vasovagal syncope; deferred to oral surgeon."
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
              required
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsCancelOpen(false)}
              className="px-3 py-2 text-slate-600 hover:bg-slate-100 rounded-md"
            >
              Keep Open
            </button>
            <button
              type="button"
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending || !cancelReason.trim()}
              className="px-4 py-2 bg-rose-700 hover:bg-rose-800 text-white font-semibold rounded-md shadow-2xs disabled:opacity-50"
            >
              {cancelMutation.isPending ? "Cancelling..." : "Confirm Cancellation"}
            </button>
          </div>
        </div>
      </Dialog>

      {/* Delete Treatment Dialog */}
      <Dialog
        open={isDeleteOpen}
        onOpenChange={setIsDeleteOpen}
        title="Delete Treatment Record"
        description="Are you sure you want to soft-delete this treatment? Only Clinic Administrators can perform this action."
      >
        <div className="space-y-4 text-xs">
          <div className="p-3 rounded-md bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-2">
            <AlertTriangle size={16} className="text-rose-600 shrink-0 mt-0.5" />
            <span>This action soft-deletes the clinical record and logs a security audit event.</span>
          </div>

          <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsDeleteOpen(false)}
              className="px-3 py-2 text-slate-600 hover:bg-slate-100 rounded-md"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
              className="px-4 py-2 bg-rose-700 hover:bg-rose-800 text-white font-semibold rounded-md shadow-2xs disabled:opacity-50"
            >
              {deleteMutation.isPending ? "Deleting..." : "Permanently Delete"}
            </button>
          </div>
        </div>
      </Dialog>
    </main>
  );
}

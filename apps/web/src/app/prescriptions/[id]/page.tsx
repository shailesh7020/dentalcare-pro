"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Copy,
  Download,
  ExternalLink,
  FileCheck,
  FileText,
  Pill,
  Printer,
  Shield,
  ShieldAlert,
  Stethoscope,
  Trash2,
  User,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  PrescriptionCancel,
  PrescriptionDetail,
  PrescriptionStatus,
} from "../types";

export default function PrescriptionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;
  const router = useRouter();
  const queryClient = useQueryClient();

  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [sendingWhatsApp, setSendingWhatsApp] = useState(false);
  const [whatsAppSuccess, setWhatsAppSuccess] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch Prescription
  const rxQuery = useQuery({
    queryKey: ["prescription-detail", id],
    queryFn: async () => {
      const res = await api.get<PrescriptionDetail>(`/prescriptions/${id}`);
      return res.data;
    },
  });

  const invalidateData = () => {
    void queryClient.invalidateQueries({
      queryKey: ["prescription-detail", id],
    });
    void queryClient.invalidateQueries({
      queryKey: ["prescriptions-list"],
    });
    void queryClient.invalidateQueries({
      queryKey: ["prescription-dashboard-stats"],
    });
  };

  // Issue Mutation
  const issueMutation = useMutation({
    mutationFn: async () => {
      setErrorMessage(null);
      const res = await api.post<PrescriptionDetail>(
        `/prescriptions/${id}/issue`
      );
      return res.data;
    },
    onSuccess: () => {
      invalidateData();
    },
    onError: (err: any) => {
      setErrorMessage(
        err.response?.data?.detail || err.message || "Failed to issue prescription."
      );
    },
  });

  // Cancel Mutation
  const cancelMutation = useMutation({
    mutationFn: async (payload: PrescriptionCancel) => {
      setErrorMessage(null);
      const res = await api.post<PrescriptionDetail>(
        `/prescriptions/${id}/cancel`,
        payload
      );
      return res.data;
    },
    onSuccess: () => {
      setIsCancelModalOpen(false);
      setCancelReason("");
      invalidateData();
    },
    onError: (err: any) => {
      setErrorMessage(
        err.response?.data?.detail || err.message || "Failed to cancel prescription."
      );
    },
  });

  // Duplicate Mutation
  const duplicateMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post<PrescriptionDetail>(
        `/prescriptions/${id}/duplicate`
      );
      return res.data;
    },
    onSuccess: (newRx) => {
      router.push(`/prescriptions/${newRx.id}`);
    },
    onError: (err: any) => {
      setErrorMessage(
        err.response?.data?.detail || err.message || "Failed to duplicate prescription."
      );
    },
  });

  // Delete Draft Mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      await api.delete(`/prescriptions/${id}`);
    },
    onSuccess: () => {
      router.push("/prescriptions");
    },
    onError: (err: any) => {
      setErrorMessage(
        err.response?.data?.detail || err.message || "Failed to delete draft prescription."
      );
    },
  });

  const handleDownloadPdf = async () => {
    if (!rxQuery.data) return;
    try {
      setDownloading(true);
      const res = await api.get(`/prescriptions/${id}/pdf`, {
        responseType: "blob",
      });
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const patientSlug = (rxQuery.data.patient_name || "Patient")
        .trim()
        .replace(/[^A-Za-z0-9]+/g, "_")
        .toUpperCase();
      link.setAttribute(
        "download",
        `${patientSlug}_Prescription_${rxQuery.data.prescription_number}.pdf`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download PDF", err);
      alert("Could not generate prescription PDF.");
    } finally {
      setDownloading(false);
    }
  };

  const handleSendWhatsApp = async () => {
    if (!rxQuery.data) return;
    try {
      setSendingWhatsApp(true);
      setErrorMessage(null);
      setWhatsAppSuccess(null);
      const res = await api.post(`/prescriptions/${id}/send-whatsapp`, {});
      const data = res.data;
      if (data?.success === false) {
        setErrorMessage(
          data.error ||
            "WhatsApp Gateway is not paired yet. Please link WhatsApp from Patient Report or Billing."
        );
      } else {
        setWhatsAppSuccess(
          `Direct PDF (${data?.filename || "Prescription.pdf"}) sent to patient's WhatsApp (${data?.recipient || ""})!`
        );
      }
    } catch (err: any) {
      setErrorMessage(
        err.response?.data?.detail ||
          err.message ||
          "Failed to send prescription PDF to WhatsApp."
      );
    } finally {
      setSendingWhatsApp(false);
    }
  };

  const rx = rxQuery.data;

  if (rxQuery.isLoading) {
    return (
      <main className="min-h-screen bg-slate-50/60 p-8 max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-44 w-full" />
        <Skeleton className="h-72 w-full" />
      </main>
    );
  }

  if (!rx) {
    return (
      <main className="min-h-screen bg-slate-50/60 flex items-center justify-center p-6 text-center">
        <div>
          <AlertCircle size={40} className="text-slate-400 mx-auto mb-2" />
          <h2 className="text-base font-bold text-slate-800">
            Prescription Not Found
          </h2>
          <p className="text-xs text-slate-500 mt-1 mb-4">
            The requested prescription record does not exist or has been deleted.
          </p>
          <Link
            href="/prescriptions"
            className="px-3.5 py-2 text-xs font-semibold bg-teal-700 text-white rounded-md"
          >
            Back to Prescriptions
          </Link>
        </div>
      </main>
    );
  }

  const isIssued = rx.status === "ISSUED";
  const isDraft = rx.status === "DRAFT";
  const isCancelled = rx.status === "CANCELLED";

  const getStatusBadge = (status: PrescriptionStatus) => {
    switch (status) {
      case "ISSUED":
        return <Badge variant="success">Issued & Signed</Badge>;
      case "DRAFT":
        return <Badge variant="warning">Draft (Unsigned)</Badge>;
      case "CANCELLED":
        return <Badge variant="destructive">Cancelled</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <main className="min-h-screen bg-slate-50/60 pb-24 print:bg-white print:pb-0">
      {/* Top Action Bar (Hidden on print) */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs print:hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Link
              href="/prescriptions"
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
              title="Back to Prescriptions"
            >
              <ArrowLeft size={18} />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-teal-800 text-lg">
                  {rx.prescription_number}
                </span>
                {getStatusBadge(rx.status)}
              </div>
              <p className="text-xs text-slate-500">
                Created on {new Date(rx.created_at).toLocaleString("en-IN")}
                {rx.issued_at &&
                  ` · Issued at ${new Date(rx.issued_at).toLocaleString("en-IN")}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap justify-end w-full sm:w-auto">
            {isDraft && (
              <>
                <button
                  onClick={() => issueMutation.mutate()}
                  disabled={issueMutation.isPending}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold rounded-md shadow-2xs disabled:opacity-50 transition-colors"
                >
                  <CheckCircle2 size={13} /> Issue & Sign
                </button>
                <button
                  onClick={() => deleteMutation.mutate()}
                  disabled={deleteMutation.isPending}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold rounded-md border border-rose-200 transition-colors"
                >
                  <Trash2 size={13} /> Delete Draft
                </button>
              </>
            )}

            {isIssued && (
              <button
                onClick={() => setIsCancelModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold rounded-md border border-rose-200 transition-colors"
              >
                <XCircle size={13} /> Cancel Prescription
              </button>
            )}

            <button
              onClick={() => duplicateMutation.mutate()}
              disabled={duplicateMutation.isPending}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-md border border-slate-300 shadow-2xs transition-colors"
              title="Duplicate as New Draft"
            >
              <Copy size={13} /> Duplicate
            </button>

            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-md border border-slate-300 shadow-2xs transition-colors"
              title="Print"
            >
              <Printer size={13} /> Print
            </button>

            <button
              onClick={handleDownloadPdf}
              disabled={downloading}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold rounded-md shadow-2xs disabled:opacity-50 transition-colors"
            >
              <Download size={13} />{" "}
              {downloading ? "Generating..." : "Download Official PDF"}
            </button>

            <button
              onClick={handleSendWhatsApp}
              disabled={sendingWhatsApp}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-md shadow-2xs disabled:opacity-50 transition-colors"
              title="Send Prescription PDF directly to patient's WhatsApp"
            >
              <CheckCircle2 size={13} />{" "}
              {sendingWhatsApp ? "Sending to WhatsApp..." : "Send PDF on WhatsApp"}
            </button>
          </div>
        </div>
      </div>

      {/* Main Printable Document Sheet */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 pt-6 space-y-6 print:p-0 print:m-0 print:max-w-none">
        {whatsAppSuccess && (
          <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-md flex items-center gap-2 text-xs text-emerald-800 print:hidden">
            <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
            <span className="font-semibold">{whatsAppSuccess}</span>
          </div>
        )}

        {/* Error Notification */}
        {errorMessage && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-3 text-rose-800 text-xs print:hidden">
            <AlertCircle size={17} className="text-rose-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">Action Failed</p>
              <p className="mt-0.5">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Cancellation Notice Banner */}
        {isCancelled && (
          <div className="p-4 bg-rose-50 border-2 border-rose-300 rounded-lg flex items-start gap-3 text-rose-900 text-xs">
            <ShieldAlert size={20} className="text-rose-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-sm">PRESCRIPTION CANCELLED</p>
              <p className="mt-0.5 font-medium">
                Reason: {rx.cancellation_reason || "Discontinued by clinician."}
              </p>
              <p className="text-[11px] text-rose-700 mt-1">
                This prescription is null and void. Do not dispense medications under this record.
              </p>
            </div>
          </div>
        )}

        {/* Printable Paper Card */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-8 print:shadow-none print:border-none print:p-6 space-y-6">
          {/* Clinic Header */}
          <div className="border-b-2 border-teal-700 pb-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-black tracking-tight text-teal-900">
                {rx.clinic_name || "DENTALCARE PRO CLINIC"}
              </h1>
              <p className="text-xs text-slate-600 font-medium mt-0.5">
                Multi-Speciality Dental Care & Oral Implantology Centre
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Phone: {rx.clinic_phone || "+91 98765 43210"} · Email:{" "}
                {rx.clinic_email || "contact@dentalcarepro.in"}
              </p>
            </div>

            <div className="text-right sm:border-l sm:border-slate-200 sm:pl-4">
              <span className="text-xs font-bold text-teal-800 uppercase tracking-wider block">
                Prescription
              </span>
              <span className="font-mono font-bold text-slate-900 text-sm">
                {rx.prescription_number}
              </span>
              <p className="text-xs text-slate-500 mt-0.5">
                Date:{" "}
                {new Date(rx.date).toLocaleDateString("en-IN", {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                })}
              </p>
            </div>
          </div>

          {/* Patient & Doctor Two-Column Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50/70 p-4 rounded-md border border-slate-200/80 text-xs">
            {/* Patient Details */}
            <div className="space-y-1">
              <div className="flex items-center gap-1 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
                <User size={12} /> Patient Information
              </div>
              <p className="font-bold text-slate-900 text-sm">
                <Link
                  href={`/patients/${rx.patient_id}`}
                  className="hover:underline hover:text-teal-700"
                >
                  {rx.patient_name || "N/A"}
                </Link>
              </p>
              <p className="text-slate-600">
                ID: <span className="font-mono font-semibold">{rx.patient_number}</span> ·{" "}
                {rx.patient_gender || "Unknown"},{" "}
                {rx.patient_age !== null ? `${rx.patient_age} yrs` : ""}
              </p>
            </div>

            {/* Prescribing Doctor Details */}
            <div className="space-y-1 sm:border-l sm:border-slate-200 sm:pl-4">
              <div className="flex items-center gap-1 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
                <Stethoscope size={12} /> Prescribing Clinician
              </div>
              <p className="font-bold text-slate-900 text-sm">
                {rx.dentist_name || "Registered Dental Surgeon"}
              </p>
              <p className="text-slate-600 font-mono">
                Reg No: {rx.dentist_registration || "DCI-REG-VERIFIED"}
              </p>
              {rx.treatment_number && (
                <p className="text-[11px] text-teal-700 font-medium">
                  Linked Treatment:{" "}
                  <Link
                    href={`/treatments/${rx.treatment_id}`}
                    className="hover:underline font-mono"
                  >
                    {rx.treatment_number}
                  </Link>
                </p>
              )}
            </div>
          </div>

          {/* Critical Patient Allergies Banner */}
          {rx.patient_alerts && rx.patient_alerts.length > 0 && (
            <div className="p-3 bg-rose-50 border border-rose-300 rounded-md flex items-center gap-2 text-xs text-rose-900">
              <AlertTriangle size={16} className="text-rose-600 shrink-0" />
              <div>
                <span className="font-bold uppercase mr-2">Medical Alerts:</span>
                <span className="font-semibold">{rx.patient_alerts.join("  |  ")}</span>
              </div>
            </div>
          )}

          {/* Clinical Diagnosis */}
          <div className="space-y-1">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Clinical Diagnosis
            </h3>
            <p className="text-sm font-semibold text-slate-900 bg-slate-50 p-2.5 rounded border border-slate-200">
              {rx.diagnosis}
            </p>
          </div>

          {/* Structured Medication Table */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="text-xl font-bold font-serif text-teal-900">℞</span>
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Medication Orders ({rx.items_count})
                </h3>
              </div>
            </div>

            <div className="border border-slate-200 rounded-md overflow-hidden">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-100/80 border-b border-slate-200 text-[11px] font-bold text-slate-700 uppercase">
                    <th className="py-2.5 px-3">#</th>
                    <th className="py-2.5 px-3">Medicine & Generic</th>
                    <th className="py-2.5 px-3">Form</th>
                    <th className="py-2.5 px-3">Dosage</th>
                    <th className="py-2.5 px-3">Frequency</th>
                    <th className="py-2.5 px-3">Duration</th>
                    <th className="py-2.5 px-3">Qty</th>
                    <th className="py-2.5 px-3">Instructions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {rx.items?.map((item, idx) => (
                    <tr key={item.id || idx} className="hover:bg-slate-50/50">
                      <td className="py-2.5 px-3 text-slate-400 font-mono">
                        {idx + 1}
                      </td>
                      <td className="py-2.5 px-3">
                        <p className="font-bold text-slate-900">
                          {item.medicine_name}{" "}
                          {item.strength && (
                            <span className="font-normal text-slate-600">
                              ({item.strength})
                            </span>
                          )}
                        </p>
                        {item.generic_name && (
                          <p className="text-[11px] text-slate-500 italic">
                            {item.generic_name}
                          </p>
                        )}
                        {item.notes && (
                          <p className="text-[10px] text-teal-700 mt-0.5">
                            Note: {item.notes}
                          </p>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-700 font-medium">
                        {item.form}
                      </td>
                      <td className="py-2.5 px-3 text-slate-800 font-semibold">
                        {item.dosage}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="px-1.5 py-0.5 bg-slate-100 text-slate-800 rounded font-semibold text-[11px]">
                          {item.frequency}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-700">
                        {item.duration}
                      </td>
                      <td className="py-2.5 px-3 font-bold text-slate-900 font-mono">
                        {item.quantity}
                      </td>
                      <td className="py-2.5 px-3 text-slate-600">
                        {item.food_instructions || "After food"}
                        {item.timing && (
                          <span className="block text-[10px] text-slate-400">
                            {item.timing}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Patient Directions & Precautions */}
          {rx.instructions && (
            <div className="space-y-1 bg-teal-50/40 p-4 rounded-md border border-teal-100">
              <h3 className="text-xs font-bold text-teal-900 uppercase tracking-wider">
                Patient Instructions & Precautions
              </h3>
              <p className="text-xs text-slate-700 whitespace-pre-line leading-relaxed mt-1">
                {rx.instructions}
              </p>
            </div>
          )}

          {/* Follow-up Review Date */}
          {rx.follow_up_date && (
            <div className="flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-md text-xs text-blue-900">
              <Calendar size={16} className="text-blue-600" />
              <span>
                <strong>Scheduled Follow-up Review:</strong>{" "}
                {new Date(rx.follow_up_date).toLocaleDateString("en-IN", {
                  weekday: "long",
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                })}
              </span>
            </div>
          )}

          {/* Doctor Signature & Stamp Footer */}
          <div className="pt-8 border-t border-slate-200 flex flex-col sm:flex-row items-end justify-between gap-6">
            <div className="text-[11px] text-slate-400 space-y-0.5">
              <p>Generated by DentalCare Pro Clinical Management System</p>
              <p>Official Document ID: {rx.id}</p>
            </div>

            <div className="text-right space-y-1 min-w-[200px]">
              <div className="h-10 flex items-end justify-end">
                <span className="font-serif italic text-teal-800 text-sm">
                  {rx.dentist_name || "Doctor's Signature"}
                </span>
              </div>
              <div className="w-full border-t border-slate-400 pt-1">
                <p className="text-xs font-bold text-slate-900">
                  {rx.dentist_name || "Prescribing Clinician"}
                </p>
                <p className="text-[11px] text-slate-500 font-mono">
                  {rx.dentist_registration || "DCI-REG-VERIFIED"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Cancel Prescription Modal */}
      <Dialog
        open={isCancelModalOpen}
        onOpenChange={setIsCancelModalOpen}
        title="Cancel Clinical Prescription"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-600">
            Cancelling an issued prescription will permanently mark it as cancelled in the clinical audit log. Please state the clinical rationale.
          </p>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">
              Cancellation Reason: <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="e.g. Patient allergic reaction / Adverse gastrointestinal intolerance / Switched to Augmentin"
              className="w-full px-3 py-2 text-xs border border-slate-200 rounded-md focus:ring-1 focus:ring-rose-500"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              onClick={() => setIsCancelModalOpen(false)}
              className="px-3.5 py-1.5 bg-white border border-slate-300 text-slate-700 text-xs font-semibold rounded-md"
            >
              Back
            </button>
            <button
              onClick={() =>
                cancelMutation.mutate({ reason: cancelReason.trim() })
              }
              disabled={cancelMutation.isPending || !cancelReason.trim()}
              className="px-4 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-md disabled:opacity-50"
            >
              Confirm Cancellation
            </button>
          </div>
        </div>
      </Dialog>
    </main>
  );
}

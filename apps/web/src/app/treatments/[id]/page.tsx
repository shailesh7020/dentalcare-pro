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
  Plus,
  Printer,
  RotateCcw,
  Sparkles,
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

interface RxPreset {
  medicine_name: string;
  strength: string;
  form: string;
  dosage: string;
  frequency: string;
  duration: string;
  food_instructions: string;
  quantity: number;
}

const DENTAL_RX_PRESETS: RxPreset[] = [
  {
    medicine_name: "Amoxicillin",
    strength: "500 mg",
    form: "CAPSULE",
    dosage: "1 capsule",
    frequency: "TDS",
    duration: "5 days",
    food_instructions: "After food",
    quantity: 15,
  },
  {
    medicine_name: "Augmentin 625",
    strength: "625 mg",
    form: "TABLET",
    dosage: "1 tablet",
    frequency: "BD",
    duration: "5 days",
    food_instructions: "After food",
    quantity: 10,
  },
  {
    medicine_name: "Paracetamol",
    strength: "650 mg",
    form: "TABLET",
    dosage: "1 tablet",
    frequency: "SOS",
    duration: "3 days",
    food_instructions: "After food (when pain arises)",
    quantity: 10,
  },
  {
    medicine_name: "Ibuprofen",
    strength: "400 mg",
    form: "TABLET",
    dosage: "1 tablet",
    frequency: "BD",
    duration: "3 days",
    food_instructions: "After food",
    quantity: 6,
  },
  {
    medicine_name: "Ketorol-DT",
    strength: "10 mg",
    form: "TABLET",
    dosage: "1 tablet",
    frequency: "SOS",
    duration: "2 days",
    food_instructions: "Dissolve in water, after food (for severe pain)",
    quantity: 4,
  },
  {
    medicine_name: "Metronidazole",
    strength: "400 mg",
    form: "TABLET",
    dosage: "1 tablet",
    frequency: "TDS",
    duration: "5 days",
    food_instructions: "After food",
    quantity: 15,
  },
  {
    medicine_name: "Chlorhexidine 0.2% Rinse",
    strength: "0.2% w/v",
    form: "MOUTHWASH",
    dosage: "10 ml",
    frequency: "BD",
    duration: "7 days",
    food_instructions: "Rinse for 30s after brushing; do not swallow",
    quantity: 1,
  },
  {
    medicine_name: "Pantoprazole",
    strength: "40 mg",
    form: "TABLET",
    dosage: "1 tablet",
    frequency: "OD",
    duration: "5 days",
    food_instructions: "Morning before food",
    quantity: 5,
  },
];

const DENTAL_PROCEDURE_PRESETS = [
  { name: "Scaling & Polishing (Dental Cleaning)", cost: 500, duration: 30 },
  { name: "Composite Restoration (Light-Cure Filling)", cost: 1200, duration: 30 },
  { name: "Root Canal Treatment (RCT - Anterior)", cost: 3500, duration: 45 },
  { name: "Root Canal Treatment (RCT - Molar)", cost: 5000, duration: 60 },
  { name: "Simple Tooth Extraction", cost: 800, duration: 20 },
  { name: "Surgical Extraction / Impaction", cost: 3000, duration: 45 },
  { name: "Ceramic / Zirconia Crown", cost: 6000, duration: 45 },
  { name: "Intraoral Periapical X-Ray (IOPA)", cost: 250, duration: 15 },
  { name: "Deep Periodontal Curettage", cost: 1500, duration: 40 },
  { name: "Dental Bleaching / Whitening", cost: 5000, duration: 60 },
];

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

  // Quick Prescribe State
  const [isPrescribeOpen, setIsPrescribeOpen] = useState(false);
  const [prescribeItems, setPrescribeItems] = useState<RxPreset[]>([]);
  const [prescribeDiagnosis, setPrescribeDiagnosis] = useState("");
  const [prescribeInstructions, setPrescribeInstructions] = useState("");
  const [customRxMed, setCustomRxMed] = useState("");
  const [customRxStrength, setCustomRxStrength] = useState("");
  const [customRxDosage, setCustomRxDosage] = useState("1 tablet");
  const [customRxFreq, setCustomRxFreq] = useState("BD");
  const [customRxDuration, setCustomRxDuration] = useState("5 days");
  const [customRxInstructions, setCustomRxInstructions] = useState("After food");

  // Quick Edit Notes & Findings State
  const [isEditNotesOpen, setIsEditNotesOpen] = useState(false);
  const [editDiagnosis, setEditDiagnosis] = useState("");
  const [editChiefComplaint, setEditChiefComplaint] = useState("");
  const [editClinicalFindings, setEditClinicalFindings] = useState("");
  const [editTreatmentPlan, setEditTreatmentPlan] = useState("");
  const [editSoapSubjective, setEditSoapSubjective] = useState("");
  const [editSoapObjective, setEditSoapObjective] = useState("");
  const [editSoapAssessment, setEditSoapAssessment] = useState("");
  const [editSoapPlan, setEditSoapPlan] = useState("");
  const [editLocalAnaesthesia, setEditLocalAnaesthesia] = useState("");
  const [editMedicinesUsed, setEditMedicinesUsed] = useState("");
  const [editClinicalNotes, setEditClinicalNotes] = useState("");
  const [editFollowUpInstructions, setEditFollowUpInstructions] = useState("");

  // Quick Add Procedure State
  const [isAddProcedureOpen, setIsAddProcedureOpen] = useState(false);
  const [newProcName, setNewProcName] = useState("");
  const [newProcTooth, setNewProcTooth] = useState("");
  const [newProcCost, setNewProcCost] = useState(500);
  const [newProcDuration, setNewProcDuration] = useState(30);
  const [newProcNotes, setNewProcNotes] = useState("");

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

  const handleOpenEditNotes = () => {
    const t = treatmentQuery.data;
    if (!t) return;
    setEditDiagnosis(t.diagnosis || "");
    setEditChiefComplaint(t.chief_complaint || "");
    setEditClinicalFindings(t.clinical_findings || "");
    setEditTreatmentPlan(t.treatment_plan || "");
    setEditSoapSubjective(t.soap_subjective || "");
    setEditSoapObjective(t.soap_objective || "");
    setEditSoapAssessment(t.soap_assessment || "");
    setEditSoapPlan(t.soap_plan || "");
    setEditLocalAnaesthesia(t.local_anaesthesia_used || "");
    setEditMedicinesUsed(t.medicines_used || "");
    setEditClinicalNotes(t.clinical_notes || "");
    setEditFollowUpInstructions(t.follow_up_instructions || "");
    setIsEditNotesOpen(true);
  };

  // Complete Treatment Mutation
  const completeMutation = useMutation({
    mutationFn: async (vars?: { redirectToReport?: boolean }) => {
      setActionError(null);
      const res = await api.post(`/treatments/${id}/complete`, {
        notes: completeNotes.trim() || undefined,
        complete_appointment: completeAppointment,
      });
      return { data: res.data, redirectToReport: vars?.redirectToReport };
    },
    onSuccess: (result) => {
      setIsCompleteOpen(false);
      invalidateData();
      if (result.redirectToReport && treatmentQuery.data) {
        router.push(`/patients/${treatmentQuery.data.patient_id}/report?autoPrint=true`);
      }
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || "Failed to complete treatment.");
    },
  });

  // Quick Prescribe Mutation
  const prescribeMutation = useMutation({
    mutationFn: async () => {
      setActionError(null);
      const t = treatmentQuery.data;
      if (!t) throw new Error("Treatment record not loaded");
      if (prescribeItems.length === 0) throw new Error("Please add at least one medication to prescribe.");

      const res = await api.post("/prescriptions", {
        patient_id: t.patient_id,
        treatment_id: t.id,
        appointment_id: t.appointment_id || undefined,
        dentist_id: t.dentist_id || undefined,
        diagnosis: prescribeDiagnosis.trim() || t.diagnosis || "Dental Clinical Encounter",
        instructions: prescribeInstructions.trim() || undefined,
        issue_immediately: true,
        items: prescribeItems.map((it) => ({
          medicine_name: it.medicine_name.trim(),
          strength: it.strength.trim(),
          form: it.form || "TABLET",
          dosage: it.dosage.trim() || "1 tablet",
          frequency: it.frequency || "BD",
          duration: it.duration.trim() || "5 days",
          quantity: Number(it.quantity) || 10,
          food_instructions: it.food_instructions || undefined,
        })),
      });
      return res.data;
    },
    onSuccess: () => {
      setIsPrescribeOpen(false);
      setPrescribeItems([]);
      setPrescribeInstructions("");
      void queryClient.invalidateQueries({ queryKey: ["treatment-prescriptions", id] });
      void queryClient.invalidateQueries({
        queryKey: ["patient-prescriptions", treatmentQuery.data?.patient_id],
      });
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || "Failed to issue prescription.");
    },
  });

  // Edit Findings & Notes Mutation
  const editNotesMutation = useMutation({
    mutationFn: async () => {
      setActionError(null);
      const res = await api.patch(`/treatments/${id}`, {
        diagnosis: editDiagnosis.trim() || treatmentQuery.data?.diagnosis,
        chief_complaint: editChiefComplaint.trim() || undefined,
        clinical_findings: editClinicalFindings.trim() || undefined,
        treatment_plan: editTreatmentPlan.trim() || undefined,
        soap: {
          subjective: editSoapSubjective.trim() || undefined,
          objective: editSoapObjective.trim() || undefined,
          assessment: editSoapAssessment.trim() || undefined,
          plan: editSoapPlan.trim() || undefined,
        },
        local_anaesthesia_used: editLocalAnaesthesia.trim() || undefined,
        medicines_used: editMedicinesUsed.trim() || undefined,
        clinical_notes: editClinicalNotes.trim() || undefined,
        follow_up_instructions: editFollowUpInstructions.trim() || undefined,
      });
      return res.data;
    },
    onSuccess: () => {
      setIsEditNotesOpen(false);
      invalidateData();
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || "Failed to update clinical findings.");
    },
  });

  // Add Procedure Mutation
  const addProcedureMutation = useMutation({
    mutationFn: async () => {
      setActionError(null);
      const t = treatmentQuery.data;
      if (!t) throw new Error("Treatment not loaded");
      if (!newProcName.trim()) throw new Error("Procedure name is required");

      const existingProcs = (t.procedures || []).map((p) => ({
        procedure_name: p.procedure_name,
        tooth_number: p.tooth_number || undefined,
        quantity: p.quantity || 1,
        cost: Number(p.cost) || 0,
        duration: p.duration || 30,
        notes: p.notes || undefined,
        status: p.status || "COMPLETED",
      }));

      const newProc = {
        procedure_name: newProcName.trim(),
        tooth_number: newProcTooth.trim() || undefined,
        quantity: 1,
        cost: Number(newProcCost) || 0,
        duration: Number(newProcDuration) || 30,
        notes: newProcNotes.trim() || undefined,
        status: "COMPLETED",
      };

      const res = await api.patch(`/treatments/${id}`, {
        procedures: [...existingProcs, newProc],
      });
      return res.data;
    },
    onSuccess: () => {
      setIsAddProcedureOpen(false);
      setNewProcName("");
      setNewProcTooth("");
      setNewProcCost(500);
      setNewProcDuration(30);
      setNewProcNotes("");
      invalidateData();
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || "Failed to add procedure.");
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
          <div className="flex items-center gap-2 w-full sm:w-auto justify-end flex-wrap">
            <Link
              href={`/patients/${treatment.patient_id}/report`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs rounded-md shadow-2xs transition-colors"
              title="Open the single-page clinical report for viewing, 1-click printing, or sharing"
            >
              <FileText size={14} /> View / Print Patient Report
            </Link>

            <Link
              href={`/billing/new?patient_id=${treatment.patient_id}&treatment_id=${treatment.id}&appointment_id=${treatment.appointment_id || ""}`}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-md shadow-2xs transition-colors"
            >
              <IndianRupee size={13} /> Generate Invoice
            </Link>

            {!isCompleted && !isCancelled && (
              <>
                <button
                  type="button"
                  onClick={() => {
                    setPrescribeDiagnosis(treatment.diagnosis || "");
                    setIsPrescribeOpen(true);
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-2 bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 font-semibold text-xs rounded-md shadow-2xs transition-colors cursor-pointer"
                >
                  <Pill size={13} /> Quick Prescribe
                </button>

                <button
                  type="button"
                  onClick={handleOpenEditNotes}
                  className="inline-flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-md shadow-2xs transition-colors cursor-pointer"
                >
                  <Edit2 size={13} /> Quick Edit Notes
                </button>

                <button
                  type="button"
                  onClick={() => setIsCancelOpen(true)}
                  className="inline-flex items-center gap-1.5 px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-semibold text-xs rounded-md transition-colors cursor-pointer"
                >
                  <XCircle size={13} /> Cancel
                </button>

                <button
                  type="button"
                  onClick={() => setIsCompleteOpen(true)}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs rounded-md shadow-2xs transition-colors cursor-pointer"
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
          <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-emerald-900">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 size={18} className="text-emerald-600 shrink-0" />
              <span>
                <b>Treatment Completed & Locked:</b> This clinical record is finalized. All findings,
                procedures, and prescriptions are compiled in the patient's comprehensive report.
              </span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Link
                href={`/patients/${treatment.patient_id}/report`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-700 hover:bg-teal-800 text-white rounded font-bold text-xs shadow-2xs transition-colors"
              >
                <FileText size={13} /> View Patient Report
              </Link>
              <Link
                href={`/patients/${treatment.patient_id}/report?autoPrint=true`}
                className="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-white border border-emerald-300 text-emerald-800 rounded font-semibold text-xs hover:bg-emerald-100 transition-colors"
              >
                <Printer size={13} /> Print Report
              </Link>
            </div>
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
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Stethoscope size={16} className="text-teal-700" /> Clinical Diagnosis & Findings
            </h2>
            {!isCompleted && !isCancelled && (
              <button
                type="button"
                onClick={handleOpenEditNotes}
                className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800 bg-teal-50 hover:bg-teal-100 px-2.5 py-1 rounded transition-colors cursor-pointer"
              >
                <Edit2 size={12} /> Edit Findings & Notes
              </button>
            )}
          </div>

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
          <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900">
                  Dental Procedures ({treatment.procedures.length})
                </h2>
                {!isCompleted && !isCancelled && (
                  <button
                    type="button"
                    onClick={() => setIsAddProcedureOpen(true)}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800 bg-teal-50 hover:bg-teal-100 px-2.5 py-1 rounded transition-colors cursor-pointer"
                  >
                    <Plus size={12} /> Add Procedure
                  </button>
                )}
              </div>
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
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-2 border-b border-slate-100 gap-2">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Pill size={16} className="text-teal-700" /> Prescriptions & Medication Orders ({treatmentPrescriptionsQuery.data?.length ?? 0})
              </h2>
              <p className="text-[11px] text-slate-500">
                Prescribed medications for this treatment encounter.
              </p>
            </div>
            {!isCompleted && !isCancelled && (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setPrescribeDiagnosis(treatment.diagnosis || "");
                    setIsPrescribeOpen(true);
                  }}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-teal-800 bg-teal-100 hover:bg-teal-200 px-3 py-1.5 rounded-md transition-colors cursor-pointer"
                >
                  <Sparkles size={13} className="text-teal-700" /> + Quick Prescribe
                </button>
                <Link
                  href={`/prescriptions/new?patient_id=${treatment.patient_id}&treatment_id=${treatment.id}&appointment_id=${treatment.appointment_id}`}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 px-2.5 py-1.5 rounded-md transition-colors"
                >
                  Full Form &rarr;
                </Link>
              </div>
            )}
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

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-end gap-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsCompleteOpen(false)}
              className="px-3 py-2 text-slate-600 hover:bg-slate-100 rounded-md text-center cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => completeMutation.mutate({ redirectToReport: false })}
              disabled={completeMutation.isPending}
              className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-md disabled:opacity-50 text-center cursor-pointer"
            >
              Complete Only
            </button>
            <button
              type="button"
              onClick={() => completeMutation.mutate({ redirectToReport: true })}
              disabled={completeMutation.isPending}
              className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white font-bold rounded-md shadow-2xs disabled:opacity-50 inline-flex items-center justify-center gap-1.5 text-center cursor-pointer"
            >
              <FileCheck size={14} />
              {completeMutation.isPending ? "Completing..." : "Complete & Open Patient Report"}
            </button>
          </div>
        </div>
      </Dialog>

      {/* Quick Prescribe Dialog */}
      <Dialog
        open={isPrescribeOpen}
        onOpenChange={setIsPrescribeOpen}
        title="Quick Prescribe Medications"
        description="Select common dental medication presets with 1 click or add custom prescriptions directly to this treatment encounter."
      >
        <div className="space-y-4 text-xs max-h-[75vh] overflow-y-auto pr-1">
          {/* Quick Dental Presets */}
          <div>
            <label className="block text-slate-700 font-bold mb-1.5 flex items-center gap-1.5">
              <Sparkles size={13} className="text-teal-600" />
              1-Click Dental Medication Presets
            </label>
            <div className="flex flex-wrap gap-1.5">
              {DENTAL_RX_PRESETS.map((preset) => {
                const isSelected = prescribeItems.some(
                  (it) => it.medicine_name === preset.medicine_name
                );
                return (
                  <button
                    key={preset.medicine_name}
                    type="button"
                    onClick={() => {
                      if (isSelected) {
                        setPrescribeItems((prev) =>
                          prev.filter((it) => it.medicine_name !== preset.medicine_name)
                        );
                      } else {
                        setPrescribeItems((prev) => [...prev, preset]);
                      }
                    }}
                    className={`px-2.5 py-1.5 rounded-md font-medium text-[11px] border transition-colors flex items-center gap-1.5 cursor-pointer ${
                      isSelected
                        ? "bg-teal-700 text-white border-teal-800 shadow-2xs"
                        : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-teal-50 hover:border-teal-300"
                    }`}
                  >
                    <span>💊</span>
                    <span className="font-semibold">{preset.medicine_name}</span>
                    <span className={isSelected ? "text-teal-100" : "text-slate-400"}>
                      ({preset.strength})
                    </span>
                    {isSelected && <CheckCircle2 size={12} className="text-white ml-0.5" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Prescribed Items Table */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-slate-700 font-bold">
                Selected Prescriptions ({prescribeItems.length})
              </label>
              {prescribeItems.length > 0 && (
                <button
                  type="button"
                  onClick={() => setPrescribeItems([])}
                  className="text-[11px] text-rose-600 hover:underline cursor-pointer"
                >
                  Clear all
                </button>
              )}
            </div>

            {prescribeItems.length > 0 ? (
              <div className="border border-slate-200 rounded-md overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-semibold text-[11px] border-b">
                    <tr>
                      <th className="py-2 px-3">Medicine</th>
                      <th className="py-2 px-2">Dose / Freq</th>
                      <th className="py-2 px-2">Duration</th>
                      <th className="py-2 px-2">Instructions</th>
                      <th className="py-2 px-2 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {prescribeItems.map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50">
                        <td className="py-2 px-3 font-semibold text-slate-800">
                          {item.medicine_name}
                          <span className="text-[10px] text-slate-400 block font-normal">
                            {item.strength} · {item.form}
                          </span>
                        </td>
                        <td className="py-2 px-2">
                          <span className="font-semibold text-teal-800">{item.frequency}</span>
                          <span className="text-[10px] text-slate-400 block">{item.dosage}</span>
                        </td>
                        <td className="py-2 px-2 font-mono text-slate-600">{item.duration}</td>
                        <td className="py-2 px-2 text-slate-600 text-[11px]">
                          {item.food_instructions || "After food"}
                        </td>
                        <td className="py-2 px-2 text-right">
                          <button
                            type="button"
                            onClick={() =>
                              setPrescribeItems((prev) => prev.filter((_, i) => i !== idx))
                            }
                            className="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors cursor-pointer"
                            title="Remove item"
                          >
                            <Trash2 size={13} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-4 border border-dashed border-slate-300 rounded-md text-center text-slate-400">
                Click any preset button above or add custom medicine below.
              </div>
            )}
          </div>

          {/* Add Custom Medicine Row */}
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
            <span className="font-bold text-slate-700 block text-[11px]">
              + Add Custom Medication
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="col-span-2">
                <input
                  type="text"
                  placeholder="Medicine Name (e.g. Ofloxacin-Ornidazole)"
                  value={customRxMed}
                  onChange={(e) => setCustomRxMed(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <input
                  type="text"
                  placeholder="Strength (e.g. 200mg/500mg)"
                  value={customRxStrength}
                  onChange={(e) => setCustomRxStrength(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <select
                  value={customRxFreq}
                  onChange={(e) => setCustomRxFreq(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-teal-600"
                >
                  <option value="BD">BD (Twice daily)</option>
                  <option value="TDS">TDS (Thrice daily)</option>
                  <option value="OD">OD (Once daily)</option>
                  <option value="SOS">SOS (As needed)</option>
                  <option value="QID">QID (Four times daily)</option>
                </select>
              </div>
              <div>
                <input
                  type="text"
                  placeholder="Duration (e.g. 5 days)"
                  value={customRxDuration}
                  onChange={(e) => setCustomRxDuration(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div className="col-span-2">
                <input
                  type="text"
                  placeholder="Instructions (e.g. After food with full glass of water)"
                  value={customRxInstructions}
                  onChange={(e) => setCustomRxInstructions(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div className="flex items-center">
                <button
                  type="button"
                  onClick={() => {
                    if (!customRxMed.trim()) return;
                    setPrescribeItems((prev) => [
                      ...prev,
                      {
                        medicine_name: customRxMed.trim(),
                        strength: customRxStrength.trim() || "Standard",
                        form: "TABLET",
                        dosage: customRxDosage.trim() || "1 tablet",
                        frequency: customRxFreq,
                        duration: customRxDuration.trim() || "5 days",
                        food_instructions: customRxInstructions.trim() || "After food",
                        quantity: 10,
                      },
                    ]);
                    setCustomRxMed("");
                    setCustomRxStrength("");
                  }}
                  disabled={!customRxMed.trim()}
                  className="w-full py-1.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold rounded text-xs disabled:opacity-50 cursor-pointer"
                >
                  + Add to List
                </button>
              </div>
            </div>
          </div>

          {/* Rx Instructions */}
          <div>
            <label className="block text-slate-700 font-semibold mb-1">
              General Prescription Advice / Notes (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Complete antibiotic course. Avoid skipping doses. Drink plenty of water."
              value={prescribeInstructions}
              onChange={(e) => setPrescribeInstructions(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsPrescribeOpen(false)}
              className="px-3 py-2 text-slate-600 hover:bg-slate-100 rounded-md cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => prescribeMutation.mutate()}
              disabled={prescribeMutation.isPending || prescribeItems.length === 0}
              className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white font-bold rounded-md shadow-2xs disabled:opacity-50 inline-flex items-center gap-1.5 cursor-pointer"
            >
              <Pill size={13} />
              {prescribeMutation.isPending ? "Issuing..." : "Save & Issue Prescription"}
            </button>
          </div>
        </div>
      </Dialog>

      {/* Quick Edit Clinical Findings & Notes Dialog */}
      <Dialog
        open={isEditNotesOpen}
        onOpenChange={setIsEditNotesOpen}
        title="Quick Edit Clinical Findings & Notes"
        description="Update diagnosis, clinical findings, longitudinal SOAP notes, and pharmacology notes without leaving this screen."
      >
        <div className="space-y-4 text-xs max-h-[75vh] overflow-y-auto pr-1">
          <div>
            <label className="block text-slate-700 font-bold mb-1">
              Primary Diagnosis <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={editDiagnosis}
              onChange={(e) => setEditDiagnosis(e.target.value)}
              placeholder="e.g. Dental caries on #12, Chronic generalized periodontitis"
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-teal-600 font-semibold"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 font-medium mb-1">Chief Complaint</label>
              <textarea
                rows={2}
                value={editChiefComplaint}
                onChange={(e) => setEditChiefComplaint(e.target.value)}
                placeholder="e.g. Pain in upper right front tooth since 3 days"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
              />
            </div>
            <div>
              <label className="block text-slate-700 font-medium mb-1">Clinical Findings</label>
              <textarea
                rows={2}
                value={editClinicalFindings}
                onChange={(e) => setEditClinicalFindings(e.target.value)}
                placeholder="e.g. Deep disto-occlusal cavitated lesion on #12, tender on percussion"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-700 font-medium mb-1">Staged Treatment Plan</label>
            <input
              type="text"
              value={editTreatmentPlan}
              onChange={(e) => setEditTreatmentPlan(e.target.value)}
              placeholder="e.g. Phase 1: Oral prophylaxis; Phase 2: RCT #12; Phase 3: Zirconia crown"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
            />
          </div>

          {/* SOAP Notes */}
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2.5">
            <span className="font-bold text-teal-800 block text-[11px] uppercase tracking-wider">
              Longitudinal SOAP Notes
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <div>
                <label className="block text-slate-600 font-medium mb-0.5 text-[11px]">
                  [S] Subjective History
                </label>
                <textarea
                  rows={2}
                  value={editSoapSubjective}
                  onChange={(e) => setEditSoapSubjective(e.target.value)}
                  placeholder="Patient history, reported pain score, onset..."
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-slate-600 font-medium mb-0.5 text-[11px]">
                  [O] Objective Examination
                </label>
                <textarea
                  rows={2}
                  value={editSoapObjective}
                  onChange={(e) => setEditSoapObjective(e.target.value)}
                  placeholder="Visual exam, probe depths, radiographs..."
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-slate-600 font-medium mb-0.5 text-[11px]">
                  [A] Assessment & Staging
                </label>
                <textarea
                  rows={2}
                  value={editSoapAssessment}
                  onChange={(e) => setEditSoapAssessment(e.target.value)}
                  placeholder="Prognosis, pulp vitality stage..."
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-slate-600 font-medium mb-0.5 text-[11px]">
                  [P] Plan & Prescriptions
                </label>
                <textarea
                  rows={2}
                  value={editSoapPlan}
                  onChange={(e) => setEditSoapPlan(e.target.value)}
                  placeholder="Next session goals, medication plan..."
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 font-medium mb-1">Local Anaesthesia Used</label>
              <input
                type="text"
                value={editLocalAnaesthesia}
                onChange={(e) => setEditLocalAnaesthesia(e.target.value)}
                placeholder="e.g. 2% Lignocaine with 1:80,000 Adrenaline (1.8 ml)"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
              />
            </div>
            <div>
              <label className="block text-slate-700 font-medium mb-1">
                Medicines Used / Dispensed in Session
              </label>
              <input
                type="text"
                value={editMedicinesUsed}
                onChange={(e) => setEditMedicinesUsed(e.target.value)}
                placeholder="e.g. Formocresol, Calcium hydroxide dressing"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-700 font-medium mb-1">General Clinical Notes</label>
            <textarea
              rows={2}
              value={editClinicalNotes}
              onChange={(e) => setEditClinicalNotes(e.target.value)}
              placeholder="Any additional observations or intra-operative notes..."
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
            />
          </div>

          <div>
            <label className="block text-slate-700 font-medium mb-1">
              Post-Op Patient Instructions
            </label>
            <input
              type="text"
              value={editFollowUpInstructions}
              onChange={(e) => setEditFollowUpInstructions(e.target.value)}
              placeholder="e.g. Warm saline gargles after 24 hrs. Avoid biting hard food on right side."
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsEditNotesOpen(false)}
              className="px-3 py-2 text-slate-600 hover:bg-slate-100 rounded-md cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => editNotesMutation.mutate()}
              disabled={editNotesMutation.isPending || !editDiagnosis.trim()}
              className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white font-bold rounded-md shadow-2xs disabled:opacity-50 inline-flex items-center gap-1.5 cursor-pointer"
            >
              <CheckCircle2 size={13} />
              {editNotesMutation.isPending ? "Saving..." : "Save Findings & Notes"}
            </button>
          </div>
        </div>
      </Dialog>

      {/* Quick Add Procedure Dialog */}
      <Dialog
        open={isAddProcedureOpen}
        onOpenChange={setIsAddProcedureOpen}
        title="Add Dental Procedure"
        description="Chart an additional clinical procedure performed during this visit."
      >
        <div className="space-y-4 text-xs">
          {/* Quick Procedure Presets */}
          <div>
            <label className="block text-slate-700 font-bold mb-1.5">
              Quick Dental Procedure Presets
            </label>
            <div className="flex flex-wrap gap-1.5">
              {DENTAL_PROCEDURE_PRESETS.map((p) => (
                <button
                  key={p.name}
                  type="button"
                  onClick={() => {
                    setNewProcName(p.name);
                    setNewProcCost(p.cost);
                    setNewProcDuration(p.duration);
                  }}
                  className={`px-2.5 py-1.5 rounded-md font-medium text-[11px] border transition-colors cursor-pointer ${
                    newProcName === p.name
                      ? "bg-teal-700 text-white border-teal-800 shadow-2xs"
                      : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-teal-50 hover:border-teal-300"
                  }`}
                >
                  {p.name} (₹{p.cost})
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-slate-700 font-semibold mb-1">
              Procedure Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={newProcName}
              onChange={(e) => setNewProcName(e.target.value)}
              placeholder="e.g. Scaling & Polishing, Root Canal Treatment"
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-teal-600 font-semibold"
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-slate-700 font-medium mb-1">Tooth #</label>
              <input
                type="text"
                value={newProcTooth}
                onChange={(e) => setNewProcTooth(e.target.value)}
                placeholder="e.g. 12, 16, 21"
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-teal-600 font-mono font-bold"
              />
            </div>
            <div>
              <label className="block text-slate-700 font-medium mb-1">Cost (₹)</label>
              <input
                type="number"
                min="0"
                step="50"
                value={newProcCost}
                onChange={(e) => setNewProcCost(Number(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-teal-600 font-mono font-semibold"
              />
            </div>
            <div>
              <label className="block text-slate-700 font-medium mb-1">Duration (min)</label>
              <input
                type="number"
                min="5"
                step="5"
                value={newProcDuration}
                onChange={(e) => setNewProcDuration(Number(e.target.value) || 30)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-teal-600 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-700 font-medium mb-1">Clinical Notes (Optional)</label>
            <input
              type="text"
              value={newProcNotes}
              onChange={(e) => setNewProcNotes(e.target.value)}
              placeholder="e.g. Shade A2 composite used, isolated with rubber dam"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsAddProcedureOpen(false)}
              className="px-3 py-2 text-slate-600 hover:bg-slate-100 rounded-md cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => addProcedureMutation.mutate()}
              disabled={addProcedureMutation.isPending || !newProcName.trim()}
              className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white font-bold rounded-md shadow-2xs disabled:opacity-50 inline-flex items-center gap-1.5 cursor-pointer"
            >
              <Plus size={13} />
              {addProcedureMutation.isPending ? "Adding..." : "Add Procedure to Record"}
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

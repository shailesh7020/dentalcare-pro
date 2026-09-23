"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  HeartPulse,
  Info,
  Layers,
  Pill,
  Plus,
  RotateCcw,
  Save,
  Stethoscope,
  Trash2,
  User,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { TreatmentCreateInput, TreatmentDetail, TreatmentStatus } from "../types";

interface ProcedureFormRow {
  procedure_name: string;
  tooth_number: string;
  quantity: number;
  cost: number;
  duration: number;
  notes: string;
  status: string;
}

function TreatmentNewForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  const appointmentIdParam = searchParams.get("appointment_id") || "";
  const patientIdParam = searchParams.get("patient_id") || "";

  // Form states
  const [patientId, setPatientId] = useState(patientIdParam);
  const [appointmentId, setAppointmentId] = useState(appointmentIdParam);
  const [isManualAppointment, setIsManualAppointment] = useState(false);
  const [dentistId, setDentistId] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [clinicalFindings, setClinicalFindings] = useState("");
  const [treatmentPlan, setTreatmentPlan] = useState("");
  const [procedurePerformed, setProcedurePerformed] = useState("");
  const [localAnaesthesia, setLocalAnaesthesia] = useState("");
  const [medicinesUsed, setMedicinesUsed] = useState("");
  const [clinicalNotes, setClinicalNotes] = useState("");
  const [status, setStatus] = useState<TreatmentStatus>("IN_PROGRESS");
  const [isOverride, setIsOverride] = useState(false);

  // SOAP notes
  const [soapSubjective, setSoapSubjective] = useState("");
  const [soapObjective, setSoapObjective] = useState("");
  const [soapAssessment, setSoapAssessment] = useState("");
  const [soapPlan, setSoapPlan] = useState("");

  // Follow-up
  const [hasFollowUp, setHasFollowUp] = useState(false);
  const [followUpDate, setFollowUpDate] = useState("");
  const [followUpReason, setFollowUpReason] = useState("");
  const [followUpInstructions, setFollowUpInstructions] = useState("");

  // Dynamic procedures builder
  const [procedures, setProcedures] = useState<ProcedureFormRow[]>([
    {
      procedure_name: "",
      tooth_number: "",
      quantity: 1,
      cost: 0,
      duration: 30,
      notes: "",
      status: "COMPLETED",
    },
  ]);

  const [formError, setFormError] = useState<string | null>(null);

  // Load Patient Detail if patientId is provided
  const patientQuery = useQuery({
    queryKey: ["patient-summary", patientId],
    queryFn: async () => {
      if (!patientId) return null;
      const res = await api.get(`/patients/${patientId}`);
      return res.data;
    },
    enabled: Boolean(patientId),
  });

  // Load Patient Appointments if patientId is provided
  const appointmentsQuery = useQuery({
    queryKey: ["patient-appointments", patientId],
    queryFn: async () => {
      if (!patientId) return [];
      const res = await api.get<any>("/appointments", {
        params: { patient_id: patientId, limit: 50 },
      });
      const data = res.data;
      if (Array.isArray(data)) return data;
      if (Array.isArray(data?.items)) return data.items;
      return [];
    },
    enabled: Boolean(patientId),
  });

  // Load Appointment Detail if appointmentId is provided
  const appointmentQuery = useQuery({
    queryKey: ["appointment-detail", appointmentId],
    queryFn: async () => {
      if (!appointmentId) return null;
      const res = await api.get(`/appointments/${appointmentId}`);
      return res.data;
    },
    enabled: Boolean(appointmentId),
  });

  // Load Clinicians list
  const cliniciansQuery = useQuery({
    queryKey: ["dentists-list"],
    queryFn: async () => {
      const res = await api.get("/dentists");
      const data = res.data;
      if (Array.isArray(data)) return data;
      if (Array.isArray(data?.items)) return data.items;
      return [];
    },
  });

  const appointmentsList: any[] = Array.isArray(appointmentsQuery.data)
    ? appointmentsQuery.data
    : [];
  const appointmentData = appointmentQuery.data;
  const patientData = patientQuery.data;

  // Auto-select first active or scheduled appointment if none selected
  useEffect(() => {
    if (!appointmentId && appointmentsList.length > 0) {
      const activeApt =
        appointmentsList.find(
          (a) => a.status === "CHECKED_IN" || a.status === "IN_TREATMENT"
        ) ||
        appointmentsList.find((a) => a.status === "SCHEDULED") ||
        appointmentsList[0];
      if (activeApt) {
        setAppointmentId(activeApt.id);
        if (!dentistId && activeApt.dentist_id) {
          setDentistId(activeApt.dentist_id);
        }
      }
    }
  }, [appointmentsList, appointmentId, dentistId]);

  // Auto-fill dentist and patient IDs if appointment detail loaded
  useEffect(() => {
    if (appointmentData) {
      if (!dentistId && appointmentData.dentist_id) {
        setDentistId(appointmentData.dentist_id);
      }
      if (!patientId && appointmentData.patient_id) {
        setPatientId(appointmentData.patient_id);
      }
    }
  }, [appointmentData, dentistId, patientId]);

  const handleSelectAppointment = (id: string) => {
    if (id === "__MANUAL__") {
      setIsManualAppointment(true);
      return;
    }
    setAppointmentId(id);
    const selected = appointmentsList.find((a) => a.id === id);
    if (selected?.dentist_id) {
      setDentistId(selected.dentist_id);
    }
  };

  // Procedure list helpers
  const handleAddProcedure = () => {
    setProcedures((prev) => [
      ...prev,
      {
        procedure_name: "",
        tooth_number: "",
        quantity: 1,
        cost: 0,
        duration: 30,
        notes: "",
        status: "COMPLETED",
      },
    ]);
  };

  const handleRemoveProcedure = (index: number) => {
    setProcedures((prev) => prev.filter((_, i) => i !== index));
  };

  const handleProcedureChange = (
    index: number,
    field: keyof ProcedureFormRow,
    value: any
  ) => {
    setProcedures((prev) =>
      prev.map((row, i) => (i === index ? { ...row, [field]: value } : row))
    );
  };

  // Calculation summaries
  const totalCost = useMemo(() => {
    return procedures.reduce(
      (sum, row) => sum + (Number(row.cost) || 0) * (Number(row.quantity) || 1),
      0
    );
  }, [procedures]);

  const totalDuration = useMemo(() => {
    return procedures.reduce((sum, row) => sum + (Number(row.duration) || 0), 0);
  }, [procedures]);

  // Submission mutation
  const createMutation = useMutation({
    mutationFn: async (payload: TreatmentCreateInput) => {
      setFormError(null);
      const res = await api.post<TreatmentDetail>("/treatments", payload);
      return res.data;
    },
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["treatments-list"] });
      void queryClient.invalidateQueries({ queryKey: ["treatment-dashboard-stats"] });
      void queryClient.invalidateQueries({ queryKey: ["patient-timeline", patientId] });
      void queryClient.invalidateQueries({ queryKey: ["appointments"] });
      router.push(`/treatments/${data.id}`);
    },
    onError: (err: any) => {
      const data = err.response?.data;
      if (Array.isArray(data?.error?.details) && data.error.details.length > 0) {
        const detailMsgs = data.error.details.map((d: any) => {
          const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "";
          const fieldName =
            field && typeof field === "string" ? field.replace(/_/g, " ") : "";
          return fieldName ? `${fieldName}: ${d.msg}` : d.msg;
        });
        setFormError(detailMsgs.join(" | "));
        return;
      }
      setFormError(
        data?.message || data?.detail || err.message || "Failed to create treatment record."
      );
    },
  });

  const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const cleanPatientId = patientId.trim();
    const cleanAppointmentId = appointmentId.trim();
    const cleanDentistId = dentistId.trim();

    if (!cleanPatientId) {
      setFormError("Patient ID is required.");
      return;
    }
    if (!UUID_REGEX.test(cleanPatientId)) {
      setFormError("Patient ID must be a valid 36-character UUID.");
      return;
    }
    if (!cleanAppointmentId) {
      setFormError("Please select an appointment to link this clinical treatment session.");
      return;
    }
    if (!UUID_REGEX.test(cleanAppointmentId)) {
      setFormError(
        "Appointment ID must be a valid 36-character UUID (e.g. 79a8570e-b6b4-4fb8-b829-16c06fc58848). Please select an appointment from the dropdown list."
      );
      return;
    }
    if (!cleanDentistId) {
      setFormError("Attending Clinician must be selected.");
      return;
    }
    if (!diagnosis.trim()) {
      setFormError("Clinical Diagnosis is required.");
      return;
    }

    // Clean valid procedures
    const validProcedures = procedures
      .filter((p) => p.procedure_name.trim().length > 0)
      .map((p) => ({
        procedure_name: p.procedure_name.trim(),
        tooth_number: p.tooth_number.trim() || undefined,
        quantity: Number(p.quantity) || 1,
        cost: Number(p.cost) || 0.0,
        duration: Number(p.duration) || 30,
        notes: p.notes.trim() || undefined,
        status: p.status || "COMPLETED",
      }));

    // Follow-up
    let followUpPayload = null;
    if (hasFollowUp && followUpDate.trim() && followUpReason.trim()) {
      followUpPayload = {
        follow_up_date: followUpDate.trim(),
        reason: followUpReason.trim(),
        instructions: followUpInstructions.trim() || undefined,
        status: "SCHEDULED" as const,
      };
    }

    const payload: TreatmentCreateInput = {
      patient_id: patientId.trim(),
      appointment_id: appointmentId.trim(),
      dentist_id: dentistId.trim(),
      diagnosis: diagnosis.trim(),
      chief_complaint: chiefComplaint.trim() || undefined,
      clinical_findings: clinicalFindings.trim() || undefined,
      treatment_plan: treatmentPlan.trim() || undefined,
      procedure_performed: procedurePerformed.trim() || undefined,
      local_anaesthesia_used: localAnaesthesia.trim() || undefined,
      medicines_used: medicinesUsed.trim() || undefined,
      clinical_notes: clinicalNotes.trim() || undefined,
      soap: {
        subjective: soapSubjective.trim() || undefined,
        objective: soapObjective.trim() || undefined,
        assessment: soapAssessment.trim() || undefined,
        plan: soapPlan.trim() || undefined,
      },
      follow_up_instructions: followUpInstructions.trim() || undefined,
      status,
      is_override: isOverride,
      procedures: validProcedures,
      follow_up: followUpPayload,
    };

    createMutation.mutate(payload);
  };

  // Extract medical alerts
  const med = patientData?.medical_history;
  const criticalConditions = [
    med?.cardiac_disease && "Cardiac Disease",
    med?.hypertension && "Hypertension",
    med?.diabetes && "Diabetes",
    med?.asthma && "Asthma",
    med?.epilepsy && "Epilepsy",
    med?.pregnancy && "Pregnancy",
    med?.allergies && `Allergies: ${med.allergies}`,
  ].filter(Boolean) as string[];

  return (
    <main className="min-h-screen bg-slate-50/60 pb-24">
      {/* Top Breadcrumb & Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/treatments"
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
            >
              <ArrowLeft size={18} />
            </Link>
            <div>
              <h1 className="text-xl font-bold text-slate-900">New Clinical Treatment Record</h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Record diagnosis, dynamic procedures, SOAP clinical notes, and post-op care
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/treatments"
              className="px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-md border border-slate-200"
            >
              Cancel
            </Link>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={createMutation.isPending}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-md shadow-2xs disabled:opacity-50 transition-colors"
            >
              <Save size={14} />
              {createMutation.isPending ? "Creating..." : "Save Clinical Record"}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {/* Error Alert Bar */}
        {formError && (
          <div className="mb-6 p-4 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-3 text-xs text-rose-900 animate-in fade-in">
            <AlertCircle size={18} className="text-rose-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Validation Error:</span> {formError}
            </div>
          </div>
        )}

        {/* Patient & Appointment Summary Card */}
        {patientData && (
          <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 mb-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-base border border-teal-300">
                  {patientData.first_name?.[0]}
                  {patientData.last_name?.[0]}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-slate-900">
                      {patientData.first_name} {patientData.last_name}
                    </h2>
                    <Badge variant="secondary" className="font-mono text-xs">
                      {patientData.patient_number}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-500 mt-1 flex items-center gap-3">
                    <span>{patientData.age} yrs</span>
                    <span>·</span>
                    <span className="capitalize">{patientData.gender?.toLowerCase()}</span>
                    <span>·</span>
                    <span className="font-mono">{patientData.mobile_number}</span>
                  </div>
                </div>
              </div>

              {appointmentData && (
                <div className="text-right text-xs bg-slate-50 border border-slate-200 p-2.5 rounded-md">
                  <div className="font-semibold text-slate-800 flex items-center gap-1.5 justify-end">
                    <Calendar size={13} className="text-teal-700" />
                    Appointment #{appointmentData.appointment_number}
                  </div>
                  <div className="text-slate-500 mt-0.5">
                    {appointmentData.date} at {appointmentData.start_time?.slice(0, 5)} · Chair{" "}
                    {appointmentData.chair_name}
                  </div>
                </div>
              )}
            </div>

            {/* Critical Conditions Banner */}
            {criticalConditions.length > 0 && (
              <div className="mt-4 p-3 rounded-md bg-rose-50 border border-rose-200 flex items-center gap-2 text-xs text-rose-900">
                <AlertTriangle size={16} className="text-rose-600 shrink-0" />
                <span className="font-bold mr-1">Medical Alerts:</span>
                <span>{criticalConditions.join("  |  ")}</span>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Section 1: Session Linkage & Clinician Assignment */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-2 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <User size={16} className="text-teal-700" /> 1. Session & Clinician Linkage
              </h2>
              {patientData && (
                <span className="text-xs text-slate-500 font-medium">
                  Patient: <strong className="text-slate-800">{patientData.first_name} {patientData.last_name}</strong> ({patientData.patient_number})
                </span>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Patient ID <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  placeholder="UUID of patient"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md font-mono focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  required
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-slate-700 font-semibold">
                    Appointment Session <span className="text-rose-500">*</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setIsManualAppointment((prev) => !prev)}
                    className="text-[11px] text-teal-600 hover:text-teal-800 font-medium underline"
                  >
                    {isManualAppointment ? "Select from list" : "Enter UUID manually"}
                  </button>
                </div>

                {isManualAppointment ? (
                  <input
                    type="text"
                    value={appointmentId}
                    onChange={(e) => setAppointmentId(e.target.value)}
                    placeholder="Enter 36-char Appointment UUID"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md font-mono focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                    required
                  />
                ) : appointmentsQuery.isLoading ? (
                  <div className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-slate-400">
                    Loading appointments...
                  </div>
                ) : appointmentsList.length > 0 ? (
                  <select
                    value={appointmentId}
                    onChange={(e) => handleSelectAppointment(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                    required
                  >
                    <option value="">-- Select an Appointment ({appointmentsList.length}) --</option>
                    {appointmentsList.map((apt: any) => (
                      <option key={apt.id} value={apt.id}>
                        #{apt.appointment_number} · {apt.date} at {apt.start_time?.slice(0, 5)} · [{apt.status}] · {apt.dentist_name ? `Dr. ${apt.dentist_name}` : "Assigned"}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="p-2 rounded-md bg-amber-50 border border-amber-200 text-amber-900 text-xs">
                    <p className="font-semibold">No appointments found</p>
                    <div className="mt-1 flex items-center gap-2">
                      <Link
                        href={`/appointments?patient_id=${patientId}`}
                        target="_blank"
                        className="text-teal-700 underline font-medium hover:text-teal-900"
                      >
                        + Book appointment
                      </Link>
                      <span>·</span>
                      <button
                        type="button"
                        onClick={() => setIsManualAppointment(true)}
                        className="underline text-slate-600"
                      >
                        Enter UUID
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Attending Clinician <span className="text-rose-500">*</span>
                </label>
                <select
                  value={dentistId}
                  onChange={(e) => setDentistId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  required
                >
                  <option value="">Select attending dentist</option>
                  {(cliniciansQuery.data || []).map((doc: any) => (
                    <option key={doc.id} value={doc.id}>
                      Dr. {doc.first_name} {doc.last_name} ({doc.specialization || "General"})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Section 2: Clinical Diagnosis & Complaints */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
              <Stethoscope size={16} className="text-teal-700" /> 2. Diagnosis & Findings
            </h2>
            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Clinical Diagnosis <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  placeholder="e.g. Irreversible Pulpitis on #46, Class II Caries #25"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Chief Complaint</label>
                  <textarea
                    rows={2}
                    value={chiefComplaint}
                    onChange={(e) => setChiefComplaint(e.target.value)}
                    placeholder="Patient's primary symptom, pain duration, intensity, triggers..."
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  />
                </div>

                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Clinical Findings</label>
                  <textarea
                    rows={2}
                    value={clinicalFindings}
                    onChange={(e) => setClinicalFindings(e.target.value)}
                    placeholder="Intraoral examination, percussion tenderness, probing depths..."
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Dynamic Procedure Builder */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
              <div>
                <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Layers size={16} className="text-teal-700" /> 3. Dental Procedures Performed / Planned
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Prepares clinical line items for treatment charting and billing invoicing.
                </p>
              </div>

              <button
                type="button"
                onClick={handleAddProcedure}
                className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-200 px-3 py-1.5 rounded-md transition-colors"
              >
                <Plus size={13} /> Add Procedure Row
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                    <th className="py-2.5 px-3">Procedure Name *</th>
                    <th className="py-2.5 px-3 w-28">Tooth #</th>
                    <th className="py-2.5 px-3 w-20 text-center">Qty</th>
                    <th className="py-2.5 px-3 w-28 text-right">Cost (₹)</th>
                    <th className="py-2.5 px-3 w-24 text-center">Duration</th>
                    <th className="py-2.5 px-3">Notes</th>
                    <th className="py-2.5 px-2 w-12 text-center"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {procedures.map((proc, index) => (
                    <tr key={index} className="hover:bg-slate-50/50">
                      <td className="py-2 px-3">
                        <input
                          type="text"
                          value={proc.procedure_name}
                          onChange={(e) =>
                            handleProcedureChange(index, "procedure_name", e.target.value)
                          }
                          placeholder="e.g. Root Canal Therapy, Composite Restoration"
                          className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                          required
                        />
                      </td>
                      <td className="py-2 px-3">
                        <input
                          type="text"
                          value={proc.tooth_number}
                          onChange={(e) =>
                            handleProcedureChange(index, "tooth_number", e.target.value)
                          }
                          placeholder="e.g. 46, 11-21"
                          className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded font-mono focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                        />
                      </td>
                      <td className="py-2 px-3">
                        <input
                          type="number"
                          min="1"
                          max="32"
                          value={proc.quantity}
                          onChange={(e) =>
                            handleProcedureChange(
                              index,
                              "quantity",
                              parseInt(e.target.value) || 1
                            )
                          }
                          className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded text-center focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                        />
                      </td>
                      <td className="py-2 px-3">
                        <input
                          type="number"
                          step="50"
                          min="0"
                          value={proc.cost}
                          onChange={(e) =>
                            handleProcedureChange(
                              index,
                              "cost",
                              parseFloat(e.target.value) || 0
                            )
                          }
                          className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded text-right font-mono focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                        />
                      </td>
                      <td className="py-2 px-3">
                        <input
                          type="number"
                          step="5"
                          min="5"
                          value={proc.duration}
                          onChange={(e) =>
                            handleProcedureChange(
                              index,
                              "duration",
                              parseInt(e.target.value) || 30
                            )
                          }
                          className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded text-center focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                        />
                      </td>
                      <td className="py-2 px-3">
                        <input
                          type="text"
                          value={proc.notes}
                          onChange={(e) =>
                            handleProcedureChange(index, "notes", e.target.value)
                          }
                          placeholder="Canals, shade, notes..."
                          className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                        />
                      </td>
                      <td className="py-2 px-2 text-center">
                        {procedures.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveProcedure(index)}
                            className="text-slate-400 hover:text-rose-600 p-1 rounded"
                            title="Remove row"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Total Summary Footer */}
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-500">
                {procedures.length} procedure item{procedures.length !== 1 ? "s" : ""} · Total
                estimated chair time: <b>{totalDuration} mins</b>
              </span>
              <div className="font-mono text-sm font-bold text-slate-900">
                Total Estimated Cost: ₹
                {totalCost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          {/* Section 4: Structured SOAP Notes */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-bold text-slate-900 mb-2 pb-2 border-b border-slate-100 flex items-center gap-2">
              <Activity size={16} className="text-teal-700" /> 4. Structured SOAP Clinical Notes
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Standard medical charting documentation (Subjective, Objective, Assessment, Plan).
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  [S] Subjective <span className="font-normal text-slate-400">(Patient history, symptoms)</span>
                </label>
                <textarea
                  rows={3}
                  value={soapSubjective}
                  onChange={(e) => setSoapSubjective(e.target.value)}
                  placeholder="Patient reports spontaneous throbbing pain radiating to ear since 2 nights ago..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  [O] Objective <span className="font-normal text-slate-400">(Clinical examination, tests)</span>
                </label>
                <textarea
                  rows={3}
                  value={soapObjective}
                  onChange={(e) => setSoapObjective(e.target.value)}
                  placeholder="Percussion +++, palpation negative. Thermal test shows lingering exaggerated response..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  [A] Assessment <span className="font-normal text-slate-400">(Clinical diagnosis, staging)</span>
                </label>
                <textarea
                  rows={3}
                  value={soapAssessment}
                  onChange={(e) => setSoapAssessment(e.target.value)}
                  placeholder="Acute Irreversible Pulpitis with symptomatic apical periodontitis #46..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  [P] Plan <span className="font-normal text-slate-400">(Action steps, prescriptions)</span>
                </label>
                <textarea
                  rows={3}
                  value={soapPlan}
                  onChange={(e) => setSoapPlan(e.target.value)}
                  placeholder="Access opening, pulp extirpation, BMP with rotary files, Ca(OH)2 dressing, analgesics..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
            </div>
          </div>

          {/* Section 5: Pharmaceuticals & Anaesthesia */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
              <Pill size={16} className="text-teal-700" /> 5. Pharmaceuticals & Anaesthesia
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Local Anaesthesia Used
                </label>
                <input
                  type="text"
                  value={localAnaesthesia}
                  onChange={(e) => setLocalAnaesthesia(e.target.value)}
                  placeholder="e.g. Lignocaine 2% with 1:80,000 Adrenaline (1.8 ml IANB)"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Medicines Prescribed / Dispensed
                </label>
                <input
                  type="text"
                  value={medicinesUsed}
                  onChange={(e) => setMedicinesUsed(e.target.value)}
                  placeholder="e.g. Amoxicillin 500mg TDS x 5 days, Ibuprofen 400mg BD x 3 days"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-slate-700 font-semibold mb-1">
                  General Clinical Notes
                </label>
                <textarea
                  rows={2}
                  value={clinicalNotes}
                  onChange={(e) => setClinicalNotes(e.target.value)}
                  placeholder="Working length: MB 21mm, ML 21mm, D 21.5mm. Irrigation with 2.5% NaOCl and saline. Closed with Cavit."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
            </div>
          </div>

          {/* Section 6: Follow-up & Treatment Status */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
              <Calendar size={16} className="text-teal-700" /> 6. Post-Operative Follow-Up & Status
            </h2>

            <div className="space-y-4 text-xs">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="hasFollowUp"
                  checked={hasFollowUp}
                  onChange={(e) => setHasFollowUp(e.target.checked)}
                  className="w-4 h-4 text-teal-600 border-slate-300 rounded focus:ring-teal-500"
                />
                <label htmlFor="hasFollowUp" className="font-semibold text-slate-800 cursor-pointer">
                  Schedule Clinical Follow-Up Visit for this Treatment
                </label>
              </div>

              {hasFollowUp && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pl-7 pt-2 animate-in fade-in">
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">
                      Follow-up Date <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="date"
                      value={followUpDate}
                      onChange={(e) => setFollowUpDate(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                      required={hasFollowUp}
                    />
                  </div>

                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">
                      Reason for Follow-up <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={followUpReason}
                      onChange={(e) => setFollowUpReason(e.target.value)}
                      placeholder="e.g. RCT Stage 2 Obturation, Suture removal, Polish"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                      required={hasFollowUp}
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Post-Op Instructions for Patient
                </label>
                <input
                  type="text"
                  value={followUpInstructions}
                  onChange={(e) => setFollowUpInstructions(e.target.value)}
                  placeholder="e.g. Do not chew on right side until anesthesia wears off. Avoid hard foods."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-slate-100">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Initial Status</label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value as TreatmentStatus)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  >
                    <option value="IN_PROGRESS">In Progress (Session active)</option>
                    <option value="PLANNED">Planned (Future session)</option>
                  </select>
                </div>

                <div className="flex items-center gap-2 pt-5">
                  <input
                    type="checkbox"
                    id="isOverride"
                    checked={isOverride}
                    onChange={(e) => setIsOverride(e.target.checked)}
                    className="w-4 h-4 text-purple-600 border-slate-300 rounded focus:ring-purple-500"
                  />
                  <div>
                    <label htmlFor="isOverride" className="font-semibold text-slate-800 cursor-pointer block">
                      Administrative Override
                    </label>
                    <span className="text-[11px] text-slate-400">
                      Allows multiple active treatments for same appointment (Clinic Admin only).
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Form Actions Footer */}
          <div className="flex items-center justify-end gap-3 pt-4">
            <Link
              href="/treatments"
              className="px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-md border border-slate-200 transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-md shadow-sm disabled:opacity-50 transition-colors"
            >
              <Save size={14} />
              {createMutation.isPending ? "Creating Treatment..." : "Save & Open Treatment Record"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}

export default function NewTreatmentPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-500">Loading form...</div>}>
      <TreatmentNewForm />
    </Suspense>
  );
}

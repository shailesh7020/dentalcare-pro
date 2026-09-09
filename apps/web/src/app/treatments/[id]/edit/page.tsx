"use client";

import { use, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Layers,
  Lock,
  Pill,
  Plus,
  Save,
  Stethoscope,
  Trash2,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { TreatmentDetail, TreatmentStatus, TreatmentUpdateInput } from "../../types";

interface ProcedureRow {
  procedure_name: string;
  tooth_number: string;
  quantity: number;
  cost: number;
  duration: number;
  notes: string;
  status: string;
}

export default function TreatmentEditPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();

  // Form states
  const [diagnosis, setDiagnosis] = useState("");
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [clinicalFindings, setClinicalFindings] = useState("");
  const [treatmentPlan, setTreatmentPlan] = useState("");
  const [procedurePerformed, setProcedurePerformed] = useState("");
  const [localAnaesthesia, setLocalAnaesthesia] = useState("");
  const [medicinesUsed, setMedicinesUsed] = useState("");
  const [clinicalNotes, setClinicalNotes] = useState("");
  const [status, setStatus] = useState<TreatmentStatus>("IN_PROGRESS");

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

  // Procedures
  const [procedures, setProcedures] = useState<ProcedureRow[]>([]);
  const [formError, setFormError] = useState<string | null>(null);

  // Fetch Treatment Detail
  const treatmentQuery = useQuery({
    queryKey: ["treatment-detail", id],
    queryFn: async () => {
      const res = await api.get<TreatmentDetail>(`/treatments/${id}`);
      return res.data;
    },
  });

  const treatment = treatmentQuery.data;

  // Pre-fill state once loaded
  useEffect(() => {
    if (treatment) {
      setDiagnosis(treatment.diagnosis || "");
      setChiefComplaint(treatment.chief_complaint || "");
      setClinicalFindings(treatment.clinical_findings || "");
      setTreatmentPlan(treatment.treatment_plan || "");
      setProcedurePerformed(treatment.procedure_performed || "");
      setLocalAnaesthesia(treatment.local_anaesthesia_used || "");
      setMedicinesUsed(treatment.medicines_used || "");
      setClinicalNotes(treatment.clinical_notes || "");
      setStatus(treatment.status);

      setSoapSubjective(treatment.soap_subjective || "");
      setSoapObjective(treatment.soap_objective || "");
      setSoapAssessment(treatment.soap_assessment || "");
      setSoapPlan(treatment.soap_plan || "");

      if (treatment.follow_ups && treatment.follow_ups.length > 0) {
        const latest = treatment.follow_ups[0];
        setHasFollowUp(true);
        setFollowUpDate(latest.follow_up_date || "");
        setFollowUpReason(latest.reason || "");
        setFollowUpInstructions(latest.instructions || "");
      }

      if (treatment.procedures && treatment.procedures.length > 0) {
        setProcedures(
          treatment.procedures.map((p) => ({
            procedure_name: p.procedure_name,
            tooth_number: p.tooth_number || "",
            quantity: p.quantity,
            cost: Number(p.cost) || 0,
            duration: p.duration,
            notes: p.notes || "",
            status: p.status,
          }))
        );
      } else {
        setProcedures([
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
      }
    }
  }, [treatment]);

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

  const handleProcedureChange = (index: number, field: keyof ProcedureRow, value: any) => {
    setProcedures((prev) =>
      prev.map((row, i) => (i === index ? { ...row, [field]: value } : row))
    );
  };

  const totalCost = useMemo(() => {
    return procedures.reduce(
      (sum, row) => sum + (Number(row.cost) || 0) * (Number(row.quantity) || 1),
      0
    );
  }, [procedures]);

  // Update Mutation
  const updateMutation = useMutation({
    mutationFn: async (payload: TreatmentUpdateInput) => {
      setFormError(null);
      const res = await api.patch<TreatmentDetail>(`/treatments/${id}`, payload);
      return res.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["treatment-detail", id] });
      void queryClient.invalidateQueries({ queryKey: ["treatments-list"] });
      void queryClient.invalidateQueries({ queryKey: ["treatment-dashboard-stats"] });
      router.push(`/treatments/${id}`);
    },
    onError: (err: any) => {
      setFormError(
        err.response?.data?.detail || err.message || "Failed to update treatment record."
      );
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!diagnosis.trim()) {
      setFormError("Clinical Diagnosis is required.");
      return;
    }

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

    let followUpPayload = null;
    if (hasFollowUp && followUpDate.trim() && followUpReason.trim()) {
      followUpPayload = {
        follow_up_date: followUpDate.trim(),
        reason: followUpReason.trim(),
        instructions: followUpInstructions.trim() || undefined,
        status: "SCHEDULED" as const,
      };
    }

    const payload: TreatmentUpdateInput = {
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
      procedures: validProcedures,
      follow_up: followUpPayload,
    };

    updateMutation.mutate(payload);
  };

  if (treatmentQuery.isLoading) {
    return (
      <main className="min-h-screen bg-slate-50/60 p-8 max-w-6xl mx-auto space-y-6">
        <Skeleton className="h-12 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }

  if (treatment && treatment.status === "COMPLETED") {
    return (
      <main className="min-h-screen bg-slate-50/60 flex items-center justify-center p-6 text-center">
        <div className="bg-white p-8 rounded-lg border border-slate-200 max-w-md shadow-xs">
          <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-700 flex items-center justify-center mx-auto mb-3">
            <Lock size={24} />
          </div>
          <h2 className="text-base font-bold text-slate-900">Treatment Is Completed & Locked</h2>
          <p className="text-xs text-slate-500 mt-1 mb-5">
            In compliance with dental clinical records governance, completed treatments are
            permanent and cannot be modified.
          </p>
          <Link
            href={`/treatments/${id}`}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-md shadow-2xs"
          >
            <ArrowLeft size={13} /> Return to Treatment View
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50/60 pb-24">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href={`/treatments/${id}`}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
            >
              <ArrowLeft size={18} />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold font-mono text-slate-900">
                  Edit {treatment?.treatment_number || "Treatment"}
                </h1>
                <Badge variant="warning">In Edit Mode</Badge>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Modifying clinical findings, procedures, and SOAP notes
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href={`/treatments/${id}`}
              className="px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-md border border-slate-200"
            >
              Cancel
            </Link>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={updateMutation.isPending}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-md shadow-2xs disabled:opacity-50 transition-colors"
            >
              <Save size={14} />
              {updateMutation.isPending ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {formError && (
          <div className="mb-6 p-4 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-3 text-xs text-rose-900 animate-in fade-in">
            <AlertCircle size={18} className="text-rose-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Error:</span> {formError}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Section 1: Clinical Diagnosis */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
              <Stethoscope size={16} className="text-teal-700" /> Diagnosis & Clinical Findings
            </h2>
            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Primary Clinical Diagnosis <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
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
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  />
                </div>

                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Clinical Findings</label>
                  <textarea
                    rows={2}
                    value={clinicalFindings}
                    onChange={(e) => setClinicalFindings(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Procedures Builder */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Layers size={16} className="text-teal-700" /> Dental Procedures Charted
              </h2>
              <button
                type="button"
                onClick={handleAddProcedure}
                className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-200 px-3 py-1.5 rounded-md"
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

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-500">
                {procedures.length} procedure item{procedures.length !== 1 ? "s" : ""}
              </span>
              <div className="font-mono text-sm font-bold text-slate-900">
                Total Cost: ₹{totalCost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          {/* Section 3: SOAP Notes */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
              <Activity size={16} className="text-teal-700" /> Longitudinal SOAP Notes
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">[S] Subjective</label>
                <textarea
                  rows={3}
                  value={soapSubjective}
                  onChange={(e) => setSoapSubjective(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">[O] Objective</label>
                <textarea
                  rows={3}
                  value={soapObjective}
                  onChange={(e) => setSoapObjective(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">[A] Assessment</label>
                <textarea
                  rows={3}
                  value={soapAssessment}
                  onChange={(e) => setSoapAssessment(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">[P] Plan</label>
                <textarea
                  rows={3}
                  value={soapPlan}
                  onChange={(e) => setSoapPlan(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
            </div>
          </div>

          {/* Section 4: Pharmaceuticals & Clinical Notes */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
              <Pill size={16} className="text-teal-700" /> Pharmacology & Clinical Notes
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Local Anaesthesia</label>
                <input
                  type="text"
                  value={localAnaesthesia}
                  onChange={(e) => setLocalAnaesthesia(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Medicines Prescribed</label>
                <input
                  type="text"
                  value={medicinesUsed}
                  onChange={(e) => setMedicinesUsed(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-slate-700 font-semibold mb-1">General Notes</label>
                <textarea
                  rows={2}
                  value={clinicalNotes}
                  onChange={(e) => setClinicalNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
            </div>
          </div>

          {/* Form Actions Footer */}
          <div className="flex items-center justify-end gap-3 pt-4">
            <Link
              href={`/treatments/${id}`}
              className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-md border border-slate-200"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="inline-flex items-center gap-1.5 px-5 py-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-md shadow-2xs disabled:opacity-50"
            >
              <Save size={14} />
              {updateMutation.isPending ? "Updating..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}

"use client";

import { use, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  XCircle,
  FileSpreadsheet,
  Building2,
  Sparkles,
  AlertTriangle,
  Send,
  Check,
  Copy,
  Receipt,
  Download,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { InsuranceNav } from "../../nav";
import type {
  ClaimDetail,
  ClaimStatus,
  InsuranceClaimItem,
  AICompletenessAudit,
  AIRejectionAnalysis,
} from "../../types";

export default function ClaimDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: claimId } = use(params);
  const queryClient = useQueryClient();

  const [auditResult, setAuditResult] = useState<AICompletenessAudit | null>(null);
  const [appealResult, setAppealResult] = useState<AIRejectionAnalysis | null>(null);
  const [copiedAppeal, setCopiedAppeal] = useState(false);

  const { data: claim, isLoading } = useQuery<ClaimDetail>({
    queryKey: ["insurance-claim-detail", claimId],
    queryFn: async () => {
      const res = await api.get<ClaimDetail>(`/insurance/claims/${claimId}`);
      return res.data;
    },
  });

  // Status transition mutation
  const updateStatusMutation = useMutation({
    mutationFn: async ({
      status,
      approved_amount,
      paid_amount,
      denial_code,
      denial_reason,
    }: {
      status: ClaimStatus;
      approved_amount?: number;
      paid_amount?: number;
      denial_code?: string;
      denial_reason?: string;
    }) => {
      await api.put(`/insurance/claims/${claimId}/status`, {
        status,
        approved_amount,
        paid_amount,
        denial_code,
        denial_reason,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insurance-claim-detail", claimId] });
    },
  });

  // AI Audit Mutation
  const auditMutation = useMutation({
    mutationFn: async () => {
      const codes = claim?.items?.map((it: InsuranceClaimItem) => it.procedure_code) || ["D3330"];
      const res = await api.post<AICompletenessAudit>("/insurance/ai/audit-completeness", {
        claim_id: claimId,
        procedure_codes: codes,
        attached_document_types: ["TREATMENT_PLAN", "X_RAY"],
      });
      return res.data;
    },
    onSuccess: (data) => {
      setAuditResult(data);
    },
  });

  // AI Denial / Appeal Mutation
  const appealMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post<AIRejectionAnalysis>("/insurance/ai/analyze-rejection", {
        claim_id: claimId,
        denial_code: claim?.denial_code || "CO-16",
        denial_reason: claim?.denial_reason || "Lacking necessary pre-operative radiographs",
      });
      return res.data;
    },
    onSuccess: (data) => {
      setAppealResult(data);
    },
  });

  const handleCopyAppeal = () => {
    if (appealResult?.suggested_appeal_letter) {
      navigator.clipboard.writeText(appealResult.suggested_appeal_letter);
      setCopiedAppeal(true);
      setTimeout(() => setCopiedAppeal(false), 2000);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50/50">
        <InsuranceNav />
        <div className="max-w-7xl mx-auto px-4 py-12 text-center text-slate-500 text-sm">
          Loading claim dossier...
        </div>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="min-h-screen bg-slate-50/50">
        <InsuranceNav />
        <div className="max-w-7xl mx-auto px-4 py-12 text-center text-slate-500 text-sm">
          Claim not found.
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50/50 pb-12">
      <InsuranceNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Navigation Breadcrumb & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/insurance/claims"
              className="p-2 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-slate-900">{claim.claim_number}</h1>
                <span
                  className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold ${
                    claim.status === "APPROVED" || claim.status === "PAID"
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      : claim.status === "REJECTED"
                      ? "bg-rose-50 text-rose-700 border border-rose-200"
                      : "bg-amber-50 text-amber-700 border border-amber-200"
                  }`}
                >
                  {(claim.status === "APPROVED" || claim.status === "PAID") && (
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  )}
                  {claim.status === "REJECTED" && <XCircle className="w-3.5 h-3.5" />}
                  {claim.status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Submitted on {claim.submission_date || "Not yet submitted"} · Adjudication:{" "}
                {claim.adjudication_date || "Pending"}
              </p>
            </div>
          </div>

          {/* Quick Lifecycle Status Actions */}
          <div className="flex flex-wrap items-center gap-2">
            {claim.status === "DRAFT" && (
              <button
                onClick={() =>
                  updateStatusMutation.mutate({
                    status: "SUBMITTED",
                  })
                }
                disabled={updateStatusMutation.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-600 text-white text-xs font-semibold rounded-lg hover:bg-teal-700 shadow-sm cursor-pointer"
              >
                <Send className="w-3.5 h-3.5" /> Submit to Payer
              </button>
            )}

            {(claim.status === "SUBMITTED" || claim.status === "PENDING") && (
              <>
                <button
                  onClick={() =>
                    updateStatusMutation.mutate({
                      status: "APPROVED",
                      approved_amount: claim.total_claimed_amount * 0.8,
                    })
                  }
                  disabled={updateStatusMutation.isPending}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 text-white text-xs font-semibold rounded-lg hover:bg-emerald-700 shadow-sm cursor-pointer"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" /> Mark Approved (80%)
                </button>
                <button
                  onClick={() =>
                    updateStatusMutation.mutate({
                      status: "REJECTED",
                      denial_code: "CO-16",
                      denial_reason: "Missing supporting radiograph",
                    })
                  }
                  disabled={updateStatusMutation.isPending}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 text-white text-xs font-semibold rounded-lg hover:bg-rose-700 shadow-sm cursor-pointer"
                >
                  <XCircle className="w-3.5 h-3.5" /> Mark Rejected
                </button>
              </>
            )}

            {claim.status === "APPROVED" && (
              <button
                onClick={() =>
                  updateStatusMutation.mutate({
                    status: "PAID",
                    paid_amount: claim.approved_amount ?? claim.total_claimed_amount * 0.8,
                  })
                }
                disabled={updateStatusMutation.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-700 text-white text-xs font-semibold rounded-lg hover:bg-teal-800 shadow-sm cursor-pointer"
              >
                <Receipt className="w-3.5 h-3.5" /> Record Payment Received
              </button>
            )}
          </div>
        </div>

        {/* Top Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-medium text-slate-500 uppercase">Total Claimed</span>
            <p className="text-xl font-bold text-slate-900 mt-1">₹{claim.total_claimed_amount.toLocaleString()}</p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-medium text-slate-500 uppercase">Payer Approved</span>
            <p className="text-xl font-bold text-emerald-600 mt-1">
              {claim.approved_amount !== null && claim.approved_amount !== undefined
                ? `₹${claim.approved_amount.toLocaleString()}`
                : "Pending"}
            </p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-medium text-slate-500 uppercase">Remitted / Paid</span>
            <p className="text-xl font-bold text-slate-800 mt-1">
              {claim.paid_amount ? `₹${claim.paid_amount.toLocaleString()}` : "₹0"}
            </p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-medium text-slate-500 uppercase">Patient Co-Pay Due</span>
            <p className="text-xl font-bold text-amber-600 mt-1">
              ₹{(claim.patient_copay_amount ?? claim.total_claimed_amount * 0.2).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Claim Procedure Line Items */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Claimed Dental Procedures</h3>
            <span className="text-xs text-slate-500">{claim.items?.length || 0} line item(s)</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">CDT Code</th>
                  <th className="py-3 px-4">Tooth #</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4">Total Cost</th>
                  <th className="py-3 px-4">Covered Share</th>
                  <th className="py-3 px-4">Patient Co-pay</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {claim.items && claim.items.length > 0 ? (
                  claim.items.map((item: InsuranceClaimItem) => (
                    <tr key={item.id} className="hover:bg-slate-50/50">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">{item.procedure_code}</td>
                      <td className="py-3 px-4 font-semibold text-slate-700">{item.tooth_number || "All"}</td>
                      <td className="py-3 px-4 text-slate-700">{item.procedure_name}</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">₹{item.total_cost.toLocaleString()}</td>
                      <td className="py-3 px-4 font-medium text-emerald-700">₹{item.covered_amount.toLocaleString()}</td>
                      <td className="py-3 px-4 font-medium text-amber-700">
                        ₹{item.patient_responsibility.toLocaleString()}
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="text-center py-6 text-slate-400">
                      No procedure items attached.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI Claim Assistant Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Card 1: Pre-Submission Completeness Auditor */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-teal-50 text-teal-700 rounded-lg">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">AI Completeness Auditor</h3>
                  <p className="text-xs text-slate-500">Scans missing x-rays, pre-auth, and clinical notes</p>
                </div>
              </div>
              <button
                onClick={() => auditMutation.mutate()}
                disabled={auditMutation.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 border border-teal-200 rounded-md hover:bg-teal-100 cursor-pointer"
              >
                {auditMutation.isPending ? "Auditing..." : "Run AI Audit"}
              </button>
            </div>

            {auditResult && (
              <div className="space-y-3 pt-2 border-t border-slate-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-700">Completeness Score</span>
                  <span
                    className={`text-sm font-bold ${
                      auditResult.completeness_score >= 80 ? "text-emerald-700" : "text-amber-600"
                    }`}
                  >
                    {auditResult.completeness_score}%
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-2 rounded-full ${
                      auditResult.completeness_score >= 80 ? "bg-emerald-500" : "bg-amber-500"
                    }`}
                    style={{ width: `${auditResult.completeness_score}%` }}
                  />
                </div>

                {auditResult.missing_requirements && auditResult.missing_requirements.length > 0 ? (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs space-y-1">
                    <span className="font-semibold text-amber-800 flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> Missing Requirements:
                    </span>
                    <ul className="list-disc list-inside text-amber-700 pl-1">
                      {auditResult.missing_requirements.map((req, i) => (
                        <li key={i}>{req}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-xs text-emerald-700 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Ready for submission. All mandatory
                    documentation attached.
                  </div>
                )}

                <p className="text-[10px] text-slate-400 italic">{auditResult.disclaimer}</p>
              </div>
            )}
          </div>

          {/* Card 2: Denial Root Cause & Automated Appeal Generator */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-purple-50 text-purple-700 rounded-lg">
                  <AlertCircle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Denial Analysis & Appeal Drafter</h3>
                  <p className="text-xs text-slate-500">Root-cause breakdown and one-click clinical appeal letter</p>
                </div>
              </div>
              <button
                onClick={() => appealMutation.mutate()}
                disabled={appealMutation.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-purple-700 bg-purple-50 border border-purple-200 rounded-md hover:bg-purple-100 cursor-pointer"
              >
                {appealMutation.isPending ? "Generating..." : "Generate Appeal"}
              </button>
            </div>

            {appealResult && (
              <div className="space-y-3 pt-2 border-t border-slate-100">
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs space-y-1">
                  <p className="font-semibold text-slate-800">
                    Denial Code: <span className="font-mono text-purple-700">{appealResult.denial_code}</span>
                  </p>
                  <p className="text-slate-600">
                    <span className="font-medium">Root Cause:</span> {appealResult.root_cause}
                  </p>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800">Drafted Formal Appeal Letter</span>
                    <button
                      onClick={handleCopyAppeal}
                      className="inline-flex items-center gap-1 text-xs text-teal-700 hover:text-teal-900 font-medium cursor-pointer"
                    >
                      {copiedAppeal ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      {copiedAppeal ? "Copied!" : "Copy Letter"}
                    </button>
                  </div>
                  <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg text-[11px] font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
                    {appealResult.suggested_appeal_letter}
                  </pre>
                </div>

                <p className="text-[10px] text-slate-400 italic">{appealResult.disclaimer}</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

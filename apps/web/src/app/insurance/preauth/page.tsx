"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  FileCheck2,
  Plus,
  Clock,
  CheckCircle2,
  XCircle,
  X,
  AlertCircle,
  ShieldAlert,
} from "lucide-react";
import { api } from "@/lib/api";
import { InsuranceNav } from "../nav";
import type { InsurancePreAuthorization, PreAuthStatus } from "../types";

export default function PreAuthorizationsPage() {
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [selectedPreAuthId, setSelectedPreAuthId] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (isCreateModalOpen) setIsCreateModalOpen(false);
        if (isUpdateModalOpen) setIsUpdateModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isCreateModalOpen, isUpdateModalOpen]);

  // Form State
  const [patientId, setPatientId] = useState("");
  const [policyId, setPolicyId] = useState("");
  const [requestedAmount, setRequestedAmount] = useState(15000);
  const [justification, setJustification] = useState("");

  // Status Update State
  const [newStatus, setNewStatus] = useState<PreAuthStatus>("APPROVED");
  const [approvedAmount, setApprovedAmount] = useState(15000);
  const [rejectionReason, setRejectionReason] = useState("");
  const [denialCode, setDenialCode] = useState("");

  const { data: preauthList = [], isLoading } = useQuery<InsurancePreAuthorization[]>({
    queryKey: ["insurance-preauthorizations"],
    queryFn: async () => {
      const res = await api.get<InsurancePreAuthorization[]>("/insurance/preauthorizations");
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      await api.post("/insurance/preauthorizations", {
        patient_id: patientId,
        policy_id: policyId,
        requested_amount: Number(requestedAmount),
        clinical_justification: justification,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insurance-preauthorizations"] });
      setIsCreateModalOpen(false);
      resetCreateForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPreAuthId) return;
      await api.put(`/insurance/preauthorizations/${selectedPreAuthId}/status`, {
        status: newStatus,
        approved_amount: newStatus === "APPROVED" ? Number(approvedAmount) : 0,
        rejection_reason: newStatus === "REJECTED" ? rejectionReason : null,
        denial_code: newStatus === "REJECTED" ? denialCode : null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insurance-preauthorizations"] });
      setIsUpdateModalOpen(false);
      setSelectedPreAuthId(null);
    },
  });

  const resetCreateForm = () => {
    setPatientId("");
    setPolicyId("");
    setRequestedAmount(15000);
    setJustification("");
  };

  return (
    <div className="min-h-screen bg-slate-50/50">
      <InsuranceNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Pre-Authorizations</h1>
            <p className="text-sm text-slate-600 mt-1">
              Prior approvals, medical necessity justifications, validity limits, and adjudication status.
            </p>
          </div>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-semibold hover:bg-teal-700 shadow-sm transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Request Pre-Authorization
          </button>
        </div>

        {/* List Table */}
        {isLoading ? (
          <div className="text-center py-12 text-slate-500 text-sm">Loading pre-authorizations...</div>
        ) : preauthList.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <FileCheck2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No pre-authorizations found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Major dental procedures (endodontics, implants, crowns) exceeding policy limits require prior approval.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Pre-Auth Number</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Requested Amount</th>
                    <th className="py-3 px-4">Approved Amount</th>
                    <th className="py-3 px-4">Validity</th>
                    <th className="py-3 px-4">Clinical Justification</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {preauthList.map((pa) => (
                    <tr key={pa.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">
                        {pa.preauth_number || "PENDING-ASSIGN"}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold ${
                            pa.status === "APPROVED"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : pa.status === "REJECTED"
                              ? "bg-rose-50 text-rose-700 border border-rose-200"
                              : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}
                        >
                          {pa.status === "APPROVED" && <CheckCircle2 className="w-3 h-3" />}
                          {pa.status === "REJECTED" && <XCircle className="w-3 h-3" />}
                          {pa.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-800">₹{pa.requested_amount.toLocaleString()}</td>
                      <td className="py-3 px-4 font-bold text-emerald-700">
                        {pa.approved_amount ? `₹${pa.approved_amount.toLocaleString()}` : "—"}
                      </td>
                      <td className="py-3 px-4 text-slate-600">{pa.valid_until || "Under Review"}</td>
                      <td className="py-3 px-4 text-slate-600 max-w-xs truncate">
                        {pa.clinical_justification || "None provided"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedPreAuthId(pa.id);
                            setIsUpdateModalOpen(true);
                          }}
                          className="px-2.5 py-1 text-xs font-semibold text-teal-700 bg-teal-50 border border-teal-200 rounded hover:bg-teal-100 cursor-pointer"
                        >
                          Update Status
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal: Create Pre-Auth */}
        {isCreateModalOpen && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 overflow-y-auto"
            onClick={(e) => {
              if (e.target === e.currentTarget) setIsCreateModalOpen(false);
            }}
          >
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-lg max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Request Pre-Authorization</h3>
                <button onClick={() => setIsCreateModalOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Patient UUID *</label>
                  <input
                    type="text"
                    placeholder="Patient ID"
                    value={patientId}
                    onChange={(e) => setPatientId(e.target.value)}
                    className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Policy UUID *</label>
                  <input
                    type="text"
                    placeholder="Policy ID"
                    value={policyId}
                    onChange={(e) => setPolicyId(e.target.value)}
                    className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Requested Coverage Amount (₹) *</label>
                  <input
                    type="number"
                    value={requestedAmount}
                    onChange={(e) => setRequestedAmount(Number(e.target.value))}
                    className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Clinical Justification & Notes</label>
                  <textarea
                    rows={3}
                    placeholder="Describe dental diagnosis, tooth numbers, procedure necessity, and radiograph evidence..."
                    value={justification}
                    onChange={(e) => setJustification(e.target.value)}
                    className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                  />
                </div>
              </div>
              <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
                <button
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createMutation.mutate()}
                  disabled={!patientId || !policyId || !requestedAmount || createMutation.isPending}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-md shadow-sm cursor-pointer disabled:opacity-50 transition-colors"
                >
                  {createMutation.isPending ? "Submitting..." : "Submit Pre-Auth"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Update Status */}
        {isUpdateModalOpen && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 overflow-y-auto"
            onClick={(e) => {
              if (e.target === e.currentTarget) setIsUpdateModalOpen(false);
            }}
          >
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-md max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Update Pre-Authorization Status</h3>
                <button onClick={() => setIsUpdateModalOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Status</label>
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value as PreAuthStatus)}
                    className="w-full text-xs border border-slate-300 dark:border-slate-700 rounded-md p-2 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                  >
                    <option value="SUBMITTED">Submitted</option>
                    <option value="UNDER_REVIEW">Under Review</option>
                    <option value="APPROVED">Approved</option>
                    <option value="REJECTED">Rejected</option>
                    <option value="EXPIRED">Expired</option>
                  </select>
                </div>
                {newStatus === "APPROVED" && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Approved Amount (₹)</label>
                    <input
                      type="number"
                      value={approvedAmount}
                      onChange={(e) => setApprovedAmount(Number(e.target.value))}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                )}
                {newStatus === "REJECTED" && (
                  <>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Denial Code</label>
                      <input
                        type="text"
                        placeholder="e.g. CO-16"
                        value={denialCode}
                        onChange={(e) => setDenialCode(e.target.value)}
                        className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Rejection Reason</label>
                      <textarea
                        rows={2}
                        placeholder="Lack of prior radiograph or excluded procedure"
                        value={rejectionReason}
                        onChange={(e) => setRejectionReason(e.target.value)}
                        className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                      />
                    </div>
                  </>
                )}
              </div>
              <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
                <button
                  onClick={() => setIsUpdateModalOpen(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => updateMutation.mutate()}
                  disabled={updateMutation.isPending}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-md shadow-sm cursor-pointer transition-colors"
                >
                  {updateMutation.isPending ? "Updating..." : "Confirm Update"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

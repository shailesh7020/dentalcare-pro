"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  FileSpreadsheet,
  Plus,
  Search,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  XCircle,
  X,
  Filter,
  Sparkles,
  AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import { InsuranceNav } from "../nav";
import type { InsuranceClaim, ClaimStatus, ClaimItemCreate } from "../types";

export default function InsuranceClaimsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isModalOpen) {
        setIsModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isModalOpen]);

  // New Claim Form
  const [patientId, setPatientId] = useState("");
  const [policyId, setPolicyId] = useState("");
  const [preauthId, setPreauthId] = useState("");
  const [procedureCode, setProcedureCode] = useState("D3330");
  const [procedureName, setProcedureName] = useState("Molar Root Canal Therapy");
  const [toothNumber, setToothNumber] = useState("46");
  const [unitCost, setUnitCost] = useState(12000);
  const [coveredAmount, setCoveredAmount] = useState(9600);
  const [patientShare, setPatientShare] = useState(2400);

  const { data: claims = [], isLoading } = useQuery<InsuranceClaim[]>({
    queryKey: ["insurance-claims", statusFilter],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (statusFilter !== "ALL") params.status = statusFilter;
      const res = await api.get<InsuranceClaim[]>("/insurance/claims", { params });
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const items: ClaimItemCreate[] = [
        {
          procedure_code: procedureCode,
          procedure_name: procedureName,
          tooth_number: toothNumber || null,
          quantity: 1,
          unit_cost: Number(unitCost),
          total_cost: Number(unitCost),
          covered_amount: Number(coveredAmount),
          patient_responsibility: Number(patientShare),
          insurance_responsibility: Number(coveredAmount),
        },
      ];
      await api.post("/insurance/claims", {
        patient_id: patientId,
        policy_id: policyId,
        preauth_id: preauthId || null,
        total_claimed_amount: Number(unitCost),
        items,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insurance-claims"] });
      setIsModalOpen(false);
      resetForm();
    },
  });

  const resetForm = () => {
    setPatientId("");
    setPolicyId("");
    setPreauthId("");
    setProcedureCode("D3330");
    setProcedureName("Molar Root Canal Therapy");
    setToothNumber("46");
    setUnitCost(12000);
    setCoveredAmount(9600);
    setPatientShare(2400);
  };

  const filteredClaims = claims.filter((c) => {
    if (!search.trim()) return true;
    return c.claim_number.toLowerCase().includes(search.toLowerCase());
  });

  return (
    <div className="min-h-screen bg-slate-50/50">
      <InsuranceNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Claims Management</h1>
            <p className="text-sm text-slate-600 mt-1">
              Submit, track, adjudicate, and audit electronic dental claims with payers.
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-semibold hover:bg-teal-700 shadow-sm transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Create Dental Claim
          </button>
        </div>

        {/* Filter Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by Claim Number (CLM-)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs text-slate-500 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="PENDING">Pending Adjudication</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected / Denied</option>
              <option value="PAID">Paid / Settled</option>
            </select>
          </div>
        </div>

        {/* Claims Table */}
        {isLoading ? (
          <div className="text-center py-12 text-slate-500 text-sm">Loading claims...</div>
        ) : filteredClaims.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <FileSpreadsheet className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No claims found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Create a new claim from completed treatment procedures to initiate payer reimbursement.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Claim #</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Claimed Amount</th>
                    <th className="py-3 px-4">Approved Amount</th>
                    <th className="py-3 px-4">Settled Amount</th>
                    <th className="py-3 px-4">Submission Date</th>
                    <th className="py-3 px-4 text-right">Dossier</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredClaims.map((claim) => (
                    <tr key={claim.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">{claim.claim_number}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold ${
                            claim.status === "APPROVED" || claim.status === "PAID"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : claim.status === "REJECTED"
                              ? "bg-rose-50 text-rose-700 border border-rose-200"
                              : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}
                        >
                          {(claim.status === "APPROVED" || claim.status === "PAID") && (
                            <CheckCircle2 className="w-3 h-3" />
                          )}
                          {claim.status === "REJECTED" && <XCircle className="w-3 h-3" />}
                          {claim.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-900">
                        ₹{claim.total_claimed_amount.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 font-bold text-emerald-700">
                        {claim.approved_amount !== null && claim.approved_amount !== undefined
                          ? `₹${claim.approved_amount.toLocaleString()}`
                          : "—"}
                      </td>
                      <td className="py-3 px-4 text-slate-700">
                        {claim.paid_amount ? `₹${claim.paid_amount.toLocaleString()}` : "₹0"}
                      </td>
                      <td className="py-3 px-4 text-slate-500">{claim.submission_date || "Draft"}</td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/insurance/claims/${claim.id}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 border border-teal-200 rounded-md hover:bg-teal-100 transition-colors"
                        >
                          View & Audit <ArrowUpRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal: Create Claim */}
        {isModalOpen && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 overflow-y-auto"
            onClick={(e) => {
              if (e.target === e.currentTarget) setIsModalOpen(false);
            }}
          >
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-xl max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Create Dental Claim</h3>
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
                    <Sparkles className="w-3 h-3" /> AI Validated
                  </span>
                </div>
                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Patient UUID *</label>
                    <input
                      type="text"
                      placeholder="Paste registered patient ID"
                      value={patientId}
                      onChange={(e) => setPatientId(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Policy UUID *</label>
                    <input
                      type="text"
                      placeholder="Paste active policy ID"
                      value={policyId}
                      onChange={(e) => setPolicyId(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Pre-Auth UUID (Optional)</label>
                    <input
                      type="text"
                      placeholder="Linked pre-authorization"
                      value={preauthId}
                      onChange={(e) => setPreauthId(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>

                  <div className="col-span-2 border-t border-slate-200 dark:border-slate-800 pt-3">
                    <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-2">Procedure Line Item</h4>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">CDT Procedure Code *</label>
                    <input
                      type="text"
                      placeholder="e.g. D3330"
                      value={procedureCode}
                      onChange={(e) => setProcedureCode(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 uppercase"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Tooth #</label>
                    <input
                      type="text"
                      placeholder="e.g. 46"
                      value={toothNumber}
                      onChange={(e) => setToothNumber(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Procedure Description *</label>
                    <input
                      type="text"
                      value={procedureName}
                      onChange={(e) => setProcedureName(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Procedure Fee / Cost (₹) *</label>
                    <input
                      type="number"
                      value={unitCost}
                      onChange={(e) => {
                        const val = Number(e.target.value);
                        setUnitCost(val);
                        setCoveredAmount(Math.round(val * 0.8));
                        setPatientShare(Math.round(val * 0.2));
                      }}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Expected Payer Share (80%)</label>
                    <input
                      type="number"
                      value={coveredAmount}
                      onChange={(e) => setCoveredAmount(Number(e.target.value))}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                </div>
              </div>
              <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createMutation.mutate()}
                  disabled={!patientId || !policyId || !unitCost || createMutation.isPending}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-md shadow-sm cursor-pointer disabled:opacity-50 transition-colors"
                >
                  {createMutation.isPending ? "Submitting..." : "Generate Claim"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

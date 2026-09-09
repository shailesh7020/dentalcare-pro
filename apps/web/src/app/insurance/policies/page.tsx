"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  UserCheck,
  Search,
  Plus,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldCheck,
  X,
  FileText,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { InsuranceNav } from "../nav";
import type { PatientInsurancePolicy, InsuranceProvider, InsurancePlan, PolicyStatus } from "../types";

export default function InsurancePoliciesPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);
  const [selectedPolicyForVerify, setSelectedPolicyForVerify] = useState<string | null>(null);

  // Form State for Policy Assignment
  const [patientId, setPatientId] = useState("");
  const [providerId, setProviderId] = useState("");
  const [planId, setPlanId] = useState("");
  const [policyNumber, setPolicyNumber] = useState("");
  const [memberId, setMemberId] = useState("");
  const [groupNumber, setGroupNumber] = useState("");
  const [relationship, setRelationship] = useState("SELF");
  const [priority, setPriority] = useState<"PRIMARY" | "SECONDARY" | "TERTIARY">("PRIMARY");
  const [effectiveDate, setEffectiveDate] = useState("2026-01-01");
  const [expiryDate, setExpiryDate] = useState("2026-12-31");

  // Verification Form State
  const [isVerified, setIsVerified] = useState(true);
  const [verificationNotes, setVerificationNotes] = useState("");

  const { data: providers = [] } = useQuery<InsuranceProvider[]>({
    queryKey: ["insurance-providers"],
    queryFn: async () => {
      const res = await api.get<InsuranceProvider[]>("/insurance/providers");
      return res.data;
    },
  });

  const { data: plans = [] } = useQuery<InsurancePlan[]>({
    queryKey: ["insurance-plans", providerId],
    enabled: !!providerId,
    queryFn: async () => {
      const res = await api.get<InsurancePlan[]>("/insurance/plans", {
        params: { provider_id: providerId },
      });
      return res.data;
    },
  });

  const { data: policies = [], isLoading } = useQuery<PatientInsurancePolicy[]>({
    queryKey: ["insurance-policies"],
    queryFn: async () => {
      const res = await api.get<PatientInsurancePolicy[]>("/insurance/policies");
      return res.data;
    },
  });

  const assignMutation = useMutation({
    mutationFn: async () => {
      await api.post("/insurance/policies", {
        patient_id: patientId,
        provider_id: providerId,
        plan_id: planId || null,
        policy_number: policyNumber,
        member_id: memberId,
        group_number: groupNumber || null,
        relationship: relationship,
        priority: priority,
        effective_date: effectiveDate,
        expiry_date: expiryDate,
        status: "PENDING_VERIFICATION",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insurance-policies"] });
      setIsAssignModalOpen(false);
      resetAssignForm();
    },
  });

  const verifyMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPolicyForVerify) return;
      await api.post(`/insurance/policies/${selectedPolicyForVerify}/verify`, {
        is_verified: isVerified,
        notes: verificationNotes || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insurance-policies"] });
      setIsVerifyModalOpen(false);
      setSelectedPolicyForVerify(null);
      setVerificationNotes("");
    },
  });

  const resetAssignForm = () => {
    setPatientId("");
    setProviderId("");
    setPlanId("");
    setPolicyNumber("");
    setMemberId("");
    setGroupNumber("");
    setRelationship("SELF");
    setPriority("PRIMARY");
  };

  const filteredPolicies = policies.filter((p) => {
    if (!search.trim()) return true;
    const s = search.toLowerCase();
    return (
      p.policy_number.toLowerCase().includes(s) ||
      p.member_id.toLowerCase().includes(s)
    );
  });

  return (
    <div className="min-h-screen bg-slate-50/50">
      <InsuranceNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Patient Insurance Policies</h1>
            <p className="text-sm text-slate-600 mt-1">
              Active subscriber coverages, member identification, priority coordination, and payer verification status.
            </p>
          </div>
          <button
            onClick={() => setIsAssignModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-semibold hover:bg-teal-700 shadow-sm transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Link Patient Policy
          </button>
        </div>

        {/* Search */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center gap-3">
          <div className="relative w-full sm:w-96">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by Policy Number or Member ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
        </div>

        {/* Policies Table */}
        {isLoading ? (
          <div className="text-center py-12 text-slate-500 text-sm">Loading policies...</div>
        ) : filteredPolicies.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <UserCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No patient policies found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Link an insurance policy to a registered patient to streamline automated claim billing.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Policy Number</th>
                    <th className="py-3 px-4">Member ID</th>
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Relationship</th>
                    <th className="py-3 px-4">Effective Dates</th>
                    <th className="py-3 px-4">Verification Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredPolicies.map((pol) => (
                    <tr key={pol.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">{pol.policy_number}</td>
                      <td className="py-3 px-4 font-mono text-slate-700">{pol.member_id}</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-teal-50 text-teal-700 border border-teal-200">
                          {pol.priority}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600 font-medium">{pol.relationship}</td>
                      <td className="py-3 px-4 text-slate-600">
                        {pol.effective_date} → {pol.expiry_date}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold ${
                            pol.status === "ACTIVE"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : pol.status === "PENDING_VERIFICATION"
                              ? "bg-amber-50 text-amber-700 border border-amber-200"
                              : "bg-rose-50 text-rose-700 border border-rose-200"
                          }`}
                        >
                          {pol.status === "ACTIVE" && <CheckCircle2 className="w-3 h-3" />}
                          {pol.status === "PENDING_VERIFICATION" && <Clock className="w-3 h-3" />}
                          {pol.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {pol.status !== "ACTIVE" && (
                          <button
                            onClick={() => {
                              setSelectedPolicyForVerify(pol.id);
                              setIsVerifyModalOpen(true);
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-teal-700 bg-teal-50 border border-teal-200 rounded hover:bg-teal-100 cursor-pointer"
                          >
                            <ShieldCheck className="w-3.5 h-3.5" /> Verify Coverage
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal: Link Policy */}
        {isAssignModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
            <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
                <h3 className="text-base font-bold text-slate-900">Link Patient Insurance Policy</h3>
                <button onClick={() => setIsAssignModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Patient UUID *</label>
                    <input
                      type="text"
                      placeholder="Paste Patient ID"
                      value={patientId}
                      onChange={(e) => setPatientId(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Payer / Carrier *</label>
                    <select
                      value={providerId}
                      onChange={(e) => setProviderId(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-md p-2 bg-white"
                    >
                      <option value="">Select Provider</option>
                      {providers.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.provider_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Insurance Plan</label>
                    <select
                      value={planId}
                      onChange={(e) => setPlanId(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-md p-2 bg-white"
                    >
                      <option value="">Standard Plan</option>
                      {plans.map((pl) => (
                        <option key={pl.id} value={pl.id}>
                          {pl.plan_name} ({pl.coverage_percentage}%)
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Policy Number *</label>
                    <input
                      type="text"
                      placeholder="e.g. POL-882910"
                      value={policyNumber}
                      onChange={(e) => setPolicyNumber(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Member / ID Number *</label>
                    <input
                      type="text"
                      placeholder="e.g. MEM-90412"
                      value={memberId}
                      onChange={(e) => setMemberId(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Priority</label>
                    <select
                      value={priority}
                      onChange={(e) => setPriority(e.target.value as any)}
                      className="w-full text-xs border border-slate-300 rounded-md p-2 bg-white"
                    >
                      <option value="PRIMARY">Primary Coverage</option>
                      <option value="SECONDARY">Secondary</option>
                      <option value="TERTIARY">Tertiary</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Relationship</label>
                    <select
                      value={relationship}
                      onChange={(e) => setRelationship(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-md p-2 bg-white"
                    >
                      <option value="SELF">Self / Subscriber</option>
                      <option value="SPOUSE">Spouse</option>
                      <option value="CHILD">Dependent Child</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Effective Date</label>
                    <input
                      type="date"
                      value={effectiveDate}
                      onChange={(e) => setEffectiveDate(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Expiry Date</label>
                    <input
                      type="date"
                      value={expiryDate}
                      onChange={(e) => setExpiryDate(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-md p-2"
                    />
                  </div>
                </div>
              </div>
              <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end gap-2">
                <button
                  onClick={() => setIsAssignModalOpen(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded-md"
                >
                  Cancel
                </button>
                <button
                  onClick={() => assignMutation.mutate()}
                  disabled={!patientId || !providerId || !policyNumber || !memberId || assignMutation.isPending}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-md shadow-sm disabled:opacity-50 cursor-pointer"
                >
                  {assignMutation.isPending ? "Linking..." : "Link Policy"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Verify Policy */}
        {isVerifyModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
            <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
                <h3 className="text-base font-bold text-slate-900">Verify Insurance Coverage</h3>
                <button onClick={() => setIsVerifyModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="verifyCheck"
                    checked={isVerified}
                    onChange={(e) => setIsVerified(e.target.checked)}
                    className="rounded text-teal-600 focus:ring-teal-500"
                  />
                  <label htmlFor="verifyCheck" className="text-xs font-medium text-slate-700">
                    Confirmed active member status with payer portal / helpline
                  </label>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Verification Notes</label>
                  <textarea
                    rows={3}
                    placeholder="Verified coverage limit, remaining annual balance, and copay requirements..."
                    value={verificationNotes}
                    onChange={(e) => setVerificationNotes(e.target.value)}
                    className="w-full text-xs border border-slate-300 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end gap-2">
                <button
                  onClick={() => setIsVerifyModalOpen(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded-md"
                >
                  Cancel
                </button>
                <button
                  onClick={() => verifyMutation.mutate()}
                  disabled={verifyMutation.isPending}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-md shadow-sm cursor-pointer"
                >
                  {verifyMutation.isPending ? "Updating..." : "Confirm Verification"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
